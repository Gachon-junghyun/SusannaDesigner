# -*- coding: utf-8 -*-
"""까치발 철문자(T9) 로고 시안 세트 — 45° 원근 시뮬레이션 + 까치발 자동 배치 (aidesigner 공용, 2026-09-27).

  python sim/standoff_sheet.py <spec.json>

spec.json 은 이 파일 맨 아래 `SPEC_EXAMPLE` 모양이다(상호·색·이격·봉 규칙·안 목록). 안(variant)의 SVG 는
«평평한 한 색 로고»(maker_up.py 로 올리는 것과 같은 모양)면 된다. 첫 실측: runs/2026-09-27_고객A네일/11_sheet/spec.json.


sign-proof 의 sheet.jsx 는 «가로 바탕판 + 조명 채널» 틀이라 세로 로고·45° 시뮬레이션이 안 들어가서,
파이썬으로 짠다(같은 브랜드 토큰: 청록 #00A79D 머리띠 · 도면 격자 · 고운바탕).
정면 = 실측 치수, 45° = 벽을 45° 돌려 본 원근(벽 평면 + 이격 + 철판 두께 + 벽 그림자).
이격·두께는 수산나 메이커 T9 기본값(config/maker.ts: 이격 80mm · 두께 5mm) — 🔴 실측 전 «가정».
"""
import io, json, math, os, sys, time
import cv2, fitz, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get('FONTAI_CODE', os.path.join(os.path.expanduser('~'), 'font-ai', 'code')))
from letter_svg import fab_check  # noqa: E402
sys.path.insert(0, os.path.dirname(HERE))
from ad.measure import pin_layout  # noqa: E402

FONT_B = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Windows', 'Fonts', 'GowunBatang-Bold.ttf')
FONT_R = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Windows', 'Fonts', 'GowunBatang-Regular.ttf')
SANS = r'C:\Windows\Fonts\malgun.ttf'
SANS_B = r'C:\Windows\Fonts\malgunbd.ttf'
F = lambda p, s: ImageFont.truetype(p, s)

BRAND, BRAND7, BRAND1, INK, ACC = '#00A79D', '#00726C', '#CFF0ED', '#0F1A19', '#FF5900'
# ↓ 기본값 — spec.json 이 덮어쓴다(load_spec)
FACE = (139, 79, 74)          # 도장색
WALL = (242, 220, 213)        # 벽(시안용 — 실제 벽 색은 현장)
STANDOFF, THICK = 80.0, 5.0   # mm — 수산나 메이커 T9 기본값(config/maker.ts, 가정)
SHOP_KO, SHOP_EN, STEM, FACE_NAME, DATE = '가게', 'SHOP', '시안', '도장색', ''
LASER_MIN, BEND_MIN, HOLE_MIN, SPECK = 3.0, 38.0, 30.0, 400.0
# 까치발(스페이서 봉) — 🔴 공장 기준을 못 봤다. 전부 «가정»이고 시트에도 그렇게 적는다 (2026-09-27 사람 승인)
PIN_D, PIN_MIN, PIN_GAP, PIN_SMALL, PIN_EDGE = 10.0, 2, 300.0, 80.0, 3.0   # 지름·조각당 최소·간격·작은 조각(1개)·획 가장자리 여유(mm)
PIN_COLOR = (150, 154, 156)
VARIANTS = []



