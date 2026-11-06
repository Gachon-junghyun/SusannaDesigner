# -*- coding: utf-8 -*-
"""2D 윤곽 부품 — 판·철판·받침 모양을 «접선이 이어지게» 다듬는 함수들. 단위는 mm, 좌표는 (x, 높이).

처음 쓰인 곳: jobs/2026-10_고객K(6차 철판 받침). 거기서 사람이 세 번 거절한 끝에 통과한 모양을 함수로 굳혔다.
- 오목 구석을 메울 땐 «구석만» 메운다(띠·상자·S자 덧대기는 거절됐다) → fillet_fill / bezier_fill
- 메우기 전에 가장 좁은 폭(neck)을 재서 어느 구석이 원인인지 본다
- 꼭짓점 아래로 받침을 내릴 땐 세로 기둥 + 접선 원호 → stem_under_vertex
- 합친 뒤엔 폭 0 가시를 지운다 → despike
"""
import math
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union


def sharpen(poly, min_len=3.0):
    """띄운 다각형의 긴 변끼리 연장해 꼭지를 세운다(둥근 꼭지 점이 남아 여백이 2.8 로 줄던 문제, 10-21)."""
    pts = list(poly.exterior.coords)[:-1]
    segs = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts)) if math.dist(pts[i], pts[(i + 1) % len(pts)]) >= min_len]
    out = []
    for i in range(len(segs)):
        (p1, p2), (p3, p4) = segs[i], segs[(i + 1) % len(segs)]
        d = (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0])
        if abs(d) < 1e-12:
            out.append(p2); continue
        t = ((p1[0] - p3[0]) * (p3[1] - p4[1]) - (p1[1] - p3[1]) * (p3[0] - p4[0])) / d
        out.append((p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])))
    return Polygon(out)


def corner_at(poly, near):
    """near 에 가장 가까운 꼭짓점 P 와, 그 앞뒤 변의 단위 방향(P 에서 멀어지는 쪽) u1·u2."""
    pts = list(poly.exterior.coords)[:-1]
    i = min(range(len(pts)), key=lambda k: math.dist(pts[k], near))
    P, a, b = pts[i], pts[i - 1], pts[(i + 1) % len(pts)]
    u = lambda q: ((q[0] - P[0]) / math.dist(P, q), (q[1] - P[1]) / math.dist(P, q))
    return P, u(a), u(b)


def fillet_fill(P, u1, u2, r, n=120):
    """오목 구석 P(두 변 방향 u1·u2)를 반지름 r 원호로 메우는 조각과 원호 점들. 원호는 두 변에 접한다(G1)."""
    ang = math.acos(max(-1, min(1, u1[0] * u2[0] + u1[1] * u2[1])))
    k = r / math.tan(ang / 2)
    T1 = (P[0] + k * u1[0], P[1] + k * u1[1]); T2 = (P[0] + k * u2[0], P[1] + k * u2[1])
    bis = (u1[0] + u2[0], u1[1] + u2[1]); bl = math.hypot(*bis); bis = (bis[0] / bl, bis[1] / bl)
    C = (P[0] + r / math.sin(ang / 2) * bis[0], P[1] + r / math.sin(ang / 2) * bis[1])
    a1 = math.atan2(T1[1] - C[1], T1[0] - C[0]); a2 = math.atan2(T2[1] - C[1], T2[0] - C[0])
    da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
    arc = [(C[0] + r * math.cos(a1 + da * i / n), C[1] + r * math.sin(a1 + da * i / n)) for i in range(n + 1)]
    return Polygon([P] + arc), arc


def bezier_fill(P, u1, d1, u2, d2, n=400):
    """오목 구석 P 를 2차 베지어(조절점 = P)로 메움. 끝점에서 두 변에 접한다(G1). 두 변 쪽 길이 d1·d2 를 따로 줄 수 있어
    둔각 구석을 «한쪽은 길게, 한쪽은 얕게»(예: 마름모 밑 36, 아래로 12) 메울 때 쓴다."""
    A = (P[0] + d1 * u1[0], P[1] + d1 * u1[1]); B = (P[0] + d2 * u2[0], P[1] + d2 * u2[1])
    crv = [((1 - t) ** 2 * A[0] + 2 * t * (1 - t) * P[0] + t * t * B[0], (1 - t) ** 2 * A[1] + 2 * t * (1 - t) * P[1] + t * t * B[1])
           for t in (i / n for i in range(n + 1))]
    return Polygon([P] + crv), crv


