# -*- coding: utf-8 -*-
"""
레퍼런스 창고 — 디자인 나무의 개념마다 «참고 그림 + 프롬프트 조각»을 모은다. 🔴 비공개다.

- 개념 목록(나무)의 원본은 드로우사인 사이트의 `content/design-tree.ts` 하나다(간판 방식·재질·조명·벽 잎은 거기서 `config/tree.ts` 를 읽는다). 여기 폴더는 그걸 «따라» 만든다(scaffold) —
  나무를 두 벌로 적지 않는다(한쪽만 고치면 갈린다).
- 🔴 여기엔 남의 로고·사진(저작권·상표 있는 것)도 둔다. 프롬프트를 만들 때 참고로 쓰는 내부 자료다.
  **사이트(public/)·깃·드라이브 공유로 옮기지 마라.** 손님에게 보이는 건 제미나이로 뽑은 샘플뿐이다(사이트 `> 샘플)` 줄).
  이 폴더(STARTUP)는 git 도 원격도 없는 이 PC 전용이다(2026-09-28 확인).
- 남의 로고를 `--ref` 로 넣어 «닮게» 뽑지 마라(STAGES 3) — 결(선 굵기·구도·색 수)을 말로 옮기는 데 쓴다. 참고 파일은 결만 가져가라.

REFS.md 한 장 = 개념 하나:
    # 로고/유형/심벌형
    프롬프트: flat vector logo symbol, solid fills only, ...
    ## 레퍼런스
    - 파일.jpg :: 출처(URL 또는 run) :: 우리 것 | 남의 것 :: 왜 모았나
"""
import io
import os
import re
import shutil

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(HERE, 'refs')
TREE_TS = os.path.join(os.path.expanduser('~'), 'HOMEPAGE_MAKER', 'sites', 'drawsign', 'content', 'design-tree.ts')
COMBO_TS = os.path.join(os.path.expanduser('~'), 'HOMEPAGE_MAKER', 'sites', 'drawsign', 'config', 'tree.ts')
KEEP = '_보관'   # 나무에서 빠진 옛 개념의 레퍼런스 — 지우지 않고 여기 둔다(scaffold 가 «나무에 없는 폴더»로 안 센다)
IMG = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.svg')


def combo_leaves(branch):
    """config/tree.ts(/combo) 의 한 칸 → [(이름, 이럴 때 좋아요)] — 나무의 `> 잎) combo:<칸>` 줄이 이걸 펼친다(사이트 lib/designTree.ts 와 같은 규칙)"""
    src = io.open(COMBO_TS, encoding='utf-8').read()
    m = re.search(r'key: "%s",\s*name: "[^"]*",\s*q: "[^"]*",\s*leaves: \[(.*?)\n    \],' % re.escape(branch), src, re.S)
    if not m:
        return []
    # make 는 "…" 또는 `…${FAB…}` (템플릿) — 둘 다 받는다. 🔴 따옴표만 받았더니 «채널 (전면 발광)»이 조용히 빠졌다
    return [(lm.group(1), lm.group(4) or lm.group(2) or lm.group(3))
            for lm in re.finditer(r'\{ key: "[^"]+", name: "([^"]+)", make: (?:"([^"]*)"|`([^`]*)`)(?:, good: "([^"]*)")?', m.group(1))]


def concepts():
    """design-tree.ts → [(경로 키, 설명)] — 뿌리는 빼고 «어떤 로고로 할까?/그림 하나로» 처럼. `> 잎) combo:` 줄은 펼친다"""
    src = io.open(TREE_TS, encoding='utf-8').read()
    body = src[src.index('`') + 1:src.rindex('`')]
    stack, out = [], {}
    for raw in body.split('\n'):
        lm = re.match(r'^ *> 잎\) combo:(\w+)', raw)
        if lm and len(stack) > 1:
            for name, desc in combo_leaves(lm.group(1)):
                out.setdefault('/'.join(stack[1:] + [name]), desc)
            continue
        m = re.match(r'^( *)- (.+)$', raw)
        if not m:
            continue
        depth = len(m.group(1)) // 2
        parts = [p.strip() for p in m.group(2).split('::')]
        stack = stack[:depth] + [parts[0]]
        if depth == 0:
            continue
        out.setdefault('/'.join(stack[1:]), parts[1] if len(parts) > 1 else '')
    return list(out.items())


