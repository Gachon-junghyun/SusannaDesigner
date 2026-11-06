"""골유리(플루티드 글라스) 굴절 — 판을 세로 띠로 나누고, 띠마다 자기 폭의 squeeze 배 구간을 가로로 눌러 담는다.

레퍼런스(refs/_모음/골유리_토러스, 1125×2000 흑백 토러스) 실측: 띠 44px(판 폭 3.9%, 25~26개), 띠 안 곡선 기울기가
실제 곡선의 약 2.5배 → 띠 가운데는 원래 자리, 띠 가장자리로 갈수록 바깥 내용을 끌어온다. 그래서 둥근 윤곽이 띠마다
위아래로 끊겨 톱날처럼 솟는다. 세로 방향은 건드리지 않는다.

python -m ad fluted <그림> --out <png> [--strip 0.039] [--squeeze 2.5] [--seam 0.18] [--soften 0] [--blur 0.6] [--gray] [--phase 0]
함수: fluted(img, strip=0.039, squeeze=2.5, seam=0.18, blur=0.6, gray=False, phase=0.0, bg=(0,0,0), soften=0.0) -> PIL RGB
"""
import numpy as np
from PIL import Image, ImageFilter


def fluted(img, strip=0.039, squeeze=2.5, seam=0.18, blur=0.6, gray=False, phase=0.0, bg=(0, 0, 0), soften=0.0):
    """strip: 띠 폭(판 폭 비율, 1 넘으면 px) · squeeze: 띠 하나가 담는 폭 배수(1 = 그대로, 클수록 톱날이 가파름)
    seam: 띠 가장자리 어둡게(0~1) · blur: 굴절 «뒤» 번짐 px(크면 띠 경계까지 뭉개진다, 레퍼런스는 경계가 또렷) ·
    soften: 굴절 «앞» 입력 흐림 px(띠 안만 부드럽게 — 잔무늬 많은 렌더는 6~8) · phase: 띠 시작 어긋남(띠 폭 비율)"""
    import cv2   # 무거운 의존은 함수 안에서
    im = img.convert("RGBA")
    if soften:
        im = im.filter(ImageFilter.GaussianBlur(soften))
    base = Image.new("RGBA", im.size, bg + (255,))
    base.alpha_composite(im)
    a = np.asarray(base.convert("RGB")).astype(np.float32)
    h, w = a.shape[:2]
    sw = strip if strip > 1 else strip * w
    x = np.arange(w, dtype=np.float32)
    i = np.floor((x - phase * sw) / sw)
    cx = (i + 0.5) * sw + phase * sw
    u = (x - cx) / (sw / 2)                     # 띠 안 위치 -1 ~ 1
    xs = cx + squeeze * (x - cx)
    mapx = np.tile(xs, (h, 1)).astype(np.float32)
    mapy = np.tile(np.arange(h, dtype=np.float32)[:, None], (1, w))
    out = cv2.remap(a, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if seam:
        out *= (1 - seam * np.abs(u) ** 3)[None, :, None]
    o = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    if blur:
        o = o.filter(ImageFilter.GaussianBlur(blur))
    return o.convert("L").convert("RGB") if gray else o
