"""로고 입체 한 장 — `python -m ad render3d` 가 부른다(직접 부를 때는 DeGaJa_Agent 에서 `python -m module_render run`).

아무 로고 SVG(경로만) → 두께·둥근 베벨 → 재질 → 조명 → Cycles(OptiX). 실험 원본: runs/2026-09-28_로고빛/scene_logo_light.py·scene_d_icon.py.
  flat   기준(평면 그대로, Standard 뷰)
  chrome 은빛 금속 + 스튜디오 반사 + 앞면 반사선 위 띠 조명 (집지켜)
  ink    먹색 광택 «관» — 앞면은 어둠만, 빛은 베벨만 긁는다 (ChatGPT)
  glass  투명 유리 + 짙은 대표색 바탕 (Liquid Glass)
  front  간판 전면 발광(앞면만 빛, 옆면 알루미늄)
  halo   간판 후광(벽에서 띄우고 뒷면만 빛)
  glow   발광 색 흐름(대표색 → 산호 → 호박)
🔴 함정은 전부 DeGaJa_Agent/module_render/BLENDER.md ⑫⑱㉓ — reset 누락(기본 큐브) · 면광원이 카메라에 찍힘 · 반두께 extrude.
"""
import argparse
import os
import sys

sys.path.insert(0, os.environ["DEGAJA_ROOT"])
import addon_utils  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from module_render import _scene as S  # noqa: E402

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--svg", required=True)
ap.add_argument("--look", required=True)
ap.add_argument("--main", default="#17161a")
ap.add_argument("--out", required=True)
ap.add_argument("--samples", type=int, default=128)
ap.add_argument("--w", type=int, default=1024)
ap.add_argument("--h", type=int, default=1024)
ap.add_argument("--bevel", type=float, default=1.0, help="베벨 배율 — 획이 가는 로고면 줄여라(겹친 획 이음매에 검은 점이 생긴다)")
A = ap.parse_args(argv)
HDRI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "studio_small_08_2k.hdr")
CAM = (0, -1.5, 7.6)
LENS = 90


def lin(hexc):
    c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1,)


def mixc(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3)) + (1,)


