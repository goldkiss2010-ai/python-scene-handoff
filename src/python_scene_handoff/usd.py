from __future__ import annotations

from pathlib import Path

import numpy as np
import pyvista as pv

from .scene import Node, Scene


def _require_usd():
    try:
        from pxr import Gf, Sdf, Usd, UsdGeom  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise RuntimeError(
            "USD export requires the optional usd-core dependency. "
            "Install with: uv sync --extra usd"
        ) from exc
    return Gf, Sdf, Usd, UsdGeom


def _polydata_faces(poly: pv.PolyData) -> tuple[list[int], list[int]]:
    tri = poly.extract_surface().triangulate()
    faces = np.asarray(tri.faces, dtype=np.int64)
    counts: list[int] = []
    indices: list[int] = []
    cursor = 0
    while cursor < len(faces):
        count = int(faces[cursor])
        counts.append(count)
        start = cursor + 1
        indices.extend(int(x) for x in faces[start : start + count])
        cursor = start + count
    return counts, indices


def _safe_prim_name(name: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)
    if not cleaned:
        cleaned = "Node"
    if cleaned[0].isdigit():
        cleaned = "N_" + cleaned
    return cleaned


def export_usd(scene: Scene, path: str | Path) -> Path:
    """Export Scene as an animated USD stage for Resolve/Fusion and other DCCs."""

    Gf, _Sdf, Usd, UsdGeom = _require_usd()
    scene.validate()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    stage = Usd.Stage.CreateNew(str(path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    stage.SetFramesPerSecond(scene.fps)
    stage.SetTimeCodesPerSecond(scene.fps)
    stage.SetStartTimeCode(float(scene.times[0] * scene.fps))
    stage.SetEndTimeCode(float(scene.times[-1] * scene.fps))

    root = UsdGeom.Xform.Define(stage, f"/{_safe_prim_name(scene.name)}")
    stage.SetDefaultPrim(root.GetPrim())

    def author(node: Node, parent_path: str) -> None:
        node_name = _safe_prim_name(node.name)
        node_path = f"{parent_path}/{node_name}"
        xform = UsdGeom.Xform.Define(stage, node_path)
        translate_op = xform.AddTranslateOp()
        translate_op.Set(Gf.Vec3d(0.0, 0.0, 0.0))

        if node.translation_track is not None:
            for t, value in zip(scene.times, node.translation_track.values, strict=True):
                translate_op.Set(
                    Gf.Vec3d(float(value[0]), float(value[1]), float(value[2])),
                    Usd.TimeCode(float(t * scene.fps)),
                )

        if node.mesh is not None:
            poly = node.mesh.extract_surface().triangulate()
            counts, indices = _polydata_faces(poly)
            mesh = UsdGeom.Mesh.Define(stage, f"{node_path}/Mesh")
            mesh.CreatePointsAttr(
                [Gf.Vec3f(float(x), float(y), float(z)) for x, y, z in poly.points]
            )
            mesh.CreateFaceVertexCountsAttr(counts)
            mesh.CreateFaceVertexIndicesAttr(indices)
            mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
            r, g, b = node.material.rgb
            mesh.CreateDisplayColorAttr([Gf.Vec3f(r, g, b)])
            mesh.CreateDisplayOpacityAttr([float(node.material.opacity)])

        for child in node.children:
            author(child, node_path)

    root_path = root.GetPath().pathString
    for node in scene.roots:
        author(node, root_path)

    stage.GetRootLayer().Save()
    return path
