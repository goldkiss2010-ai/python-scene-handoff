from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np
import pyvista as pv


Vec3 = tuple[float, float, float]


def _as_vec3(value: Sequence[float]) -> Vec3:
    if len(value) != 3:
        raise ValueError(f"Expected three components, got {value!r}")
    return (float(value[0]), float(value[1]), float(value[2]))


def hex_to_rgb01(value: str) -> Vec3:
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected #RRGGBB color, got {value!r}")
    return tuple(int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


@dataclass(slots=True)
class Material:
    color: str | Vec3 = "#FFFFFF"
    opacity: float = 1.0

    @property
    def rgb(self) -> Vec3:
        if isinstance(self.color, str):
            return hex_to_rgb01(self.color)
        return _as_vec3(self.color)


@dataclass(slots=True)
class TranslationTrack:
    """Dense translation samples aligned to Scene.times.

    Values are offsets relative to the node's base pose, not absolute positions.
    """

    values: np.ndarray

    def __post_init__(self) -> None:
        arr = np.asarray(self.values, dtype=float)
        if arr.ndim != 2 or arr.shape[1] != 3:
            raise ValueError(f"TranslationTrack must have shape (N, 3), got {arr.shape}")
        self.values = arr


@dataclass(slots=True)
class Node:
    name: str
    mesh: pv.PolyData | None = None
    material: Material = field(default_factory=Material)
    children: list["Node"] = field(default_factory=list)
    translation_track: TranslationTrack | None = None

    def add(self, *children: "Node") -> "Node":
        self.children.extend(children)
        return self

    @property
    def is_group(self) -> bool:
        return self.mesh is None


@dataclass(slots=True)
class Scene:
    """Minimal time-varying scene used by the interchange exporters.

    The scene deliberately models only what the proof-of-concept needs:
    PolyData geometry, hierarchy, material display color/opacity, and dense
    translation tracks. Rotation, scale, cameras, lights and deformation are
    intentionally left for future versions.
    """

    fps: float
    times: np.ndarray
    roots: list[Node] = field(default_factory=list)
    name: str = "Scene"

    def __post_init__(self) -> None:
        self.fps = float(self.fps)
        if self.fps <= 0:
            raise ValueError("fps must be positive")
        times = np.asarray(self.times, dtype=float)
        if times.ndim != 1 or len(times) < 2:
            raise ValueError("times must be a one-dimensional array with at least two samples")
        if np.any(np.diff(times) <= 0):
            raise ValueError("times must be strictly increasing")
        self.times = times

    @classmethod
    def from_duration(cls, *, fps: float, duration: float, name: str = "Scene") -> "Scene":
        frame_count = int(round(float(fps) * float(duration))) + 1
        times = np.arange(frame_count, dtype=float) / float(fps)
        return cls(fps=fps, times=times, name=name)

    def add(self, *nodes: Node) -> "Scene":
        self.roots.extend(nodes)
        return self

    def walk(self) -> Iterable[Node]:
        def visit(node: Node) -> Iterable[Node]:
            yield node
            for child in node.children:
                yield from visit(child)

        for root in self.roots:
            yield from visit(root)

    def mesh_nodes(self) -> list[Node]:
        return [node for node in self.walk() if node.mesh is not None]

    def validate(self) -> None:
        seen_ids: set[int] = set()
        for node in self.walk():
            ident = id(node)
            if ident in seen_ids:
                raise ValueError(f"Node {node.name!r} appears more than once in the scene graph")
            seen_ids.add(ident)
            if node.mesh is not None and not isinstance(node.mesh, pv.PolyData):
                raise TypeError(f"Node {node.name!r} mesh must be pyvista.PolyData")
            if node.translation_track is not None:
                if len(node.translation_track.values) != len(self.times):
                    raise ValueError(
                        f"Node {node.name!r}: track has {len(node.translation_track.values)} samples, "
                        f"scene has {len(self.times)} times"
                    )
