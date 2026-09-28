"""Minimal dual-target example: one cube, one sampled translation track."""

from pathlib import Path

import numpy as np
import pyvista as pv

from python_scene_handoff import Material, Node, Scene, TranslationTrack, export_gltf, export_usd

OUT = Path("output")
OUT.mkdir(exist_ok=True)

FPS = 30
DURATION = 2.0
scene = Scene.from_duration(fps=FPS, duration=DURATION, name="MovingCube")

phase = scene.times / DURATION
# Smooth out-and-back motion; values are node offsets from the base pose.
x = 1.5 * np.sin(np.pi * phase)
translations = np.column_stack([x, np.zeros_like(x), np.zeros_like(x)])

cube = Node(
    "Cube",
    mesh=pv.Cube(x_length=1.4, y_length=1.4, z_length=1.4).triangulate(),
    material=Material("#7FD6FF", 0.8),
    translation_track=TranslationTrack(translations),
)
scene.add(cube)

export_gltf(scene, OUT / "moving_cube.gltf", animation_name="MoveCube")
print("Created output/moving_cube.gltf")

try:
    export_usd(scene, OUT / "moving_cube.usda")
    print("Created output/moving_cube.usda")
except RuntimeError as exc:
    print(f"USD skipped: {exc}")
