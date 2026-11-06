# -*- coding: utf-8 -*-
"""고객B · 한지 반전 — 깨끗한 벡터로 다시 짓기.
좌표 단위 = 원안(1086x1448) 1px. 4배 업스케일 마스크에서 따고 /4 한다.
  틀(네모 둘)   : 정확한 기하(다각형). 끝 자름만 지붕에서 일정한 틈(G)으로 잰다
  처마+서까래  : r1_x4 빨강 마스크 왼쪽 반을 거울로 → 좌우 대칭 → potrace
  기와 줄      : 가운데 다섯 장 평균 → 한 장 → 같은 모양 아홉 장, 같은 간격, 처마 밑 같은 틈
  가마솥       : 왼쪽 반 거울 → potrace
  글자         : redraw3(ChatGPT) x4 → potrace (티끌·틈 정리)
"""
import io, json, os, sys
import numpy as np, cv2, potrace
from PIL import Image
from shapely.geometry import Polygon, LineString, box
from shapely.affinity import translate
from shapely.ops import unary_union

W_ = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(W_)
RED, CREAM, BLACK = '#A8232A', '#F3E9D2', '#1A1A1A'
S = 4.0                      # 마스크 배율
G = 14.0                     # 지붕과 틀 끝 사이 틈(원안 실측 14px)
T = 30.0                     # 틀 두께(원안 29~30)
args = dict(a.split('=') for a in sys.argv[1:])
OPEN = float(args.get('open', 0))    # 글자 열기 반지름(4x px)
BLACK = args.get('black', BLACK)


def trace(mask, blur=2.0, optol=0.8, alphamax=1.0, turd=200):
    big = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), blur) > 0.5
    pl = potrace.Bitmap(~big).trace(turdsize=turd, alphamax=alphamax, opticurve=True, opttolerance=optol)
    curves = []
    for cv in pl:
        segs = []
        p0 = (cv.start_point.x / S, cv.start_point.y / S)
        cur = p0
        for sg in cv.segments:
            if sg.is_corner:
                segs.append(('L', (sg.c.x / S, sg.c.y / S)))
                segs.append(('L', (sg.end_point.x / S, sg.end_point.y / S)))
            else:
                segs.append(('C', (sg.c1.x / S, sg.c1.y / S), (sg.c2.x / S, sg.c2.y / S), (sg.end_point.x / S, sg.end_point.y / S)))
        curves.append((p0, segs))
    return curves


def g1(curves, lim=10.0):
    """곡선-곡선 마디에서 두 핸들을 한 직선 위로(길이는 그대로) — 선만 보기에서 미세한 꺾임이 안 남게"""
    import math
    out = []
    for p0, segs in curves:
        segs = [list(s) for s in segs]
        n = len(segs)
        for i in range(n):
            a, b = segs[i], segs[(i + 1) % n]
            if a[0] != 'C' or b[0] != 'C':
                continue
            P = a[3]; hin = (P[0] - a[2][0], P[1] - a[2][1]); hout = (b[1][0] - P[0], b[1][1] - P[1])
            li, lo = math.hypot(*hin), math.hypot(*hout)
            if li < 1e-6 or lo < 1e-6:
                continue
            ui = (hin[0] / li, hin[1] / li); uo = (hout[0] / lo, hout[1] / lo)
            ang = math.degrees(math.acos(max(-1, min(1, ui[0] * uo[0] + ui[1] * uo[1]))))
            if ang > lim or ang < 1e-9:
                continue
            u = (ui[0] + uo[0], ui[1] + uo[1]); lu = math.hypot(*u); u = (u[0] / lu, u[1] / lu)
            a[2] = (P[0] - u[0] * li, P[1] - u[1] * li)
            b[1] = (P[0] + u[0] * lo, P[1] + u[1] * lo)
        out.append((p0, [tuple(s) for s in segs]))
    return out


def d_of(curves, dx=0.0, dy=0.0):
    curves = g1(curves)
    f = lambda p: '%.3f %.3f' % (p[0] + dx, p[1] + dy)
    out = ''
    for p0, segs in curves:
        out += 'M' + f(p0)
        for s in segs:
            out += ('L' + f(s[1])) if s[0] == 'L' else ('C' + f(s[1]) + ' ' + f(s[2]) + ' ' + f(s[3]))
        out += 'Z'
    return out


