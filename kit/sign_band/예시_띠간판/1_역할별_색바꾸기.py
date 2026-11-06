import fitz, os
from PIL import Image, ImageDraw, ImageFont
os.chdir(os.path.join(os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent')), 'users', os.environ.get('DEGAJA_USER', 'user'), 'domains', 'susanna', '시안', '2026-10_부대찌개', 'src', '1011'))
src = fitz.open('고객B시안.ai')[0]
DR = src.get_drawings()
R, L, K = '#A8232A', '#F3E9D2', '#1E1E1E'
RM = '#9E3B37'   # 빨강 채도 낮춤 (A8232A 채도 0.79 -> 약 0.65, 살짝 따뜻하게)
X = [('크림', '#F3E9D2'), ('오프화이트', '#F7F4EE'), ('웜그레이', '#CFC8BD'), ('쿨그레이', '#C6CACE'), ('살구', '#EFC3A4')]
hx = lambda c: '#%02X%02X%02X' % tuple(round(v * 255) for v in c[:3]) if c else None
rgb = lambda h: tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def role(h):
    if h is None: return None
    if h == '#E71D1B': return 'guide'
    if h == '#A91D24': return 'logo_red'
    if h == '#B3121A': return 'title1'
    if h == '#EA5515': return 'top_sub'
    if h == '#181C62': return 'bot_sub'
    if h == '#595757': return 'top_band'
    if h == '#FFE200': return 'bot_band'
    if h == '#F6EED8': return 'cream'
    r, g, b = rgb(h)
    if max(r, g, b) < 60 / 255: return 'ink'
    if min(r, g, b) > 240 / 255: return 'white'
    return 'other'


def build(m, phone):
    doc = fitz.open(); pg = doc.new_page(width=src.rect.width, height=src.rect.height)
    sh = pg.new_shape()
    for d in DR:
        f, s = hx(d.get('fill')), hx(d.get('color'))
        rf, rs = role(f), role(s)
        if 'guide' in (rf, rs): continue
        r = d['rect']
        if r.x0 > 800 and r.y0 > 200:                       # 전화번호·지점 글자
            nf, ns = phone, None
        else:
            nf = m.get(rf, f) if f else None; ns = m.get(rs, s) if s else None
        for it in d['items']:
            if it[0] == 'l': sh.draw_line(it[1], it[2])
            elif it[0] == 'c': sh.draw_bezier(it[1], it[2], it[3], it[4])
            elif it[0] == 're': sh.draw_rect(it[1])
            elif it[0] == 'qu': sh.draw_quad(it[1])
        sh.finish(fill=rgb(nf) if nf else None, color=rgb(ns) if ns else None, width=d.get('width') or 0,
                  even_odd=d.get('even_odd', False), closePath=d.get('closePath', False),
                  lineJoin=d.get('lineJoin', 0) if isinstance(d.get('lineJoin'), (int, float)) else 0,
                  lineCap=max(d.get('lineCap') or (0,)) if isinstance(d.get('lineCap'), tuple) else 0)
    sh.commit(); return doc


def render(doc, clip, z=4):
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(z, z), clip=fitz.Rect(*clip))
    return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)


TOP, BOT = (200, 182, 948, 280), (200, 296, 948, 392)
font = ImageFont.truetype(r'C:\Windows\Fonts\malgunbd.ttf', 46)


def sheet(opts, out):
    tiles = []
    for i, (name, m, x) in enumerate(opts):
        doc = build(m, x); doc.save(out + f'_{i+1}.pdf'); t, b = render(doc, TOP), render(doc, BOT)
        used = sorted(set(m.values()))
        W = t.width; im = Image.new('RGB', (W, 90 + t.height + 30 + b.height + 40), 'white'); dr = ImageDraw.Draw(im)
        dr.text((20, 20), name, fill='black', font=font); xx = W - 120 * len(used) - 20
        for c in used: dr.rectangle((xx, 22, xx + 90, 72), fill=c, outline='#999'); xx += 120
        im.paste(t, (0, 90)); im.paste(b, (0, 90 + t.height + 30)); tiles.append(im); im.save(out + f'_{i+1}.png')
    W = max(t.width for t in tiles); sh = Image.new('RGB', (W, sum(t.height for t in tiles) + 10 * len(tiles)), '#ccc'); y = 0
    for t in tiles: sh.paste(t, (0, y)); y += t.height + 10
    sh.save(out + '.png'); sh.resize((W // 2, sh.height // 2)).save(out + '_small.jpg', quality=88)


# 요청 1: 먹 띠 + 낮춘 빨강(삼겹살·로고) + 부대찌개 색 다섯. 로고 밝은 칸도 같은 색(3색), 글자 바깥 테두리는 먹
opts = []
for i, (n, x) in enumerate(X):
    m = dict(top_band=K, bot_band=K, title1=RM, top_sub=x, bot_sub=x, white=K, cream=x, logo_red=RM, ink=K)
    opts.append((f'{i+1}  먹 띠 · 빨강 {RM} · {n} {x}', m, x))
sheet(opts, '고객B_먹띠_5색')

# 요청 2: 4번(먹 띠 · 크림 글자 · 빨강은 로고만) 바깥 테두리 먹 — 로고 빨강은 원래 값 / 낮춘 값
opts = []
for i, rr in enumerate((R, RM)):
    m = dict(top_band=K, bot_band=K, title1=L, top_sub=L, bot_sub=L, white=K, cream=L, logo_red=rr, ink=K)
    opts.append((f'4-{i+1}  먹 띠 · 크림 글자 · 테두리 먹 · 로고 빨강 {rr}', m, L))
sheet(opts, '고객B_4번_테두리먹')
print('ok')
