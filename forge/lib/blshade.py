# -*- coding: utf-8 -*-
"""Blender 안에서 쓰는 재질 부품(bpy 만 쓴다, 다른 의존 없음). 장면 스크립트에서
    sys.path.insert(0, r'<작업 폴더>'); from forge.lib.blshade import bevel_round
로 부른다.
"""


def bevel_round(materials, radius_m, samples=16):
    """채널 글자 «원형 마감»: 형상은 그대로 두고 렌더러가 모서리를 반지름 radius_m(미터)로 둥글게 칠하게 한다(Cycles Bevel 셰이더).
    방법 대장 round_edge 의 shader_bevel(10-22 1건 승, 아직 공식 아님). 형상을 깎는 BEVEL 은 S 끝 깨짐·마름모 앞면 선·삼각형 분홍 줄을 남겼다(10-22)."""
    for m in materials:
        nt = m.node_tree; b = nt.nodes['Principled BSDF']
        bv = nt.nodes.new('ShaderNodeBevel'); bv.inputs['Radius'].default_value = radius_m; bv.samples = samples
        nt.links.new(bv.outputs['Normal'], b.inputs['Normal'])
        if 'Coat Normal' in b.inputs:
            nt.links.new(bv.outputs['Normal'], b.inputs['Coat Normal'])
