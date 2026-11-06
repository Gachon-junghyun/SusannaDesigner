# -*- coding: utf-8 -*-
"""원본 받기부터 손님에게 넘기기까지 — 키우기 · 크게 보기 · 나란히 보기 · 내보내기(.ai·.pdf·.png) · 폰으로 보내기.

전부 아담 왕관(2026-09-28)에서 손으로 여러 번 한 것이다. 같은 걸 또 손으로 짜지 않게 한 칸씩 묶었다.
- upscale: 작은 원본(154px 자수 사진)을 Real-ESRGAN 으로 4배. 제미나이에 `--ref` 로 주면 밑단이 원본처럼 두툼하게 나왔다.
- look:    SVG·PDF·AI·PNG 를 «크게» 그려 본다. 🔴 1024 로 보면 오돌토돌이 안 보여 «됐다»로 넘긴다 — 2000px 이상 + 확대 칸.
- strip:   원본과 후보를 한 줄로. 사람에게 «뭐가 달라졌나»를 한 장으로 보여 준다.
- export:  SVG → .pdf · .png · .ai(이 PC 의 일러스트레이터로 «진짜» .ai) · 폰(텔레그램).
"""
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

ESRGAN = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', 'realesrgan-ncnn-vulkan', 'realesrgan-ncnn-vulkan.exe')
ESRGAN_URL = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-windows.zip'
AGENT = os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent'))     # module_voice(텔레그램) 가 있는 리포


def _ascii_tmp():
    """🔴 realesrgan exe·일러스트 COM 은 한글 경로를 못 읽는다(decode image failed) — 영문 임시 폴더에서 돌린다."""
    base = os.environ.get('TEMP') or tempfile.gettempdir()
    try:
        base.encode('ascii')
    except UnicodeEncodeError:
        base = r'C:\Windows\Temp'
    return tempfile.mkdtemp(prefix='ad_', dir=base)


def upscale(src, out, model='realesrgan-x4plus'):
    """작은 그림 → 4배. 모델: realesrgan-x4plus(사진·자수 — 가장자리·줄무늬를 살렸다) · realesrgan-x4plus-anime(평면 그림 — 자수 별을 찌그러뜨렸다)."""
    if not os.path.exists(ESRGAN):
        raise SystemExit(f'Real-ESRGAN 이 없다 — 받는 건 사람 허락 뒤: {ESRGAN_URL}\n  풀 자리: {os.path.dirname(ESRGAN)}')
    t = _ascii_tmp()
    try:
        Image.open(src).convert('RGB').save(os.path.join(t, 'in.png'))
        r = subprocess.run([ESRGAN, '-i', os.path.join(t, 'in.png'), '-o', os.path.join(t, 'out.png'), '-n', model],
                           cwd=os.path.dirname(ESRGAN), capture_output=True)
        if not os.path.exists(os.path.join(t, 'out.png')):
            raise SystemExit('업스케일 실패: ' + (r.stderr or b'').decode('utf-8', 'replace')[-300:])
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        shutil.copy(os.path.join(t, 'out.png'), out)
    finally:
        shutil.rmtree(t, ignore_errors=True)
    return Image.open(out).size


def _page(path):
    """SVG·PDF·AI → PyMuPDF 한 쪽. (.ai 는 PDF 호환이라 filetype='pdf' 로 연다)"""
    import fitz
    ext = os.path.splitext(path)[1].lower()
    if ext == '.svg':
        return fitz.open('pdf', fitz.open(path).convert_to_pdf())[0]
    return fitz.open(path, filetype='pdf')[0]


def look(path, out, px=2000, zoom=None, zoom_px=2000):
    """크게 그려 본다. zoom='x0,y0,x1,y1'(0~1 비율)이면 그 칸만 zoom_px 폭으로 따로 떨군다(out 이름에 _zoom)."""
    import fitz
    ext = os.path.splitext(path)[1].lower()
    outs = []
    if ext in ('.png', '.jpg', '.jpeg', '.webp'):
        im = Image.open(path).convert('RGB')
        im.resize((px, round(im.height * px / im.width)), Image.LANCZOS).save(out); outs.append(out)
        if zoom:
            x0, y0, x1, y1 = [float(v) for v in zoom.split(',')]
            c = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
            zo = os.path.splitext(out)[0] + '_zoom.png'
            c.resize((zoom_px, round(c.height * zoom_px / c.width)), Image.LANCZOS).save(zo); outs.append(zo)
        return outs
    pg = _page(path)
    r = pg.rect
    z = px / r.width
    pg.get_pixmap(matrix=fitz.Matrix(z, z)).save(out); outs.append(out)
    if zoom:
        x0, y0, x1, y1 = [float(v) for v in zoom.split(',')]
        clip = fitz.Rect(r.x0 + x0 * r.width, r.y0 + y0 * r.height, r.x0 + x1 * r.width, r.y0 + y1 * r.height)
        z2 = zoom_px / clip.width
        zo = os.path.splitext(out)[0] + '_zoom.png'
        pg.get_pixmap(matrix=fitz.Matrix(z2, z2), clip=clip).save(zo); outs.append(zo)
    return outs


