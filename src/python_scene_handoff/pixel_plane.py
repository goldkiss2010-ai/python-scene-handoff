from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


_DEFAULT_PALETTE = {
    "R": "#D94B4B",
    "G": "#55A868",
    "B": "#4C72B0",
}


@dataclass(frozen=True)
class PixelPlaneSpec:
    """Exact 2D sensor/image plane described in source-pixel coordinates."""

    width: int = 2000
    height: int = 2000
    hot_x: int | None = None
    hot_y: int | None = None
    cfa_pattern: str = "RGGB"

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")

        pattern = self.cfa_pattern.upper()
        if len(pattern) != 4 or any(ch not in "RGB" for ch in pattern):
            raise ValueError("cfa_pattern must be four RGB letters in row-major 2x2 order")
        object.__setattr__(self, "cfa_pattern", pattern)

        hot_x = self.width // 2 if self.hot_x is None else self.hot_x
        hot_y = self.height // 2 if self.hot_y is None else self.hot_y

        if not 0 <= hot_x < self.width:
            raise ValueError("hot_x must be inside the plane")
        if not 0 <= hot_y < self.height:
            raise ValueError("hot_y must be inside the plane")

        object.__setattr__(self, "hot_x", int(hot_x))
        object.__setattr__(self, "hot_y", int(hot_y))

    @property
    def pixel_count(self) -> int:
        return self.width * self.height

    @property
    def hot_cfa_channel(self) -> str:
        row = self.hot_y % 2
        col = self.hot_x % 2
        return self.cfa_pattern[row * 2 + col]


@dataclass(frozen=True)
class PixelPlanePackage:
    cfa_svg: Path | None
    hot_pixel_svg: Path
    ae_jsx: Path
    manifest: Path


def _svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none" shape-rendering="crispEdges">'
    )


def write_cfa_svg(
    spec: PixelPlaneSpec,
    path: str | Path,
    *,
    palette: dict[str, str] | None = None,
) -> Path:
    """Write one compact SVG whose 2x2 pattern fills the exact sensor plane."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    colors = dict(_DEFAULT_PALETTE)
    if palette:
        colors.update({k.upper(): v for k, v in palette.items()})

    p = spec.cfa_pattern
    svg = "\n".join(
        [
            _svg_header(spec.width, spec.height),
            "  <defs>",
            '    <pattern id="cfa" width="2" height="2" patternUnits="userSpaceOnUse">',
            f'      <rect x="0" y="0" width="1" height="1" fill="{colors[p[0]]}"/>',
            f'      <rect x="1" y="0" width="1" height="1" fill="{colors[p[1]]}"/>',
            f'      <rect x="0" y="1" width="1" height="1" fill="{colors[p[2]]}"/>',
            f'      <rect x="1" y="1" width="1" height="1" fill="{colors[p[3]]}"/>',
            "    </pattern>",
            "  </defs>",
            f'  <rect id="cfa-plane" x="0" y="0" width="{spec.width}" height="{spec.height}" fill="url(#cfa)"/>',
            "</svg>",
            "",
        ]
    )
    path.write_text(svg, encoding="utf-8")
    return path


def write_hot_pixel_svg(
    spec: PixelPlaneSpec,
    path: str | Path,
    *,
    color: str = "#FFFFFF",
) -> Path:
    """Write a transparent full-plane SVG with exactly one 1x1 hot-pixel cell."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    svg = "\n".join(
        [
            _svg_header(spec.width, spec.height),
            (
                f'  <rect id="hot-pixel" x="{spec.hot_x}" y="{spec.hot_y}" '
                f'width="1" height="1" fill="{color}"/>'
            ),
            "</svg>",
            "",
        ]
    )
    path.write_text(svg, encoding="utf-8")
    return path


