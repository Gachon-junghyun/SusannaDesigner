# -*- coding: utf-8 -*-
"""검사 — 사람이 고객A 네일(2026-09-27)에서 «직접 짚어 준» 디테일을 자동으로 잡는다. 클로드가 눈으로 놓치던 것들.

한 줄씩 (등급, 코드, 문장). 등급: no(이대로 안 됨) · check(사람이 봐야 함) · ok.
각 검사 위 주석이 «언제 누가 짚었나»다 — 새로 짚히면 여기 한 칸을 더한다(도구를 새로 짓지 않는다).
"""
import cv2
import numpy as np
from PIL import Image

from . import measure, svgio

LASER_MIN, HOLE_MIN, LINE_GAP, PIECE_GAP = 3.0, 30.0, 15.0, 5.0


def run(svg_path, w_mm, raster=None, pin_d=10.0, pin_edge=3.0, ppm=2.0, letters=None):
    layers, vb = svgio.read(svg_path)
    out = []
    add = lambda lv, code, msg: out.append((lv, code, msg))

    # ① 흰 배경 사각형 — letter_svg SVG 가 품고 있고, 업로더가 흰 경로로 평평하게 만든다 → «색 한 벌로 칠하기»가 네모가 됨 (09-27 흐름 설계 중)
    if vb:
        area = vb[2] * vb[3]
        for d, f in layers:
            x0, y0, x1, y1 = svgio.bbox(d)
            if (x1 - x0) * (y1 - y0) >= area * 0.97 and len(svgio.subpaths(d)) <= 2:
                add('no', 'bg-rect', f'캔버스 전체를 덮는 사각형 층({f}) — 흰 배경입니다. 지우고 쓰세요(ad clean).')
    ink = [(d, f) for d, f in layers if not (vb and _covers(d, vb))]
    if not ink:
        add('no', 'empty', '칠한 경로가 없습니다.'); return out
    d = ''.join(x for x, _ in ink)
    colors = {f.lower() for _, f in ink}
    # ② 색 수 — 간판은 2~3색(로고.md · F26-i)
    if len(colors) > 3:
        add('check', 'colors', f'색 {len(colors)}개 — 간판은 2~3색이 보통입니다(색마다 아크릴·시트).')

    # ③ 원본보다 잉크가 짧다 — 두 줄 레터링의 부제가 keep_text 에 지워진 적(09-27, 사람이 «CLIENTA NAIL 빠졌다» 전에 잡음)
    if raster:
        g = np.array(Image.open(raster).convert('L'))
        ys, xs = np.where(g < 128)
        rx0, ry0, rx1, ry1 = xs.min(), ys.min(), xs.max(), ys.max()
        if vb and abs(vb[2] - g.shape[1]) < 2:          # letter_svg 는 viewBox = 원본 픽셀
            sx0, sy0, sx1, sy1 = svgio.bbox(d)
            ext = max(rx1 - rx0, ry1 - ry0)
            short = max(sx0 - rx0, sy0 - ry0, rx1 - sx1, ry1 - sy1)
            if short > ext * 0.03:
                add('no', 'dropped', f'벡터의 잉크가 원본보다 {short:.0f}px 짧습니다 — 부제·작은 조각이 벡터화에서 빠졌을 수 있습니다(두 줄이면 keep_text 를 끄고 다시).')
        edge = (g[:3] < 128).any() or (g[-3:] < 128).any() or (g[:, :3] < 128).any() or (g[:, -3:] < 128).any()
        if edge:
            add('no', 'edge', '원본 그림에서 잉크가 테두리에 닿습니다 — 벡터화가 그 덩이를 통째로 버립니다. 흰 여백을 덧대세요.')

    m, ppm, _ = measure.mask(d, w_mm, ppm)
    # ④ 겹친 획 — 같은 색을 한 층(evenodd)으로 칠하면 겹친 곳에 구멍이 난다(09-26 가변 글꼴 · 메이커 에디터)
    nz, _, _ = measure.mask(d, w_mm, ppm, rule='nonzero')
    diff = (m ^ nz).sum() / max(1, nz.sum())
    if diff > 0.005:
        add('no', 'overlap', f'획이 겹친 곳이 있습니다(잉크의 {diff * 100:.1f}%) — 한 색 한 층으로 칠하면 구멍이 납니다. ad clean --merge 로 합치세요.')

    # ⑤ 획 — 레이저 최소 3mm · 선 끝 테이퍼(겹선 스케치 · 붓, 09-27 «선 끝 1.8mm»)
    s10, s50 = measure.strokes(m, ppm)
    if s10 < LASER_MIN:
        add('no', 'thin', f'가장 가는 곳 {s10:.1f}mm — 레이저 최소 {LASER_MIN:.0f}mm 미만입니다. 선을 굵히거나(ad clean --thicken) 크기를 키우세요.')
    if s50 and s10 / s50 < 0.4 and s10 < LASER_MIN * 2:      # 굵은 심벌(고양이 7mm)까지 잡지 않게 — 절대값도 본다
        add('check', 'taper', f'선 끝이 가늘어집니다(하위 10% {s10:.1f}mm / 가운데 {s50:.1f}mm) — 제작 때 끝을 {LASER_MIN:.0f}mm 로 뭉툭하게 처리합니다.')

    # ⑥ 속공간·오려 낸 틈 — 고양이 흰 선 8mm(09-27). 글자 속공간이면 멀리서 메워짐
    hs = measure.holes(m, ppm)
    if hs and hs[0] < HOLE_MIN:
        add('check', 'hole', f'가장 좁은 빈 틈 {hs[0]:.0f}mm(기준 {HOLE_MIN:.0f}mm) — 글자 속이면 멀리서 메워져 보이고, 심벌 안 틈이면 레이저로는 되지만 흐려집니다.')

    # ⑦ 잡티 · 조각끼리 너무 가까움(따로 오려 까치발로 세우기 어려움)
    ps, lab = measure.pieces(m, ppm)
    specks = sum(a < measure.SPECK_MM2 for a, _ in ps)
    if specks:
        add('check', 'speck', f'가로세로 20mm 미만 조각 {specks}개 — 따로 세우기 어려워 빼거나 시트로.')
    k = max(1, int(round(PIECE_GAP * ppm / 2)))
    n0 = cv2.connectedComponents(m.astype(np.uint8))[0]
    n1 = cv2.connectedComponents(cv2.dilate(m.astype(np.uint8), np.ones((2 * k + 1, 2 * k + 1), np.uint8)))[0]
    if n1 < n0:
        add('check', 'near', f'조각 사이가 {PIECE_GAP:.0f}mm 보다 가까운 곳이 {n0 - n1}군데 — 따로 자르고 세우기 빠듯합니다(붙이거나 띄우세요).')

    # ⑧ 줄끼리 부딪힘 — S2 의 J 내림이 NAIL STUDIO 에 파고듦(09-27 화면에서 봄)
    lines = svgio.split_lines(d)
    if len(lines) > 1:
        fr = svgio.bbox(d)
        masks = [_frame_mask(l, fr, w_mm, ppm) for l in lines]
        for i in range(len(masks) - 1):
            a, b = masks[i], masks[i + 1]
            dist = cv2.distanceTransform((~a).astype(np.uint8), cv2.DIST_L2, 5)
            gap = float(dist[b].min()) / ppm if b.any() else 1e9
            if gap < LINE_GAP:
                add('no' if gap < 1 else 'check', 'lines', f'{i + 1}번째 줄과 {i + 2}번째 줄 사이 가장 가까운 곳 {gap:.0f}mm — {"겹칩니다" if gap < 1 else "너무 붙었습니다"}(기준 {LINE_GAP:.0f}mm).')

    # ⑨ 자간 들쭉날쭉 — 꾸밈 없는 고객A네일 원래 자간 8~15%(09-27 «자간 넓혀»)
    # 🔴 글자 수를 모르면 음절 «안»의 틈(네 = ㄴ|ㅔ)을 자간으로 센다 — 그래서 --letters 를 줄 때만 잰다
    main = max(lines, key=lambda l: svgio.bbox(l)[3] - svgio.bbox(l)[1])
    gs = svgio.group_x(svgio.subpaths(main), letters) if letters else []
    if len(gs) >= 3:
        h = svgio.bbox(main)[3] - svgio.bbox(main)[1]
        gaps = [(gs[i + 1]['x0'] - gs[i]['x1']) / h for i in range(len(gs) - 1)]
        pos = sorted(g for g in gaps if g > 0.01)
        if len(pos) >= 3:                                    # 단어 사이(띄어쓰기)는 빼고 잰다 — 가운데의 2.5배 넘는 틈
            med = pos[len(pos) // 2]
            pos = [g for g in pos if g <= med * 2.5]
        if len(pos) >= 2 and max(pos) / min(pos) > 2.2:
            add('check', 'tracking', f'글자(덩어리) 사이가 들쭉날쭉합니다 — 글자 높이의 {min(pos) * 100:.0f}~{max(pos) * 100:.0f}%. ad respace 로 고르게.')

    # ⑩ 까치발 봉 — 가는 글자엔 10mm 봉이 안 들어감(09-27 PEONIA 결)
    pins, cnt, narrow = measure.pin_layout(m, ppm, d_mm=pin_d, edge_mm=pin_edge)
    if narrow:
        add('check', 'pins', f'봉(지름 {pin_d:.0f}mm)이 안 들어가는 조각 {narrow}개 / {cnt}조각 — 봉을 가늘게(스터드), 그 조각만 붙임, 또는 부제는 시트.')
    add('ok', 'summary', f'가로 {w_mm:,.0f}mm · 최소 획 {s10:.1f}mm · 조각 {len(ps)} · 까치발 {len(pins)}개(지름 {pin_d:.0f}mm 가정) · 색 {len(colors)}')
    return out


def _covers(d, vb):
    x0, y0, x1, y1 = svgio.bbox(d)
    return (x1 - x0) * (y1 - y0) >= vb[2] * vb[3] * 0.97 and len(svgio.subpaths(d)) <= 2


def _frame_mask(d, frame, w_mm, ppm):
    """전체 상자(frame) 기준으로 한 줄만 칠한다 — 줄끼리 같은 자리에서 비교하려고."""
    return measure.mask(d, w_mm, ppm, frame=frame)[0]


def show(results):
    mark = {'no': '🔴', 'check': '⚠️', 'ok': '🟢'}
    for lv, code, msg in results:
        print(f'{mark[lv]} [{code}] {msg}')
    worst = 'no' if any(r[0] == 'no' for r in results) else 'check' if any(r[0] == 'check' for r in results) else 'ok'
    print({'no': '판정: 이대로는 안 됨', 'check': '판정: 조건부 — 사람이 볼 것', 'ok': '판정: 통과'}[worst])
    return worst
