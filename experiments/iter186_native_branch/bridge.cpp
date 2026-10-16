// Sentinel extra-branch RRT extension. This changes planner semantics.
// The sampling/insertion skeleton follows OMPL control::RRT::solve at
// c509861210a63ec962bbec72c52823abc16b102e; see LICENSE_OMPL.txt.
// Preserve the existing bridge implementation and its allocation order as a
// separately callable baseline, without changing any historical bytes.
#define sentinel_rrt sentinel_rrt_parent186
#define sentinel_distance sentinel_distance_parent186
#include "../iter172_integrated_rrt/bridge.cpp"
#undef sentinel_rrt
#undef sentinel_distance
#include <cstdint>
#include <limits>
#include <memory>
#include <unordered_map>
#include <unordered_set>
#include <vector>

struct Branch186 {
    std::uint64_t parent, token;
    std::uint32_t steps, flags;
    double before[6], after[6];
};
using Branches186 = int (*)(std::uint64_t, const double *, const double *, Branch186 *);
using Event186 = int (*)(int, std::uint64_t, std::uint64_t, std::uint64_t,
                        unsigned, const double *, const double *);

class RetainingRRT186 : public oc::RRT {
    Branches186 callback_;
    Event186 event_;
    Stop hard_stop_;
    std::unordered_map<Motion *, std::uint64_t> ids_;
    std::unordered_set<std::uint64_t> tokens_;
    std::vector<Motion *> nodes_;
    std::vector<Motion *> path_;
    bool expired_ = false;
    int stop_code_ = 0;
    bool hard() { if (hard_stop_()) expired_ = true; return expired_; }
    static const double *values(const Motion *m) { return m->state->as<State>()->values; }
    static bool equal(const double *a, const double *b) {
        for (unsigned i=0;i<6;++i) if (a[i]!=b[i]) return false;
        return true;
    }
    void emit(int kind, Motion *m, const double *target=nullptr) {
        const auto parent=m->parent ? ids_.at(m->parent) : 0;
        const auto token=m->parent ? static_cast<std::uint64_t>(m->control->as<Control>()->values[0]) : 0;
        if (event_(kind,ids_.at(m),parent,token,m->steps,values(m),target))
            throw std::logic_error("event_callback");
    }
    void validate(const Branch186 &b, Motion *parent, bool extra) {
        if (b.parent!=ids_.at(parent) || !equal(b.before,values(parent)))
            throw std::logic_error("branch_parent");
        if (!b.token || b.token>9007199254740991ULL || tokens_.count(b.token))
            throw std::logic_error("branch_token");
        if (!b.steps || b.steps>8 || b.after[5]!=b.before[5]+b.steps ||
            std::floor(b.after[5])!=b.after[5]) throw std::logic_error("branch_duration");
        if (b.flags!=3) throw std::logic_error("branch_eligibility");
        for (double v:b.after) if (!std::isfinite(v)) throw std::logic_error("branch_finite");
        // Physical admissibility is checked by the producer and separate replay.
        // Do not introduce tighter endpoint bounds than the retained contract.
        if (extra) for (auto *node:nodes_) if (equal(values(node),b.after))
            throw std::logic_error("branch_duplicate");
    }
    Motion *insert(const Branch186 &b, Motion *parent, bool extra) {
        validate(b,parent,extra);
        auto *m=new Motion(siC_);
        std::memcpy(m->state->as<State>()->values,b.after,6*sizeof(double));
        m->control->as<Control>()->values[0]=static_cast<double>(b.token);
        m->steps=b.steps;m->parent=parent;
        nn_->add(m); ids_[m]=nodes_.size()+1; nodes_.push_back(m);tokens_.insert(b.token);
        emit(extra ? 2 : 1,m);return m;
    }
public:
    RetainingRRT186(const oc::SpaceInformationPtr &si, Branches186 cb, Event186 event, Stop hard_stop)
        : oc::RRT(si),callback_(cb),event_(event),hard_stop_(hard_stop) { setName("SentinelRetainingRRT186"); }
    ob::PlannerStatus solve(const ob::PlannerTerminationCondition &ptc) override {
        checkValidity();auto *goal=pdef_->getGoal().get();
        auto *goal_s=dynamic_cast<ob::GoalSampleableRegion *>(goal);
        while (const ob::State *st=pis_.nextStart()) {
            auto *m=new Motion(siC_);si_->copyState(m->state,st);siC_->nullControl(m->control);
            nn_->add(m);ids_[m]=nodes_.size()+1;nodes_.push_back(m);emit(0,m);
        }
        if (nodes_.size()!=1) throw std::logic_error("one_root_required");
        if (!sampler_) sampler_=si_->allocStateSampler();
        if (!controlSampler_) controlSampler_=siC_->allocDirectedControlSampler();
        auto destroy=[this](Motion *m){si_->freeState(m->state);siC_->freeControl(m->control);delete m;};
        std::unique_ptr<Motion,decltype(destroy)> random(new Motion(siC_),destroy);
        Motion *best=nullptr,*solution=nullptr;
        double best_distance=std::numeric_limits<double>::infinity();
        while (!ptc) {
            if (hard()) break;
            auto *rstate=random->state;
            if (goal_s && rng_.uniform01()<goalBias_ && goal_s->canSample()) goal_s->sampleGoal(rstate);
            else sampler_->sampleUniform(rstate);
            Motion *parent=nn_->nearest(random.get());
            if (hard()) break;
            double target[6];std::memcpy(target,rstate->as<State>()->values,sizeof(target));
            if (event_(3,ids_.at(parent),ids_.at(parent),0,0,values(parent),target))
                throw std::logic_error("event_callback");
            if (hard()) break;
            Branch186 branches[2]{};
            int count=callback_(ids_.at(parent),values(parent),target,branches);
            if (count<0 || count>2) throw std::logic_error("branch_count");
            if (hard()) break;
            for (int i=0;i<count;++i) {
                if (hard()) break;
                Motion *m=insert(branches[i],parent,i==1);
                if (hard()) break;
                double distance=0;
                bool solved=goal->isSatisfied(m->state,&distance);
                if (!std::isfinite(distance)) throw std::logic_error("goal_distance");
                if (hard()) break;
                if (solved) {solution=m;best_distance=distance;break;}
                if (distance<best_distance) {best=m;best_distance=distance;}
            }
            if (expired_ || solution) break;
        }
        if (hard()) {stop_code_=2;return ob::PlannerStatus::TIMEOUT;}
        stop_code_=solution ? 3 : 1;
        bool approximate=!solution;
        if (!solution) solution=best;
        if (!solution) return ob::PlannerStatus::TIMEOUT;
        lastGoalMotion_=solution;
        for (auto *m=solution;m;m=m->parent) path_.push_back(m);
        std::reverse(path_.begin(),path_.end());
        auto path=std::make_shared<oc::PathControl>(si_);
        for (auto *m:path_) {
            if (m->parent) path->append(m->state,m->control,m->steps*siC_->getPropagationStepSize());
            else path->append(m->state);
        }
        pdef_->addSolutionPath(path,approximate,best_distance,getName());
        return {true,approximate};
    }
    int output(double *out,int capacity,int *length,int *stop_code) {
        *stop_code=stop_code_;*length=0;
        if (hard()) {*stop_code=2;return 0;}
        if (path_.size()>static_cast<unsigned>(capacity)) throw std::logic_error("path_capacity");
        for (unsigned i=0;i<path_.size();++i) {
            auto *m=path_[i];auto *row=out+11*i;
            std::memcpy(row,values(m),6*sizeof(double));
            row[6]=m->parent ? m->control->as<Control>()->values[0] : 0;
            row[7]=ids_.at(m);row[8]=m->parent ? ids_.at(m->parent) : 0;
            row[9]=m->steps;row[10]=m->steps*siC_->getPropagationStepSize();
        }
        if (hard()) {*stop_code=2;return 0;}
        *length=path_.size();return pdef_->hasExactSolution() ? 2 : (pdef_->hasSolution() ? 1 : 0);
    }
};