def load_spec(path):
    """spec.json → 전역 값. 상대 경로(svg·out)는 spec 파일 폴더 기준."""
    global FACE, WALL, STANDOFF, THICK, SHOP_KO, SHOP_EN, STEM, FACE_NAME, DATE, VARIANTS
    global PIN_D, PIN_MIN, PIN_GAP, PIN_SMALL, PIN_EDGE
    sp = json.load(io.open(path, encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(path))
    hx = lambda h: tuple(int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    SHOP_KO, SHOP_EN = sp['shop_ko'], sp.get('shop_en', '')
    STEM = sp.get('stem', SHOP_KO.replace(' ', ''))
    FACE, FACE_NAME = hx(sp.get('face', '#8b4f4a')), sp.get('face_name', '도장색')
    WALL = hx(sp.get('wall', '#f2dcd5'))
    STANDOFF, THICK = float(sp.get('standoff_mm', 80)), float(sp.get('thick_mm', 5))
    pin = sp.get('pin', {})
    PIN_D, PIN_MIN, PIN_GAP = float(pin.get('d', PIN_D)), int(pin.get('min', PIN_MIN)), float(pin.get('gap', PIN_GAP))
    PIN_SMALL, PIN_EDGE = float(pin.get('small', PIN_SMALL)), float(pin.get('edge', PIN_EDGE))
    DATE = sp.get('date', time.strftime('%Y-%m-%d'))
    VARIANTS = [(v['tag'], v.get('key', v['tag']), os.path.join(base, v['svg']), float(v.get('w_mm', 1500)), v['desc'], v.get('cat', True))
                for v in sp['variants']]
    out = os.path.join(base, sp.get('out', '.'))
    os.makedirs(out, exist_ok=True)
    return out


def mask_of(svg_path, px_w):
    """SVG → 잉크 마스크(잉크 상자로 자름). 가로 px_w 픽셀."""
    s = open(svg_path, encoding='utf-8').read()
    s = s.replace('<svg ', '<svg ', 1)
    pg = fitz.open('svg', s.encode())[0]
    z = px_w * 1.25 / pg.rect.width
    pm = pg.get_pixmap(matrix=fitz.Matrix(z, z), alpha=True)
    a = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, pm.n)[..., 3]
    ys, xs = np.where(a > 127)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h = int(round(a.shape[0] * px_w / a.shape[1]))
    return cv2.resize(a, (px_w, h), interpolation=cv2.INTER_AREA)


def measure(svg_path, w_mm):
    m = mask_of(svg_path, 3000)
    h_mm = w_mm * m.shape[0] / m.shape[1]
    r = fab_check(m > 127, text_h_mm=h_mm)
    return dict(w=w_mm, h=h_mm, **r)


def brackets(svg_path, w_mm, ppm=2.0):
    """조각마다 까치발 자리 — 규칙 본체는 ad.measure.pin_layout 하나(검사기·3D 미리보기와 같은 자)."""
    m = mask_of(svg_path, int(w_mm * ppm)) > 127
    pins, pieces, narrow = pin_layout(m, ppm, d_mm=PIN_D, edge_mm=PIN_EDGE, per_min=PIN_MIN, gap_mm=PIN_GAP, small_mm=PIN_SMALL)
    return pins, pieces, narrow, m


# ---------------------------------------------------------------- 렌더
def wall_texture(W, H, s):
    rng = np.random.default_rng(7)
    base = np.ones((H, W, 3), np.float32) * np.array(WALL, np.float32)
    noise = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 1.2) * 3.0
    grad = np.linspace(1.03, 0.94, H, dtype=np.float32)[:, None]            # 위가 조금 밝다(낮 하늘빛)
    base = base * grad[..., None] + noise[..., None]
    return np.clip(base, 0, 255)


def layers(svg_path, w_mm, s, margin=(800, 600)):
    """벽 좌표(mm) 위의 층들 — 벽(그림자 포함) · 옆면 마스크 · 앞면 마스크. s = px/mm."""
    m = mask_of(svg_path, int(w_mm * s)) / 255.0
    lh, lw = m.shape
    W, H = lw + int(2 * margin[0] * s), lh + int(2 * margin[1] * s)
    ox, oy = (W - lw) // 2, int((H - lh) * 0.45)
    full = np.zeros((H, W), np.float32); full[oy:oy + lh, ox:ox + lw] = m
    wall = wall_texture(W, H, s)
    # 벽 그림자: 빛이 왼쪽 위에서 — 이격만큼 오른쪽 아래로 밀리고 번진다
    dx, dy = STANDOFF * 0.45 * s, STANDOFF * 0.75 * s
    sh = cv2.warpAffine(full, np.float32([[1, 0, dx], [0, 1, dy]]), (W, H))
    sh = cv2.GaussianBlur(sh, (0, 0), 14 * s)
    wall = wall * (1 - 0.30 * sh[..., None])
    return wall, full, (W, H), (ox, oy, lw, lh)


