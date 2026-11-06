# -*- coding: utf-8 -*-
"""한 획 마커 레터링 → «펜으로 그리는» 로고 SVG (정지판 + 그리기 애니메이션판).

채운 윤곽을 따는 vecc 와 다르다 — 여기는 **중심선**을 따서 `stroke` 로 다시 그린다. 그래서
① 굵기를 마음대로 바꿀 수 있고(`--weight`) ② 세로만 누를 때 획이 안 가늘어지고(`--sy`)
③ 정지 로고와 애니메이션이 «같은 선»이다(stroke-dashoffset 으로 한 획씩 그린다).
🔴 굵기가 고른 한 획 글씨(마커·모노라인)에만 맞는다. 채운 버블·블록 글자에 쓰면 뼈대가 엉뚱하게 나온다.
2026-09-28 드로우사인 자체 로고에서 만들었다."""
import os

import numpy as np

N8 = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]


def _thin(m):
    """Zhang-Suen 세선화(skimage 없이 numpy 로)."""
    m = np.pad(m.astype(np.uint8), 1)
    while True:
        changed = False
        for step in (0, 1):
            P = [np.roll(np.roll(m, -dy, 0), -dx, 1) for dy, dx in N8]   # P2..P9 (위부터 시계방향)
            B = sum(P)
            A = sum(((P[i] == 0) & (P[(i + 1) % 8] == 1)).astype(np.uint8) for i in range(8))
            if step == 0:
                c = (P[0] * P[2] * P[4] == 0) & (P[2] * P[4] * P[6] == 0)
            else:
                c = (P[0] * P[2] * P[6] == 0) & (P[0] * P[4] * P[6] == 0)
            d = (m == 1) & (B >= 2) & (B <= 6) & (A == 1) & c
            if d.any():
                m[d] = 0
                changed = True
        if not changed:
            return _slim(m[1:-1, 1:-1].astype(bool))


def _slim(sk):
    """계단 모서리 걷기 — 세선화 뒤 대각선에 남는 «ㄴ» 모서리 픽셀은 이웃이 셋이라 갈림점으로 잡혀
    획이 118 조각으로 부서졌다(2026-09-28). 지워도 이웃끼리 8-연결이 유지되는 픽셀만 지운다."""
    sk = sk.copy()
    for y, x in zip(*np.nonzero(sk)):
        nb = _nbrs(sk, y, x)
        if len(nb) < 2:
            continue                                   # 끝점은 남긴다
        # 이웃끼리 서로 닿아 한 덩이인가
        todo, seen = [nb[0]], {nb[0]}
        while todo:
            a = todo.pop()
            for b in nb:
                if b not in seen and max(abs(a[0] - b[0]), abs(a[1] - b[1])) == 1:
                    seen.add(b); todo.append(b)
        if len(seen) == len(nb):
            sk[y, x] = False
    return sk


def _nbrs(sk, y, x):
    H, W = sk.shape
    return [(y + dy, x + dx) for dy, dx in N8 if 0 <= y + dy < H and 0 <= x + dx < W and sk[y + dy, x + dx]]


def _chains(sk):
    """뼈대 → 끝점·갈림점 사이의 픽셀 사슬들."""
    deg = {}
    for y, x in zip(*np.nonzero(sk)):
        deg[(y, x)] = len(_nbrs(sk, y, x))
    nodes = {p for p, d in deg.items() if d != 2}
    seen, out = set(), []
    for n in nodes:
        for q in _nbrs(sk, *n):
            if (n, q) in seen:
                continue
            ch, prev, cur = [n], n, q
            while True:
                ch.append(cur)
                seen.add((prev, cur)); seen.add((cur, prev))
                if cur in nodes:
                    break
                nx = [r for r in _nbrs(sk, *cur) if r != prev and (cur, r) not in seen]
                if not nx:
                    break
                prev, cur = cur, nx[0]
            out.append(ch)
    rest = {p for p in deg if p not in nodes and not any((p, r) in seen for r in _nbrs(sk, *p))}
    while rest:                                   # 갈림점 없는 고리(O 같은 것)
        s = rest.pop(); ch, prev, cur = [s], None, s
        while True:
            nx = [r for r in _nbrs(sk, *cur) if r != prev and r in rest]
            if not nx:
                break
            prev, cur = cur, nx[0]; rest.discard(cur); ch.append(cur)
        ch.append(s); out.append(ch)
    return out, deg