def _jsx_string(value: str | Path) -> str:
    text = str(value).replace("\\", "/")
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_ae_import_jsx(
    spec: PixelPlaneSpec,
    path: str | Path,
    *,
    background_path: str | Path,
    hot_pixel_path: str | Path,
    background_kind: str = "cfa",
    grayscale_background: bool = False,
    comp_name: str = "Hot Pixel Sensor",
    duration: float = 6.0,
    fps: float = 30.0,
    birth_time: float | None = None,
) -> Path:
    """Write JSX that imports the plane and exposes hot-pixel birth as a checkbox."""
    if background_kind not in {"cfa", "image"}:
        raise ValueError("background_kind must be 'cfa' or 'image'")
    if duration <= 0 or fps <= 0:
        raise ValueError("duration and fps must be positive")
    if birth_time is not None and not 0 <= birth_time <= duration:
        raise ValueError("birth_time must be inside the composition duration")

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    background_abs = Path(background_path).resolve()
    hot_abs = Path(hot_pixel_path).resolve()
    bg_name = "CFA_BACKGROUND" if background_kind == "cfa" else "IMAGE_BACKGROUND"
    grayscale_js = ""
    if grayscale_background:
        grayscale_js = '''
    var tint = bgLayer.property("ADBE Effect Parade").addProperty("ADBE Tint");
    tint.name = "Grayscale";
    tint.property("ADBE Tint-0003").setValue(100);
'''

    birth_js = '    checkbox.setValue(0);'
    if birth_time is not None:
        pre = max(0.0, birth_time - 1.0 / fps)
        birth_js = f'''
    checkbox.setValueAtTime(0, 0);
    checkbox.setValueAtTime({pre:.10g}, 0);
    checkbox.setValueAtTime({birth_time:.10g}, 1);
    for (var k = 1; k <= checkbox.numKeys; k++) {{
        checkbox.setInterpolationTypeAtKey(
            k,
            KeyframeInterpolationType.HOLD,
            KeyframeInterpolationType.HOLD
        );
    }}
'''

    jsx = f'''(function () {{
    app.beginUndoGroup("Exact Pixel Plane Handoff");

    var WIDTH = {spec.width};
    var HEIGHT = {spec.height};
    var HOT_X = {spec.hot_x};
    var HOT_Y = {spec.hot_y};
    var BG_PATH = {_jsx_string(background_abs)};
    var HOT_PATH = {_jsx_string(hot_abs)};

    function importAsset(filePath) {{
        var file = new File(filePath);
        if (!file.exists) {{
            throw new Error("File not found: " + filePath);
        }}
        var options = new ImportOptions(file);
        return app.project.importFile(options);
    }}

    function centerLayer(layer) {{
        var tr = layer.property("ADBE Transform Group");
        tr.property("ADBE Position").setValue([WIDTH / 2, HEIGHT / 2, 0]);
    }}

    var bgItem = importAsset(BG_PATH);
    var hotItem = importAsset(HOT_PATH);

    if ({str(background_kind == "image").lower()} &&
        (bgItem.width !== WIDTH || bgItem.height !== HEIGHT)) {{
        throw new Error(
            "Background image must match the declared pixel plane exactly. " +
            "Expected " + WIDTH + "x" + HEIGHT + ", got " +
            bgItem.width + "x" + bgItem.height + "."
        );
    }}

    var comp = app.project.items.addComp(
        {_jsx_string(comp_name)},
        WIDTH,
        HEIGHT,
        1.0,
        {duration:.10g},
        {fps:.10g}
    );

    var bgLayer = comp.layers.add(bgItem);
    bgLayer.name = "{bg_name}";
    bgLayer.threeDLayer = true;
    centerLayer(bgLayer);
    try {{ bgLayer.collapseTransformation = true; }} catch (e) {{}}
{grayscale_js}
    var hotLayer = comp.layers.add(hotItem);
    hotLayer.name = "HOT_PIXEL";
    hotLayer.threeDLayer = true;
    centerLayer(hotLayer);
    try {{ hotLayer.collapseTransformation = true; }} catch (e) {{}}

    var rig = comp.layers.addNull();
    rig.name = "SENSOR_RIG";
    rig.threeDLayer = true;
    rig.property("ADBE Transform Group").property("ADBE Position").setValue([WIDTH / 2, HEIGHT / 2, 0]);

    bgLayer.parent = rig;
    hotLayer.parent = rig;

    // The imported plane stays centered on the rig. The hot pixel is a hair closer
    // to the default camera to avoid coplanar 3D ambiguity.
    bgLayer.property("ADBE Transform Group").property("ADBE Position").setValue([0, 0, 0]);
    hotLayer.property("ADBE Transform Group").property("ADBE Position").setValue([0, 0, -0.01]);

    var ctrl = comp.layers.addNull();
    ctrl.name = "HOT_PIXEL_CTRL";
    ctrl.threeDLayer = false;

    var fx = ctrl.property("ADBE Effect Parade").addProperty("ADBE Checkbox Control");
    fx.name = "Hot Pixel On";
    var checkbox = fx.property(1);
{birth_js}

    hotLayer.property("ADBE Transform Group").property("ADBE Opacity").expression =
        'thisComp.layer("HOT_PIXEL_CTRL").effect("Hot Pixel On")("Checkbox") * 100';

    ctrl.comment =
        "pixel-plane {spec.width}x{spec.height}; " +
        "hot=(" + HOT_X + "," + HOT_Y + "); " +
        "coordinates are zero-based source pixels";

    ctrl.moveToBeginning();
    hotLayer.moveAfter(ctrl);

    comp.openInViewer();
    app.endUndoGroup();
}})();
'''
    path.write_text(jsx, encoding="utf-8")
    return path


