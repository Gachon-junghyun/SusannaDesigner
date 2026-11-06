# -*- coding: utf-8 -*-
"""검사(gates). 사람이 잡은 결함은 다음 건부터 검사가 먼저 잡게 여기에 올린다 — LESSONS 한 줄로 끝내지 않는다.

막는 검사(실패하면 파이프라인이 멈춘다)
- text        : 글(txt·md·pdf)에 Claude 기호·금지 표현(RULES/산출물.md §5)·금지 값(예: 보이기용 과장 값 70)이 있나
- files       : 출력 파일 수·그림 크기·용량
- pdf_overlap : PDF 쪽 안 글자끼리 겹침(10-22 시안 2쪽 «삼각형 281 x 237» 이 점선을 가로지른 것 같은 조판 사고)
- cmd         : 독립 숫자 대조 같은 임의 검사 명령(종료코드 0 이어야)
- graded      : 넘기기 전 독립 채점(·원본 대조) 보고서가 «지금 결과물»보다 새것이고 판정이 «고칠 것 있음»이 아닌가(protocols/grade.md)
보는 검사(멈추지 않고 «볼 것» 그림을 만든다)
- zoom        : 렌더마다 칸을 나눠 4배 확대판 한 장(전체 화면에선 안 보이는 결함용)
- diff        : 옵션을 켠 그림과 끈 그림의 차이를 붉게 칠하고 차이 큰 자리를 확대해 붙인다
                (10-22 원형 마감 형상 깎기가 만든 마름모 앞면 선을 «반사겠지»로 넘겼다 — 켠 것과 끈 것을 나란히 봤으면 바로 보였다)
"""
import glob
import os
import re

SYMS = r'[«»·•—–―※☆▸▶►→←↔⇒➜✓✔✅❌⚠\U0001F300-\U0001FAFF☀-☄☆-➿]'
PHRASES = ['핵심은', '한 줄로', '정리하면', '결론부터', '짚어', '흥미롭게도', '살펴보겠습니다', '해 드렸습니다', '거든요', '리포에', '갈래', '원장', '스윕', '창고', '원문 봄', '요약만 봄']


def _files(work, pats):
    out = []
    for p in pats:
        out += sorted(glob.glob(os.path.join(work, p)))
    return out


def _text(path):
    if path.lower().endswith('.pdf'):
        import fitz
        return '\n'.join(p.get_text() for p in fitz.open(path))
    return open(path, encoding='utf-8', errors='replace').read()


def g_text(work, g):
    fs = _files(work, g['files']); bad = []
    if not fs:
        return False, [f'글 파일이 없다 {g["files"]}']
    for f in fs:
        t = _text(f); name = os.path.basename(f)
        if g.get('symbols', True):
            hit = sorted(set(re.findall(SYMS, t)))
            if hit: bad.append(f'{name}: 금지 기호 {hit}')
        if g.get('phrases', True):
            hit = [p for p in PHRASES if p in t]
            if hit: bad.append(f'{name}: 금지 표현 {hit}')
        for rule in g.get('forbid', []):
            for mm in re.finditer(rule['re'], t):
                ctx = t[max(0, mm.start() - 12): mm.end() + 12].replace('\n', ' ')
                if rule.get('unless') and re.search(rule['unless'], ctx):
                    continue
                bad.append(f'{name}: 금지 값 «{mm.group(0)}» ({rule.get("why", "")}) … {ctx} …')
    return not bad, bad or [f'글 {len(fs)}개 통과']


def g_files(work, g):
    fs = _files(work, [g['glob']]); bad = []
    if 'count' in g and len(fs) != g['count']:
        bad.append(f'개수 {len(fs)} (나와야 할 수 {g["count"]})')
    if g.get('size'):
        from PIL import Image
        for f in fs:
            sz = list(Image.open(f).size)
            if sz != list(g['size']): bad.append(f'{os.path.basename(f)} 크기 {sz}')
    if g.get('max_mb'):
        for f in fs:
            mb = os.path.getsize(f) / 1e6
            if mb > g['max_mb']: bad.append(f'{os.path.basename(f)} {mb:.1f}MB > {g["max_mb"]}')
    return not bad, bad or [f'{len(fs)}개, 크기·용량 통과']


def _body(r):
    """글자 상자를 몸통 높이로 좁힌다(글꼴 위아래 여유까지 든 상자는 위아래 줄이 겹쳐 보여 헛경보가 났다)."""
    import fitz
    h = r.height
    return fitz.Rect(r.x0 + 0.5, r.y0 + 0.28 * h, r.x1 - 0.5, r.y1 - 0.22 * h)


