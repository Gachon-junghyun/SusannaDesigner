# -*- coding: utf-8 -*-
"""손님 로고 원안 → 상업용 벡터 한 바퀴 (2026-10-03, 고객H 뷰티에서 굳힘).

  redraw    원안을 ChatGPT·제미나이에 --ref 로 넣어 «그대로 깨끗하게» 다시 그리게 하고 원본 크기로 받는다
  retrace   깨끗한 그림 → 매끈한 SVG (업스케일 → 픽셀 사이 윤곽 → 티끌·워터마크 제거 → potrace → 가로 띠별 무리 + 그라디언트)
  fabcheck  실제 크기(mm)에서 가장 가는 곳·선 끝 두께를 재고 걸린 자리를 빨갛게 표시
  swap      SVG 의 한 무리(예: beauty)만 새 레터링 그림으로 갈아 끼운다 — 나머지는 한 점도 안 건드린다
  board     여러 SVG → 한 .ai(대지 여러 개 + 이름표) · 글자 전부 외곽선 · PDF
  straighten  사람이 조립한 .ai 에서 곧아야 할 획 테두리(수직·수평)가 토막 나 꺾인 것을 직선 한 줄로 (2026-10-04, 고객H «메»)
             + 가로 이음을 사이에 둔 같은 줄 테두리를 한 x 로(«층 떨어짐») · PDF 는 «_보기용»(일러로 다시 열면 그라디언트 네모가 생긴다)
  cutfile   시안 .ai → 재단선 .ai: 그라디언트 네모·대지 밖 사본 빼고 클립 풀고 칠 없음 + 검정 선 하나 (따낼 때 쓴다)

🔴 왜 이 순서인가 — 실측:
  · 원안(458px 칸)을 그대로 따면 아무리 다듬어도 확대 시 울퉁불퉁하다 → 원본 자체를 AI 로 다시 그려 해상도를 얻는다
  · 제미나이는 «원본 크기 이미지 다운로드»가 2266px, 미리보기는 1024px → gen.py 가 이제 버튼을 눌러 받는다
  · vclean(own)으로 따면 1px 흔들림을 다 따라가 잔물결·면 깎임 → potrace(흐림 2 · opttolerance 0.8 · alphamax 1.0) 가 곡선 1,266→257
  · «뾰족하면 시공이 안 된다»를 벡터를 불려서 고치면(열기 + 뼈대 불리기) 선이 울퉁불퉁해진다 → redraw --blunt 로 다시 뽑는다
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

DEGAJA = os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent'))

PROMPT = ('Create an image: redraw the attached logo EXACTLY as a clean, high-resolution master artwork for commercial print '
          'and storefront signage. Do NOT redesign anything. Keep the identical composition, proportions, drawing, text and colors. '
          'Only make it crisp: perfectly smooth, continuous lines, no jagged edges, no wobble, no stray dots, no specks, no noise, '
          'no grain, no paper texture, no glow, no shadow. {change}Wide margin around the logo, nothing touches the image edge. '
          'Flat 2D artwork, NOT a mockup, NOT a photograph, no 3D, no watermark.')
BLUNT = ('Change ONLY the stroke endings so the logo can be fabricated as a metal sign: every line keeps an even thickness all the way '
         'to its end, and every end is blunt and rounded (round cap) — no sharp tapered points, no hairline tips; serifs become soft '
         'rounded slab serifs of even thickness. ')


# ───────────────────────── redraw ─────────────────────────
def redraw(ref, out, change='', blunt=False, engines=('chatgpt', 'gemini'), name='redraw'):
    """원안 → AI 두 곳에서 다시 그린 원본 크기 PNG. change 에 글자를 박아라(한글은 음절을 풀어서)."""
    os.makedirs(out, exist_ok=True)
    im = Image.open(ref).convert('RGB')
    if im.width > 1100:   # 제미나이 붙여넣기 첨부는 1100px 이하(gemini 함정 ⑩)
        im = im.resize((1100, round(im.height * 1100 / im.width)), Image.LANCZOS)
    r = os.path.join(out, '_ref.png'); im.save(r)
    ch = (BLUNT if blunt else '') + (change.strip() + ' ' if change else '')
    jobs = os.path.join(out, '_jobs.json')
    io.open(jobs, 'w', encoding='utf-8').write(json.dumps([{'name': name, 'prompt': PROMPT.format(change=ch)}], ensure_ascii=False))
    made = []
    for e in engines:
        gen = os.path.join(DEGAJA, '.claude', 'skills', '%s-image' % e, 'gen.py')
        od = os.path.join(out, e)
        env = dict(os.environ, PYTHONIOENCODING='utf-8')
        p = subprocess.run([sys.executable, gen, '--out', od, '--jobs', jobs, '--ref', r, '--per-chat', '1', '--pause', '3-6'],
                           cwd=DEGAJA, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
        f = os.path.join(od, name + '.png')
        ok = os.path.exists(f)
        print(e, '✅' if ok else '🔴', f if ok else (p.stdout + p.stderr)[-400:])
        if ok:
            made.append(f)
    return made


# ───────────────────────── 공통: 잉크 마스크 ─────────────────────────
def _ink(rgb, sig=1.6, drop_grey=True, speck=2.5e-6):
    """단색 바탕 + 잉크 → (마스크, alpha, 바탕색, 리포트). 바탕 = 가장자리 중앙값, 잉크 = Lab 거리(픽셀 사이 윤곽용 연속값)."""
    import cv2
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    e = 40
    edge = np.concatenate([lab[:e].reshape(-1, 3), lab[-e:].reshape(-1, 3), lab[:, :e].reshape(-1, 3), lab[:, -e:].reshape(-1, 3)])
    bgL = np.median(edge, 0)
    d = np.linalg.norm(lab - bgL, axis=-1)
    noise = np.percentile(np.linalg.norm(edge - bgL, axis=-1), 99) + 2
    full = np.percentile(d[d > noise * 3], 60) if (d > noise * 3).any() else 60
    alpha = np.clip((d - noise) / max(full - noise, 1), 0, 1)
    m = (cv2.GaussianBlur(alpha, (0, 0), sig) > 0.5).astype(np.uint8)   # 🔴 흐린 뒤 반에서 자른다 = 계단이 안 생긴다
    H, W = m.shape
    amin = speck * H * W
    bg_chroma = float(np.hypot(bgL[1] - 128, bgL[2] - 128))
    chroma = np.hypot(lab[..., 1] - 128, lab[..., 2] - 128)
    n, lb, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros_like(m); specks, grey = 0, 0
    for i in range(1, n):
        sel = lb == i
        if st[i, 4] < amin:
            specks += 1; continue
        # 무채색 조각 = 제미나이 ✦. 바탕도 잉크도 색이 있을 때만 쓴다(흑백 그림에선 끈다)
        if drop_grey and bg_chroma > 4 and float(np.median(chroma[sel])) < 9:
            grey += 1; continue
        keep[sel] = 1
    inv = (1 - keep).astype(np.uint8)
    n2, lb2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    holes = 0
    for i in range(1, n2):
        if st2[i, 4] < amin and st2[i, 0] > 0 and st2[i, 1] > 0:
            keep[lb2 == i] = 1; holes += 1
    bg = np.median(rgb[alpha < 0.02].reshape(-1, 3)[::37], 0)   # 표본으로 — 큰 그림에서 메모리
    return keep, alpha, bg, dict(specks_removed=specks, watermark_removed=grey, holes_filled=holes)


def _bands(m, gap=0.012):
    rows = m.any(1); H = len(rows); bands = []; y = 0
    while y < H:
        if rows[y]:
            y0 = y
            while y < H and rows[y]:
                y += 1
            bands.append([y0, y])
        y += 1
    out = []
    for b in bands:
        if out and b[0] - out[-1][1] < gap * H:
            out[-1][1] = b[1]
        else:
            out.append(b)
    return out


def _potrace_d(mask, mapf, blur=2.0, optol=0.8, alphamax=1.0, turd=60):
    """마스크 → potrace 경로 d. mapf(x, y) → (x, y) 로 좌표를 옮긴다. 계단만 지우고 곡선은 최소 개수, 꺾임이 크면 모서리로 남긴다."""
    import cv2
    import potrace
    big = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), blur) > 0.5
    pl = potrace.Bitmap(~big).trace(turdsize=turd, alphamax=alphamax, opticurve=True, opttolerance=optol)
    f = lambda p: '%.2f %.2f' % mapf(p.x, p.y)
    d, nseg = '', 0
    for cv in pl:
        d += 'M' + f(cv.start_point)
        for sg in cv.segments:
            nseg += 1
            d += ('L' + f(sg.c) + 'L' + f(sg.end_point)) if sg.is_corner else ('C' + f(sg.c1) + ' ' + f(sg.c2) + ' ' + f(sg.end_point))
        d += 'Z'
    return d, nseg, len(pl)


def _hex(c):
    return '#%02x%02x%02x' % tuple(int(round(v)) for v in c)


# ───────────────────────── retrace ─────────────────────────
def retrace(png, out_svg, work=4800, up=True, names=None, blur=2.0, optol=0.8, alphamax=1.0, speck=2.5e-6):
    """깨끗한 그림 → 매끈한 SVG. 가로 띠마다 한 무리(<g id=…>)로 나누고 원본 색으로 3단 그라디언트."""
    from . import deliver
    png, out_svg = os.path.abspath(png), os.path.abspath(out_svg)   # 🔴 상대 경로면 업스케일 결과를 못 찾는다(2026-10-03 실측)
    src = png
    if up and Image.open(png).width < 3000:
        x4 = os.path.splitext(out_svg)[0] + '_x4.png'
        deliver.upscale(png, x4, 'realesrgan-x4plus-anime')
        src = x4
    im = Image.open(src).convert('RGB')
    if im.width > work:
        im = im.resize((work, round(im.height * work / im.width)), Image.LANCZOS)
    rgb = np.array(im); H, W = rgb.shape[:2]
    m, alpha, bg, rep = _ink(rgb, speck=speck)
    bands = _bands(m)
    names = names or (['emblem', 'wordmark', 'beauty'] if len(bands) == 3 else ['g%d' % i for i in range(len(bands))])
    ys, xs = np.where(m)
    pad = int(0.10 * max(xs.max() - xs.min(), ys.max() - ys.min()))
    X0, Y0, X1, Y1 = max(0, xs.min() - pad), max(0, ys.min() - pad), min(W, xs.max() + pad), min(H, ys.max() + pad)
    defs, body, groups = [], [], []
    for nm, (b0, b1) in zip(names, bands):
        gm = np.zeros_like(m); gm[b0:b1] = m[b0:b1]
        px = rgb[(gm > 0) & (alpha > 0.9)].astype(np.float32)
        if len(px) < 10:
            px = rgb[gm > 0].astype(np.float32)
        L = px @ np.array([.299, .587, .114]); lo, hi = np.percentile(L, 15), np.percentile(L, 85)
        cols = [px[L >= hi].mean(0), px[(L > lo) & (L < hi)].mean(0) if ((L > lo) & (L < hi)).any() else px.mean(0), px[L <= lo].mean(0)]
        d, nseg, ncont = _potrace_d(gm > 0, lambda x, y: (x - X0, y - Y0), blur=blur, optol=optol, alphamax=alphamax, turd=int(speck * H * W) + 1)
        gy, gx = np.where(gm)
        defs.append('<linearGradient id="grad_%s" gradientUnits="userSpaceOnUse" x1="%d" y1="%d" x2="%d" y2="%d">'
                    '<stop offset="0" stop-color="%s"/><stop offset="0.5" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
                    % (nm, gx.max() - X0, gy.min() - Y0, gx.min() - X0, gy.max() - Y0, *[_hex(c) for c in cols]))
        body.append('<g id="%s"><path fill="url(#grad_%s)" fill-rule="evenodd" d="%s"/></g>' % (nm, nm, d))
        groups.append(dict(group=nm, segments=nseg, contours=ncont, colors=[_hex(c) for c in cols]))
    Wc, Hc = X1 - X0, Y1 - Y0
    io.open(out_svg, 'w', encoding='utf-8').write(
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d"><defs>%s</defs>'
        '<g id="background"><rect width="%d" height="%d" fill="%s"/></g>%s</svg>' % (Wc, Hc, Wc, Hc, ''.join(defs), Wc, Hc, _hex(bg), ''.join(body)))
    rep.update(src=os.path.basename(src), canvas=[int(Wc), int(Hc)], bg=_hex(bg), groups=groups)
    json.dump(rep, open(os.path.splitext(out_svg)[0] + '_측정.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=int)
    return rep


# ───────────────────────── fabcheck ─────────────────────────
def fabcheck(path, logo_h_mm, min_mm=None, out_png=None, px=3000):
    """실제 크기에서 가장 가는 곳·선 끝 두께(mm). min_mm 를 주면 그보다 가는 자리를 빨갛게(끝은 주황) 표시한다.
    PNG·AI·PDF 를 받는다(SVG 는 그라디언트가 안 그려질 수 있어 .ai 로 먼저 저장해서 준다)."""
    import cv2
    from . import deliver
    if os.path.splitext(path)[1].lower() == '.svg':
        ai = os.path.splitext(path)[0] + '.ai'
        if not os.path.exists(ai):
            deliver.to_ai(path, ai)
        path = ai
    if os.path.splitext(path)[1].lower() in ('.png', '.jpg', '.jpeg', '.webp'):
        rgb = np.array(Image.open(path).convert('RGB'))
    else:
        tmp = os.path.join(tempfile.mkdtemp(prefix='ad_fab_'), 'r.png')
        deliver.look(path, tmp, px=px)
        rgb = np.array(Image.open(tmp).convert('RGB'))
    m, _, _, _ = _ink(rgb, sig=1.0)
    ys = np.where(m.any(1))[0]; LH = ys[-1] - ys[0]
    mm = lambda v: round(float(v) / LH * logo_h_mm, 1)
    dt = cv2.distanceTransform(m, cv2.DIST_L2, 5)
    sk = cv2.ximgproc.thinning(m * 255) > 0
    k = cv2.filter2D(sk.astype(np.uint8), -1, np.ones((3, 3), np.uint8))
    ends = sk & (k == 2)
    rr = max(2, int(np.median(dt[sk]) * 1.2))
    disk = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rr + 1, 2 * rr + 1))
    near = cv2.dilate(ends.astype(np.uint8), disk) > 0
    body = sk & ~near
    w = dt[body] * 2
    # 선 끝 두께 = 끝점에서 rr 안쪽(반 줄기) 지점의 폭 — 끝점 바로 위는 둥근 마감이라 늘 작게 잡힌다
    ey, ex = np.where(ends)
    tip = []
    for y, x in zip(ey, ex):
        y0, y1, x0, x1 = max(0, y - rr), y + rr + 1, max(0, x - rr), x + rr + 1
        win = dt[y0:y1, x0:x1] * (sk[y0:y1, x0:x1])
        tip.append(float(win.max()) * 2 if win.size else 0)
    tip = np.array(tip) if tip else np.array([0.0])
    bands = _bands(m)
    per = []
    for b0, b1 in bands:
        s = body.copy(); s[:b0] = False; s[b1:] = False
        if s.any():
            per.append(mm(np.median(dt[s] * 2)))
    rep = dict(logo_h_mm=logo_h_mm, min_mm=mm(np.percentile(w, 1)), median_mm=mm(np.median(w)),
               band_median_mm=per, tip_p10_mm=mm(np.percentile(tip, 10)), tips=int(len(tip)),
               channel_38mm=('가능' if mm(np.percentile(w, 1)) >= 38 else '불가'))
    if min_mm:
        lim = min_mm / logo_h_mm * LH
        thin = body & (dt * 2 < lim)
        bad_tip = [(y, x) for (y, x), t in zip(zip(ey, ex), tip) if t < lim]
        rep.update(thin_px=int(thin.sum()), bad_tips=len(bad_tip))
        if out_png:
            o = rgb.copy() // 2 + 60
            o[cv2.dilate(thin.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0] = (230, 40, 40)
            for (y, x) in bad_tip:
                cv2.circle(o, (int(x), int(y)), int(rr * 2.5), (255, 140, 0), 4)
            Image.fromarray(o).save(out_png)
    return rep


# ───────────────────────── swap ─────────────────────────
def swap(svg, group, png, out_svg, fit='width'):
    """SVG 의 <g id=group> 만 새 레터링(단색 바탕 그림)으로 바꾼다. 폭·가운데를 원래 무리에 맞추고, 칠은 원래 무리 것을 그대로."""
    import cv2
    s = io.open(svg, encoding='utf-8').read()
    g = re.search(r'<g id="%s">.*?</g>' % re.escape(group), s, re.S).group(0)
    fill = re.search(r'fill="([^"]+)"', g).group(1)
    nums = np.array([float(v) for v in re.findall(r'-?\d+\.\d+', re.search(r' d="([^"]+)"', g).group(1))]).reshape(-1, 2)
    ox0, oy0 = nums.min(0); ox1, oy1 = nums.max(0); ow, oh = ox1 - ox0, oy1 - oy0
    im = Image.open(png).convert('RGB')
    if im.width < 3000:
        im = im.resize((im.width * 2, im.height * 2), Image.BICUBIC)
    m, _, _, _ = _ink(np.array(im), drop_grey=False, speck=4e-5)
    ys, xs = np.where(m); nx0, nx1, ny0, ny1 = xs.min(), xs.max(), ys.min(), ys.max()
    k = ow / (nx1 - nx0) if fit == 'width' else oh / (ny1 - ny0)
    nh = (ny1 - ny0) * k
    # 위 무리와의 틈은 원래 틈 이상으로(굵은 체는 높이가 커진다)
    above = [float(v) for v in re.findall(r'-?\d+\.\d+ (-?\d+\.\d+)', s[:s.index(g)])]
    prev_bottom = max([y for y in above if y < oy0], default=oy0)
    ty0 = max((oy0 + oy1) / 2 - nh / 2, prev_bottom + (oy0 - prev_bottom) * 0.9)
    tx0 = (ox0 + ox1) / 2 - (nx1 - nx0) * k / 2
    d, nseg, _ = _potrace_d(m > 0, lambda x, y: ((x - nx0) * k + tx0, (y - ny0) * k + ty0), blur=2.0, optol=0.6)
    out = s.replace(g, '<g id="%s"><path fill="%s" fill-rule="evenodd" d="%s"/></g>' % (group, fill, d))
    W, Hh = [int(v) for v in re.search(r'width="(\d+)" height="(\d+)"', out).groups()]
    need = int(ty0 + nh + max(0, Hh - oy1))
    if need > Hh:   # 캔버스·바탕을 아래로 늘린다
        out = out.replace('height="%d" viewBox="0 0 %d %d"' % (Hh, W, Hh), 'height="%d" viewBox="0 0 %d %d"' % (need, W, need), 1)
        out = out.replace('<rect width="%d" height="%d"' % (W, Hh), '<rect width="%d" height="%d"' % (W, need), 1)
    io.open(out_svg, 'w', encoding='utf-8').write(out)
    return dict(height_ratio=round(nh / oh, 2), segments=nseg)


# ───────────────────────── board ─────────────────────────
def board(svgs, labels, out_stem, w_mm=200, cols=3):
    """여러 SVG → 한 .ai(대지 여럿, 이름표) · 글자 외곽선 · PDF · 미리보기 PNG. 🔴 다른 문서에서 그룹으로 바로 복제하면 PARM — 레이어로 복제 후 묶는다."""
    import win32com.client as w32
    L = [{'svg': os.path.abspath(p).replace('\\', '/'), 'label': l} for p, l in zip(svgs, labels)]
    O = os.path.abspath(out_stem).replace('\\', '/')
    js = r'''app.userInteractionLevel=UserInteractionLevel.DONTDISPLAYALERTS;
var MM=72/25.4, L=%s, OUT="%s", COLS=%d, W=%f*MM, GAP=20*MM, LAB=18*MM;
var doc=app.documents.add(DocumentColorSpace.RGB, W, W); var main=doc.layers[0]; main.name="시안"; var rects=[], rowH=0;
for(var i=0;i<L.length;i++){ var s=app.open(File(L[i].svg)); var g=main.groupItems.add(); g.name=L[i].label; var cp=[];
  for(var k=s.pageItems.length-1;k>=0;k--){ var it=s.pageItems[k]; if(it.parent.typename!=="Layer") continue; cp.push(it.duplicate(main, ElementPlacement.PLACEATBEGINNING)); }
  s.close(SaveOptions.DONOTSAVECHANGES); app.activeDocument=doc; for(var m=0;m<cp.length;m++) cp[m].moveToBeginning(g);
  var b=g.geometricBounds, sc=W/(b[2]-b[0])*100; g.resize(sc,sc,true,true,true,true,sc,Transformation.TOPLEFT);
  b=g.geometricBounds; var h=b[1]-b[3]; rowH=Math.max(rowH,h);
  var col=i%%COLS, row=Math.floor(i/COLS), x=col*(W+GAP), y=-row*(W*1.3+LAB+GAP);
  g.translate(x-b[0], (y-LAB)-b[1]);
  var t=main.textFrames.add(); t.contents=L[i].label; try{ t.textRange.characterAttributes.textFont=app.textFonts.getByName("NotoSansKR-Bold"); }catch(e){}
  t.textRange.characterAttributes.size=20; var c=new RGBColor(); c.red=30;c.green=30;c.blue=30; t.textRange.characterAttributes.fillColor=c; t.left=x; t.top=y-2*MM;
  rects.push([x,y,x+W,y-LAB-h]); }
for(var r=0;r<rects.length;r++){ doc.artboards.add(rects[r]); doc.artboards[doc.artboards.length-1].name=L[r].label; }
doc.artboards.remove(0); var n=doc.textFrames.length; for(var q=n-1;q>=0;q--) doc.textFrames[q].createOutline();
var opt=new IllustratorSaveOptions(); opt.compatibility=Compatibility.ILLUSTRATOR17; opt.pdfCompatible=true; doc.saveAs(new File(OUT+".ai"), opt);
var po=new PDFSaveOptions(); po.compatibility=PDFCompatibility.ACROBAT7; po.preserveEditability=false; doc.saveAs(new File(OUT+".pdf"), po);
var e=new ExportOptionsPNG24(); e.artBoardClipping=false; e.horizontalScale=e.verticalScale=40; e.transparency=false; doc.exportFile(new File(OUT+"_미리보기.png"), ExportType.PNG24, e);
var res=doc.artboards.length+"/"+doc.textFrames.length; doc.close(SaveOptions.DONOTSAVECHANGES); app.userInteractionLevel=UserInteractionLevel.DISPLAYALERTS; res;''' % (
        json.dumps(L, ensure_ascii=False), O, cols, w_mm)
    try:
        app = w32.GetActiveObject('Illustrator.Application')
    except Exception:
        app = w32.Dispatch('Illustrator.Application')
    nab, left = app.DoJavaScript(js).split('/')
    import fitz
    fonts = [len(p.get_fonts()) for p in fitz.open(O + '.pdf')]
    return dict(ai=O + '.ai', pdf=O + '.pdf', artboards=int(nab), text_left=int(left), pdf_fonts=fonts)


# ───────────────────────── straighten ─────────────────────────
# 일러 «선만 보기»에서 곧아야 할 획 테두리가 «두 줄로 꺾여» 보이는 것을 편다 (2026-10-04, 고객H 간판 시안 «메»).
# 🔴 왜: potrace 는 긴 세로획 테두리를 곡선+직선 여러 토막으로 나누고 토막끼리 0.5~1° 어긋난다 — 미리보기에선
#    안 보이는데 선만 보기·확대에선 «꺾임»으로 보인다(실측: 메 ㅔ 기둥 = 곡선 107pt + 직선 106pt + 모서리 3pt, 0.8°).
# 수직·수평 ±axis 안의 거의 곧은 구간을 직선 한 줄로 합치고, snap 안이면 정확히 세운다. 이웃 곡선 핸들은 직선 방향으로
# 맞춰 이음새에 새 꺾임이 안 생기게 한다. 곡선(엠블럼·필기체)은 조건에 안 걸려 그대로다 — 고객H에서 0px 변화.
_ST = dict(axis=3.0, snap=1.5, min_len=12.0, dev_abs=2.2, dev_rel=0.03, smooth=35.0, align_tol=2.5, align_gap=80.0)
# 🔴 2026-10-04 (이어서) dev_abs 1.6→2.2 · smooth 20→35°: 1.6 이면 메 ㅁ 오른쪽 아래(1.7pt 출렁)가 안 펴졌고,
#    둥근 획 끝이 곧은 테두리에 20~32° 로 붙는 자리가 선만 보기에서 «꺾임»으로 남았다(사람: «아예 매끈해야»).


def _st_path(pts, log, P=_ST):
    import math
    sub = lambda a, b: (a[0] - b[0], a[1] - b[1])
    add = lambda a, b: (a[0] + b[0], a[1] + b[1])
    mul = lambda a, k: (a[0] * k, a[1] * k)
    L = lambda v: math.hypot(*v)

    def axoff(v):
        g = math.degrees(math.atan2(v[1], v[0])) % 180
        return min(g, abs(g - 90), 180 - g)

    keep_s = [p[6] if len(p) > 6 else 0 for p in pts]
    A = [(p[0], p[1]) for p in pts]; Lh = [(p[2], p[3]) for p in pts]; Rh = [(p[4], p[5]) for p in pts]; n = len(A)
    seg = lambda i: (A[i], Rh[i], Lh[(i + 1) % n], A[(i + 1) % n])

    def bez(q0, q1, q2, q3, m=8):
        return [((1 - t) ** 3 * q0[0] + 3 * (1 - t) ** 2 * t * q1[0] + 3 * (1 - t) * t * t * q2[0] + t ** 3 * q3[0],
                 (1 - t) ** 3 * q0[1] + 3 * (1 - t) ** 2 * t * q1[1] + 3 * (1 - t) * t * t * q2[1] + t ** 3 * q3[1])
                for t in [k / m for k in range(m + 1)]]

    def ok(i, j):
        """구간 i..j 전체에 직선을 최소제곱으로 맞춘다 — 🔴 끝점 두 개만 이으면 끝점이 흔들릴 때 놓친다
        (메 ㅁ 오른쪽 아래: 시작점이 이음 모서리라 3.3° 로 재져서 빠졌다). 맞으면 (중심, 방향) 을 돌려준다."""
        S = [q for k in range(i, j + 1) for q in bez(*seg(k % n))]
        cx = sum(q[0] for q in S) / len(S); cy = sum(q[1] for q in S) / len(S)
        sxx = sum((q[0] - cx) ** 2 for q in S); syy = sum((q[1] - cy) ** 2 for q in S); sxy = sum((q[0] - cx) * (q[1] - cy) for q in S)
        th = 0.5 * math.atan2(2 * sxy, sxx - syy); u = (math.cos(th), math.sin(th))
        pr = lambda q: (q[0] - cx) * u[0] + (q[1] - cy) * u[1]
        rs = lambda q: abs(-(q[0] - cx) * u[1] + (q[1] - cy) * u[0])
        s_ = [pr(q) for q in S]; ln = max(s_) - min(s_)
        if ln < P['min_len'] or axoff(u) > P['axis']:
            return None
        tol = min(P['dev_abs'], max(0.4, ln * P['dev_rel']))
        if max(rs(q) for q in S) > tol:
            return None
        an = [pr(A[k % n]) for k in range(i, j + 2)]          # 앵커가 한 방향으로만 나아가야 한다(되돌아가면 모서리다)
        if not (all(b > a for a, b in zip(an, an[1:])) or all(b < a for a, b in zip(an, an[1:]))):
            return None
        for k in range(i, j + 1):                               # 핸들이 구간 밖으로 삐져나가면 곡선이다
            for q in seg(k % n)[1:3]:
                if rs(q) > tol * 1.5 or not min(s_) - 0.02 * ln <= pr(q) <= max(s_) + 0.02 * ln:
                    return None
        return (cx, cy), u

    used = [False] * n; runs = []; i = 0; steps = 0
    while steps < n:                                  # 가장 긴 구간부터 욕심껏
        best = None
        for m in range(n - 2, -1, -1):
            j = i + m
            if any(used[k % n] for k in range(i, j + 1)):
                continue
            f = ok(i % n, j)
            if f:
                best = j; break
        if best is None:
            i += 1; steps += 1; continue
        for k in range(i, best + 1):
            used[k % n] = True
        runs.append((i % n, best - i + 1, f)); steps += best - i + 1; i = best + 1
    keep = [True] * n; nA, nL, nR = list(A), list(Lh), list(Rh); moved = set()
    for i, cnt, (c, u) in runs:
        e = (i + cnt) % n; a, b = nA[i], nA[e]        # 🔴 앞 구간이 옮긴 점 기준(원래 좌표로 되돌리면 축 맞춤이 풀린다)
        off = axoff(u)
        if cnt == 1 and L(sub(Rh[i], A[i])) < 1e-3 and L(sub(Lh[e], A[e])) < 1e-3 and axoff(sub(b, a)) < 1e-3:
            continue
        if i in moved and e in moved:
            na, nb = a, b
        elif off <= P['snap']:                         # 축에 세운다 — 맞춘 직선의 중심을 지나게
            vert = abs(u[1]) > abs(u[0])
            fix = a if i in moved else (b if e in moved else None)
            if vert:
                x = fix[0] if fix else c[0]; na, nb = (x, a[1]), (x, b[1])
            else:
                y = fix[1] if fix else c[1]; na, nb = (a[0], y), (b[0], y)
        else:                                          # 축에서 조금 기운 채로 — 맞춘 직선 위로 끝점을 수직으로 옮긴다
            o = a if i in moved else (b if e in moved else c)
            prj = lambda q: add(o, mul(u, (q[0] - o[0]) * u[0] + (q[1] - o[1]) * u[1]))
            na, nb = prj(a), prj(b)
        for k, old, new in ((i, a, na), (e, b, nb)):
            d = sub(new, old); nA[k] = new; nL[k] = add(nL[k], d); nR[k] = add(nR[k], d); moved.add(k)
        for k in range(i + 1, i + cnt):
            keep[k % n] = False
        log.append(dict(at=[round(a[0], 1), round(a[1], 1)], to=[round(b[0], 1), round(b[1], 1)], parts=cnt, deg=round(off, 2)))
    smooth = list(keep_s)
    for i, cnt, _ in runs:
        e = (i + cnt) % n; nR[i] = nA[i]; nL[e] = nA[e]
    for i, cnt, _ in runs:                               # 이음새: 원래 20° 안으로 이어지던 곡선 핸들을 직선 방향에 맞춘다
        e = (i + cnt) % n; d = sub(nA[e], nA[i]); dn = mul(d, 1 / L(d))
        for k, side, sg in ((i, 'L', -1), (e, 'R', 1)):
            hv = sub(nL[k] if side == 'L' else nR[k], nA[k]); hl = L(hv)
            if hl < 1e-3:
                continue
            w = mul(dn, sg)
            if (hv[0] * w[0] + hv[1] * w[1]) / hl > math.cos(math.radians(P['smooth'])):
                nv = add(nA[k], mul(w, hl))
                if side == 'L':
                    nL[k] = nv
                else:
                    nR[k] = nv
                smooth[k] = 1
    return [[nA[k][0], nA[k][1], nL[k][0], nL[k][1], nR[k][0], nR[k][1], smooth[k]] for k in range(n) if keep[k]]


def _st_align(pts, log, P=_ST):
    """가로획(짧은 이음)을 사이에 둔 같은 줄의 수직·수평 직선을 한 x(y)로 맞춘다 — «층 떨어짐».
    실측(메): ㅁ 오른쪽 테두리 위 5477.7 · 아래 5475.9~5478.7, ㅓ 기둥 위 5523.3 · 아래 5524.3."""
    n = len(pts); P_ = [list(q) + [0] * (7 - len(q)) for q in pts]
    lines = []
    for k in range(n):
        a, b = P_[k], P_[(k + 1) % n]
        if abs(a[4] - a[0]) > 1e-6 or abs(a[5] - a[1]) > 1e-6 or abs(b[2] - b[0]) > 1e-6 or abs(b[3] - b[1]) > 1e-6:
            continue
        if abs(a[0] - b[0]) < 1e-6 and abs(a[1] - b[1]) >= P['min_len']:
            lines.append(('v', k, a[0], min(a[1], b[1]), max(a[1], b[1])))
        elif abs(a[1] - b[1]) < 1e-6 and abs(a[0] - b[0]) >= P['min_len']:
            lines.append(('h', k, a[1], min(a[0], b[0]), max(a[0], b[0])))
    par = list(range(len(lines)))
    def root(i):
        while par[i] != i: i = par[i]
        return i
    for u in range(len(lines)):
        for v in range(u + 1, len(lines)):
            U, V = lines[u], lines[v]
            if U[0] != V[0] or abs(U[2] - V[2]) > P['align_tol'] or abs(U[2] - V[2]) < 1e-6: continue
            gap = max(U[3], V[3]) - min(U[4], V[4])
            if 0 < gap <= P['align_gap']: par[root(u)] = root(v)
    sets = {}
    for i in range(len(lines)): sets.setdefault(root(i), []).append(lines[i])
    for grp in sets.values():
        if len(grp) < 2: continue
        tot = sum(g[4] - g[3] for g in grp); tgt = sum(g[2] * (g[4] - g[3]) for g in grp) / tot
        for kind, k, c, _, _ in grp:
            for idx in (k, (k + 1) % n):
                q = P_[idx]; d = tgt - (q[0] if kind == 'v' else q[1]); j = 0 if kind == 'v' else 1
                q[j] += d; q[2 + j] += d; q[4 + j] += d
        log.append(dict(align=grp[0][0], to=round(tgt, 2), was=[round(g[2], 2) for g in grp]))
    return P_


_ST_JS = r'''app.userInteractionLevel=UserInteractionLevel.DONTDISPLAYALERTS;
function J(v){ if(typeof v=="number") return String(v); if(typeof v=="string") return '"'+v+'"';
 if(v instanceof Array){ var o=[]; for(var i=0;i<v.length;i++) o.push(J(v[i])); return "["+o.join(",")+"]"; }
 var o=[]; for(var k in v) o.push('"'+k+'":'+J(v[k])); return "{"+o.join(",")+"}"; }
var G=__G__, OFF=__OFF__;
function onboard(d,b){ for(var a=0;a<d.artboards.length;a++){ var r=d.artboards[a].artboardRect;
  if(b[0]>=r[0]-1&&b[2]<=r[2]+1&&b[1]<=r[1]+1&&b[3]>=r[3]-1) return true; } return false; }
function targets(d){ var r=[]; for(var i=0;i<d.compoundPathItems.length;i++){ var c=d.compoundPathItems[i];
  var n=c.parent.typename=="GroupItem"?c.parent.name:""; var hit=false; for(var g=0;g<G.length;g++) if(n==G[g]||G[g]=="*") hit=true;
  if(hit&&(OFF||onboard(d,c.geometricBounds))) r.push(i); } return r; }
'''


def straighten(ai_in, ai_out, groups=('wordmark', 'beauty'), offboard=False, corners=True, humps=False):
    """.ai 안 그룹(이름)의 컴파운드 패스 → 곧은 획 테두리를 한 줄로. 새 .ai + PDF. 원본은 안 건드린다.
    groups: 대상 그룹 이름(retrace 의 --names 와 같은 이름, '*' 는 대지 위 전부). offboard=False 면 대지 밖 사본은 둔다
    (🔴 2026-10-04 실측: 고객H 사본은 회전 없이 크기만 0.88~2.6배였다 — «회전돼 있다»는 짐작은 틀렸다).
    corners: 곧은 테두리 사이 둥근 모서리의 층·꺾임을 깨끗한 원호로(humps=True 면 위로 솟은 붓 «혹»까지).
    🔴 곡선 «다시 맞추기»(Schneider·Taubin·극점 앵커·고해상도 재트레이스)는 시험했다가 뺐다(2026-10-04) — 출렁임 수치는 0 이 됐지만
    일러 선만 보기에서 눈에 띄게 나아지지 않고 앵커만 늘었다. 엠블럼·필기체는 일러 화면에서 이미 매끈했다. 층은 «모서리»에 있었다."""
    import win32com.client as w32
    import fitz
    I = os.path.abspath(ai_in).replace('\\', '/'); O = os.path.abspath(ai_out).replace('\\', '/')
    pre = _ST_JS.replace('__G__', json.dumps(list(groups), ensure_ascii=False)).replace('__OFF__', 'true' if offboard else 'false')
    try:
        app = w32.GetActiveObject('Illustrator.Application')
    except Exception:
        app = w32.Dispatch('Illustrator.Application')
    js = pre + r'''var d=app.open(File("%s")); var T=targets(d), out=[];
for(var t=0;t<T.length;t++){ var c=d.compoundPathItems[T[t]], ps=[];
  for(var p=0;p<c.pathItems.length;p++){ var pi=c.pathItems[p], pts=[];
    for(var k=0;k<pi.pathPoints.length;k++){ var q=pi.pathPoints[k]; pts.push([q.anchor[0],q.anchor[1],q.leftDirection[0],q.leftDirection[1],q.rightDirection[0],q.rightDirection[1]]); }
    ps.push(pts); }
  out.push({idx:T[t],name:c.parent.name,paths:ps}); }
d.close(SaveOptions.DONOTSAVECHANGES); J(out);''' % I
    data = json.loads(app.DoJavaScript(js))
    rep = []
    for t in data:
        log = []; paths = []
        for p in t['paths']:
            q = _st_path(_st_align(_st_path(p, log), log), log)
            if corners:                                      # 곧은 테두리 사이 모서리의 층·꺾임(+ humps 면 혹) → 깨끗한 원호
                q = _corners(q, log, humps=humps)
            paths.append(q)
        t['paths'] = paths
        rep.append(dict(name=t['name'], fixes=len(log), anchors=sum(len(p) for p in t['paths']),
                        corners=[g for g in log if 'corner' in g]))
    js = pre + r'''var d=app.open(File("%s")); var D=%s;
for(var t=0;t<D.length;t++){ var c=d.compoundPathItems[D[t].idx];
  for(var p=0;p<D[t].paths.length;p++){ var pi=c.pathItems[p], P=D[t].paths[p];
    while(pi.pathPoints.length>P.length) pi.pathPoints[pi.pathPoints.length-1].remove();
    while(pi.pathPoints.length<P.length) pi.pathPoints.add();
    for(var k=0;k<P.length;k++){ var q=pi.pathPoints[k]; q.anchor=[P[k][0],P[k][1]]; q.leftDirection=[P[k][2],P[k][3]]; q.rightDirection=[P[k][4],P[k][5]];
      q.pointType=P[k][6]?PointType.SMOOTH:PointType.CORNER; } } }
var o=new IllustratorSaveOptions(); o.pdfCompatible=true; d.saveAs(new File("%s"), o);
var po=new PDFSaveOptions(); po.preserveEditability=false; d.saveAs(new File("%s"), po);
d.close(SaveOptions.DONOTSAVECHANGES); app.userInteractionLevel=UserInteractionLevel.DISPLAYALERTS; "ok";''' % (
        I, json.dumps(data, ensure_ascii=False), O, os.path.splitext(O)[0] + '_보기용.pdf')
    app.DoJavaScript(js)
    # 검증: 원본과 면 차이 픽셀(144dpi) — 대상 밖(엠블럼·필기체)은 0 이어야 정상
    pa, pb = fitz.open(ai_in)[0].get_pixmap(dpi=144), fitz.open(ai_out)[0].get_pixmap(dpi=144)
    xa = np.frombuffer(pa.samples, np.uint8).reshape(pa.height, pa.width, pa.n).astype(int)
    xb = np.frombuffer(pb.samples, np.uint8).reshape(pb.height, pb.width, pb.n).astype(int)
    diff = int((np.abs(xa - xb).max(axis=2) > 60).sum())
    return dict(ai=ai_out, pdf=os.path.splitext(ai_out)[0] + '_보기용.pdf', groups=rep, changed_px_at_144dpi=diff)


# ───────────────────────── cutfile ─────────────────────────
# 🔴 «그라데이션 때문에 윤곽선 보기에서 네모가 같이 나온다 — 딸 때 같이 따지면 안 된다» (2026-10-04, 고객H 간판 시안).
# 원인(실측): 그라디언트를 PDF 로 저장했다 일러로 다시 열거나 «확장»하면, 로고 하나가 «클립 그룹 = 글자 윤곽(클립) +
#   그라디언트를 칠한 큰 네모» 로 바뀐다. 패스에 직접 칠한 그라디언트(일러 고유)는 윤곽선 보기에 네모가 없다.
# 그래서 색과 재단을 나눈다 — 색은 패스에 직접 칠한 채로 시안 .ai 에 두고, 따낼 때는 이 명령으로 «재단선 파일»을 뽑는다:
#   그라디언트 네모 · 대지 밖 사본 · 숨긴/잠긴 것 빼고, 클립 그룹은 풀고, 모든 패스를 칠 없음 + 검정 선 하나로.
def cutfile(ai_in, ai_out, stroke_pt=0.25, min_mm=0.0):
    """시안 .ai → 재단선 .ai (외곽선만). min_mm>0 이면 그보다 작은 조각은 빼고 목록으로 돌려준다."""
    import win32com.client as w32
    I = os.path.abspath(ai_in).replace('\\', '/'); O = os.path.abspath(ai_out).replace('\\', '/')
    js = r'''app.userInteractionLevel=UserInteractionLevel.DONTDISPLAYALERTS;
var d=app.open(File("%s")); var SW=%f, MIN=%f*72/25.4, rep={box:0,pageclip:0,offboard:0,unclip:0,paths:0,small:[]}; try{
var K=new RGBColor(); K.red=0;K.green=0;K.blue=0;
function onboard(b){ for(var a=0;a<d.artboards.length;a++){ var r=d.artboards[a].artboardRect;
  if(b[0]<r[2]&&b[2]>r[0]&&b[1]>r[3]&&b[3]<r[1]) return true; } return false; }
function pageclip(p){ if(p.typename!="PathItem"||!p.clipping) return false;   // PDF 가 붙이는 «쪽 전체» 클립 네모 — 따면 큰 사각형이 하나 더 나온다
  var b=p.geometricBounds, r=d.artboards[0].artboardRect; return (b[2]-b[0])>=0.95*(r[2]-r[0]) && (b[1]-b[3])>=0.95*(r[1]-r[3]); }
function grad(p){ return p.typename=="PathItem"&&p.filled&&p.fillColor.typename=="GradientColor"&&!p.clipping; }
for(var t=d.textFrames.length-1;t>=0;t--) d.textFrames[t].createOutline();
// ① 대지 밖 · 숨김 지우기
for(var L=0;L<d.layers.length;L++){ var ly=d.layers[L]; ly.locked=false; ly.visible=true;
  for(var i=ly.pageItems.length-1;i>=0;i--){ var it=ly.pageItems[i]; it.locked=false;
    if(it.hidden||!onboard(it.geometricBounds)){ it.remove(); rep.offboard++; } } }
// ② 클립 그룹 풀기 + 그라디언트 네모 지우기
function walk(g){ for(var i=g.pageItems.length-1;i>=0;i--){ var it=g.pageItems[i];
  if(it.typename=="GroupItem"){ if(it.clipped){ rep.unclip++;
      // 🔴 clipped=false 는 스크립트에서 9045·9046 으로 막힌다 — 안의 것을 그룹 앞으로 꺼내고 네모는 버리고 빈 그룹을 지운다
      for(var k=it.pageItems.length-1;k>=0;k--){ var c=it.pageItems[k]; if(grad(c)){ c.remove(); rep.box++; } else if(pageclip(c)){ c.remove(); rep.pageclip++; } else c.move(it, ElementPlacement.PLACEBEFORE); }
      it.remove(); } else walk(it); } } }
for(var L=0;L<d.layers.length;L++) walk(d.layers[L]);
// ③ 모든 패스 → 칠 없음 + 검정 선
for(var i=d.pathItems.length-1;i>=0;i--){ var p=d.pathItems[i];
  var b=p.geometricBounds, w=b[2]-b[0], h=b[1]-b[3];
  if(MIN>0&&Math.max(w,h)<MIN&&p.parent.typename!="CompoundPathItem"){ rep.small.push([Math.round(w*25.4/72*10)/10,Math.round(h*25.4/72*10)/10]); p.remove(); continue; }
  p.clipping=false; p.filled=false; p.stroked=true; p.strokeColor=K; p.strokeWidth=SW; rep.paths++; }
var o=new IllustratorSaveOptions(); o.pdfCompatible=true; d.saveAs(new File("%s"), o);
} finally { d.close(SaveOptions.DONOTSAVECHANGES); app.userInteractionLevel=UserInteractionLevel.DISPLAYALERTS; }   // 🔴 실패해도 «이 문서만» 닫는다
"{\"box\":"+rep.box+",\"pageclip\":"+rep.pageclip+",\"offboard\":"+rep.offboard+",\"unclip\":"+rep.unclip+",\"paths\":"+rep.paths+",\"small_mm\":["+rep.small.join("],[").replace(/^(.+)$/,"[$1]")+"]}";''' % (
        I, stroke_pt, min_mm, O)
    try:
        app = w32.GetActiveObject('Illustrator.Application')
    except Exception:
        app = w32.Dispatch('Illustrator.Application')
    r = app.DoJavaScript(js)
    r = json.loads(r)
    r['ai'] = ai_out
    return r


# ───────────────────────── corners (곧은 테두리 사이 둥근 모서리) ─────────────────────────
# 🔴 «회전하는 곳도 그렇던데» (2026-10-04, 고객H). 일러 화면으로 직접 보니 «층»은 둥근 모서리가 곧은 테두리보다 바깥으로
#    불거졌다 꺾이거나(ㄹ 가운데 오른쪽 · 22°) 아래로 처진 발(ㅁ 왼쪽 아래)이었다 — potrace 가 붓글씨풍 원안을 그대로 딴 흔적.
# 곧은 테두리 두 개(45~135°) 사이의 곡선 줄기를 «두 직선에 접하는 깨끗한 원호 하나»로 바꾼다. 반지름 = 짧은 쪽 다리(XP·XQ 중 작은 것),
# 상한 cap. 바깥으로 튀어나온 «귀»(교점을 넘어선 다리)와 이미 대칭인 둥근 끝(다리 비 < sym)은 두지만, 꺾임(kink°↑)이 있으면 고친다.
_CORNER = dict(lo=45.0, hi=135.0, sym=1.6, cap=12.0, kink=8.0, maxspan=6, min_line=10.0)
# min_line: 이보다 짧은 직선은 «테두리»가 아니라 모서리 줄기의 일부로 본다 — ㄹ 의 22° 꺾임은 세로 테두리 끝에 낀 6.4pt 비스듬한 직선이었다.


def _corners(pts, log, C=_CORNER, humps=True):
    import math
    P = [list(q) + [0] * (7 - len(q)) for q in pts]; n = len(P)
    def isl(k):
        a, b = P[k % n], P[(k + 1) % n]
        return (abs(a[4] - a[0]) < 1e-6 and abs(a[5] - a[1]) < 1e-6 and abs(b[2] - b[0]) < 1e-6 and abs(b[3] - b[1]) < 1e-6
                and math.hypot(b[0] - a[0], b[1] - a[1]) >= C['min_line'])
    unit = lambda v: (lambda l: (v[0] / l, v[1] / l))(math.hypot(*v) or 1e-9)
    def kinked(i, j):                                       # 줄기 안·양 끝에 꺾임이 있나
        for k in range(i, j + 1):
            q = P[k % n]; a = (q[2] - q[0], q[3] - q[1]); b = (q[4] - q[0], q[5] - q[1])
            if k == i or math.hypot(*a) < 1e-6: a = (P[(k - 1) % n][0] - q[0], P[(k - 1) % n][1] - q[1])   # 핸들 없으면(직선 끝) 이웃 앵커 쪽
            if k == j or math.hypot(*b) < 1e-6: b = (P[(k + 1) % n][0] - q[0], P[(k + 1) % n][1] - q[1])
            la, lb = math.hypot(*a), math.hypot(*b)
            if la < 1e-6 or lb < 1e-6: continue
            c = -(a[0] * b[0] + a[1] * b[1]) / (la * lb)
            if math.degrees(math.acos(max(-1, min(1, c)))) > C['kink']: return True
        return False
    jobs = []
    for i in range(n):
        if not isl(i - 1) or isl(i): continue
        j = i
        while not isl(j) and j - i < C['maxspan']: j += 1
        if not isl(j) or j == i: continue
        A0, Pp, Q, B1 = P[(i - 1) % n], P[i % n], P[j % n], P[(j + 1) % n]
        d1 = unit((Pp[0] - A0[0], Pp[1] - A0[1])); d2 = unit((B1[0] - Q[0], B1[1] - Q[1]))
        ang = math.degrees(math.acos(max(-1, min(1, d1[0] * d2[0] + d1[1] * d2[1]))))
        if not C['lo'] <= ang <= C['hi']: continue
        den = d1[0] * d2[1] - d1[1] * d2[0]
        s = ((Q[0] - Pp[0]) * d2[1] - (Q[1] - Pp[1]) * d2[0]) / den; t = ((Q[0] - Pp[0]) * d1[1] - (Q[1] - Pp[1]) * d1[0]) / den
        XP, XQ = s, -t
        if XP <= 0.5 or XQ <= 0.5: continue                 # 귀(교점을 넘어 튀어나온 붓 머리) — 디자인으로 둔다
        sym = max(XP, XQ) / min(XP, XQ) < C['sym']
        kink = kinked(i, j)
        if sym and not kink: continue                       # 이미 깨끗한 둥근 끝
        if not humps and not kink and max(XP, XQ) / min(XP, XQ) >= C['sym']:
            pass                                            # humps=False 여도 «처진 발·꺾임»은 고친다 — 아래에서 혹만 거른다
        X = (Pp[0] + s * d1[0], Pp[1] + s * d1[1])
        # 혹(바깥으로 솟음) 판정: 줄기 중간점이 교점 X 보다 모서리 바깥(두 직선의 바깥쪽)에 있으면 혹
        mid = P[((i + j) // 2) % n] if j - i > 1 else [(Pp[0] + Q[0]) / 2, (Pp[1] + Q[1]) / 2]
        out = ((mid[0] - X[0]) * (d1[0] - d2[0]) + (mid[1] - X[1]) * (d1[1] - d2[1])) > 0   # 모서리 바깥 = d1−d2 쪽
        if out and not humps and not kink: continue
        r = min(XP, XQ, C['cap'])
        k = 4 / 3 * math.tan(math.radians(ang) / 4)
        P1 = (X[0] - d1[0] * r, X[1] - d1[1] * r); Q1 = (X[0] + d2[0] * r, X[1] + d2[1] * r)
        if r > min(XP, XQ) + 1e-6: continue
        jobs.append((i % n, j - i, P1, Q1, (P1[0] + d1[0] * k * r, P1[1] + d1[1] * k * r), (Q1[0] - d2[0] * k * r, Q1[1] - d2[1] * k * r),
                     dict(corner=[round(X[0], 1), round(X[1], 1)], XP=round(XP, 1), XQ=round(XQ, 1), r=round(r, 1), kink=kink, hump=out)))
    drop = set(); setp = {}
    for i, span, P1, Q1, h1, h2, info in jobs:
        if any(((i + m) % n) in drop or ((i + m) % n) in setp for m in range(span + 1)): continue
        setp[i] = [P1[0], P1[1], P1[0], P1[1], h1[0], h1[1], 1]
        setp[(i + span) % n] = [Q1[0], Q1[1], h2[0], h2[1], Q1[0], Q1[1], 1]
        for m in range(1, span): drop.add((i + m) % n)
        log.append(info)
    return [setp.get(k, P[k]) for k in range(n) if k not in drop]
