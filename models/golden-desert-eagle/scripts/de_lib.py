"""Shared bpy helpers for golden-desert-eagle.

Operator-free by design: geometry is built with bmesh, booleans are evaluated
through the depsgraph, shading is done with bmesh flags. This keeps every call
inside the MCP sandbox's allowed API surface.

Import from a phase script:
    import sys, importlib
    sys.path.insert(0, SCRIPTS)
    import de_lib; importlib.reload(de_lib)
    from de_lib import *
"""

from __future__ import annotations

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = r"C:\Teerth Stuff\Games Stuff\projects\3dmodels\Models\golden-desert-eagle"
SCRIPTS = os.path.join(ROOT, "scripts")
RENDERS = os.path.join(ROOT, "renders")
EXPORTS = os.path.join(ROOT, "exports")
VERSIONS = os.path.join(ROOT, "versions")
BLEND = os.path.join(ROOT, "golden-desert-eagle.blend")


# --------------------------------------------------------------------------- scene


def col(name: str):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def clear_collection(name: str) -> None:
    for ob in list(col(name).objects):
        data = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if data and data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)


def save(path: str = BLEND) -> str:
    bpy.ops.wm.save_as_mainfile(filepath=path)
    return bpy.data.filepath


# --------------------------------------------------------------------------- materials


def mat(name: str):
    return bpy.data.materials.get(name)


