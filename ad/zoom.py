# -*- coding: utf-8 -*-
"""좌표 확대 — Claude 가 «보면서» 픽셀 좌표로 구역을 불러 원본에서 크게 떼어 본다.

근거: anthropics/claude-cookbooks `multimodal/crop_tool.ipynb`(차트 읽기 정답률 29% → 73%).
Claude 는 그림을 28x28 픽셀 칸 단위로 보고, 한도를 넘는 그림은 줄여서 본다. 그래서 작은 글자·붙은 선은
지시로는 안 읽힌다. 셋을 지킨다:
1. 보는 판(view)은 Claude 가 «실제로 볼 크기»로 우리가 먼저 줄인다 → Claude 가 말하는 좌표가 판과 1:1.
2. 확대는 «원본»에서 자른다(벡터면 그 구역만 다시 그린다) → 줄인 판을 키우는 게 아니다.
3. 자른 구역은 한도 안에서 가장 크게 키워 돌려준다. 확대한 그림에서 또 확대할 수 있다(옆 json 이 원본 좌표를 들고 다닌다).
좌표는 0~1 비율이 아니라 픽셀(쿡북이 비율 좌표를 권하지 않는다). 기존 `forge zoom`(고정 격자 4배판)·`ad look --zoom`(비율 한 번)과 다르다.

판마다 옆에 `<이름>.json`: {src, kind: raster|vector, page, box: 원본 단위(px 또는 PDF pt) [x0,y0,x1,y1], w, h, parent}.
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

TIERS = {'std': (1568, 1568), 'high': (2576, 4784)}   # (긴 변 한도, 그림 토큰 한도) — 쿡북 기재값
RASTER = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff')
VECTOR = ('.pdf', '.ai', '.svg')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # SusannaDesigner
DEFAULT_OUT = os.path.join(HERE, 'runs', 'zoom')                     # 🔴 손님 원본 폴더에 쓰지 않는다


def tokens(w, h):
    """그림 토큰: 28x28 칸 하나에 하나."""
    return math.ceil(w / 28) * math.ceil(h / 28)


def resized_size(w, h, tier='std'):
    """Claude 가 줄여서 볼 크기(쿡북 resized_size 그대로). 이미 한도 안이면 그대로."""
    edge, budget = TIERS[tier]

    def fits(a, b):
        return math.ceil(a / 28) * 28 <= edge and math.ceil(b / 28) * 28 <= edge and tokens(a, b) <= budget

    if fits(w, h):
        return w, h
    if h > w:
        rh, rw = resized_size(h, w, tier)
        return rw, rh
    ar = w / h
    lo, hi = 1, w
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if fits(mid, max(round(mid / ar), 1)):
            lo = mid
        else:
            hi = mid
    return lo, max(round(lo / ar), 1)


def fill_size(w, h, tier='std'):
    """같은 비율로 한도 안에서 가장 큰 크기(확대판 목표)."""
    return resized_size(max(1, round(w * 10_000)), max(1, round(h * 10_000)), tier)   # PDF pt 는 소수라 정수로


def _kind(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in RASTER:
        return 'raster'
    if ext in VECTOR:
        return 'vector'
    raise SystemExit(f'모르는 형식: {ext} (그림 {RASTER} · 벡터 {VECTOR})')


def _vpage(src, page):
    import fitz
    ext = os.path.splitext(src)[1].lower()
    doc = fitz.open('pdf', fitz.open(src).convert_to_pdf()) if ext == '.svg' else fitz.open(src, filetype='pdf')
    if not 0 <= page < doc.page_count:
        raise SystemExit(f'쪽 {page} 없음 (0~{doc.page_count - 1})')
    return doc[page]


def _render(meta, size):
    """meta 의 box(원본 단위)를 size 크기로 그린다. 그림은 원본에서 잘라 키우고, 벡터는 그 구역만 다시 그린다."""
    x0, y0, x1, y1 = meta['box']
    if meta['kind'] == 'raster':
        im = Image.open(meta['src'])
        if im.mode != 'RGB':                                        # 투명은 흰 바탕에(그냥 RGB 로 바꾸면 검게 된다)
            rgba = im.convert('RGBA'); bg = Image.new('RGB', rgba.size, 'white'); bg.paste(rgba, mask=rgba.getchannel('A')); im = bg
        return im.crop((round(x0), round(y0), round(x1), round(y1))).resize(size, Image.LANCZOS)
    import fitz
    pg = _vpage(meta['src'], meta.get('page', 0))
    clip = fitz.Rect(x0, y0, x1, y1)
    pix = pg.get_pixmap(matrix=fitz.Matrix(size[0] / clip.width, size[1] / clip.height), clip=clip, alpha=False)
    im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    return im if im.size == tuple(size) else im.resize(size, Image.LANCZOS)


def _save(im, meta, path):
    if path.lower().endswith('.png'):
        im.save(path)
    else:
        im.save(path, quality=92, subsampling=0)                    # 4:2:0 이면 1~2px 색선이 번진다
    meta = dict(meta, w=im.width, h=im.height)
    with open(os.path.splitext(path)[0] + '.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    return meta


def _grid(im, step):
    """같은 크기 사본에 옅은 격자와 좌표 숫자. 좌표는 판과 같다."""
    g = im.copy().convert('RGB'); d = ImageDraw.Draw(g, 'RGBA')
    try:
        font = ImageFont.truetype('arial.ttf', 12)
    except OSError:
        font = ImageFont.load_default()
    for x in range(step, g.width, step):
        d.line([(x, 0), (x, g.height)], fill=(255, 0, 255, 90), width=1); d.text((x + 2, 2), str(x), fill=(255, 0, 255, 230), font=font)
    for y in range(step, g.height, step):
        d.line([(0, y), (g.width, y)], fill=(255, 0, 255, 90), width=1); d.text((2, y + 2), str(y), fill=(255, 0, 255, 230), font=font)
    return g


def view(src, out=None, tier='std', page=0, grid=0):
    """보는 판을 만든다. 돌려주는 것: (판 경로, meta)."""
    src = os.path.abspath(src); kind = _kind(src)
    if kind == 'raster':
        W, H = Image.open(src).size
        box = [0, 0, W, H]; size = resized_size(W, H, tier)
    else:
        r = _vpage(src, page).rect
        box = [r.x0, r.y0, r.x1, r.y1]; size = fill_size(r.width, r.height, tier)
    stem = os.path.splitext(os.path.basename(src))[0] + (f'_p{page}' if kind == 'vector' and page else '')
    out = os.path.normpath(out or os.path.join(DEFAULT_OUT, stem))
    os.makedirs(out, exist_ok=True)
    meta = {'src': src, 'kind': kind, 'page': page, 'box': box, 'tier': tier, 'parent': None}
    im = _render(meta, size)
    path = os.path.join(out, stem + '_view.png')
    meta = _save(im, meta, path)
    if grid:
        gp = os.path.join(out, stem + '_view_grid.png'); _grid(im, grid).save(gp)
        meta['grid_path'] = gp
    return path, meta


def _meta_of(img):
    side = os.path.splitext(img)[0] + '.json'
    if os.path.exists(side):
        return json.load(open(side, encoding='utf-8'))
    w, h = Image.open(img).size                                     # 옆 json 이 없으면 그 그림 자체가 원본
    if resized_size(w, h) != (w, h):
        raise SystemExit(f'{os.path.basename(img)} 는 {w}x{h} 라 Claude 가 줄여 본다 — 먼저 `ad zoom {img}` 로 보는 판을 만든다')
    return {'src': os.path.abspath(img), 'kind': 'raster', 'page': 0, 'box': [0, 0, w, h], 'w': w, 'h': h, 'tier': 'std', 'parent': None}


def zoom(img, x1, y1, x2, y2, out=None, tier=None):
    """img(보는 판 또는 앞선 확대판)의 픽셀 좌표 구역을 원본에서 떼어 키운다. 돌려주는 것: (확대판 경로, meta, 알림 글)."""
    pm = _meta_of(img)
    w, h = pm['w'], pm['h']
    x1, x2 = max(0, min(x1, w)), max(0, min(x2, w)); y1, y2 = max(0, min(y1, h)), max(0, min(y2, h))
    if x1 >= x2 or y1 >= y2:
        raise SystemExit(f'구역이 틀렸다: x1<x2, y1<y2 이고 판 {w}x{h} 안이어야 한다')
    bx0, by0, bx1, by1 = pm['box']
    sx, sy = (bx1 - bx0) / w, (by1 - by0) / h
    box = [bx0 + x1 * sx, by0 + y1 * sy, bx0 + x2 * sx, by0 + y2 * sy]
    tier = tier or pm.get('tier', 'std')
    bw, bh = box[2] - box[0], box[3] - box[1]
    size = fill_size(bw, bh, tier)
    meta = {'src': pm['src'], 'kind': pm['kind'], 'page': pm.get('page', 0), 'box': box, 'tier': tier, 'parent': os.path.abspath(img),
            'from': [x1, y1, x2, y2]}
    out = out or os.path.dirname(os.path.abspath(img))
    os.makedirs(out, exist_ok=True)
    base = os.path.splitext(os.path.basename(pm['src']))[0]
    n = 1
    while os.path.exists(os.path.join(out, f'{base}_z{n}.jpg')):
        n += 1
    path = os.path.join(out, f'{base}_z{n}.jpg')
    meta = _save(_render(meta, size), meta, path)
    unit = 'px' if meta['kind'] == 'raster' else 'pt'
    mag = meta['w'] / bw if meta['kind'] == 'raster' else meta['w'] / (bw / 72 * 25.4)
    note = (f'({x1},{y1})-({x2},{y2}) of {os.path.basename(img)} {w}x{h} → 원본 {unit} '
            f'[{box[0]:.1f},{box[1]:.1f},{box[2]:.1f},{box[3]:.1f}] ({bw:.1f}x{bh:.1f}{unit}) → {meta["w"]}x{meta["h"]}px'
            + (f' (원본 화소의 {mag:.1f}배' + ('' if mag <= 6 else ', 원본보다 세부가 늘지는 않는다') + ')' if meta['kind'] == 'raster'
               else f' ({mag:.1f}px/mm, 벡터를 다시 그림)'))
    return path, meta, note
