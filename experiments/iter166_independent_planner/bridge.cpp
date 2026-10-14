// Sentinel adapter around unmodified released OMPL control::RRT.
// OMPL is BSD licensed; see RUNTIME.json and the retained upstream license.
#include <ompl/base/spaces/RealVectorStateSpace.h>
#include <ompl/base/goals/GoalSampleableRegion.h>
#include <ompl/control/spaces/RealVectorControlSpace.h>
#include <ompl/control/planners/rrt/RRT.h>
#include <ompl/control/PathControl.h>
#include <ompl/control/SpaceInformation.h>
#include <ompl/util/RandomNumbers.h>
#include <ompl/datastructures/NearestNeighborsLinear.h>
#include <cmath>
#include <cstring>
#include <stdexcept>

namespace ob = ompl::base;
namespace oc = ompl::control;
using State = ob::RealVectorStateSpace::StateType;
using Control = oc::RealVectorControlSpace::ControlType;
using Directed = int (*)(const double *, const double *, double *, double *);
using GoalDistance = double (*)(const double *);
using Stop = int (*)();
using Sample = void (*)(double *);

class Space : public ob::RealVectorStateSpace {
public:
    Space() : ob::RealVectorStateSpace(6) {}
    double distance(const ob::State *a, const ob::State *b) const override {
        const auto *x=a->as<State>()->values, *y=b->as<State>()->values;
        const double weights[6]={1,1,2,0.5,2,0.01};
        double sum=0;
        for (int i=0;i<6;i++) {
            double d=x[i]-y[i];
            if (i==2) d=std::remainder(d,2*M_PI);
            sum+=weights[i]*weights[i]*d*d;
        }
        return std::sqrt(sum);
    }
};

class Sampler : public ob::StateSampler {
    Sample callback_;
public:
    Sampler(const ob::StateSpace *s, Sample cb) : ob::StateSampler(s), callback_(cb) {}
    void sampleUniform(ob::State *s) override { callback_(s->as<State>()->values); }
    void sampleUniformNear(ob::State *,const ob::State *,double) override { throw std::logic_error("unexpected near sampler"); }
    void sampleGaussian(ob::State *,const ob::State *,double) override { throw std::logic_error("unexpected Gaussian sampler"); }
};

class DirectedSampler : public oc::DirectedControlSampler {
    Directed callback_;
public:
    DirectedSampler(const oc::SpaceInformation *si, Directed cb) : oc::DirectedControlSampler(si), callback_(cb) {}
    unsigned int sampleTo(oc::Control *c,const ob::State *s,ob::State *d) override {
        double target[6]; std::memcpy(target,d->as<State>()->values,sizeof(target));
        return callback_(s->as<State>()->values,target,d->as<State>()->values,c->as<Control>()->values) ? 1 : 0;
    }
    unsigned int sampleTo(oc::Control *c,const oc::Control *,const ob::State *s,ob::State *d) override { return sampleTo(c,s,d); }
};

class Goal : public ob::GoalSampleableRegion {
    GoalDistance callback_;
    double target_[6];
public:
    Goal(const ob::SpaceInformationPtr &si,GoalDistance cb,const double *target) : ob::GoalSampleableRegion(si), callback_(cb) {
        std::memcpy(target_,target,sizeof(target_)); threshold_=0;
    }
    double distanceGoal(const ob::State *s) const override { return callback_(s->as<State>()->values); }
    bool isSatisfied(const ob::State *s) const override { return distanceGoal(s)==0; }
    bool isSatisfied(const ob::State *s,double *distance) const override {
        double d=distanceGoal(s); if(distance) *distance=d; return d==0;
    }
    void sampleGoal(ob::State *s) const override { std::memcpy(s->as<State>()->values,target_,sizeof(target_)); }
    unsigned int maxSampleCount() const override { return 1; }
};

extern "C" int sentinel_rrt(unsigned seed,const double *start,const double *low,const double *high,const double *goal,
    Directed directed,GoalDistance goal_distance,Stop stop,Sample sample,double *output,int capacity,int *length,char *error) {
    try {
        ompl::RNG::setSeed(seed);
        auto space=std::make_shared<Space>();
        ob::RealVectorBounds bounds(6);
        for (int i=0;i<6;i++) { bounds.setLow(i,low[i]); bounds.setHigh(i,high[i]); }
        space->setBounds(bounds);
        space->setStateSamplerAllocator([sample](const ob::StateSpace *s){return std::make_shared<Sampler>(s,sample);});
        auto controls=std::make_shared<oc::RealVectorControlSpace>(space,2);
        ob::RealVectorBounds cb(2); cb.setLow(0,-2);cb.setHigh(0,2);cb.setLow(1,-M_PI/12);cb.setHigh(1,M_PI/12);controls->setBounds(cb);
        auto si=std::make_shared<oc::SpaceInformation>(space,controls);
        si->setPropagationStepSize(0.25); si->setMinMaxControlDuration(1,1);
        // Directed sampler validates the complete one-step edge. This callback only
        // checks state bounds; unexpected propagation must never escape accounting.
        si->setStateValidityChecker([space](const ob::State *s){return space->satisfiesBounds(s);});
        si->setStatePropagator([](const ob::State *,const oc::Control *,double,ob::State *){throw std::logic_error("unaccounted propagation");});
        si->setDirectedControlSamplerAllocator([directed](const oc::SpaceInformation *s){return std::make_shared<DirectedSampler>(s,directed);});
        si->setup();
        auto problem=std::make_shared<ob::ProblemDefinition>(si);
        ob::State *initial=space->allocState(); std::memcpy(initial->as<State>()->values,start,6*sizeof(double));
        problem->addStartState(initial);space->freeState(initial);
        problem->setGoal(std::make_shared<Goal>(si,goal_distance,goal));
        auto planner=std::make_shared<oc::RRT>(si);planner->setNearestNeighbors<ompl::NearestNeighborsLinear>();planner->setIntermediateStates(false);planner->setGoalBias(0.1);
        planner->setProblemDefinition(problem);planner->setup();
        planner->solve(ob::PlannerTerminationCondition([stop](){return stop()!=0;}));
        *length=0;
        if (!problem->hasSolution()) return 0;
        auto path=std::dynamic_pointer_cast<oc::PathControl>(problem->getSolutionPath());
        if (!path || path->getStateCount()>static_cast<unsigned>(capacity)) throw std::logic_error("path capacity");
        *length=path->getStateCount();
        for(int i=0;i<*length;i++) {
            auto *row=output+9*i;
            std::memcpy(row,path->getState(i)->as<State>()->values,6*sizeof(double));
            row[6]=row[7]=row[8]=0;
            if(i) { const auto *c=path->getControl(i-1)->as<Control>()->values;row[6]=c[0];row[7]=c[1];row[8]=path->getControlDuration(i-1); }
        }
        return problem->hasExactSolution() ? 2 : 1;
    } catch(const std::exception &e) { std::strncpy(error,e.what(),511);error[511]=0;return -1; }
}

extern "C" double sentinel_distance(const double *a,const double *b) {
    Space space; auto *x=space.allocState(),*y=space.allocState();
    std::memcpy(x->as<State>()->values,a,6*sizeof(double));std::memcpy(y->as<State>()->values,b,6*sizeof(double));
    double result=space.distance(x,y);space.freeState(x);space.freeState(y);return result;
}