def safe(key):
    return os.path.join(ROOT, *[re.sub(r'[<>:"|?*]', '_', p) for p in key.split('/')])


def read(key):
    p = os.path.join(safe(key), 'REFS.md')
    if not os.path.exists(p):
        return {'prompt': '', 'refs': []}
    t = io.open(p, encoding='utf-8').read()
    m = re.search(r'^프롬프트:[ \t]*(.*)$', t, re.M)
    refs = []
    for line in re.findall(r'^- (.+)$', t, re.M):
        f = [x.strip() for x in line.split('::')]
        refs.append({'file': os.path.join(safe(key), f[0]), 'src': f[1] if len(f) > 1 else '', 'own': f[2] if len(f) > 2 else '', 'why': f[3] if len(f) > 3 else ''})
    return {'prompt': (m.group(1).strip() if m else ''), 'refs': refs}


def scaffold():
    """나무의 개념마다 폴더와 빈 REFS.md — 있는 건 절대 안 건드린다"""
    made = 0
    for key, desc in concepts():
        d = safe(key)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, 'REFS.md')
        if not os.path.exists(p):
            io.open(p, 'w', encoding='utf-8').write(f'# {key}\n\n{desc}\n\n프롬프트: \n\n## 레퍼런스\n\n')
            made += 1
    stale = []
    # 🔴 폴더 이름은 safe() 를 지난 것(«?»→«_»)이라 개념 키가 아니라 «폴더 경로»끼리 비교한다 — 키끼리 비교했더니 «어떤 로고로 할까?» 폴더가 전부 «나무에 없는 폴더»로 잡혔다(2026-09-28)
    keys = {os.path.relpath(safe(k), ROOT).replace(os.sep, '/') for k, _ in concepts()}
    for dp, _, fs in os.walk(ROOT):
        if 'REFS.md' in fs:
            k = os.path.relpath(dp, ROOT).replace(os.sep, '/')
            if k not in keys and not k.startswith(KEEP):
                stale.append(k)
    return made, stale


def listing():
    rows = []
    for key, _ in concepts():
        r = read(key)
        files = [x for x in os.listdir(safe(key)) if x.lower().endswith(IMG)] if os.path.isdir(safe(key)) else []
        rows.append((key, len(r['refs']), len(files), bool(r['prompt'])))
    return rows


def prompt(key):
    """조상부터 이 개념까지 프롬프트 조각을 이어 붙이고, 이 개념의 참고 파일을 낸다"""
    parts = key.split('/')
    frags = []
    for i in range(1, len(parts) + 1):
        f = read('/'.join(parts[:i]))['prompt']
        if f:
            frags.append(f)
    return ', '.join(frags), read(key)['refs']


def add(key, image, src, own, why):
    if key not in {k for k, _ in concepts()}:
        raise SystemExit(f'나무에 없는 개념: {key} — content/design-tree.ts 에 먼저 적어라')
    d = safe(key)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'REFS.md')
    if not os.path.exists(p):
        scaffold()
    name = os.path.basename(image)
    dst = os.path.join(d, name)
    # 🔴 이름이 겹치면 번호를 붙인다 — 위키미디어 긴 제목을 자르다 두 장이 같은 이름이 되어 한 장이 덮였다(2026-09-28)
    stem, ext = os.path.splitext(name)
    k = 2
    while os.path.exists(dst) and os.path.abspath(image) != os.path.abspath(dst):
        name = f'{stem}_{k}{ext}'
        dst = os.path.join(d, name)
        k += 1
    if os.path.abspath(image) != os.path.abspath(dst):
        shutil.copy2(image, dst)
    with io.open(p, 'a', encoding='utf-8') as fp:
        fp.write(f'- {name} :: {src} :: {own} :: {why}\n')
    return dst
