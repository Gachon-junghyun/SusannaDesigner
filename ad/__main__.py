# -*- coding: utf-8 -*-
"""python -m ad <명령> … — 잔손질 CLI. 명령마다 한 가지만 한다(한 번에 한 가지 — 작업분해 7)."""
import argparse
import io
import json
import os
import shutil
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from . import check, clean, deliver, draw, finish, layout, measure, refs, relogo, render, score, svgio, unmark, vecc, zoom

FONTAI = os.environ.get('FONTAI_CODE', os.path.join(os.path.expanduser('~'), 'font-ai', 'code'))
INK_NAMES = ['brush1', 'brush2', 'brush3', 'retro1', 'retro3']   # letter_svg.LAYERS 의 «먹» 이름 — 이 이름이어야 먹 층으로 가른다


def cmd_vec(a):
    """그림 → 평평한 SVG. 🔴 keep_text 는 끈다(두 줄 부제가 사라짐 — 09-27) · 흰 배경 사각형은 뺀다 · 2배로 키워 가는 선을 살린다."""
    sys.path.insert(0, FONTAI)
    import letter_svg as L
    from PIL import Image
    if not a.keep_text:
        L.keep_text = lambda g: g
    os.makedirs(a.out, exist_ok=True)
    pngs = list(a.png)
    for i in range(0, len(pngs), len(INK_NAMES)):
        tmp = tempfile.mkdtemp(prefix='ad_vec_')
        batch = dict(zip(INK_NAMES, pngs[i:i + len(INK_NAMES)]))
        for nm, src in batch.items():
            im = Image.open(src).convert('L')
            if a.up > 1:
                im = im.resize((im.width * a.up, im.height * a.up), Image.BICUBIC)
            im.save(os.path.join(tmp, nm + '.png'))
        rows = {r['name']: r for r in L.run(tmp, text_h_mm=a.letter_h)}
        for nm, src in batch.items():
            layers, vb = svgio.read(os.path.join(tmp, 'svg', nm + '.svg'))
            layers = clean.strip_bg(layers, vb)
            color = a.color or layers[0][1]
            dst = os.path.join(a.out, os.path.splitext(os.path.basename(src))[0] + '.svg')
            svgio.write(dst, [(d, color) for d, _ in layers], vb[2], vb[3], x0=vb[0], y0=vb[1])
            r = rows.get(nm, {})
            print(f'{os.path.basename(dst)}  IoU {r.get("iou")}  극점누락 {r.get("missing_extrema")}  조각 {r.get("pieces")}')
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_check(a):
    res = check.run(a.svg, a.w_mm, raster=a.raster, pin_d=a.pin, pin_edge=a.pin_edge, letters=a.letters)
    w = check.show(res)
    sys.exit(0 if w != 'no' else 1)


def cmd_measure(a):
    d = svgio.joined(a.svg)
    print(json.dumps(measure.report(d, a.w_mm, pin=dict(d_mm=a.pin)), ensure_ascii=False, default=float))


def cmd_clean(a):
    lay = clean.per_color(a.svg, a.w_mm, thicken_mm=a.thicken, min_speck_mm2=a.specks, merge=not a.no_merge)
    lay, w, h = svgio.crop(lay)
    svgio.write(a.out, lay, w, h, mm=True)
    print(f'→ {a.out}  ({w:,.0f} × {h:,.0f}mm, 층 {len(lay)})')


def _write_like(src, d, out):
    layers, _ = svgio.read(src)
    color = layers[0][1] if layers else '#000'
    lay, w, h = svgio.crop([(d, color)], pad=0)
    svgio.write(out, lay, w, h)
    print(f'→ {out}')


def cmd_respace(a):
    layers, vb = svgio.read(a.svg)
    d = ''.join(x for x, _ in clean.strip_bg(layers, vb))
    counts = [int(c) for c in a.counts.split(',')]
    nd = layout.respace_line(d, counts[0], a.scale, a.track) if len(counts) == 1 else layout.respace(d, counts, a.scale, a.track, a.sub_track)
    _write_like(a.svg, nd, a.out)


def cmd_squash(a):
    _write_like(a.svg, layout.squash(svgio.joined(a.svg), a.sx, a.sy), a.out)


def cmd_stack(a):
    lay, w, h = layout.stack(svgio.joined(a.symbol), svgio.joined(a.text), a.sym_w, a.text_w, a.gap, color=a.color, pad=a.pad)
    svgio.write(a.out, lay, w, h, mm=True)
    print(f'→ {a.out}  ({w:,.0f} × {h:,.0f}mm)')


def cmd_preview3d(a):
    out, n = render.preview3d(a.svg, a.w_mm, a.out, deg=a.deg, face=a.face, wall=a.wall, standoff=a.standoff, thick=a.thick, pin_d=a.pin)
    print(f'→ {out}  (까치발 {n}개, 지름 {a.pin:g}mm 가정)')