def strip(paths, out, h=500, gap=12):
    """여러 장을 같은 높이로 한 줄에. 벡터(SVG·PDF·AI)도 받는다."""
    import fitz
    ims = []
    for p in paths:
        if os.path.splitext(p)[1].lower() in ('.svg', '.pdf', '.ai'):
            pg = _page(p)
            z = h / pg.rect.height
            pix = pg.get_pixmap(matrix=fitz.Matrix(z, z))
            im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        else:
            im = Image.open(p).convert('RGB')
            im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        ims.append(im)
    W = sum(i.width for i in ims) + gap * (len(ims) - 1)
    sheet = Image.new('RGB', (W, h), 'white')
    x = 0
    for i in ims:
        sheet.paste(i, (x, 0)); x += i.width + gap
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    sheet.save(out)
    return sheet.size


_PS_AI = r'''$ErrorActionPreference = 'Stop'
$app = New-Object -ComObject Illustrator.Application
$doc = $app.Open($args[0])
$opts = New-Object -ComObject Illustrator.IllustratorSaveOptions
$doc.SaveAs($args[1], $opts)
$doc.Close(2)
'''


def to_ai(svg, out_ai):
    """SVG → «진짜» .ai — 이 PC 의 일러스트레이터(COM)로 열어 저장한다. PDF 이름만 바꾼 가짜가 아니다.
    일러가 처음 뜨면 수십 초 걸린다. 🔴 스크립트·경로는 영문만(PowerShell 5.1 이 BOM 없는 .ps1 을 cp949 로 읽는다 — 헌법 규약)."""
    t = _ascii_tmp()
    try:
        shutil.copy(svg, os.path.join(t, 'in.svg'))
        ps = os.path.join(t, 'toai.ps1')
        open(ps, 'w', encoding='ascii').write(_PS_AI)
        r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ps,
                            os.path.join(t, 'in.svg'), os.path.join(t, 'out.ai')], capture_output=True, timeout=600)
        if not os.path.exists(os.path.join(t, 'out.ai')):
            raise SystemExit('.ai 저장 실패(일러스트레이터가 없거나 COM 이 막힘): ' + (r.stderr or b'').decode('cp949', 'replace')[-300:])
        shutil.copy(os.path.join(t, 'out.ai'), out_ai)
    finally:
        shutil.rmtree(t, ignore_errors=True)
    return out_ai


def to_phone(paths, caption=''):
    """텔레그램으로 파일 첨부(module_voice.push_file). 🔴 한 번은 RemoteDisconnected 로 끊겼다 — 두 번까지 다시 보낸다."""
    sys.path.insert(0, AGENT)
    from module_voice import _push
    bad = []
    for p in paths:
        err = None
        for _ in range(3):
            err = _push.push_file(p, (caption + ' — ' if caption else '') + os.path.basename(p))
            if err is None:
                break
        if err:
            bad.append((p, err))
    return bad


def export(svg, ai=True, pdf=True, png=True, px=2000, phone=False, caption=''):
    """SVG 옆에 같은 이름으로 .pdf · .png · .ai 를 떨군다. phone 이면 .ai·.pdf 를 폰으로."""
    import fitz
    stem = os.path.splitext(svg)[0]
    made = []
    if pdf:
        open(stem + '.pdf', 'wb').write(fitz.open(svg).convert_to_pdf()); made.append(stem + '.pdf')
    if png:
        look(svg, stem + '.png', px=px); made.append(stem + '.png')
    if ai:
        made.append(to_ai(svg, stem + '.ai'))
    bad = to_phone([m for m in made if m.endswith(('.ai', '.pdf'))], caption) if phone else []
    return made, bad
