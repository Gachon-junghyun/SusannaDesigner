# -*- coding: utf-8 -*-
"""포스터 레퍼런스를 «데이터»로 쓰기 — pgrid 가 잰 것(analysis.json · blocks.json · tags.json)을 모아 다시 쓴다.

tag     : 레퍼런스 꼬리표(유형·서체·대소문자·쓰임·분위기·시대·써도 되나) — vocab.json 밖 낱말은 거부
table   : 한 장 = 한 줄 전체 표(table.csv) + 글·그림 상자 한 개 = 한 줄(elements.csv). 엑셀에서 바로 연다(UTF-8 BOM)
types   : 유형마다 수치 기준(중앙값·최소·최대)과 역할 기준(날짜는 제목의 몇 분의 1, 로고 크기·자리) → types.json
check   : 우리 시안을 같은 자로 재서 가장 가까운 유형과 비교 → CHECK.md · check.png (기준 밖인 칸을 숫자로)
pick    : 시안을 고른 기록 한 줄(picks.csv) · picks 로 유형별 집계
embed   : 레퍼런스 그림 지문(CLIP) → emb.npz · similar 로 «이 그림과 비슷한 레퍼런스», «빨간 타이포 포스터» 같은 말로 찾기
picker  : 고르기 창(ad picker) 레퍼런스 모음(items.json)을 다시 쓴다 — 유형별로 창에서 넘겨 본다

모든 산출물은 레퍼런스 창고(refs/_모음/포스터_그리드/, 비공개) 안에 둔다. 남의 포스터 그림은 창고 밖으로 내보내지 않는다.
"""
import csv
import io
import json
import math
import os
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', 'refs', '_모음', '포스터_그리드')
FEATS = [  # (키, 이름, 보기 단위)
    ('head', '제목 글자 높이', '%H'), ('head_w', '제목 폭', '%W'), ('step', '둘째 글과의 크기 차이', '배'), ('levels', '글자 크기 단계', '단계'),
    ('small', '가장 작은 글', '%H'), ('img', '가장 큰 그림 넓이', '%'), ('empty', '빈 곳', '%'), ('mL', '왼쪽 여백', '%W'),
    ('colors', '쓴 색', '가지'), ('neutral', '무채색 넓이', '%'), ('chroma', '평균 채도', ''), ('contrast', '밝기 대비', ''),
    ('straight', '직선 비율', '%'), ('ttop', '글자 중 위 3분의 1에 있는 비율', '%'), ('tbot', '글자 중 아래 3분의 1에 있는 비율', '%'),
]
DIST = {'full': 1.5, 'head': 1.5, 'img': 1.2, 'step': 1.0, 'empty': 1.0, 'neutral': 0.8, 'chroma': 0.8, 'straight': 0.6, 'ttop': 1.0, 'tbot': 1.0, 'levels': 0.6}


def refs(root=ROOT):
    return sorted(d for d in os.listdir(root) if os.path.isfile(os.path.join(root, d, 'analysis.json')))


def load(d, root=ROOT):
    j = lambda n: json.load(open(os.path.join(root, d, n), encoding='utf-8')) if os.path.exists(os.path.join(root, d, n)) else {}
    return j('analysis.json'), j('blocks.json'), j('tags.json')