def cmd_gradient(a):
    for f in render.gradient(a.svg, a.w_mm, a.out, a.c1, a.c2, bands=a.bands, vertical=not a.horizontal):
        print('→', f)
    print('🔴 채널 간판은 면 하나가 한 색 — 진짜 그라데이션은 출력 시트·LED 로만. 톤 띠는 되지만 조각이 늡니다(로고.md).')


def cmd_split(a):
    for f in render.split(a.svg, a.by, a.out, n=a.n, w_mm=a.w_mm):
        print('→', f)


def cmd_sheet(a):
    import runpy
    sys.argv = ['standoff_sheet.py', a.spec]
    runpy.run_path(os.path.join(render.ROOT, 'sim', 'standoff_sheet.py'), run_name='__main__')


def _styles(given, allowed):
    return list(allowed) if given == 'all' else given.split(',')


def cmd_flatfx(a):
    """평면 기법(벡터) — 한 색 면·바탕 흐름·톤 쌓기·반투명 겹침·롱섀도·테·그려 넣은 광택. ad/finish.py 머리말."""
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(a.svg))[0]
    for st in _styles(a.style, finish.FLAT_STYLES):
        print(finish.flatfx(a.svg, st, os.path.join(a.out, f'{stem}_{st}.png'), color=a.color, bg=a.bg))


def cmd_render3d(a):
    """Blender 입체(Cycles) — 크롬·먹색 광택·유리·전면 발광·후광·발광 흐름. 한 장에 수 초~십수 초."""
    os.makedirs(a.out, exist_ok=True)
    stem = os.path.splitext(os.path.basename(a.svg))[0]
    for st in _styles(a.style, finish.RENDER_STYLES):
        print(finish.render3d(a.svg, st, os.path.join(a.out, f'{stem}_3d_{st}.png'), samples=a.samples, size=a.size, degaja=a.degaja))


def cmd_refs(a):
    """레퍼런스 창고(비공개) — 디자인 나무 개념마다 참고 그림 + 프롬프트 조각. 자세한 건 ad/refs.py 머리말"""
    if a.do == 'scaffold':
        made, stale = refs.scaffold()
        print(f'새 개념 폴더 {made}개 · 나무에서 사라진 폴더 {len(stale)}개')
        for k in stale:
            print('  ⚠ 나무에 없는 폴더(지우지 말고 옮길 곳을 정하라):', k)
    elif a.do == 'list':
        for key, n, files, has_p in refs.listing():
            if a.key and not key.startswith(a.key):
                continue
            print(f'{key:<34} 레퍼런스 {n:>2} · 그림 {files:>2} · 프롬프트 {"있음" if has_p else "—"}')
    elif a.do == 'prompt':
        text, rs = refs.prompt(a.key)
        print('프롬프트 조각:', text or '(아직 없음 — REFS.md 의 «프롬프트:» 줄을 채워라)')
        for r in rs:
            print(f'  참고 {r["file"]}  [{r["own"]}]  {r["why"]}')
        if rs:
            print('🔴 남의 것은 --ref 로 «닮게» 뽑지 말고 결만 말로 옮겨라(STAGES 3). 우리 것만 --ref 로 붙인다.')
    elif a.do == 'add':
        if not a.image or a.own not in ('우리 것', '남의 것'):
            raise SystemExit('add 에는 그림 경로와 --own «우리 것»|«남의 것» 이 필요하다')
        print('넣음:', refs.add(a.key, a.image, a.src or '', a.own, a.why or ''))


def cmd_draw(a):
    """한 획 마커 레터링 → 중심선 stroke 로고 + 그리기 애니메이션 — 본체는 ad/draw.py"""
    draw.run(a.png, a.out, weight=a.weight, sy=a.sy, sx=a.sx, draw_s=a.draw_s, cycle_s=a.cycle, tsx=a.tsx)


def cmd_vecc(a):
    """여러 색 로고 → 색마다 층 SVG(일러 시안) — 본체는 ad/vecc.py"""
    vecc.run(a.png, a.out, up=a.up, k=a.k, inks=a.inks, eps=a.eps, pad=a.pad, engine=a.engine, alphamax=a.alphamax, snap=not a.no_snap)


def cmd_upscale(a):
    """작은 원본 → 4배(Real-ESRGAN). 제미나이 --ref 로 주기 전에"""
    print(deliver.upscale(a.png, a.out, a.model), '→', a.out)


def cmd_look(a):
    """크게 그려 보기 — 🔴 1024 로 보면 오돌토돌이 안 보인다"""
    for o in deliver.look(a.path, a.out, a.px, a.zoom):
        print('→', o)


