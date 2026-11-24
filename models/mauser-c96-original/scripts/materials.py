"""Procedural PBR look-dev for the C96 materials (runs inside Blender via MCP)."""
import bpy
import os

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\models\mauser-c96-original"
BLEND = os.path.join(ROOT, "mauser-c96-original.blend")


def prep(name):
    m = bpy.data.materials.get(name)
    if m is None:
        print("MISSING MATERIAL", name)
        return None, None
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL"):
            nt.nodes.remove(n)
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    return nt, bsdf


def ramp(nt, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    el = r.color_ramp.elements
    while len(el) > 1:
        el.remove(el[-1])
    el[0].position = stops[0][0]
    el[0].color = (*stops[0][1], 1.0)
    for pos, col in stops[1:]:
        e = el.new(pos)
        e.color = (*col, 1.0)
    return r


def noise(nt, scale, detail=6.0, rough=0.6, dist=0.0):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    if "Roughness" in n.inputs:
        n.inputs["Roughness"].default_value = rough
    if "Distortion" in n.inputs:
        n.inputs["Distortion"].default_value = dist
    return n


def setup_steel(name, base_dark, base_mid, base_light, rough_lo, rough_hi,
                bump_scale, bump_strength, bump_dist):
    nt, b = prep(name)
    if not nt:
        return
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = noise(nt, 190.0, 5.0, 0.55, 0.04)
    c1 = ramp(nt, [(0.20, base_dark), (0.58, base_mid), (0.92, base_light)])
    rr = ramp(nt, [(0.0, (rough_lo,) * 3), (1.0, (rough_hi,) * 3)])
    n2 = noise(nt, bump_scale, 3.0, 0.5)
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump_strength
    bp.inputs["Distance"].default_value = bump_dist
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], c1.inputs["Fac"])
    nt.links.new(c1.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(n1.outputs["Fac"], rr.inputs["Fac"])
    nt.links.new(rr.outputs["Color"], b.inputs["Roughness"])
    nt.links.new(n2.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Metallic"].default_value = 1.0
    print("steel ok", name)


setup_steel("MAT_Metal_Blued_Steel",
            (0.027, 0.029, 0.036), (0.036, 0.038, 0.047), (0.052, 0.055, 0.066),
            0.26, 0.38, 900.0, 0.03, 0.00006)
setup_steel("MAT_Metal_Polished_Highlights",
            (0.29, 0.29, 0.305), (0.36, 0.36, 0.375), (0.46, 0.46, 0.475),
            0.11, 0.19, 900.0, 0.035, 0.00005)

# ------------------------------------------------------------------ walnut
nt, b = prep("MAT_Wood_Walnut_Grip")
if nt:
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (22.0, 4.0, 0.06)
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "BANDS"
    try:
        wave.bands_direction = "X"
    except Exception:
        pass
    wave.inputs["Scale"].default_value = 5.0
    wave.inputs["Distortion"].default_value = 3.0
    wave.inputs["Detail"].default_value = 2.0
    if "Detail Scale" in wave.inputs:
        wave.inputs["Detail Scale"].default_value = 1.6
    c1 = ramp(nt, [(0.00, (0.023, 0.0105, 0.0050)),
                   (0.42, (0.038, 0.0170, 0.0078)),
                   (0.72, (0.057, 0.0265, 0.0122)),
                   (1.00, (0.085, 0.0410, 0.0190))])
    rr = ramp(nt, [(0.0, (0.42, 0.42, 0.42)), (1.0, (0.62, 0.62, 0.62))])
    bp = nt.nodes.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.10
    bp.inputs["Distance"].default_value = 0.00025
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], c1.inputs["Fac"])
    nt.links.new(c1.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(wave.outputs["Fac"], rr.inputs["Fac"])
    nt.links.new(rr.outputs["Color"], b.inputs["Roughness"])
    nt.links.new(wave.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Metallic"].default_value = 0.0
    print("wood ok")

# ------------------------------------------------------------------ bore
nt, b = prep("MAT_Metal_Bore_Shadow")
if nt:
    b.inputs["Base Color"].default_value = (0.008, 0.008, 0.009, 1.0)
    b.inputs["Metallic"].default_value = 0.5
    b.inputs["Roughness"].default_value = 0.82
    print("bore ok")

for m in bpy.data.materials:
    if m.name.startswith("MAT_Metal_Blued"):
        m.diffuse_color = (0.05, 0.05, 0.06, 1)
    elif m.name.startswith("MAT_Wood"):
        m.diffuse_color = (0.10, 0.05, 0.025, 1)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print("SAVED", BLEND)
