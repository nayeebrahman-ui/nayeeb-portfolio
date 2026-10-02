"""Berlin hero: green beans -> roast -> Berlin cup. Blender (bpy) scene, real-world metres.

Usage: python3 scene.py [--test FRAME] [--start N --end M] [--res W H] [--samples S] [--out DIR] [--cam desk|mob]
"""
import bpy, bmesh, math, random, sys, os
from mathutils import Vector, Matrix, Euler
import numpy as np
from PIL import Image

args = sys.argv[1:]
def opt(name, default, n=1, cast=str):
    if name in args:
        i = args.index(name)
        v = [cast(a) for a in args[i + 1:i + 1 + n]]
        return v if n > 1 else v[0]
    return default

TEST = opt("--test", None, cast=int)
START = opt("--start", 1, cast=int)
END = opt("--end", 90, cast=int)
RES = opt("--res", [1600, 1000], 2, int)
SAMPLES = opt("--samples", 48, cast=int)
OUT = opt("--out", "/home/claude/berlin-cafe/render/frames", cast=str)
CAM = opt("--cam", "desk", cast=str)
CUP_PNG = "/home/claude/berlin-cafe/assets/cup.png"

FRAMES = 90
F_ROAST0, F_ROAST1, F_REVEAL0 = 22, 62, 64

random.seed(7)
np.random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start, scene.frame_end = 1, FRAMES

# ---------------------------------------------------------------- helpers
def smooth(a, b, x):
    t = min(1, max(0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)

def lin(c):  # sRGB -> linear
    return tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c)

def node(nt, kind, loc=(0, 0), **props):
    n = nt.nodes.new(kind)
    n.location = loc
    for k, v in props.items():
        setattr(n, k, v)
    return n

# ---------------------------------------------------------------- bean meshes
L, W, H, HB = 0.0058, 0.0043, 0.0034, 0.0011  # half extents; HB = flat-side depth

def make_bean(name, seed):
    rnd = random.Random(seed)
    lx = L * rnd.uniform(0.92, 1.08)
    wy = W * rnd.uniform(0.92, 1.08)
    hz = H * rnd.uniform(0.9, 1.1)
    bend = rnd.uniform(-0.0006, 0.0006)
    sk = rnd.uniform(0.6, 1.4)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    seg, ring = 128, 64
    verts = []
    crease = []
    for r in range(ring + 1):
        a = math.pi * r / ring  # along long axis
        row = []
        for s in range(seg):
            b = 2 * math.pi * s / seg
            nx = math.cos(a)
            ry = math.sin(a) * math.cos(b)
            rz = math.sin(a) * math.sin(b)
            # superellipsoid-ish: fuller shoulders
            nx_s = math.copysign(abs(nx) ** 0.9, nx)
            x = lx * nx_s
            y = wy * ry
            z = (hz * rz) if rz > 0 else (HB * rz)
            # gentle bend along length
            z += bend * (1 - nx * nx)
            # groove on flat side: S-curve along x
            g = 0.0
            if rz < 0.35:
                sc = 0.0011 * sk * math.sin(math.pi * nx * 1.15)
                taper = max(0.0, 1 - abs(nx) ** 3)
                d = math.exp(-((y - sc) / 0.00042) ** 2) * taper
                side = smooth(0.35, -0.5, rz)
                g = d * side
                z += 0.0021 * g
                # soft lips beside the groove
                lip = math.exp(-((abs(y - sc) - 0.0008) / 0.0005) ** 2) * taper * side
                z -= 0.00012 * lip
            v = bm.verts.new((x, y, z))
            row.append(v)
            crease.append(g)
        verts.append(row)
    for r in range(ring):
        for s in range(seg):
            a, b = verts[r][s], verts[r][(s + 1) % seg]
            c, d = verts[r + 1][(s + 1) % seg], verts[r + 1][s]
            try:
                bm.faces.new((a, b, c, d))
            except ValueError:
                pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    # crease attribute (after remove_doubles the vertex order of poles changes; recompute by position)
    attr = me.attributes.new("crease", 'FLOAT', 'POINT')
    for i, v in enumerate(me.vertices):
        x, y, z = v.co
        nx = max(-1, min(1, x / lx))
        sc = 0.0011 * sk * math.sin(math.pi * nx * 1.15)
        taper = max(0.0, 1 - abs(nx) ** 3)
        g = math.exp(-((y - sc) / 0.00055) ** 2) * taper if z < 0.0011 else 0.0
        attr.data[i].value = g
    for p in me.polygons:
        p.use_smooth = True
    return me, (lx, wy, hz)

