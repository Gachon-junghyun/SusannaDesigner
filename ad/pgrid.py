# -*- coding: utf-8 -*-
"""포스터 레퍼런스 해부 — 그리드를 그려 «글자 크기 ↔ 그림 자리»를 잰다.

detect  : 그림 → 글줄(OCR + 실제 잉크 높이) · 그림 덩어리 상자 → blocks.json + detect.png
          🔴 자동 상자는 «초안»이다. detect.png 를 눈으로 보고 blocks.json 을 고친 뒤 analyze 로 간다.
fix     : 눈으로 본 뒤 고치기 한 번에(drop · set · merge · add · retight — fix() 머리말)
analyze : blocks.json → 여백 · 정렬축 · 단 그리드 맞추기 · 글자 크기 사다리 · 그림 자리 · 글-그림 관계 · 색·모양·질감(style)
          → analysis.json + grid.png(그리드 덮개) + style.png + REPORT.md
summary : 해부 폴더 여럿 → 숫자 모음표 + 그림·글자 자리 열지도(heat.png) + 색 띠(palettes.png) → SUMMARY.md

글자 크기는 «잉크 높이»로 잰다(윗끝 ~ 기준선: 대문자·숫자 줄 = 캡 높이, 소문자 섞인 줄 = 어센더 높이, 내림은 뺀다, 한글 = 네모틀 높이).
포인트 크기는 그림만으로 알 수 없어서 쓰지 않는다 — 비율(판 높이 대비 %, 단계 사이 배율)로만 말한다.
"""
import json
import os
import re
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = r'C:\Windows\Fonts\malgun.ttf'
SCALES = [(1.125, '장2도'), (1.2, '단3도'), (1.25, '장3도'), (1.333, '완전4도'), (1.414, '증4도'),
          (1.5, '완전5도'), (1.6, '단6도'), (1.618, '황금비'), (2.0, '옥타브'), (2.5, '2.5배'), (3.0, '3배')]
HEAT = (12, 16)                                    # 열지도 칸(가로 12 · 세로 16)
_READER = None


def _font(px):
    try:
        return ImageFont.truetype(FONT, max(10, int(px)))
    except OSError:
        return ImageFont.load_default()


def _reader():
    global _READER
    if _READER is None:
        import easyocr, torch                      # 무거운 의존은 함수 안에서만
        _READER = easyocr.Reader(['ko', 'en'], gpu=torch.cuda.is_available(), verbose=False)
    return _READER


# ───────────────────────── 받기 ─────────────────────────

