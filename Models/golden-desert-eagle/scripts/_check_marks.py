import bpy
for ob in bpy.data.collections["COL_Part_Marks"].objects:
    xs = [(ob.matrix_world @ v.co).x for v in ob.data.vertices]
    print(ob.name, "x", round(min(xs)*1000,1), "..", round(max(xs)*1000,1),
          "loc", [round(c*1000,1) for c in ob.location])