def write_manifest(
    spec: PixelPlaneSpec,
    path: str | Path,
    *,
    hot_color: str,
    background_kind: str,
    background_path: str | Path,
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema": "python-scene-handoff.pixel-plane.v1",
        "width": spec.width,
        "height": spec.height,
        "pixel_count": spec.pixel_count,
        "coordinate_convention": "zero-based, top-left origin, x right, y down",
        "cfa_pattern": spec.cfa_pattern if background_kind == "cfa" else None,
        "hot_pixel": {
            "x": spec.hot_x,
            "y": spec.hot_y,
            "width": 1,
            "height": 1,
            "color": hot_color,
            "cfa_channel": spec.hot_cfa_channel if background_kind == "cfa" else None,
        },
        "background": {
            "kind": background_kind,
            "path": str(Path(background_path)),
        },
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def build_pixel_plane_package(
    output_dir: str | Path,
    *,
    spec: PixelPlaneSpec | None = None,
    background_image: str | Path | None = None,
    hot_color: str | None = None,
    grayscale_background: bool = False,
    birth_time: float | None = None,
    comp_name: str = "Hot Pixel Sensor",
    duration: float = 6.0,
    fps: float = 30.0,
) -> PixelPlanePackage:
    """Build a CFA package, or an image-backed package with the same hot-pixel overlay."""
    spec = spec or PixelPlaneSpec()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    hot_color = hot_color or ("#FF2D2D" if background_image else "#FFFFFF")
    hot_svg = write_hot_pixel_svg(spec, output_dir / "hot_pixel.svg", color=hot_color)

    if background_image is None:
        cfa_svg = write_cfa_svg(spec, output_dir / "cfa_background.svg")
        background_path = cfa_svg
        background_kind = "cfa"
    else:
        cfa_svg = None
        background_path = Path(background_image)
        background_kind = "image"

    jsx = write_ae_import_jsx(
        spec,
        output_dir / "build_in_after_effects.jsx",
        background_path=background_path,
        hot_pixel_path=hot_svg,
        background_kind=background_kind,
        grayscale_background=grayscale_background,
        comp_name=comp_name,
        duration=duration,
        fps=fps,
        birth_time=birth_time,
    )
    manifest = write_manifest(
        spec,
        output_dir / "pixel_plane.json",
        hot_color=hot_color,
        background_kind=background_kind,
        background_path=background_path,
    )
    return PixelPlanePackage(
        cfa_svg=cfa_svg,
        hot_pixel_svg=hot_svg,
        ae_jsx=jsx,
        manifest=manifest,
    )