bean_meshes = [make_bean(f"bean{i}", 100 + i) for i in range(5)]

# ---------------------------------------------------------------- bean material
bm_mat = bpy.data.materials.new("Bean")
bm_mat.use_nodes = True
nt = bm_mat.node_tree
nt.nodes.clear()
outn = node(nt, "ShaderNodeOutputMaterial", (900, 0))
bsdf = node(nt, "ShaderNodeBsdfPrincipled", (600, 0))
nt.links.new(bsdf.outputs[0], outn.inputs[0])
roast = node(nt, "ShaderNodeValue", (-900, 200), label="roast")
roast.name = "roast"
oinfo = node(nt, "ShaderNodeObjectInfo", (-900, -100))
# per-bean roast variation: roast + (rand-0.5)*0.12
m1 = node(nt, "ShaderNodeMath", (-700, -100), operation='SUBTRACT')
m1.inputs[1].default_value = 0.5
nt.links.new(oinfo.outputs["Random"], m1.inputs[0])
m2 = node(nt, "ShaderNodeMath", (-550, -100), operation='MULTIPLY')
m2.inputs[1].default_value = 0.12
nt.links.new(m1.outputs[0], m2.inputs[0])
rv = node(nt, "ShaderNodeMath", (-400, 100), operation='ADD', use_clamp=True)
nt.links.new(roast.outputs[0], rv.inputs[0])
nt.links.new(m2.outputs[0], rv.inputs[1])

ramp = node(nt, "ShaderNodeValToRGB", (-200, 250))
cr = ramp.color_ramp
stops = [
    (0.00, (0.50, 0.60, 0.38)),   # green, jade
    (0.10, (0.56, 0.62, 0.40)),
    (0.24, (0.76, 0.66, 0.42)),   # yellowing
    (0.40, (0.62, 0.40, 0.21)),   # cinnamon
    (0.58, (0.43, 0.24, 0.12)),   # city
    (0.78, (0.28, 0.14, 0.07)),   # full city
    (1.00, (0.16, 0.08, 0.045)),  # dark
]
cr.elements[0].position, cr.elements[0].color = stops[0][0], (*lin(stops[0][1]), 1)
cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*lin(stops[-1][1]), 1)
for pos, col in stops[1:-1]:
    e = cr.elements.new(pos)
    e.color = (*lin(col), 1)
nt.links.new(rv.outputs[0], ramp.inputs[0])

# fine mottling so beans aren't flat colour
tc = node(nt, "ShaderNodeTexCoord", (-900, -400))
noise = node(nt, "ShaderNodeTexNoise", (-700, -400))
noise.inputs["Scale"].default_value = 900.0
noise.inputs["Detail"].default_value = 3.0
nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
mott = node(nt, "ShaderNodeMix", (100, 250), data_type='RGBA', blend_type='MULTIPLY')
mott.inputs["Factor"].default_value = 0.35
nt.links.new(ramp.outputs[0], mott.inputs[6])
nt.links.new(noise.outputs["Color"], mott.inputs[7])
# chaff (silverskin) in the crease
attrn = node(nt, "ShaderNodeAttribute", (-200, -150), attribute_name="crease")
chaffmix = node(nt, "ShaderNodeMix", (300, 250), data_type='RGBA', blend_type='MIX')
cf = node(nt, "ShaderNodeMath", (100, -150), operation='MULTIPLY')
cf.inputs[1].default_value = 0.8
nt.links.new(attrn.outputs["Fac"], cf.inputs[0])
nt.links.new(cf.outputs[0], chaffmix.inputs["Factor"])
nt.links.new(mott.outputs[2], chaffmix.inputs[6])
chaffmix.inputs[7].default_value = (*lin((0.72, 0.64, 0.48)), 1)
tone = node(nt, "ShaderNodeMapRange", (300, 450))
tone.inputs["To Min"].default_value = 0.8
tone.inputs["To Max"].default_value = 1.12
oinfo2 = node(nt, "ShaderNodeObjectInfo", (100, 450))
nt.links.new(oinfo2.outputs["Random"], tone.inputs["Value"])
hsv = node(nt, "ShaderNodeHueSaturation", (500, 300))
nt.links.new(chaffmix.outputs[2], hsv.inputs["Color"])
nt.links.new(tone.outputs[0], hsv.inputs["Value"])
hshift = node(nt, "ShaderNodeMapRange", (300, 600))
hshift.inputs["To Min"].default_value = 0.485
hshift.inputs["To Max"].default_value = 0.52
nt.links.new(oinfo.outputs["Random"], hshift.inputs["Value"])
nt.links.new(hshift.outputs[0], hsv.inputs["Hue"])
nt.links.new(hsv.outputs[0], bsdf.inputs["Base Color"])