def _auto_crop(arr):
    """목업 사진(벽·그림자 위 포스터)이면 포스터 판만 잘라 낸다. 판이 화면 전체면 그대로."""
    import cv2
    h, w = arr.shape[:2]
    ring = np.concatenate([arr[:max(2, h // 50)].reshape(-1, 3), arr[-max(2, h // 50):].reshape(-1, 3),
                           arr[:, :max(2, w // 50)].reshape(-1, 3), arr[:, -max(2, w // 50):].reshape(-1, 3)])
    if ring.std(axis=0).mean() > 18:               # 가장자리가 고르지 않다 = 판이 화면을 꽉 채움
        return None
    bg = np.median(ring, axis=0)
    m = (np.linalg.norm(arr.astype(float) - bg, axis=2) > 60).astype(np.uint8)   # 30 이면 목업 그림자까지 딸려 온다(루체른)
    k = max(3, min(h, w) // 100)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    n, _, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return None
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    x, y, bw, bh = st[i, :4]
    if bw * bh < 0.2 * w * h or bw * bh > 0.97 * w * h:
        return None
    return [int(x), int(y), int(x + bw), int(y + bh)]


def _ink(arr, box, color=None, rot=False, tol=70):
    """OCR 상자 → 실제 잉크가 있는 상자와 잉크 색. OCR 상자는 위아래로 여유가 붙어 크기 판단에 못 쓴다.
    🔴 가장 많은 잉크 «색 하나»만, 그리고 이어진 줄 «한 덩어리»만 잰다 — 행간이 좁으면 옆줄 글자가,
    글 위로 선이 지나가면 그 선이 상자를 키운다(호프만 Kunst/halle · 스위스에어 DC-6B 위 빨간 비행기 선, 10-20)."""
    if rot:                                          # 세로로 돌린 글줄: 판을 눕혀 재고 상자를 되돌린다(잉크 높이 = 가로 두께)
        x0, y0, x1, y1 = box
        r, c = _ink(np.ascontiguousarray(arr.transpose(1, 0, 2)), [y0, x0, y1, x1], color, False, tol)
        return [r[1], r[0], r[3], r[2]], c
    h, w = arr.shape[:2]
    x0, y0, x1, y1 = box
    pad = max(2, int((y1 - y0) * 0.12))
    X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(w, x1 + pad), min(h, y1 + pad)
    c = arr[Y0:Y1, X0:X1].astype(float)
    edge = np.concatenate([c[0], c[-1], c[:, 0], c[:, -1]])
    bg = np.median(edge, axis=0)
    d = np.linalg.norm(c - bg, axis=2)
    if d.max() < 25 and not color:
        return list(box), None
    if color:                                        # 글자 색을 사람이 짚어 줬으면 그 색만(사진 위 글자 — 사진의 어두운 곳이 잉크로 잡힌다, 10-20 In The Park)
        top = np.array([int(color.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)
        m = np.linalg.norm(c - top, axis=2) < tol
    else:
        m = d > max(25, 0.5 * np.percentile(d, 99))
        px = c[m]
        q = (px // 48).astype(int)
        keys, cnt = np.unique(q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2], return_counts=True)
        top = px[(q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]) == keys[np.argmax(cnt)]].mean(axis=0)
        m &= np.linalg.norm(c - top, axis=2) < tol
    rs = m.sum(1)
    rowm = rs > max(1, 0.08 * rs.max())          # 🔴 «폭의 1%» 로 하면 붙어 있는 이웃 줄의 획 끝 몇 점이 다리를 놓는다(호프만 76px → 실제 56px)
    # 이어진 줄 덩어리 중 잉크가 가장 많은 것(빈 줄이 하나라도 있으면 끊는다 — 악센트·i 점은 빠져도 된다, 재는 건 대문자·어센더 높이)
    runs, cur, gap = [], None, 0
    for i, on in enumerate(rowm):
        if on:
            if cur and i - cur[1] <= gap + 1:
                cur[1] = i
            else:
                cur = [i, i]; runs.append(cur)
    if not runs:
        return list(box), None
    r0, r1 = max(runs, key=lambda r: m[r[0]:r[1] + 1].sum())
    # 기준선에서 자른다: 내림(g·p·y)은 글자 몇 개만 내려가 줄 잉크가 확 줄어든다 — 그 아래는 높이에 안 넣는다
    # («Los Angeles» 가 같은 크기 «San Francisco» 보다 1.4배로 잡혔다, 10-20)
    band = rs[r0:r1 + 1]
    strong = np.where(band >= 0.25 * band.max())[0]
    if len(strong) and r0 + strong[-1] > r0 + 0.6 * (r1 - r0):
        r1 = r0 + int(strong[-1])
    sub = m[r0:r1 + 1]
    cols = np.where(sub.sum(0) > max(1, 0.02 * sub.shape[0]))[0]
    if not len(cols):
        return list(box), None
    col = top
    return [int(X0 + cols[0]), int(Y0 + r0), int(X0 + cols[-1] + 1), int(Y0 + r1 + 1)],         '#%02X%02X%02X' % tuple(int(v) for v in col)


def _merge_lines(words):
    """OCR 낱말 상자 → 한 줄(높이가 비슷하고 같은 높이에 있고 사이가 좁은 것)."""
    words = sorted(words, key=lambda t: (t['bbox'][1], t['bbox'][0]))
    lines = []
    for t in words:
        x0, y0, x1, y1 = t['bbox']
        hh = y1 - y0
        for L in lines:
            a0, b0, a1, b1 = L['bbox']
            lh = b1 - b0
            ov = min(y1, b1) - max(y0, b0)
            gap = max(a0 - x1, x0 - a1)
            if ov > 0.6 * min(hh, lh) and max(hh, lh) / max(1, min(hh, lh)) < 1.3 and gap < 1.2 * max(hh, lh):
                L['bbox'] = [min(a0, x0), min(b0, y0), max(a1, x1), max(b1, y1)]
                L['text'] = (L['text'] + ' ' + t['text']) if x0 >= a0 else (t['text'] + ' ' + L['text'])
                L['conf'] = min(L['conf'], t['conf'])
                break
        else:
            lines.append(dict(t))
    return lines


def _figures(arr, text_boxes):
    """글이 아닌 덩어리(사진·일러·입체) 상자. 바탕색과 다른 곳에서 글 상자를 빼고 뭉친다."""
    import cv2
    h, w = arr.shape[:2]
    s = min(1.0, 800 / max(h, w))
    small = cv2.resize(arr, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA).astype(float)
    sh, sw = small.shape[:2]
    ring = np.concatenate([small[:3].reshape(-1, 3), small[-3:].reshape(-1, 3),
                           small[:, :3].reshape(-1, 3), small[:, -3:].reshape(-1, 3)])
    q = (ring // 24).astype(int)
    keys, cnt = np.unique(q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2], return_counts=True)
    top = keys[np.argmax(cnt)]
    bg = ring[(q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]) == top].mean(axis=0)
    m = (np.linalg.norm(small - bg, axis=2) > 48).astype(np.uint8)
    for x0, y0, x1, y1, ih in text_boxes:
        p = 0.35 * ih
        m[max(0, int((y0 - p) * s)):int((y1 + p) * s) + 1, max(0, int((x0 - p) * s)):int((x1 + p) * s) + 1] = 0
    k = max(3, int(min(sh, sw) * 0.015))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    n, _, st, _ = cv2.connectedComponentsWithStats(m)
    out = []
    for i in range(1, n):
        x, y, bw, bh, area = st[i]
        if area < 0.004 * sh * sw:
            continue
        out.append([int(x / s), int(y / s), int((x + bw) / s), int((y + bh) / s)])
    # 겹치는 상자는 합친다
    merged = True
    while merged:
        merged = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                a, b = out[i], out[j]
                if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                    out[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    out.pop(j)
                    merged = True
                    break
            if merged:
                break
    return '#%02X%02X%02X' % tuple(int(v) for v in bg), out


def detect(img, out, crop='auto', src='', own='남의 것'):
    os.makedirs(out, exist_ok=True)
    im = Image.open(img).convert('RGB')
    arr = np.array(im)
    box = None
    if crop == 'auto':
        box = _auto_crop(arr)
    elif crop and crop != 'none':
        box = [int(v) for v in crop.split(',')]
    if box:
        arr = arr[box[1]:box[3], box[0]:box[2]].copy()
    H, W = arr.shape[:2]
    ext = os.path.splitext(img)[1].lower() or '.png'
    shutil.copy(img, os.path.join(out, '원본' + ext))
    Image.fromarray(arr).save(os.path.join(out, 'poster.png'))     # 🔴 이후 좌표는 전부 이 판 기준
    words = []
    up = max(1, int(np.ceil(1400 / max(W, H))))                     # 작은 그림은 키워서 읽는다(465px 루체른에서 두 줄이 한 줄로 붙었다)
    big = np.array(Image.fromarray(arr).resize((W * up, H * up), Image.LANCZOS)) if up > 1 else arr
    for b, t, c in _reader().readtext(big, paragraph=False):        # 🔴 경로를 주면 cv2 가 한글 경로를 못 연다 — 배열로 준다
        xs, ys = [p[0] / up for p in b], [p[1] / up for p in b]
        words.append({'bbox': [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))], 'text': t, 'conf': round(float(c), 2)})
    items = []
    for L in _merge_lines(words):
        ink, col = _ink(arr, L['bbox'])
        if ink[3] - ink[1] < 6:
            continue
        items.append({'kind': 'text', 'bbox': ink, 'text': L['text'], 'ink_h': ink[3] - ink[1], 'color': col, 'conf': L['conf']})
    bg, figs = _figures(arr, [it['bbox'] + [it['ink_h']] for it in items])
    for f in figs:
        a = (f[2] - f[0]) * (f[3] - f[1]) / (W * H)
        items.append({'kind': 'image', 'bbox': f, 'role': 'bg' if a > 0.85 else ''})
    items.sort(key=lambda t: (t['bbox'][1], t['bbox'][0]))
    for i, it in enumerate(items, 1):
        it['id'] = ('T' if it['kind'] == 'text' else 'I') + str(i)
    doc = {'src': src, 'own': own, 'file': os.path.basename(img), 'crop': box, 'W': W, 'H': H, 'bg': bg,
           'note': 'kind: text | image | logo | rule(선·띠) — 틀린 상자는 고치고, 빠진 건 더하고, 잡음은 지운다',
           'items': items}
    json.dump(doc, open(os.path.join(out, 'blocks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    _draw_boxes(arr, items, os.path.join(out, 'detect.png'))
    return doc


def _draw_boxes(arr, items, path):
    im = Image.fromarray(arr).convert('RGBA')
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    W, H = im.size
    f = _font(max(14, min(W, H) * 0.018))
    lw = max(2, W // 500)
    for it in items:
        c = {'text': (0, 200, 255), 'image': (255, 40, 170), 'logo': (255, 170, 0), 'rule': (120, 255, 80)}.get(it['kind'], (255, 255, 255))
        d.rectangle(it['bbox'], outline=c + (255,), width=lw)
        lab = it['id'] + (f" {it.get('text', '')[:18]}" if it['kind'] == 'text' else f" {it['kind']}")
        bb = d.textbbox((it['bbox'][0], it['bbox'][1]), lab, font=f)
        y = it['bbox'][1] - (bb[3] - bb[1]) - 6
        y = y if y > 0 else it['bbox'][1] + 2
        d.rectangle([it['bbox'][0], y, it['bbox'][0] + bb[2] - bb[0] + 8, y + bb[3] - bb[1] + 6], fill=(0, 0, 0, 190))
        d.text((it['bbox'][0] + 4, y), lab, font=f, fill=c + (255,))
    im.alpha_composite(ov)
    im.convert('RGB').save(path)


def fix(folder, spec):
    """눈으로 본 뒤 고치기(단계 3)를 한 번에. spec(json 문자열·파일·dict):
    drop: [id…]                         지운다(그림 속 글자·잡음)
    drop_below: 0.01                    잉크 높이가 판 높이의 이 비율 아래인 글줄을 지운다(작은 글 잡음 정리 — 크기 사다리의 바닥이 무너진다)
    set: {id: {kind/role/text/ink_h…}}  값 바꾸기(그림→글자, role bg, 로고)
    merge: [[id…, kind], …]             합쳐 하나로(로고 글자 둘 → logo)
    add: [{kind, text, box:[x0,y0,x1,y1] 또는 pct:[…], color?, rot?, tol?}]
         글자는 대강 그린 상자를 «그 색»으로 조여 잉크 높이를 잰다. pct 는 판 대비 % 좌표.
    retight: {id: {color, rot?, tol?}}  있는 글줄을 색으로 다시 조인다(사진 위 글자)
    note: "…"                           고친 이유(blocks.json 의 fixed 에 남는다)"""
    if isinstance(spec, str):
        spec = json.load(open(spec, encoding='utf-8')) if os.path.exists(spec) else json.loads(spec)
    bp = os.path.join(folder, 'blocks.json')
    doc = json.load(open(bp, encoding='utf-8'))
    W, H = doc['W'], doc['H']
    arr = np.array(Image.open(os.path.join(folder, 'poster.png')).convert('RGB'))
    items = {it['id']: it for it in doc['items']}

    def col(c):                                      # '#RRGGBB' · '@x,y'(판 대비 % 자리의 색) · 'same:<id>'(그 상자의 잉크 색)
        if not c:
            return None
        if c.startswith('@'):
            x, y = [float(v) for v in c[1:].split(',')]
            px, py = int(x * W / 100), int(y * H / 100)
            patch = arr[max(0, py - 3):py + 4, max(0, px - 3):px + 4].reshape(-1, 3)
            return '#%02X%02X%02X' % tuple(int(v) for v in np.median(patch, axis=0))
        if c.startswith('same:'):
            return (items.get(c[5:]) or {}).get('color')
        return c
    for i in spec.get('drop', []):
        items.pop(i, None)
    if spec.get('drop_below'):
        for k in [k for k, it in items.items() if it['kind'] == 'text' and it.get('ink_h', 1e9) < spec['drop_below'] * H]:
            items.pop(k)
    for i, v in spec.get('set', {}).items():
        if i in items:
            items[i].update(v)
    for i, v in spec.get('retight', {}).items():
        if i in items:
            b, c = _ink(arr, items[i]['bbox'], col(v.get('color')), v.get('rot', False), v.get('tol', 70))
            items[i].update(bbox=b, ink_h=(b[2] - b[0]) if v.get('rot') else (b[3] - b[1]), color=c, rot=v.get('rot', False))
    for grp in spec.get('merge', []):
        ids, kind = [g for g in grp[:-1] if g in items], grp[-1]
        if not ids:
            continue
        bb = [min(items[g]['bbox'][0] for g in ids), min(items[g]['bbox'][1] for g in ids),
              max(items[g]['bbox'][2] for g in ids), max(items[g]['bbox'][3] for g in ids)]
        new = {'id': ids[0], 'kind': kind, 'bbox': bb, 'text': ' '.join(items[g].get('text', '') for g in ids)}
        if kind == 'text':
            new['ink_h'] = max(items[g].get('ink_h', 0) for g in ids)
        for g in ids:
            items.pop(g)
        items[new['id']] = new
    n = 0
    for a in spec.get('add', []):
        n += 1
        box = a.get('box') or [round(a['pct'][0] * W / 100), round(a['pct'][1] * H / 100), round(a['pct'][2] * W / 100), round(a['pct'][3] * H / 100)]
        it = {'id': a.get('id') or f'A{n}', 'kind': a.get('kind', 'text'), 'text': a.get('text', '')}
        if it['kind'] == 'text' and not a.get('raw'):
            b, c = _ink(arr, box, col(a.get('color')), a.get('rot', False), a.get('tol', 70))
            it.update(bbox=b, color=c, ink_h=(b[2] - b[0]) if a.get('rot') else (b[3] - b[1]), rot=a.get('rot', False))
        elif it['kind'] != 'text' and a.get('color'):       # 그림·띠를 «이 색 덩어리»의 상자로(빨간 인물 같은 오려 붙인 그림)
            cc = col(a['color'])
            tgt = np.array([int(cc.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], float)
            x0, y0, x1, y1 = box
            m = np.linalg.norm(arr[y0:y1, x0:x1].astype(float) - tgt, axis=2) < a.get('tol', 60)
            ys = np.where(m.sum(1) > 0.003 * m.shape[1])[0]
            xs = np.where(m.sum(0) > 0.003 * m.shape[0])[0]
            it['bbox'] = [int(x0 + xs[0]), int(y0 + ys[0]), int(x0 + xs[-1] + 1), int(y0 + ys[-1] + 1)] if len(xs) and len(ys) else box
        else:
            it['bbox'] = box
            if it['kind'] == 'text':
                it['ink_h'] = a.get('ink_h', box[3] - box[1])
        for k in ('role',):
            if k in a:
                it[k] = a[k]
        items[it['id']] = it
    doc['items'] = sorted(items.values(), key=lambda t: (t['bbox'][1], t['bbox'][0]))
    if spec.get('note'):
        doc['fixed'] = spec['note']
    json.dump(doc, open(bp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    _draw_boxes(arr, doc['items'], os.path.join(folder, 'fixed.png'))
    return doc


# ───────────────────────── 재기 ─────────────────────────

ROLES = ['제목', '부제', '날짜', '장소', '정보', '본문', '로고', '크레딧', '메뉴']
_DATE = re.compile(r'(20\d\d|19\d\d|\d{1,2}[./]\s?\d{1,2}|\d{1,2}:\d\d|[0-9]{1,2}\s*(월|일)|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d|\d\s*(okt|nov|dez|oct|sept?))', re.I)


def _auto_roles(texts, logos, W, H):
    """글줄마다 역할(제목·부제·날짜·장소·정보·본문·로고·크레딧·메뉴) 초안. 사람이 붙인 role 은 건드리지 않는다.
    🔴 초안이다 — fix 의 set 으로 고친다(«T5 는 날짜»). 날짜는 숫자 꼴로, 크레딧·메뉴는 아주 작고 판 끝에 붙은 것으로 가른다."""
    for lg in logos:
        lg.setdefault('role', '로고')
    free = [t for t in texts if not t.get('role')]
    if not texts:
        return
    hs = sorted({round(t['ink_h']) for t in texts}, reverse=True)
    top = hs[0]
    for t in free:
        x0, y0, x1, y1 = t['bbox']
        h = t['ink_h']
        small = h < 0.012 * H
        edge = y0 < 0.06 * H or y1 > 0.94 * H or x0 < 0.03 * W or x1 > 0.97 * W
        if h >= 0.85 * top:
            t['role'] = '제목'
        elif _DATE.search(t.get('text', '')) and h >= 0.006 * H:
            t['role'] = '날짜'
        elif small and y0 < 0.06 * H and len(t.get('text', '')) < 30:
            t['role'] = '메뉴'
        elif small and edge:
            t['role'] = '크레딧'
        elif len(hs) > 1 and h >= 0.85 * hs[1] and h >= 0.02 * H:
            t['role'] = '부제'
        elif small:
            t['role'] = '본문'
        else:
            t['role'] = '정보'


def _zone(b, W, H):
    cx, cy = (b[0] + b[2]) / 2 / W, (b[1] + b[3]) / 2 / H
    return ['위', '가운데', '아래'][min(2, int(cy * 3))] + ' ' + ['왼쪽', '가운데', '오른쪽'][min(2, int(cx * 3))]


def _role_stats(items, W, H, head_h):
    """역할마다: 개수 · 가장 큰 글자 높이(%H) · 제목 대비 크기 · 자리(3×3) — 로고는 넓이와 폭"""
    out = {}
    for r in ROLES:
        its = [i for i in items if i.get('role') == r]
        if not its:
            continue
        big = max(its, key=lambda i: (i.get('ink_h') or (i['bbox'][3] - i['bbox'][1])))
        h = big.get('ink_h') or (big['bbox'][3] - big['bbox'][1])
        d = {'n': len(its), 'h_pct': round(100 * h / H, 2), 'where': _zone(big['bbox'], W, H)}
        if head_h and r != '제목':
            d['x_head'] = round(h / head_h, 3)
        if r == '로고':
            b = big['bbox']
            d.update(w_pct=round(100 * (b[2] - b[0]) / W, 1), area_pct=round(100 * (b[2] - b[0]) * (b[3] - b[1]) / (W * H), 2))
        out[r] = d
    return out


def _bleed(b, W, H, tol=0.006):
    return {'L': b[0] <= tol * W, 'T': b[1] <= tol * H, 'R': b[2] >= (1 - tol) * W, 'B': b[3] >= (1 - tol) * H}


def _paragraphs(texts):
    """글줄 → 글 덩어리(크기 같고, 왼끝이나 가운데가 맞고, 줄 사이가 좁은 것). 행간(줄 간격 / 잉크 높이)도 잰다."""
    texts = sorted(texts, key=lambda t: t['bbox'][1])
    blocks = []
    for t in texts:
        x0, y0, x1, y1 = t['bbox']
        h = t['ink_h']
        # 🔴 바로 위 줄(아랫끝이 가장 가까운 것)이 든 덩어리하고만 비교한다 — 아무 덩어리나 먼저 맞으면
        #    호프만 «22. Nov.»가 바로 위 «24.Okt.»를 건너 «Basel»에 붙었다(오른끝이 우연히 맞아서, 10-20)
        above = [B for B in blocks if B['lines'][-1]['bbox'][3] <= y0 + 0.3 * h]
        above = sorted(above, key=lambda B: -B['lines'][-1]['bbox'][3])[:1]
        for B in above:
            last = B['lines'][-1]
            lh = last['ink_h']
            same = max(h, lh) / max(1, min(h, lh)) < 1.12
            left = abs(x0 - last['bbox'][0]) < 0.5 * h
            mid = abs((x0 + x1) / 2 - (last['bbox'][0] + last['bbox'][2]) / 2) < 0.5 * h
            right = abs(x1 - last['bbox'][2]) < 0.5 * h
            gap = y0 - last['bbox'][3]
            if same and (left or mid or right) and -0.2 * h < gap < 1.6 * h:
                B['lines'].append(t)
                break
        else:
            blocks.append({'lines': [t]})
    for B in blocks:
        L = B['lines']
        B['bbox'] = [min(l['bbox'][0] for l in L), min(l['bbox'][1] for l in L), max(l['bbox'][2] for l in L), max(l['bbox'][3] for l in L)]
        B['ink_h'] = float(np.median([l['ink_h'] for l in L]))
        B['text'] = ' / '.join(l.get('text', '') for l in L)
        if len(L) > 1:
            pitch = np.median([L[i + 1]['bbox'][1] - L[i]['bbox'][1] for i in range(len(L) - 1)])
            B['leading'] = round(float(pitch / B['ink_h']), 2)
        lefts = [l['bbox'][0] for l in L]
        rights = [l['bbox'][2] for l in L]
        mids = [(l['bbox'][0] + l['bbox'][2]) / 2 for l in L]
        h = B['ink_h']
        if len(L) == 1:
            B['align'] = '한 줄'
        elif np.ptp(lefts) < 0.3 * h:
            B['align'] = '왼끝'
        elif np.ptp(rights) < 0.3 * h:
            B['align'] = '오른끝'
        elif np.ptp(mids) < 0.3 * h:
            B['align'] = '가운데'
        else:
            B['align'] = '자유'
        B['id'] = '+'.join(l['id'] for l in L)
    return blocks


def _nearest_scale(r):
    best = min(SCALES, key=lambda s: abs(r / s[0] - 1))
    return best[1] if abs(r / best[0] - 1) < 0.05 else ''


def _levels(blocks, H):
    hs = sorted({round(b['ink_h']) for b in blocks}, reverse=True)
    lv = []
    for h in hs:
        if lv and lv[-1][-1] / h < 1.10:
            lv[-1].append(h)
        else:
            lv.append([h])
    lv = [float(np.mean(g)) for g in lv]
    out = []
    for i, h in enumerate(lv):
        who = [b['id'] for b in blocks if lv.index(min(lv, key=lambda v: abs(v - b['ink_h']))) == i]
        r_next = lv[i] / lv[i + 1] if i + 1 < len(lv) else None
        out.append({'level': i + 1, 'ink_h': round(h, 1), 'pct_H': round(100 * h / H, 2), 'x_smallest': round(h / lv[-1], 2),
                    'x_next': round(r_next, 2) if r_next else None, 'scale': _nearest_scale(r_next) if r_next else '', 'blocks': who})
    return out


def _fit(edges, lo, hi, nmax, tol, gutters, force=None, gforce=None):
    """가장자리 목록에 가장 잘 맞는 n 단(행) 격자.
    🔴 같은 선에 선 가장자리는 «한 줄»로 센다(왼끝 맞춤 다섯 줄이 아무 단 수에나 «맞음»으로 나왔다 — 10-20 첫 시험).
    🔴 여백 선 자체(lo·hi)는 세지 않는다 — 여백을 거기서 쟀으니 늘 맞는다.
    우연히 맞을 몫도 뺀다 — 잘게 쪼갤수록 아무 선이나 맞는 걸 막는다."""
    span = hi - lo
    if span <= 0:
        return None, []
    lines = []
    for kind, v in sorted(edges, key=lambda e: e[1]):
        if abs(v - lo) <= tol or abs(v - hi) <= tol:
            continue
        if lines and lines[-1][0] == kind and v - lines[-1][1] <= tol:
            continue
        lines.append((kind, v))
    tries = []
    for n in ([force] if force else range(2, nmax + 1)):
        for g in ([gforce] if gforce is not None else gutters):
            cw = (span - (n - 1) * g) / n
            if cw <= 2 * g or cw <= 0:
                continue
            starts = [lo + i * (cw + g) for i in range(n)]
            ends = [s + cw for s in starts]
            hit = 0
            for kind, v in lines:
                ref = starts if kind == 'a' else ends
                if min(abs(v - r) for r in ref) <= tol:
                    hit += 1
            chance = min(1.0, n * 2 * tol / span)
            score = hit - chance * len(lines)
            tries.append({'n': n, 'gutter': g, 'cell': cw, 'hit': hit, 'of': len(lines), 'score': round(score, 2),
                          'starts': starts, 'ends': ends})
    if not tries:
        return None, []
    best = max(tries, key=lambda t: (round(t['score'], 1), -t['n'], -t['gutter']))
    per_n = {}
    for t in tries:
        if t['n'] not in per_n or t['score'] > per_n[t['n']]['score']:
            per_n[t['n']] = t
    return best, [{'n': k, 'hit': v['hit'], 'of': v['of'], 'score': v['score']} for k, v in sorted(per_n.items())]


def _ruler(lo, hi, n=12):
    """근거가 모자랄 때 쓰는 «참고 자» — 여백 안을 n 등분(단 사이 0). 레퍼런스끼리 자리를 같은 자로 비교하려고 쓴다."""
    cw = (hi - lo) / n
    return {'n': n, 'gutter': 0.0, 'cell': cw, 'hit': 0, 'of': 0, 'score': 0, 'ruler': True,
            'starts': [lo + i * cw for i in range(n)], 'ends': [lo + (i + 1) * cw for i in range(n)]}


def _span(a, b, grid):
    """좌표 구간 → 몇 번째 칸부터 몇 번째 칸까지(1부터, 소수점은 칸 안 어디쯤인지)."""
    if not grid:
        return None
    pitch = grid['cell'] + grid['gutter']
    lo = grid['starts'][0]
    return round((a - lo) / pitch + 1, 2), round((b - lo - grid['cell']) / pitch + 1, 2)


def _span_txt(sp, word, bleed=()):
    if not sp:
        return ''
    a, b = sp
    ia, ib = int(round(a)), int(round(b))
    sa = '판 끝' if ('L' in bleed or 'T' in bleed) else str(ia)
    sb = '판 끝' if ('R' in bleed or 'B' in bleed) else str(ib)
    loose = ' (칸 선과 어긋남)' if (sa != '판 끝' and abs(a - ia) > 0.15) or (sb != '판 끝' and abs(b - ib) > 0.15) else ''
    return f'{word} {sa}~{sb}' + loose


def _third(cx, cy, W, H):
    hx = ['왼쪽', '가운데', '오른쪽'][min(2, int(3 * cx / W))]
    vy = ['위', '가운데', '아래'][min(2, int(3 * cy / H))]
    return '정가운데' if hx == vy == '가운데' else f'{hx} {vy}'


def analyze(folder, cols=None, gutter=None, rows=None):
    doc = json.load(open(os.path.join(folder, 'blocks.json'), encoding='utf-8'))
    W, H = doc['W'], doc['H']
    items = [it for it in doc['items'] if it['kind'] in ('text', 'image', 'logo', 'rule')]
    for it in items:
        it['bleed'] = _bleed(it['bbox'], W, H)
    texts = [it for it in items if it['kind'] == 'text']
    for t in texts:
        t.setdefault('ink_h', t['bbox'][3] - t['bbox'][1])
    imgs = [it for it in items if it['kind'] == 'image' and it.get('role') != 'bg']
    bgimg = [it for it in items if it['kind'] == 'image' and it.get('role') == 'bg']
    _auto_roles(texts, [it for it in items if it['kind'] == 'logo'], W, H)
    paras = _paragraphs(texts)

    # 여백: 판 끝을 뚫고 나간 쪽은 빼고 가장 바깥 것
    def edge(side):
        k = {'L': 0, 'T': 1, 'R': 2, 'B': 3}[side]
        vals = [it['bbox'][k] for it in items if not it['bleed'][side] and it.get('role') != 'bg']
        if not vals:
            return None
        return min(vals) if side in 'LT' else max(vals)
    mL, mT, mR, mB = edge('L'), edge('T'), edge('R'), edge('B')
    # 오른쪽 여백은 «오른쪽에 선이 있을 때만» 믿는다 — 왼끝 맞춤 글의 들쭉날쭉한 오른끝은 여백이 아니다(10-20 첫 시험에서 28% 로 잡혔다)
    if mR is not None:
        tol = 0.008 * W
        sharers = [it for it in items if not it['bleed']['R'] and it.get('role') != 'bg' and abs(it['bbox'][2] - mR) <= tol]
        firm = any(it['kind'] in ('image', 'logo', 'rule') for it in sharers) or len(sharers) >= 2 or             any(b.get('align') in ('오른끝', '가운데') and abs(b['bbox'][2] - mR) <= tol for b in paras)
        if not firm:
            mR = None
    margins = {'L': mL, 'T': mT, 'R': (W - mR) if mR is not None else None, 'B': (H - mB) if mB is not None else None}
    for k in margins:                                          # 25% 를 넘으면 여백이 아니라 «그쪽이 비었다» (루체른: 글이 바닥에만 있어 위 여백 88%)
        if margins[k] is not None and margins[k] > 0.25 * (W if k in 'LR' else H):
            margins[k] = None
    assumed = []
    if margins['R'] is None:                                  # 오른쪽에 선이 없거나 뚫렸으면 왼쪽과 같다고 본다
        margins['R'] = margins['L']; assumed.append('R')
    if margins['L'] is None:
        margins['L'] = margins['R']; assumed.append('L')
    if margins['T'] is None and margins['B'] is not None:
        margins['T'] = margins['B']; assumed.append('T')
    elif margins['B'] is None and margins['T'] is not None:
        margins['B'] = margins['T']; assumed.append('B')

    # 단 그리드: 글 덩어리·그림·로고의 «뚫리지 않은» 가장자리
    xe, ye = [], []
    for b in paras + [it for it in items if it['kind'] in ('image', 'logo', 'rule') and it.get('role') != 'bg']:
        bl = _bleed(b['bbox'], W, H)
        if not bl['L']: xe.append(('a', b['bbox'][0]))
        if not bl['R'] and b.get('align', '왼끝') != '왼끝' or (not bl['R'] and 'align' not in b): xe.append(('b', b['bbox'][2]))
        if not bl['T']: ye.append(('a', b['bbox'][1]))
        if not bl['B']: ye.append(('b', b['bbox'][3]))
    gx = [0, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04]
    colg, coltries = (None, [])
    if margins['L'] is not None:
        colg, coltries = _fit(xe, margins['L'], W - margins['R'], 12, 0.008 * W, [g * W for g in gx],
                              force=cols, gforce=gutter)
    if margins['L'] is not None and (not colg or (colg['hit'] < 2 and not cols)):
        colg = _ruler(margins['L'], W - margins['R'])
    rowg, rowtries = (None, [])
    if margins['T'] is not None and margins['B'] is not None:
        rowg, rowtries = _fit(ye, margins['T'], H - margins['B'], 16, 0.008 * H, [g * H for g in gx],
                              force=rows, gforce=None)
        if not rowg or (rowg['hit'] < 2 and not rows):
            rowg = _ruler(margins['T'], H - margins['B'], 16)

    levels = _levels(paras, H) if paras else []
    content_w = W - margins['L'] - margins['R'] if margins['L'] is not None else W

    # 정렬축: 둘 이상이 같은 선에 서 있나
    axes = []
    for name, k in (('왼끝', 0), ('오른끝', 2)):
        vals = sorted([(b['bbox'][k], b['id']) for b in paras + imgs])
        group = []
        for v, i in vals:
            if group and v - group[-1][0] > 0.008 * W:
                if len(group) > 1: axes.append({'axis': name, 'x': round(np.mean([g[0] for g in group])), 'who': [g[1] for g in group]})
                group = []
            group.append((v, i))
        if len(group) > 1: axes.append({'axis': name, 'x': round(np.mean([g[0] for g in group])), 'who': [g[1] for g in group]})

    P = []
    for b in paras:
        x0, y0, x1, y1 = b['bbox']
        P.append({'id': b['id'], 'text': b['text'], 'ink_h': round(b['ink_h'], 1), 'pct_H': round(100 * b['ink_h'] / H, 2),
                  'w_pct_content': round(100 * (x1 - x0) / content_w, 1), 'lines': len(b['lines']),
                  'leading': b.get('leading'), 'align': b['align'], 'cols': _span(x0, x1, colg), 'rows': _span(y0, y1, rowg),
                  'bbox': b['bbox'], 'color': b['lines'][0].get('color')})
    I = []
    for it in imgs:
        x0, y0, x1, y1 = it['bbox']
        I.append({'id': it['id'], 'area_pct': round(100 * (x1 - x0) * (y1 - y0) / (W * H), 1),
                  'w_pct': round(100 * (x1 - x0) / W, 1), 'h_pct': round(100 * (y1 - y0) / H, 1),
                  'bleed': [k for k, v in it['bleed'].items() if v], 'where': _third((x0 + x1) / 2, (y0 + y1) / 2, W, H),
                  'cols': _span(x0, x1, colg), 'rows': _span(y0, y1, rowg), 'bbox': it['bbox']})

    # 글 ↔ 그림: 가장 큰 글(제목)과 가장 큰 그림
    rel = {}
    if P and I:
        head = max(P, key=lambda p: p['ink_h'])
        img = max(I, key=lambda i: i['area_pct'])
        hb, ib = head['bbox'], img['bbox']
        rel = {'head': head['id'], 'image': img['id'],
               'img_h_over_head_h': round((ib[3] - ib[1]) / head['ink_h'], 1),
               'img_w_over_head_w': round((ib[2] - ib[0]) / max(1, hb[2] - hb[0]), 2),
               'h_gap_pct_W': round(100 * (ib[0] - hb[2]) / W, 1) if ib[0] >= hb[0] else round(100 * (hb[0] - ib[2]) / W, 1),
               'v_gap_pct_H': round(100 * (ib[1] - hb[3]) / H, 1),
               'overlap': bool(hb[0] < ib[2] and ib[0] < hb[2] and hb[1] < ib[3] and ib[1] < hb[3]),
               'shared_edges': [n for n, a, b in (('왼끝', hb[0], ib[0]), ('오른끝', hb[2], ib[2]), ('윗끝', hb[1], ib[1]),
                                                   ('그림 왼끝=글 오른끝', hb[2], ib[0]), ('그림 윗끝=글 아랫끝', hb[3], ib[1]))
                                if abs(a - b) <= 0.01 * max(W, H)]}
        # 글 덩어리마다 그림의 어느 쪽에 있나 → 모아서 한 말로(«위·왼쪽에서 감쌈» = ㄱ자)
        # 🔴 글 모둠 전체 상자로 판정하면 «겹침»이 된다 — 제목은 그림 위로 길게 지나가고 본문은 왼쪽에 있어서(10-20 첫 시험)
        tx1 = max(p['bbox'][2] for p in P)
        rel['text_zone_w_pct'] = round(100 * (tx1 - min(p['bbox'][0] for p in P)) / W, 1)
        side = {}
        for p in P:
            b = p['bbox']
            if b[0] < ib[2] and ib[0] < b[2] and b[1] < ib[3] and ib[1] < b[3]:
                d = '겹침'
            else:
                gaps = {'왼쪽': ib[0] - b[2], '오른쪽': b[0] - ib[2], '위': ib[1] - b[3], '아래': b[1] - ib[3]}
                d = max(gaps, key=gaps.get)
            p['vs_image'] = d
            side[d] = side.get(d, 0) + 1
        rel['blocks_by_side'] = side
        ks = set(side)
        if ks == {'겹침'}:
            rel['text_vs_image_split'] = '글이 그림 위에 얹힘'
        elif '겹침' in ks:
            rel['text_vs_image_split'] = '일부 겹침(' + '·'.join(k for k in side if k != '겹침') + ' + 겹침)'
        elif len(ks) == 1:
            rel['text_vs_image_split'] = {'왼쪽': '글 왼쪽, 그림 오른쪽(나란히)', '오른쪽': '그림 왼쪽, 글 오른쪽(나란히)',
                                          '위': '글 위, 그림 아래', '아래': '그림 위, 글 아래'}[ks.pop()]
        else:
            rel['text_vs_image_split'] = '·'.join(sorted(ks)) + '에서 그림을 감쌈'

    covered = np.zeros((H // 4 + 1, W // 4 + 1), bool)
    for b in paras:
        x0, y0, x1, y1 = b['bbox']; covered[y0 // 4:y1 // 4 + 1, x0 // 4:x1 // 4 + 1] = True
    for it in imgs + bgimg + [i for i in items if i['kind'] in ('logo', 'rule')]:
        x0, y0, x1, y1 = it['bbox']; covered[y0 // 4:y1 // 4 + 1, x0 // 4:x1 // 4 + 1] = True
    text_area = sum((b['bbox'][2] - b['bbox'][0]) * (b['bbox'][3] - b['bbox'][1]) for b in paras) / (W * H)

    res = {'src': doc.get('src', ''), 'own': doc.get('own', ''), 'W': W, 'H': H, 'ratio': round(H / W, 3), 'bg': doc.get('bg'),
           'full_bleed_art': bool(bgimg),
           'margins_pct': {k: (round(100 * v / (W if k in 'LR' else H), 1) if v is not None else None) for k, v in margins.items()},
           'margins_assumed': assumed,
           'columns': ({'n': colg['n'], 'gutter_pct_W': round(100 * colg['gutter'] / W, 1), 'cell_pct_W': round(100 * colg['cell'] / W, 1),
                        'hit': colg['hit'], 'of': colg['of'], 'forced': bool(cols), 'ruler': bool(colg.get('ruler'))} if colg else None),
           'columns_tried': coltries,
           'rows': ({'n': rowg['n'], 'gutter_pct_H': round(100 * rowg['gutter'] / H, 1), 'cell_pct_H': round(100 * rowg['cell'] / H, 1),
                     'hit': rowg['hit'], 'of': rowg['of'], 'forced': bool(rows), 'ruler': bool(rowg.get('ruler'))} if rowg else None),
           'rows_tried': rowtries,
           'type_levels': levels, 'text_blocks': P, 'images': I, 'relation': rel, 'axes': axes,
           'text_area_pct': round(100 * text_area, 1), 'empty_pct': round(100 * (1 - covered.mean()), 1),
           'heat_text': _heat(paras, W, H), 'heat_image': _heat(imgs, W, H), 'heat_bg': bool(bgimg),
           'roles': _role_stats(texts + [it for it in items if it['kind'] == 'logo'], W, H, max((t['ink_h'] for t in texts if t.get('role') == '제목'), default=0))}
    doc['items'] = [dict(it, **{k: v for k, v in it.items()}) for it in doc['items']]      # 역할 초안을 blocks.json 에도 남긴다(사람이 고칠 자리)
    json.dump({**doc, 'items': [{k: v for k, v in it.items() if k != 'bleed'} for it in doc['items']]},
              open(os.path.join(folder, 'blocks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(res, open(os.path.join(folder, 'analysis.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
    _draw_grid(folder, res, colg, rowg, margins, paras, imgs, items)
    try:
        res['style'] = style(folder)
    except Exception as e:                           # 색·모양이 실패해도 그리드 보고는 낸다
        res['style'] = {'error': str(e)}
    json.dump(res, open(os.path.join(folder, 'analysis.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
    rp = os.path.join(folder, 'REPORT.md')
    new = _report(folder, res)
    mark = '## 눈으로 본 것'
    if os.path.exists(rp):                                     # 다시 돌려도 사람·에이전트가 쓴 «눈으로 본 것» 이하는 지킨다
        old = open(rp, encoding='utf-8').read()
        if mark in old:
            body = old.split(mark, 1)[1].split('\n', 1)[-1].split('---')[0]
            if body.replace('-', '').strip():
                new = new.split(mark, 1)[0] + mark + old.split(mark, 1)[1]
    open(rp, 'w', encoding='utf-8').write(new)
    return res


def _heat(boxes, W, H):
    gx, gy = HEAT
    m = np.zeros((gy, gx))
    for b in boxes:
        x0, y0, x1, y1 = b['bbox']
        for j in range(gy):
            for i in range(gx):
                cx0, cy0, cx1, cy1 = i * W / gx, j * H / gy, (i + 1) * W / gx, (j + 1) * H / gy
                ov = max(0, min(x1, cx1) - max(x0, cx0)) * max(0, min(y1, cy1) - max(y0, cy0))
                m[j, i] = max(m[j, i], ov / ((W / gx) * (H / gy)))
    return np.round(m, 2).tolist()


def _draw_grid(folder, res, colg, rowg, margins, paras, imgs, items):
    im = Image.open(os.path.join(folder, 'poster.png')).convert('RGBA')
    W, H = im.size
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    lw = max(2, W // 600)
    f = _font(max(13, min(W, H) * 0.016))
    if colg:                                                     # 단: 번갈아 옅은 자홍
        for i, (s, e) in enumerate(zip(colg['starts'], colg['ends'])):
            d.rectangle([s, 0, e, H], fill=(255, 40, 170, 24 if i % 2 == 0 else 10))
            d.line([(s, 0), (s, H)], fill=(255, 40, 170, 170), width=lw)
            d.line([(e, 0), (e, H)], fill=(255, 40, 170, 170), width=lw)
            d.text((s + 4, 4), str(i + 1), font=f, fill=(255, 80, 190, 255))
    if rowg:
        for i, (s, e) in enumerate(zip(rowg['starts'], rowg['ends'])):
            d.line([(0, s), (W, s)], fill=(255, 200, 0, 120), width=max(1, lw // 2))
            d.line([(0, e), (W, e)], fill=(255, 200, 0, 120), width=max(1, lw // 2))
            d.text((4, s + 2), str(i + 1), font=f, fill=(255, 210, 40, 255))
    for k, v in margins.items():                                 # 여백: 청록 점선 느낌의 굵은 선
        if v is None:
            continue
        x = {'L': v, 'R': W - v}.get(k); y = {'T': v, 'B': H - v}.get(k)
        if x is not None: d.line([(x, 0), (x, H)], fill=(0, 230, 200, 230), width=lw * 2)
        if y is not None: d.line([(0, y), (W, y)], fill=(0, 230, 200, 230), width=lw * 2)
    lv = res['type_levels']
    for b in paras:
        L = next((l['level'] for l in lv if b['id'] in l['blocks']), '?')
        d.rectangle(b['bbox'], outline=(0, 200, 255, 255), width=lw)
        lab = f"글{L} {100 * b['ink_h'] / H:.1f}%H" + (f" 행간{b['leading']}" if b.get('leading') else '')
        _tag(d, b['bbox'], lab, f, (0, 200, 255))
    for it in imgs:
        x0, y0, x1, y1 = it['bbox']
        d.rectangle(it['bbox'], outline=(255, 40, 170, 255), width=lw * 2)
        _tag(d, it['bbox'], f"그림 {100 * (x1 - x0) * (y1 - y0) / (W * H):.0f}%", f, (255, 40, 170))
    for it in items:
        if it['kind'] in ('logo', 'rule'):
            d.rectangle(it['bbox'], outline=(255, 170, 0, 255), width=lw)
            _tag(d, it['bbox'], it['kind'], f, (255, 170, 0))
    im.alpha_composite(ov)
    im.convert('RGB').save(os.path.join(folder, 'grid.png'))


def _tag(d, b, lab, f, c):
    bb = d.textbbox((0, 0), lab, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x, y = b[0], b[3] + 4
    d.rectangle([x, y, x + tw + 10, y + th + 8], fill=(0, 0, 0, 200))
    d.text((x + 5, y + 1), lab, font=f, fill=c + (255,))


def _report(folder, r):
    name = os.path.basename(os.path.abspath(folder))
    L = [f'# 포스터 해부 — {name}', '',
         f'> **뭐냐:** 레퍼런스 한 장을 그리드로 잰 기록(`python -m ad pgrid analyze` 가 씀). 숫자는 `analysis.json`, 그림은 `grid.png`.',
         '> **언제 읽나:** 이 레퍼런스의 결을 빌릴 때, 모음표(`SUMMARY.md`)의 숫자가 이상할 때 근거를 볼 때.',
         '> **안 담는 것:** 여러 장 모은 경향 → 상위 폴더 `SUMMARY.md` · 해부 방법 → `protocols/promo.md` §포스터 레퍼런스 해부.', '',
         f"- 출처: {r['src'] or '확인 못 함'} ({r['own']}) · 판 {r['W']}×{r['H']} (세로/가로 {r['ratio']})"
         + (' · 그림이 판 전체를 덮음' if r['full_bleed_art'] else '')]
    m = r['margins_pct']
    L.append(f"- 여백(판 대비 %): 왼 {m['L']} · 위 {m['T']} · 오른 {m['R']} · 아래 {m['B']}"
             + (f" (가정: {','.join(r['margins_assumed'])} 은 반대쪽과 같다고 봄)" if r['margins_assumed'] else ''))
    c = r['columns']
    if c and c['ruler']:
        L.append(f"- 단 그리드: **확인 못 함** — 여백 선 말고 칸 선에 맞는 가장자리가 둘 미만(안쪽 선 {max((t['of'] for t in r['columns_tried']), default=0)}개). "
                 f"자리는 «참고 자»(여백 안 {c['n']}등분)로 적는다")
    elif c:
        weak = ' · 🔴 근거 약함(맞은 선이 셋 미만)' if c['hit'] < 3 else ''
        L.append(f"- 단 그리드: **{c['n']}단**, 칸 {c['cell_pct_W']}%W, 사이 {c['gutter_pct_W']}%W — 여백 선 말고 안쪽 선 {c['of']}개 중 {c['hit']}개가 칸 선에 맞음"
                 + (' (사람이 정한 단 수)' if c['forced'] else '') + weak)
        alt = [f"{t['n']}단 {t['hit']}/{t['of']}" for t in r['columns_tried'] if t['hit'] == c['hit'] and t['n'] != c['n']]
        if alt:
            L.append(f"  - 똑같이 맞는 다른 단 수: {', '.join(alt[:6])} → 이 레퍼런스만으로는 단 수를 하나로 못 정한다")
    rw = r['rows']
    if rw and rw['ruler']:
        L.append(f"- 행 그리드: 확인 못 함 — 자리는 «참고 자»(여백 안 {rw['n']}등분)로 적는다")
    elif rw:
        L.append(f"- 행 그리드: {rw['n']}행, 칸 {rw['cell_pct_H']}%H — 안쪽 선 {rw['of']}개 중 {rw['hit']}개 맞음"
                 + (' · 🔴 근거 약함' if rw['hit'] < 3 else ''))
    if r['axes']:
        L.append('- 정렬축: ' + ' · '.join(f"{a['axis']} x={a['x']} ({', '.join(a['who'])})" for a in r['axes']))
    L += ['', '## 글자 크기 사다리 (잉크 높이)', '', '| 단계 | 판 높이 대비 | 가장 작은 글 대비 | 바로 아래 단계 대비 | 가까운 비율 | 덩어리 |', '|---|---|---|---|---|---|']
    for l in r['type_levels']:
        L.append(f"| {l['level']} | {l['pct_H']}% | ×{l['x_smallest']} | {('×' + str(l['x_next'])) if l['x_next'] else '-'} | {l['scale'] or '-'} | {', '.join(l['blocks'])} |")
    L += ['', '## 글 덩어리', '', '| 덩어리 | 글 | 높이 %H | 폭(본문 폭 대비) | 줄 | 행간 | 맞춤 | 단 | 그림의 어느 쪽 |', '|---|---|---|---|---|---|---|---|---|']
    for p in r['text_blocks']:
        L.append(f"| {p['id']} | {p['text'][:30]} | {p['pct_H']} | {p['w_pct_content']}% | {p['lines']} | {p['leading'] or '-'} | {p['align']} | {_span_txt(p['cols'], '단') or '-'} | {p.get('vs_image', '-')} |")
    if r['images']:
        L += ['', '## 그림', '', '| 그림 | 넓이 | 가로·세로(판 대비) | 자리(3분할) | 판 밖으로 | 단 | 행 |', '|---|---|---|---|---|---|---|']
        for i in r['images']:
            L.append(f"| {i['id']} | {i['area_pct']}% | {i['w_pct']}% × {i['h_pct']}% | {i['where']} | {','.join(i['bleed']) or '없음'} | {_span_txt(i['cols'], '단', [k for k in i['bleed'] if k in 'LR']) or '-'} | {_span_txt(i['rows'], '행', [k for k in i['bleed'] if k in 'TB']) or '-'} |")
    rel = r['relation']
    if rel:
        L += ['', '## 제목 글 ↔ 가장 큰 그림', '',
              f"- 배치: **{rel['text_vs_image_split']}** · 글 모둠 폭 {rel['text_zone_w_pct']}%W",
              f"- 그림 높이 = 제목 글자 높이의 **{rel['img_h_over_head_h']}배** · 그림 폭 = 제목 줄 폭의 {rel['img_w_over_head_w']}배",
              f"- 사이: 가로 {rel['h_gap_pct_W']}%W · 세로 {rel['v_gap_pct_H']}%H (음수 = 겹침){' · 상자가 겹친다' if rel['overlap'] else ''}",
              f"- 같은 선을 쓰는 가장자리: {', '.join(rel['shared_edges']) or '없음'}"]
    stl = r.get('style') or {}
    if stl.get('palette'):
        sh = stl['shape']
        L += ['', '## 색·모양·질감 (`style.png`)', '',
              '| 색 | 넓이 | 밝기 L* | 채도 C | 이름 | 온도 |', '|---|---|---|---|---|---|']
        for p_ in stl['palette']:
            if p_['area'] >= 1:
                L.append(f"| `{p_['hex']}` | {p_['area']}% | {p_['L']} | {p_['C']} | {p_['name']} | {p_['temp']} |")
        L += ['', f"- 실제로 쓴 색(넓이 3% 이상) **{stl['colors_used']}개** · 밝기 {stl['light_tiers']}단 · 밝기 대비 {stl['contrast_L']} · 평균 채도 {stl['chroma_mean']} · 무채색 {stl['neutral_pct']}% · 따뜻 {stl['warm_pct']}% / 차가움 {stl['cool_pct']}%",
              f"- 칠한 법: **{stl['render']}**(부드러운 톤 {stl['soft_pct']}% 대 날카로운 경계 {stl['sharp_pct']}% = {stl['softness']}, 1 아래 평면 · 1.8 위 사진·그라데이션) · 질감 {stl['texture']}(잔떨림 {stl['grain']})",
              f"- 모양(글자·로고 뺀 경계): **{stl.get('hardness', '-')}**, 모서리 {stl.get('edge_feel', '-')} · 직선 {sh.get('straight', '-')}% · 곡선 {sh.get('curved', '-')}% · 꺾인 모서리 {sh.get('corners_per_1000px', '-')}개/경계 1000px · 경계 방향 수평 {sh.get('horizontal', '-')}% 수직 {sh.get('vertical', '-')}% 사선 {sh.get('diagonal', '-')}%",
              f"- 큰 덩어리: {', '.join(f'{k} {v}%' for k, v in sh.get('blobs', {}).items()) or '없음'} · 무게중심 (가로 {stl['center'][0]}%, 세로 {stl['center'][1]}%) · 좌우 대칭 {stl['symmetry']}"]
    L += ['', f"- 글 덩어리 넓이 {r['text_area_pct']}% · 빈 곳(어느 상자에도 안 든 곳) {r['empty_pct']}%", '',
          '## 눈으로 본 것 (에이전트가 grid.png 를 보고 채운다)', '', '- ', '', '---', '', '## 변경 이력', '- 자동 생성']
    return '\n'.join(L) + '\n'


# ───────────────────────── 색·모양·질감 ─────────────────────────

HUES = [(12, '빨강'), (40, '주황'), (65, '노랑'), (95, '연두'), (150, '초록'), (190, '청록'), (225, '파랑'), (255, '남색'), (290, '보라'), (340, '분홍'), (361, '빨강')]


def _hue_name(rgb, C, L):
    """이름·온도는 사람이 쓰는 색상환(HSV)으로 — Lab 색상각을 그대로 대면 빨강이 주황, 노랑이 연두로 붙는다(10-20)."""
    import colorsys
    if C < 10:
        return ('흰색' if L > 85 else ('검정' if L < 22 else '회색')), '무채'
    h = colorsys.rgb_to_hsv(*[v / 255 for v in rgb])[0] * 360
    name = next(n for lim, n in HUES if h < lim)
    return name, ('따뜻' if (h < 75 or h > 300) else '차가움')


def style(folder):
    """판 하나의 색·모양·질감을 잰다 → style.json · style.png. 무엇을 그렸나가 아니라 «어떻게 칠했나»(guides/poster_flat.md 스타일 시트와 같은 자).
    색: 군집 색(넓이·밝기 L*·채도 C·색 이름·온도) · 실제로 쓴 색 수(3% 이상) · 밝기 단계 · 대비 · 무채색 비율 · 평면 순도(면이 한 색으로 깨끗한가 = 평면/사진)
    모양: 경계의 방향(수평·수직·사선) · 직선으로 설명되는 경계 비율(= 딱딱함) · 큰 덩어리가 각졌나·둥근가 (글자·로고 상자는 뺀다 — 글자 모양은 서체가 정한다)
    질감: 평평한 곳의 잔떨림(거칠기) · 무게중심 · 좌우 대칭"""
    import cv2
    from skimage.color import rgb2lab
    doc = json.load(open(os.path.join(folder, 'blocks.json'), encoding='utf-8'))
    im = Image.open(os.path.join(folder, 'poster.png')).convert('RGB')
    W, H = im.size
    sc = 480 / max(W, H)
    sm = np.array(im.resize((max(1, int(W * sc)), max(1, int(H * sc))), Image.LANCZOS))
    lab = rgb2lab(sm / 255.0).reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    cv2.setRNGSeed(1)
    _, lbl, cen = cv2.kmeans(lab, 10, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    lbl = lbl.ravel()
    groups = []                                       # ΔE 12 안의 군집은 같은 색으로 합친다
    for k in np.argsort(-np.bincount(lbl, minlength=10)):
        for g in groups:
            if np.linalg.norm(cen[k] - cen[g[0]]) < 12:
                g.append(int(k))
                break
        else:
            groups.append([int(k)])
    n = len(lbl)
    pal = []
    for g in groups:
        m = np.isin(lbl, g)
        if not m.any():
            continue
        L, A, B = [float(v) for v in lab[m].mean(axis=0)]
        C = float(np.hypot(A, B))
        h = float(np.degrees(np.arctan2(B, A)) % 360)
        rgb = sm.reshape(-1, 3)[m].mean(axis=0)
        name, temp = _hue_name(rgb, C, L)
        pal.append({'hex': '#%02X%02X%02X' % tuple(int(v) for v in rgb), 'area': round(100 * m.sum() / n, 1),
                    'L': round(L), 'C': round(C), 'hue': round(h), 'name': name, 'temp': temp})
    pal.sort(key=lambda p: -p['area'])
    used = [p for p in pal if p['area'] >= 3]
    Ls = sorted(p['L'] for p in used)
    tiers = 1 + sum(1 for a_, b_ in zip(Ls, Ls[1:]) if b_ - a_ > 15)
    # 칠한 법: 부드러운 톤 변화(사진·에어브러시·3D) 대 날카로운 경계(평면 면 나누기)의 비
    # 🔴 «군집 색에 얼마나 가깝나»로 재면 흑백 사진이 회색 열 단계로 근사돼 «평면»이 된다(10-20)
    Lb = cv2.GaussianBlur(lab[:, 0].reshape(sm.shape[:2]), (3, 3), 0)
    gm = np.hypot(cv2.Sobel(Lb, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(Lb, cv2.CV_32F, 0, 1, ksize=3)) / 8
    soft = float(((gm > 0.6) & (gm < 4)).mean()); sharp = float((gm >= 4).mean())
    softness = soft / max(sharp, 1e-3)
    gray = np.array(Image.fromarray(sm).convert('L'))
    tmask = np.zeros_like(gray, bool)
    for it in doc['items']:
        if it['kind'] in ('text', 'logo'):
            x0, y0, x1, y1 = [int(v * sc) for v in it['bbox']]
            tmask[max(0, y0 - 2):y1 + 3, max(0, x0 - 2):x1 + 3] = True
    med = float(np.median(gray))
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), int(max(10, 0.66 * med)), int(min(255, max(40, 1.33 * med))))
    edges[tmask] = 0
    bd = max(3, int(0.02 * min(sm.shape[:2])))       # 판 가장자리 띠(스캔 테두리·목업 그림자)는 모양이 아니다 — 조개 그림이 «딱딱함»으로 나왔다(10-20)
    edges[:bd] = 0; edges[-bd:] = 0; edges[:, :bd] = 0; edges[:, -bd:] = 0
    ne = int((edges > 0).sum())
    shape, lm = {'edge_px': ne}, None
    if ne > 50:
        gx = cv2.Sobel(gray.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
        ys, xs = np.nonzero(edges)
        ang = (np.degrees(np.arctan2(gy[ys, xs], gx[ys, xs])) + 90) % 180     # 경계선이 놓인 방향
        hor = float(((ang < 12) | (ang > 168)).mean())
        ver = float((np.abs(ang - 90) < 12).mean())
        shape.update(horizontal=round(100 * hor), vertical=round(100 * ver), diagonal=round(100 * (1 - hor - ver)))
        # 경계선을 따라가며 20px 마디마다 방향이 얼마나 도나: 4° 아래 = 직선, 40° 아래 = 곡선, 그 위 = 꺾인 모서리
        # (반지름이 판 폭의 3분의 2 넘는 아주 완만한 곡선만 직선으로 친다)
        # (짧은 직선 찾기(Hough)로는 큰 원호도 «직선»이 된다 — 누보 에스파스의 큰 S 가 딱딱함으로 나왔다, 10-20)
        lm = np.zeros(sm.shape[:2] + (3,), np.uint8)
        cs, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        st = cu = 0
        corners = 0
        for c in cs:
            pts = c[:, 0, :].astype(float)
            if len(pts) < 60:
                continue
            q = pts[::20]
            v = np.diff(q, axis=0)
            a_ = np.arctan2(v[:, 1], v[:, 0])
            da = np.degrees(np.abs((np.diff(a_) + np.pi) % (2 * np.pi) - np.pi))
            prev = False
            for j, x_ in enumerate(da):
                p0 = tuple(int(t) for t in q[j + 1]); p1 = tuple(int(t) for t in q[j + 2])
                if x_ < 4:
                    st += 1; cv2.line(lm, p0, p1, (0, 160, 170), 1); prev = False
                elif x_ < 40:
                    cu += 1; cv2.line(lm, p0, p1, (210, 40, 140), 1); prev = False
                else:
                    if not prev:
                        corners += 1; cv2.circle(lm, p0, 2, (230, 170, 0), -1)
                    prev = True
        tot_ = max(1, st + cu)
        shape['segments'] = st + cu
        shape['straight'] = round(100 * st / tot_)
        shape['curved'] = round(100 * cu / tot_)
        shape['corners_per_1000px'] = round(1000 * corners / max(1, 20 * tot_ / 2), 1)   # 경계 1000px(왕복 경로라 반으로) 당 꺾인 모서리 수
        lbl_img = lbl.reshape(sm.shape[:2])
        kinds = {'각짐': 0.0, '둥긂': 0.0, '자유곡선': 0.0}
        for g in groups:
            mm = np.isin(lbl_img, g).astype(np.uint8)
            mm[tmask] = 0
            mm = cv2.morphologyEx(mm, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            cs, _ = cv2.findContours(mm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            for c in cs:
                area = cv2.contourArea(c)
                if area < 0.004 * mm.size:
                    continue
                per = cv2.arcLength(c, True)
                circ = 4 * np.pi * area / (per * per + 1e-6)
                ap = cv2.approxPolyDP(c, 0.015 * per, True)
                x_, y_, w_, h_ = cv2.boundingRect(c)
                if w_ * h_ > 0.8 * mm.size:              # 판 전체를 덮는 바탕 덩어리는 «모양»이 아니다(남은 자리일 뿐)
                    continue
                if len(ap) <= 8 and area / (w_ * h_ + 1e-6) > 0.6:
                    k_ = '각짐'
                elif circ > 0.55:
                    k_ = '둥긂'
                else:
                    k_ = '자유곡선'
                kinds[k_] += area
        tot = sum(kinds.values()) or 1
        shape['blobs'] = {k: round(100 * v / tot) for k, v in kinds.items()}
    Lc = lab[:, 0].reshape(sm.shape[:2])
    hh, ww = (Lc.shape[0] // 8) * 8, (Lc.shape[1] // 8) * 8
    blk = Lc[:hh, :ww].reshape(hh // 8, 8, ww // 8, 8).std(axis=(1, 3))
    grain = float(np.percentile(blk, 25))                                   # 평평한 곳(하위 25% 칸)의 잔떨림
    bgL = float(np.median(np.concatenate([Lc[0], Lc[-1], Lc[:, 0], Lc[:, -1]])))
    wgt = np.abs(Lc - bgL)
    yy, xx = np.mgrid[0:Lc.shape[0], 0:Lc.shape[1]]
    cx = float((wgt * xx).sum() / (wgt.sum() + 1e-6) / Lc.shape[1])
    cy = float((wgt * yy).sum() / (wgt.sum() + 1e-6) / Lc.shape[0])
    sym = float(1 - np.abs(Lc - Lc[:, ::-1]).mean() / (np.abs(Lc - Lc.mean()).mean() * 2 + 1e-6))
    res = {'palette': pal, 'colors_used': len(used), 'light_tiers': tiers,
           'contrast_L': (Ls[-1] - Ls[0]) if Ls else 0,
           'chroma_mean': round(sum(p['C'] * p['area'] for p in pal) / 100, 1),
           'neutral_pct': min(100.0, round(sum(p['area'] for p in pal if p['C'] < 10), 1)),
           'warm_pct': round(sum(p['area'] for p in pal if p['temp'] == '따뜻'), 1),
           'cool_pct': round(sum(p['area'] for p in pal if p['temp'] == '차가움'), 1),
           'soft_pct': round(100 * soft), 'sharp_pct': round(100 * sharp), 'softness': round(softness, 2),
           'render': '평면' if softness < 1.0 else ('섞임' if softness < 1.8 else '사진·그라데이션'),
           'grain': round(grain, 2), 'texture': '깨끗' if grain < 0.8 else ('미세 질감' if grain < 2.5 else '거친 질감'),
           'center': [round(100 * cx), round(100 * cy)], 'symmetry': round(100 * max(0.0, sym)), 'shape': shape}
    if shape.get('segments', 0) < 40:                 # 글자 말고는 경계가 거의 없다(글만 있는 판 · 매끈한 3D)
        res['hardness'] = '확인 못 함(글 말고 모양이 거의 없음)'
    elif 'straight' in shape:
        res['hardness'] = '딱딱함' if shape['straight'] >= 60 else ('중간' if shape['straight'] >= 40 else '부드러움')
        cp = shape.get('corners_per_1000px', 0)
        res['edge_feel'] = '뾰족함' if cp >= 60 else ('매끈함' if cp <= 25 else '보통')   # 꺾인 모서리 밀도(직선·곡선과 따로 본다 — 폭발 그래픽은 곡선이어도 뾰족하다)
    json.dump(res, open(os.path.join(folder, 'style.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    _style_png(folder, sm, edges, lm, res)
    return res


def _style_png(folder, sm, edges, lines, r):
    """한 장: 왼쪽 = 원본 축소 · 가운데 = 경계(직선 청록, 곡선·자유선 자홍) · 오른쪽 = 색 막대(넓이 비례)와 숫자"""
    h, w = sm.shape[:2]
    ev = np.full((h, w, 3), 250, np.uint8)
    if lines is not None:
        on = lines.any(axis=2)
        ev[on] = lines[on]
    panel = Image.new('RGB', (w * 2 + 380, h), (250, 250, 248))
    panel.paste(Image.fromarray(sm), (0, 0))
    panel.paste(Image.fromarray(ev), (w, 0))
    d = ImageDraw.Draw(panel)
    x, y = w * 2 + 16, 10
    for p in r['palette']:
        bh = max(3, int((h - 150) * p['area'] / 100))
        d.rectangle([x, y, x + 60, y + bh], fill=p['hex'], outline=(200, 200, 200))
        if bh >= 14:
            d.text((x + 70, y + bh / 2 - 9), f"{p['area']}% L{p['L']} C{p['C']} {p['name']}", font=_font(15), fill=(40, 40, 40))
        y += bh + 2
    sh = r['shape']
    rows = [f"색 {r['colors_used']}개, 밝기 {r['light_tiers']}단, 대비 {r['contrast_L']}",
            f"채도 {r['chroma_mean']}, 무채 {r['neutral_pct']}%, {r['render']}",
            f"직선 {sh.get('straight', '-')}% 곡선 {sh.get('curved', '-')}% 꺾임 {sh.get('corners_per_1000px', '-')}/1000px ({r.get('hardness', '-')})",
            f"수평 {sh.get('horizontal', '-')} 수직 {sh.get('vertical', '-')} 사선 {sh.get('diagonal', '-')}",
            f"덩어리 {', '.join(f'{k} {v}' for k, v in sh.get('blobs', {}).items())}",
            f"질감 {r['texture']}({r['grain']}), 중심 {r['center']}, 대칭 {r['symmetry']}"]
    yy = h - 145
    for t in rows:
        d.text((w * 2 + 12, yy), t, font=_font(13), fill=(30, 30, 30))
        yy += 23
    panel.save(os.path.join(folder, 'style.png'))


# ───────────────────────── 모으기 ─────────────────────────

def summary(root):
    rows = []
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name, 'analysis.json')
        if os.path.exists(p):
            rows.append((name, json.load(open(p, encoding='utf-8'))))
    if not rows:
        return None
    gx, gy = HEAT
    ht = np.mean([np.array(r['heat_text']) for _, r in rows], axis=0)
    withimg = [r for _, r in rows if r['images']]      # 판 전체 그림(bg)은 열지도에서 뺀다 — 전부 진해져 아무것도 안 보인다(10-20)
    hi = np.mean([np.array(r['heat_image']) for r in withimg], axis=0) if withimg else np.zeros((HEAT[1], HEAT[0]))
    _heat_png(ht, hi, os.path.join(root, 'heat.png'), len(rows), len(withimg))
    L = ['# 포스터 그리드 모음표', '',
         '> **뭐냐:** 해부한 레퍼런스 전부의 숫자를 한 장에 모은 표와 경향(`python -m ad pgrid summary` 가 다시 씀 — 손으로 고치지 마라).',
         '> **언제 읽나:** 포스터 배치를 잡기 «전», «제목은 판의 몇 %», «그림은 어디에 얼마나» 를 정할 때.',
         '> **안 담는 것:** 한 장씩의 근거 → 각 폴더 `REPORT.md` · 레퍼런스 목록·출처 → `INDEX.md` · 방법 → `protocols/promo.md`.', '',
         f"레퍼런스 {len(rows)}장(그림이 판 전체를 덮는 판 {sum(1 for _, r in rows if r['full_bleed_art'])}장). 열지도: `heat.png`(왼쪽 = 글자 자리, 오른쪽 = 따로 놓인 그림 자리, 가장 많이 쓴 칸을 가장 진하게).", '',
         '| 레퍼런스 | 비 | 단 | 여백 왼·위 % | 제목 %H | 단계 수 | 단계 배율 | 그림 넓이 % | 그림 자리 | 판 밖 | 글↔그림 | 그림÷제목 높이 | 빈 곳 % |',
         '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    stat = {'head': [], 'ratio': [], 'imgarea': [], 'empty': [], 'cols': [], 'imgx': [], 'mL': []}
    for name, r in rows:
        lv = r['type_levels']
        head = lv[0]['pct_H'] if lv else None
        steps = '·'.join(f"{l['x_next']}" for l in lv if l['x_next'])
        big = max(r['images'], key=lambda i: i['area_pct']) if r['images'] else None
        rel = r['relation']
        c = r['columns']
        L.append(f"| {name} | {r['ratio']} | {(str(c['n']) + ('' if c['hit'] >= 3 else '?')) if c else '-'} | {r['margins_pct']['L']}·{r['margins_pct']['T']} | {head or '-'} | {len(lv)} | {steps or '-'} | "
                 f"{big['area_pct'] if big else ('전면' if r['full_bleed_art'] else '-')} | {big['where'] if big else '-'} | {','.join(big['bleed']) if big else '-'} | "
                 f"{rel.get('text_vs_image_split', '-')} | {rel.get('img_h_over_head_h', '-')} | {r['empty_pct']} |")
        if head: stat['head'].append(head)
        stat['ratio'] += [l['x_next'] for l in lv if l['x_next']]
        if big: stat['imgarea'].append(big['area_pct']); stat['imgx'].append(big['where'])
        stat['empty'].append(r['empty_pct'])
        if c and c['hit'] >= 3: stat['cols'].append(c['n'])
        if r['margins_pct']['L'] is not None: stat['mL'].append(r['margins_pct']['L'])

    def rng(v):
        return f"중앙값 {np.median(v):.1f} (범위 {min(v):.1f}~{max(v):.1f}, {len(v)}장)" if v else '자료 없음'
    from collections import Counter
    L += ['', '## 경향 (숫자만 — 해석은 아래 «읽은 것»에)', '',
          f"- 제목 글자 높이(판 높이 대비 %): {rng(stat['head'])}",
          f"- 글자 단계 사이 배율: {rng(stat['ratio'])}",
          f"- 가장 큰 그림 넓이(판 대비 %): {rng(stat['imgarea'])}",
          f"- 왼쪽 여백(판 폭 대비 %): {rng(stat['mL'])}",
          f"- 빈 곳 %: {rng(stat['empty'])}",
          f"- 그림 자리: {', '.join(f'{k} {v}' for k, v in Counter(stat['imgx']).most_common()) or '자료 없음'}",
          f"- 단 수(근거 셋 이상인 것만): {', '.join(f'{k}단 {v}장' for k, v in sorted(Counter(stat['cols']).items())) or '자료 없음'}"]
    # 색·모양 표 + 팔레트 띠 한 장(palettes.png)
    st_rows = [(name, r['style']) for name, r in rows if (r.get('style') or {}).get('palette')]
    if st_rows:
        L += ['', '## 색·모양 모음 (`palettes.png` = 한 줄에 한 장, 넓이 비례 색 띠)', '',
              '| 레퍼런스 | 쓴 색 | 밝기 단 | 대비 | 채도 | 무채 % | 따뜻·차가움 % | 칠한 법 | 질감 | 모양 | 직선·곡선 % | 꺾임/1000px | 대칭 |',
              '|---|---|---|---|---|---|---|---|---|---|---|---|---|']
        for name, t in st_rows:
            sh = t['shape']
            L.append(f"| {name} | {t['colors_used']} | {t['light_tiers']} | {t['contrast_L']} | {t['chroma_mean']} | {t['neutral_pct']} | {t['warm_pct']}·{t['cool_pct']} | "
                     f"{t['render']} | {t['texture']} | {t.get('hardness', '-')}, {t.get('edge_feel', '-')} | {sh.get('straight', '-')}·{sh.get('curved', '-')} | {sh.get('corners_per_1000px', '-')} | {t['symmetry']} |")
        g = lambda k: [t[k] for _, t in st_rows]
        hard = Counter(t.get('hardness', '-') for _, t in st_rows)
        rend = Counter(t['render'] for _, t in st_rows)
        L += ['', f"- 쓴 색 수: {rng(g('colors_used'))}", f"- 밝기 대비(L*): {rng(g('contrast_L'))}", f"- 평균 채도: {rng(g('chroma_mean'))}",
              f"- 무채색 넓이 %: {rng(g('neutral_pct'))}",
              f"- 칠한 법: {', '.join(f'{k} {v}장' for k, v in rend.most_common())}",
              f"- 모양: {', '.join(f'{k} {v}장' for k, v in hard.most_common())}",
              f"- 직선 비율(모양 잰 판만): {rng([t['shape']['straight'] for _, t in st_rows if t['shape'].get('segments', 0) >= 40])}"]
        _palettes_png([(n, t) for n, t in st_rows], os.path.join(root, 'palettes.png'))
    L += ['', '## 읽은 것 (사람·에이전트가 쓴다 — summary 를 다시 돌리면 이 아래는 지켜진다)', '']
    keep = ''
    sp = os.path.join(root, 'SUMMARY.md')
    if os.path.exists(sp):
        old = open(sp, encoding='utf-8').read()
        if '## 읽은 것' in old:
            keep = old.split('## 읽은 것', 1)[1].split('\n', 1)[1] if '\n' in old.split('## 읽은 것', 1)[1] else ''
    out = '\n'.join(L) + '\n' + (keep.lstrip('\n') if keep.strip() else '- \n\n---\n\n## 변경 이력\n- 자동 생성\n')
    open(sp, 'w', encoding='utf-8').write(out)
    return sp


def _palettes_png(rows, path):
    """한 줄 = 레퍼런스 한 장: 작은 원본 + 넓이 비례 색 띠 + 모양 한 마디"""
    rh, tw, bw = 64, 46, 760
    im = Image.new('RGB', (tw + bw + 420, rh * len(rows) + 10), (250, 250, 248))
    d = ImageDraw.Draw(im)
    root = os.path.dirname(path)
    for i, (name, t) in enumerate(rows):
        y = 5 + i * rh
        try:
            th = Image.open(os.path.join(root, name, 'poster.png')).convert('RGB')
            th.thumbnail((tw, rh - 6))
            im.paste(th, (2, y))
        except OSError:
            pass
        x = tw + 8
        for p in t['palette']:
            w = int(bw * p['area'] / 100)
            if w > 0:
                d.rectangle([x, y + 4, x + w, y + rh - 10], fill=p['hex'])
            x += w
        sh = t['shape']
        d.text((tw + bw + 16, y + 6), name, font=_font(13), fill=(30, 30, 30))
        d.text((tw + bw + 16, y + 26), f"색 {t['colors_used']} · {t['render']} · {t.get('hardness', '-')[:6]} · 직선 {sh.get('straight', '-')}%", font=_font(13), fill=(90, 90, 90))
    im.save(path)


def _heat_png(ht, hi, path, n, ni=None):
    gx, gy = HEAT
    cs = 40
    pad = 30
    im = Image.new('RGB', (2 * gx * cs + 3 * pad, gy * cs + 2 * pad + 30), (250, 250, 248))
    d = ImageDraw.Draw(im)
    f = _font(16)
    for k, (m, col, lab) in enumerate(((ht, (0, 120, 200), f'글자 자리 ({n}장)'), (hi, (210, 30, 130), f'따로 놓인 그림 자리 ({ni if ni is not None else n}장)'))):
        m = np.array(m) / max(1e-6, float(np.max(m)))
        ox = pad + k * (gx * cs + pad)
        d.text((ox, 6), lab, font=f, fill=(30, 30, 30))
        for j in range(gy):
            for i in range(gx):
                v = float(m[j][i])
                c = tuple(int(255 - (255 - cc) * v) for cc in col)
                d.rectangle([ox + i * cs, pad + j * cs, ox + (i + 1) * cs - 1, pad + (j + 1) * cs - 1], fill=c)
        d.rectangle([ox, pad, ox + gx * cs, pad + gy * cs], outline=(60, 60, 60), width=2)
    im.save(path)