def cmd_zoom(a):
    """좌표 확대 — 좌표 없이 부르면 «보는 판»(Claude 가 볼 크기), 좌표를 주면 그 판의 픽셀 구역을 원본에서 떼어 키운다"""
    if not a.box:
        path, m = zoom.view(a.path, a.out, a.tier or 'std', a.page, a.grid)
        unit = 'px' if m['kind'] == 'raster' else 'pt'
        b = m['box']
        print(f"보는 판 {path}  {m['w']}x{m['h']}px (좌표는 이 판 기준, 왼쪽 위 0,0, x 오른쪽 · y 아래)")
        print(f"  원본 {m['kind']} {b[2] - b[0]:.0f}x{b[3] - b[1]:.0f}{unit} · 그림 토큰 {zoom.tokens(m['w'], m['h'])}")
        if m.get('grid_path'):
            print(f"  격자 사본 {m['grid_path']}")
        print(f"  다음: python -m ad zoom \"{path}\" x1 y1 x2 y2")
        return
    if len(a.box) != 4:
        raise SystemExit('좌표는 넷: x1 y1 x2 y2')
    path, m, note = zoom.zoom(a.path, *a.box, out=a.out, tier=a.tier)
    print(f'확대판 {path}')
    print('  ' + note)


def cmd_strip(a):
    """원본과 후보를 한 줄로"""
    print(deliver.strip(a.paths, a.out, a.h), '→', a.out)


def cmd_export(a):
    """SVG → .pdf · .png · .ai(일러로 진짜 저장) [· 폰]"""
    made, bad = deliver.export(a.svg, ai=not a.no_ai, pdf=True, png=True, px=a.px, phone=a.phone, caption=a.caption)
    for m in made:
        print('→', m)
    for p_, e in bad:
        print('🔴 폰 전송 실패', os.path.basename(p_), e)
    sys.exit(1 if bad else 0)


def cmd_unmark(a):
    """제미나이 ✦ 표시 지우기 — 오른쪽 아래에서 네 갈래 별을 찾아 그 모양만 메운다. 못 찾으면 안 건드리고 그대로 옮긴다"""
    os.makedirs(a.out, exist_ok=True)
    miss = 0
    for src in a.png:
        stem = os.path.splitext(os.path.basename(src))[0]
        dst = os.path.join(a.out, stem + '.' + a.fmt)
        hit = unmark.run(src, dst, a.min_score)
        miss += hit is None
        print(f'{os.path.basename(dst)}  ' + (f"지움 {hit}" if hit else '⚠ 못 찾음 — 그대로 옮김(눈으로 확인)'))
    sys.exit(1 if miss else 0)


def cmd_redraw(a):
    """원안 → ChatGPT·제미나이가 «그대로 깨끗하게» 다시 그린 원본 크기 PNG (--blunt 면 선 끝만 둥근 마감)"""
    made = relogo.redraw(a.ref, a.out, change=a.change, blunt=a.blunt, engines=a.engines.split(','), name=a.name)
    sys.exit(0 if made else 1)


def cmd_retrace(a):
    """깨끗한 그림 → 매끈한 SVG(무리별 그라디언트). --ai 면 일러 파일까지"""
    rep = relogo.retrace(a.png, a.out, up=not a.no_up, names=a.names.split(',') if a.names else None,
                         blur=a.blur, optol=a.optol, alphamax=a.alphamax)
    print(json.dumps(rep, ensure_ascii=False, default=int))
    if a.ai:
        print('→', deliver.to_ai(a.out, os.path.splitext(a.out)[0] + '.ai') or os.path.splitext(a.out)[0] + '.ai')


def cmd_fabcheck(a):
    """실제 크기(mm)에서 가장 가는 곳·선 끝 두께 + 걸린 자리 표시"""
    print(json.dumps(relogo.fabcheck(a.path, a.h, min_mm=a.min, out_png=a.out), ensure_ascii=False))


def cmd_swap(a):
    """SVG 의 한 무리만 새 레터링으로"""
    print(json.dumps(relogo.swap(a.svg, a.group, a.png, a.out, fit=a.fit), ensure_ascii=False))


def cmd_board(a):
    """여러 SVG → 한 .ai(대지 여럿) · 외곽선 · PDF"""
    labels = a.labels.split('|') if a.labels else [os.path.splitext(os.path.basename(x))[0] for x in a.svgs]
    print(json.dumps(relogo.board(a.svgs, labels, a.out, w_mm=a.w_mm, cols=a.cols), ensure_ascii=False))


def cmd_straighten(a):
    """.ai 선만 보기에서 «두 줄로 꺾인» 곧은 획 테두리 → 직선 한 줄(새 .ai + PDF)"""
    print(json.dumps(relogo.straighten(a.ai, a.out, groups=a.groups.split(','), offboard=a.offboard,
                                       corners=not a.no_corners, humps=a.humps), ensure_ascii=False))


def cmd_cutfile(a):
    """시안 .ai → 재단선 .ai(그라디언트 네모·대지 밖 사본 없이 외곽선만)"""
    print(json.dumps(relogo.cutfile(a.ai, a.out, stroke_pt=a.stroke, min_mm=a.min_mm), ensure_ascii=False))


def cmd_score(a):
    """벡터 후보 채점(결투의 같은 자) — 원본과 닮음·잔물결·꼭짓점·티끌·노드 [+ 시공 mm]"""
    rows = score.score(a.ref, a.cands, h_mm=a.h, min_mm=a.min, strip=a.strip)
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))


def cmd_picker(a):
    """디자인 고르기 창 — 혼자 시험(MCP 없이). 보낸 것을 JSON 으로 찍는다. 자세한 건 ad/picker.py 머리말"""
    from . import picker
    picker.cli(a.store, a.brief)