def to_rgba(color, alpha):
    img = np.zeros(alpha.shape + (4,), np.float32)
    img[..., :3] = color
    img[..., 3] = alpha
    return img


def project(pts_mm, z, th, f, zc, u0, v0):
    out = []
    for x, y in pts_mm:
        X = x * math.cos(th) + z * math.sin(th)
        depth = zc + x * math.sin(th) - z * math.cos(th)
        out.append((f * X / depth + u0, f * y / depth + v0))
    return np.float32(out)


def over(canvas, rgba):
    a = rgba[..., 3:4]
    canvas[:] = canvas * (1 - a) + rgba[..., :3] * a


def render_45(svg_path, w_mm, pins=(), deg=45, s=1.0, out_w=4200):
    wall, full, (W, H), (ox, oy, lw, lh) = layers(svg_path, w_mm, s)
    th = math.radians(deg)
    corners_px = [(0, 0), (W, 0), (W, H), (0, H)]
    to_mm = lambda p: ((p[0] - W / 2) / s, (p[1] - H / 2) / s)
    corners_mm = [to_mm(p) for p in corners_px]
    zc = max(W, H) / s * 1.35
    # 화면 크기 맞추기 — 벽 네 모서리를 투영해 가로 out_w 에 맞춘다
    probe = project(corners_mm, 0, th, 1.0, zc, 0, 0)
    f = out_w * 0.92 / (probe[:, 0].max() - probe[:, 0].min())
    p0 = project(corners_mm, 0, th, f, zc, 0, 0)
    pad = 40
    u0, v0 = -p0[:, 0].min() + pad, -p0[:, 1].min() + pad
    out_h = int(p0[:, 1].max() - p0[:, 1].min() + 2 * pad)
    canvas = np.ones((out_h, out_w, 3), np.float32) * np.array((233, 233, 230), np.float32)
    src = np.float32(corners_px)

    def warp(img_rgba, z):
        dst = project(corners_mm, z, th, f, zc, u0, v0)
        M = cv2.getPerspectiveTransform(src, dst)
        return cv2.warpPerspective(img_rgba, M, (out_w, out_h), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))

    over(canvas, warp(np.dstack([wall, np.ones((H, W), np.float32)]), 0))
    if pins:                                                  # 까치발 봉 — 벽(z=0)에서 판 뒤(z=이격)까지 원판을 쌓는다
        pm = np.zeros((H, W), np.float32)
        for q in pins:
            cv2.circle(pm, (int(round(ox + q['x'] * s)), int(round(oy + q['y'] * s))), max(1, int(round(PIN_D / 2 * s))), 1.0, -1, cv2.LINE_AA)
        steps = 24
        for i in range(steps + 1):
            shade = 0.72 + 0.28 * i / steps                   # 벽 쪽이 조금 어둡다
            over(canvas, warp(to_rgba(tuple(c * shade for c in PIN_COLOR), pm), STANDOFF * i / steps))
    side = tuple(c * 0.62 for c in FACE)
    n = 8
    for i in range(n + 1):                                   # 옆면(철판 두께) — 이격 위에서 앞면까지
        z = STANDOFF + THICK * i / n
        over(canvas, warp(to_rgba(side, full), z))
    face = to_rgba(FACE, full)
    face[..., :3] *= 1.02
    fw = warp(face, STANDOFF + THICK)
    over(canvas, fw)
    # 로고 둘레만 잘라 «45° 에서 찍은 사진»처럼 — 벽 전체를 보이면 로고가 작아진다
    ys, xs = np.where(fw[..., 3] > 0.5)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    mx, my = int((x1 - x0) * 0.35), int((y1 - y0) * 0.45)
    crop = canvas[max(0, y0 - my):y1 + my, max(0, x0 - mx):x1 + mx]
    return Image.fromarray(np.clip(crop, 0, 255).astype(np.uint8))


