"""Phase 1 — material set (working values; refined at lookdev).

Created before the part gates so close-up renders read like the canon photo.
All materials are procedural; the asset is render-only.
"""

import importlib
import sys

import bpy

sys.path.insert(0, r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\golden-desert-eagle\scripts")
import de_lib  # noqa: E402

importlib.reload(de_lib)
from de_lib import save  # noqa: E402


def bsdf_of(m):
    return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


# RE-RUN SAFE: existing datablocks are updated in place (never removed), so all
# objects keep their material links while values change.


def set_in(node, name, value):
    if name in node.inputs:
        node.inputs[name].default_value = value
    else:
        print("  !! missing input", name)


def make(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.location = (60, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m, nt, b


def coord(nt, scale=1.0):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    tc.location = (-1400, 0)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.location = (-1200, 0)
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


# ---------------------------------------------------------------- gold (TiN plate)
m, nt, b = make("MAT_Gold_TitaniumGold")
set_in(b, "Base Color", (0.900, 0.560, 0.160, 1.0))
set_in(b, "Metallic", 1.0)
set_in(b, "Roughness", 0.14)
set_in(b, "IOR", 2.4)

v = coord(nt, 1.0)
noise = nt.nodes.new("ShaderNodeTexNoise")
noise.location = (-1000, 100)
noise.inputs["Scale"].default_value = 55.0
noise.inputs["Detail"].default_value = 5.0
noise.inputs["Roughness"].default_value = 0.55
nt.links.new(v, noise.inputs["Vector"])

ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.location = (-800, 100)
ramp.color_ramp.elements[0].position = 0.32
ramp.color_ramp.elements[0].color = (0.115, 0.115, 0.115, 1)
ramp.color_ramp.elements[1].position = 0.70
ramp.color_ramp.elements[1].color = (0.155, 0.155, 0.155, 1)
nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])

# broad smudge / handling layer
smudge = nt.nodes.new("ShaderNodeTexNoise")
smudge.location = (-1000, -220)
smudge.inputs["Scale"].default_value = 3.0
smudge.inputs["Detail"].default_value = 3.0
nt.links.new(v, smudge.inputs["Vector"])

sramp = nt.nodes.new("ShaderNodeValToRGB")
sramp.location = (-800, -220)
sramp.color_ramp.elements[0].position = 0.42
sramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1)
sramp.color_ramp.elements[1].position = 0.70
sramp.color_ramp.elements[1].color = (0.026, 0.026, 0.026, 1)
nt.links.new(smudge.outputs["Fac"], sramp.inputs["Fac"])

add = nt.nodes.new("ShaderNodeMixRGB")
add.location = (-560, -40)
add.blend_type = "ADD"
add.inputs["Fac"].default_value = 1.0
nt.links.new(ramp.outputs["Color"], add.inputs["Color1"])
nt.links.new(sramp.outputs["Color"], add.inputs["Color2"])
nt.links.new(add.outputs["Color"], b.inputs["Roughness"])

# crevice darkening: engraved lettering, serrations and panel gaps go dark
geo = nt.nodes.new("ShaderNodeNewGeometry")
geo.location = (-1000, 420)
pramp = nt.nodes.new("ShaderNodeValToRGB")
pramp.location = (-800, 420)
pramp.color_ramp.elements[0].position = 0.435
pramp.color_ramp.elements[0].color = (1, 1, 1, 1)
pramp.color_ramp.elements[1].position = 0.500
pramp.color_ramp.elements[1].color = (0, 0, 0, 1)
nt.links.new(geo.outputs["Pointiness"], pramp.inputs["Fac"])

mixc = nt.nodes.new("ShaderNodeMixRGB")
mixc.location = (-620, 300)
mixc.blend_type = "MIX"
mixc.inputs["Color1"].default_value = (0.900, 0.560, 0.160, 1.0)
mixc.inputs["Color2"].default_value = (0.16, 0.065, 0.012, 1.0)
nt.links.new(pramp.outputs["Color"], mixc.inputs["Fac"])
nt.links.new(mixc.outputs["Color"], b.inputs["Base Color"])

