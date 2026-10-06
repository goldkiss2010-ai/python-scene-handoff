from __future__ import annotations

import argparse
from pathlib import Path

from python_scene_handoff.pixel_plane import PixelPlaneSpec, build_pixel_plane_package


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an exact 2D pixel-plane handoff for After Effects."
    )
    parser.add_argument("--width", type=int, default=2000)
    parser.add_argument("--height", type=int, default=2000)
    parser.add_argument("--hot-x", type=int, default=None)
    parser.add_argument("--hot-y", type=int, default=None)
    parser.add_argument(
        "--pattern",
        default="RGGB",
        help="2x2 CFA pattern in row-major order, e.g. RGGB/BGGR/GRBG/GBRG.",
    )
    parser.add_argument(
        "--image",
        type=Path,
        default=None,
        help="Optional background image. If omitted, an RGGB CFA SVG is generated.",
    )
    parser.add_argument(
        "--grayscale",
        action="store_true",
        help="Apply AE Tint to the imported image background. Hot pixel remains colored.",
    )
    parser.add_argument(
        "--hot-color",
        default=None,
        help="SVG color such as #FFFFFF, #FFFF00, or #FF0000. "
        "Defaults to white for CFA and red for image mode.",
    )
    parser.add_argument(
        "--birth",
        type=float,
        default=None,
        help="Optional hot-pixel birth time in seconds. Creates HOLD checkbox keys.",
    )
    parser.add_argument("--duration", type=float, default=6.0)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/hot_pixel_sensor"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    spec = PixelPlaneSpec(
        width=args.width,
        height=args.height,
        hot_x=args.hot_x,
        hot_y=args.hot_y,
        cfa_pattern=args.pattern,
    )

    package = build_pixel_plane_package(
        args.output,
        spec=spec,
        background_image=args.image,
        hot_color=args.hot_color,
        grayscale_background=args.grayscale,
        birth_time=args.birth,
        duration=args.duration,
        fps=args.fps,
    )

    print(f"pixel plane: {spec.width} x {spec.height} = {spec.pixel_count:,} pixels")
    print(f"hot pixel: ({spec.hot_x}, {spec.hot_y})")
    if package.cfa_svg is not None:
        print(f"CFA SVG: {package.cfa_svg}")
        print(f"underlying CFA channel: {spec.hot_cfa_channel}")
    else:
        print(f"background image: {args.image}")
    print(f"hot-pixel SVG: {package.hot_pixel_svg}")
    print(f"AE builder: {package.ae_jsx}")
    print(f"manifest: {package.manifest}")


if __name__ == "__main__":
    main()