def cycles(samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    sc.cycles.device = 'GPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    return sc


def mat(name, color, *, rough=0.5, metal=0.0, coat=0.0, trans=0.0, emit=None, emit_strength=0.0):
    m = S.solid(name, color, roughness=rough, metallic=metal, transmission=trans, ior=1.45,
                emission=emit, emission_strength=emit_strength)
    if coat:
        p = m.node_tree.nodes["Principled BSDF"]
        p.inputs["Coat Weight"].default_value = coat
        p.inputs["Coat Roughness"].default_value = 0.02
    return m


def gradient_emission(name, stops, strength, span):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    geo, sep = nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeSeparateXYZ")
    mr, ramp = nt.nodes.new("ShaderNodeMapRange"), nt.nodes.new("ShaderNodeValToRGB")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = -span / 2, span / 2
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = stops[0]
    els[1].position, els[1].color = stops[-1]
    for pos, col in stops[1:-1]:
        els.new(pos).color = col
    em, out = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
    em.inputs["Strength"].default_value = strength
    for a, b in ((geo.outputs["Position"], sep.inputs["Vector"]), (sep.outputs["X"], mr.inputs["Value"]),
                 (mr.outputs["Result"], ramp.inputs["Fac"]), (ramp.outputs["Color"], em.inputs["Color"]),
                 (em.outputs["Emission"], out.inputs["Surface"])):
        nt.links.new(a, b)
    return m


def radial_plate(name, inner, outer, radius):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.6
    geo, ln = nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = 'LENGTH'
    mr, ramp = nt.nodes.new("ShaderNodeMapRange"), nt.nodes.new("ShaderNodeValToRGB")
    mr.inputs["From Max"].default_value = radius
    ramp.color_ramp.elements[0].color, ramp.color_ramp.elements[1].color = inner, outer
    for a, b in ((geo.outputs["Position"], ln.inputs[0]), (ln.outputs["Value"], mr.inputs["Value"]),
                 (mr.outputs["Result"], ramp.inputs["Fac"]), (ramp.outputs["Color"], p.inputs["Base Color"])):
        nt.links.new(a, b)
    return m


def load(depth_ratio, bevel_ratio, standoff=0.0):
    """SVG → 메시들. 반환 [(오브젝트, 원래색 선형, 대표인가)], 로고 (가로, 세로) m."""
    addon_utils.enable("io_curve_svg", default_set=False, persistent=False)
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=A.svg)
    objs = [o for o in bpy.data.objects if o not in before and o.type == 'CURVE']
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    lw, lh = max(xs) - min(xs), max(ys) - min(ys)
    fw = 36 / LENS * Vector(CAM).length
    fh = fw * A.h / A.w
    s = min(fw * 0.6 / lw, fh * 0.55 / lh)
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    H = lh * s
    depth, bevel = depth_ratio * H, bevel_ratio * H * A.bevel
    z0 = depth / 2 + bevel + standoff * H
    main = lin(A.main)
    out = []
    for o in objs:
        m0 = o.data.materials[0] if o.data.materials else None
        col = tuple(m0.diffuse_color) if m0 else main
        is_main = sum(abs(col[i] - main[i]) for i in range(3)) < 0.03
        o.data.materials.clear()
        o.data.extrude = depth / 2 / s              # BLENDER.md ⑱ 반두께 · ⑫① 스케일 역보정
        o.data.bevel_depth = bevel / s
        o.data.bevel_resolution = 8
        o.data.resolution_u = 24
        L0 = o.location.copy()
        o.scale = (s, s, s)
        o.location = (s * (L0.x - cx), s * (L0.y - cy), z0)
        with S._ui(o):
            bpy.ops.object.convert(target='MESH')
        if not hasattr(o.data, "polygons"):
            raise RuntimeError(f"{o.name}: convert(MESH) 가 안 됐다 (BLENDER.md ⑬)")
        out.append((o, col, is_main))
    return out, (lw * s, H)


def assign(o, front, side=None, back=None):
    o.data.materials.clear()
    for m in (front, side or front, back or side or front):
        o.data.materials.append(m)
    for poly in o.data.polygons:
        nz = poly.normal.z
        poly.material_index = 0 if nz > 0.7 else (2 if nz < -0.7 else 1)


def plate(m):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    p = S._added()
    p.scale = (14, 10, 1)
    p.data.materials.append(m)


def softbox(name, loc, energy, size):
    lt = S.area_light(name, loc, energy=energy)
    lt.visible_camera = False          # BLENDER.md ㉓a — Cycles 는 면광원을 카메라에 찍는다
    lt.data.shape = 'RECTANGLE'
    lt.data.size, lt.data.size_y = size
    lt.rotation_euler = (Vector((0, 0, 0)) - lt.location).to_track_quat('-Z', 'Y').to_euler()


def studio(key, fill, rim, band):
    softbox("Key", (-2.2, 2.0, 4.2), key, (3.0, 1.5))
    softbox("Fill", (2.8, -2.2, 3.0), fill, (2.4, 2.4))
    softbox("Rim", (0.0, 3.2, 1.1), rim, (5.0, 0.25))
    if band:                          # ㉓c — 평평한 앞면이 비추는 자리(위·약간 뒤)
        softbox("Band", (0.0, 1.7, 7.4), band, (2.2, 0.9))


S.reset()                             # 🔴 빠뜨리면 기본 큐브가 로고를 덮는다(㉓b)
sc = cycles(A.samples)
sc.view_settings.view_transform = 'AgX'
MAIN = lin(A.main)
look = A.look

