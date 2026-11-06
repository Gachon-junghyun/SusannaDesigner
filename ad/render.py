# -*- coding: utf-8 -*-
"""그려 보기 — 3D(까치발 45°) · 그라데이션(과 제작 가능한 «톤 띠») · 분리.

3D 는 sim/standoff_sheet.py 의 45° 렌더(벽에 나란한 면마다 호모그래피)를 그대로 부른다 — 두 벌을 짓지 않는다.
"""
import importlib.util
import os

import cv2
import numpy as np
from PIL import Image

from . import clean, measure, svgio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sheet():
    spec = importlib.util.spec_from_file_location('standoff_sheet', os.path.join(ROOT, 'sim', 'standoff_sheet.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def preview3d(svg, w_mm, out_png, deg=45, face='#8b4f4a', wall='#f2dcd5', standoff=80, thick=5, pin_d=10.0, pins=True):
    S = _sheet()
    hx = lambda h: tuple(int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    S.FACE, S.WALL, S.STANDOFF, S.THICK, S.PIN_D = hx(face), hx(wall), float(standoff), float(thick), float(pin_d)
    ps = S.brackets(svg, w_mm)[0] if pins else ()
    S.render_45(svg, w_mm, ps, deg=deg).save(out_png)
    return out_png, len(ps)


def gradient(svg, w_mm, out_prefix, c1='#b77a73', c2='#5e2f2c', bands=0, vertical=True, ppm=3.0):
    """그라데이션 미리보기 PNG. bands>0 이면 «톤 띠»(한 색상 N단) SVG 도 — 🔴 채널 간판은 면 하나가 한 색이라 진짜 그라데이션은 못 만든다.
    톤 띠는 만들 수 있지만 띠마다 조각이 갈라져 조각 수(=제작비)가 는다."""
    d = svgio.joined(svg)
    m, ppm, _ = measure.mask(d, w_mm, ppm, pad_mm=10)
    H, W = m.shape
    ys, xs = np.where(m)
    a0, a1 = (ys.min(), ys.max()) if vertical else (xs.min(), xs.max())
    t = np.clip(((np.arange(H)[:, None] if vertical else np.arange(W)[None, :]) - a0) / max(1, a1 - a0), 0, 1)
    t = np.broadcast_to(t, (H, W))
    hx = lambda h: np.array([int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
    C1, C2 = hx(c1), hx(c2)
    img = np.full((H, W, 3), 255, np.float32)
    img[m] = (C1 * (1 - t[m, None]) + C2 * t[m, None])
    Image.fromarray(img.astype(np.uint8)).save(out_prefix + '_gradient.png')
    outs = [out_prefix + '_gradient.png']
    if bands:
        layers = []
        band_img = np.full((H, W, 3), 255, np.uint8)
        for b in range(bands):
            lo, hi = b / bands, (b + 1) / bands
            mb = m & (t >= lo) & ((t < hi) if b < bands - 1 else (t <= 1))
            if not mb.any():
                continue
            col = C1 * (1 - (b + 0.5) / bands) + C2 * ((b + 0.5) / bands)
            hexc = '#%02x%02x%02x' % tuple(int(v) for v in col)
            band_img[mb] = col.astype(np.uint8)
            dd = clean.revector(mb, ppm, 0)
            # 전체 잉크 상자 기준 자리로
            bys, bxs = np.where(mb)
            dd = svgio.move(dd, lambda v, o=bxs.min() / ppm - xs.min() / ppm: v + o, lambda v, o=bys.min() / ppm - ys.min() / ppm: v + o)
            layers.append((dd, hexc))
        Image.fromarray(band_img).save(out_prefix + f'_bands{bands}.png')
        lay, w, h = svgio.crop(layers)
        svgio.write(out_prefix + f'_bands{bands}.svg', lay, w, h, mm=True)
        n0 = measure.pieces(m, ppm)[0]
        n1 = sum(len(measure.pieces(measure.mask(dd, (svgio.bbox(dd)[2] - svgio.bbox(dd)[0]), ppm)[0], ppm)[0]) for dd, _ in lay)
        outs += [out_prefix + f'_bands{bands}.png', out_prefix + f'_bands{bands}.svg']
        print(f'톤 띠 {bands}단: 조각 {len(n0)} → {n1} (띠마다 갈라짐 — 제작비↑)')
    return outs


def split(svg, by, outdir, n=None, w_mm=None):
    """분리 — pieces(떨어진 조각마다) · lines(줄마다) · letters(윗줄 글자 n 개). 제작·까치발 도면용 낱개 SVG."""
    os.makedirs(outdir, exist_ok=True)
    layers, vb = svgio.read(svg)
    layers = clean.strip_bg(layers, vb)
    d = ''.join(x for x, _ in layers)
    color = layers[0][1] if layers else '#000'
    files = []
    if by == 'lines':
        parts = svgio.split_lines(d)
    elif by == 'letters':
        main = svgio.split_lines(d)[0]
        parts = [g['d'] for g in svgio.group_x(svgio.subpaths(main), n)]
    else:   # pieces — 칠해서 떨어진 덩이마다 다시 딴다(겹친 하위 경로도 한 조각이 된다)
        w_mm = w_mm or 1000.0
        m, ppm, _ = measure.mask(d, w_mm, 3.0, rule='nonzero')
        nlab, lab = cv2.connectedComponents(m.astype(np.uint8), connectivity=8)
        parts = []
        for i in range(1, nlab):
            mi = lab == i
            if mi.sum() / ppm / ppm < 20:
                continue
            ys, xs = np.where(mi)
            dd = clean.revector(mi, ppm, 0)
            parts.append(svgio.move(dd, lambda v, o=xs.min() / ppm: v + o, lambda v, o=ys.min() / ppm: v + o))
    for i, p in enumerate(parts, 1):
        lay, w, h = svgio.crop([(p, color)])
        files.append(svgio.write(os.path.join(outdir, f'{by}_{i:02d}.svg'), lay, w, h, mm=(by == 'pieces')))
    return files
