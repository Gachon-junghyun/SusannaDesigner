# -*- coding: utf-8 -*-
"""둥근 앞 모서리 압출(호스트 파이썬, shapely). 채널 글자 «원형 마감»을 렌더 셰이더가 아니라 실제 형상으로 만든다.

방법(round_edge: offset_loft): 2D 윤곽을 앞에서부터 1/4 원을 따라 안으로 깎은(negative buffer) 고리 여러 층을 만들고,
이웃한 두 층을 둘레 비율로 이어 붙인다(점 수가 달라도 된다). 앞면은 가장 안쪽 층을 삼각분할, 뒷면은 원래 윤곽.
Blender BEVEL(형상 깎기)은 점이 촘촘한 S 끝에서 교점이 튀고 앞면에 선을 남겼다(10-22). 깎은 윤곽은 shapely 가 만들므로 자기 교차가 없다.

    from forge.lib.roundext import rounded_prism
    m = rounded_prism(ext, holes, r=8, depth=60, steps=6)   # 좌표 mm (가로 x, 높이 z), 앞면이 깊이 0
    m['verts'] = [[x, z, d], ...]; m['front'] = 앞면과 둥근 띠 삼각형; m['side'] = 옆면과 뒷면 삼각형; m['r'] = 실제로 쓴 반지름
"""
import math
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon, MultiPolygon, LinearRing, Point
from shapely.geometry.polygon import orient


def _ring(coords, tol=0.01):
    pts = list(coords)[:-1]
    out = []
    for p in pts:
        if not out or math.dist(out[-1], p) > tol:
            out.append(tuple(p))
    if len(out) > 1 and math.dist(out[0], out[-1]) <= tol:
        out.pop()
    return out


def _clean(Q):
    # 0.01mm 안의 겹친 점을 뺀 다각형. 삼각분할도 이 다각형으로 해야 띠와 앞뒷면이 같은 점을 쓴다
    Q = orient(Polygon(_ring(Q.exterior.coords), [_ring(h.coords) for h in Q.interiors]), 1.0)
    return Q if Q.is_valid else None


def _level(P, inset):
    Q = P if inset <= 1e-9 else P.buffer(-inset, quad_segs=6, join_style='round')
    if isinstance(Q, MultiPolygon) or Q.is_empty or len(Q.interiors) != len(P.interiors):
        return None
    return _clean(Q)


def rounded_prism(ext, holes, r=8.0, depth=60.0, steps=6, shrink=(1.0, 0.75, 0.5, 0.25)):
    P = Polygon(ext, holes).buffer(0)
    if isinstance(P, MultiPolygon):
        raise ValueError('윤곽이 둘로 나뉜다')
    P = _clean(P)
    for k in shrink:   # 가는 곳이 반지름을 못 받으면(층이 갈라지거나 구멍이 사라지면) 반지름을 줄인다
        rr = r * k
        th = [math.radians(90.0 * i / steps) for i in range(steps + 1)]
        lv = [(_level(P, rr * (1 - math.sin(t))), rr * (1 - math.cos(t))) for t in th]
        if all(q is not None for q, _ in lv):
            break
    else:
        raise ValueError('반지름을 줄여도 층이 갈라진다')

    verts, front, side = [], [], []
    idx = {}

    def vid(x, z, d):
        key = (round(x, 4), round(z, 4), round(d, 4))
        if key not in idx:
            idx[key] = len(verts); verts.append([x, z, d])
        return idx[key]

    def rings(Q, d):
        out = [[vid(x, z, d) for x, z in _ring(Q.exterior.coords)]]
        for h in Q.interiors:
            out.append([vid(x, z, d) for x, z in _ring(h.coords)])
        return out

    def stitch(B, A, sink):
        # A = 덜 깎인(바깥) 고리, B = 더 깎인(안) 고리. B 의 점을 A 위로 내린 자리(둘레 거리)로 두 고리를 한 줄에 세워 잇는다.
        # 둘레 «비율»로 이으면 짧은 끝(S 꼬리)에서 층이 밀려 계단이 생겼다(10-23 확대 검수).
        pa = [verts[i][:2] for i in A]; pb = [verts[i][:2] for i in B]
        LA = LinearRing(pa); L = LA.length
        sa = [0.0]
        for a, b in zip(pa, pa[1:] + pa[:1]):
            sa.append(sa[-1] + math.dist(a, b))
        tb = [LA.project(Point(q)) for q in pb]
        j0 = min(range(len(tb)), key=lambda j: tb[j])
        B = B[j0:] + B[:j0]; tb = tb[j0:] + tb[:j0]
        for j in range(1, len(tb)):   # 내린 자리가 거꾸로 가면(오목 구석) 앞 점에 붙인다
            tb[j] = max(tb[j], tb[j - 1])
        tb.append(L + tb[0])
        na, nb = len(A), len(B); i = j = 0
        while i < na or j < nb:
            if j >= nb or (i < na and sa[i + 1] <= tb[j + 1]):
                sink.append((A[i % na], A[(i + 1) % na], B[j % nb])); i += 1
            else:
                sink.append((A[i % na], B[(j + 1) % nb], B[j % nb])); j += 1

    def match(R0, R1, Q0, Q1):
        # 바깥 고리는 바깥끼리, 구멍은 무게중심이 가장 가까운 것끼리
        pairs = [(R0[0], R1[0])]
        c0 = [Polygon(h).centroid for h in Q0.interiors]; c1 = [Polygon(h).centroid for h in Q1.interiors]
        used = set()
        for a, ca in enumerate(c0):
            b = min((b for b in range(len(c1)) if b not in used), key=lambda b: ca.distance(c1[b]))
            used.add(b); pairs.append((R0[a + 1], R1[b + 1]))
        return pairs

    L = [(Q, d, rings(Q, d)) for Q, d in lv]
    for (Q0, _, R0), (Q1, _, R1) in zip(L, L[1:]):   # 앞(안쪽) → 원래 윤곽, 둥근 띠
        for a, b in match(R0, R1, Q0, Q1):
            stitch(a, b, front)
    Qf, d0, _ = L[0]
    for t in constrained_delaunay_triangles(Qf).geoms:   # 앞면
        c = _ring(t.exterior.coords, tol=0.0)
        front.append(tuple(vid(x, z, d0) for x, z in c))
    Pn, dr, Rn = L[-1]
    Rb = rings(Pn, depth)
    for a, b in zip(Rn, Rb):   # 옆면: 둥근 띠 끝(깊이 rr)에서 뒤까지
        n = len(a)
        for k in range(n):
            side.append((a[k], a[(k + 1) % n], b[(k + 1) % n])); side.append((a[k], b[(k + 1) % n], b[k]))
    for t in constrained_delaunay_triangles(Pn).geoms:   # 뒷면
        c = _ring(t.exterior.coords, tol=0.0)
        side.append(tuple(vid(x, z, depth) for x, z in c))
    return {'verts': verts, 'front': front, 'side': side, 'r': rr}
