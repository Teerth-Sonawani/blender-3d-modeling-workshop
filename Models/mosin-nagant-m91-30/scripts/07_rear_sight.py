"""Mosin M91/30 — rebuild the rear sight leaf so the graduations actually read.

Delivered state, measured from the scene:
  SM_RearSight_Leaf      x -0.0235 .. 0.0715,  y +-0.006,  z 0.0903 .. 0.0938
  SM_RearSight_Tick_*    z 0.0896 .. 0.0908   -> *inside* the leaf, invisible
  SM_RearSight_Num*      y 0.0062 .. 0.0066   -> on the +Y flank, camera is at -Y
  SM_RearSight_Ear_L/R   x 0.070 .. 0.073     -> at the FRONT, but the sighting
                                                 notch belongs at the rear edge

Fixes:
  1. Leaf rebuilt as a plate with a U sighting notch cut into the rear edge
     (rear = -X, the end nearest the shooter's eye).
  2. The two front "ears" are removed - the notch lives in the leaf itself.
  3. All 20 ticks raised onto the leaf's top face and shortened to graduation
     length, offset to the near (-Y) side.
  4. Numerals 5 / 10 / 15 / 20 rebuilt as flat text on the top face, aligned
     with their ticks, on the far (+Y) side.
  5. Slider beveled so it reads as a machined block rather than a raw cube.

Run from Blender (MCP execute_blender_code: exec(open(path).read())).
"""
import bpy
import bmesh
import math

LEAF = "SM_RearSight_Leaf"
Z_LO, Z_HI = 0.0903, 0.0938
Z_MID = (Z_LO + Z_HI) / 2.0
THICK = Z_HI - Z_LO

# Leaf outline in XY, with the rear U-notch cut in from x = -0.0235.
OUTLINE = [(-0.0235, -0.0060), (0.0715, -0.0060), (0.0715, 0.0060),
           (-0.0235, 0.0060), (-0.0235, 0.0016), (-0.0195, 0.0016),
           (-0.0195, -0.0016), (-0.0235, -0.0016)]

TICK_Y = -0.0033
TICK_SCALE_Y = 0.40
TICK_Z = 0.0940
NUM_Y = 0.0034
NUM_SIZE = 0.0022
NUMERALS = [("5", -0.0065), ("10", 0.0131), ("15", 0.0326), ("20", 0.0520)]


def link(ob):
    for coll in ("COL_Geo", "COL_Export"):
        c = bpy.data.collections.get(coll)
        if c:
            c.objects.link(ob)
    bpy.context.scene.collection.objects.link(ob)
    root = bpy.data.objects.get("SM_MosinNagant_Root")
    if root:
        ob.parent = root
        ob.matrix_parent_inverse = root.matrix_world.inverted()


def rebuild_leaf():
    old = bpy.data.objects.get(LEAF)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)

    me = bpy.data.meshes.new(LEAF)
    bm = bmesh.new()
    verts = [bm.verts.new((x, y, Z_MID)) for x, y in OUTLINE]
    bm.faces.new(verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.validate()

    ob = bpy.data.objects.new(LEAF, me)
    link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    solid = ob.modifiers.new("Solidify", 'SOLIDIFY')
    solid.thickness = THICK
    solid.offset = 0.0
    solid.use_even_offset = True
    bpy.ops.object.modifier_apply(modifier=solid.name)

    bev = ob.modifiers.new("Bevel", 'BEVEL')
    bev.width = 0.00025
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    bev.angle_limit = 0.52
    bpy.ops.object.modifier_apply(modifier=bev.name)

    mat = bpy.data.materials.get("MAT_Steel_Blued")
    if mat:
        ob.data.materials.append(mat)
    ob.select_set(False)
    return ob


def lift_ticks():
    moved = 0
    for i in range(1, 21):
        ob = bpy.data.objects.get("SM_RearSight_Tick_%02d" % i)
        if not ob:
            continue
        ob.scale.y = TICK_SCALE_Y
        ob.location.y = TICK_Y
        ob.location.z = TICK_Z
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        ob.select_set(False)
        moved += 1
    return moved


def remove_old_numerals():
    gone = []
    for name in ("SM_RearSight_Num5", "SM_RearSight_Num10",
                 "SM_RearSight_Num15", "SM_RearSight_Num20",
                 "SM_RearSight_Ear_L", "SM_RearSight_Ear_R"):
        ob = bpy.data.objects.get(name)
        if ob:
            gone.append(name)
            bpy.data.objects.remove(ob, do_unlink=True)
    return gone


def build_numerals():
    made = []
    mat = bpy.data.materials.get("MAT_Steel_Marked")
    for text, x in NUMERALS:
        cu = bpy.data.curves.new("TMP_Num" + text, type='FONT')
        cu.body = text
        cu.size = NUM_SIZE
        cu.extrude = 0.00018
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        ob = bpy.data.objects.new("SM_RearSight_Num" + text, cu)
        bpy.context.scene.collection.objects.link(ob)
        ob.location = (x, NUM_Y, Z_HI + 0.0001)
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.convert(target='MESH')
        ob = bpy.context.view_layer.objects.active
        ob.name = "SM_RearSight_Num" + text
        if mat:
            ob.data.materials.clear()
            ob.data.materials.append(mat)
        root = bpy.data.objects.get("SM_MosinNagant_Root")
        if root:
            ob.parent = root
            ob.matrix_parent_inverse = root.matrix_world.inverted()
        for coll in ("COL_Geo", "COL_Export"):
            c = bpy.data.collections.get(coll)
            if c:
                c.objects.link(ob)
        ob.select_set(False)
        made.append((ob.name, sum(len(p.vertices) - 2 for p in ob.data.polygons)))
    return made


def bevel_slider():
    ob = bpy.data.objects.get("SM_RearSight_Slider")
    if not ob:
        return None
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bev = ob.modifiers.new("Bevel", 'BEVEL')
    bev.width = 0.0004
    bev.segments = 2
    bev.limit_method = 'ANGLE'
    bev.angle_limit = 0.52
    bpy.ops.object.modifier_apply(modifier=bev.name)
    ob.select_set(False)
    return ob.name


leaf = rebuild_leaf()
moved = lift_ticks()
gone = remove_old_numerals()
made = build_numerals()
slider = bevel_slider()

result = {
    "leaf_tris": sum(len(p.vertices) - 2 for p in leaf.data.polygons),
    "leaf_dims_mm": [round(d * 1000, 2) for d in leaf.dimensions],
    "ticks_lifted": moved,
    "removed": gone,
    "numerals": made,
    "slider": slider,
}
print("REAR SIGHT:", result)
