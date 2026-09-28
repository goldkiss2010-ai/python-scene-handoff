# Related work

The problem is not new: scientific and numerical tools are good at computation, while DCC tools are good at final visual presentation. Several projects approach that boundary from different directions.

## pyvista-blender

https://github.com/kmarchais/pyvista-blender

Build a scene in PyVista and render or export it through Blender. Its current API includes animation baking to native `.blend` files, cameras, lights, deformation and scalar animation. This is the closest contemporary example of the same broad division of labor, but it intentionally targets Blender directly.

## BVTKNodes

https://github.com/tkeskita/BVtkNodes

A Blender add-on that brings VTK pipelines into Blender's node environment and converts scientific data to Blender geometry. This solves the boundary from the DCC side.

## OpenUSD

https://openusd.org/

A general scene description and composition system with time-sampled attributes. The project here should not grow into an accidental reimplementation of USD.

## usd2gltf

https://github.com/mikelyndon/usd2gltf

A USD-to-glTF converter supporting meshes, cameras, lights, animated transforms and animation. It demonstrates that USD and glTF can be complementary interchange targets rather than competing internal abstractions.

## Position of this proof of concept

```text
BVTKNodes:        scientific stack inside Blender
pyvista-blender:  PyVista scene -> Blender
this project:     Python time-varying scene -> standard interchange -> DCC
```

The distinction is deliberately narrow: keep computation and procedural motion in Python, and postpone the choice of finishing DCC.