def poly_of(curves):
    """윤곽들 → shapely (가장 바깥 + 구멍 무시: 거리 재기용)"""
    rings = []
    for p0, segs in curves:
        pts = [p0]; cur = p0
        for s in segs:
            if s[0] == 'L':
                pts.append(s[1]); cur = s[1]
            else:
                a, b, c = s[1], s[2], s[3]
                for t in np.linspace(0.1, 1, 10):
                    u = 1 - t
                    pts.append((u**3 * cur[0] + 3*u*u*t*a[0] + 3*u*t*t*b[0] + t**3*c[0],
                                u**3 * cur[1] + 3*u*u*t*a[1] + 3*u*t*t*b[1] + t**3*c[1]))
                cur = c
        rings.append(Polygon(pts).buffer(0))
    return unary_union(rings)


def npts(curves):
    return sum(len(s) for _, s in curves)


# ───────────── 1. 빨강 마스크 ─────────────
im = np.array(Image.open(os.path.join(W_, 'r1_x4.png')).convert('RGB')).astype(np.float32)
redness = im[..., 0] - im[..., 1]                       # 크림 ~32 · 빨강 ~150 · 흰 0
red = cv2.GaussianBlur(redness, (0, 0), 1.2) > 92
H4, W4 = red.shape
n, lb, st, cen = cv2.connectedComponentsWithStats(red.astype(np.uint8), 8)
comps = [(i, st[i], cen[i]) for i in range(1, n) if st[i, 4] > 400 * S * S]

# 축: 아래 네모 좌우 바깥 테두리(가운데 높이 여러 줄 평균)
xs_l, xs_r = [], []
for y in range(int(700 * S), int(1200 * S), 8):
    row = np.where(red[y])[0]
    xs_l.append(row.min()); xs_r.append(row.max() + 1)
cx4 = (np.median(xs_l) + np.median(xs_r)) / 2
CX = cx4 / S
print('축 cx = %.2f  아래 네모 바깥 %.2f ~ %.2f' % (CX, np.median(xs_l) / S, np.median(xs_r) / S))


def comp_at(x, y):
    return lb[int(y * S), int(x * S)]


def mirror_left(mask):
    c = int(round(cx4))
    left = mask[:, :c]
    out = np.zeros_like(mask)
    out[:, :c] = left
    w = min(c, W4 - c)
    out[:, c:c + w] = left[:, ::-1][:, :w]
    return out


# 처마+서까래 = (540, 282) 를 품은 덩이
roof_id = comp_at(300, 290) or comp_at(540, 290)
def opened(m, r):
    if r <= 0:
        return m
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2 * r + 1),) * 2)
    return cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, k).astype(bool)


RB = float(args.get('rblur', 2)); RO = float(args.get('ropen', 0))
roof_raw = opened(lb == roof_id, RO).astype(np.uint8)
# 서까래 바깥 테두리의 «어깨»(처마 밑에서 한 번 꺾여 넓어지는 턱)를 메워 한 줄로 — 원안 좌표(왼쪽만, 거울이 오른쪽을 만든다)
# 🔴 열기(open) «뒤에» 메운다 — 먼저 메우면 얇은 쐐기라 열기가 도로 깎는다(실측)
if args.get('shoulder', '1') == '1':
    sh = np.array([(125.2, 277.0), (131.0, 277.0), (122.0, 294.8), (114.0, 302.0), (100.0, 318.0)]) * S
    cv2.fillPoly(roof_raw, [sh.astype(np.int32)], 1)
