# Lorenz butterfly showcase

The showcase integrates the classical Lorenz system with RK4:

```text
dx/dt = sigma (y - x)
dy/dt = x (rho - z) - y
dz/dt = x y - beta z
```

using `sigma=10`, `rho=28`, and `beta=8/3`.

Eleven trajectories start from `x = 1 + epsilon`, with `epsilon` spread only across `[-2e-5, 2e-5]`. They therefore begin visually coincident and later separate macroscopically.

For presentation, all trajectories share the same monotone smootherstep mapping from display time to simulation time. This changes only presentation pacing; it does not give individual particles independent timing.

The output is sampled at 60 fps for 14 seconds. Static attractor/orbit tubes establish the structure, while the moving particles and small delayed ghost particles carry the time-varying motion.