# roughness: 0.62 green -> 0.34 roasted
rough = node(nt, "ShaderNodeMapRange", (100, -350))
rough.inputs["From Min"].default_value = 0.3
rough.inputs["From Max"].default_value = 1.0
rough.inputs["To Min"].default_value = 0.6
rough.inputs["To Max"].default_value = 0.36
nt.links.new(rv.outputs[0], rough.inputs["Value"])
nt.links.new(rough.outputs[0], bsdf.inputs["Roughness"])
# coat (faint oil sheen late in roast)
coat = node(nt, "ShaderNodeMapRange", (100, -550))
coat.inputs["From Min"].default_value = 0.7
coat.inputs["From Max"].default_value = 1.0
coat.inputs["To Min"].default_value = 0.0
coat.inputs["To Max"].default_value = 0.35
nt.links.new(rv.outputs[0], coat.inputs["Value"])
nt.links.new(coat.outputs[0], bsdf.inputs["Coat Weight"])
bsdf.inputs["Coat Roughness"].default_value = 0.22
bsdf.inputs["Subsurface Radius"].default_value = (0.0006, 0.0003, 0.0002)

# wrinkle bump: stronger as beans roast and expand
wn = node(nt, "ShaderNodeTexNoise", (-700, -700))
wn.inputs["Scale"].default_value = 420.0
wn.inputs["Detail"].default_value = 3.0
wn.inputs["Distortion"].default_value = 0.6
nt.links.new(tc.outputs["Object"], wn.inputs["Vector"])
bstr = node(nt, "ShaderNodeMapRange", (100, -750))
bstr.inputs["From Min"].default_value = 0.0
bstr.inputs["From Max"].default_value = 1.0
bstr.inputs["To Min"].default_value = 0.11
bstr.inputs["To Max"].default_value = 0.2
nt.links.new(rv.outputs[0], bstr.inputs["Value"])
bump = node(nt, "ShaderNodeBump", (350, -650))
bump.inputs["Distance"].default_value = 0.00012
nt.links.new(bstr.outputs[0], bump.inputs["Strength"])
nt.links.new(wn.outputs["Fac"], bump.inputs["Height"])
nt.links.new(bump.outputs[0], bsdf.inputs["Normal"])

def roast_at(f):
    # 0 -> 0.92 across the roast window, slow start, fast middle, ease at end
    return 0.92 * smooth(F_ROAST0, F_ROAST1, f) ** 1.15

for f in range(1, FRAMES + 1):
    roast.outputs[0].default_value = roast_at(f)
    roast.outputs[0].keyframe_insert("default_value", frame=f)

for me, _ in bean_meshes:
    me.materials.append(bm_mat)

# ---------------------------------------------------------------- pile
pile = bpy.data.objects.new("Pile", None)
scene.collection.objects.link(pile)
GRID = 0.0006
R_PILE = 0.058
hmap_n = int(0.16 / GRID)
hmap = np.zeros((hmap_n, hmap_n))
def hm_idx(x, y):
    return int((x + 0.08) / GRID), int((y + 0.08) / GRID)