def _smooth(pts, win):
    p = np.array(pts, float)
    if len(p) < 3 or win < 2:
        return p
    k = np.ones(win) / win
    closed = np.allclose(p[0], p[-1])
    pad = np.concatenate([p[-win:-1], p, p[1:win]]) if closed else np.concatenate([np.repeat(p[:1], win, 0), p, np.repeat(p[-1:], win, 0)])
    s = np.stack([np.convolve(pad[:, i], k, 'same') for i in (0, 1)], 1)
    s = s[win - 1:win - 1 + len(p)] if closed else s[win:win + len(p)]
    s[0], s[-1] = (p[0], p[-1]) if not closed else (s[0], s[0])
    return s


def _rdp(p, eps):
    if len(p) < 3:
        return p
    if np.allclose(p[0], p[-1]):                  # 🔴 닫힌 고리는 시작=끝이라 통째로 점 하나가 됐다(D) — 가장 먼 점에서 반으로
        k = int(np.argmax(np.hypot(*(p - p[0]).T)))
        return np.concatenate([_rdp(p[:k + 1], eps)[:-1], _rdp(p[k:], eps)])
    a, b = p[0], p[-1]
    ab = b - a
    L = np.hypot(*ab) or 1.0
    d = np.abs(ab[0] * (p[:, 1] - a[1]) - ab[1] * (p[:, 0] - a[0])) / L
    i = int(np.argmax(d))
    if d[i] > eps:
        return np.concatenate([_rdp(p[:i + 1], eps)[:-1], _rdp(p[i:], eps)])
    return np.array([a, b])


def _bez(p):
    """점열(x,y) → Catmull-Rom 을 3차 베지어로 바꾼 path d."""
    if len(p) == 2:
        return f'M{p[0][0]:.1f},{p[0][1]:.1f}L{p[1][0]:.1f},{p[1][1]:.1f}'
    d = f'M{p[0][0]:.1f},{p[0][1]:.1f}'
    q = np.concatenate([p[:1], p, p[-1:]])
    for i in range(1, len(q) - 2):
        p0, p1, p2, p3 = q[i - 1], q[i], q[i + 1], q[i + 2]
        c1 = p1 + (p2 - p0) / 6
        c2 = p2 - (p3 - p1) / 6
        d += f'C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}'
    return d


