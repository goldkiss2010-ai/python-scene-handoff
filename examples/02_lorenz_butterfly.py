"""Showcase: a smooth Lorenz butterfly-effect flow exported to glTF and USD.

Near-identical initial conditions are integrated in Python. The same sampled
scene state is then handed off to either After Effects (glTF) or Resolve/Fusion
(USD). Motion is dense-sampled at the destination frame rate.
"""

from pathlib import Path

import numpy as np
import pyvista as pv

from python_scene_handoff import Material, Node, Scene, TranslationTrack, export_gltf, export_usd

OUT = Path("output")
OUT.mkdir(exist_ok=True)

FPS = 60
DURATION = 14.0
SIM_DURATION = 38.0
INTEGRATION_DT = 0.0025

SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0

# A narrow bundle of almost identical initial conditions.
PERTURBATIONS = np.linspace(-2.0e-5, 2.0e-5, 11)
INITIAL_STATES = [np.array([1.0 + eps, 1.0, 1.0]) for eps in PERTURBATIONS]

COLORS = [
    "#54D7FF",
    "#68DDFB",
    "#7CE4F6",
    "#94E9EE",
    "#B1ECE5",
    "#E8EEF2",
    "#F3DCEB",
    "#F7C5E3",
    "#F7AEDA",
    "#F494D0",
    "#EC79C5",
]


def lorenz(state: np.ndarray) -> np.ndarray:
    x, y, z = state
    return np.array(
        [
            SIGMA * (y - x),
            x * (RHO - z) - y,
            x * y - BETA * z,
        ],
        dtype=float,
    )


def rk4_step(state: np.ndarray, dt: float) -> np.ndarray:
    k1 = lorenz(state)
    k2 = lorenz(state + 0.5 * dt * k1)
    k3 = lorenz(state + 0.5 * dt * k2)
    k4 = lorenz(state + dt * k3)
    return state + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0


def integrate_dense(initial: np.ndarray, sim_duration: float) -> tuple[np.ndarray, np.ndarray]:
    steps = int(np.ceil(sim_duration / INTEGRATION_DT))
    times = np.linspace(0.0, sim_duration, steps + 1)
    points = np.empty((steps + 1, 3), dtype=float)
    state = initial.astype(float).copy()
    points[0] = state
    dt = times[1] - times[0]
    for i in range(1, steps + 1):
        state = rk4_step(state, dt)
        points[i] = state
    return times, points


def smootherstep(s: np.ndarray) -> np.ndarray:
    """Monotone presentation-time map: gentle start/end, faster middle."""
    return s**3 * (s * (s * 6.0 - 15.0) + 10.0)


def sample_trajectory(raw_t: np.ndarray, raw_points: np.ndarray, display_t: np.ndarray) -> np.ndarray:
    out = np.empty((len(display_t), 3), dtype=float)
    for axis in range(3):
        out[:, axis] = np.interp(display_t, raw_t, raw_points[:, axis])
    return out


def polyline_tube(points: np.ndarray, radius: float, sides: int = 6) -> pv.PolyData:
    poly = pv.PolyData(points)
    poly.lines = np.hstack(([len(points)], np.arange(len(points), dtype=np.int64)))
    return poly.tube(radius=radius, n_sides=sides).triangulate()


# Reference orbit determines one stable shared normalization.
ref_t, reference_raw = integrate_dense(np.array([1.0, 1.0, 1.0]), 60.0)
reference_raw = reference_raw[2000::4]  # discard transient and thin static geometry
lo = reference_raw.min(axis=0)
hi = reference_raw.max(axis=0)
center = 0.5 * (lo + hi)
uniform_scale = 3.65 / float(np.max(hi - lo))


def to_scene(points: np.ndarray) -> np.ndarray:
    return (np.asarray(points) - center) * uniform_scale


scene = Scene.from_duration(fps=FPS, duration=DURATION, name="LorenzButterfly")
normalized_t = scene.times / DURATION
sim_display_t = SIM_DURATION * smootherstep(normalized_t)

raw_trajectories = [integrate_dense(state, SIM_DURATION) for state in INITIAL_STATES]
trajectories = [
    to_scene(sample_trajectory(raw_t, raw_points, sim_display_t))
    for raw_t, raw_points in raw_trajectories
]

# Static hairline attractor: enough geometry to establish the butterfly shape,
# but faint enough that the moving bundle remains dominant.
reference_scene = to_scene(reference_raw)
scene.add(
    Node(
        "Attractor",
        mesh=polyline_tube(reference_scene, radius=0.0042, sides=5),
        material=Material("#8BCBFF", 0.13),
    )
)

# Add several faint full trajectories as fine structural lines.
for index in (0, 2, 5, 8, 10):
    scene.add(
        Node(
            f"Orbit_{index:02d}",
            mesh=polyline_tube(trajectories[index], radius=0.0028, sides=5),
            material=Material(COLORS[index], 0.10),
        )
    )

# Moving particles plus three subtle delayed ghosts. All tracks are derived from
# the same time-warped simulation samples, so the motion remains synchronized.
GHOST_LAGS = (3, 7, 12)
GHOST_SCALES = (0.72, 0.52, 0.36)
GHOST_OPACITIES = (0.24, 0.14, 0.08)

for index, (points, color) in enumerate(zip(trajectories, COLORS, strict=True)):
    origin = points[0]
    particle = Node(
        f"Particle_{index:02d}",
        mesh=pv.Sphere(radius=0.045, center=origin, theta_resolution=18, phi_resolution=18).triangulate(),
        material=Material(color, 0.95),
        translation_track=TranslationTrack(points - origin),
    )
    scene.add(particle)

    for ghost_i, (lag, scale, opacity) in enumerate(
        zip(GHOST_LAGS, GHOST_SCALES, GHOST_OPACITIES, strict=True)
    ):
        delayed = points[np.maximum(np.arange(len(points)) - lag, 0)]
        ghost = Node(
            f"Particle_{index:02d}_Ghost_{ghost_i}",
            mesh=pv.Sphere(
                radius=0.045 * scale,
                center=origin,
                theta_resolution=14,
                phi_resolution=14,
            ).triangulate(),
            material=Material(color, opacity),
            translation_track=TranslationTrack(delayed - origin),
        )
        scene.add(ghost)

export_gltf(
    scene,
    OUT / "lorenz_butterfly.gltf",
    animation_name="Lorenz_Butterfly_Flow",
)
print("Created output/lorenz_butterfly.gltf")

try:
    export_usd(scene, OUT / "lorenz_butterfly.usda")
    print("Created output/lorenz_butterfly.usda")
except RuntimeError as exc:
    print(f"USD skipped: {exc}")