beans = []
target_n = 340
tries = 0
while len(beans) < target_n and tries < 20000:
    tries += 1
    r = R_PILE * math.sqrt(random.random()) ** 0.85
    th = random.random() * 2 * math.pi
    x, y = r * math.cos(th), r * math.sin(th) * 0.92
    # mound bias: accept fewer beans near the edge
    if random.random() > 1.05 - (r / R_PILE) ** 2 * 0.6:
        continue
    me, (lx, wy, hz) = random.choice(bean_meshes)
    yaw = random.random() * 2 * math.pi
    pose = random.random()
    if pose < 0.58:      # flat side down (dome up)
        rot = Euler((random.uniform(-0.18, 0.18), random.uniform(-0.18, 0.18), yaw))
        half = hz
        lowz = HB
    elif pose < 0.86:    # flat side up, crease visible
        rot = Euler((math.pi + random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), yaw))
        half = HB
        lowz = hz
    else:                # on its side
        rot = Euler((math.pi / 2 * random.choice((-1, 1)) + random.uniform(-0.3, 0.3), random.uniform(-0.2, 0.2), yaw))
        half = wy * 0.9
        lowz = wy * 0.9
    # footprint
    rm = rot.to_matrix()
    ax = rm @ Vector((lx, 0, 0))
    ay = rm @ Vector((0, wy, 0))
    pts = []
    for u in (-0.75, 0, 0.75):
        for v in (-0.6, 0, 0.6):
            pts.append((x + ax.x * u + ay.x * v, y + ax.y * u + ay.y * v))
    hs = []
    for px, py in pts:
        i, j = hm_idx(px, py)
        if 0 <= i < hmap_n and 0 <= j < hmap_n:
            hs.append(hmap[i, j])
    base = max(hs) if hs else 0.0
    # limit stack height so the pile reads as a mound, not a tower
    cap = 0.026 * (1 - (r / R_PILE) ** 1.6) + 0.004
    if base > cap:
        continue
    z = base + lowz * 0.88
    top = z + half
    for px, py in pts:
        i, j = hm_idx(px, py)
        for di in range(-4, 5):
            for dj in range(-4, 5):
                ii, jj = i + di, j + dj
                if 0 <= ii < hmap_n and 0 <= jj < hmap_n:
                    fall = math.hypot(di, dj) * GRID * 0.9
                    hmap[ii, jj] = max(hmap[ii, jj], top - fall)
    ob = bpy.data.objects.new("b", me)
    ob.location = (x, y, z)
    ob.rotation_euler = rot
    ob.parent = pile
    scene.collection.objects.link(ob)
    beans.append(ob)

# a few strays drifting toward the cup and the camera
for k in range(26):
    me, (lx, wy, hz) = random.choice(bean_meshes)
    a = random.uniform(-1.3, 1.3) + (math.pi / 2 if k % 3 == 0 else -math.pi / 2)
    d = random.uniform(0.064, 0.12)
    x, y = d * math.cos(a) * 1.25, d * math.sin(a)
    if abs(x) < 0.035 and 0.10 < y < 0.19:  # keep the cup footprint clear
        continue
    ob = bpy.data.objects.new("s", me)
    flat_up = random.random() < 0.35
    ob.rotation_euler = Euler(((math.pi if flat_up else 0) + random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.random() * 6.28))
    ob.location = (x, y, (hz if flat_up else HB) * 0.95)
    ob.parent = pile
    scene.collection.objects.link(ob)
    beans.append(ob)
print("beans", len(beans))

# swell ~14% through the roast (beans expand as they lose water and build CO2)
for f in (1, F_ROAST0, int((F_ROAST0 + F_ROAST1) / 2), F_ROAST1, FRAMES):
    s = 1 + 0.14 * smooth(F_ROAST0 + 6, F_ROAST1, f)
    pile.scale = (s, s, s)
    pile.keyframe_insert("scale", frame=f)


# ---------------------------------------------------------------- Berlin cup (lathe traced from the photo)
img = Image.open(CUP_PNG).convert("RGBA")
bbox = img.split()[-1].getbbox()
crop = img.crop(bbox)
cw, ch = crop.size
alpha = np.array(crop.split()[-1]) > 40
CUP_H = 0.122
px = CUP_H / ch
cup_img_path = "/home/claude/berlin-cafe/render/cup_tex.png"
crop.save(cup_img_path)

rgb = np.array(crop.convert("RGB")).astype(float) / 255
lumr = []
for yy in range(ch):
    m = alpha[yy]
    lumr.append(rgb[yy][m].mean() if m.sum() > 10 else 0)
lumr = np.array(lumr)
# lid band ends where the silhouette narrows from the lid rim to the paper sleeve
wid = alpha.sum(1)
rim = int(np.argmax(wid[: int(ch * 0.35)]))
LID_END = next(y for y in range(rim, int(ch * 0.45)) if wid[y] < wid[rim] * 0.925) + 3
print("lid ends at row", LID_END, "of", ch)
profile = []
rows = list(range(LID_END, ch, 4)) + [ch - 1]
for yy in rows:
    xs = np.where(alpha[yy])[0]
    if len(xs) < 2:
        continue
    half = (xs[-1] - xs[0]) / 2 * px
    cx = (xs[-1] + xs[0]) / 2
    profile.append((yy, half, cx))