def cmd_pgrid(a):
    """포스터 레퍼런스 해부 — 자세한 건 ad/pgrid.py 머리말 · protocols/promo.md §포스터 레퍼런스 해부"""
    from . import pgrid
    if a.do == 'detect':
        out = a.out or os.path.join(os.path.dirname(a.path), os.path.splitext(os.path.basename(a.path))[0])
        doc = pgrid.detect(a.path, out, crop=a.crop, src=a.src or '', own=a.own)
        print(f"{out}  판 {doc['W']}x{doc['H']} 잘라냄 {doc['crop']}  글줄 {sum(i['kind'] == 'text' for i in doc['items'])}  그림 {sum(i['kind'] == 'image' for i in doc['items'])}")
        print('→ detect.png 를 눈으로 보고 blocks.json 을 고친 뒤: python -m ad pgrid analyze', out)
    elif a.do == 'fix':
        doc = pgrid.fix(a.path, a.spec[0] if a.spec else '{}')
        print(f"{a.path}  상자 {len(doc['items'])} → fixed.png 로 다시 본다")
    elif a.do == 'analyze':
        r = pgrid.analyze(a.path, cols=a.cols, gutter=a.gutter, rows=a.rows)
        c = r['columns']
        print(f"단 {c['n'] if c else '-'} ({c['hit'] if c else 0}/{c['of'] if c else 0})  글 단계 {len(r['type_levels'])}  그림 {len(r['images'])}  → {a.path}/grid.png · REPORT.md")
    elif a.do == 'summary':
        print(pgrid.summary(a.path))
    else:
        from . import pdata, playout
        if a.do == 'tag':
            print(json.dumps(pdata.tag(a.path, a.spec), ensure_ascii=False))
        elif a.do == 'table':
            print('표 · 상자 줄 수', pdata.table(), '→', os.path.join(pdata.ROOT, 'table.csv'))
        elif a.do == 'types':
            T = pdata.types()
            for k, t in T.items():
                print(k, t.get('name', ''), len(t['members']), '장  제목', t['stats'].get('head', {}).get('med'), '%H')
        elif a.do == 'check':
            spec = a.spec[0] if a.spec else None
            r = pdata.check(a.path, out=a.out, spec=spec, crop=a.crop if a.crop != 'auto' else 'none')
            print('가까운 유형', [(k, round(d, 2)) for d, k in r['nearest']], '→', os.path.join(r['out'], 'CHECK.md'))
        elif a.do == 'pick':
            print(pdata.pick(a.path, a.result, type_=a.type or '', who=a.who, job=a.job or '', note=a.note or ''))
        elif a.do == 'picks':
            print(pdata.picks_summary(as_text=True))
        elif a.do == 'embed':
            print('지문', pdata.embed(), '장')
        elif a.do == 'similar':
            for s_ in pdata.similar(a.path, k=a.k):
                print(f"{s_['score']:.3f}  {s_['id']}  {s_['title']}  유형 {s_['type']}")
        elif a.do == 'picker':
            print('고르기 창 모음', pdata.picker_items(), '장')
        elif a.do == 'layout':
            c = {'title': a.title or '', 'sub': a.sub or '', 'date': a.date or '', 'place': a.place or '', 'brand': a.brand or '',
                 'info': a.info or [], 'photo': a.photo, 'photo2': a.photo2, 'accent': a.accent}
            keys = 'ABCDEFGHI' if a.path in ('all', '전부') else a.path.upper()
            out = a.out or '.'
            for k in keys:
                print(playout.layout(k, c, out))


def cmd_fluted(a):
    """골유리 굴절 — ad/fluted.py 머리말 · techniques/골유리_굴절.md"""
    from PIL import Image
    from . import fluted
    o = fluted.fluted(Image.open(a.img), strip=a.strip, squeeze=a.squeeze, seam=a.seam, blur=a.blur, gray=a.gray, phase=a.phase, soften=a.soften)
    o.save(a.out)
    print('→', a.out, o.size)


def cmd_liquid(a):
    """액체 크롬 덮개 + 역광 — ad/liquid.py 머리말 · techniques/액체_크롬_반사.md · techniques/역광_후광.md"""
    from PIL import Image
    from . import liquid as L
    W, H = (int(x) for x in a.size.split('x'))
    ss = 2
    if a.img:
        base = Image.open(a.img).convert('RGB').resize((W * ss, H * ss), Image.LANCZOS); g = None
    elif a.glow:
        base, g = L.glow_poster(a.text.split('|'), a.font, W * ss, H * ss, rays=a.rays, bloom=a.bloom, ray_len=a.ray_len)
    else:
        base, g = L.poster(a.text.split('|'), a.font, W * ss, H * ss), None
    o = L.overlay(base, seed=a.seed, refract=a.refract, f0=a.f0, film=a.film, ss=ss,
                  ramp=L.RAMP_TEALCHROME if a.glow else L.RAMP_BRAND)
    if g is not None:
        o = L.screen_light(o, g, a.light)
    o.save(a.out)
    print('→', a.out, o.size)


