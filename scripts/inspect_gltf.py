from __future__ import annotations

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("path", type=Path)
args = parser.parse_args()

with args.path.open("r", encoding="utf-8") as f:
    gltf = json.load(f)

print("SCENES")
for i, scene in enumerate(gltf.get("scenes", [])):
    print(i, scene)

print("\nNODES")
for i, node in enumerate(gltf.get("nodes", [])):
    print(i, "name=", node.get("name"), "mesh=", node.get("mesh"), "children=", node.get("children"))

print("\nANIMATIONS")
for i, animation in enumerate(gltf.get("animations", [])):
    print(i, animation.get("name"), "channels=", len(animation.get("channels", [])))