roof_m = mirror_left(roof_raw.astype(bool))
Image.fromarray((roof_m[int(250*S):int(350*S), int(60*S):int(160*S)]*255).astype(np.uint8)).save(os.path.join(W_, "dbg_roof.png"))
ROT = float(args.get('roptol', 0.8))
roof_c = trace(roof_m, blur=RB, optol=ROT)
def parab_fix(curves, box, tag):
    """box 안에 시작·끝이 모두 든 연속 마디들을 «포물선 하나»(= 3차 베지어 하나)로 바꾼다.
    potrace 는 거의 수평인 곳을 평평한 직선 + 급한 곡선으로 나눠 선만 보기에서 꺾여 보인다(처마 가운데 실측)."""
    x0, x1, y0, y1 = box
    inb = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    out = []
    for p0, segs in curves:
        n = len(segs)
        starts = [segs[i - 1][-1] if i else p0 for i in range(n)]
        ok = [inb(starts[i]) and inb(segs[i][-1]) for i in range(n)]
        if not any(ok) or all(ok):
            out.append((p0, segs)); continue
        # 순환 연속 구간 찾기
        i0 = next(i for i in range(n) if ok[i] and not ok[i - 1])
        run = []
        i = i0
        while ok[i % n]:
            run.append(i % n); i += 1
        Pa, Pb = starts[run[0]], segs[run[-1]][-1]
        samp = []
        for j in run:
            cur = starts[j]; sg = segs[j]
            if sg[0] == 'L':
                samp.append(sg[-1]); continue
            a, b, c = sg[1], sg[2], sg[3]
            for t in np.linspace(0.05, 1, 12):
                u = 1 - t
                samp.append((u**3*cur[0]+3*u*u*t*a[0]+3*u*t*t*b[0]+t**3*c[0], u**3*cur[1]+3*u*u*t*a[1]+3*u*t*t*b[1]+t**3*c[1]))
        samp = np.array(samp)
        xa, ya, xb, yb = Pa[0], Pa[1], Pb[0], Pb[1]
        L = ya + (samp[:, 0] - xa) * (yb - ya) / (xb - xa)
        q = (samp[:, 0] - xa) * (samp[:, 0] - xb)
        cq = float((q * (samp[:, 1] - L)).sum() / (q * q).sum())
        err = np.abs(L + cq * q - samp[:, 1]).max()
        D = xb - xa
        Q = ((xa + xb) / 2, (ya + yb - cq * D * D) / 2)
        C1 = (Pa[0] + 2 / 3 * (Q[0] - Pa[0]), Pa[1] + 2 / 3 * (Q[1] - Pa[1]))
        C2 = (Pb[0] + 2 / 3 * (Q[0] - Pb[0]), Pb[1] + 2 / 3 * (Q[1] - Pb[1]))
        print('포물선 %s: 마디 %d 개 → 1 개 (%.1f→%.1f) · 최대 차 %.2f' % (tag, len(run), xa, xb, err))
        keep = [segs[j] for j in range(n) if j not in run]
        # 순서 유지: run 자리에 새 마디 하나
        new = []
        for j in range(n):
            if j == run[0]:
                new.append(('C', C1, C2, Pb))
            elif j not in run:
                new.append(segs[j])
        # p0 가 run 안의 시작점이면(run 이 0 을 지나면) 시작점을 Pb 로 옮겨야 하지만, i0 를 run 의 처음으로 잡아 p0 는 run 밖이다
        out.append((p0 if run[0] != 0 or True else Pb, new))
    return out


if args.get('parab', '1') == '1':
    roof_c = parab_fix(roof_c, (300, 790, 295, 318), '처마 밑')
    roof_c = parab_fix(roof_c, (320, 795, 255, 285), '처마 위')
roof_p = poly_of(roof_c)
print('지붕: 윤곽 %d · 마디 %d' % (len(roof_c), npts(roof_c)))

# 가마솥
caul_id = comp_at(543, 820)
caul_m = opened(mirror_left(lb == caul_id), RO)
caul_c = trace(caul_m, blur=RB, optol=ROT)
print('가마솥: 윤곽 %d · 마디 %d' % (len(caul_c), npts(caul_c)))

# ───────────── 2. 기와 한 장 ─────────────
tiles = sorted([(c[2][0], c[0]) for c in comps if 280 * S < c[1][1] < 340 * S and c[1][3] < 160 * S], key=lambda t: t[0])
print('기와 덩이 %d 개, 중심 x:' % len(tiles), [round(t[0] / S, 1) for t in tiles])
use = tiles[2:7]
P = int(90 * S)
acc = np.zeros((2 * P, 2 * P), np.float32)
for cxk, i in use:
    m = (lb == i).astype(np.float32)
    ys, xs = np.nonzero(m)
    my, mx = ys.mean(), xs.mean()
    M = np.float32([[1, 0, P - mx], [0, 1, P - my]])
    acc += cv2.warpAffine(m, M, (2 * P, 2 * P), flags=cv2.INTER_LINEAR)
