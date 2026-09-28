# Architecture

The project separates numerical/procedural motion from DCC finishing.

```text
Python numerical / procedural source
                ↓
         sampled scene state
                ↓
     Scene / Node / TranslationTrack
          ↙                 ↘
   glTF exporter         USD exporter
        ↓                    ↓
After Effects         Resolve / Fusion
```

The common layer is intentionally small. It stores only the geometry, hierarchy, materials needed by the current examples, and sampled transform tracks.

## Why a common scene layer?

The source of motion should not matter. A track may come from an ODE solver, NumPy, SciPy, a Manim adapter, a VTK/PyVista computation, or custom Python code. Once sampled, the exporters consume the same scene state.

This keeps DCC-specific interchange details outside the numerical model.

## Why both glTF and USD?

They are two useful handoff targets with different ecosystems.

- glTF provides a compact animated 3D asset that works well with the tested After Effects workflow.
- USD provides a time-sampled scene representation that works well with the tested Resolve/Fusion workflow and other USD-aware tools.

The common scene representation is not intended to become a new universal scene description. If the project grows toward rich materials, cameras, lights, references, variants, deformation, instancing, and larger composition graphs, OpenUSD itself should be considered as a canonical representation rather than reimplemented here.

## Current time model

The source motion is sampled at the scene frame rate. The glTF exporter writes dense transform samples, and the USD exporter writes the same samples as USD time samples.

This makes the numerical state shared while allowing each target format to encode it in its native way.