# micro orange-peel / plating grain
grain = nt.nodes.new("ShaderNodeTexNoise")
grain.location = (-1000, -480)
grain.inputs["Scale"].default_value = 420.0
grain.inputs["Detail"].default_value = 4.0
nt.links.new(v, grain.inputs["Vector"])
bump = nt.nodes.new("ShaderNodeBump")
bump.location = (-420, -420)
bump.inputs["Strength"].default_value = 0.042
bump.inputs["Distance"].default_value = 0.00008
nt.links.new(grain.outputs["Fac"], bump.inputs["Height"])

# broad plating undulation, fed under the fine grain so highlights ripple
wave = nt.nodes.new("ShaderNodeTexNoise")
wave.location = (-1000, -660)
wave.inputs["Scale"].default_value = 16.0
wave.inputs["Detail"].default_value = 2.0
nt.links.new(v, wave.inputs["Vector"])
bump2 = nt.nodes.new("ShaderNodeBump")
bump2.location = (-640, -600)
bump2.inputs["Strength"].default_value = 0.012
bump2.inputs["Distance"].default_value = 0.00010
nt.links.new(wave.outputs["Fac"], bump2.inputs["Height"])
nt.links.new(bump2.outputs["Normal"], bump.inputs["Normal"])
nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
print("gold nodes:", len(nt.nodes))

# ---------------------------------------------------------------- rubber grip
m, nt, b = make("MAT_Rubber_Grip")
set_in(b, "Base Color", (0.030, 0.031, 0.034, 1.0))
set_in(b, "Metallic", 0.0)
set_in(b, "Roughness", 0.56)
set_in(b, "Specular IOR Level", 0.35) if "Specular IOR Level" in b.inputs else None

v = coord(nt, 1.0)
vor = nt.nodes.new("ShaderNodeTexVoronoi")
vor.location = (-1000, 0)
vor.feature = "DISTANCE_TO_EDGE"
vor.voronoi_dimensions = "3D"
vor.inputs["Scale"].default_value = 1250.0
nt.links.new(v, vor.inputs["Vector"])

vramp = nt.nodes.new("ShaderNodeValToRGB")
vramp.location = (-800, 0)
vramp.color_ramp.elements[0].position = 0.02
vramp.color_ramp.elements[0].color = (0, 0, 0, 1)
vramp.color_ramp.elements[1].position = 0.20
vramp.color_ramp.elements[1].color = (1, 1, 1, 1)
nt.links.new(vor.outputs["Distance"], vramp.inputs["Fac"])

bump = nt.nodes.new("ShaderNodeBump")
bump.location = (-500, -120)
bump.inputs["Strength"].default_value = 0.55
bump.inputs["Distance"].default_value = 0.00012
nt.links.new(vramp.outputs["Color"], bump.inputs["Height"])
nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
print("rubber nodes:", len(nt.nodes))

# ---------------------------------------------------------------- supporting materials
m, nt, b = make("MAT_Steel_Bore")
set_in(b, "Base Color", (0.012, 0.012, 0.013, 1.0))
set_in(b, "Metallic", 1.0)
set_in(b, "Roughness", 0.38)

m, nt, b = make("MAT_Black_Metal")
set_in(b, "Base Color", (0.016, 0.016, 0.018, 1.0))
set_in(b, "Metallic", 0.55)
set_in(b, "Roughness", 0.40)

m, nt, b = make("MAT_Sight_Black")
set_in(b, "Base Color", (0.016, 0.016, 0.018, 1.0))
set_in(b, "Metallic", 0.65)
set_in(b, "Roughness", 0.34)

m, nt, b = make("MAT_Mark_Etch")
set_in(b, "Base Color", (0.020, 0.014, 0.008, 1.0))
set_in(b, "Metallic", 0.35)
set_in(b, "Roughness", 0.42)

m, nt, b = make("MAT_Red_Indicator")
set_in(b, "Base Color", (0.42, 0.012, 0.008, 1.0))
set_in(b, "Metallic", 0.0)
set_in(b, "Roughness", 0.30)
set_in(b, "Emission Color", (0.35, 0.01, 0.005, 1.0))
set_in(b, "Emission Strength", 0.15)

print("MATERIALS:", sorted(m.name for m in bpy.data.materials))
save()