tile_m = (acc / len(use)) > 0.5
tile_c0 = trace(opened(tile_m, RO), blur=float(args.get('tblur', 2)), optol=ROT)
tile_p0 = poly_of(tile_c0)
tile_c = [((p0[0] - P / S, p0[1] - P / S), [(s[0],) + tuple((q[0] - P / S, q[1] - P / S) for q in s[1:]) for s in segs]) for p0, segs in tile_c0]
tile_p = translate(tile_p0, -P / S, -P / S)            # 무게중심이 (0,0)
print('기와 한 장: 마디 %d · 폭 %.1f 높이 %.1f' % (npts(tile_c), tile_p.bounds[2] - tile_p.bounds[0], tile_p.bounds[3] - tile_p.bounds[1]))

# 원안 기와-처마 틈(가운데 다섯 장)
roof_full = roof_p
gaps = []
for cxk, i in use:
    ys, xs = np.nonzero(lb == i)
    tp = translate(tile_p, xs.mean() / S, ys.mean() / S)
    gaps.append(tp.distance(roof_p))
GT = float(np.median(gaps))
print('원안 기와-처마 틈 %.2f' % GT, [round(g, 1) for g in gaps])


def place(x):
    """x 에 놓고 처마와 틈이 GT 가 되는 y"""
    lo, hi = 300.0, 460.0
    for _ in range(40):
        mid = (lo + hi) / 2
        d = translate(tile_p, x, mid).distance(roof_p)
        if translate(tile_p, x, mid).intersects(roof_p) or d < GT:
            lo = mid
        else:
            hi = mid
    return hi


def fits(sp, c0):
    """아홉 장이 전부 처마 밑 틈 GT 로 앉고(서까래에 안 걸리고) 양끝 여유가 얼마나 되나"""
    xs = [CX + c0 + (k - 4) * sp for k in range(9)]
    ys = [place(x) for x in xs]
    # 처마에 걸린 자리(y)가 매끈한 포물선이어야 — 서까래에 걸리면 튀어 내려간다
    jump = max(abs(ys[k] - (ys[k - 1] + ys[k + 1]) / 2) for k in range(1, 8))
    end = max(ys[0], ys[-1]) - min(ys)
    return xs, ys, jump


best = None
if 'sp' not in args:
    for sp in np.arange(92.0, 80.0, -0.5):
        for c0 in np.arange(-45, 45.1, 1.0):
            xs, ys, jump = fits(sp, c0)
            # 양끝이 서까래에 걸리지 않았나: 끝 장 y 가 이웃 경향(2차 외삽)에서 1px 안
            e0 = abs(ys[0] - (3 * ys[1] - 3 * ys[2] + ys[3])); e8 = abs(ys[8] - (3 * ys[7] - 3 * ys[6] + ys[5]))
            if e0 < 1.0 and e8 < 1.0:
                best = (best or []) + [c0]
        if best:
            SP, C0 = float(sp), float((min(best) + max(best)) / 2)   # 되는 범위의 가운데 = 양끝 여유가 같다
            print('되는 치우침 범위 %.0f ~ %.0f' % (min(best), max(best)))
            break
else:
    SP = float(args['sp']); C0 = float(args.get('c0', 0))
xs_t = [CX + C0 + (k - 4) * SP for k in range(9)]
placed = [translate(tile_p, x, place(x)) for x in xs_t]
print('간격 %.2f · 치우침 %.2f' % (SP, C0))
dl = placed[0].distance(roof_p); dr = placed[-1].distance(roof_p)
print('양끝 기와 ↔ 지붕 거리: 왼 %.2f 오른 %.2f' % (dl, dr))
ty = [round(p.centroid.y, 2) for p in placed]
print('기와 y:', ty)

# ───────────── 3. 틀 ─────────────
TOP, BOT = 119.5, 1321.5
uL, uR = CX - 401.5, CX + 401.5
lL, lR = CX - 448.0, CX + 448.0
roof_g = roof_p.buffer(G)


