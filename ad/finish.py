# -*- coding: utf-8 -*-
"""마감 표현 — 같은 로고를 «평면 기법»(flatfx) 또는 «Blender 입체»(render3d)로 한 벌 더 찍는다.

왜 있나 (2026-09-28): 앱스토어 아이콘 30개를 뜯어 보니 디테일이 두 갈래였다 —
  ① 평면 벡터 기법(한 색 면·바탕 흐름·톤 겹쳐 쌓기·반투명 겹침·롱섀도·테·그려 넣은 광택) — 대부분이 이쪽
  ② 진짜 입체 렌더(크롬·먹색 광택·유리·빛) — ChatGPT·집지켜 같은 소수
사람이 둘 다 보고 *"렌더링스럽긴 한데 이쁘다 … 2D 느낌이 강하니 전통 방식도"* 라고 해서, 둘 다 아무 로고 SVG 에 걸 수 있게 했다.
실험 원본: runs/2026-09-28_로고빛/(LOG.md). 디자인 나무 «평면으로 둘까, 입체로 보일까?» 의 샘플이 여기서 나왔다.

🔴 평면판이 원본이다. 이 명령들이 만드는 건 «화면용 한 벌»이지 간판 재단 파일이 아니다 — 재단은 원래 SVG 로.
"""
import io
import math
import os
import re
import shutil
import subprocess
import tempfile

from . import svgio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPER = '#f3eee6'
FLAT_STYLES = ('solid', 'bg_grad', 'mark_grad', 'tone', 'overlap', 'longshadow', 'ring', 'gloss')
RENDER_STYLES = ('flat', 'chrome', 'ink', 'glass', 'front', 'halo', 'glow')