def main():
    p = argparse.ArgumentParser(prog='python -m ad', description='AI 디자이너 잔손질 — 한 명령에 한 가지')
    sp = p.add_subparsers(dest='cmd', required=True)
    s = sp.add_parser('vec', help='그림 → 평평한 SVG'); s.add_argument('png', nargs='+'); s.add_argument('--out', default='.'); s.add_argument('--up', type=int, default=2)
    s.add_argument('--letter-h', type=float, default=400); s.add_argument('--keep-text', action='store_true', help='글자 띠 밖 덩이 지우기(간판 «사진» 레터링일 때만)'); s.add_argument('--color'); s.set_defaults(f=cmd_vec)
    s = sp.add_parser('vecc', help='여러 색 로고 → 색마다 층 SVG(일러 시안) — 원·직사각형·매끈한 곡선으로'); s.add_argument('png'); s.add_argument('--out', required=True); s.add_argument('--up', type=int, default=2)
    s.add_argument('--k', type=int, default=4, help='자동으로 고를 색 수'); s.add_argument('--inks', help='직접 줄 색, 예) #c8c8c8,#e4a830,#c02424,#18843c')
    s.add_argument('--eps', type=float, default=1.0, help='윤곽 단순화(원본 px) — 크면 더 매끈·덜 충실')
    s.add_argument('--pad', type=float, default=30, help='잉크 둘레 여백(원본 px), 음수면 원래 캔버스')
    s.add_argument('--engine', choices=['own', 'potrace'], default='own', help='윤곽 엔진 — own(각진 로고: 모서리 날카롭게·곧은 변은 직선, 기본) · potrace(둥근 로고: 곡선이 가장 매끈하나 끝이 뭉개짐)')
    s.add_argument('--alphamax', type=float, default=1.0, help='potrace 모서리 기준: 0=전부 각 · 1=기본 · 1.33=전부 곡선')
    s.add_argument('--no-snap', action='store_true', help='원·직사각형으로 펴지 않는다(손글씨·낙서 레터링)'); s.set_defaults(f=cmd_vecc)
    s = sp.add_parser('draw', help='한 획 마커 레터링 → 중심선 로고 + 펜으로 그리는 애니메이션 SVG'); s.add_argument('png'); s.add_argument('--out', required=True)
    s.add_argument('--weight', type=float, default=1.0, help='획 굵기 배수'); s.add_argument('--sy', type=float, default=1.0, help='세로 배율(획은 안 가늘어짐)'); s.add_argument('--sx', type=float, default=1.0)
    s.add_argument('--draw-s', type=float, default=2.4, help='한 번 그리는 데 걸리는 초'); s.add_argument('--cycle', type=float, default=30.0, help='몇 초마다 다시 그리나')
    s.add_argument('--tsx', help='사이트용 React 부품(.tsx) 경로 — 글자색 currentColor · 점 var(--wine)'); s.set_defaults(f=cmd_draw)
    s = sp.add_parser('upscale', help='작은 원본 → 4배(Real-ESRGAN, 로컬)'); s.add_argument('png'); s.add_argument('--out', required=True)
    s.add_argument('--model', default='realesrgan-x4plus', choices=['realesrgan-x4plus', 'realesrgan-x4plus-anime']); s.set_defaults(f=cmd_upscale)
    s = sp.add_parser('look', help='크게 그려 보기(SVG·PDF·AI·PNG) + 확대 칸'); s.add_argument('path'); s.add_argument('--out', required=True)
    s.add_argument('--px', type=int, default=2000); s.add_argument('--zoom', help='확대 칸 x0,y0,x1,y1 (0~1 비율)'); s.set_defaults(f=cmd_look)
    s = sp.add_parser('zoom', help='좌표 확대: 좌표 없으면 보는 판, x1 y1 x2 y2(그 판 픽셀)면 원본에서 떼어 키움 · 확대판에서 또 확대')
    s.add_argument('path', help='원본 그림·PDF·AI·SVG, 또는 앞서 만든 보는 판·확대판'); s.add_argument('box', nargs='*', type=int)
    s.add_argument('--out', help='쓸 폴더(기본: 보는 판은 runs/zoom/<이름>/, 확대판은 받은 판의 폴더)')
    s.add_argument('--tier', choices=['std', 'high'], default=None, help='그림 한도 std(긴 변 1568·1568토큰, 기본) | high(2576·4784)')
    s.add_argument('--page', type=int, default=0, help='PDF 쪽(0부터)'); s.add_argument('--grid', type=int, default=0, help='보는 판에 N px 격자 사본도')
    s.set_defaults(f=cmd_zoom)
    s = sp.add_parser('strip', help='원본과 후보를 한 줄로'); s.add_argument('paths', nargs='+'); s.add_argument('--out', required=True)
    s.add_argument('--h', type=int, default=500); s.set_defaults(f=cmd_strip)
    s = sp.add_parser('export', help='SVG → .pdf·.png·.ai(일러) [+ --phone 텔레그램]'); s.add_argument('svg'); s.add_argument('--px', type=int, default=2000)
    s.add_argument('--no-ai', action='store_true'); s.add_argument('--phone', action='store_true'); s.add_argument('--caption', default=''); s.set_defaults(f=cmd_export)
    s = sp.add_parser('check', help='사람이 짚던 디테일 자동 검사'); s.add_argument('svg'); s.add_argument('--w-mm', type=float, required=True, help='실제 잉크 가로(mm)')
    s.add_argument('--raster', help='벡터화 전 원본 그림(빠진 조각·테두리 닿음 검사)'); s.add_argument('--pin', type=float, default=10.0); s.add_argument('--pin-edge', type=float, default=3.0)
    s.add_argument('--letters', type=int, help='가장 큰 줄의 글자 수(예: 고객A네일 4) — 주면 자간이 고른지도 잰다'); s.set_defaults(f=cmd_check)
    s = sp.add_parser('measure', help='최소 획·속공간·조각·까치발 수'); s.add_argument('svg'); s.add_argument('--w-mm', type=float, required=True); s.add_argument('--pin', type=float, default=10.0); s.set_defaults(f=cmd_measure)
    s = sp.add_parser('clean', help='흰 배경 빼기·겹침 합치기·굵게·잡티 빼기'); s.add_argument('svg'); s.add_argument('--w-mm', type=float, required=True); s.add_argument('--out', required=True)
    s.add_argument('--thicken', type=float, default=0.0, help='획 폭에 더할 mm(음수면 가늘게)'); s.add_argument('--specks', type=float, default=0.0, help='이보다 작은 조각(mm²) 빼기'); s.add_argument('--no-merge', action='store_true'); s.set_defaults(f=cmd_clean)
    s = sp.add_parser('respace', help='글자 작게 + 자간 고르게/넓게'); s.add_argument('svg'); s.add_argument('--counts', required=True, help='줄마다 글자 수, 예) 4  또는  6,10'); s.add_argument('--scale', type=float, default=0.86)
    s.add_argument('--track', type=float, default=0.3, help='윗줄 글자 사이 = 글자 높이 × 이 값'); s.add_argument('--sub-track', type=float, default=1.6); s.add_argument('--out', required=True); s.set_defaults(f=cmd_respace)
    s = sp.add_parser('squash', help='상하(세로)만 줄이기'); s.add_argument('svg'); s.add_argument('--sx', type=float, default=1.0); s.add_argument('--sy', type=float, default=0.8); s.add_argument('--out', required=True); s.set_defaults(f=cmd_squash)
    s = sp.add_parser('stack', help='심벌 위 + 글자 아래 (mm)'); s.add_argument('symbol'); s.add_argument('text'); s.add_argument('--sym-w', type=float, required=True); s.add_argument('--text-w', type=float, required=True)
    s.add_argument('--gap', type=float, default=120); s.add_argument('--color', default='#8b4f4a'); s.add_argument('--pad', type=float, default=0); s.add_argument('--out', required=True); s.set_defaults(f=cmd_stack)
    s = sp.add_parser('preview3d', help='까치발 45° 입체 미리보기'); s.add_argument('svg'); s.add_argument('--w-mm', type=float, required=True); s.add_argument('--out', required=True); s.add_argument('--deg', type=float, default=45)
    s.add_argument('--face', default='#8b4f4a'); s.add_argument('--wall', default='#f2dcd5'); s.add_argument('--standoff', type=float, default=80); s.add_argument('--thick', type=float, default=5); s.add_argument('--pin', type=float, default=10); s.set_defaults(f=cmd_preview3d)
    s = sp.add_parser('gradient', help='그라데이션 미리보기 + 제작 가능한 톤 띠'); s.add_argument('svg'); s.add_argument('--w-mm', type=float, required=True); s.add_argument('--out', required=True, help='파일 앞 이름')
    s.add_argument('--c1', default='#c99089'); s.add_argument('--c2', default='#5e2f2c'); s.add_argument('--bands', type=int, default=0); s.add_argument('--horizontal', action='store_true'); s.set_defaults(f=cmd_gradient)
    s = sp.add_parser('split', help='조각·줄·글자로 분리'); s.add_argument('svg'); s.add_argument('--by', choices=['pieces', 'lines', 'letters'], default='pieces'); s.add_argument('--n', type=int); s.add_argument('--w-mm', type=float)
    s.add_argument('--out', required=True); s.set_defaults(f=cmd_split)
    s = sp.add_parser('sheet', help='까치발 45° 시안 세트'); s.add_argument('spec'); s.set_defaults(f=cmd_sheet)
    s = sp.add_parser('unmark', help='제미나이 ✦ 표시 지우기(오른쪽 아래)'); s.add_argument('png', nargs='+'); s.add_argument('--out', required=True)
    s.add_argument('--fmt', default='jpg', choices=['jpg', 'png']); s.add_argument('--min-score', type=float, default=0.45); s.set_defaults(f=cmd_unmark)
    s = sp.add_parser('refs', help='레퍼런스 창고(비공개) — scaffold · list [키] · prompt 키 · add 키 그림'); s.add_argument('do', choices=['scaffold', 'list', 'prompt', 'add'])
    s.add_argument('key', nargs='?', default=''); s.add_argument('image', nargs='?'); s.add_argument('--src'); s.add_argument('--own', help='우리 것 | 남의 것'); s.add_argument('--why'); s.set_defaults(f=cmd_refs)
    s = sp.add_parser('flatfx', help='평면 기법 한 벌(벡터 → PNG): ' + '·'.join(finish.FLAT_STYLES) + ' | all'); s.add_argument('svg')
    s.add_argument('--style', default='all'); s.add_argument('--out', default='.'); s.add_argument('--color', help='대표색(기본: 가장 넓은 색)'); s.add_argument('--bg'); s.set_defaults(f=cmd_flatfx)
    s = sp.add_parser('render3d', help='Blender 입체 한 장: ' + '·'.join(finish.RENDER_STYLES) + ' | all'); s.add_argument('svg')
    s.add_argument('--style', default='all'); s.add_argument('--out', default='.'); s.add_argument('--samples', type=int, default=128)
    s.add_argument('--size', type=int, help='정사각 한 변(기본: 가로로 긴 로고면 1600×900, 아니면 1024)'); s.add_argument('--degaja', help='DeGaJa_Agent 경로(module_render)'); s.set_defaults(f=cmd_render3d)
    s = sp.add_parser('redraw', help='원안 → AI 두 곳이 그대로 깨끗하게 다시 그림(원본 크기 다운로드)'); s.add_argument('ref'); s.add_argument('--out', required=True)
    s.add_argument('--change', default='', help='바꿀 것·지킬 글자(한글은 음절을 풀어서)'); s.add_argument('--blunt', action='store_true', help='선 끝만 둥근 마감(시공용)')
    s.add_argument('--engines', default='chatgpt,gemini'); s.add_argument('--name', default='redraw'); s.set_defaults(f=cmd_redraw)
    s = sp.add_parser('retrace', help='깨끗한 그림 → 매끈한 SVG(업스케일·티끌/워터마크 제거·potrace·무리별 그라디언트)'); s.add_argument('png'); s.add_argument('--out', required=True)
    s.add_argument('--names', help='가로 띠 이름, 예) emblem,wordmark,beauty'); s.add_argument('--no-up', action='store_true'); s.add_argument('--ai', action='store_true')
    s.add_argument('--blur', type=float, default=2.0); s.add_argument('--optol', type=float, default=0.8); s.add_argument('--alphamax', type=float, default=1.0); s.set_defaults(f=cmd_retrace)
    s = sp.add_parser('fabcheck', help='실제 크기에서 최소 폭·선 끝 두께(mm) + 걸린 자리 빨갛게'); s.add_argument('path'); s.add_argument('--h', type=float, required=True, help='로고 전체 높이 mm')
    s.add_argument('--min', type=float, help='최소 폭 mm(주면 표시)'); s.add_argument('--out', help='표시 PNG'); s.set_defaults(f=cmd_fabcheck)
    s = sp.add_parser('swap', help='SVG 의 한 무리만 새 레터링으로'); s.add_argument('svg'); s.add_argument('png'); s.add_argument('--group', required=True); s.add_argument('--out', required=True)
    s.add_argument('--fit', choices=['width', 'height'], default='width'); s.set_defaults(f=cmd_swap)
    s = sp.add_parser('board', help='여러 SVG → 한 .ai(대지 여럿·이름표) · 외곽선 · PDF'); s.add_argument('svgs', nargs='+'); s.add_argument('--out', required=True, help='확장자 없는 파일 앞 이름')
    s.add_argument('--labels', help='| 로 구분'); s.add_argument('--w-mm', type=float, default=200); s.add_argument('--cols', type=int, default=3); s.set_defaults(f=cmd_board)
    s = sp.add_parser('straighten', help='.ai 곧은 획 테두리 꺾임·층 펴기 + 테두리 사이 모서리의 층·꺾임 → 깨끗한 원호 → 새 .ai·PDF'); s.add_argument('ai'); s.add_argument('--out', required=True)
    s.add_argument('--groups', default='wordmark,beauty', help="대상 그룹 이름(쉼표), '*' 는 대지 위 전부"); s.add_argument('--offboard', action='store_true', help='대지 밖 사본도')
    s.add_argument('--no-corners', action='store_true', help='모서리 정리 끄기'); s.add_argument('--humps', action='store_true', help='모서리 위로 솟은 붓 «혹»까지 펴기')
    s.set_defaults(f=cmd_straighten)
    s = sp.add_parser('cutfile', help='시안 .ai → 재단선 .ai: 그라디언트 네모·대지 밖 사본 빼고 칠 없음 + 검정 선(따낼 때)'); s.add_argument('ai'); s.add_argument('--out', required=True)
    s.add_argument('--stroke', type=float, default=0.25, help='선 굵기 pt'); s.add_argument('--min-mm', type=float, default=0.0, help='이보다 작은 조각은 빼고 알려 줌'); s.set_defaults(f=cmd_cutfile)
    s = sp.add_parser('score', help='벡터 후보 채점(결투용 같은 자): 닮음·잔물결·꼭짓점·티끌·노드'); s.add_argument('ref'); s.add_argument('cands', nargs='+')
    s.add_argument('--h', type=float, help='로고 높이 mm(주면 시공 검사도)'); s.add_argument('--min', type=float); s.add_argument('--strip', help='확대 비교 PNG'); s.set_defaults(f=cmd_score)
    s = sp.add_parser('picker', help='디자인 고르기 창(앱) — 나무에서 그림 보며 고르기, MCP 는 ad/picker_mcp.py'); s.add_argument('--store', default=''); s.add_argument('--brief', default='')
    s.set_defaults(f=cmd_picker)
    s = sp.add_parser('pgrid', help='포스터 레퍼런스 해부: detect 그림 → 상자 초안 · analyze 폴더 → 그리드·글자 사다리·그림 자리 · summary 상위폴더 → 모음표·열지도')
    s.add_argument('do', choices=['detect', 'fix', 'analyze', 'summary', 'tag', 'table', 'types', 'check', 'pick', 'picks', 'embed', 'similar', 'picker', 'layout'])
    s.add_argument('path', nargs='?', default='', help='그림·폴더 / similar: 그림·레퍼런스 이름·영어 낱말 / layout: 유형 A~I 또는 all')
    s.add_argument('spec', nargs='*', help='fix·check: 고칠 것 json(파일 또는 문자열) / tag: type=D mood=대담,차분 …')
    s.add_argument('--result', default='고름', help='pick: 고름 | 안 고름 | 고쳐서 고름'); s.add_argument('--type', help='pick: 유형'); s.add_argument('--who', default='작업자님')
    s.add_argument('--job', help='pick: 건 이름'); s.add_argument('--note'); s.add_argument('-k', type=int, default=5)
    s.add_argument('--title'); s.add_argument('--sub'); s.add_argument('--date'); s.add_argument('--place'); s.add_argument('--brand')
    s.add_argument('--info', action='append', help='layout: 정보 줄(여러 번)'); s.add_argument('--photo'); s.add_argument('--photo2'); s.add_argument('--accent', help='layout: 강조색 #RRGGBB')
    s.add_argument('--out', help='detect: 해부 폴더(기본: 그림 옆 같은 이름)'); s.add_argument('--crop', default='auto', help='auto | none | x0,y0,x1,y1 (목업 사진에서 판만)')
    s.add_argument('--src', help='출처 URL'); s.add_argument('--own', default='남의 것', help='우리 것 | 남의 것')
    s.add_argument('--cols', type=int, help='analyze: 단 수를 사람이 정함(레퍼런스에 그리드가 알려져 있을 때)'); s.add_argument('--gutter', type=float, help='단 사이 px')
    s.add_argument('--rows', type=int); s.set_defaults(f=cmd_pgrid)
    s = sp.add_parser('fluted', help='골유리(세로 골 유리) 굴절: 세로 띠마다 squeeze 배 구간을 눌러 담아 둥근 윤곽이 톱날처럼 끊김')
    s.add_argument('img'); s.add_argument('--out', required=True); s.add_argument('--strip', type=float, default=0.039, help='띠 폭(판 폭 비율, 1 넘으면 px)')
    s.add_argument('--squeeze', type=float, default=2.5); s.add_argument('--seam', type=float, default=0.18); s.add_argument('--blur', type=float, default=0.6, help='굴절 뒤 번짐(크면 띠 경계가 뭉개짐)')
    s.add_argument('--soften', type=float, default=0.0, help='굴절 앞 입력 흐림(띠 안만 부드럽게)')
    s.add_argument('--gray', action='store_true'); s.add_argument('--phase', type=float, default=0.0); s.set_defaults(f=cmd_fluted)
    s = sp.add_parser('liquid', help='액체 크롬 덮개(굴절·반사·흰 테·박막 간섭) + 글자 역광(후광·빛줄기)')
    s.add_argument('--img', help='평면 판 그림(없으면 --text 로 판을 만든다)'); s.add_argument('--text', default='S U|SAN|N A', help='칸 격자, 줄은 |, 빈 칸은 공백')
    s.add_argument('--font'); s.add_argument('--out', required=True); s.add_argument('--size', default='1600x1600')
    s.add_argument('--glow', action='store_true', help='글자 뒤 역광'); s.add_argument('--rays', type=float, default=1.8); s.add_argument('--bloom', type=float, default=0.4)
    s.add_argument('--ray-len', dest='ray_len', type=float, default=0.8); s.add_argument('--light', type=float, default=0.12, help='덮개 위로 다시 비치는 빛')
    s.add_argument('--seed', type=int, default=7); s.add_argument('--refract', type=float, default=0.03); s.add_argument('--f0', type=float, default=0.06)
    s.add_argument('--film', type=int, default=3); s.set_defaults(f=cmd_liquid)
    a = p.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
