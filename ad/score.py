# -*- coding: utf-8 -*-
"""벡터 후보 채점 — 결투(/duel)의 «같은 자». 기준 그림(깨끗한 원본 PNG) 하나에 후보 벡터 여럿을 잰다.

  fidelity   원본 잉크와 겹치는 정도(IoU) — 높을수록 원본과 같다
  wiggle     윤곽의 잔물결(둘레 / 다림질한 둘레 − 1, ‰) — 낮을수록 매끈
  corners    원본의 뚜렷한 꼭짓점 중 후보에도 있는 비율 — 높을수록 꼭짓점이 살아 있다
  specks     아주 작은 떨어진 조각 수 — 0 이어야 한다
  nodes      경로 명령 수(C·L·Q·A …) — 적을수록 손보기 쉽다(참고값)
  fab        --h 를 주면 relogo.fabcheck 의 최소 폭·선 끝(mm)

🔴 후보는 어떤 구조의 SVG 든 받는다(획·원·변환). 그라디언트 칠은 PyMuPDF 가 검정으로 그려서(2026-10-03 실측)
   가운데 색으로 바꿔 그린다. .ai/.pdf 도 받는다. 위치·크기는 «잉크 상자»로 맞춰서 잰다(캔버스가 달라도 된다).
"""
import io
import json
import os
import re
import tempfile

import numpy as np
from PIL import Image

NORM_H = 2000   # 잉크 높이를 이 픽셀로 맞춰서 잰다(해상도가 달라도 같은 자)


def _flat_svg(path):
    s = io.open(path, encoding='utf-8', errors='replace').read()
    stops = {}
    for m in re.finditer(r'<(linearGradient|radialGradient)[^>]*id="([^"]+)"[^>]*>(.*?)</\1>', s, re.S):
        cols = re.findall(r'stop-color="([^"]+)"', m.group(3)) or re.findall(r'stop-color:\s*([^;"]+)', m.group(3))
        if cols:
            stops[m.group(2)] = cols[len(cols) // 2]
    s = re.sub(r'url\(#([^)]+)\)', lambda m: stops.get(m.group(1), '#000'), s)
    t = os.path.join(tempfile.mkdtemp(prefix='ad_score_'), 'flat.svg')
    io.open(t, 'w', encoding='utf-8').write(s)
    return t


def _render(path, px=3000):
    import fitz
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.png', '.jpg', '.jpeg', '.webp'):
        im = Image.open(path).convert('RGB')
        if im.width > px:   # 9000px 원본을 그대로 쓰면 메모리가 모자란다(2026-10-03 실측)
            im = im.resize((px, round(im.height * px / im.width)), Image.LANCZOS)
        return np.array(im)
    src = _flat_svg(path) if ext == '.svg' else path
    pg = fitz.open(src)[0]
    z = px / pg.rect.width
    pm = pg.get_pixmap(matrix=fitz.Matrix(z, z), alpha=False)
    return np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, pm.n)[..., :3].copy()


def _mask(rgb):
    from .relogo import _ink
    m, _, _, _ = _ink(rgb, sig=1.0, drop_grey=True, speck=0)   # 채점은 아무것도 지우지 않고 본다
    return m


def _norm(m):
    """잉크 상자로 잘라 높이 NORM_H 로."""
    import cv2
    ys, xs = np.where(m)
    c = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    k = NORM_H / c.shape[0]
    return (cv2.resize(c.astype(np.float32), (max(1, round(c.shape[1] * k)), NORM_H), interpolation=cv2.INTER_AREA) > 0.5).astype(np.uint8)


def _perim(m):
    import cv2
    cs, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    return sum(cv2.arcLength(c, True) for c in cs)


def _wiggle(m):
    import cv2
    p0 = _perim(m)
    sm = (cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3.0) > 0.5).astype(np.uint8)
    return (p0 / max(_perim(sm), 1) - 1) * 1000


def _corners(m, n=300):
    import cv2
    pts = cv2.goodFeaturesToTrack(m.astype(np.float32) * 255, maxCorners=n, qualityLevel=0.25, minDistance=12, blockSize=7, useHarrisDetector=True)
    return np.zeros((0, 2)) if pts is None else pts.reshape(-1, 2)


