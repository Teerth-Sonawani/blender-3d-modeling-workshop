# Procedural-only delivery

This model ships no image textures. Blued steel, polished wear and walnut grain live in the
Blender node graphs, so the GLB/FBX carry flat PBR factors only.

Consequence: the look does not survive export. This asset is a portfolio/render delivery, not
an engine-ready one, despite the brief's "unreal/unity ready" line. Baking BC/N/R/M here is
the fix if it needs to ship.
