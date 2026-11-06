# -*- coding: utf-8 -*-
"""Blender 안에서 쓰는 내보내기 부품(bpy 만 쓴다, 다른 의존 없음). 장면을 스케치업이 여는 COLLADA(.dae)로 쓴다.
Blender 5.0 부터 COLLADA 내보내기가 빠져서 직접 쓴다. 장면 스크립트에서
    sys.path.insert(0, r'<작업 폴더>'); from forge.lib.bldae import write_dae
로 부른다.

- 단위는 mm(`<unit meter="0.001">`), Z 위. 스케치업은 이 단위를 읽어 실물 크기로 연다.
- 오브젝트 하나 = 노드 하나(스케치업에서 그룹 하나), 이름 그대로. 모디파이어는 적용된 모양으로 쓴다.
- 면은 삼각형으로 쓴다. 스케치업에서 가져올 때 «같은 평면 면 합치기(Merge Coplanar Faces)»를 켜면 대각선이 사라진다.
- 재질은 Principled 의 Base Color(선형 → 화면값)와 투과(Transmission Weight)만 옮긴다. 셰이더로만 낸 모양(Bevel 셰이더 원형 마감)은 안 옮겨진다.
"""
import bpy
from xml.sax.saxutils import escape


def _srgb(v):
    return 1.055 * v ** (1 / 2.4) - 0.055 if v > 0.0031308 else 12.92 * v


def _mat_info(m):
    col, trans = (0.8, 0.8, 0.8), 0.0
    if m and m.use_nodes and 'Principled BSDF' in m.node_tree.nodes:
        b = m.node_tree.nodes['Principled BSDF']
        col = tuple(_srgb(c) for c in b.inputs['Base Color'].default_value[:3])
        trans = b.inputs['Transmission Weight'].default_value
    return col, trans


def write_dae(path, objects=None, opacity_glass=0.35, author='SusannaDesigner'):
    """objects: 쓸 메시 오브젝트 목록(None 이면 장면의 모든 메시). 투과가 있는 재질은 불투명도 opacity_glass 로 쓴다.
    돌려주는 값: {'objects': n, 'tris': n, 'bounds_mm': [x0,y0,z0,x1,y1,z1]}"""
    dg = bpy.context.evaluated_depsgraph_get()
    obs = [o for o in (objects if objects is not None else bpy.context.scene.objects) if o.type == 'MESH']
    mats, geoms, nodes = {}, [], []
    lo, hi = [1e18] * 3, [-1e18] * 3
    ntri = 0
    for gi, ob in enumerate(obs):
        ev = ob.evaluated_get(dg); me = ev.to_mesh(); me.calc_loop_triangles()
        mw = ob.matrix_world
        pos = []
        for v in me.vertices:
            p = mw @ v.co
            q = (p.x * 1000.0, p.y * 1000.0, p.z * 1000.0); pos.append(q)
            for k in range(3): lo[k] = min(lo[k], q[k]); hi[k] = max(hi[k], q[k])
        by_mat = {}
        for t in me.loop_triangles:
            by_mat.setdefault(t.material_index, []).append(tuple(t.vertices))
        slots = [s.material for s in ob.material_slots] or [None]
        gid = f'g{gi}'
        tris_xml = []
        for mi, tris in sorted(by_mat.items()):
            m = slots[mi] if mi < len(slots) else None
            key = m.name if m else '_기본'
            if key not in mats: mats[key] = (f'm{len(mats)}', m)
            mid = mats[key][0]
            idx = ' '.join(f'{a} {b} {c}' for a, b, c in tris); ntri += len(tris)
            tris_xml.append((mid, f'<triangles material="{mid}" count="{len(tris)}"><input semantic="VERTEX" source="#{gid}-v" offset="0"/><p>{idx}</p></triangles>'))
        flat = ' '.join(f'{x:.4f} {y:.4f} {z:.4f}' for x, y, z in pos)
        geoms.append(f'<geometry id="{gid}" name="{escape(ob.name)}"><mesh>'
                     f'<source id="{gid}-p"><float_array id="{gid}-pa" count="{len(pos) * 3}">{flat}</float_array>'
                     f'<technique_common><accessor source="#{gid}-pa" count="{len(pos)}" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source>'
                     f'<vertices id="{gid}-v"><input semantic="POSITION" source="#{gid}-p"/></vertices>'
                     + ''.join(x for _, x in tris_xml) + '</mesh></geometry>')
        binds = ''.join(f'<instance_material symbol="{mid}" target="#{mid}-mat"/>' for mid, _ in tris_xml)
        nodes.append(f'<node id="n{gi}" name="{escape(ob.name)}" type="NODE"><instance_geometry url="#{gid}"><bind_material><technique_common>{binds}</technique_common></bind_material></instance_geometry></node>')
        ev.to_mesh_clear()
    effects, materials = [], []
    for name, (mid, m) in mats.items():
        (r, g, b), trans = _mat_info(m)
        op = opacity_glass if trans > 0.3 else 1.0
        effects.append(f'<effect id="{mid}-fx"><profile_COMMON><technique sid="common"><lambert>'
                       f'<diffuse><color>{r:.4f} {g:.4f} {b:.4f} 1</color></diffuse>'
                       f'<transparent opaque="A_ONE"><color>1 1 1 {op:.3f}</color></transparent><transparency><float>1</float></transparency>'
                       f'</lambert></technique></profile_COMMON></effect>')
        materials.append(f'<material id="{mid}-mat" name="{escape(name)}"><instance_effect url="#{mid}-fx"/></material>')
    xml = ('<?xml version="1.0" encoding="utf-8"?>\n'
           '<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">'
           f'<asset><contributor><author>{escape(author)}</author></contributor><unit name="millimeter" meter="0.001"/><up_axis>Z_UP</up_axis></asset>'
           '<library_effects>' + ''.join(effects) + '</library_effects>'
           '<library_materials>' + ''.join(materials) + '</library_materials>'
           '<library_geometries>' + ''.join(geoms) + '</library_geometries>'
           '<library_visual_scenes><visual_scene id="scene" name="scene">' + ''.join(nodes) + '</visual_scene></library_visual_scenes>'
           '<scene><instance_visual_scene url="#scene"/></scene></COLLADA>\n')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(xml)
    return {'objects': len(obs), 'tris': ntri, 'bounds_mm': [round(v, 2) for v in lo + hi]}


