"""Streetak hero ball, rendered in Blender (bpy) for the landing page.

A truncated icosahedron (12 black pentagons, 20 white hexagons) with stitched seams,
inflated to a sphere, lit like a floodlit night match: a warm key, a gold rim and a
red rim (the team colours). Transparent background, so the page can float it.

usage: python3 ball.py OUT_DIR [size] [samples] [frames]
"""
import math
import sys

import bpy  # first: it puts bmesh and mathutils on the path
import bmesh
from mathutils import Euler, Vector

out = sys.argv[1]
size = int(sys.argv[2]) if len(sys.argv) > 2 else 1200
samples = int(sys.argv[3]) if len(sys.argv) > 3 else 96
frames = int(sys.argv[4]) if len(sys.argv) > 4 else 1
# ALBEDO: flat emission colours, no lights: the panels only, to be relit with a scene's own light (fix_balls.py)
import os
ALBEDO = os.environ.get("ALBEDO") == "1"
SEED = int(os.environ.get("SEED", "0"))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---- the ball: icosahedron -> truncate the vertices -> inset each panel for the seams
mesh = bpy.data.meshes.new("Ball")
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=0, radius=1.0)
bmesh.ops.bevel(bm, geom=list(bm.verts), offset=100 / 3, offset_type="PERCENT", affect="VERTICES", segments=1)
panels = list(bm.faces)
kinds = {f: (0 if len(f.verts) == 5 else 1) for f in panels}
res = bmesh.ops.inset_individual(bm, faces=panels, thickness=0.014, depth=-0.018, use_even_offset=True)
for f in bm.faces:
    f.material_index = kinds.get(f, 2)  # 0 black panel, 1 white panel, 2 seam
for f in res["faces"]:
    f.material_index = 2
bm.to_mesh(mesh)
bm.free()

ball = bpy.data.objects.new("Ball", mesh)
scene.collection.objects.link(ball)
sub = ball.modifiers.new("sub", "SUBSURF")
sub.subdivision_type = "SIMPLE"  # keep the panels' shape; only add points for the cast
sub.levels = sub.render_levels = 4
cast = ball.modifiers.new("cast", "CAST")
cast.factor = 1.0
cast.use_radius_as_size = False
sub2 = ball.modifiers.new("sub2", "SUBSURF")
sub2.levels = sub2.render_levels = 1
for p in mesh.polygons:
    p.use_smooth = True


def mat(name, color, rough, coat=0.0, bump=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    if ALBEDO:
        nt = m.node_tree
        for n in list(nt.nodes):
            if n.type != "OUTPUT_MATERIAL":
                nt.nodes.remove(n)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*color, 1)
        nt.links.new(em.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])
        return m
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = 0.25
    if bump:
        # fine pebbled synthetic-leather grain + a few scuffs
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 420.0
        tex.inputs["Detail"].default_value = 6.0
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        b.inputs["Distance"].default_value = 0.002
        nt.links.new(tex.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])
        scuff = nt.nodes.new("ShaderNodeTexNoise")
        scuff.inputs["Scale"].default_value = 9.0
        scuff.inputs["Detail"].default_value = 10.0
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.58
        ramp.color_ramp.elements[0].color = (*color, 1)
        ramp.color_ramp.elements[1].position = 0.72
        ramp.color_ramp.elements[1].color = tuple(c * 0.78 for c in color) + (1,)
        nt.links.new(scuff.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    return m


mesh.materials.append(mat("Black", (0.012, 0.012, 0.016), 0.42, coat=0.35, bump=0.25))
mesh.materials.append(mat("White", (0.86, 0.85, 0.82), 0.38, coat=0.4, bump=0.25))
mesh.materials.append(mat("Seam", (0.02, 0.02, 0.025), 0.9))

# ---- floodlit night lighting
def area(name, loc, energy, color, size_):
    l = bpy.data.lights.new(name, "AREA")
    l.energy = energy
    l.color = color
    l.size = size_
    o = bpy.data.objects.new(name, l)
    o.location = loc
    d = Vector((0, 0, 0)) - Vector(loc)
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(o)
    return o


area("Key", (2.6, -3.2, 3.4), 1400, (1.0, 0.93, 0.82), 2.2)       # floodlight, warm
area("RimGold", (-3.2, 1.6, 1.4), 1800, (1.0, 0.72, 0.30), 1.2)   # lantern-gold rim
area("RimRed", (3.0, 2.6, -0.6), 1500, (1.0, 0.22, 0.16), 1.2)     # team-red kicker
area("Fill", (-1.5, -4.0, -1.0), 90, (0.45, 0.55, 1.0), 3.0)      # cool night fill

world = bpy.data.worlds.new("Night")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.012, 0.03, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
scene.world = world

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 85
cam = bpy.data.objects.new("Cam", cam_data)
cam.location = (0, -6.4, 0.6)
cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(cam)
scene.camera = cam

r = scene.render
r.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = samples
scene.cycles.use_denoising = True
r.film_transparent = True
r.resolution_x = r.resolution_y = size
r.image_settings.file_format = "PNG"
r.image_settings.color_mode = "RGBA"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"

if ALBEDO:
    for o in list(scene.objects):
        if o.type == "LIGHT":
            bpy.data.objects.remove(o)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.0
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.cycles.use_denoising = False
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2.0 * 1.0  # the ball fills the frame edge to edge
    cam.location = (0, -6.4, 0)
    cam.rotation_euler = (math.radians(90), 0, 0)
for i in range(frames):
    a = i / max(frames, 1)
    rx, ry, rz = 18 + SEED * 37, -12 + SEED * 53, 25 + SEED * 71
    ball.rotation_euler = Euler((math.radians(rx), math.radians(ry), math.radians(rz) + a * 2 * math.pi), "XYZ")
    r.filepath = f"{out}/ball_{i:02d}.png"
    bpy.ops.render.render(write_still=True)
    print("wrote", r.filepath, flush=True)
