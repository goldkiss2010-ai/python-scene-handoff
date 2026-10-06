# Exact pixel-plane handoff

This is a lightweight 2D handoff for sensor/image diagrams where source-pixel
coordinates matter more than rich 3D geometry.

The default scene is a square 4 MP sensor plane:

- width: 2000 px
- height: 2000 px
- Bayer CFA: RGGB
- hot pixel: (1000, 1000), zero-based
- hot-pixel extent: exactly 1 x 1 source pixel

The CFA background and the hot pixel are separate SVG files. The CFA SVG uses
one repeating 2 x 2 pattern rather than four million explicit rectangles, so
the source stays compact while the coordinate system remains exact.

## CFA mode

Run:

```powershell
uv run python examples/03_hot_pixel_sensor.py --birth 2
```

This writes:

```text
output/hot_pixel_sensor/
  cfa_background.svg
  hot_pixel.svg
  build_in_after_effects.jsx
  pixel_plane.json
```

Open After Effects, then run `build_in_after_effects.jsx` from
`File > Scripts > Run Script File...`.

The generated composition contains:

- `CFA_BACKGROUND`
- `HOT_PIXEL`
- `SENSOR_RIG`
- `HOT_PIXEL_CTRL`

`HOT_PIXEL_CTRL > Hot Pixel On` drives the opacity of the separate
`HOT_PIXEL` layer. If `--birth` is supplied, HOLD keys are created so the
pixel appears instantaneously.

The two SVGs use the same full-plane viewBox, so the overlay is aligned by
source-pixel coordinates rather than by eye.

## Image mode

The same one-pixel overlay can be placed over a real image:

```powershell
uv run python examples/03_hot_pixel_sensor.py \
  --width 2000 \
  --height 2000 \
  --image D:/images/source.png \
  --grayscale \
  --hot-color "#FF0000" \
  --birth 2
```

The image dimensions must exactly match the declared plane. The generated JSX
checks this in After Effects and aborts on a mismatch instead of silently
rescaling the image.

With `--grayscale`, AE applies Tint only to `IMAGE_BACKGROUND`; the
separate `HOT_PIXEL` layer remains red.

## Coordinate convention

Coordinates are:

- zero-based
- origin at top-left
- x increases rightward
- y increases downward

For an RGGB pattern:

```text
R G
G B
```

the CFA phase under any hot pixel is therefore determined directly from
`(x mod 2, y mod 2)` and is recorded in `pixel_plane.json`.

## Why SVG here?

Recent After Effects versions can import SVG as continuously rasterizable
vector footage or as editable shape-layer compositions. For this use case the
single-layer footage path is preferable: the CFA stays one compact background
object, while the hot pixel remains a separate layer that can be switched,
animated, recolored, or replaced independently.
