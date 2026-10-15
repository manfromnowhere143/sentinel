# A bounded initial guess from a discrete endpoint approximation

State is `(x,y,theta,v,delta)` and control is acceleration `a` and steering rate `r`.
The existing update first changes speed and steering, then position using the old
heading, then heading using the new speed/steering. Let `h=1/4 s`, `L=2.7 m`,
requested horizon `n`, and `T=nh`. Transform target displacement into the current
body frame `(X,Y)` and wrap target heading minus current heading to `Theta` with
remainder modulo `2*pi`. The proposed program repeats one `(a,r)` at each frame.
Prescribed wait/stop tasks retain the original initial program; the four original
integrated cases have neither prescribed phase.

## Longitudinal fit

Ignoring turning loss gives `v_j=v+a*h*j` and longitudinal endpoint `v*T+A*a`,
where `A=h*h*n*(n+1)/2`. With the existing position/speed metric weights `1,1/2`,
minimize `(v*T+A*a-X)^2 + (v+T*a-v_goal)^2/4`. Its scalar solution is

```text
a = [A*(X-v*T) + T*(v_goal-v)/4] / [A*A + T*T/4]
```

Clamp to `[max(-2,-v/T), min(2,(6-v)/T)]`. This also bounds all intermediate
speeds for the constant-acceleration sequence, up to the retained floating tolerance.

## Lateral and heading fit

Approximate `tan(delta+h*j*r)` by `tan(delta)+h*j*r*(1+tan(delta)^2)` and lateral
displacement by velocity times accumulated heading relative to the root. Define

```text
V = sum_j v_j                 J = sum_j j*v_j
C = sum_j v_j*sum_(k<j) v_k   D = sum_j v_j*sum_(k<j) k*v_k
q = tan(delta)               s = 1+q*q
y0 = q*h*h*C/L               theta0 = q*h*V/L
By = s*h*h*h*D/L             Bt = s*h*h*J/L
```

The strict `k<j` follows the actual position-before-heading update. At `n=1`,
`C=D=0`, so newly applied steering cannot alter that first lateral displacement.
Using existing lateral/heading/steering weights `1,2,2`, minimize
`(y0+By*r-Y)^2 + 4*(theta0+Bt*r-Theta)^2 + 4*(delta+T*r-delta_goal)^2`:

```text
r = [By*(Y-y0) + 4*Bt*(Theta-theta0) + 4*T*(delta_goal-delta)] /
    [By*By + 4*Bt*Bt + 4*T*T]
```

Clamp to `[max(-pi/12,(-pi/3-delta)/T), min(pi/12,(pi/3-delta)/T)]`.
Emit normalized `a/2` and `r/(pi/12)` in the unchanged variable order.
The producer accumulates prefix sums in one bounded loop. There is no nonlinear
propagation, scene query, fitted hyperparameter or optimizer inside this arithmetic.
Its computation remains inside the original wall deadline.

## Independent reconstruction and limits

The checker uses polynomial sums rather than the producer's prefix loop. Let
`b=a*h`, `S1=n(n+1)/2`, `S2=n(n+1)(2n+1)/6`, `S3=S1^2`, and
`S4=n(n+1)(2n+1)(3n^2+3n-1)/30`. Then

```text
V = n*v+b*S1
J = v*S1+b*S2
C = [V*V-(n*v*v+2*v*b*S1+b*b*S2)]/2
D = v*v*(S2-S1)/2 + v*b*(5*S3-6*S2+S1)/6 + b*b*(2*S4-3*S3+S2)/6
```

The two fits are sequential, not a joint nonlinear optimum. Turning changes actual
longitudinal travel; large heading or steering changes can invalidate the local
approximation. Speed/steering bounds do not guarantee yaw, lateral acceleration,
collision, route or checkpoint validity. All full dynamics and hard checks remain.
The separate parameter tolerance is `2e-14` for the new seed and `2e-15` for later
unchanged programs; physical and goal tolerances are unchanged.

Physical reflection negates `Y,Theta,delta,r` and preserves `X,v,a`. Equal planar
position weights preserve rigid-coordinate behavior up to roundoff. Neither case
labels, direction labels, obstacle data nor witness actions enter the proposal.
Constructed controls include improvements and an exact old curved connection lost
by this approximation. These behaviors qualify the implementation's stated scope;
they do not predict the original four integrated outcomes.