def cut_top(x):          # 위 네모 옆기둥 아래 끝: 지붕(틈 G) 바로 위
    ln = LineString([(x, 0), (x, 800)])
    return min(pt[1] for g in [ln.intersection(roof_g)] for pt in (g.coords if g.geom_type == 'LineString' else [c for gg in g.geoms for c in gg.coords]))


ya_o, ya_i = cut_top(uL), cut_top(uL + T)
upper = [(uL, ya_o), (uL, TOP), (2 * CX - uL, TOP), (2 * CX - uL, ya_o), (2 * CX - uL - T, ya_i), (2 * CX - uL - T, TOP + T), (uL + T, TOP + T), (uL + T, ya_i)]
# 아래 네모 옆기둥 위 끝: 지붕·기와(틈 G) 아래 — 좌우 중 더 낮은 쪽으로 맞춰 수평
allr = unary_union([roof_p] + placed).buffer(G)


def cut_bot(x):
    ln = LineString([(x, 0), (x, 800)])
    g = ln.intersection(allr)
    cs = g.coords if g.geom_type == 'LineString' else [c for gg in g.geoms for c in gg.coords]
    return max(c[1] for c in cs)


yb = max(cut_bot(x) for x in np.linspace(lL, lL + T, 7).tolist() + np.linspace(lR - T, lR, 7).tolist())
yb = float(args.get('yb', yb))
lower = [(lL, yb), (lL, BOT), (lR, BOT), (lR, yb), (lR - T, yb), (lR - T, BOT - T), (lL + T, BOT - T), (lL + T, yb)]
print('위 기둥 끝 y %.1f/%.1f · 아래 기둥 시작 y %.1f' % (ya_o, ya_i, yb))

# ───────────── 4. 한지(크림) ─────────────
# 위 네모 바깥 → 처마 밑 → 서까래 속을 따라 아래 네모 바깥으로 내려간다(이음은 빨강 밑에 숨는다)
inner = roof_p.buffer(-3)


def mid_cov(x, ymin=200, ymax=420):
    ln = LineString([(x, ymin), (x, ymax)])
    g = ln.intersection(inner)
    segs = [g] if g.geom_type == 'LineString' else list(g.geoms)
    segs = [s for s in segs if s.length > 2]
    s = max(segs, key=lambda s: s.coords[0][1])      # 가장 아래 덩이(서까래)
    return (s.coords[0][1] + s.coords[-1][1]) / 2


yA = mid_cov(uL); yB = mid_cov(lL)
ok = inner.contains(LineString([(uL, yA), (lL, yB)]))
print('한지 계단 (%.1f → %.1f) 지붕 속에 숨나: %s' % (yA, yB, ok))
cream = [(uL, TOP), (2 * CX - uL, TOP), (2 * CX - uL, yA), (2 * CX - lL, yB), (2 * CX - lL, BOT), (lL, BOT), (lL, yB), (uL, yA)]

# ───────────── 5. 글자 ─────────────
li = np.array(Image.open(os.path.join(W_, 'l3_x4.png')).convert('L')).astype(np.float32)
ink = cv2.GaussianBlur(255 - li, (0, 0), 1.2) > 128
n2, lb2, st2, _ = cv2.connectedComponentsWithStats(ink.astype(np.uint8), 8)
big = max(st2[1:, 4])
keep = np.zeros_like(ink)
dropped = []
for i in range(1, n2):
    if st2[i, 4] > 0.002 * big:
        keep |= lb2 == i
    else:
        dropped.append(int(st2[i, 4]))
# 작은 구멍(틈·긁힘) 메우기 — ㅇ 속은 크니 남는다
inv = (~keep).astype(np.uint8)
n3, lb3, st3, _ = cv2.connectedComponentsWithStats(inv, 4)
filled = []
for i in range(1, n3):
    if st3[i, 4] < 0.02 * big and st3[i, 0] > 0 and st3[i, 1] > 0:
        keep[lb3 == i] = True; filled.append(int(st3[i, 4]))
raw_keep = keep.copy()
CLOSE = float(args.get('close', 0))
if CLOSE > 0:   # 좁은 틈·홈 메우기
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2 * CLOSE + 1),) * 2)
    keep = cv2.morphologyEx(keep.astype(np.uint8), cv2.MORPH_CLOSE, k).astype(bool)