def render_front(svg_path, w_mm, s=0.6):
    wall, full, (W, H), (ox, oy, lw, lh) = layers(svg_path, w_mm, s, margin=(450, 380))
    canvas = wall.copy()
    over(canvas, to_rgba(FACE, full))
    img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    f = F(SANS_B, 24)
    col = (60, 60, 60)
    # 가로 치수
    y = oy - 40
    d.line([(ox, y), (ox + lw, y)], fill=col, width=2)
    for x in (ox, ox + lw):
        d.line([(x, y - 12), (x, y + 12)], fill=col, width=2)
    t = f'{w_mm:,.0f}mm'
    tw = d.textlength(t, font=f)
    d.rectangle([ox + lw / 2 - tw / 2 - 8, y - 16, ox + lw / 2 + tw / 2 + 8, y + 16], fill=tuple(WALL))
    d.text((ox + lw / 2 - tw / 2, y - 15), t, fill=col, font=f)
    # 세로 치수
    x = ox + lw + 40
    d.line([(x, oy), (x, oy + lh)], fill=col, width=2)
    for yy in (oy, oy + lh):
        d.line([(x - 12, yy), (x + 12, yy)], fill=col, width=2)
    h_mm = w_mm * lh / lw
    d.text((x + 14, oy + lh / 2 - 14), f'{h_mm:,.0f}mm', fill=col, font=f)
    return img


# ---------------------------------------------------------------- 판정
def verdict(r, cat=True):
    notes, level = [], '제작 가능'
    st, hole, sp = r['stroke_mm'], r['min_hole_mm'], r['specks']
    if st < LASER_MIN:
        level = '불가'
        notes.append(f'가장 가는 곳 {st:.1f}mm — 레이저 최소 {LASER_MIN:.0f}mm 미만. 선을 굵히거나 크기를 키워야 합니다.')
    if hole is not None and hole < HOLE_MIN:
        level = '조건부' if level != '불가' else level
        notes.append((f'가장 좁은 빈 틈 {hole:.0f}mm — 심벌 안의 흰 선(오려 낸 틈)입니다. 레이저로 따는 틈이라 만들 수 있지만 멀리서는 흐려집니다. 12mm 로 넓히면 풀립니다.') if cat else f'글자 속 빈 공간 {hole:.0f}mm — 30mm 보다 좁아 멀리서 메워져 보일 수 있습니다.')
    if sp:
        level = '조건부' if level != '불가' else level
        notes.append(f'가로세로 20mm 미만 조각 {sp}개 — 따로 까치발을 박기 어려워 부제만 시트(스티커)로 대체합니다.')
    return level, notes


# ---------------------------------------------------------------- 시트
A3 = (2480, 1754)   # 150dpi 가로


def head(img, right):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, A3[0], 150], fill=BRAND)
    for x in range(0, A3[0], 50):
        d.line([(x, 0), (x, 150)], fill=(0, 190, 178), width=1)
    for y in range(0, 150, 50):
        d.line([(0, y), (A3[0], y)], fill=(0, 190, 178), width=1)
    d.text((110, 48), 'SUSANNA DESIGN', fill='white', font=F(SANS_B, 44))
    tw = d.textlength(right, font=F(SANS_B, 30))
    d.text((A3[0] - 110 - tw, 60), right, fill='white', font=F(SANS_B, 30))


NOTICE = [
    '· «시안»이며 제작 원본이 아닙니다. 제작 데이터는 현장 실측 후 칼선을 다시 뽑습니다.',
    '· 45° 그림은 원근 «표현»입니다 — 이격 80mm·철판 두께 5mm·까치발 지름 10mm·배치 규칙은 가정이며 공장·현장 실측 후 확정합니다.',
    '· 심벌·레터링 초안은 생성형 AI(제미나이)로 뽑아 사람이 고르고 다듬었습니다. 무점등(까치발 철문자)이라 야간 점등 컷은 없습니다.',
    '· 최종 치수·색·위치는 현장 실측 후 확정되며, 옥외광고물 표시는 관할 구청 신고 대상입니다. 납품 전 상표 검색(KIPRIS)을 합니다.',
]


