# -*- coding: utf-8 -*-
"""재기 — 경로를 실제 크기(mm)로 칠해 최소 획·속공간·조각·잡티·까치발 자리를 잰다.

자는 /sign-proof·수산나 메이커와 같다: 획 = 골격(이웃 둘 이상) 거리 하위 10% × 2 · 잡티 = 400mm² 미만 조각.
"""
import math

import cv2
import fitz
import numpy as np

from . import svgio

SPECK_MM2 = 400.0


def mask(d, w_mm, ppm=2.0, pad_mm=20.0, rule='evenodd', frame=None):
    """d 의 잉크 가로를 w_mm 로 놓고 ppm(px/mm) 로 칠한 마스크. → (mask, ppm, (ox, oy) 잉크 왼쪽 위의 픽셀 자리).
    frame=(x0,y0,x1,y1) 을 주면 그 상자 기준으로 칠한다 — 여러 줄을 «같은 자리»에 따로 칠해 비교할 때."""
    x0, y0, x1, y1 = frame or svgio.bbox(d)
    k = w_mm / (x1 - x0)                      # 단위 → mm
    pad_u = pad_mm / k
    W, H = (x1 - x0) + 2 * pad_u, (y1 - y0) + 2 * pad_u
    pw, ph = int(round(W * k * ppm)), int(round(H * k * ppm))
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{pw}" height="{ph}" viewBox="{x0 - pad_u} {y0 - pad_u} {W} {H}">'
           f'<path fill="#000" fill-rule="{rule}" d="{d}"/></svg>')
    pg = fitz.open('svg', svg.encode())[0]
    pm = pg.get_pixmap(matrix=fitz.Matrix(pw / pg.rect.width, ph / pg.rect.height), alpha=True)
    a = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, pm.n)[..., 3] > 127
    return a, ppm, (pad_mm * ppm, pad_mm * ppm)


def strokes(m, ppm):
    """(하위 10%, 가운데) 획 폭 mm. 끝점·잡티는 뺀다(이웃 둘 이상인 골격점만)."""
    a = m.astype(np.uint8)
    dist = cv2.distanceTransform(a, cv2.DIST_L2, 5)
    sk = cv2.ximgproc.thinning(a * 255) > 0
    nb = cv2.filter2D(sk.astype(np.uint8), -1, np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], np.uint8), borderType=cv2.BORDER_CONSTANT)
    core = sk & (nb >= 2)
    v = dist[core] if core.sum() > 20 else dist[sk]
    if not len(v):
        return 0.0, 0.0
    return float(np.percentile(v, 10)) * 2 / ppm, float(np.percentile(v, 50)) * 2 / ppm


def holes(m, ppm):
    """가장자리에 안 닿는 빈 덩이(= 속공간·오려 낸 틈)마다 폭 mm. 작은 순."""
    inv = (~m).astype(np.uint8)
    n, lab = cv2.connectedComponents(inv)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    dist = cv2.distanceTransform(inv, cv2.DIST_L2, 5)
    out = []
    for i in range(1, n):
        if i in border:
            continue
        out.append(float(dist[lab == i].max()) * 2 / ppm)
    return sorted(out)


def pieces(m, ppm):
    """떨어진 조각들 → [(면적 mm², 상자(x,y,w,h) px)]."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    return [(st[i, 4] / ppm / ppm, tuple(int(v) for v in st[i, :4])) for i in range(1, n)], lab


def pin_layout(m, ppm, d_mm=10.0, edge_mm=3.0, per_min=2, gap_mm=300.0, small_mm=80.0, speck_mm2=60.0):
    """조각마다 까치발 자리(mm, 마스크 왼쪽 위 기준). 규칙은 전부 인자 — 공장 기준을 받으면 바꾼다.
    ① 봉 지름 + 가장자리 여유가 들어가는 «두꺼운 곳»만 후보 ② 개수 = max(최소, 긴 변 ÷ 간격 올림), 작은 조각은 1개
    ③ 가장 두꺼운 곳부터 «이미 고른 자리에서 가장 먼 후보»(먼 점 고르기) ④ 후보가 없으면 가장 두꺼운 한 점 + «좁음»."""
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    dt = cv2.distanceTransform(m.astype(np.uint8), cv2.DIST_L2, 5) / ppm
    need = d_mm / 2 + edge_mm
    pins, narrow, count = [], 0, 0
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a / ppm / ppm < speck_mm2:
            continue
        count += 1
        ys, xs = np.where(lab == i)
        dd = dt[ys, xs]
        ext = max(w, h) / ppm
        k = 1 if ext < small_mm else max(per_min, math.ceil(ext / gap_mm))
        ok = dd >= need
        if not ok.any():
            narrow += 1
            j = int(np.argmax(dd))
            pins.append(dict(piece=count, x=xs[j] / ppm, y=ys[j] / ppm, narrow=True))
            continue
        cx, cy, cd = xs[ok], ys[ok], dd[ok]
        if len(cx) > 4000:
            sel = np.random.default_rng(i).choice(len(cx), 4000, replace=False)
            cx, cy, cd = cx[sel], cy[sel], cd[sel]
        chosen = [int(np.argmax(cd))]
        mind = np.hypot(cx - cx[chosen[0]], cy - cy[chosen[0]])
        for _ in range(min(k, len(cx)) - 1):
            j = int(np.argmax(mind))
            chosen.append(j)
            mind = np.minimum(mind, np.hypot(cx - cx[j], cy - cy[j]))
        pins += [dict(piece=count, x=cx[j] / ppm, y=cy[j] / ppm, narrow=False) for j in chosen]
    return pins, count, narrow


def report(d, w_mm, ppm=2.0, pin=None):
    m, ppm, _ = mask(d, w_mm, ppm)
    s10, s50 = strokes(m, ppm)
    hs = holes(m, ppm)
    ps, _ = pieces(m, ppm)
    x0, y0, x1, y1 = svgio.bbox(d)
    out = dict(w_mm=w_mm, h_mm=w_mm * (y1 - y0) / (x1 - x0), stroke_p10=s10, stroke_p50=s50,
               min_hole=hs[0] if hs else None, holes=len(hs), pieces=len(ps), specks=sum(a < SPECK_MM2 for a, _ in ps))
    if pin:
        pins, cnt, narrow = pin_layout(m, ppm, **pin)
        out.update(pins=len(pins), pin_narrow=narrow)
    return out
