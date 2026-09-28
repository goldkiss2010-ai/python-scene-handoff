import numpy as np
import pyvista as pv
import pytest

from python_scene_handoff import Node, Scene, TranslationTrack


def test_scene_rejects_track_length_mismatch():
    scene = Scene.from_duration(fps=30, duration=1.0)
    node = Node(
        "Point",
        mesh=pv.Sphere(radius=0.1).triangulate(),
        translation_track=TranslationTrack(np.zeros((3, 3))),
    )
    scene.add(node)
    with pytest.raises(ValueError):
        scene.validate()


def test_scene_accepts_dense_track():
    scene = Scene.from_duration(fps=30, duration=1.0)
    node = Node(
        "Point",
        mesh=pv.Sphere(radius=0.1).triangulate(),
        translation_track=TranslationTrack(np.zeros((len(scene.times), 3))),
    )
    scene.add(node)
    scene.validate()