def features(a):
    """analysis.json → 비교용 숫자. 없는 값은 None"""
    lv = a.get('type_levels') or []
    st = a.get('style') or {}
    sh = st.get('shape') or {}
    tb = a.get('text_blocks') or []
    head_w = None
    if tb:
        hb = max(tb, key=lambda p: p['ink_h'])
        head_w = round(100 * (hb['bbox'][2] - hb['bbox'][0]) / a['W'], 1)
    img = max((i['area_pct'] for i in a.get('images') or []), default=None)
    if img is None and a.get('full_bleed_art'):
        img = 100.0
    ht = np.array(a.get('heat_text') or [[0]])
    tot = ht.sum() or 1
    third = max(1, ht.shape[0] // 3)
    return {
        'full': 1.0 if a.get('full_bleed_art') else 0.0,
        'head': lv[0]['pct_H'] if lv else None, 'head_w': head_w,
        'step': lv[0]['x_next'] if len(lv) > 1 else 1.0, 'levels': len(lv), 'small': lv[-1]['pct_H'] if lv else None,
        'img': img if img is not None else 0.0, 'empty': a.get('empty_pct'), 'mL': (a.get('margins_pct') or {}).get('L'),
        'colors': st.get('colors_used'), 'neutral': st.get('neutral_pct'), 'chroma': st.get('chroma_mean'), 'contrast': st.get('contrast_L'),
        'straight': sh.get('straight') if sh.get('segments', 0) >= 40 else None,
        'ttop': round(100 * float(ht[:third].sum() / tot), 1), 'tbot': round(100 * float(ht[-third:].sum() / tot), 1),
    }


# ───────────────────────── 꼬리표 ─────────────────────────

def vocab(root=ROOT):
    return json.load(open(os.path.join(root, 'vocab.json'), encoding='utf-8'))


def tag(folder, pairs, root=ROOT):
    """pairs = ['type=D', 'mood=대담,차분', 'title=…'] — 목록 칸은 쉼표로. vocab 밖 낱말이면 멈춘다"""
    V = vocab(root)
    p = os.path.join(folder, 'tags.json')
    t = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    for kv in pairs:
        k, _, v = kv.partition('=')
        if k in ('typeface', 'use', 'mood'):
            vals = [x.strip() for x in v.split(',') if x.strip()]
        else:
            vals = v.strip()
        if k in V:
            bad = [x for x in (vals if isinstance(vals, list) else [vals]) if x not in V[k]]
            if bad:
                raise ValueError(f'{k} 에 없는 낱말 {bad} — vocab.json 에 먼저 더한다. 쓸 수 있는 것: {V[k]}')
        t[k] = vals
    json.dump(t, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return t


# ───────────────────────── 표 ─────────────────────────

def table(root=ROOT):
    rows, els = [], []
    for d in refs(root):
        a, b, t = load(d, root)
        f = features(a)
        st = a.get('style') or {}
        ro = a.get('roles') or {}
        rows.append({
            'id': d, 'title': t.get('title', ''), 'site': t.get('site', ''), 'url': t.get('url', ''), 'ok': t.get('ok', b.get('own', '')),
            'type': t.get('type', ''), 'typeface': ' / '.join(t.get('typeface', [])), 'case': t.get('case', ''), 'use': ' / '.join(t.get('use', [])),
            'mood': ' / '.join(t.get('mood', [])), 'era': t.get('era', ''), 'ratio': a.get('ratio'),
            **{k: f[k] for k in ('head', 'head_w', 'step', 'levels', 'small', 'img', 'empty', 'mL', 'colors', 'neutral', 'chroma', 'contrast', 'straight', 'ttop', 'tbot')},
            'full_bleed': int(f['full']), 'relation': (a.get('relation') or {}).get('text_vs_image_split', ''),
            'img_where': ', '.join(sorted({i['where'] for i in a.get('images') or []})),
            'columns': (a.get('columns') or {}).get('n') if not (a.get('columns') or {}).get('ruler') else '',
            'render': st.get('render', ''), 'hardness': st.get('hardness', ''), 'edge_feel': st.get('edge_feel', ''),
            'symmetry': st.get('symmetry'), 'warm': st.get('warm_pct'), 'cool': st.get('cool_pct'),
            'palette': ' '.join(p['hex'] + f"({p['area']})" for p in (st.get('palette') or []) if p['area'] >= 3),
            'date_x_head': (ro.get('날짜') or {}).get('x_head'), 'date_where': (ro.get('날짜') or {}).get('where', ''),
            'place_x_head': (ro.get('장소') or {}).get('x_head'), 'sub_x_head': (ro.get('부제') or {}).get('x_head'),
            'logo_w': (ro.get('로고') or {}).get('w_pct'), 'logo_where': (ro.get('로고') or {}).get('where', ''),
        })
        W, H = b.get('W', 1), b.get('H', 1)
        for it in b.get('items', []):
            x0, y0, x1, y1 = it['bbox']
            els.append({'id': d, 'item': it['id'], 'kind': it['kind'], 'role': it.get('role', ''), 'text': it.get('text', ''),
                        'x0': round(100 * x0 / W, 1), 'y0': round(100 * y0 / H, 1), 'x1': round(100 * x1 / W, 1), 'y1': round(100 * y1 / H, 1),
                        'ink_h': round(100 * it['ink_h'] / H, 2) if it.get('ink_h') else '', 'rot': int(bool(it.get('rot'))), 'color': it.get('color') or ''})
    _csv(os.path.join(root, 'table.csv'), rows)
    _csv(os.path.join(root, 'elements.csv'), els)
    return len(rows), len(els)


def _csv(path, rows):
    if not rows:
        return
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: ('' if v is None else v) for k, v in r.items()})