if look == "flat":
    sc.view_settings.view_transform = 'Standard'
    parts, (W, H) = load(0.004, 0.0)
    for o, col, _ in parts:
        assign(o, mat("c", col, rough=0.9))
    plate(mat("paper", (0.83, 0.80, 0.75, 1), rough=0.95))
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
elif look == "chrome":
    parts, (W, H) = load(0.085, 0.035)
    for o, col, is_main in parts:
        assign(o, mat("chrome", (0.93, 0.93, 0.95, 1), rough=0.05, metal=1.0) if is_main
               else mat("anod", col, rough=0.15, metal=1.0))
    plate(radial_plate("navy", (0.03, 0.045, 0.11, 1), (0.004, 0.006, 0.02, 1), max(W, H) * 1.6))
    S.world_hdri(HDRI, strength=0.8, visible=False)
    studio(300, 60, 900, 500)
elif look == "ink":
    parts, (W, H) = load(0.085, 0.042)
    for o, col, is_main in parts:
        assign(o, mat("ink", (0.006, 0.006, 0.008, 1), rough=0.28, coat=1.0) if is_main
               else mat("acc", col, rough=0.25, coat=1.0))
    plate(radial_plate("bg", (0.92, 0.91, 0.90, 1), (0.62, 0.61, 0.62, 1), max(W, H) * 1.6))
    S.world_hdri(HDRI, strength=0.025, visible=False)
    studio(520, 60, 900, 0)
elif look == "glass":
    parts, (W, H) = load(0.085, 0.035, standoff=0.03)
    for o, col, is_main in parts:
        assign(o, mat("glass", (1.0, 0.95, 0.96, 1), rough=0.04, trans=1.0, coat=0.5) if is_main
               else mat("glow", (1, 1, 1, 1), emit=col, emit_strength=2.2))
    plate(radial_plate("bg", mixc(MAIN, (1, 1, 1), 0.15), mixc(MAIN, (0, 0, 0), 0.85), max(W, H) * 1.5))
    S.world_hdri(HDRI, strength=0.5, visible=False)
    studio(160, 30, 800, 260)
    S.post(glare_type='Bloom', threshold=1.0, glare_size=0.55, glare_strength=0.3)
elif look in ("front", "halo"):
    halo = look == "halo"
    parts, (W, H) = load(0.13, 0.007, standoff=0.07 if halo else 0.0)
    alu = mat("alu", (0.55, 0.56, 0.58, 1), rough=0.35, metal=1.0)
    black = mat("black", (0.02, 0.02, 0.022, 1), rough=0.45)
    for o, col, is_main in parts:
        if halo:
            assign(o, black if is_main else mat("accpaint", col, rough=0.4), black,
                   mat("led", (0, 0, 0, 1), emit=(1.0, 0.82, 0.62, 1), emit_strength=60.0))
        else:
            assign(o, mat("acryl", (1, 1, 1, 1), emit=(1.0, 0.93, 0.85, 1) if is_main else col, emit_strength=4.5), alu)
    plate(mat("wall", (0.10, 0.10, 0.10, 1), rough=0.85))
    S.world_gradient()
    softbox("Street", (0.0, -5.0, 3.0), 60, (6.0, 2.0))
    S.post(glare_type='Bloom', threshold=1.0, glare_size=0.55, glare_strength=0.35)
elif look == "glow":
    parts, (W, H) = load(0.07, 0.007)
    side = mat("side", (0.03, 0.03, 0.035, 1), rough=0.4)
    em = gradient_emission("glow", [(0.0, mixc(MAIN, (1, 0.3, 0.4), 0.6)), (0.5, (1.0, 0.45, 0.30, 1)),
                                    (1.0, (1.0, 0.78, 0.25, 1))], 1.6, W)   # 5 면 흰색으로 탄다(⑰e)
    for o, _, _ in parts:
        assign(o, em, side)
    plate(mat("black", (0.012, 0.012, 0.014, 1), rough=0.6))
    S.world_gradient()
    S.post(glare_type='Bloom', threshold=0.9, glare_size=0.7, glare_strength=0.6)
else:
    raise SystemExit(f"모르는 룩: {look}")

S.camera_at(CAM, (0, 0, 0.03), lens=LENS)
bpy.context.scene.camera.data.sensor_fit = 'HORIZONTAL'
S.render_to(A.out, width=A.w, height=A.h)
