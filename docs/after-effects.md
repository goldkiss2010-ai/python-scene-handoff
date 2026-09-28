# After Effects handoff

The glTF backend writes animated node transforms into a normal glTF scene that can be imported into After Effects as a real 3D model.

## Export

```powershell
uv sync
uv run python examples/02_lorenz_butterfly.py
```

Import `output/lorenz_butterfly.gltf` into After Effects and select the embedded animation:

```text
Animation Options -> Name -> Lorenz_Butterfly_Flow
```

The mathematical motion is baked into the asset. Camera work, lighting, typography, compositing, and finishing remain editable in After Effects.

## Current authored subset

- polygon mesh geometry;
- display color and opacity;
- hierarchy;
- sampled translation animation.
