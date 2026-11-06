"""액체 크롬 덮개 — 평면 포스터 위에 판 전체 액체 금속 층을 한 장 덮는다(2D, numpy).

레퍼런스(refs/_모음/포스터_그리드/36_liquid_chrome) 실측: 몸은 검정·흰색이 크게 갈린 부드러운 반사, 등성이마다 판 폭 0.9%
안팎의 얇고 또렷한 흰 테, 강한 색은 몇 군데의 박막 간섭(무지개)뿐(약 5%). 순서:
  1) 판 전체 높이 지도(휘어 민 노이즈 → 덩어리·구멍·등성이)  2) 법선으로 아래 판을 굴절(왜곡)
  3) 반사 방향 → 위도·경도 스튜디오 지도 → 색 램프(브랜드)  4) 프레넬(기울수록 크롬, 평평하면 아래 판이 보임)
  5) 강조(점광 하이라이트)  6) 박막 간섭(고른 자리에만)
아래 판의 글자는 손대지 않는다 — 덮개가 굴절·반사로만 바꾼다.

python -m ad liquid --text "S U|SAN|N A" --font <ttf> --out <png> [--size 1600x1600] [--refract 0.03] [--seed 7]
함수: overlay(base, ...) -> PIL RGB · poster(rows, font, W, H, bg, fg) -> PIL RGB(평면 판)
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 수산나 청록(브랜드 700 · 600 · 기본 · 400) 램프. 0 = 반사 없음, 1 = 하얗게 날아감
RAMP_BRAND = [(0.00, "#010605"), (0.25, "#04211E"), (0.45, "#00726C"), (0.62, "#00A79D"),
              (0.78, "#35C2B8"), (0.90, "#CFF0ED"), (1.00, "#FFFFFF")]
# 크롬은 흑백 위주에 청록 기운만(역광과 같이 쓸 때 — 청록은 빛줄기가 낸다)
RAMP_TEALCHROME = [(0.00, "#000000"), (0.30, "#050D0C"), (0.55, "#24413E"), (0.72, "#5E8F8A"),
                   (0.86, "#CFE6E3"), (1.00, "#FFFFFF")]
RAMP_CHROME = [(0.00, "#0A0A0A"), (0.30, "#2E2C2B"), (0.55, "#7A746D"), (0.80, "#D9DEE2"), (1.00, "#FFFFFF")]


def _hex(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def _ramp(t, stops):
    xs = np.array([s[0] for s in stops], np.float32)
    cs = np.stack([_hex(s[1]) for s in stops])
    t = np.clip(t, 0, 1)
    return np.stack([np.interp(t, xs, cs[:, k]) for k in range(3)], -1)


def _noise(h, w, scale, rng):
    """부드러운 노이즈(대략 -1~1). scale = 덩어리 크기 px"""
    import cv2
    sh, sw = max(2, int(h / scale) + 3), max(2, int(w / scale) + 3)
    n = rng.standard_normal((sh, sw)).astype(np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    n = cv2.GaussianBlur(n, (0, 0), scale * 0.25)
    return n / (np.abs(n).max() + 1e-6)


def poster(rows, font, W, H, bg="#000000", fg="#FFFFFF", margin=0.08, gap=0.03):
    """평면 판: rows = ['S U', 'SAN', 'N A'] 칸 격자(공백 = 빈 칸). 모든 글자 같은 크기, 칸 가운데."""
    nr, nc = len(rows), max(len(r) for r in rows)
    cw = (W * (1 - 2 * margin) - gap * W * (nc - 1)) / nc
    ch = (H * (1 - 2 * margin) - gap * W * (nr - 1)) / nr
    probe = ImageFont.truetype(font, 1000)
    chars = [c for r in rows for c in r if c != " "]
    bw = max(probe.getbbox(c)[2] - probe.getbbox(c)[0] for c in chars)
    bh = max(probe.getbbox(c)[3] - probe.getbbox(c)[1] for c in chars)
    f = ImageFont.truetype(font, int(1000 * min(cw / bw, ch / bh)))
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    for i, r in enumerate(rows):
        for j, c in enumerate(r.ljust(nc)):
            if c == " ":
                continue
            bx = f.getbbox(c)
            cx = W * margin + j * (cw + gap * W) + cw / 2
            cy = H * margin + i * (ch + gap * W) + ch / 2
            d.text((cx - (bx[0] + bx[2]) / 2, cy - (bx[1] + bx[3]) / 2), c, font=f, fill=fg)
    return im


def _env(seed, envscale=0.22, envedge=0.07):
    """위도·경도 스튜디오 지도: 밝은 덩어리·어두운 덩어리가 또렷한 경계로 섞이고 경계마다 밝은 테."""
    rng = np.random.default_rng(seed + 100)
    EH, EW = 256, 512
    en = _noise(EH, EW, EW * envscale, rng) * 0.75 + _noise(EH, EW, EW * envscale * 0.4, rng) * 0.25
    en = (en - np.median(en)) / (en.std() + 1e-6)
    elat = np.linspace(np.pi / 2, -np.pi / 2, EH, dtype=np.float32)[:, None]
    tex = 1 / (1 + np.exp(np.clip(-en / envedge, -60, 60)))
    tex = tex * (0.30 + 0.70 * np.clip((elat + 0.3) / 0.8, 0, 1)) + 0.04
    tex += 0.55 * np.exp(-(en / (envedge * 2.5)) ** 2)
    return np.clip(tex, 0, 1.2).astype(np.float32)


def overlay(base, seed=7, scale=0.30, warp=0.35, relief=0.08, refract=0.025, f0=0.06, fpow=1.6,
            ramp=RAMP_BRAND, spec=0.9, film=3, film_w=0.9, film_r=0.05, dispersion=0.0, rim=0.8, rim_w=0.035, ss=1):
    """base: 평면 판(PIL). scale: 액체 덩어리 크기(판 폭 비율) · warp: 휘어 밀기 세기(덩어리가 흘러내린 모양)
    relief: 높이(판 폭 비율, 클수록 등성이가 가파르고 크롬이 넓어짐) · refract: 굴절로 아래 판을 미는 거리(판 폭 비율)
    f0: 평평한 곳의 반사율(작을수록 글자가 잘 보임) · fpow: 기울기에 따른 반사율 오름 · spec: 강조 하이라이트 세기
    film: 박막 간섭 자리 수 · film_w: 그 세기 · film_r: 자리 반경(판 폭 비율) · dispersion: 굴절 색 갈림(0 = 없음)"""
    import cv2
    rng = np.random.default_rng(seed)
    b0 = np.asarray(base.convert("RGB")).astype(np.float32)
    H0, W0 = b0.shape[:2]
    P = int(W0 * 0.15)                               # 판 밖 여유 — 끝에서 노이즈를 접으면 가로 띠가 생긴다
    b = cv2.copyMakeBorder(b0, P, P, P, P, cv2.BORDER_CONSTANT, value=[float(x) for x in b0[0, 0]])
    H, W = b.shape[:2]
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    # 1) 높이 지도 — 노이즈를 노이즈로 휘어 밀어(도메인 워핑) 흘러내린 덩어리·구멍을 만든다
    S = W0 * scale
    wx = _noise(H, W, S * 1.2, rng) * warp * S
    wy = _noise(H, W, S * 1.2, rng) * warp * S
    n1 = _noise(H, W, S, rng)
    n2 = _noise(H, W, S * 0.45, rng)
    f = cv2.remap(n1 * 0.75 + n2 * 0.25, gx + wx, gy + wy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    f = (f - f.mean()) / (f.std() + 1e-6)
    h = np.tanh(f * 1.6) * relief * W0              # 판판한 고원 + 가파른 비탈 = 액체 막
    h = cv2.GaussianBlur(h, (0, 0), W0 * 0.002)
    # 2) 법선
    hx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3) / 8
    hy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3) / 8
    nrm = np.stack([-hx, -hy, np.ones_like(h)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    nx, ny, nz = nrm[..., 0], nrm[..., 1], nrm[..., 2]
    # 3) 굴절 — 아래 판을 «매끈하게 다듬은» 법선 방향으로 민다(왜곡). 날 선 법선으로 밀면 글자 속공간이 찢겨 조각이 남는다
    hs = cv2.GaussianBlur(h, (0, 0), W0 * 0.008)
    sx = cv2.Sobel(hs, cv2.CV_32F, 1, 0, ksize=3) / 8
    sy = cv2.Sobel(hs, cv2.CV_32F, 0, 1, ksize=3) / 8
    sn = np.sqrt(sx ** 2 + sy ** 2 + 1)
    rnx, rny = -sx / sn, -sy / sn
    k = refract * W0
    chans = []
    for ci, mul in enumerate((1 + dispersion, 1.0, 1 - dispersion)):
        chans.append(cv2.remap(b[..., ci], gx - rnx * k * mul, gy - rny * k * mul, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT))
    under = np.stack(chans, -1)
    # 4) 반사 — 보는 방향 +z, 반사 방향을 위도·경도 지도로
    r = np.stack([2 * nz * nx, 2 * nz * ny, 2 * nz * nz - 1], -1)
    lon = np.arctan2(r[..., 0], r[..., 2])
    lat = np.arcsin(np.clip(-r[..., 1], -1, 1))
    tex = _env(seed)
    EH, EW = tex.shape
    u = ((lon / (2 * np.pi) + 0.5) * (EW - 1)).astype(np.float32)
    v = ((0.5 - lat / np.pi) * (EH - 1)).astype(np.float32)
    env = cv2.remap(tex, u, v, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    chrome = _ramp(env, ramp)
    F = f0 + (1 - f0) * np.clip(1 - nz, 0, 1) ** (1 / fpow) * 1.0
    F = np.clip(F, 0, 1)[..., None]
    out = under * (1 - F) + chrome * F
    # 4-b) 흰 테 — 고원 어깨의 등고선(레퍼런스의 판 폭 0.9% 흰 반사 테)
    if rim:
        rl = np.exp(-((np.abs(f) - 0.45) / rim_w) ** 2) * np.clip((1 - nz) * 6, 0, 1)
        out = 255 - (255 - out) * (1 - np.clip(rl * rim, 0, 1)[..., None])
    # 5) 강조 — 점광 둘(위 왼쪽, 오른쪽)의 거울 하이라이트를 «스크린»으로
    if spec:
        hl = np.zeros_like(h)
        for l in ((-0.45, -0.55, 0.70), (0.6, -0.2, 0.77)):
            l = np.array(l, np.float32); l /= np.linalg.norm(l)
            hl += np.clip(r[..., 0] * l[0] + r[..., 1] * l[1] + r[..., 2] * l[2], 0, 1) ** 220
        hl = np.clip(hl * spec, 0, 1)[..., None]
        out = 255 - (255 - out) * (1 - hl)
    # 6) 박막 간섭 — 고른 자리 근처, 비탈 띠에만 무지개(두께 = 높이·기울기)
    if film:
        slope = 1 - nz
        cand = np.argwhere((slope > np.percentile(slope, 80)) & (gx > P + W0 * 0.12) & (gx < P + W0 * 0.88) & (gy > P + H0 * 0.08) & (gy < P + H0 * 0.92))
        pick = cand[rng.choice(len(cand), film, replace=False)]
        spot = np.zeros_like(h)
        rad = W0 * film_r
        for yy, xx in pick:
            spot = np.maximum(spot, np.exp(-(((gx - xx) ** 2 + (gy - yy) ** 2) / (2 * rad ** 2))))
        thick = (h / (relief * W0) * 0.8 + slope * 3.0)
        hue = (thick * 1.9 + 0.6) % 1.0
        hsv = np.stack([hue * 179, np.full_like(hue, 230), np.full_like(hue, 255)], -1).astype(np.uint8)
        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).astype(np.float32)
        band = np.exp(-((slope - 0.30) / 0.17) ** 2)        # 좁은 비탈 띠에만(넓히면 기름막처럼 번진다)
        wgt = (spot * band * film_w)[..., None]
        lum = out.mean(-1, keepdims=True) / 255
        out = out * (1 - wgt) + rgb * (0.35 + 0.65 * lum) * wgt
    out = out[P:P + H0, P:P + W0]
    o = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    if ss > 1:
        o = o.resize((W0 // ss, H0 // ss), Image.LANCZOS)
    return o


# 수산나 후광 램프: 0 = 빛 없음, 1 = 하얗게 날아감(가운데 흰 → 청록 400 → 청록 700 → 어둠)
GLOW_BRAND = [(0.00, "#000000"), (0.18, "#003A36"), (0.40, "#00726C"), (0.62, "#35C2B8"),
              (0.82, "#CFF0ED"), (1.00, "#FFFFFF")]


def backlight(mask, center=(0.5, 0.5), rays=1.0, ray_len=0.6, ray_n=72, ray_break=0.85, bloom=0.6,
              peak=0.72, ramp=GLOW_BRAND, seed=7, work=0.25):
    """역광(후광) — 글자 «뒤»에 광원을 두어 윤곽에서 빛이 퍼지고(bloom) 빛줄기가 바깥으로 뻗게(god rays).
    mask: 0~1 글자 마스크 · center: 광원 자리(판 비율) · rays: 빛줄기 세기 · ray_len: 빛줄기 길이(0~1, 클수록 멀리)
    ray_n: 표본 수 · ray_break: 빛줄기를 각도 노이즈로 끊는 정도(0 = 고른 부채, 1 = 갈라진 줄기)
    bloom: 윤곽 번짐 세기 · peak: 글자 밖 빛의 상한(0.72 = 밝은 청록, 1 이면 흰색이라 글자 윤곽이 묻힌다) · work: 계산 해상도 비율(빛은 부드러워 낮춰도 된다). 반환: 0~1+ 밝기(H×W float)"""
    import cv2
    H, W = mask.shape
    w, h = max(64, int(W * work)), max(64, int(H * work))
    m = cv2.resize(mask.astype(np.float32), (w, h), interpolation=cv2.INTER_AREA)
    rng = np.random.default_rng(seed)
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    cx, cy = center[0] * w, center[1] * h
    # 빛줄기를 갈라 주는 각도 노이즈(가는 줄 + 굵은 줄)
    ang = np.arctan2(gy - cy, gx - cx)
    fine = rng.standard_normal(720).astype(np.float32)
    coarse = rng.standard_normal(90).astype(np.float32)
    ia = ((ang + np.pi) / (2 * np.pi))
    angn = np.interp(ia * 720, np.arange(721), np.r_[fine, fine[0]]) * 0.5 + \
           np.interp(ia * 90, np.arange(91), np.r_[coarse, coarse[0]])
    angn = (angn - angn.min()) / (np.ptp(angn) + 1e-6)
    src = m * (1 - ray_break + ray_break * angn ** 2.5)
    # 빛줄기: 광원 쪽으로 가며 표본을 모은다(그 선 위에 글자가 있으면 빛을 받는다 → 글자 바깥으로 뻗음)
    acc = np.zeros_like(m)
    wsum = 0.0
    for i in range(ray_n):
        s = 1 - ray_len * i / ray_n
        wt = (1 - i / ray_n) ** 1.2
        acc += cv2.remap(src, cx + (gx - cx) * s, cy + (gy - cy) * s, cv2.INTER_LINEAR, borderValue=0) * wt
        wsum += wt
    ray = acc / wsum
    ray = cv2.GaussianBlur(ray, (0, 0), w * 0.003)
    # 번짐: 세 크기 가우시안을 더한다(가까이 강하게, 멀리 넓게)
    bl = sum(cv2.GaussianBlur(m, (0, 0), w * r) * a for r, a in ((0.006, 0.9), (0.025, 0.7), (0.08, 0.6)))
    g = rays * ray + bloom * bl
    out = m < 0.5
    g = g / (np.percentile(g[out], 99.5) + 1e-6) * peak       # 글자 밖 빛을 peak 에 맞춘다(글자 윤곽을 지킨다)
    return cv2.resize(g, (W, H), interpolation=cv2.INTER_CUBIC)


def glow_poster(rows, font, W, H, bg="#000000", fg="#FFFFFF", ramp=GLOW_BRAND, gain=1.0, **kw):
    """평면 판 + 글자 뒤 후광. 반환: (판 PIL, 빛 밝기 float) — 빛은 overlay 뒤에 한 번 더 «스크린»으로 얹을 수 있다."""
    flat = poster(rows, font, W, H, bg="#000000", fg="#FFFFFF")
    m = np.asarray(flat.convert("L")).astype(np.float32) / 255
    g = np.clip(backlight(m, **kw) * gain, 0, 1.2)
    light = _ramp(np.clip(g, 0, 1), ramp)
    b = _hex(bg)
    out = np.clip(b + light, 0, 255)                         # 바탕에 빛을 더하고
    out = out * (1 - m[..., None]) + _hex(fg) * m[..., None]  # 글자는 그 위(빛보다 앞)
    return Image.fromarray(out.astype(np.uint8)), g


def screen_light(img, g, amount=0.12, ramp=GLOW_BRAND):
    """덮개 위로 빛을 한 번 더 «스크린» — 크롬 막 너머로 빛이 비쳐 나오는 느낌."""
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    if g.shape != a.shape[:2]:
        import cv2
        g = cv2.resize(g, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA)
    L = _ramp(np.clip(g, 0, 1), ramp) * amount
    out = 255 - (255 - a) * (255 - L) / 255
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
