# -*- coding: utf-8 -*-
"""평평한 SVG(한 색 또는 색마다 <path fill d>) 읽기·쓰기·옮기기·가르기.

«평평한» = 변형(transform) 없음, 명령은 대문자 M·L·C·Q·Z 절대좌표 — letter_svg.py·maker_up.py·수산나 메이커가 주고받는 모양.
🔴 H·V·A·상대좌표가 섞이면 멈춘다(숫자를 두 개씩 x,y 로 짝짓기 때문 — 조용히 틀리면 획이 엉뚱한 데로 간다).
"""
import io
import re

NUM = r'-?\d+\.?\d*(?:e-?\d+)?'


def read(path):
    """→ (layers=[(d, fill)], viewBox=(x0,y0,w,h)). 흰 배경 <rect> 는 layers 에 안 들어온다(사각형은 path 가 아니라서)."""
    s = io.open(path, encoding='utf-8').read()
    vb = re.search(r'viewBox="([^"]+)"', s)
    vb = tuple(float(v) for v in vb.group(1).replace(',', ' ').split()) if vb else None
    layers = []
    for tag in re.findall(r'<path[^>]*>', s):
        d = re.search(r'\sd="([^"]+)"', tag)
        if not d:
            continue
        f = re.search(r'fill="([^"]+)"', tag)
        fill = f.group(1) if f else '#000000'
        if fill in ('none', 'transparent'):
            continue
        check(d.group(1))
        layers.append((d.group(1), fill))
    return layers, vb


def check(d):
    bad = set(re.findall(r'[A-Za-z]', d)) - set('MLCQZ')
    if bad:
        raise ValueError(f'평평하지 않은 경로 명령 {sorted(bad)} — maker_up.py 로 평평하게 만든 뒤 쓰세요')


def joined(path):
    return ''.join(d for d, _ in read(path)[0])


def bbox(d):
    v = [float(x) for x in re.findall(NUM, d)]
    return min(v[0::2]), min(v[1::2]), max(v[0::2]), max(v[1::2])


def move(d, fx, fy):
    """좌표마다 x→fx(x), y→fy(y). 명령 글자는 그대로."""
    c = iter(range(10 ** 9))
    return re.sub(NUM, lambda m: '%.2f' % (fx(float(m.group(0))) if next(c) % 2 == 0 else fy(float(m.group(0)))), d)


def affine(d, kx, dx, dy, ky=None):
    ky = kx if ky is None else ky
    return move(d, lambda v: v * kx + dx, lambda v: v * ky + dy)


def fit(d, w=None, h=None, x=0.0, y=0.0, sy=1.0):
    """잉크 상자를 (x,y) 에 놓고 가로 w(또는 세로 h)에 맞춘다. sy = 세로만 추가 배율(납작하게)."""
    x0, y0, x1, y1 = bbox(d)
    k = (w / (x1 - x0)) if w else (h / (y1 - y0))
    return move(d, lambda v: (v - x0) * k + x, lambda v: (v - y0) * k * sy + y), k


def subpaths(d):
    return ['M' + p for p in d.split('M') if p.strip()]


def group_x(subs, n=None, tol=1.0):
    """하위 경로를 가로 겹침으로 묶는다(ㅎ 속·ㅇ 구멍·i 점 포함). n 을 주면 그 수가 될 때까지 가장 좁은 틈부터 합친다
    (한 음절 안에도 틈이 있다 — 네 = ㄴ + ㅔ, 일 = ㅇㄹ + ㅣ)."""
    items = sorted(((bbox(sd), sd) for sd in subs), key=lambda t: t[0][0])
    gs = []
    for b, sd in items:
        if gs and b[0] <= gs[-1]['x1'] + tol:
            g = gs[-1]; g['x1'] = max(g['x1'], b[2]); g['y0'] = min(g['y0'], b[1]); g['y1'] = max(g['y1'], b[3]); g['d'] += sd
        else:
            gs.append(dict(x0=b[0], x1=b[2], y0=b[1], y1=b[3], d=sd))
    while n and len(gs) > n:
        i = min(range(len(gs) - 1), key=lambda k: gs[k + 1]['x0'] - gs[k]['x1'])
        a, b = gs[i], gs.pop(i + 1)
        a['x1'] = max(a['x1'], b['x1']); a['y0'] = min(a['y0'], b['y0']); a['y1'] = max(a['y1'], b['y1']); a['d'] += b['d']
    return gs


def split_lines(d, n=None, min_gap_ratio=0.25):
    """하위 경로를 «윗끝(top)» 으로 줄로 가른다. n 이 없으면 윗끝 사이 틈이 (가장 큰 글자 높이 × min_gap_ratio) 보다 큰 곳마다 자른다.
    🔴 윗끝으로 가르는 이유: J·g·y 의 내림이 아랫줄까지 내려와도 윗끝은 윗줄에 있다."""
    subs = subpaths(d)
    tops = sorted(set(round(bbox(s)[1], 1) for s in subs))
    hmax = max(bbox(s)[3] - bbox(s)[1] for s in subs)
    gaps = sorted(((tops[i + 1] - tops[i], i) for i in range(len(tops) - 1)), reverse=True)
    if n:
        cuts = sorted(i for _, i in gaps[:n - 1])
    else:
        cuts = sorted(i for g, i in gaps if g > hmax * min_gap_ratio)
    edges = [(tops[i] + tops[i + 1]) / 2 for i in cuts]
    lines = [[] for _ in range(len(edges) + 1)]
    for s in subs:
        t = bbox(s)[1]
        lines[sum(t > e for e in edges)].append(s)
    return [''.join(l) for l in lines if l]


def write(path, layers, w, h, mm=False, x0=0.0, y0=0.0):
    size = f' width="{w:.1f}mm" height="{h:.1f}mm"' if mm else ''
    body = ''.join(f'<path fill="{f}" fill-rule="evenodd" d="{d}"/>' for d, f in layers)
    io.open(path, 'w', encoding='utf-8').write(
        f'<svg xmlns="http://www.w3.org/2000/svg"{size} viewBox="{x0:.1f} {y0:.1f} {w:.1f} {h:.1f}">{body}</svg>\n')
    return path


def crop(layers, pad=0.0):
    """잉크 상자로 자르고 (0,0) 부터 — pad 만큼 여백."""
    xs0, ys0, xs1, ys1 = zip(*(bbox(d) for d, _ in layers))
    x0, y0 = min(xs0) - pad, min(ys0) - pad
    w, h = max(xs1) + pad - x0, max(ys1) + pad - y0
    return [(move(d, lambda v: v - x0, lambda v: v - y0), f) for d, f in layers], w, h
