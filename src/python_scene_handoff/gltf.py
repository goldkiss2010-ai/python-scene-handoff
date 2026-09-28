from __future__ import annotations

import base64
import json
import struct
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import pyvista as pv

from .scene import Node, Scene


def load_gltf(path: str | Path) -> dict:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_gltf(gltf: dict, path: str | Path) -> None:
    path = Path(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(gltf, f, ensure_ascii=False, indent=2)


def mesh_node_indices(gltf: dict) -> list[int]:
    return [i for i, node in enumerate(gltf.get("nodes", [])) if "mesh" in node]


def primary_scene_root(gltf: dict) -> int:
    scene_index = gltf.get("scene", 0)
    roots = gltf["scenes"][scene_index].get("nodes", [])
    if len(roots) != 1:
        raise ValueError(f"Expected one active-scene root node, found {roots!r}")
    return roots[0]


def _pack_float32(values: Iterable[float]) -> bytes:
    return b"".join(struct.pack("<f", float(v)) for v in values)


def _pack_vec3_float32(values: Iterable[Sequence[float]]) -> bytes:
    out = bytearray()
    for value in values:
        if len(value) != 3:
            raise ValueError(f"Expected VEC3, got {value!r}")
        out.extend(struct.pack("<fff", *(float(x) for x in value)))
    return bytes(out)


def add_baked_translation_tracks(
    gltf: dict,
    *,
    times: Sequence[float],
    tracks: Mapping[int, Sequence[Sequence[float]]],
    animation_name: str = "BakedTranslations",
) -> None:
    if len(times) < 2:
        raise ValueError("At least two time samples are required")
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("times must be strictly increasing")
    if not tracks:
        return

    node_count = len(gltf.get("nodes", []))
    for target_node, translations in tracks.items():
        if not 0 <= target_node < node_count:
            raise ValueError(f"Invalid target node index: {target_node}")
        if len(translations) != len(times):
            raise ValueError(
                f"Node {target_node}: expected {len(times)} translations, got {len(translations)}"
            )

    time_bytes = _pack_float32(times)
    track_bytes = [
        (target_node, _pack_vec3_float32(translations))
        for target_node, translations in tracks.items()
    ]

    offsets: list[tuple[int, int, int]] = []
    binary = bytearray(time_bytes)
    for target_node, payload in track_bytes:
        offset = len(binary)
        binary.extend(payload)
        offsets.append((target_node, offset, len(payload)))

    encoded = base64.b64encode(bytes(binary)).decode("ascii")
    buffers = gltf.setdefault("buffers", [])
    buffer_index = len(buffers)
    buffers.append(
        {
            "byteLength": len(binary),
            "uri": "data:application/octet-stream;base64," + encoded,
        }
    )

    buffer_views = gltf.setdefault("bufferViews", [])
    time_view_index = len(buffer_views)
    buffer_views.append(
        {"buffer": buffer_index, "byteOffset": 0, "byteLength": len(time_bytes)}
    )

    accessors = gltf.setdefault("accessors", [])
    time_accessor_index = len(accessors)
    accessors.append(
        {
            "bufferView": time_view_index,
            "componentType": 5126,
            "count": len(times),
            "type": "SCALAR",
            "min": [float(min(times))],
            "max": [float(max(times))],
        }
    )

    samplers = []
    channels = []
    for sampler_index, (target_node, byte_offset, byte_length) in enumerate(offsets):
        translation_view_index = len(buffer_views)
        buffer_views.append(
            {
                "buffer": buffer_index,
                "byteOffset": byte_offset,
                "byteLength": byte_length,
            }
        )
        translation_accessor_index = len(accessors)
        accessors.append(
            {
                "bufferView": translation_view_index,
                "componentType": 5126,
                "count": len(times),
                "type": "VEC3",
            }
        )
        samplers.append(
            {
                "input": time_accessor_index,
                "output": translation_accessor_index,
                "interpolation": "LINEAR",
            }
        )
        channels.append(
            {
                "sampler": sampler_index,
                "target": {"node": target_node, "path": "translation"},
            }
        )

    gltf.setdefault("animations", []).append(
        {"name": animation_name, "samplers": samplers, "channels": channels}
    )


def _build_scene_graph(
    gltf: dict,
    scene: Scene,
    mesh_mapping: dict[int, int],
) -> tuple[list[int], dict[int, int]]:
    """Create group nodes and return (top-level glTF nodes, node-id mapping)."""

    node_index_by_python_id: dict[int, int] = {}

    def build(node: Node) -> int:
        if node.mesh is not None:
            idx = mesh_mapping[id(node)]
            gltf["nodes"][idx]["name"] = node.name
            node_index_by_python_id[id(node)] = idx
            return idx

        child_indices = [build(child) for child in node.children]
        idx = len(gltf.setdefault("nodes", []))
        gltf["nodes"].append(
            {
                "name": node.name,
                "children": child_indices,
                "translation": [0.0, 0.0, 0.0],
            }
        )
        node_index_by_python_id[id(node)] = idx
        return idx

    roots = [build(root) for root in scene.roots]
    return roots, node_index_by_python_id


def export_gltf(
    scene: Scene,
    path: str | Path,
    *,
    animation_name: str = "PythonScene",
    keep_base: bool = False,
) -> Path:
    """Export the common Scene to animated glTF.

    PyVista/VTK authors valid static geometry; this function then rebuilds the
    scene hierarchy and appends frame-baked node translation channels.
    """

    scene.validate()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    base_path = path.with_name(path.stem + "_base.gltf")

    plotter = pv.Plotter(off_screen=True)
    mesh_nodes = scene.mesh_nodes()
    for node in mesh_nodes:
        r, g, b = node.material.rgb
        plotter.add_mesh(
            node.mesh,
            color=(r, g, b),
            opacity=float(node.material.opacity),
        )
    plotter.export_gltf(str(base_path), inline_data=True, rotate_scene=False)
    plotter.close()

    gltf = load_gltf(base_path)
    exported_mesh_nodes = mesh_node_indices(gltf)
    if len(exported_mesh_nodes) != len(mesh_nodes):
        raise RuntimeError(
            f"Expected {len(mesh_nodes)} mesh nodes from PyVista, got {exported_mesh_nodes!r}"
        )

    mesh_mapping = {
        id(py_node): gltf_node
        for py_node, gltf_node in zip(mesh_nodes, exported_mesh_nodes, strict=True)
    }
    top_nodes, mapping = _build_scene_graph(gltf, scene, mesh_mapping)

    renderer = primary_scene_root(gltf)
    renderer_children = list(gltf["nodes"][renderer].get("children", []))
    preserved = [n for n in renderer_children if n not in exported_mesh_nodes]
    gltf["nodes"][renderer]["children"] = preserved + top_nodes

    tracks: dict[int, list[list[float]]] = {}
    for node in scene.walk():
        if node.translation_track is None:
            continue
        target = mapping[id(node)]
        tracks[target] = node.translation_track.values.tolist()

    add_baked_translation_tracks(
        gltf,
        times=scene.times.tolist(),
        tracks=tracks,
        animation_name=animation_name,
    )
    save_gltf(gltf, path)

    if not keep_base:
        base_path.unlink(missing_ok=True)
    return path