if OPEN > 0:    # 좁은 돌기(혹·바늘 끝) 떼기
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(2 * OPEN + 1),) * 2)
    keep = cv2.morphologyEx(keep.astype(np.uint8), cv2.MORPH_OPEN, k).astype(bool)
Image.fromarray(((raw_keep ^ keep) * 255).astype(np.uint8)).save(os.path.join(W_, 'let_diff.png'))
print('글자 정리로 바뀐 픽셀 %d (전체 잉크의 %.2f%%)' % ((raw_keep ^ keep).sum(), 100 * (raw_keep ^ keep).sum() / raw_keep.sum()))
print('글자: 티끌 %d 개 버림 %s · 구멍 %d 개 메움 %s' % (len(dropped), dropped[:8], len(filled), filled[:8]))
let_c = trace(keep, blur=float(args.get('lblur', 2)), optol=float(args.get('loptol', 0.8)), alphamax=float(args.get('lalpha', 1.0)), turd=400)
# 원안 글자 상자에 맞춘다(원안 검정 덩이 상자)
org = np.array(Image.open(os.path.join(OUT, '..', '..', 'mark', 'tall', 'P03_한지반전.png')).convert('RGB')).astype(int)
blk = (org.mean(2) < 90) & (np.abs(org[..., 0] - org[..., 2]) < 40)
blk[:800] = False
ys, xs = np.nonzero(blk)
ob = (np.percentile(xs, 0.05), np.percentile(ys, 0.05), np.percentile(xs, 99.95), np.percentile(ys, 99.95))
lp = poly_of(let_c)
lb_ = lp.bounds
sc = (ob[2] - ob[0]) / (lb_[2] - lb_[0])
ocx, ocy = (ob[0] + ob[2]) / 2, (ob[1] + ob[3]) / 2
lcx, lcy = (lb_[0] + lb_[2]) / 2, (lb_[1] + lb_[3]) / 2
OX = float(args.get('lx', 0)); OY = float(args.get('ly', 0))
let_c = [((ocx + (p0[0] - lcx) * sc + OX, ocy + (p0[1] - lcy) * sc + OY),
          [(s[0],) + tuple((ocx + (q[0] - lcx) * sc + OX, ocy + (q[1] - lcy) * sc + OY) for q in s[1:]) for s in segs]) for p0, segs in let_c]
print('글자: 윤곽 %d · 마디 %d · 배율 %.4f · 원안 상자 %s' % (len(let_c), npts(let_c), sc, [round(v, 1) for v in ob]))

# ───────────── 6. SVG ─────────────
def pts_d(pts):
    return 'M' + 'L'.join('%.2f %.2f' % p for p in pts) + 'Z'


allb = unary_union([roof_p, Polygon(lower), Polygon(upper)]).bounds
M = 40
vx, vy = allb[0] - M, allb[1] - M
vw, vh = allb[2] - allb[0] + 2 * M, allb[3] - allb[1] + 2 * M
svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%.2f" height="%.2f" viewBox="%.2f %.2f %.2f %.2f">\n'
       '<g id="hanji"><path fill="%s" d="%s"/></g>\n'
       '<g id="frame"><path fill="%s" d="%s"/><path fill="%s" d="%s"/></g>\n'
       '<g id="roof"><path fill="%s" d="%s"/><g id="tiles">%s</g></g>\n'
       '<g id="cauldron"><path fill="%s" d="%s"/></g>\n'
       '<g id="letters"><path fill="%s" fill-rule="evenodd" d="%s"/></g>\n</svg>\n') % (
    vw, vh, vx, vy, vw, vh, CREAM, pts_d(cream), RED, pts_d(upper), RED, pts_d(lower),
    RED, d_of(roof_c), ''.join('<path fill="%s" d="%s"/>' % (RED, d_of(tile_c, x, p.centroid.y - tile_p.centroid.y)) for x, p in zip(xs_t, placed)),
    RED, d_of(caul_c), BLACK, d_of(let_c))
name = args.get('out', os.path.join(W_, 'build.svg'))
io.open(name, 'w', encoding='utf-8').write(svg)
print('→', name, '%.0f x %.0f' % (vw, vh))
