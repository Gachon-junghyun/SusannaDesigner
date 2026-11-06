"""고객B 간판 4안 — 전부 벡터 PDF(1:10, 580mm 폭). 일러로 열어 CS6 .ai 로 굽는 건 save_cs6.py."""
import os, fitz
from PIL import Image

BASE = os.path.join(os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent')), 'users', os.environ.get('DEGAJA_USER', 'user'), 'domains', 'susanna', '시안', '2026-10_부대찌개')
OUT = os.path.join(BASE, r'sim1011\ai'); os.makedirs(OUT, exist_ok=True)
src = fitz.open(os.path.join(BASE, r'src\1011\고객B시안.ai'))[0]
DR = src.get_drawings()
R, L, K, O = '#A8232A', '#F3E9D2', '#1E1E1E', '#E8803E'
hx = lambda c: '#%02X%02X%02X' % tuple(round(v * 255) for v in c[:3]) if c else None
rgb = lambda h: tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))

BAND = fitz.Rect(205.0, 212.7, 944.3, 250.9)            # 대표님 AI 의 띠 = 5800 x 300 mm
MM = 5800 / BAND.width                                   # 원본 1pt = 몇 mm
K10 = (580 / 25.4 * 72) / BAND.width                     # 1:10 배율 (원본 pt → 결과 pt)
MARGIN = 20 / 25.4 * 72                                  # 대지 여백 20mm(1:10 도면 위)
TOP_Y, BOT_Y = 182.0, 282.0                              # 로고가 띠 위아래로 걸치는 범위
X0 = 200.0
PAGE_W = (948 - X0) * K10 + 2 * MARGIN
PAGE_H = (BOT_Y - TOP_Y) * K10 + 2 * MARGIN


def to_page(p): return fitz.Point((p.x - X0) * K10 + MARGIN, (p.y - TOP_Y) * K10 + MARGIN)


def draw(sh, items, tf):
    for it in items:
        if it[0] == 'l': sh.draw_line(tf(it[1]), tf(it[2]))
        elif it[0] == 'c': sh.draw_bezier(tf(it[1]), tf(it[2]), tf(it[3]), tf(it[4]))
        elif it[0] == 're':
            r = it[1]; sh.draw_quad(fitz.Quad(tf(r.tl), tf(r.tr), tf(r.bl), tf(r.br)))
        elif it[0] == 'qu':
            q = it[1]; sh.draw_quad(fitz.Quad(tf(q.ul), tf(q.ur), tf(q.ll), tf(q.lr)))


def finish(sh, d, nf, ns, scale):
    sh.finish(fill=rgb(nf) if nf else None, color=rgb(ns) if ns else None,
              width=(d.get('width') or 0) * scale, even_odd=d.get('even_odd', False),
              closePath=d.get('closePath', False))


def build(sub, logo):
    MAP = {'#B3121A': R, '#A91D24': R, '#595757': K, '#EA5515': sub, '#F6EED8': L}

    def m(h):
        if h is None: return None
        r, g, b = rgb(h)
        if max(r, g, b) < 60 / 255 or min(r, g, b) > 240 / 255: return K
        return MAP.get(h, h)
    doc = fitz.open(); pg = doc.new_page(width=PAGE_W, height=PAGE_H); sh = pg.new_shape()
    dy_box = (BAND.y0 + BAND.y1) / 2 - (326.0 + 364.2) / 2
    for d in DR:
        rc = d['rect']; f, st = hx(d.get('fill')), hx(d.get('color'))
        if '#E71D1B' in (f, st): continue                      # 치수선·화살표
        if st == '#FFFFFF' and f is None and rc.x1 < 301: continue   # 옛 로고 옆 흰 테 조각(먹으로 바뀌면 보임)
        is_logo = rc.x0 > 210 and rc.x1 < 300
        dy = 0.0
        if is_logo and rc.y0 > 290:                            # 아래 줄 세로현판 → 위 띠로
            if logo != 'box': continue
            dy = dy_box
        elif rc.y0 > 290 or rc.y1 < 180 or is_logo: continue
        if rc.x0 > 800 and rc.y0 > 200: nf, ns = L, None       # 전화번호·지점
        else: nf, ns = m(f), m(st)
        draw(sh, d['items'], lambda p, dy=dy: to_page(fitz.Point(p.x, p.y + dy)))
        finish(sh, d, nf, ns, K10)
    if logo == 'disc':                                         # 원판 1A — SVG 를 PDF 로 바꿔 그리기 단위로 다시 그림
        dsvg = open(os.path.join(BASE, r'circle\원판2_1A.svg'), encoding='utf-8').read()
        dp = fitz.open(stream=dsvg.encode('utf-8'), filetype='svg')
        dp = fitz.open('pdf', dp.convert_to_pdf())[0]
        S = dp.rect.width                                      # 5400 단위 캔버스, 원판 지름은 2*2444
        d_pt = BAND.height * 700 / 300                         # 원판 지름 700mm
        canvas = d_pt * S / (2 * 2444 * S / 5400)
        cx = 296 - d_pt / 2; cy = (BAND.y0 + BAND.y1) / 2
        k = canvas / S
        tf = lambda p: to_page(fitz.Point(cx + (p.x - S / 2) * k, cy + (p.y - S / 2) * k))
        for d in dp.get_drawings():
            draw(sh, d['items'], tf); finish(sh, d, hx(d.get('fill')), hx(d.get('color')), K10 * k)
    sh.commit()
    return doc


JOBS = [('고객B_1_원판_3색', L, 'disc'), ('고객B_2_네모_3색', L, 'box'),
        ('고객B_3_원판_4색', O, 'disc'), ('고객B_4_네모_4색', O, 'box')]
for name, sub, logo in JOBS:
    doc = build(sub, logo)
    doc.set_metadata({'title': name + ' (1:10, 실제 5800x300mm 띠)', 'creator': 'Susanna Design'})
    p = os.path.join(OUT, name + '.pdf'); doc.save(p)
    pix = doc[0].get_pixmap(dpi=200); pix.save(os.path.join(OUT, name + '_preview.png'))
    print(name, round(PAGE_W / 72 * 25.4, 1), 'x', round(PAGE_H / 72 * 25.4, 1), 'mm', len(doc[0].get_drawings()))
