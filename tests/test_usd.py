import importlib.util

import numpy as np
import pyvista as pv
import pytest

from python_scene_handoff import Node, Scene, TranslationTrack, export_usd


@pytest.mark.skipif(importlib.util.find_spec("pxr") is None, reason="usd-core not installed")
def test_usd_export(tmp_path):
    scene = Scene.from_duration(fps=10, duration=0.5, name="TestUSD")
    track = np.zeros((len(scene.times), 3))
    track[:, 1] = np.linspace(0.0, 1.0, len(scene.times))
    scene.add(
        Node(
            "Cube",
            mesh=pv.Cube().triangulate(),
            translation_track=TranslationTrack(track),
        )
    )
    out = tmp_path / "test.usda"
    export_usd(scene, out)
    text = out.read_text(encoding="utf-8")
    assert "TestUSD" in text
    assert "timeSamples" in text
