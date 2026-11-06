# -*- coding: utf-8 -*-
"""정리 — 흰 배경 빼기 · 겹친 획 합치기 · 잡티 빼기 · 살짝 굵게/가늘게. 결과는 mm 좌표(잉크 왼쪽 위 = 0,0)의 평평한 경로.

모양을 «다시 그리는» 건 전부 칠한 뒤 vclean(수산나 메이커·sign-proof 와 같은 벡터화기)으로 다시 딴다 — 새 벡터화기를 짓지 않는다.
"""
import os
import re
import sys

import cv2
import numpy as np

from . import measure, svgio

FONTAI = os.environ.get('FONTAI_CODE', os.path.join(os.path.expanduser('~'), 'font-ai', 'code'))


def revector(m, ppm, pad_px):
    """마스크 → 경로(mm, 잉크 왼쪽 위 0,0). vclean 은 반~한 픽셀 밀리므로 잉크 상자에 다시 맞춘다(maker_up.retrace 와 같은 처방)."""
    sys.path.insert(0, FONTAI)
    import vclean
    import letter_svg as L
    g = np.where(m, 0, 255).astype(np.uint8)
    cs = vclean.clean(g, up=1, min_area=4)
    raw = L.to_path(cs)
    if not raw:
        return ''
    ys, xs = np.where(m)
    ix0, iy0, ix1, iy1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    tx0, ty0, tx1, ty1 = svgio.bbox(raw)
    sx, sy = (ix1 - ix0) / (tx1 - tx0), (iy1 - iy0) / (ty1 - ty0)
    return svgio.move(raw, lambda v: (v - tx0) * sx / ppm, lambda v: (v - ty0) * sy / ppm)


def strip_bg(layers, vb):
    """캔버스 전체를 덮는 사각형 층(흰 배경)을 뺀다."""
    if not vb:
        return layers
    area = vb[2] * vb[3]
    keep = []
    for d, f in layers:
        x0, y0, x1, y1 = svgio.bbox(d)
        if (x1 - x0) * (y1 - y0) >= area * 0.97 and len(svgio.subpaths(d)) <= 2:
            continue
        keep.append((d, f))
    return keep


def reshape(d, w_mm, ppm=4.0, thicken_mm=0.0, min_speck_mm2=0.0, merge=True):
    """칠해서 → (겹침 합치기) → (굵게/가늘게) → (잡티 빼기) → 다시 따기. thicken_mm 는 «획 폭»에 더하는 양(양쪽 합)."""
    rule = 'nonzero' if merge else 'evenodd'
    m, ppm, (px, py) = measure.mask(d, w_mm, ppm, rule=rule)
    if thicken_mm:
        r = max(1, int(round(abs(thicken_mm) / 2 * ppm)))
        ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        m = (cv2.dilate if thicken_mm > 0 else cv2.erode)(m.astype(np.uint8), ker) > 0
    if min_speck_mm2:
        n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
        for i in range(1, n):
            if st[i, 4] / ppm / ppm < min_speck_mm2:
                m[lab == i] = False
    return revector(m, ppm, px)


def per_color(path, w_mm, **kw):
    """색마다 따로 reshape — 여러 색 로고도 색은 그대로. 같은 자리를 지키도록 전체 상자 기준으로 옮긴다."""
    layers, vb = svgio.read(path)
    layers = strip_bg(layers, vb)
    allx0, ally0, allx1, ally1 = svgio.bbox(''.join(d for d, _ in layers))
    k = w_mm / (allx1 - allx0)
    out = []
    for d, f in layers:
        x0, y0, x1, y1 = svgio.bbox(d)
        nd = reshape(d, (x1 - x0) * k, **kw)
        if not nd:
            continue
        nx0, ny0, _, _ = svgio.bbox(nd)
        ox, oy = (x0 - allx0) * k, (y0 - ally0) * k
        out.append((svgio.move(nd, lambda v: v - nx0 + ox, lambda v: v - ny0 + oy), f))
    return out