def foot(img, y=1560):
    d = ImageDraw.Draw(img)
    d.line([(110, y), (A3[0] - 110, y)], fill=(200, 200, 200), width=2)
    for i, t in enumerate(NOTICE):
        d.text((110, y + 20 + i * 34), t, fill=(90, 90, 90), font=F(SANS, 22))
    t = '(주) 수산나디자인 · 010-0000-0000 · susannadesign.co.kr'
    tw = d.textlength(t, font=F(SANS, 22))
    d.text((A3[0] - 110 - tw, y + 20 + 3 * 34), t, fill=(90, 90, 90), font=F(SANS, 22))


def fit(im, box):
    im = im.copy(); im.thumbnail(box, Image.LANCZOS); return im


def page_variant(tag, name, desc, r, lv, notes, sim, front, date):
    img = Image.new('RGB', A3, 'white'); d = ImageDraw.Draw(img)
    head(img, f'{SHOP_EN} · {SHOP_KO}  ·  시안 {tag}안  ·  {date}')
    d.text((110, 190), f'{tag}안', fill=INK, font=F(FONT_B, 72))
    d.text((260, 214), desc, fill=(80, 80, 80), font=F(SANS, 30))
    s = fit(sim, (1460, 1060)); img.paste(s, (110, 300))
    d.text((110, 300 + s.height + 10), '45° 원근 시뮬레이션 — 벽을 45° 돌려 본 모습 · 벽에서 80mm 띄운 5mm 철판(가정) · 낮', fill=(110, 110, 110), font=F(SANS, 22))
    fr = fit(front, (760, 520)); img.paste(fr, (1610, 300))
    d.text((1610, 300 + fr.height + 10), '정면 · 실측 치수', fill=(110, 110, 110), font=F(SANS, 22))
    # 사양·판정 표
    y = 300 + fr.height + 70
    rows = [
        ('간판 종류', 'T9 까치발 철문자 (무점등 · 철판 레이저 절단 · 도장)'),
        ('크기', f'가로 {r["w"]:,.0f} × 세로 {r["h"]:,.0f}mm'),
        ('색', f'{FACE_NAME} 도장 (#%02X%02X%02X) · 벽은 현장' % FACE),
        ('최소 획', f'{r["stroke_mm"]:.1f}mm  (레이저 최소 {LASER_MIN:.0f}mm)'),
        ('최소 속공간', '없음' if r['min_hole_mm'] is None else f'{r["min_hole_mm"]:.0f}mm  (기준 {HOLE_MIN:.0f}mm)'),
        ('절곡(38mm)', '해당 없음 — 레이저 절단 철판' + ('' if r['stroke_mm'] >= BEND_MIN else ' (채널이면 불가)')),
        ('까치발', f'{r["pins"]}개 · 지름 {PIN_D:.0f}mm · 이격 {STANDOFF:.0f}mm (가정) — 다음 쪽 배치도'),
    ]
    d.rectangle([1610, y - 10, A3[0] - 110, y + 46], fill=BRAND1)
    d.text((1625, y), '사양 · 제작 판정', fill=BRAND7, font=F(SANS_B, 28))
    y += 62
    for k, v in rows:
        d.text((1625, y), k, fill=(90, 90, 90), font=F(SANS_B, 24))
        d.text((1800, y), v, fill=INK, font=F(SANS, 24))
        y += 40
        d.line([(1610, y - 6), (A3[0] - 110, y - 6)], fill=(225, 225, 225), width=1)
    col = BRAND7 if lv == '제작 가능' else ('#9A6A00' if lv == '조건부' else ACC)
    d.text((1625, y + 10), f'판정: {lv}', fill=col, font=F(SANS_B, 32))
    yy = y + 60
    for n in notes or ['그대로 제작할 수 있습니다.']:
        for line in wrap(d, '대안 · ' + n, F(SANS, 22), A3[0] - 110 - 1625):
            d.text((1625, yy), line, fill=(70, 70, 70), font=F(SANS, 22)); yy += 32
    foot(img)
    return img


