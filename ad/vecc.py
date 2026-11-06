# -*- coding: utf-8 -*-
"""여러 색 로고 → 색마다 층인 SVG(일러 시안). `python -m ad vecc` 의 본체.

아담 왕관(2026-09-28)에서 지었다 — `ad vec`(letter_svg)는 한 색만 따고, 1px 요철까지 따라가 크게 키우면 오돌토돌했다.
원은 원, 길쭉하게 꽉 찬 띠는 반듯한 직사각형, 나머지는 모서리 + 직선 + 스플라인 곡선으로 딴다.
"""
import os

from . import svgio


def _path(mask, up, eps=1.0, corner_deg=40):
    """마스크 → 매끈한 SVG 경로(원본 px × up 좌표).
    ① 모서리: 촘촘한 윤곽에서 «앞뒤 3px 방향»이 corner_deg 이상 꺾이는 곳의 극대점(흐림에 둥글어진 모서리도 한 점으로 잡힌다).
    ② 모서리 사이 구간이 곧으면(현에서 eps×2 px 안) 직선 — 양옆이 둘 다 직선인 모서리는 «두 직선의 교점»으로 되세운다
       (십자 끝·별 끝이 흐림에 깎이지 않게).
    ③ 휜 구간은 앞뒤 «곧은 꼬리»를 직선으로 떼고, 가운데를 스무딩 스플라인에 맞춰 베지어로 옮긴다(C1 연속, 꼬리 방향을 접선으로).
       점을 이어 만든 곡선(캣멀-롬)은 1px 미만 흔들림이 크게 키웠을 때 «면(facet)»으로 보였다(2026-09-28 실측).
    🔴 픽셀을 그대로 따면 1px 요철이 크게 키웠을 때 «오돌토돌»로 보인다 — 흐리게 키워 문턱을 넘긴 윤곽에서 시작한다."""
    import cv2
    import numpy as np
    from scipy.ndimage import gaussian_filter1d
    k = 4
    big = cv2.resize(mask.astype(np.float32), (mask.shape[1] * k, mask.shape[0] * k), interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (0, 0), k * 0.6)
    cs, _ = cv2.findContours((big > 0.5).astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    f = lambda q: f'{q[0] * up:.1f},{q[1] * up:.1f}'
    out = []
    for c in cs:
        if cv2.contourArea(c) < (k * 3) ** 2:
            continue
        D = c[:, 0, :].astype(float) / k + 0.5 / k
        N = len(D)
        if N < 24:
            continue
        w = 3 * k                                                        # 3px
        vin = D - np.roll(D, w, 0)
        vout = np.roll(D, -w, 0) - D
        ang = np.degrees(np.arctan2(vout[:, 1], vout[:, 0]) - np.arctan2(vin[:, 1], vin[:, 0]))
        ang = np.abs((ang + 180) % 360 - 180)
        cor = [i for i in range(N) if ang[i] >= corner_deg and ang[i] == max(ang[(i + t) % N] for t in range(-w, w + 1))]
        # 같은 값이 이어진 극대는 하나만
        cor = [i for n_, i in enumerate(cor) if n_ == 0 or i - cor[n_ - 1] > w]
        if not cor:
            cor = [0]

        def seg(i, j):
            return D[[(i + t) % N for t in range(((j - i) % N or N) + 1)]]
        runs = []
        for t in range(len(cor)):
            P = seg(cor[t], cor[(t + 1) % len(cor)])
            # 곧은가: 양 끝 15% 를 뺀 점들을 직선에 맞춰 벗어남을 잰다(끝은 모서리·다른 색 밑이라 흐트러져 있다)
            m = len(P)
            Q = P[int(m * 0.15): m - int(m * 0.15)] if m >= 14 else P
            mu = Q.mean(0)
            _, _, vt = np.linalg.svd(Q - mu)
            nrm = np.array([-vt[0][1], vt[0][0]])
            dev = np.abs((Q - mu) @ nrm).max()
            runs.append(dict(P=P, straight=dev <= 2.0 * eps, line=None))
        # 곧은 구간은 양 끝 20% 를 뺀 점들로 직선을 맞춘다(모서리 근처는 흐림에 휘어 있다)
        for r in runs:
            if r['straight']:
                P = r['P']; m = len(P)
                Q = P[int(m * 0.15): m - int(m * 0.15)] if m >= 14 else P
                mu = Q.mean(0)
                _, _, vt = np.linalg.svd(Q - mu)
                r['line'] = (mu, vt[0])
        # 모서리 자리: 양옆이 직선이면 교점, 아니면 윤곽 위 그 점
        V = []
        for t in range(len(runs)):
            pr, nx = runs[t - 1], runs[t]
            X = nx['P'][0]
            if pr['line'] is not None and nx['line'] is not None:
                (p, d1), (q, d2) = pr['line'], nx['line']
                den = d1[0] * d2[1] - d1[1] * d2[0]
                if abs(den) > 1e-3:
                    s_ = ((q - p)[0] * d2[1] - (q - p)[1] * d2[0]) / den
                    Y = p + s_ * d1
                    if np.hypot(*(Y - X)) < 4:
                        X = Y
            V.append(X)
        d = 'M' + f(V[0])
        for t, r in enumerate(runs):
            end = V[(t + 1) % len(runs)]
            if r['straight'] or len(r['P']) < 8:
                d += 'L' + f(end)
                continue
            P = r['P'].copy()
            P[0], P[-1] = V[t], end
            # 휜 구간 앞·뒤에 «곧은 꼬리»가 길게 붙어 있으면(뾰족 끝 → U 자) 그 꼬리는 직선으로 떼어 낸다
            def straight_len(A):
                lo, hi = 0, len(A)
                while hi - lo > 8:
                    mid = (lo + hi) // 2
                    B = A[:mid]
                    a0, b0 = B[0], B[-1]
                    L0 = np.hypot(*(b0 - a0))
                    ok = L0 > 1e-6 and np.abs((B - a0) @ (np.array([-(b0 - a0)[1], (b0 - a0)[0]]) / L0)).max() <= 1.5 * eps
                    lo, hi = (mid, hi) if ok else (lo, mid)
                return lo
            head = straight_len(P)
            tail = straight_len(P[::-1])
            hdir = tdir = None                                           # 곧은 꼬리 방향 — 곡선이 그 방향으로 이어 나가게(꺾임 없이)
            if head > len(P) * 0.2 and head < len(P) - 16:
                hdir = (P[head] - P[0]) / max(np.hypot(*(P[head] - P[0])), 1e-6)
                d += 'L' + f(P[head]); P = P[head:]
            tl = None
            if tail > len(P) * 0.2 and tail < len(P) - 16:
                tl = P[-1]
                tdir = (P[-1] - P[len(P) - tail]) / max(np.hypot(*(P[-1] - P[len(P) - tail])), 1e-6)
                P = P[:len(P) - tail + 1]
            # 🔴 점을 이어 만든 곡선은 1px 미만 흔들림이 «면(facet)»으로 보인다 — 매끈한 스플라인을 맞춰
            #    그 위에서 점과 접선을 뽑아 베지어로 옮긴다(C1 연속). 곧은 꼬리 쪽 끝은 그 방향을 접선으로 쓴다
            from scipy.interpolate import splprep, splev
            sl = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
            keep = np.concatenate([[True], np.diff(sl) > 1e-6])
            P2, sl2 = P[keep], sl[keep]
            if len(P2) < 6:
                d += 'L' + f(P[-1])
            else:
                w_ = np.ones(len(P2)); w_[0] = w_[-1] = 100
                tck, _ = splprep([P2[:, 0], P2[:, 1]], u=sl2 / sl2[-1], w=w_, s=len(P2) * (0.6 * eps) ** 2, k=3)
                m = max(2, int(round(sl2[-1] / 20.0)))
                uu = np.linspace(0, 1, m + 1)
                X = np.stack(splev(uu, tck), 1)
                Tg = np.stack(splev(uu, tck, der=1), 1)
                X[0], X[-1] = P[0], P[-1]
                if hdir is not None:
                    Tg[0] = hdir * np.hypot(*Tg[0])
                if tdir is not None:
                    Tg[-1] = tdir * np.hypot(*Tg[-1])
                du = 1.0 / m
                for q in range(m):
                    c1 = X[q] + Tg[q] * du / 3
                    c2 = X[q + 1] - Tg[q + 1] * du / 3
                    d += 'C' + f(c1) + ' ' + f(c2) + ' ' + f(X[q + 1])
            if tl is not None:
                d += 'L' + f(tl)
        out.append(d + 'Z')
    return ''.join(out)


def _path_potrace(mask, up, alphamax=1.0, opttolerance=1.0, pre=1, blur=2.5):
    """마스크 → SVG 경로, Potrace 로(`potracer` — 순수 파이썬판, 이미 깔려 있다).
    Potrace 가 하는 일이 정확히 «계단만 지우기»다: 픽셀 윤곽을 최적 다각형으로 잡고, 꺾임이 alphamax 보다 작으면
    베지어 곡선, 크면 모서리로 남긴다(0 = 전부 각, 1 = 기본, 1.334 = 전부 곡선). opttolerance 는 곡선을 얼마나 합치나.
    🔴 기본값(pre 2·흐림 0.5·opttolerance 0.2)은 제미나이 그림에서 «더 나빴다» — 흔들림이 1px 보다 커서 Potrace 가
       디자인으로 보고 남긴다. 흐림 2.5px·opttolerance 1.0 이 U 자를 가장 매끈하게 했다(곡선 302 → 39개).
    🔴 대가: 뾰족한 끝·홈 바닥이 둥글게 뭉개진다 — 그래서 각진 로고(별·왕관)는 own 엔진이 기본이고,
       이건 동물·손글씨처럼 «둥근» 로고용이다 (2026-09-28 아담 왕관 비교: runs/…/engine_compare_*.png)."""
    import cv2
    import numpy as np
    import potrace
    big = cv2.resize(mask.astype(np.float32), (mask.shape[1] * pre, mask.shape[0] * pre), interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (0, 0), pre * blur) > 0.5
    path = potrace.Bitmap(~big).trace(turdsize=int(16 * pre * pre), alphamax=alphamax, opticurve=True, opttolerance=opttolerance)
    s = up / pre
    f = lambda p: f'{p.x * s:.2f},{p.y * s:.2f}'
    d = ''
    for cv in path:
        d += 'M' + f(cv.start_point)
        for sg in cv.segments:
            if sg.is_corner:
                d += 'L' + f(sg.c) + 'L' + f(sg.end_point)
            else:
                d += 'C' + f(sg.c1) + ' ' + f(sg.c2) + ' ' + f(sg.end_point)
        d += 'Z'
    return d


def _circle(cx, cy, r, up):
    """원 → 베지어 넷(svgio 는 M·L·C·Z 만 읽는다)."""
    x, y, R, K = cx * up, cy * up, r * up, 0.5523 * r * up
    return (f'M{x + R:.1f},{y:.1f}C{x + R:.1f},{y + K:.1f} {x + K:.1f},{y + R:.1f} {x:.1f},{y + R:.1f}'
            f'C{x - K:.1f},{y + R:.1f} {x - R:.1f},{y + K:.1f} {x - R:.1f},{y:.1f}'
            f'C{x - R:.1f},{y - K:.1f} {x - K:.1f},{y - R:.1f} {x:.1f},{y - R:.1f}'
            f'C{x + K:.1f},{y - R:.1f} {x + R:.1f},{y - K:.1f} {x + R:.1f},{y:.1f}Z')


def run(png, out, up=2, k=4, inks=None, eps=1.0, pad=30, engine='own', alphamax=1.0, snap=True):
    """여러 색 로고 → 색마다 층인 SVG(일러스트레이터 시안용). 색은 --inks 로 주거나 자동으로 k 개를 고른다.
    도형은 «도형답게» 딴다 — 원은 원, 길쭉하게 꽉 찬 띠·막대는 반듯한 직사각형, 나머지는 모서리+곧은 변+매끈한 곡선.
    🔴 letter_svg(=ad vec)로 따면 1px 요철을 충실히 따라가 크게 키웠을 때 오돌토돌하다(2026-09-28 아담 왕관) — 그래서 자체 윤곽.
    🔴 색 경계에 흰 실금이 안 생기게 넓은 층을 먼저 깔고 «뒤에 올 색 자리»로만 조금 넓힌다(흰 바탕 쪽으론 안 넓힌다)."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage as ndi
    im = np.asarray(Image.open(png).convert('RGB')).astype(float)
    ink = (im.min(2) < 235) | (im.max(2) - im.min(2) > 30)
    px = im[ink]
    if inks:
        cols = [np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) for h in inks.split(',')]
    else:
        # 자동: 가장 흔한 색에서 시작해 k-평균 몇 바퀴 — 흰 바탕과 섞인 가장자리 색은 결국 가까운 잉크로 간다
        q, cnt = np.unique((px // 16).astype(int), axis=0, return_counts=True)
        cols, seen = [], []
        for i in np.argsort(-cnt):
            c = q[i] * 16 + 8.0
            if all(np.abs(c - s_).sum() > 60 for s_ in seen):
                cols.append(c); seen.append(c)
            if len(cols) == k:
                break
        for _ in range(8):
            lab = np.argmin(((px[:, None] - np.array(cols)[None]) ** 2).sum(2), 1)
            cols = [px[lab == j].mean(0) if (lab == j).any() else cols[j] for j in range(len(cols))]
    cols = np.array(cols)
    lab = np.full(ink.shape, -1)
    lab[ink] = np.argmin(((px[:, None] - cols[None]) ** 2).sum(2), 1)
    order = sorted(range(len(cols)), key=lambda j: -(lab == j).sum())
    hexes = ['#%02x%02x%02x' % tuple(int(round(v)) for v in cols[j]) for j in order]
    u, total = up, ink.sum()
    layers, nrect, ncirc = [], 0, 0
    for n, j in enumerate(order):
        m = lab == j
        # 🔴 섞인 가장자리(노랑+흰 → 밝은 회색)가 다른 색 둘레에 «가는 고리»로 남는다 — 두 칸 열림으로 걷고
        #    작은 덩이(잉크의 0.3% 미만)도 뺀다 (2026-09-28 아담 왕관: 별·노란 줄 둘레 회색 테)
        m = ndi.binary_opening(m, iterations=2)
        cc, nc = ndi.label(m)
        if nc:
            sz = ndi.sum(m, cc, range(1, nc + 1))
            m = np.isin(cc, 1 + np.nonzero(sz >= total * 0.003)[0])
        shapes = []
        cc, nc = ndi.label(m)
        for kk in range(1, nc + 1):
            c = cc == kk
            ys, xs = np.nonzero(c)
            y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            w, h = x1 - x0, y1 - y0
            area = c.sum()
            if not snap:
                # 손글씨·낙서 레터링은 도형으로 펴지 않는다 — «I» 가 반듯한 직사각형이 되면 손맛이 죽는다(2026-09-28 드로우사인 로고)
                continue
            if 0.85 <= w / h <= 1.18 and abs(area / (np.pi * (max(w, h) / 2) ** 2) - 1) < 0.1:
                # 원: 가운데 = 무게중심, 반지름 = 넓이에서
                shapes.append(_circle(xs.mean() + 0.5, ys.mean() + 0.5, np.sqrt(area / np.pi), u)); ncirc += 1
                m[c] = False
            elif area / (w * h) >= 0.85 and max(w, h) >= 4 * min(w, h) and area >= total * 0.002:
                # 🔴 길쭉하게 꽉 찬 덩이(띠·줄)는 반듯한 직사각형 — 제미나이 줄은 1px 씩 기울어 따면 계단이 진다
                cl = [np.nonzero(c[:, x])[0] for x in range(x0 + w // 10, x1 - w // 10)]
                rw = [np.nonzero(c[y])[0] for y in range(y0 + h // 10, y1 - h // 10)]
                cl = [v for v in cl if len(v)]; rw = [v for v in rw if len(v)]
                ry0 = np.median([v.min() for v in cl]); ry1 = np.median([v.max() for v in cl]) + 1
                rx0 = np.median([v.min() for v in rw]); rx1 = np.median([v.max() for v in rw]) + 1
                shapes.append(f'M{rx0*u:.1f},{ry0*u:.1f}L{rx1*u:.1f},{ry0*u:.1f}L{rx1*u:.1f},{ry1*u:.1f}L{rx0*u:.1f},{ry1*u:.1f}Z'); nrect += 1
                m[c] = False
        later = np.isin(lab, order[n + 1:])
        m |= ndi.binary_dilation(m, iterations=2) & later            # 뒤에 올 색 밑으로만 넓힌다
        if m.any():
            layers.append((_path_potrace(m, u, alphamax=alphamax) if engine == 'potrace' else _path(m, u, eps=eps), hexes[n]))
        layers += [(d, hexes[n]) for d in shapes]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if pad >= 0:
        layers, W, H = svgio.crop(layers, pad=pad * u)
    else:
        W, H = im.shape[1] * u, im.shape[0] * u
    svgio.write(out, layers, W, H)
    for hx, j in zip(hexes, order):
        print(f'{hx}  {(lab == j).sum() / total * 100:5.1f}%')
    print(f'→ {out}  (경로 {len(layers)} · 원 {ncirc} · 직사각형 {nrect})')
    return out