def g_pdf_overlap(work, g):
    """글자끼리 겹침 + (lines) 가는 선이 글자 몸통을 가로지름(10-22 «삼각형 281 x 237» 이 철판 점선을 가로질렀다)."""
    import fitz
    bad = []
    for f in _files(work, g['files']):
        d = fitz.open(f)
        for pi, p in enumerate(d):
            words = [w for w in p.get_text('words') if w[4].strip()]
            boxes = [_body(fitz.Rect(w[:4])) for w in words]
            for i in range(len(words)):
                for j in range(i + 1, len(words)):
                    if words[i][5:7] == words[j][5:7]:
                        continue
                    x = boxes[i] & boxes[j]
                    if not x.is_empty and x.get_area() > g.get('min_ratio', 0.2) * min(boxes[i].get_area(), boxes[j].get_area()):
                        bad.append(f'{os.path.basename(f)} {pi + 1}쪽: «{words[i][4]}» 와 «{words[j][4]}» 겹침')
            for w in words:
                if not fitz.Rect(w[:4]) in p.rect:
                    bad.append(f'{os.path.basename(f)} {pi + 1}쪽: «{w[4]}» 쪽 밖으로 나감')
            if g.get('lines', True):
                segs = []
                for dr in p.get_drawings():
                    col = dr.get('color')
                    if dr.get('fill') is not None or not col or (dr.get('width') or 0) > 1.2:
                        continue
                    if 0.2126 * col[0] + 0.7152 * col[1] + 0.0722 * col[2] > 0.85:   # 흰 격자·밝은 장식선(머리띠 격자, 로고 밑줄)은 뺀다
                        continue
                    for it in dr['items']:
                        if it[0] == 'l':
                            segs.append((it[1], it[2]))
                for k, w in enumerate(words):
                    b = boxes[k]
                    if b.is_empty: continue
                    for a, c in segs:
                        if _seg_hits(a, c, b):
                            bad.append(f'{os.path.basename(f)} {pi + 1}쪽: 선이 «{w[4]}» 를 가로지름'); break
    return not bad, bad or ['겹침 0']


def _seg_hits(a, c, r):
    """선분 a-c 가 사각형 r 안을 지나나(리앙-바스키)."""
    x0, y0, x1, y1 = a.x, a.y, c.x, c.y
    dx, dy = x1 - x0, y1 - y0; t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, x0 - r.x0), (dx, r.x1 - x0), (-dy, y0 - r.y0), (dy, r.y1 - y0)):
        if pp == 0:
            if qq < 0: return False
            continue
        t = qq / pp
        if pp < 0:
            if t > t1: return False
            t0 = max(t0, t)
        else:
            if t < t0: return False
            t1 = min(t1, t)
    return t1 - t0 > 1e-6