def read_dae(path):
    """write_dae 로 쓴 .dae 를 다시 장면에 올린다(검사용: 넘길 파일 자체를 렌더해 본다). 노드마다 메시 오브젝트 하나, 재질은 이름·색·불투명도만.
    돌려주는 값: {재질 이름: (bpy 재질, (r,g,b), 불투명도)}"""
    import xml.etree.ElementTree as ET
    ns = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}
    root = ET.parse(path).getroot()
    k = float(root.find('c:asset/c:unit', ns).get('meter'))
    fx = {}
    for e in root.findall('.//c:effect', ns):
        col = [float(v) for v in e.find('.//c:diffuse/c:color', ns).text.split()][:3]
        op = float(e.find('.//c:transparent/c:color', ns).text.split()[3])
        fx[e.get('id')] = (col, op)
    mats = {}
    for m in root.findall('.//c:material', ns):
        col, op = fx[m.find('c:instance_effect', ns).get('url')[1:]]
        bm = bpy.data.materials.new(m.get('name')); bm.use_nodes = True
        lin = tuple(((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in col)
        bm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*lin, 1)
        mats[m.get('id')] = bm; mats[m.get('name')] = (bm, tuple(col), op)
    geo = {g.get('id'): g for g in root.findall('.//c:geometry', ns)}
    for n in root.findall('.//c:visual_scene/c:node', ns):
        ig = n.find('c:instance_geometry', ns); g = geo[ig.get('url')[1:]]
        bind = {im.get('symbol'): im.get('target')[1:] for im in ig.findall('.//c:instance_material', ns)}
        a = [float(v) * k for v in g.find('.//c:float_array', ns).text.split()]
        vs = [tuple(a[i:i + 3]) for i in range(0, len(a), 3)]
        faces, fm, slots = [], [], []
        for t in g.findall('.//c:triangles', ns):
            mid = bind[t.get('material')]
            if mid not in slots: slots.append(mid)
            p = [int(v) for v in t.find('c:p', ns).text.split()]
            for i in range(0, len(p), 3):
                faces.append(tuple(p[i:i + 3])); fm.append(slots.index(mid))
        me = bpy.data.meshes.new(n.get('name')); me.from_pydata(vs, [], faces)
        for s in slots: me.materials.append(mats[s])
        for f, mi in zip(me.polygons, fm): f.material_index = mi
        ob = bpy.data.objects.new(n.get('name'), me); bpy.context.scene.collection.objects.link(ob)
    return {k_: v for k_, v in mats.items() if isinstance(v, tuple)}