# ───────────────────────── 유형 기준 ─────────────────────────

def types(root=ROOT):
    defs = json.load(open(os.path.join(root, 'types_def.json'), encoding='utf-8'))
    by = {}
    for d in refs(root):
        a, b, t = load(d, root)
        if t.get('type'):
            by.setdefault(t['type'], []).append((d, a, features(a)))
    out = {}
    for k, members in sorted(by.items()):
        fs = [m[2] for m in members]
        stats = {}
        for key in list(DIST) + ['head_w', 'small', 'mL', 'colors', 'contrast']:
            v = [f[key] for f in fs if f.get(key) is not None]
            if v:
                stats[key] = {'med': round(float(np.median(v)), 2), 'min': round(float(min(v)), 2), 'max': round(float(max(v)), 2), 'n': len(v)}
        roles = {}
        for r in ('부제', '날짜', '장소', '로고'):
            xs = [(m[1].get('roles') or {}).get(r) for m in members]
            xs = [x for x in xs if x]
            if xs:
                e = {'n': len(xs)}
                hx = [x['x_head'] for x in xs if x.get('x_head')]
                if hx:
                    e['x_head'] = {'med': round(float(np.median(hx)), 3), 'min': round(min(hx), 3), 'max': round(max(hx), 3)}
                if r == '로고':
                    e['w_pct'] = round(float(np.median([x['w_pct'] for x in xs])), 1)
                wh = [x['where'] for x in xs]
                e['where'] = max(set(wh), key=wh.count)
                roles[r] = e
        out[k] = {**(defs.get(k) or {}), 'members': [m[0] for m in members], 'stats': stats, 'roles': roles}
    json.dump(out, open(os.path.join(root, 'types.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return out


def _scale(root=ROOT):
    """거리 재기용 표준편차(레퍼런스 전체)"""
    F = [features(load(d, root)[0]) for d in refs(root)]
    sc = {}
    for k in DIST:
        v = [_tf(k, f[k]) for f in F if f.get(k) is not None]
        sc[k] = float(np.std(v)) or 1.0
    return sc


def _tf(k, v):
    return math.log(max(v, 0.3)) if k in ('head', 'step') else v


def nearest_types(f, T, sc):
    out = []
    for k, t in T.items():
        s, n = 0.0, 0
        for key, w in DIST.items():
            if f.get(key) is None or key not in t['stats']:
                continue
            s += w * ((_tf(key, f[key]) - _tf(key, t['stats'][key]['med'])) / sc[key]) ** 2
            n += w
        out.append((math.sqrt(s / max(n, 1e-6)), k))
    return sorted(out)


# ───────────────────────── 시안 검사 ─────────────────────────

def check(img, out=None, spec=None, crop='none', root=ROOT):
    """우리 시안 한 장 → 같은 자로 재고 가장 가까운 유형 둘과 비교. spec 을 주면 detect 뒤 fix 로 고친다(역할 «T3 는 날짜» 등)"""
    from . import pgrid
    out = out or os.path.splitext(img)[0] + '_검사'
    if not os.path.exists(os.path.join(out, 'blocks.json')) or spec is None:
        pgrid.detect(img, out, crop=crop, src=os.path.abspath(img), own='우리 것')
    if spec:
        pgrid.fix(out, spec)
    a = pgrid.analyze(out)
    f = features(a)
    T = json.load(open(os.path.join(root, 'types.json'), encoding='utf-8'))
    near = nearest_types(f, T, _scale(root))
    sims = []
    try:
        sims = similar(os.path.join(out, 'poster.png'), k=5, root=root)
    except Exception:
        pass
    L = [f'# 시안 검사 {os.path.basename(img)}', '',
         '> 레퍼런스 창고의 유형 기준과 같은 자로 잰 비교다(`python -m ad pgrid check`). 숫자는 `analysis.json`, 그리드는 `grid.png`, 색과 모양은 `style.png`.', '']
    L.append('가장 가까운 유형: ' + ', '.join(f"{k}({T[k].get('name', '')}, 거리 {d:.2f})" for d, k in near[:3]))
    if len(near) > 1 and near[1][0] - near[0][0] < 0.05:
        L.append('')
        L.append('판정 약함: 첫째와 둘째 유형의 거리 차이가 0.05 미만이다. 이 시안은 한 유형에 딱 맞지 않는 혼합형으로 읽힌다.')
    L += ['', '판정 기준: 크기 칸(제목 높이·폭, 크기 차이, 그림 넓이, 여백)은 유형 중앙값의 0.7~1.4배면 비슷, 비율 칸(빈 곳, 무채색, 글자 자리, 직선)은 15%포인트 안이면 비슷, 쓴 색은 1가지 안, 밝기 대비는 15 안. 레퍼런스가 5장 미만인 유형은 기준이 약하다.']
    for d, k in near[:2]:
        t = T[k]
        L += ['', f"## 유형 {k}. {t.get('name', '')} 과 비교 (레퍼런스 {len(t['members'])}장 기준)", '',
              '| 항목 | 우리 시안 | 유형 중앙값 | 유형 범위 | 판정 |', '|---|---|---|---|---|']
        for key, name, unit in FEATS:
            st = t['stats'].get(key)
            if st is None or f.get(key) is None:
                continue
            v = f[key]
            L.append(f"| {name} | {v}{unit} | {st['med']}{unit} | {st['min']}~{st['max']} | {_verdict(key, v, st['med'])} |")
        ro = a.get('roles') or {}
        for r in ('부제', '날짜', '장소'):
            tr = (t.get('roles') or {}).get(r)
            if tr and tr.get('x_head') and (ro.get(r) or {}).get('x_head'):
                v = ro[r]['x_head']; x = tr['x_head']
                L.append(f"| {r} 크기(제목 대비) | {v}배 | {x['med']}배 | {x['min']}~{x['max']} | {_verdict('step', v, x['med'])} |")
        if (t.get('roles') or {}).get('로고') and (ro.get('로고') or {}).get('w_pct'):
            L.append(f"| 로고 폭 | {ro['로고']['w_pct']}%W ({ro['로고']['where']}) | {t['roles']['로고']['w_pct']}%W ({t['roles']['로고']['where']}) | | |")
        rules = t.get('rules') or []
        if rules:
            L += ['', '이 유형의 쓰는 법:'] + [f'{i + 1}. {r}' for i, r in enumerate(rules)]
    if sims:
        L += ['', '## 비슷한 레퍼런스(그림 지문)', ''] + [f"{i + 1}. {s['id']} {s.get('title', '')} (유형 {s.get('type', '')}, 닮음 {s['score']:.2f})" for i, s in enumerate(sims)]
    picks = _picks(root)
    if picks:
        L += ['', '## 지난 고른 기록', '', picks_summary(root, as_text=True)]
    open(os.path.join(out, 'CHECK.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    return {'out': out, 'nearest': near[:3], 'features': f}


def _verdict(key, v, med):
    if key in ('head', 'head_w', 'step', 'img', 'small', 'mL', 'levels', 'chroma'):
        if med in (0, None) or v is None:
            return '비교 못 함'
        r = v / med
        return '비슷' if 0.7 <= r <= 1.4 else (f'작음(중앙값의 {r:.2f}배)' if r < 0.7 else f'큼(중앙값의 {r:.2f}배)')
    if key == 'colors':
        return '비슷' if abs(v - med) <= 1 else ('적음' if v < med else '많음')
    if key == 'contrast':
        return '비슷' if abs(v - med) <= 15 else ('약함' if v < med else '강함')
    d = v - med
    return '비슷' if abs(d) <= 15 else (f'적음({d:+.0f}%포인트)' if d < 0 else f'많음({d:+.0f}%포인트)')


# ───────────────────────── 고른 기록 ─────────────────────────

PICK_COLS = ['when', 'job', 'who', 'file', 'type', 'result', 'note', 'head', 'step', 'img', 'empty', 'colors', 'neutral', 'straight']


def pick(file, result, type_='', who='작업자님', job='', note='', root=ROOT):
    """result = 고름 | 안 고름 | 고쳐서 고름. file 이 검사 폴더(analysis.json 있는 곳)나 그림이면 숫자를 같이 남긴다"""
    f = {}
    for cand in (file, os.path.splitext(file)[0] + '_검사'):
        p = os.path.join(cand, 'analysis.json')
        if os.path.isfile(p):
            f = features(json.load(open(p, encoding='utf-8')))
            break
    row = {'when': time.strftime('%Y-%m-%d %H:%M'), 'job': job, 'who': who, 'file': os.path.abspath(file), 'type': type_, 'result': result, 'note': note,
           **{k: f.get(k, '') for k in ('head', 'step', 'img', 'empty', 'colors', 'neutral', 'straight')}}
    path = os.path.join(root, 'picks.csv')
    new = not os.path.exists(path)
    with open(path, 'a', encoding='utf-8-sig' if new else 'utf-8', newline='') as fp:
        w = csv.DictWriter(fp, fieldnames=PICK_COLS)
        if new:
            w.writeheader()
        w.writerow({k: ('' if row.get(k) is None else row.get(k, '')) for k in PICK_COLS})
    return row


def _picks(root=ROOT):
    p = os.path.join(root, 'picks.csv')
    if not os.path.exists(p):
        return []
    return list(csv.DictReader(open(p, encoding='utf-8-sig')))


def picks_summary(root=ROOT, as_text=False):
    P = _picks(root)
    by = {}
    for r in P:
        by.setdefault(r['type'] or '미정', {}).setdefault(r['result'], 0)
        by[r['type'] or '미정'][r['result']] += 1
    if not as_text:
        return by
    if not P:
        return '기록 없음'
    lines = [f"전체 {len(P)}건"] + [f"유형 {k}: " + ', '.join(f'{rk} {n}건' for rk, n in v.items()) for k, v in sorted(by.items())]
    chosen = [r for r in P if r['result'].startswith('고') and r.get('head')]
    if chosen:
        lines.append('고른 시안의 제목 높이 중앙값 ' + f"{np.median([float(r['head']) for r in chosen]):.1f}%H")
    return '\n'.join(f'- {x}' for x in lines)


# ───────────────────────── 그림 지문 ─────────────────────────

MODEL = 'openai/clip-vit-base-patch32'
_CLIP = None


def _clip():
    global _CLIP
    if _CLIP is None:
        import torch
        from transformers import CLIPModel, CLIPProcessor               # 무거운 의존은 함수 안에서만
        dev = 'cuda' if torch.cuda.is_available() else 'cpu'
        _CLIP = (CLIPModel.from_pretrained(MODEL).to(dev).eval(), CLIPProcessor.from_pretrained(MODEL), dev, torch)
    return _CLIP


def _img_vec(paths):
    from PIL import Image
    m, pr, dev, torch = _clip()
    with torch.no_grad():
        x = pr(images=[Image.open(p).convert('RGB') for p in paths], return_tensors='pt').to(dev)
        v = m.get_image_features(**x)
        v = getattr(v, 'pooler_output', v)
    v = v.float().cpu().numpy()
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def _text_vec(q):
    m, pr, dev, torch = _clip()
    with torch.no_grad():
        x = pr(text=[q], return_tensors='pt', padding=True).to(dev)
        v = m.get_text_features(**x)
        v = getattr(v, 'pooler_output', v)
    v = v.float().cpu().numpy()
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def embed(root=ROOT):
    ids = [d for d in refs(root) if os.path.exists(os.path.join(root, d, 'poster.png'))]
    vecs = np.concatenate([_img_vec([os.path.join(root, d, 'poster.png') for d in ids[i:i + 8]]) for i in range(0, len(ids), 8)])
    np.savez(os.path.join(root, 'emb.npz'), ids=np.array(ids), vecs=vecs, model=MODEL)
    return len(ids)


def similar(query, k=5, root=ROOT):
    """query = 그림 경로 · 레퍼런스 폴더 이름 · 영어 낱말(«red typographic poster»)"""
    z = np.load(os.path.join(root, 'emb.npz'))
    ids, V = [str(x) for x in z['ids']], z['vecs']
    if query in ids:
        q = V[ids.index(query)][None]
    elif os.path.isfile(query):
        q = _img_vec([query])
    else:
        q = _text_vec(query)
    s = (V @ q[0])
    order = np.argsort(-s)
    out = []
    for i in order:
        if ids[i] == query or s[i] > 0.985:            # 자기 자신(같은 그림)은 뺀다
            continue
        t = load(ids[i], root)[2]
        out.append({'id': str(ids[i]), 'score': float(s[i]), 'title': t.get('title', ''), 'type': t.get('type', '')})
        if len(out) >= k:
            break
    return out


# ───────────────────────── 고르기 창 ─────────────────────────

def picker_items(root=ROOT):
    T = {}
    tp = os.path.join(root, 'types.json')
    if os.path.exists(tp):
        T = json.load(open(tp, encoding='utf-8'))
    items = []
    for d in refs(root):
        a, b, t = load(d, root)
        f = features(a)
        ty = t.get('type', '')
        items.append({'file': f'{d}/poster.png', 'name': t.get('title') or d,
                      'region': f"유형 {ty} {T.get(ty, {}).get('name', '')}".strip() if ty else '유형 없음',
                      'note': f"제목 {f['head']}%H, 그림 {f['img']}%, 쓴 색 {f['colors']}, {(a.get('style') or {}).get('render', '')}, {(a.get('style') or {}).get('hardness', '')}",
                      'tags': t.get('typeface', []) + t.get('mood', []) + t.get('use', []), 'dark': False,
                      'site': t.get('url', ''), 'src': t.get('url', ''), 'own': t.get('ok', '내부 참고만')})
    meta = {'title': '포스터 그리드', 'made': time.strftime('%Y-%m-%d'), 'by': 'Claude',
            'why': '포스터 레퍼런스를 그리드·글자 크기·그림 자리·색·모양으로 잰 모음. 유형(구도) 이름으로 거른다.',
            'own': '남의 것이 대부분이다. 창에서 보고 결만 말로 옮긴다(그림을 닮게 뽑는 데 넣지 않는다)', 'items': items}
    json.dump(meta, open(os.path.join(root, 'items.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return len(items)