def strokes(png, prune=2.0):
    """그림 → (획 목록[(글자번호, 점열 xy)], 원래 획 굵기 px). 획은 글자 왼→오, 글자 안에선 쓰는 순서 어림."""
    from PIL import Image
    from scipy import ndimage as ndi
    m = np.asarray(Image.open(png).convert('L')) < 128
    m = ndi.binary_opening(m, iterations=2)
    cc, n = ndi.label(m)
    sz = ndi.sum(m, cc, range(1, n + 1))
    m = np.isin(cc, 1 + np.nonzero(sz >= sz.max() * 0.02)[0])     # 잡티·워터마크 빼기
    dt = ndi.distance_transform_edt(m)
    sk = _thin(m)
    w = 2 * float(np.median(dt[sk]))
    # 짧은 가시(끝점에서 갈림점까지 획 굵기×prune 보다 짧은 것)를 두 번 쳐낸다
    for _ in range(3):
        chains, deg = _chains(sk)
        for ch in chains:
            a, b = ch[0], ch[-1]
            if (deg.get(a) == 1) != (deg.get(b) == 1) and len(ch) < w * prune:
                for p in ch:
                    if deg.get(p) != None and deg[p] <= 2:
                        sk[p] = False
                end = a if deg.get(a) == 1 else b
                sk[end] = False
    chains, _ = _chains(sk)
    lab, _ = ndi.label(m)
    comps = ndi.find_objects(lab)
    order = {k + 1: r for r, k in enumerate(sorted(range(len(comps)), key=lambda k: comps[k][1].start))}
    out = []
    for ch in chains:
        if len(ch) < 3:
            continue
        xy = np.array([(x, y) for y, x in ch], float)
        g = order[lab[ch[len(ch) // 2]]]
        if len(ch) > 3 and ch[0] == ch[-1]:      # 고리: 왼쪽 위에서 시작해 오른쪽으로 돈다
            core = xy[:-1]
            k = int(np.argmin(core[:, 1] + 0.5 * core[:, 0]))
            core = np.roll(core, -k, 0)
            if core[min(5, len(core) - 1)][0] < core[0][0]:
                core = np.concatenate([core[:1], core[1:][::-1]])
            out.append((g, np.concatenate([core, core[:1]])))
            continue
        # 방향: 위·왼쪽 끝에서 시작(손으로 쓰는 쪽)
        if xy[-1][1] + 0.5 * xy[-1][0] < xy[0][1] + 0.5 * xy[0][0]:
            xy = xy[::-1]
        out.append((g, xy))
    # 글자 안 순서: 세로에 가까운(첫 획) → 왼쪽부터
    def key(s):
        g, xy = s
        span = np.ptp(xy, 0)
        return (g, round(xy[:, 0].min() / (w * 1.5)), 0 if span[1] > span[0] else 1, xy[0][1])
    out.sort(key=key)
    return out, w


def run(png, out, weight=1.0, sy=1.0, sx=1.0, ink='#17161a', dot='#8e3a4d', dot_r=0.62,
        draw_s=2.4, cycle_s=30.0, pad=None, tsx=None, prefix='lg'):
    """정지판 `<out>.svg` + 애니메이션판 `<out>_draw.svg`(30초마다 다시 그림) · `tsx` 를 주면 사이트용 React 부품도."""
    ss, w0 = strokes(png)
    W = w0 * weight
    pad = W if pad is None else pad
    allp = np.concatenate([xy for _, xy in ss])
    x0, y0 = allp.min(0)
    paths = []
    for g, xy in ss:
        p = (xy - [x0, y0]) * [sx, sy] + pad
        p = _rdp(_smooth(p, max(3, int(w0 * 0.35))), 0.9)
        paths.append((g, p))
    allp = np.concatenate([p for _, p in paths])
    xmax, ymax = allp.max(0)
    # 와인 점: 마지막 글자 오른쪽 위
    last = [p for g, p in paths if g == max(g for g, _ in paths)]
    lp = np.concatenate(last)
    r = W * dot_r
    cx = lp[:, 0].max() + W * 0.5 + r * 1.6
    cy = lp[:, 1].min() - W * 0.5 + r
    VW, VH = cx + r + pad, ymax + pad
    lens = [float(np.hypot(*np.diff(p, axis=0).T).sum()) for _, p in paths]
    ds = [_bez(p) for _, p in paths]
    attrs = f'fill="none" stroke="{ink}" stroke-width="{W:.1f}" stroke-linecap="round" stroke-linejoin="round"'
    head = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VW:.0f} {VH:.0f}" role="img" aria-label="DRAWSIGN">'
    static = head + f'<g {attrs}>' + ''.join(f'<path d="{d}"/>' for d in ds) + f'</g><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{dot}"/></svg>'
    # 🔴 숨은 획도 둥근 끝(cap)이 시작점에 점으로 찍힌다 — 자기 차례 전엔 opacity 0
    # 그리기: 전체 draw_s 초를 획 길이에 비례해 나누고, 획 사이에 펜 드는 틈을 조금
    gap = 0.06
    total = sum(lens)
    t, css = 0.0, []
    avail = draw_s - gap * len(lens) - 0.35
    for i, L in enumerate(lens):
        dur = avail * L / total
        a, b = t / cycle_s * 100, (t + dur) / cycle_s * 100
        css.append(f'@keyframes s{i}{{0%,{a:.3f}%{{stroke-dashoffset:1;opacity:0}}{a + 0.001:.3f}%{{opacity:1}}{b:.3f}%,100%{{stroke-dashoffset:0;opacity:1}}}}'
                   f'.s{i}{{animation:s{i} {cycle_s}s linear infinite}}')
        t += dur + gap
    a = t / cycle_s * 100
    css.append(f'@keyframes dt{{0%,{a:.3f}%{{transform:scale(0)}}{a + 0.6:.3f}%{{transform:scale(1.25)}}{a + 1.0:.3f}%,100%{{transform:scale(1)}}}}'
               f'.dt{{transform-box:fill-box;transform-origin:center;animation:dt {cycle_s}s ease-out infinite}}')
    style = ('<style>path{stroke-dasharray:1 1}' + ''.join(css) +
             '@media (prefers-reduced-motion:reduce){path,.dt{animation:none!important;stroke-dashoffset:0}}</style>')
    anim = (head + style + f'<g {attrs}>' +
            ''.join(f'<path class="s{i}" pathLength="1" d="{d}"/>' for i, d in enumerate(ds)) +
            f'</g><circle class="dt" cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{dot}"/></svg>')
    if tsx:
        _tsx(tsx, prefix, VW, VH, W, ds, css, cx, cy, r, cycle_s)
    base = os.path.splitext(out)[0]
    os.makedirs(os.path.dirname(os.path.abspath(out)) or '.', exist_ok=True)
    for pth, s in ((base + '.svg', static), (base + '_draw.svg', anim)):
        with open(pth, 'w', encoding='utf-8') as f:
            f.write(s)
    print(f'획 {len(paths)} · 원래 굵기 {w0:.1f}px → {W:.1f}px · 그리기 {draw_s}s / {cycle_s}s 마다')
    print(f'→ {base}.svg  (정지)\n→ {base}_draw.svg  (애니메이션 — <img> 로 넣어도 돈다)')
    return base


def _tsx(path, px, VW, VH, W, ds, css, cx, cy, r, cycle_s):
    """사이트용 React 부품 — 색은 글자색(currentColor)·점은 --wine 이라 밝은/어두운 화면을 따라간다.
    🔴 인라인 SVG 의 <style> 은 문서 전체에 걸린다 — 클래스·키프레임 이름에 접두어를 붙인다."""
    import re
    css2 = [re.sub(r'(?<![\w-])(s\d+|dt)(?![\w-])', lambda m: f'{px}-{m.group(1)}', c) for c in css]
    style = (f'.{px} path{{stroke-dasharray:1 1}}' + ''.join(css2) +
             f'@media (prefers-reduced-motion:reduce){{.{px} path,.{px} .{px}-dt{{animation:none!important;stroke-dashoffset:0!important;opacity:1!important}}}}')
    body = ''.join(f'<path className="{px}-s{i}" pathLength={{1}} d="{d}" />' for i, d in enumerate(ds))
    src = f'''/* 자동 생성 — SusannaDesigner `python -m ad draw … --tsx`. 손으로 고치지 말고 다시 뽑는다. */
const CSS = {repr(style)};

/** 펜으로 그리는 워드마크 — 처음 한 번 그리고, 그 뒤 {cycle_s:g}초마다 다시 그린다. 움직임 줄이기면 멈춘 채로. */
export default function LogoDraw({{ height = 26, title = "DRAWSIGN" }}: {{ height?: number; title?: string }}) {{
  return (
    <svg className="{px}" viewBox="0 0 {VW:.0f} {VH:.0f}" height={{height}} role="img" aria-label={{title}} style={{{{ display: "block", width: "auto" }}}}>
      <style>{{CSS}}</style>
      <g fill="none" stroke="currentColor" strokeWidth={{{W:.1f}}} strokeLinecap="round" strokeLinejoin="round">
        {body}
      </g>
      <circle className="{px}-dt" cx={{{cx:.1f}}} cy={{{cy:.1f}}} r={{{r:.1f}}} fill="var(--wine)" />
    </svg>
  );
}}
'''
    with open(path, 'w', encoding='utf-8') as f:
        f.write(src)
    print(f'→ {path}  (React 부품)')