def page_brackets(tag, r, pins, pieces, narrow, m, date):
    img = Image.new('RGB', A3, 'white'); d = ImageDraw.Draw(img)
    head(img, f'{SHOP_EN} · {SHOP_KO}  ·  시안 {tag}안 까치발 배치도  ·  {date}')
    d.text((110, 190), f'{tag}안 까치발 배치도', fill=INK, font=F(FONT_B, 60))
    d.text((640, 212), '벽을 마주 본 정면(좌우 뒤집지 않음). 점 = 스페이서 봉 자리.', fill=(80, 80, 80), font=F(SANS, 28))
    H0, W0 = m.shape
    k = min(1500 / W0, 1150 / H0)
    gx, gy = 110, 300
    fill = np.full((H0, W0, 3), 255, np.uint8)
    fill[m] = (236, 206, 200)
    edge = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    fill[edge] = FACE
    im = Image.fromarray(fill).resize((int(W0 * k), int(H0 * k)), Image.LANCZOS)
    img.paste(im, (gx, gy)); d = ImageDraw.Draw(img)
    ppm = W0 / r['w']
    fs = F(SANS_B, 16)
    for i, q in enumerate(pins, 1):
        x, y = gx + q['x'] * ppm * k, gy + q['y'] * ppm * k
        rr = max(7, PIN_D / 2 * ppm * k)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=ACC if q['narrow'] else INK)
        d.text((x + rr + 2, y - rr - 4), str(i), fill=(60, 60, 60), font=fs)
    yl = gy + im.height + 30
    d.line([(gx, yl), (gx + im.width, yl)], fill=(60, 60, 60), width=2)
    d.text((gx + im.width / 2 - 60, yl + 8), f'{r["w"]:,.0f}mm', fill=(60, 60, 60), font=F(SANS_B, 24))
    x2, y = 1700, 320
    d.rectangle([x2 - 15, y - 10, A3[0] - 110, y + 46], fill=BRAND1)
    d.text((x2, y), '까치발 (자동 배치)', fill=BRAND7, font=F(SANS_B, 28)); y += 70
    rows = [('조각', f'{pieces}조각'), ('까치발', f'{len(pins)}개'), ('봉', f'지름 {PIN_D:.0f}mm · 이격 {STANDOFF:.0f}mm (가정)'),
            ('규칙', f'조각당 최소 {PIN_MIN}개 · {PIN_GAP:.0f}mm마다 1개'), ('', f'긴 변 {PIN_SMALL:.0f}mm 미만 조각은 1개 (가정)'),
            ('좁은 조각', f'{narrow}조각' if narrow else '없음')]
    for a, b in rows:
        d.text((x2, y), a, fill=(90, 90, 90), font=F(SANS_B, 24)); d.text((x2 + 150, y), b, fill=INK, font=F(SANS, 24)); y += 42
    y += 20
    msg = ['봉은 획이 «봉 지름 + 여유 3mm» 이상 두꺼운 곳에만 놓았습니다. 가장 두꺼운 곳부터, 이미 놓은 자리에서 가장 먼 곳을 차례로 골라 한쪽에 몰리지 않게 했습니다.',
           ('주황 점은 획이 좁아 봉이 다 들어가지 않는 조각입니다 — 봉을 가늘게 하거나 그 조각만 붙임(접착)으로 바꿉니다.' if narrow else '모든 조각에 봉 자리가 들어갑니다.'),
           '1:1 타공 본(SVG)과 구멍 좌표(CSV, 로고 왼쪽 위 기준 mm)를 같이 드립니다. 벽에 대고 뚫기 전에 현장에서 한 번 더 맞춥니다.']
    for t in msg:
        for line in wrap(d, '· ' + t, F(SANS, 22), A3[0] - 110 - x2):
            d.text((x2, y), line, fill=(70, 70, 70), font=F(SANS, 22)); y += 32
        y += 8
    foot(img)
    return img