# ─────────── 공통 ───────────
def _chrome():
    """헤드리스로 SVG 를 찍을 브라우저 — 크롬, 없으면 엣지. 🔴 경로를 문서에 박지 마라(PC 마다 다르다)."""
    for p in (os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
              os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
              os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
              os.path.expandvars(r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe')):
        if os.path.exists(p):
            return p
    raise SystemExit('크롬·엣지를 못 찾았다 — SVG 를 PNG 로 찍을 브라우저가 필요하다')


def shoot(svg_path, png_path, w, h):
    subprocess.run([_chrome(), '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size={w},{h}',
                    f'--screenshot={os.path.abspath(png_path)}', 'file:///' + os.path.abspath(svg_path).replace('\\', '/')],
                   capture_output=True, timeout=90)
    if not os.path.exists(png_path):
        raise SystemExit(f'찍기 실패: {png_path}')
    return png_path


def _circle_path(cx, cy, r):
    k = 0.5523 * r
    return (f'M{cx - r},{cy} C{cx - r},{cy - k} {cx - k},{cy - r} {cx},{cy - r} C{cx + k},{cy - r} {cx + r},{cy - k} {cx + r},{cy} '
            f'C{cx + r},{cy + k} {cx + k},{cy + r} {cx},{cy + r} C{cx - k},{cy + r} {cx - r},{cy + k} {cx - r},{cy} Z')


def layers_of(svg_path):
    """svgio.read 는 <path> 만 본다 — 드로우사인 점처럼 <circle> 로 된 조각도 경로로 바꿔 더한다."""
    layers, vb = svgio.read(svg_path)
    s = io.open(svg_path, encoding='utf-8').read()
    for tag in re.findall(r'<circle[^>]*>', s):
        g = {k: float(v) for k, v in re.findall(r'\s(cx|cy|r)="([-\d.]+)"', tag)}
        f = re.search(r'fill="([^"]+)"', tag)
        if 'r' in g and (not f or f.group(1) not in ('none', 'transparent')):
            layers.append((_circle_path(g.get('cx', 0), g.get('cy', 0), g['r']), f.group(1) if f else '#000000'))
    if not layers:
        raise SystemExit(f'{svg_path}: 채운 경로가 없다')
    return layers, vb


def _area(d):
    x0, y0, x1, y1 = svgio.bbox(d)
    return (x1 - x0) * (y1 - y0)


def roles(layers):
    """가장 넓은 색 = 대표(main), 나머지 = 포인트(accent)."""
    by = {}
    for d, c in layers:
        by[c.lower()] = by.get(c.lower(), 0) + _area(d)
    main = max(by, key=by.get)
    return main, [c for c in by if c != main]


def _canvas(layers):
    xs0, ys0, xs1, ys1 = zip(*(svgio.bbox(d) for d, _ in layers))
    x0, y0, x1, y1 = min(xs0), min(ys0), max(xs1), max(ys1)
    lw, lh = x1 - x0, y1 - y0
    W, H = (1600, 900) if lw / lh > 1.6 else (1024, 1024)
    s = min(W * 0.6 / lw, H * 0.55 / lh)
    tx, ty = (W - lw * s) / 2 - x0 * s, (H - lh * s) / 2 - y0 * s
    return W, H, s, tx, ty, (x0 * s + tx, y0 * s + ty, x1 * s + tx, y1 * s + ty)


def _mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _hex6(c):
    c = c.strip()
    if re.fullmatch(r'#[0-9a-fA-F]{3}', c):
        c = '#' + ''.join(ch * 2 for ch in c[1:])
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', c):
        raise SystemExit(f'색은 #rrggbb 로 — {c}')
    return c.lower()


# ─────────── 평면 ───────────
def flatfx(svg_path, style, out_png, *, color=None, bg=None):
    """평면 기법 한 가지를 입혀 SVG+PNG 로. color = 로고 대표색(기본: 원본에서 가장 넓은 색), bg = 바탕."""
    if style not in FLAT_STYLES:
        raise SystemExit(f'모르는 평면 기법: {style} — {", ".join(FLAT_STYLES)}')
    layers, _ = layers_of(svg_path)
    main, acc = roles(layers)
    main = _hex6(color or main)
    accent = _hex6(acc[0]) if acc else _mix(main, '#e8826a', 0.6)
    dark = _mix(main, '#000000', 0.35)
    W, H, s, tx, ty, (bx0, by0, bx1, by1) = _canvas(layers)
    T = f'translate({tx:.2f},{ty:.2f}) scale({s:.5f})'

    orig_main = roles(layers)[0]

    def logo(fm=None, fa=None, dx=0, dy=0, extra=''):
        """fm 없음 = 원래 색 · fm 만 = 전부 그 색 · fm+fa = 대표 조각은 fm, 포인트 조각은 fa."""
        out = []
        for d, c in layers:
            f = c if fm is None else (fm if fa is None or c.lower() == orig_main else fa)
            out.append(f'<path fill-rule="evenodd" d="{d}" fill="{f}"/>')
        return f'<g transform="translate({dx},{dy}) {T}" {extra}>' + ''.join(out) + '</g>'

    def rect(fill):
        return f'<rect width="{W}" height="{H}" fill="{fill}"/>'

    defs, body = '', ''
    if style == 'solid':
        body = rect(_hex6(bg or main)) + logo(PAPER, _mix(accent, '#ffffff', 0.55))
    elif style == 'bg_grad':
        defs = (f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{_mix(main, "#ffffff", 0.25)}"/>'
                f'<stop offset="1" stop-color="{dark}"/></linearGradient>')
        body = rect('url(#g)') + logo('#ffffff', '#ffffff')
    elif style == 'mark_grad':
        defs = (f'<linearGradient id="g" gradientUnits="userSpaceOnUse" x1="{bx0}" y1="{by0}" x2="{bx1}" y2="{by1}">'
                f'<stop offset="0" stop-color="#17161a"/><stop offset="1" stop-color="{main}"/></linearGradient>')
        body = rect(_hex6(bg or PAPER)) + logo('url(#g)', accent)
    elif style == 'tone':
        k = max(4, (by1 - by0) * 0.02)
        # 🔴 포인트 조각은 자기 색의 짙은 톤으로 — 전부 대표색 톤으로 깔았더니 와인 점 뒤에 먹 점이 붙었다(1차)
        body = (rect(_hex6(bg or PAPER)) + logo(_mix(main, '#000000', 0.5), _mix(accent, '#000000', 0.5), 2 * k, 2 * k)
                + logo(dark, _mix(accent, '#000000', 0.3), k, k) + logo())
    elif style == 'overlap':
        k = (bx1 - bx0) * 0.08 if W == 1024 else (by1 - by0) * 0.08
        body = (rect(_hex6(bg or '#ffffff')) + logo('#e0735f', None, k, 0, 'fill-opacity="0.75"')
                + logo(main, None, 0, 0, 'fill-opacity="0.75" style="mix-blend-mode:multiply"'))
    elif style == 'longshadow':
        L = int(max(W, H) * 0.55)
        defs = (f'<linearGradient id="sh" gradientUnits="userSpaceOnUse" x1="{bx0}" y1="{by0}" x2="{bx0 + L}" y2="{by0 + L}">'
                f'<stop offset="0" stop-color="{dark}"/><stop offset="1" stop-color="{main}"/></linearGradient>')
        body = rect(main) + ''.join(logo('url(#sh)', None, k, k) for k in range(2, L, 3)) + logo(PAPER)
    elif style == 'ring':
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        r = math.hypot(bx1 - bx0, by1 - by0) / 2 + min(W, H) * 0.05
        body = (rect(_hex6(bg or PAPER)) + f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{main}" stroke-width="{min(W, H) * 0.03}"/>'
                + logo())
    elif style == 'gloss':
        clip = ''.join(f'<path fill-rule="evenodd" clip-rule="evenodd" d="{d}"/>' for d, _ in layers)
        defs = ('<radialGradient id="bg" cx="0.5" cy="0.42" r="0.75"><stop offset="0" stop-color="#f4f3f2"/><stop offset="1" stop-color="#b9b8ba"/></radialGradient>'
                f'<linearGradient id="body" gradientUnits="userSpaceOnUse" x1="0" y1="{by0}" x2="0" y2="{by1}">'
                f'<stop offset="0" stop-color="{_mix(main, "#ffffff", 0.25)}"/><stop offset="0.45" stop-color="{main}"/>'
                f'<stop offset="1" stop-color="{_mix(main, "#000000", 0.7)}"/></linearGradient>'
                '<filter id="blur" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="16"/></filter>'
                f'<clipPath id="lc" transform="{T}">{clip}</clipPath>')
        body = (rect('url(#bg)') + logo('#000000', None, 0, (by1 - by0) * 0.03, 'fill-opacity="0.35" filter="url(#blur)"')
                + logo('url(#body)', accent)
                + f'<g clip-path="url(#lc)"><ellipse cx="{bx0 + (bx1 - bx0) * 0.25}" cy="{by0}" rx="{(bx1 - bx0) * 0.9}" ry="{(by1 - by0) * 0.45}" fill="#fff" fill-opacity="0.16"/></g>')
    doc = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs>{defs}</defs>{body}</svg>'
    sp = os.path.splitext(out_png)[0] + '.svg'
    io.open(sp, 'w', encoding='utf-8').write(doc)
    return shoot(sp, out_png, W, H)


# ─────────── 입체 ───────────
def render3d(svg_path, style, out_png, *, samples=128, size=None, degaja=None):
    """Blender(Cycles·OptiX) 로 입체 한 장. 씬은 sim/scene_logo3d.py — DeGaJa_Agent 의 module_render 로 돌린다."""
    if style not in RENDER_STYLES:
        raise SystemExit(f'모르는 입체 기법: {style} — {", ".join(RENDER_STYLES)}')
    # ROOT 의 형제 폴더로 찾는다(2026-10-19 STARTUP/aidesigner → <작업 폴더> 로 옮겨 한 단계 얕아졌다)
    degaja = degaja or os.environ.get('DEGAJA_ROOT') or os.path.join(os.path.dirname(ROOT), 'DeGaJa_Agent')
    if not os.path.isdir(os.path.join(degaja, 'module_render')):
        raise SystemExit(f'module_render 를 못 찾았다({degaja}) — --degaja 로 DeGaJa_Agent 경로를 줘라')
    layers, _ = layers_of(svg_path)
    # Blender SVG 임포터는 <circle> 도 읽지만 색·스케일이 섞이지 않게 경로만 있는 SVG 로 한 번 정리해 넘긴다
    tmp = tempfile.mkdtemp(prefix='ad_r3d_')
    flat_svg = os.path.join(tmp, 'logo.svg')
    xs0, ys0, xs1, ys1 = zip(*(svgio.bbox(d) for d, _ in layers))
    vb = (min(xs0), min(ys0), max(xs1) - min(xs0), max(ys1) - min(ys0))
    io.open(flat_svg, 'w', encoding='utf-8').write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]} {vb[1]} {vb[2]} {vb[3]}">'
        + ''.join(f'<path fill-rule="evenodd" fill="{c}" d="{d}"/>' for d, c in layers) + '</svg>')
    main, _ = roles(layers)
    wide = vb[2] / vb[3] > 1.6
    w, h = (size, size) if size else ((1600, 900) if wide else (1024, 1024))
    scene = os.path.join(ROOT, 'sim', 'scene_logo3d.py')
    cmd = ['python', '-m', 'module_render', 'run', scene, '--', '--svg', flat_svg, '--look', style, '--main', main,
           '--out', os.path.abspath(out_png), '--samples', str(samples), '--w', str(w), '--h', str(h)]
    r = subprocess.run(cmd, cwd=degaja, capture_output=True, text=True, encoding='utf-8', errors='replace')
    shutil.rmtree(tmp, ignore_errors=True)
    if r.returncode != 0 or not os.path.exists(out_png):
        tail = '\n'.join((r.stdout + r.stderr).splitlines()[-15:])
        raise SystemExit(f'렌더 실패 (rc={r.returncode})\n{tail}')
    return out_png