def _nodes(path):
    if not path.lower().endswith('.svg'):
        return None
    s = io.open(path, encoding='utf-8', errors='replace').read()
    ds = re.findall(r'\sd="([^"]+)"', s)
    return sum(len(re.findall(r'[CcLlQqSsTtAaHhVv]', d)) for d in ds) + len(re.findall(r'<(circle|ellipse|line|rect)\b', s)) - len(re.findall(r'id="background"', s))


def score(ref_png, cands, h_mm=None, min_mm=None, strip=None):
    """ref_png 기준으로 후보 여럿 채점 → [{name, fidelity, wiggle, corners, specks, nodes, fab}]"""
    import cv2
    R = _norm(_mask(_render(ref_png)))
    rc = _corners(R)
    tol = 0.006 * NORM_H
    out = []
    tiles = []
    for c in cands:
        row = dict(name=os.path.basename(c))
        try:
            C = _norm(_mask(_render(c)))
            Cr = cv2.resize(C, (R.shape[1], R.shape[0]), interpolation=cv2.INTER_NEAREST)
            row['fidelity'] = round(float((Cr & R).sum() / max((Cr | R).sum(), 1)), 4)
            row['wiggle'] = round(_wiggle(C), 2)
            cc = _corners(Cr)
            if len(rc) and len(cc):
                dd = np.sqrt(((rc[:, None, :] - cc[None, :, :]) ** 2).sum(-1)).min(1)
                row['corners'] = round(float((dd <= tol).mean()), 3)
            else:
                row['corners'] = None
            n, lb, st, _ = cv2.connectedComponentsWithStats(C)
            row['specks'] = int(sum(1 for i in range(1, n) if st[i, 4] < 1e-5 * C.size))
            row['nodes'] = _nodes(c)
            if h_mm:
                from .relogo import fabcheck
                f = fabcheck(c if not c.lower().endswith('.svg') else _png_of(c), h_mm, min_mm=min_mm)
                row['fab'] = {k: f[k] for k in ('min_mm', 'tip_p10_mm', 'channel_38mm') if k in f} | ({'bad_tips': f['bad_tips']} if 'bad_tips' in f else {})
            tiles.append((row['name'], Cr))
        except Exception as e:
            row['error'] = str(e)[:200]
        out.append(row)
    out.insert(0, dict(name='(기준) ' + os.path.basename(ref_png), wiggle=round(_wiggle(R), 2), corners_ref=int(len(rc))))
    if strip and tiles:
        _strip(R, tiles, strip)
    return out


def _png_of(svg):
    t = os.path.join(tempfile.mkdtemp(prefix='ad_score_'), 'r.png')
    Image.fromarray(_render(svg)).save(t)
    return t


def _strip(R, tiles, out, boxes=((0.30, 0.02, 0.62, 0.30), (0.05, 0.55, 0.40, 0.75), (0.55, 0.80, 0.95, 0.98))):
    """확대 칸 셋을 기준·후보마다 한 줄씩 — 눈으로 판정하는 장(숫자만 믿지 않는다)."""
    from PIL import ImageDraw
    rows = []
    for name, M in [('기준', R)] + tiles:
        H, W = M.shape
        cells = []
        for x0, y0, x1, y1 in boxes:
            c = M[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]
            im = Image.fromarray(np.where(c > 0, 30, 245).astype(np.uint8)).convert('RGB')
            cells.append(im.resize((int(im.width * 360 / max(im.height, 1)), 360)))
        row = Image.new('RGB', (sum(i.width for i in cells) + 20 * len(cells) + 220, 380), 'white')
        ImageDraw.Draw(row).text((8, 170), name[:28], fill=(0, 0, 0))
        x = 220
        for i in cells:
            row.paste(i, (x, 10)); x += i.width + 20
        rows.append(row)
    Wm = max(r.width for r in rows)
    sheet = Image.new('RGB', (Wm, sum(r.height for r in rows)), 'white'); y = 0
    for r in rows:
        sheet.paste(r, (0, y)); y += r.height
    sheet.save(out)