# median-smooth the radii
rad = np.array([p[1] for p in profile])
rad_s = np.convolve(np.pad(rad, 2, mode='edge'), np.ones(5) / 5, mode='valid')
cup_me = bpy.data.meshes.new("cup")
bm = bmesh.new()
SEG = 128
rings = []
for k, (yy, _, cx) in enumerate(profile):
    rr = rad_s[k]
    z = (ch - yy) * px
    ring = []
    for s in range(SEG):
        t = 2 * math.pi * s / SEG
        ring.append(bm.verts.new((rr * math.sin(t), -rr * math.cos(t), z)))
    rings.append(ring)
for a, b in zip(rings[:-1], rings[1:]):
    for s in range(SEG):
        bm.faces.new((a[s], a[(s + 1) % SEG], b[(s + 1) % SEG], b[s]))
# procedural lid: flange, skirt, raised deck with a sip spout
z0 = (ch - profile[0][0]) * px
r0 = rad_s[0]
lid_prof = [(r0 * 1.0, z0), (r0 * 1.045, z0 + 0.0012), (r0 * 1.05, z0 + 0.0042), (r0 * 1.03, z0 + 0.0058),
            (r0 * 0.985, z0 + 0.0062), (r0 * 0.95, z0 + 0.0072), (r0 * 0.93, z0 + 0.0118), (r0 * 0.905, z0 + 0.0132),
            (r0 * 0.6, z0 + 0.0136), (0.0005, z0 + 0.0138)]
prev = rings[0]
lid_faces = []
for (lr, lz) in lid_prof:
    ring = []
    for s in range(SEG):
        t = 2 * math.pi * s / SEG
        zz = lz
        ang = abs(((t - 2.3) + math.pi) % (2 * math.pi) - math.pi)
        if lz > z0 + 0.0115 and lr > r0 * 0.5:
            zz += 0.0024 * math.exp(-(ang / 0.45) ** 2)
        ring.append(bm.verts.new((lr * math.sin(t), -lr * math.cos(t), zz)))
    for s in range(SEG):
        lid_faces.append(bm.faces.new((prev[s], prev[(s + 1) % SEG], ring[(s + 1) % SEG], ring[s])))
    prev = ring
top = bm.verts.new((0, 0, z0 + 0.0139))
for s in range(SEG):
    lid_faces.append(bm.faces.new((prev[(s + 1) % SEG], prev[s], top)))
for f_ in lid_faces:
    f_.material_index = 1
botc = bm.verts.new((0, 0, 0))
for s in range(SEG):
    bm.faces.new((rings[-1][s], rings[-1][(s + 1) % SEG], botc))
bm.normal_update()
bm.to_mesh(cup_me)
bm.free()
for p in cup_me.polygons:
    p.use_smooth = True
# planar UV from the front (photo direction is -Y)
uvl = cup_me.uv_layers.new(name="UV")
for loop in cup_me.loops:
    co = cup_me.vertices[loop.vertex_index].co
    u = 0.5 + co.x / (cw * px)
    v = co.z / (ch * px)
    uvl.data[loop.index].uv = (u, v)
cup = bpy.data.objects.new("Cup", cup_me)
scene.collection.objects.link(cup)
CUP_POS = Vector((0.0, 0.15, 0.0))
cup.location = CUP_POS
cup.rotation_euler = (0, 0, 0)

