# 글자만 3000px 로 그려 «가장 가는 곳 / 선 끝 굵기»를 주 획 굵기(중앙값)에 대어 본다
import sys, re, fitz, numpy as np, cv2
from PIL import Image
svg = open(sys.argv[1], encoding='utf-8').read()
g = re.search(r'<g id="letters">.*?</g>', svg, re.S).group(0)
vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
s2 = re.sub(r'<g id="(hanji|frame|roof|cauldron)">.*?</g>\n', '', svg, flags=re.S)
pg = fitz.open('pdf', fitz.open('svg', s2.encode()).convert_to_pdf())[0]
z = 3000 / pg.rect.width; pix = pg.get_pixmap(matrix=fitz.Matrix(z, z))
a = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3].mean(2)
m = (a < 128).astype(np.uint8)
dt = cv2.distanceTransform(m, cv2.DIST_L2, 5)
sk = cv2.ximgproc.thinning(m * 255) > 0
k = cv2.filter2D(sk.astype(np.uint8), -1, np.ones((3, 3), np.uint8))
ends = sk & (k == 2)
med = np.median(dt[sk]) * 2
p90 = np.percentile(dt[sk], 90) * 2
rr = int(med * 0.6)
out = cv2.cvtColor((255 - m * 200).astype(np.uint8), cv2.COLOR_GRAY2BGR)
rows = []
for y, x in zip(*np.where(ends)):
    win = dt[max(0, y - rr):y + rr + 1, max(0, x - rr):x + rr + 1] * sk[max(0, y - rr):y + rr + 1, max(0, x - rr):x + rr + 1]
    t = win.max() * 2
    rows.append((t / p90, x, y))
    cv2.circle(out, (int(x), int(y)), 18, (0, 0, 255) if t / p90 < 0.25 else (0, 160, 0), 3)
rows.sort()
print('주 획(90%%) %.1fpx · 중앙 %.1fpx · 선 끝 %d 개' % (p90, med, len(rows)))
print('선 끝 굵기 / 주 획 (작은 순):', [round(r[0], 2) for r in rows[:10]])
Image.fromarray(out[..., ::-1]).save(sys.argv[2])
near = cv2.dilate(ends.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rr + 1,) * 2)) > 0
body = sk & ~near
w = dt[body] * 2
print('가장 가는 곳(1%%) %.1fpx = 주 획의 %.2f · 최소 %.1fpx = %.2f' % (np.percentile(w, 1), np.percentile(w, 1) / p90, w.min(), w.min() / p90))