extern "C" int sentinel_rrt186(unsigned seed,const double *start,const double *low,const double *high,
 const double *goal,Branches186 directed,GoalDistance goal_distance,Stop stop,Stop hard_stop,
 Sample sample,Event186 event,double *output,int capacity,int *length,int *stop_code,char *error) {
    *length=0;*stop_code=0;
    try {
        if (capacity<1 || capacity>402) throw std::logic_error("path_capacity");
        ompl::RNG::setSeed(seed);auto space=std::make_shared<Space>();ob::RealVectorBounds bounds(6);
        for (int i=0;i<6;++i){bounds.setLow(i,low[i]);bounds.setHigh(i,high[i]);}
        space->setBounds(bounds);space->setStateSamplerAllocator([sample](const ob::StateSpace *s){return std::make_shared<Sampler>(s,sample);});
        auto controls=std::make_shared<oc::RealVectorControlSpace>(space,1);ob::RealVectorBounds cb(1);cb.setLow(0,0);cb.setHigh(0,9007199254740991.0);controls->setBounds(cb);
        auto si=std::make_shared<oc::SpaceInformation>(space,controls);si->setPropagationStepSize(0.25);si->setMinMaxControlDuration(1,8);
        si->setStateValidityChecker([space](const ob::State *s){return space->satisfiesBounds(s);});
        si->setStatePropagator([](const ob::State *,const oc::Control *,double,ob::State *){throw std::logic_error("unaccounted propagation");});
        si->setDirectedControlSamplerAllocator([](const oc::SpaceInformation *s){return std::make_shared<DirectedSampler>(s,[](const double *,const double *,double *,double *){return 0;});});
        si->setup();auto problem=std::make_shared<ob::ProblemDefinition>(si);
        ob::State *initial=space->allocState();std::memcpy(initial->as<State>()->values,start,6*sizeof(double));problem->addStartState(initial);space->freeState(initial);
        problem->setGoal(std::make_shared<Goal>(si,goal_distance,goal));
        auto planner=std::make_shared<RetainingRRT186>(si,directed,event,hard_stop);
        planner->setNearestNeighbors<ompl::NearestNeighborsLinear>();planner->setIntermediateStates(false);planner->setGoalBias(0.1);
        planner->setProblemDefinition(problem);planner->setup();planner->solve(ob::PlannerTerminationCondition([stop](){return stop()!=0;}));
        return planner->output(output,capacity,length,stop_code);
    } catch(const std::exception &e){std::strncpy(error,e.what(),511);error[511]=0;return -1;}
}