def template_files(tag, svg_path, r, pins, out):
    import re
    src = open(svg_path, encoding='utf-8').read()
    d_all = ''.join(re.findall(r'<path[^>]* d="([^"]+)"', src))
    num = r'-?\d+\.?\d*'
    v = [float(x) for x in re.findall(num, d_all)]
    x0, y0, iw = min(v[0::2]), min(v[1::2]), max(v[0::2]) - min(v[0::2])
    kk = r['w'] / iw
    c = iter(range(10 ** 9))
    dd = re.sub(num, lambda mm: '%.2f' % (((float(mm.group(0)) - x0) * kk) if next(c) % 2 == 0 else ((float(mm.group(0)) - y0) * kk)), d_all)
    W, H = r['w'], r['h']
    holes = ''
    for i, q in enumerate(pins, 1):
        holes += (f'<circle cx="{q["x"]:.1f}" cy="{q["y"]:.1f}" r="{PIN_D / 2:.1f}" fill="none" stroke="#ff5900" stroke-width="0.8"/>'
                  f'<path d="M{q["x"] - 8:.1f},{q["y"]:.1f}H{q["x"] + 8:.1f}M{q["x"]:.1f},{q["y"] - 8:.1f}V{q["y"] + 8:.1f}" stroke="#ff5900" stroke-width="0.5"/>'
                  f'<text x="{q["x"] + 9:.1f}" y="{q["y"] - 7:.1f}" font-size="9" fill="#ff5900">{i}</text>')
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.1f}mm" height="{H:.1f}mm" viewBox="0 0 {W:.1f} {H:.1f}">'
           f'<path d="{dd}" fill="none" stroke="#1b1d1c" stroke-width="0.6" fill-rule="evenodd"/>{holes}</svg>')
    open(os.path.join(out, f'타공본_{tag}_1대1.svg'), 'w', encoding='utf-8').write(svg)
    with open(os.path.join(out, f'타공좌표_{tag}.csv'), 'w', encoding='utf-8-sig') as fcsv:
        fcsv.write('번호,조각,x_mm(왼쪽에서),y_mm(위에서),좁음\n')
        for i, q in enumerate(pins, 1):
            fcsv.write(f'{i},{q["piece"]},{q["x"]:.1f},{q["y"]:.1f},{"예" if q["narrow"] else ""}\n')


def wrap(d, text, font, width):
    out, cur = [], ''
    for ch in text:
        if d.textlength(cur + ch, font=font) > width:
            out.append(cur); cur = ch
        else:
            cur += ch
    return out + ([cur] if cur else [])