def corner_fillet_rect(cx, cz, side, r, n=128):
    """세로선 x=cx 와 가로선 z=cz 가 만나는 직각 구석(빈 쪽이 side: -1 왼쪽, +1 오른쪽, 아래쪽)을 반지름 r 로 메우는 조각.
    기둥이 몸판 밑변에 붙는 자리(10-21 철판 다리)."""
    cc = (cx + side * r, cz - r)
    sq = box(min(cx, cx + side * r), cz - r, max(cx, cx + side * r), cz + 1)
    circ = Polygon([(cc[0] + r * math.cos(2 * math.pi * k / n), cc[1] + r * math.sin(2 * math.pi * k / n)) for k in range(n)])
    return sq.difference(circ)


def stem_under_vertex(poly, base_z, width, r):
    """poly 의 가장 낮은 꼭짓점 아래로 폭 width 세로 기둥을 base_z 까지 내리고, 기둥 옆선과 양쪽 변이 만나는 구석을 반지름 r 로.
    바닥은 평평(용접 자리). 10-22 «노란 꼭짓점 아래도 기둥처럼 박스까지, 둥글게 해서 평평하게»."""
    pts = list(poly.exterior.coords)[:-1]
    i = min(range(len(pts)), key=lambda k: pts[k][1]); T0 = pts[i]
    side = {}
    for nb in (pts[i - 1], pts[(i + 1) % len(pts)]):
        u = (nb[0] - T0[0], nb[1] - T0[1]); l = math.hypot(*u); u = (u[0] / l, u[1] / l)
        sgn = -1 if u[0] < 0 else 1
        xs = T0[0] + sgn * width / 2
        t = (xs - T0[0]) / u[0]; P = (xs, T0[1] + t * u[1])
        fill, arc = fillet_fill(P, (0.0, -1.0), u, r)
        side[sgn] = (P, fill, arc, xs)
    (PL, fL, aL, xL), (PR, fR, aR, xR) = side[-1], side[1]
    stem = Polygon([PL, (xL, base_z), (xR, base_z), PR])
    out = unary_union([stem, fL, fR]).buffer(0)
    return out, dict(tip=T0, x0=xL, x1=xR, w=xR - xL, r=r, corner_z=(PL[1], PR[1]), ends=[aL[0], aL[-1], aR[0], aR[-1]])


def despike(poly, eps=1e-3):
    """같은 선 위에서 합쳐진 조각이 남긴 폭 0 가시를 지운다(10-22 삼각형 발 이음매에서 179.9도 꺾임으로 잡힘)."""
    return poly.buffer(eps, join_style='mitre').buffer(-eps, join_style='mitre')


def max_turn(pts, at, radius=1.5):
    """닫힌 윤곽에서 at 점들 둘레(radius mm 안 꼭짓점)의 꺾임 각 최대(도). 곡선 이음매가 접선으로 이어졌나 재는 데 쓴다.
    펼친 토막 탓에 0 이 아니다 — 더 잘게 펼쳐 0 으로 줄어들면 접선 연속이다."""
    out = []
    N = len(pts)
    for q in at:
        for j in [k for k in range(N) if math.dist(pts[k], q) < radius]:
            a, b, c = pts[(j - 1) % N], pts[j % N], pts[(j + 1) % N]
            v1 = (b[0] - a[0], b[1] - a[1]); v2 = (c[0] - b[0], c[1] - b[1])
            if math.hypot(*v1) < 1e-6 or math.hypot(*v2) < 1e-6:
                continue
            out.append(abs(math.degrees(math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1[0] * v2[0] + v1[1] * v2[1]))))
    return max(out) if out else 0.0


def neck(poly, P_a, P_b, rad=60):
    """두 구석 사이 «가장 좁은 폭»: 윤곽을 따라 각 구석 앞뒤 rad mm 사슬 둘 사이 최소 거리."""
    pts = list(poly.exterior.segmentize(1.0).coords)[:-1]; N = len(pts)

    def ch(q):
        i = min(range(N), key=lambda k: math.dist(pts[k], q))
        return LineString([pts[(i + j) % N] for j in range(-int(rad), int(rad) + 1)])
    return ch(P_a).distance(ch(P_b))
