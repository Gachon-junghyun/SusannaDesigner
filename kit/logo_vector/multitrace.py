"""여러 색 로고 → 색마다 potrace(ad.relogo._potrace_d 재사용) → 평면 SVG. 바탕 네모는 따지 않고 정확한 직사각형으로 세운다.
usage: python multitrace.py <깨끗한.png> <out.svg> [--rect-color cream] [--split-red]"""
import sys, io, os, json, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import numpy as np
from PIL import Image
from scipy import ndimage
from ad.relogo import _potrace_d
PAL = {"white": (255, 255, 255), "cream": (243, 233, 210), "red": (168, 35, 42), "black": (30, 30, 30)}
ap = argparse.ArgumentParser(); ap.add_argument("png"); ap.add_argument("svg")
ap.add_argument("--work", type=int, default=4800); ap.add_argument("--rect-color", default="cream")
ap.add_argument("--split-red", action="store_true"); ap.add_argument("--close", type=int, default=0, help="이 반지름(px)보다 좁은 틈·홈을 메운다(간판으로 못 깎는 바늘 틈)"); ap.add_argument("--speck", type=float, default=4e-6)
a = ap.parse_args()
im = Image.open(a.png).convert("RGB")
if im.width != a.work: im = im.resize((a.work, round(im.height * a.work / im.width)), Image.LANCZOS)
rgb = np.asarray(im).astype(np.float32); H, W = rgb.shape[:2]
names = list(PAL); cols = np.array([PAL[n] for n in names], np.float32)
lab = np.argmin(((rgb[:, :, None, :] - cols[None, None]) ** 2).sum(-1), -1)   # 가장 가까운 팔레트 색
# 🔴 가장 가까운 색만 쓰면 «검정↔크림» 경계의 회색 픽셀이 빨강으로 간다 → 검은 선 밑에 가는 빨간 조각이 숨어
#    선만 보기에서 겹선으로 보였다(2026-10-10). 빨강은 «붉은 기가 확실한» 픽셀만, 나머지 경계는 검정/크림/흰 중 가까운 쪽으로.
r_, g_, b_ = rgb[..., 0], rgb[..., 1], rgb[..., 2]
reddish = (r_ - np.maximum(g_, b_)) > 60
ri = names.index("red")
alt = np.argmin(((rgb[:, :, None, :] - np.delete(cols, ri, 0)[None, None]) ** 2).sum(-1), -1)
alt = np.where(alt >= ri, alt + 1, alt)
lab = np.where(reddish, ri, np.where(lab == ri, alt, lab))
masks = {n: lab == i for i, n in enumerate(names)}
turd = int(a.speck * H * W) + 1
out, rep = [], {}
# 바탕 네모: 크림 픽셀 + 그 위에 얹힌 것들이 덮은 자리까지 포함한 «행·열 다수결» 경계
rect = None
if a.rect_color in masks and masks[a.rect_color].sum() > 0.02 * H * W:
    m = masks[a.rect_color]
    rows = np.where(m.mean(1) > 0.15)[0]; colsx = np.where(m.mean(0) > 0.15)[0]
    y0, y1, x0, x1 = rows.min(), rows.max() + 1, colsx.min(), colsx.max() + 1
    rect = (x0, y0, x1, y1)
    out.append('<g id="board"><rect x="%d" y="%d" width="%d" height="%d" fill="#F3E9D2"/></g>' % (x0, y0, x1 - x0, y1 - y0))
    rep["board"] = dict(x=int(x0), y=int(y0), w=int(x1 - x0), h=int(y1 - y0))
def trace(mask, gid, fill):
    if mask.sum() < turd: return
    if a.close:
        import cv2
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * a.close + 1, 2 * a.close + 1))
        m2 = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, k) > 0
        rep.setdefault("closed_px", {})[gid] = int((m2 & ~mask).sum()); mask = m2
    d, nseg, nc = _potrace_d(mask, lambda x, y: (x, y), turd=turd)
    out.append('<g id="%s"><path fill="%s" fill-rule="evenodd" d="%s"/></g>' % (gid, fill, d))
    rep[gid] = dict(segments=nseg, contours=nc)
red = masks["red"]
if a.split_red and rect:
    lb, n = ndimage.label(red); sl = ndimage.find_objects(lb)
    parts = {"roof": np.zeros_like(red), "cauldron": np.zeros_like(red), "letters": np.zeros_like(red)}
    for i, s in enumerate(sl, 1):
        top, bot = s[0].start, s[0].stop
        left = s[1].start
        # 지붕 = 네모 윗변보다 위에서 시작하는 덩이 · 솥 = 네모 아랫변 밖으로 나가거나 왼변 밖으로 삐져나온 덩이(테두리 고리) · 나머지 = 글자
        k = "roof" if top < rect[1] else ("cauldron" if (bot > rect[3] or (left < rect[0] and top > (rect[1] + rect[3]) / 2)) else "letters")
        parts[k] |= lb == i
    for k in ("cauldron", "letters", "roof"): trace(parts[k], k, "#A8232A")
else:
    trace(red, "red", "#A8232A")
bl = masks["black"]
if bl.sum():   # 선 하나짜리 무리: 가시를 깎고(열기) 가장 큰 덩어리만 남긴다 — 끝이 가늘면 떨어진 조각이 겹선으로 남는다(2026-10-10 처마선)
    import cv2
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    bl = cv2.morphologyEx(bl.astype(np.uint8), cv2.MORPH_OPEN, k) > 0
    lb, n = ndimage.label(bl)
    if n > 1:
        sz = ndimage.sum(bl, lb, range(1, n + 1)); bl = lb == (int(np.argmax(sz)) + 1); rep["line_dropped"] = int(n - 1)
trace(bl, "line", "#1E1E1E")
open(a.svg, "w", encoding="utf-8").write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">%s</svg>' % (W, H, W, H, "".join(out)))
print(json.dumps(rep, ensure_ascii=False, default=int))