cm = bpy.data.materials.new("Cup")
cm.use_nodes = True
ct = cm.node_tree
ct.nodes.clear()
co_ = node(ct, "ShaderNodeOutputMaterial", (900, 0))
cb = node(ct, "ShaderNodeBsdfPrincipled", (500, 0))
it = node(ct, "ShaderNodeTexImage", (-300, 0))
it.image = bpy.data.images.load(cup_img_path)
it.interpolation = 'Cubic'
it.extension = 'EXTEND'
# the photo already carries shading: lift it slightly so real light does not double-darken
gam = node(ct, "ShaderNodeGamma", (0, 100))
gam.inputs[1].default_value = 1.0
ct.links.new(it.outputs[0], gam.inputs[0])
lidmix = node(ct, "ShaderNodeMix", (250, 100), data_type='RGBA', blend_type='MIX')
ct.links.new(it.outputs["Alpha"], lidmix.inputs["Factor"])
lidmix.inputs[6].default_value = (0.012, 0.012, 0.013, 1)
ct.links.new(gam.outputs[0], lidmix.inputs[7])
ct.links.new(lidmix.outputs[2], cb.inputs["Base Color"])
# lid is dark plastic (glossy), paper sleeve is matte
lum = node(ct, "ShaderNodeRGBToBW", (0, -150))
ct.links.new(it.outputs[0], lum.inputs[0])
rmap = node(ct, "ShaderNodeMapRange", (200, -150))
rmap.inputs["From Min"].default_value = 0.08
rmap.inputs["From Max"].default_value = 0.35
rmap.inputs["To Min"].default_value = 0.5
rmap.inputs["To Max"].default_value = 0.62
ct.links.new(lum.outputs[0], rmap.inputs["Value"])
ct.links.new(rmap.outputs[0], cb.inputs["Roughness"])
spec = node(ct, "ShaderNodeMapRange", (200, -350))
spec.inputs["From Min"].default_value = 0.08
spec.inputs["From Max"].default_value = 0.35
spec.inputs["To Min"].default_value = 0.25
spec.inputs["To Max"].default_value = 0.5
ct.links.new(lum.outputs[0], spec.inputs["Value"])
ct.links.new(spec.outputs[0], cb.inputs["Specular IOR Level"])
# a touch of self-illumination keeps the printed artwork legible in a dark set
em = node(ct, "ShaderNodeEmission", (500, -300))
em.inputs["Strength"].default_value = 0.08
ct.links.new(lidmix.outputs[2], em.inputs["Color"])
addsh = node(ct, "ShaderNodeAddShader", (720, 0))
ct.links.new(cb.outputs[0], addsh.inputs[0])
ct.links.new(em.outputs[0], addsh.inputs[1])
ct.links.new(addsh.outputs[0], co_.inputs[0])
cup_me.materials.append(cm)
lm = bpy.data.materials.new("Lid")
lm.use_nodes = True
lb = lm.node_tree.nodes["Principled BSDF"]
lb.inputs["Base Color"].default_value = (0.010, 0.010, 0.011, 1)
lb.inputs["Roughness"].default_value = 0.6
lb.inputs["Specular IOR Level"].default_value = 0.2
cup_me.materials.append(lm)

# ---------------------------------------------------------------- set: dark walnut-slate surface + backdrop
def surface_mat():
    m = bpy.data.materials.new("Surface")
    m.use_nodes = True
    t = m.node_tree
    t.nodes.clear()
    o = node(t, "ShaderNodeOutputMaterial", (800, 0))
    b = node(t, "ShaderNodeBsdfPrincipled", (500, 0))
    t.links.new(b.outputs[0], o.inputs[0])
    tc2 = node(t, "ShaderNodeTexCoord", (-700, 0))
    mp = node(t, "ShaderNodeMapping", (-500, 0))
    mp.inputs["Scale"].default_value = (6, 60, 6)  # stretched grain like oiled wood
    t.links.new(tc2.outputs["Object"], mp.inputs["Vector"])
    n1 = node(t, "ShaderNodeTexNoise", (-300, 0))
    n1.inputs["Scale"].default_value = 6.0
    n1.inputs["Detail"].default_value = 4.0
    n1.inputs["Distortion"].default_value = 1.2
    t.links.new(mp.outputs[0], n1.inputs["Vector"])
    rp = node(t, "ShaderNodeValToRGB", (-50, 100))
    rp.color_ramp.elements[0].color = (*lin((0.014, 0.011, 0.009)), 1)
    rp.color_ramp.elements[1].color = (*lin((0.034, 0.025, 0.019)), 1)
    t.links.new(n1.outputs["Fac"], rp.inputs[0])
    t.links.new(rp.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Specular IOR Level"].default_value = 0.12
    bp = node(t, "ShaderNodeBump", (250, -200))
    bp.inputs["Strength"].default_value = 0.08
    bp.inputs["Distance"].default_value = 0.0004
    t.links.new(n1.outputs["Fac"], bp.inputs["Height"])
    t.links.new(bp.outputs[0], b.inputs["Normal"])
    return m

bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0, 2.5, 0))
plane = bpy.context.active_object
plane.data.materials.append(surface_mat())

