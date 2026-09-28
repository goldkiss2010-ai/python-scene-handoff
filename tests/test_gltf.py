import json

import numpy as np
import pyvista as pv

from python_scene_handoff import Node, Scene, TranslationTrack, export_gltf


def test_gltf_contains_animation(tmp_path):
    scene = Scene.from_duration(fps=10, duration=0.5, name="Test")
    track = np.zeros((len(scene.times), 3))
    track[:, 0] = np.linspace(0.0, 1.0, len(scene.times))
    scene.add(
        Node(
            "Cube",
            mesh=pv.Cube().triangulate(),
            translation_track=TranslationTrack(track),
        )
    )

    out = tmp_path / "test.gltf"
    export_gltf(scene, out, animation_name="TestMove")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["animations"][0]["name"] == "TestMove"
    assert len(data["animations"][0]["channels"]) == 1
