# -*- coding: utf-8 -*-
"""제미나이 ✦ 표시 지우기 — 오른쪽 아래 구석에서 «네 갈래 별» 모양을 찾아 그 모양만 주변으로 메운다(inpaint).

- 🔴 자리를 «박지» 않고 «먼저 본다». 1024px 에서 별 가운데가 (905,905)·폭 46px 로 두 장이 같았다(2026-09-28 실측) — 알려진
  «48px·여백 32px» 자리와 달랐다. 그 자리 둘레에서 별 모양을 찾고, 약하면 구석 전체를 본다. 못 찾으면 안 건드린다.
- 표시는 반투명 흰색이라 바탕보다 «밝게» 튄다 — 국소 중앙값을 뺀 잔차에서 찾는다(어두운 사진·밝은 종이 둘 다).
- 옛 방법(font-ai letter_svg.unwatermark: 구석 사각형을 중앙값 한 색으로 덮기)은 레터링 흰 종이용이다. 사진·그림엔 네모 얼룩이 남는다.
- 🔴 이건 «보이는 표시»만 지운다. 파일 안의 생성 기록(SynthID 등)은 그대로고, 사이트는 샘플마다 «AI(제미나이)로 만든 예시»라고 적는다.
"""
import cv2
import numpy as np


def _star(size, p=2.2):
    """네 갈래 별(오목한 변) 마스크 — size×size"""
    t = np.linspace(0, 2 * np.pi, 400)
    x = np.sign(np.cos(t)) * np.abs(np.cos(t)) ** p
    y = np.sign(np.sin(t)) * np.abs(np.sin(t)) ** p
    r = (size - 1) / 2
    pts = np.stack([r + x * r, r + y * r], 1).astype(np.int32)
    m = np.zeros((size, size), np.uint8)
    cv2.fillPoly(m, [pts], 255)
    return m


# 실측(2026-09-28, 1024×1024 두 장): 별 가운데 (905,905) = 오른쪽·아래에서 119px, 폭 46px, 오목도 p≈2.8. 두 장이 1px 안에서 같았다.
ANCHOR, SIZE = 119 / 1024, 46 / 1024


def _residual(bgr):
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    res = g.astype(np.float32) - cv2.medianBlur(g, 61).astype(np.float32)
    return np.clip(cv2.GaussianBlur(res, (3, 3), 0), 0, None)


def _match(res, x0, y0, x1, y1, sizes, shapes=(2.4, 2.8)):
    roi = res[y0:y1, x0:x1]
    best = (0.0, 0, 0, 0)
    for s in sizes:
        if s >= min(roi.shape):
            break
        for p in shapes:
            sc = cv2.matchTemplate(roi, _star(s, p).astype(np.float32) / 255, cv2.TM_CCOEFF_NORMED)
            _, mx, _, loc = cv2.minMaxLoc(sc)
            if mx > best[0]:
                best = (float(mx), x0 + loc[0], y0 + loc[1], s)
    return best


def find(bgr, corner=0.26):
    """→ (score, x, y, size). 먼저 실측 자리(오른쪽·아래 119/1024) 둘레를 보고, 약하면 구석 전체를 본다"""
    h, w = bgr.shape[:2]
    res = _residual(bgr)
    k = min(w, h)
    cx, cy, s0, r = w - ANCHOR * k, h - ANCHOR * k, SIZE * k, 0.07 * k
    sizes = range(max(12, int(s0 * 0.7)), int(s0 * 1.4) + 1, 2)
    best = _match(res, max(0, int(cx - s0 - r)), max(0, int(cy - s0 - r)), min(w, int(cx + s0 + r)), min(h, int(cy + s0 + r)), sizes)
    if best[0] >= 0.5:
        return best
    wide = _match(res, int(w * (1 - corner)), int(h * (1 - corner)), w, h, range(max(12, int(s0 * 0.6)), int(s0 * 2.2) + 1, 4))
    return max(best, wide)


def unmark(bgr, min_score=0.45, grow=1.3):
    """→ (그림, 찾은 것 | None). 점수가 낮으면 안 건드린다(엉뚱한 곳을 지우느니 남기는 게 낫다)."""
    score, x, y, s = find(bgr)
    if score < min_score:
        return bgr, None
    h, w = bgr.shape[:2]
    S = int(s * grow) | 1
    cx, cy = x + s // 2, y + s // 2
    m = np.zeros((h, w), np.uint8)
    tpl = cv2.dilate(_star(S, 2.4), np.ones((5, 5), np.uint8))
    ax, ay = cx - S // 2, cy - S // 2
    bx0, by0 = max(0, ax), max(0, ay)
    bx1, by1 = min(w, ax + S), min(h, ay + S)
    m[by0:by1, bx0:bx1] = tpl[by0 - ay:by1 - ay, bx0 - ax:bx1 - ax]
    out = cv2.inpaint(bgr, m, 5, cv2.INPAINT_TELEA)
    return out, dict(score=round(score, 2), cx=int(cx), cy=int(cy), size=int(s))


def run(src, dst, min_score=0.45):
    im = cv2.imdecode(np.fromfile(src, np.uint8), cv2.IMREAD_COLOR)
    out, hit = unmark(im, min_score)
    ext = '.' + dst.rsplit('.', 1)[-1].lower()
    params = [cv2.IMWRITE_JPEG_QUALITY, 88] if ext in ('.jpg', '.jpeg') else []
    ok, buf = cv2.imencode(ext, out, params)
    buf.tofile(dst)
    return hit
