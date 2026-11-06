# -*- coding: utf-8 -*-
"""배치 — 글자 모양은 한 점도 안 바꾸고 «자리»만 옮긴다. 고객A 네일에서 사람이 요구한 손질들.

- respace : 글자 조금 작게 + 자간 넓게(«모던·심플·미니멀»). 한 줄 또는 윗줄+아랫줄(부제).
- squash  : 상하 줄이기(«덜 길쭉하게»). ⚠️ 세로만 누르면 가로획이 가늘어진다 — ad check 로 다시 재라.
- stack   : 심벌 위 + 글자 아래. 심벌 크기·자리는 고정(«고양이 크기·위치는 그대로»).
"""
from . import svgio


def respace_line(d, n, scale=1.0, track=0.3, height=None):
    """한 줄 → 글자 n 개로 묶어(가장 좁은 틈부터 합침) 글자 사이 = 줄 글자 높이 × track 으로 고르게. scale 은 글자 크기 배율.
    height 를 주면 «기준 글자 높이»로 그걸 쓴다(J 내림처럼 튀는 글자 대신 I 높이를 넘길 때)."""
    gs = svgio.group_x(svgio.subpaths(d), n)
    x0, y0, x1, y1 = svgio.bbox(d)
    h = (height or (y1 - y0)) * scale
    gap = h * track
    x = x0
    out = []
    for g in gs:
        gx0 = g['x0']
        out.append(svgio.move(g['d'], lambda v, gx0=gx0, x=x: (v - gx0) * scale + x, lambda v: (v - y0) * scale + y0))
        x += (g['x1'] - g['x0']) * scale + gap
    return ''.join(out)


def respace(d, counts, scale=1.0, track=0.3, sub_track_k=1.6, line_gap=None):
    """여러 줄(윗끝으로 가름). counts = 줄마다 글자 수(예: [6, 10] = CLIENTA / NAILSTUDIO).
    윗줄 자간 = track, 아랫줄은 원래 자간 × sub_track_k. 줄은 가운데 맞춤, 줄 사이는 원래 거리(또는 line_gap × 윗줄 높이)
    🔴 윗줄 내림(J)이 아랫줄에 파고들면 아랫줄을 그 밑으로 내린다(09-27 S2)."""
    lines = svgio.split_lines(d, n=len(counts))
    assert len(lines) == len(counts), f'줄이 {len(lines)}개로 갈렸다'
    b0 = [svgio.bbox(l) for l in lines]
    out, y, prev_bottom, widths = [], None, None, []
    parts = []
    for i, (l, n) in enumerate(zip(lines, counts)):
        if i == 0:
            nl = respace_line(l, n, scale, track)
        else:
            gs = svgio.group_x(svgio.subpaths(l), n)
            gaps = [(gs[j + 1]['x0'] - gs[j]['x1']) * sub_track_k for j in range(len(gs) - 1)]
            x, xs = b0[i][0], []
            for j, g in enumerate(gs):
                gx0 = g['x0']
                xs.append(svgio.move(g['d'], lambda v, gx0=gx0, x=x: (v - gx0) * scale + x, lambda v: (v - b0[i][1]) * scale + b0[i][1]))
                x += (g['x1'] - g['x0']) * scale + (gaps[j] * scale if j < len(gaps) else 0)
            nl = ''.join(xs)
        parts.append(nl)
    # 세로 쌓기 · 가운데 맞춤
    W = max(svgio.bbox(p)[2] - svgio.bbox(p)[0] for p in parts)
    y = b0[0][1]
    res = []
    for i, p in enumerate(parts):
        px0, py0, px1, py1 = svgio.bbox(p)
        if i > 0:
            orig = (b0[i][1] - b0[i - 1][3]) * scale
            want = (line_gap * (b0[0][3] - b0[0][1]) * scale) if line_gap else orig
            y = max(y, prev_bottom + max(want, 0))
            y = max(y, max(svgio.bbox(q)[3] for q in res) + (b0[0][3] - b0[0][1]) * scale * 0.2)   # 내림이 파고들지 않게
        dx = (W - (px1 - px0)) / 2 - px0 + b0[0][0]
        q = svgio.move(p, lambda v: v + dx, lambda v, py0=py0, y=y: v - py0 + y)
        res.append(q)
        prev_bottom = svgio.bbox(q)[3]
        y = prev_bottom
    return ''.join(res)


def squash(d, sx=1.0, sy=0.8):
    x0, y0, x1, y1 = svgio.bbox(d)
    return svgio.move(d, lambda v: x0 + (v - x0) * sx, lambda v: y0 + (v - y0) * sy)


def stack(sym_d, text_d, sym_w_mm, text_w_mm, gap_mm, color='#1b1d1c', pad=0.0):
    """심벌 위 + 글자 아래, 가운데 맞춤. 전부 mm. → (layers, W, H)."""
    s, _ = svgio.fit(sym_d, w=sym_w_mm)
    t, _ = svgio.fit(text_d, w=text_w_mm)
    sx0, sy0, sx1, sy1 = svgio.bbox(s)
    W = max(sym_w_mm, text_w_mm)
    s = svgio.move(s, lambda v: v + (W - sym_w_mm) / 2 + pad, lambda v: v + pad)
    t = svgio.move(t, lambda v: v + (W - text_w_mm) / 2 + pad, lambda v: v + sy1 + gap_mm + pad)
    H = svgio.bbox(t)[3] + pad
    return [(s, color), (t, color)], W + 2 * pad, H