def g_cmd(work, g):
    import subprocess, sys
    cmd = [sys.executable if c == 'python' else c for c in g['cmd']]
    r = subprocess.run(cmd, cwd=work, capture_output=True, text=True, encoding='utf-8', errors='replace', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    msg = (r.stdout or '').strip().splitlines()[-3:] + (r.stderr or '').strip().splitlines()[-3:]
    return r.returncode == 0, msg or [f'종료코드 {r.returncode}']


def g_graded(work, g):
    """넘기기 전 검수(protocols/grade.md)가 지금 결과물로 끝났나. 판정은 보고서의 «판정:» 줄에서 읽는다.
    문서에만 적은 검수는 바쁘면 건너뛴다(DeGaJa 운영 규칙 3) — 그래서 바깥 단계 앞에서 기계로 막는다."""
    bad, info = [], []
    newest = max((os.path.getmtime(f) for f in _files(work, g.get('after', []))), default=0)
    for label, pat, need in (('독립 채점', g.get('report', '../grade/채점_*.md'), True),
                             ('원본 대조', g.get('source', '../grade/source_check*/원본대조_보고.md'), g.get('need_source', False))):
        fs = _files(work, [pat])
        if not fs:
            if need:
                bad.append(f'{label} 보고서 없음({pat}) — protocols/grade.md 대로 부르고 보고서를 남긴다')
            continue
        f = max(fs, key=os.path.getmtime); name = os.path.relpath(f, work)
        if os.path.getmtime(f) < newest:
            bad.append(f'{label} {name} 가 결과물보다 오래됐다 — 고친 판으로 다시 부른다'); continue
        m = re.search(r'판정:\s*(넘김 가능|고칠 것 있음|사람 확인 필요)', open(f, encoding='utf-8', errors='replace').read())
        if not m:
            bad.append(f'{label} {name} 에 «판정:» 줄이 없다')
        elif m.group(1) == '고칠 것 있음':
            bad.append(f'{label} {name}: 고칠 것 있음')
        elif m.group(1) == '사람 확인 필요':
            info.append(f'{label} {name}: 사람 확인 필요 — 그 항목을 넘기기 보고 «확인이 필요한 것»에 옮긴다')
        else:
            info.append(f'{label} {name}: 넘김 가능')
    return not bad, bad + info


def zoom_sheet(images, out, grid=(3, 2), tile=800):
    """그림마다 grid 칸으로 나눠 칸마다 확대한 판을 이어 붙인다(그림 하나에 한 줄)."""
    from PIL import Image, ImageDraw
    rows = []
    for f in images:
        im = Image.open(f).convert('RGB'); W, H = im.size; gx, gy = grid
        cw, ch = W // gx, H // gy
        tiles = [im.crop((x * cw, y * ch, (x + 1) * cw, (y + 1) * ch)).resize((tile, round(tile * ch / cw))) for y in range(gy) for x in range(gx)]
        rows.append((os.path.basename(f), tiles))
    th = rows[0][1][0].height
    sheet = Image.new('RGB', (tile * len(rows[0][1]) + 10 * (len(rows[0][1]) - 1), (th + 30) * len(rows)), 'white')
    dr = ImageDraw.Draw(sheet)
    for r, (name, tiles) in enumerate(rows):
        y = r * (th + 30)
        dr.text((4, y + 4), name, fill=(0, 0, 0))
        for i, t in enumerate(tiles):
            sheet.paste(t, (i * (tile + 10), y + 26))
    sheet.save(out)
    return out


def diff_sheet(a, b, out, thresh=24, top=4, pad=60):
    """a(옵션 켬)·b(옵션 끔) 차이를 붉게 칠한 전체 + 차이가 큰 자리 top 곳을 a·b 나란히 확대."""
    import numpy as np
    from PIL import Image
    A = Image.open(a).convert('RGB'); B = Image.open(b).convert('RGB').resize(A.size)
    da = np.abs(np.asarray(A, dtype=np.int16) - np.asarray(B, dtype=np.int16)).max(axis=2)
    mask = da > thresh
    heat = np.asarray(A).copy(); heat[mask] = (heat[mask] * 0.3 + np.array([255, 0, 0]) * 0.7).astype('uint8')
    # 차이 큰 칸(64px 격자)을 골라 확대
    gs = 64; Hh, Ww = mask.shape; cells = []
    for y in range(0, Hh, gs):
        for x in range(0, Ww, gs):
            cells.append((int(mask[y:y + gs, x:x + gs].sum()), x, y))
    cells.sort(reverse=True); picked = []
    for s, x, y in cells:
        if s == 0 or len(picked) >= top: break
        if all(abs(x - px) > 3 * gs or abs(y - py) > 3 * gs for _, px, py in picked):
            picked.append((s, x, y))
    zw = 360; crops = []
    for _, x, y in picked:
        box = (max(0, x - pad), max(0, y - pad), min(Ww, x + gs + pad), min(Hh, y + gs + pad))
        crops.append((A.crop(box).resize((zw, zw)), B.crop(box).resize((zw, zw))))
    hw = Image.fromarray(heat); hw.thumbnail((zw * 2 + 10, 10000))
    sheet = Image.new('RGB', (zw * 2 + 10, hw.height + len(crops) * (zw + 10) + 10), 'white')
    sheet.paste(hw, (0, 0))
    for i, (ca, cb) in enumerate(crops):
        y = hw.height + 10 + i * (zw + 10); sheet.paste(ca, (0, y)); sheet.paste(cb, (zw + 10, y))
    sheet.save(out)
    return dict(out=out, changed_pct=round(100 * mask.mean(), 3), spots=len(picked))


def run_all(P, s):
    work = P['_work']; ok_all = True; look = []
    for g in s.get('gates', []):
        t = g['type']
        if t == 'zoom':
            fs = _files(work, g['images'])
            if fs:
                out = zoom_sheet(fs, os.path.join(work, g.get('out', '_zoom.png')), tuple(g.get('grid', (3, 2))))
                look.append(out); print(f'    [볼 것] 확대판 {os.path.relpath(out, work)} (그림 {len(fs)}장)', flush=True)
            continue
        if t == 'diff':
            r = diff_sheet(os.path.join(work, g['a']), os.path.join(work, g['b']), os.path.join(work, g.get('out', '_diff.png')), g.get('thresh', 24))
            look.append(r['out']); print(f'    [볼 것] 켬·끔 차이 {os.path.relpath(r["out"], work)} (바뀐 화소 {r["changed_pct"]}%, 확대 {r["spots"]}곳)', flush=True)
            continue
        fn = dict(text=g_text, files=g_files, pdf_overlap=g_pdf_overlap, cmd=g_cmd, graded=g_graded)[t]
        ok, msgs = fn(work, g)
        ok_all &= ok
        print(f'    [검사 {"통과" if ok else "실패"}] {t}{(" " + g["label"]) if g.get("label") else ""}', flush=True)
        for m_ in msgs[:8]:
            print('      ' + m_, flush=True)
    return dict(ok=ok_all, look=look)