def main():
    out = load_spec(sys.argv[1]); date = DATE
    rows = []
    for tag, key, p, w, desc, cat in VARIANTS:
        r = measure(p, w)
        pins, npieces, narrow, pm_ = brackets(p, w)
        r['pins'] = len(pins)
        lv, notes = verdict(r, cat=cat)
        if narrow:
            lv = '조건부' if lv == '제작 가능' else lv
            notes.append(f'획이 좁아 까치발 봉(지름 {PIN_D:.0f}mm)이 다 들어가지 않는 조각 {narrow}개 — 봉을 가늘게 하거나 그 조각만 붙임으로.')
        sim = render_45(p, w, pins)
        front = render_front(p, w)
        sim.save(os.path.join(out, f'sim45_{tag}.png')); front.save(os.path.join(out, f'front_{tag}.png'))
        page_variant(tag, key, desc, r, lv, notes, sim, front, date).save(os.path.join(out, f'{STEM}_시안_{tag}.png'))
        page_brackets(tag, r, pins, npieces, narrow, pm_, date).save(os.path.join(out, f'{STEM}_시안_{tag}_까치발.png'))
        template_files(tag, p, r, pins, out)
        rows.append(dict(tag=tag, desc=desc, lv=lv, narrow=narrow, **{k: r[k] for k in ('w', 'h', 'stroke_mm', 'min_hole_mm', 'pieces', 'specks', 'pins')}))
        print(tag, lv, '획 %.1f' % r['stroke_mm'], '조각', npieces, '까치발', len(pins), '좁음', narrow)
    # 표지
    img = Image.new('RGB', A3, 'white'); d = ImageDraw.Draw(img)
    head(img, f'간판 디자인 시안 · {date}')
    d.text((110, 240), SHOP_KO, fill=INK, font=F(FONT_B, 120))
    d.text((115, 400), f'{SHOP_EN}  ·  로고 + 까치발 철문자 시안 {len(VARIANTS)}안', fill=(80, 80, 80), font=F(SANS, 40))
    d.text((115, 470), f'간판 종류 T9 까치발 철문자(무점등)  ·  로고 가로 {VARIANTS[0][3] / 1000:g}m 기준  ·  현장: 실측 전', fill=(110, 110, 110), font=F(SANS, 28))
    x = 110
    for tag, *_ in VARIANTS:
        t = fit(Image.open(os.path.join(out, f'front_{tag}.png')), (430, 430))
        img.paste(t, (x, 620)); d.text((x, 620 + t.height + 12), f'{tag}안', fill=INK, font=F(FONT_B, 40)); x += 460
    foot(img)
    img.save(os.path.join(out, f'{STEM}_시안_cover.png'))
    # 비교 — 45° 를 3×2 로
    img = Image.new('RGB', A3, 'white'); d = ImageDraw.Draw(img)
    head(img, f'{SHOP_EN} · {SHOP_KO}  ·  전체 비교')
    d.text((110, 180), f'{len(VARIANTS)}안 비교', fill=INK, font=F(FONT_B, 56))
    d.text((520, 202), '같은 벽 · 같은 색 · 같은 45° 시점에서 봅니다. 다른 것은 로고뿐입니다.', fill=(80, 80, 80), font=F(SANS, 28))
    cw, ch = 740, 610
    for i, rw in enumerate(rows):
        cx, cy = 110 + (i % 3) * (cw + 30), 280 + (i // 3) * (ch + 40)
        t = fit(Image.open(os.path.join(out, f'sim45_{rw["tag"]}.png')), (cw, ch - 90))
        img.paste(t, (cx, cy))
        col = BRAND7 if rw['lv'] == '제작 가능' else ('#9A6A00' if rw['lv'] == '조건부' else ACC)
        d.text((cx, cy + t.height + 8), f'{rw["tag"]}안', fill=INK, font=F(FONT_B, 34))
        d.text((cx + 90, cy + t.height + 14), rw['lv'], fill=col, font=F(SANS_B, 26))
        d.text((cx + 250, cy + t.height + 16), f'최소 획 {rw["stroke_mm"]:.1f}mm · 까치발 {rw["pins"]}개', fill=(90, 90, 90), font=F(SANS, 22))
    foot(img)
    img.save(os.path.join(out, f'{STEM}_시안_compare.png'))
    # PDF 한 벌
    pages = ['cover'] + [x for v in VARIANTS for x in (v[0], v[0] + '_까치발')] + ['compare']
    ims = [Image.open(os.path.join(out, f'{STEM}_시안_{p}.png')).convert('RGB') for p in pages]
    ims[0].save(os.path.join(out, f'{STEM}_시안.pdf'), save_all=True, append_images=ims[1:], resolution=150)
    json.dump(rows, io.open(os.path.join(out, 'report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('끝', out)


if __name__ == '__main__':
    main()


SPEC_EXAMPLE = {
    "shop_ko": "고객A 네일", "shop_en": "CLIENTA NAIL", "stem": "고객A네일", "date": "2026-09-27",
    "face": "#8b4f4a", "face_name": "로즈브라운", "wall": "#f2dcd5",
    "standoff_mm": 80, "thick_mm": 5,
    "pin": {"d": 10, "min": 2, "gap": 300, "small": 80, "edge": 3},
    "out": ".",
    "variants": [{"tag": "A", "svg": "../9_silhouette/고객A네일_실루엣_영문.svg", "w_mm": 1500, "desc": "잠든 고양이 + 영문", "cat": True}],
}