def principled(name: str, base, metallic=0.0, rough=0.5, **kw):
    """Create or fetch a Principled material (inputs by name, type-based lookup)."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
        m.use_nodes = True
        bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Base Color"].default_value = (*base, 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = rough
        for key, val in kw.items():
            if key in bsdf.inputs:
                bsdf.inputs[key].default_value = val
    return m


# --------------------------------------------------------------------------- mesh core


def _finish(bm: bmesh.types.BMesh, sharp_angle=32.0) -> None:
    bmesh.ops.dissolve_degenerate(bm, dist=1.5e-6, edges=list(bm.edges))
    bm.normal_update()
    thr = math.radians(sharp_angle)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) <= thr
        else:
            e.smooth = False


def bevel_edges(bm, edges, width, segments=2, clamp=True):
    if not edges:
        return
    bmesh.ops.bevel(
        bm,
        geom=list(edges),
        offset=width,
        offset_type="OFFSET",
        segments=segments,
        profile=0.5,
        affect="EDGES",
        clamp_overlap=clamp,
        loop_slide=True,
    )


def clean_materials(ob, fallback=None):
    """Booleans can leave empty (None) material slots; fill them."""
    me = ob.data
    if fallback is None:
        fallback = next((m for m in me.materials if m is not None), None)
    if fallback is None:
        return ob
    for i in range(len(me.materials)):
        if me.materials[i] is None:
            me.materials[i] = fallback
    if len(me.materials) == 0:
        me.materials.append(fallback)
    return ob


def make_object(name, bm, collection, material=None, sharp_angle=32.0, bevel=None,
                bevel_segments=2):
    """bmesh -> object. Optional general bevel applied before shading."""
    if bevel:
        bevel_edges(bm, bm.edges, bevel, bevel_segments)
    _finish(bm, sharp_angle)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    col(collection).objects.link(ob)
    if material is not None:
        me.materials.append(material)
    return ob


def profile(name, pts_xz, width, collection, material=None, y_center=0.0,
            bevel=0.0, bevel_segments=2, sharp_angle=32.0):
    """Extrude a closed XZ polygon symmetrically along Y."""
    bm = bmesh.new()
    n = len(pts_xz)
    a = [bm.verts.new((x, y_center - width / 2.0, z)) for x, z in pts_xz]
    b = [bm.verts.new((x, y_center + width / 2.0, z)) for x, z in pts_xz]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([a[i], a[j], b[j], b[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return make_object(name, bm, collection, material, sharp_angle, bevel, bevel_segments)


def box(name, x0, x1, y0, y1, z0, z1, collection, material=None, bevel=0.0,
        bevel_segments=2, sharp_angle=32.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = z0 if v.co.z < 0 else z1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return make_object(name, bm, collection, material, sharp_angle, bevel, bevel_segments)


def cylinder(name, radius, depth, center, axis, collection, material=None,
             segments=48, bevel=0.0, bevel_segments=2, sharp_angle=32.0,
             radius2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=segments,
        radius1=radius,
        radius2=radius if radius2 is None else radius2,
        depth=depth,
    )
    if axis == "X":
        rot = Matrix.Rotation(math.radians(90), 4, "Y")
    elif axis == "Y":
        rot = Matrix.Rotation(math.radians(90), 4, "X")
    else:
        rot = Matrix.Identity(4)
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return make_object(name, bm, collection, material, sharp_angle, bevel, bevel_segments)


def rounded_rect(x0, x1, z0, z1, r, n=6):
    """Closed XZ polygon of a rounded rectangle, CCW starting bottom-left."""
    pts = []
    corners = [
        (x0 + r, z0 + r, 180, 270),
        (x1 - r, z0 + r, 270, 360),
        (x1 - r, z1 - r, 0, 90),
        (x0 + r, z1 - r, 90, 180),
    ]
    for cx, cz, a0, a1 in corners:
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def arc(cx, cz, r, a0_deg, a1_deg, n=8):
    return [
        (cx + r * math.cos(math.radians(a0_deg + (a1_deg - a0_deg) * i / n)),
         cz + r * math.sin(math.radians(a0_deg + (a1_deg - a0_deg) * i / n)))
        for i in range(n + 1)
    ]


# --------------------------------------------------------------------------- boolean


def boolean(target, cutter, operation="DIFFERENCE"):
    """Apply a boolean with modifier_apply (verified working in this sandbox).

    The depsgraph-copy route returns an uncut mesh on this build, so the operator
    is the reliable path. Removes the cutter afterwards.
    """
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    for c in target.users_collection:
        c.hide_viewport = False
    for c in cutter.users_collection:
        c.hide_viewport = False
    for ob in list(bpy.context.selected_objects):
        ob.select_set(False)
    bpy.context.view_layer.objects.active = target
    target.select_set(True)

    before = (len(target.data.vertices), len(target.data.polygons))
    mod = target.modifiers.new("bool", "BOOLEAN")
    mod.operation = operation
    mod.object = cutter
    mod.solver = "EXACT"
    bpy.context.view_layer.update()
    applied = True
    try:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    except Exception as exc:
        applied = False
        print("  !! modifier_apply failed:", exc)
        if mod.name in [m.name for m in target.modifiers]:
            target.modifiers.remove(mod)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = target.evaluated_get(dg)
        new_me = bpy.data.meshes.new_from_object(ev, depsgraph=dg)
        old = target.data
        target.data = new_me
        if old.users == 0:
            bpy.data.meshes.remove(old)
    after = (len(target.data.vertices), len(target.data.polygons))
    print(f"  boolean {cutter.name}{'' if applied else ' (fallback)'}: "
          f"{before[0]}v/{before[1]}f -> {after[0]}v/{after[1]}f")
    if after == before:
        print("  WARNING: boolean produced no topology change")
    clean_materials(target)

    cme = cutter.data
    bpy.data.objects.remove(cutter, do_unlink=True)
    if cme.users == 0:
        bpy.data.meshes.remove(cme)

    # keep shading flags consistent after the boolean rebuild
    for p in target.data.polygons:
        p.use_smooth = True
    thr = math.radians(32.0)
    import bmesh as _bm

    bm = _bm.new()
    bm.from_mesh(target.data)
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) <= thr
        else:
            e.smooth = False
    bm.to_mesh(target.data)
    bm.free()
    return target


def comb(name, x_positions, width, z0, z1, y0, y1, collection, slant_deg=0.0,
         cx=0.0, cz=0.0):
    """One mesh holding several thin boxes (a cutter comb)."""
    bm = bmesh.new()
    for x in x_positions:
        bmesh.ops.create_cube(bm, size=1.0)
        new = [v for v in bm.verts if not v.tag]
        for v in new:
            v.tag = True
            v.co.x = x - width / 2.0 if v.co.x < 0 else x + width / 2.0
            v.co.y = y0 if v.co.y < 0 else y1
            v.co.z = z0 if v.co.z < 0 else z1
    if slant_deg:
        m = Matrix.Rotation(math.radians(slant_deg), 4, "Y")
        for v in bm.verts:
            v.co = m @ (v.co - Vector((cx, 0, cz))) + Vector((cx, 0, cz))
    for v in bm.verts:
        v.tag = False
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return make_object(name, bm, collection, bevel=0.0)


def join(objects, name):
    """Join a list of objects into the first one (bmesh merge, no operators).

    Preserves the material list of every source object and remaps face indices.
    """
    objects = [o for o in objects if o is not None]
    target = objects[0]
    mats = []
    for ob in objects:
        for m in ob.data.materials:
            if m not in mats:
                mats.append(m)
    bm = bmesh.new()
    offset = 0
    for ob in objects:
        tmp = bmesh.new()
        tmp.from_mesh(ob.data)
        tmp.transform(ob.matrix_world)
        idxs = [f.material_index for f in tmp.faces]
        me = bpy.data.meshes.new("tmp_join")
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        remap = [mats.index(m) for m in ob.data.materials] or [0]
        faces = list(bm.faces)[offset:]
        for f, mi in zip(faces, idxs):
            f.material_index = remap[mi] if mi < len(remap) else 0
        offset = len(bm.faces)
    target.data = bpy.data.meshes.new(name)
    bm.to_mesh(target.data)
    bm.free()
    # vertices were baked into world space above: the object transform must go
    target.matrix_world = Matrix.Identity(4)
    target.data.materials.clear()
    for m in mats:
        target.data.materials.append(m)
    target.name = name
    target.data.name = name
    clean_materials(target)
    for ob in objects[1:]:
        data = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if data.users == 0:
            bpy.data.meshes.remove(data)
    # re-apply shading flags
    for p in target.data.polygons:
        p.use_smooth = True
    thr = math.radians(32.0)
    bm = bmesh.new()
    bm.from_mesh(target.data)
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) <= thr
        else:
            e.smooth = False
    bm.to_mesh(target.data)
    bm.free()
    return target


def text_to_mesh(name, body, size, loc, rot, extrude, spacing, collection,
                 target_width=None):
    """FONT curve -> mesh object (for engraving booleans).

    target_width compresses the run direction so a mark lands on its measured
    width from the canon (Bfont is much wider per glyph than the engraved font).
    """
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = extrude
    cu.space_character = spacing
    cu.resolution_u = 6
    ob = bpy.data.objects.new(name, cu)
    col(collection).objects.link(ob)
    ob.location = loc
    ob.rotation_euler = rot
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), depsgraph=dg)
    if target_width and len(me.vertices) > 1:
        xs = [v.co.x for v in me.vertices]
        span = max(xs) - min(xs)
        if span > 1e-9:
            s = target_width / span
            for v in me.vertices:
                v.co.x *= s
            print(f"  text {name}: x-scaled {s:.3f} -> {target_width*1000:.1f}mm wide")
    mob = bpy.data.objects.new(name, me)
    col(collection).objects.link(mob)
    mob.matrix_world = ob.matrix_world.copy()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.curves.remove(cu)
    return mob


def place_engraving(ob, surface_y, depth=0.00022, side=1):
    """Shift a text cutter in Y so it crosses the surface by exactly `depth`."""
    bpy.context.view_layer.update()
    ys = [(ob.matrix_world @ v.co).y for v in ob.data.vertices]
    xs = [(ob.matrix_world @ v.co).x for v in ob.data.vertices]
    if side > 0:
        shift = (surface_y - depth) - min(ys)
    else:
        shift = (surface_y + depth) - max(ys)
    ob.location.y += shift
    bpy.context.view_layer.update()
    print(
        f"  engraving {ob.name}: x {min(xs)*1000:.1f}..{max(xs)*1000:.1f}mm "
        f"y {min(ys)*1000:.3f}..{max(ys)*1000:.3f}mm shift {shift*1000:+.3f}mm"
    )
    return ob


# --------------------------------------------------------------------------- audit


def tri_count(ob):
    me = ob.data
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def bbox(ob):
    """Accurate world-space bounds from mesh vertices (bound_box can be stale)."""
    mw = ob.matrix_world
    if ob.type == "MESH" and len(ob.data.vertices) > 0:
        co = [(mw @ v.co) for v in ob.data.vertices]
        xs = [p.x for p in co]
        ys = [p.y for p in co]
        zs = [p.z for p in co]
        return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))
    pts = [mw @ Vector(c) for c in ob.bound_box]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    return (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def report(ob):
    (x0, x1), (y0, y1), (z0, z1) = bbox(ob)
    print(
        f"{ob.name}: tris={tri_count(ob)} "
        f"width={(y1 - y0) * 1000:.1f}mm "
        f"length={(x1 - x0) * 1000:.1f}mm height={(z1 - z0) * 1000:.1f}mm"
    )
    print(
        f"  bbox X {x0 * 1000:.1f}..{x1 * 1000:.1f}  "
        f"Y {y0 * 1000:.1f}..{y1 * 1000:.1f}  Z {z0 * 1000:.1f}..{z1 * 1000:.1f}"
    )
    return x0, x1, y0, y1, z0, z1


def mesh_health(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    loose_v = sum(1 for v in bm.verts if not v.link_edges)
    loose_e = sum(1 for e in bm.edges if not e.link_faces)
    nonman = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    interior = sum(1 for f in bm.faces if f.calc_area() < 1e-10)
    print(
        f"  health: loose_verts={loose_v} loose_edges={loose_e} "
        f"non_manifold_edges={nonman} degenerate_faces={interior}"
    )
    bm.free()


def solid_bounds(objs):
    """World-space bounds over a list of objects."""
    xs, ys, zs = [], [], []
    for ob in objs:
        (x0, x1), _, _ = bbox(ob)
        xs += [x0, x1]
        _, (y0, y1), _ = bbox(ob)
        ys += [y0, y1]
        _, _, (z0, z1) = bbox(ob)
        zs += [z0, z1]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
