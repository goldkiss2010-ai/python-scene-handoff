# Resolve / Fusion handoff

The USD backend writes the same sampled scene state as an animated USD scene for Resolve/Fusion and other USD-aware tools.

## Export

Install the OpenUSD dependency:

```powershell
uv sync --extra usd
```

Then run an example. A `.usda` file is emitted alongside the glTF.

## Minimal Fusion setup

1. Open the Fusion page.
2. Add a `uLoader` and select the generated `.usda` file.
3. Connect it into a `uMerge` and then a `uRenderer`.
4. Connect the renderer to `MediaOut`.

A `uTransform` can be inserted after `uLoader` when you want to rotate, move, or scale the imported scene. Camera and light nodes can be added to the USD scene through `uMerge` as needed.

## Current authored subset

- polygon mesh geometry;
- display color and opacity;
- Xform hierarchy;
- translation time samples;
- stage fps / timeCodesPerSecond.