bm2 = bpy.data.materials.new("Backdrop")
bm2.use_nodes = True
bb = bm2.node_tree.nodes["Principled BSDF"]
bb.inputs["Base Color"].default_value = (*lin((0.035, 0.026, 0.021)), 1)
bb.inputs["Roughness"].default_value = 0.9
bpy.ops.mesh.primitive_plane_add(size=4.0, location=(0, 1.4, 1.0), rotation=(math.pi / 2, 0, 0))
back = bpy.context.active_object
back.data.materials.append(bm2)
bpy.data.objects.remove(back)

world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (*lin((0.02, 0.016, 0.013)), 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.06

# ---------------------------------------------------------------- lights
def area(name, loc, rot, size, power, col, shape='RECTANGLE', size_y=None):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = power
    ld.color = col
    ld.shape = shape
    ld.size = size
    if size_y:
        ld.size_y = size_y
    ob = bpy.data.objects.new(name, ld)
    ob.location = loc
    ob.rotation_euler = rot
    scene.collection.objects.link(ob)
    return ob

def aim(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

key = area("Key", (-0.30, 0.20, 0.40), (0, 0, 0), 0.20, 8.0, (1.0, 0.86, 0.70), size_y=0.14)
aim(key, (0, 0.03, 0.03))
key.data.spread = math.radians(75)
rim = area("Rim", (0.42, 0.40, 0.34), (0, 0, 0), 0.16, 2.4, (1.0, 0.76, 0.52))
rim.data.spread = math.radians(38)
aim(rim, (0, 0.08, 0.05))
fill = area("Fill", (0.30, -0.45, 0.18), (0, 0, 0), 0.5, 0.45, (0.80, 0.86, 1.0))
aim(fill, (0, 0, 0.02))
glow_back = area("BackWash", (0, 1.1, 0.25), (0, 0, 0), 0.9, 1.6, (1.0, 0.66, 0.40))
aim(glow_back, (0, 1.4, 0.45))
glow_back.data.energy = 0.0
# roaster heat: low, warm, from the front-left edge of the pile; swells then fades during the roast
heat = area("Heat", (-0.09, -0.05, 0.006), (0, 0, 0), 0.06, 0.0, (1.0, 0.50, 0.20), shape='DISK')
aim(heat, (0.02, 0.0, 0.008))
for f in range(1, FRAMES + 1):
    h = smooth(F_ROAST0 - 4, F_ROAST0 + 18, f) * (1 - smooth(F_ROAST1 - 14, F_ROAST1 + 6, f))
    heat.data.energy = 5.0 * h
    heat.data.keyframe_insert("energy", frame=f)
# cup spot appears for the reveal
_sd = bpy.data.lights.new("CupSpot", 'SPOT')
_sd.spot_size = math.radians(22)
_sd.spot_blend = 0.7
_sd.shadow_soft_size = 0.04
_sd.color = (1.0, 0.88, 0.74)
cupspot = bpy.data.objects.new("CupSpot", _sd)
cupspot.location = (-0.20, -0.12, 0.38)
scene.collection.objects.link(cupspot)
aim(cupspot, (0.0, 0.15, 0.06))
aim(cupspot, (0.0, 0.15, 0.07))
for f in range(1, FRAMES + 1):
    cupspot.data.energy = 0.9 * smooth(F_REVEAL0 + 4, FRAMES - 8, f)
    cupspot.data.keyframe_insert("energy", frame=f)

# ---------------------------------------------------------------- camera
camd = bpy.data.cameras.new("Cam")
camd.lens = 85 if CAM == "desk" else 70
camd.sensor_fit = 'HORIZONTAL' if CAM == "desk" else 'VERTICAL'
camd.sensor_width = 36
camd.sensor_height = 24 if CAM == "desk" else 36
camd.clip_start = 0.002
camd.clip_end = 20
camd.dof.use_dof = True
cam = bpy.data.objects.new("Cam", camd)
scene.collection.objects.link(cam)
scene.camera = cam
focus = bpy.data.objects.new("Focus", None)
scene.collection.objects.link(focus)
camd.dof.focus_object = focus

def lerpv(a, b, t):
    return Vector(a).lerp(Vector(b), t)

def ease(t):
    return t * t * t * (t * (6 * t - 15) + 10)

def surf(x, y, s=1.0):
    i, j = hm_idx(x / s, y / s)
    return hmap[i, j] * s

if CAM == "desk":
    P0, P1, P2 = (0.070, -0.190, 0.070), (0.034, -0.160, 0.058), (0.0, -0.54, 0.155)
    T0, T1, T2 = (0.006, -0.034, 0.0), (0.0, -0.024, 0.0), (0.0, 0.15, 0.072)
else:
    P0, P1, P2 = (0.050, -0.190, 0.072), (0.024, -0.160, 0.060), (0.0, -0.60, 0.17)
    T0, T1, T2 = (0.006, -0.034, 0.0), (0.0, -0.024, 0.0), (0.0, 0.15, 0.060)

T0 = (T0[0], T0[1], surf(T0[0], T0[1]) + 0.001)
T1s = 1.14
T1 = (T1[0], T1[1] * T1s, surf(T1[0], T1[1]) * T1s + 0.001)
for f in range(1, FRAMES + 1):
    if f <= F_REVEAL0:
        t = ease((f - 1) / (F_REVEAL0 - 1))
        p, tg = lerpv(P0, P1, t), lerpv(T0, T1, t)
        fstop = 6.3
    else:
        t = ease((f - F_REVEAL0) / (FRAMES - F_REVEAL0))
        # rise a little faster than we travel back so we glide over the pile
        p = Vector((lerpv(P1, P2, t).x, lerpv(P1, P2, t).y, P1[2] + (P2[2] - P1[2]) * (1 - (1 - t) ** 1.6)))
        tg = lerpv(T1, T2, t)
        fstop = 6.3 - 1.3 * t
    cam.location = p
    d = tg - p
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    focus.location = tg
    camd.dof.aperture_fstop = fstop
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
    focus.keyframe_insert("location", frame=f)
    camd.dof.keyframe_insert("aperture_fstop", frame=f)

# ---------------------------------------------------------------- render settings
ENGINE = opt("--engine", "cycles", cast=str)
scene.render.engine = 'CYCLES'
cy = scene.cycles
cy.device = 'CPU'
cy.samples = SAMPLES
cy.use_adaptive_sampling = True
cy.adaptive_threshold = 0.04
cy.use_denoising = True
cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 6
cy.diffuse_bounces = 1
cy.glossy_bounces = 1
cy.transmission_bounces = 2
cy.volume_bounces = 0
cy.caustics_reflective = False
cy.caustics_refractive = False
cy.blur_glossy = 1.0
cy.use_fast_gi = True
cy.ao_bounces_render = 1
scene.render.use_persistent_data = True
if ENGINE == "eevee":
    scene.render.engine = 'BLENDER_EEVEE'
    ee = scene.eevee
    ee.taa_render_samples = SAMPLES
    for k, v in (("use_raytracing", True), ("use_shadows", True), ("shadow_ray_count", 2), ("shadow_step_count", 8), ("use_gtao", True), ("fast_gi_method", 'GLOBAL_ILLUMINATION')):
        try: setattr(ee, k, v)
        except Exception as e: print("eevee opt", k, e)
    try:
        ee.ray_tracing_options.resolution_scale = '1'
        ee.ray_tracing_method = 'SCREEN'
    except Exception as e: print("rt", e)
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except TypeError:
    pass
scene.view_settings.exposure = 0.0
for f in range(1, FRAMES + 1):
    scene.view_settings.exposure = -0.85 + 0.45 * smooth(F_ROAST0, F_ROAST1, f) + 0.40 * smooth(F_REVEAL0, FRAMES - 6, f)
    scene.view_settings.keyframe_insert("exposure", frame=f)
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_depth = '8'
os.makedirs(OUT, exist_ok=True)

if TEST:
    scene.frame_set(TEST)
    scene.render.filepath = os.path.join(OUT, f"test_{CAM}_{TEST:03d}.png")
    bpy.ops.render.render(write_still=True)
else:
    import time
    for f in range(START, END + 1):
        path = os.path.join(OUT, f"{CAM}_{f:03d}.png")
        if os.path.exists(path):
            continue
        t0 = time.time()
        scene.frame_set(f)
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print(f"frame {f} {time.time() - t0:.1f}s", flush=True)
