# -*- coding: utf-8 -*-
"""
디자인 고르기 창(피커) — Claude 가 디자인을 시작하면 **앱 창을 띄워** 사람이 디자인 나무에서 그림을 보며 고르고,
고른 것을 Claude 가 받아 제미나이·ChatGPT 프롬프트로 넘긴다. 뽑힌 그림을 같은 창에 다시 띄워 고르게 한다.

    python -m ad picker [--store 상호] [--brief "한 줄"]     # 혼자 시험 — 창을 띄우고 보낸 것을 JSON 으로 찍는다
    MCP: ad/picker_mcp.py (design_open · design_wait · design_show · design_tree)

- 나무 원본은 드로우사인 `content/design-tree.ts` 하나다(간판 잎은 `config/tree.ts`). 여기서 다시 적지 않고 «읽는다» —
  파서는 사이트 `lib/designTree.ts` 와 같은 규칙(`> 샘플)`·`> 예)`·`> 어울림)`·`> 잎) combo:`).
- 그림: 공개 샘플·예(사이트 public/) + 🔴 비공개 레퍼런스(`refs/`, 남의 것 포함). **이 창은 이 PC 안에서만 열린다** —
  레퍼런스를 밖으로 내보내는 길이 아니다. 프롬프트 조각은 `refs.prompt()` 가 이어 준다(새로 짓지 않음).
- 🔴 서버는 **127.0.0.1 에만** 붙고(밖에서 못 들어온다), 주소마다 무작위 토큰, Host·Origin 검사, 그림은 **번호표로만** 내준다
  (경로를 받지 않는다 — 경로 넘나들기 없음). 비슷한 오픈소스(mcp-feedback-enhanced ≤2.6)가 무인증 웹소켓으로 명령 실행을 당했다.
- 조사 근거: DeGaJa_Agent users/<작업자>/research/2026-10-10_claude-design-oss/REPORT.md
"""
import base64
import io
import json
import os
import re
import secrets
import subprocess
import threading
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import refs

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(os.path.expanduser('~'), 'HOMEPAGE_MAKER', 'sites', 'drawsign')
PUBLIC = os.path.join(SITE, 'public')
HTML = os.path.join(HERE, 'picker.html')
RUNS = os.path.join(os.path.dirname(HERE), 'runs')
GUIDES = os.path.join(os.path.dirname(HERE), 'guides')   # 레시피(갈래 가이드) — 창에서 읽고 고친다. Claude 도 같은 파일을 읽고 고친다
GEN = {
    'gemini': os.path.join(os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent')), '.claude', 'skills', 'gemini-image', 'gen.py'),
    'chatgpt': os.path.join(os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent')), '.claude', 'skills', 'chatgpt-image', 'gen.py'),
}
BROWSERS = [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
            r'C:\Program Files\Google\Chrome\Application\chrome.exe']
MAX_REFS = 40    # 한 개념에서 그림판에 띄우는 비공개 레퍼런스 수(카드에는 첫 장만)
CLAUDE = '[Claude] '   # Claude 가 올린 레퍼런스 — REFS.md 의 «왜» 칸 머리. 창에서 따로 표시한다
MAGIC = {b'\x89PNG': '.png', b'\xff\xd8\xff': '.jpg', b'RIFF': '.webp', b'GIF8': '.gif'}


# ── 나무 ─────────────────────────────────────────────────────────────

def _combo(branch):
    """config/tree.ts 한 칸 → [(이름, 만들기, 이럴 때 좋아요)] — refs.combo_leaves 와 같은 정규식, 칸 둘을 따로 낸다"""
    src = io.open(refs.COMBO_TS, encoding='utf-8').read()
    m = re.search(r'key: "%s",\s*name: "[^"]*",\s*q: "[^"]*",\s*leaves: \[(.*?)\n    \],' % re.escape(branch), src, re.S)
    if not m:
        return []
    return [(lm.group(1), lm.group(2) or lm.group(3) or '', lm.group(4) or '')
            for lm in re.finditer(r'\{ key: "[^"]+", name: "([^"]+)", make: (?:"([^"]*)"|`([^`]*)`)(?:, good: "([^"]*)")?', m.group(1))]


class Tree:
    """design-tree.ts → 노드 사전. 파일이 바뀌면 다시 읽는다(창을 연 채로 나무를 고쳐도 새로고침이면 보인다)"""

    def __init__(self, images):
        self.images = images
        self.mtime = None
        self.root = None
        self.by_key = {}
        self.ver = 0        # 다시 읽을 때마다 +1 — 열린 창이 이걸 보고 나무를 새로 받는다

    def get(self):
        mt = (os.path.getmtime(refs.TREE_TS), os.path.getmtime(refs.COMBO_TS))
        if mt != self.mtime:
            self.root = self._parse()
            self.mtime = mt
            self.ver += 1
        return self.root

    def _node(self, key, name, desc='', sign='', depth=0, combo=False):
        n = {'key': key, 'name': name, 'desc': desc, 'sign': sign, 'depth': depth, 'feels': [],
             'samples': [], 'examples': [], 'children': [], 'combo': combo, 'q': name.endswith('?')}
        return n

    def _parse(self):
        src = io.open(refs.TREE_TS, encoding='utf-8').read()
        body = src[src.index('`') + 1:src.rindex('`')]
        root = self._node('', '', depth=-1)
        stack = [root]
        for raw in body.split('\n'):
            if not raw.strip():
                continue
            indent = len(raw) - len(raw.lstrip(' '))
            line = raw.strip()
            top = stack[-1]
            if line.startswith('> 어울림)'):
                top['feels'] = [x.strip() for x in re.split(r'\s+·\s+', line[6:]) if x.strip()]
                continue
            if line.startswith('> 샘플)'):
                f = [x.strip() for x in line[5:].split('::')] + ['', '', '']
                top['samples'].append({'src': f[0], 'caption': f[1], 'prompt': f[2]})
                continue
            if line.startswith('> 예)'):
                f = [x.strip() for x in line[4:].split('::')] + ['', '', '']
                top['examples'].append({'src': f[0], 'caption': f[1], 'lesson': f[2]})
                continue
            if line.startswith('> 잎)'):
                m = re.search(r'combo:(\w+)', line)
                for name, make, good in (_combo(m.group(1)) if m else []):
                    key = '/'.join(x for x in [top['key'], name] if x)
                    top['children'].append(self._node(key, name, good or make, make, top['depth'] + 1, combo=True))
                continue
            if not line.startswith('- '):
                continue
            depth = indent // 2
            parts = [p.strip() for p in line[2:].split('::')]
            f = [p for p in parts if not p.startswith('→')]
            while len(stack) > 1 and stack[-1]['depth'] >= depth:
                stack.pop()
            parent = stack[-1]
            same = next((c for c in parent['children'] if c['combo'] and c['name'] == f[0]), None)
            if same:    # combo 에서 펼친 같은 이름 잎 → 합친다(사이트 규칙)
                if len(f) > 1 and f[1]:
                    same['desc'] = f[1]
                if len(f) > 2 and f[2]:
                    same['sign'] = f[2]
                stack.append(same)
                continue
            key = '' if parent['depth'] < 0 else '/'.join(x for x in [parent['key'], f[0]] if x)
            node = self._node(key, f[0], f[1] if len(f) > 1 else '', f[2] if len(f) > 2 else '', depth)
            parent['children'].append(node)
            stack.append(node)
        top = root['children'][0] if root['children'] else root
        self.by_key = {}
        self._finish(top)
        return top

    def _finish(self, n):
        """그림 번호표·비공개 레퍼런스·프롬프트 조각을 붙인다"""
        self.by_key[n['key']] = n
        imgs = []
        for s in n['samples']:
            p = os.path.join(PUBLIC, s['src'].lstrip('/').replace('/', os.sep))
            if os.path.isfile(p):
                imgs.append({'i': self.images.add(p), 'cap': s['caption'], 'kind': '샘플', 'path': p, 'prompt': s['prompt']})
        for e in n['examples']:
            p = os.path.join(PUBLIC, e['src'].lstrip('/').replace('/', os.sep))
            if os.path.isfile(p):
                imgs.append({'i': self.images.add(p), 'cap': e['caption'] or e['lesson'], 'kind': '본 것', 'path': p})
        frag = ''
        if n['key']:
            r = refs.read(n['key'])
            frag = r['prompt']
            why = {os.path.basename(x['file']): x for x in r['refs']}
            d = refs.safe(n['key'])
            if os.path.isdir(d):
                files = sorted(x for x in os.listdir(d) if x.lower().endswith(refs.IMG) and not x.lower().endswith('.svg'))
                # Claude 가 올린 것부터 — 방금 올린 걸 사람이 바로 보게
                files.sort(key=lambda x: not why.get(x, {}).get('why', '').startswith(CLAUDE))
                for x in files[:MAX_REFS]:
                    p = os.path.join(d, x)
                    w = why.get(x, {})
                    byc = w.get('why', '').startswith(CLAUDE)
                    cap = (w.get('why', '')[len(CLAUDE):] if byc else x) or x
                    imgs.append({'i': self.images.add(p), 'cap': cap, 'kind': 'Claude 가 올림' if byc else '레퍼런스', 'path': p,
                                 'own': w.get('own', '')})
        n['imgs'] = imgs
        n['frag'] = frag
        for c in n['children']:
            self._finish(c)

    def public(self, n=None):
        """창에 넘기는 모양 — 로컬 경로는 빼고 번호표만"""
        n = n or self.get()
        return {'key': n['key'], 'name': n['name'], 'desc': n['desc'], 'sign': n['sign'], 'q': n['q'],
                'feels': n['feels'], 'frag': n['frag'],
                'imgs': [{'i': x['i'], 'cap': x['cap'], 'kind': x['kind']} for x in n['imgs']],
                'children': [self.public(c) for c in n['children']]}

    def outline(self, n=None, depth=0, out=None):
        """글로 된 나무 한 장 — Claude 가 창 없이도 선택지를 알 수 있게"""
        n = n or self.get()
        out = [] if out is None else out
        if depth:
            mark = '' if not n['imgs'] else f'  [그림 {len(n["imgs"])}]'
            out.append('  ' * (depth - 1) + f'- {n["name"]} — {n["desc"][:60]}{mark}')
        for c in n['children']:
            self.outline(c, depth + 1, out)
        return out

    def detail(self, key):
        """고른 개념 하나 → Claude 가 프롬프트를 쓸 재료"""
        n = self.by_key.get(key)
        if not n:
            return {'key': key, 'missing': True}
        chain, _ = refs.prompt(key)
        return {'key': key, 'name': n['name'], 'question': key.rsplit('/', 1)[0] if '/' in key else '',
                'desc': n['desc'], 'sign': n['sign'], 'feels': n['feels'],
                'prompt_fragments': chain,
                'sample_prompts': [s['prompt'] for s in n['samples'] if s['prompt']],
                'sample_files': [x['path'] for x in n['imgs'] if x['kind'] == '샘플'],
                'ref_files': [{'file': x['path'], 'own': x.get('own', ''), 'by_claude': x['kind'] == 'Claude 가 올림'}
                              for x in n['imgs'] if x['kind'] in ('레퍼런스', 'Claude 가 올림')]}


class Images:
    """그림 번호표 — 창은 경로가 아니라 번호로만 그림을 달라고 한다"""

    def __init__(self):
        self.by_path, self.paths, self.lock = {}, [], threading.Lock()

    def add(self, path):
        path = os.path.abspath(path)
        with self.lock:
            if path not in self.by_path:
                self.by_path[path] = len(self.paths)
                self.paths.append(path)
            return self.by_path[path]

    def get(self, i):
        with self.lock:
            return self.paths[i] if 0 <= i < len(self.paths) else None


class Cols:
    """레퍼런스 모음 — 나무 칸에 안 묶인 그림 묶음(예: «수학 학원 로고» 조사). `refs/_모음/<이름>/items.json` 하나가 한 묶음이다.
    items.json = {title, made, by, why, own, items:[{file, name, region, note, tags, dark, site, src, shot, own}]}.
    🔴 전부 남의 것일 수 있다 — 창에 보이기만 하고, Claude 는 결만 말로 옮긴다(--ref 로 닮게 뽑지 않는다)"""

    def __init__(self, images):
        self.images = images
        self.root = os.path.join(refs.ROOT, '_모음')
        self.sig = None
        self.ver = 0
        self.cols = []

    def get(self):
        os.makedirs(self.root, exist_ok=True)
        js = sorted(os.path.join(self.root, d, 'items.json') for d in os.listdir(self.root)
                    if os.path.isfile(os.path.join(self.root, d, 'items.json')))
        sig = tuple((j, os.path.getmtime(j)) for j in js)
        if sig != self.sig:
            self.cols = [c for c in (self._read(j) for j in js) if c]
            self.sig = sig
            self.ver += 1
        return self.cols

    def _read(self, j):
        d = os.path.dirname(j)
        try:
            meta = json.load(io.open(j, encoding='utf-8'))
        except ValueError:
            return None
        if isinstance(meta, list):
            meta = {'items': meta}
        items = []
        for x in meta.get('items', []):
            f = os.path.join(d, x.get('file', ''))
            if not os.path.isfile(f):
                continue
            y = dict(x)
            y['path'] = f
            y['i'] = self.images.add(f)
            sh = os.path.join(d, 'shots', x.get('shot', '')) if x.get('shot') else ''
            y['shot_i'] = self.images.add(sh) if sh and os.path.isfile(sh) else None
            items.append(y)
        return {'id': os.path.basename(d), 'title': meta.get('title') or os.path.basename(d), 'made': meta.get('made', ''),
                'by': meta.get('by', ''), 'why': meta.get('why', ''), 'own': meta.get('own', ''), 'items': items}

    def public(self):
        keep = ('i', 'shot_i', 'name', 'region', 'note', 'tags', 'dark', 'site', 'own')
        return [{**{k: c[k] for k in ('id', 'title', 'made', 'by', 'why', 'own')},
                 'items': [{k: x.get(k) for k in keep} for x in c['items']]} for c in self.get()]

    def detail(self, cid, want, memos):
        c = next((c for c in self.get() if c['id'] == cid), None)
        if not c:
            return {'key': 'col:' + cid, 'missing': True}
        return {'key': 'col:' + cid, 'name': c['title'], 'collection': True, 'why': c['why'], 'own_rule': c['own'],
                'chosen_files': [{'file': x['path'], 'name': x.get('name', ''), 'note': x.get('note', ''), 'site': x.get('site', ''),
                                  'own': x.get('own', ''), 'memo': memos.get(str(x['i']), '')}
                                 for x in c['items'] if x['i'] in want],
                'all_files': len(c['items'])}

    def add(self, title, items, why='', by='Claude', own='남의 것'):
        """Claude 가 모음을 만들거나 덧붙인다. items = [{image(경로|주소), name, note, site, tags, dark, region}]"""
        d = os.path.join(self.root, _safe(title) or 'moum')
        os.makedirs(d, exist_ok=True)
        j = os.path.join(d, 'items.json')
        meta = json.load(io.open(j, encoding='utf-8')) if os.path.isfile(j) else {}
        meta.update({k: v for k, v in {'title': title, 'why': why, 'by': by, 'own': own}.items() if v and not meta.get(k)})
        meta.setdefault('made', time.strftime('%Y-%m-%d'))
        have = meta.setdefault('items', [])
        saved, failed = [], []
        for x in items:
            try:
                src = x.get('image', '')
                if re.match(r'https?://', src):
                    raw = urllib.request.urlopen(urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read()
                else:
                    raw = open(src, 'rb').read()
                ext = next((e for mg, e in MAGIC.items() if raw.startswith(mg)), '.svg' if b'<svg' in raw[:3000] else None)
                if not ext:
                    raise ValueError('그림이 아니다')
                name = f'{len(have) + 1:02d}_' + (_safe(x.get('name', '')) or 'ref') + ext
                with open(os.path.join(d, name), 'wb') as f:
                    f.write(raw)
                have.append({'file': name, 'name': x.get('name', ''), 'region': x.get('region', ''), 'note': x.get('note', ''),
                             'tags': x.get('tags', []), 'dark': bool(x.get('dark')), 'site': x.get('site', ''),
                             'src': src, 'own': x.get('own', own)})
                saved.append(name)
            except Exception as e:  # noqa: BLE001
                failed.append({'image': x.get('image'), 'error': f'{type(e).__name__}: {e}'})
        with io.open(j, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=1)
        self.get()
        return {'status': 'added', 'collection': os.path.basename(d), 'saved': saved, 'failed': failed,
                'hint': '열린 창 왼쪽 «레퍼런스 모음»에 몇 초 안에 뜬다.'}


class Recipes:
    """guides/*.md — 창에서 «레시피»로 보이고, 절(## ) 단위로 고칠 수 있다.
    🔴 고칠 때마다 옛 판을 guides/_history/ 에 남긴다(지우지 않는다). 이름은 폴더에 «이미 있는» .md 만 받는다 — 경로를 받지 않는다"""

    NAME = re.compile(r'^[\w가-힣 ._-]+\.md$')

    def list(self):
        out = []
        if not os.path.isdir(GUIDES):
            return out
        for f in sorted(os.listdir(GUIDES), key=lambda x: (x == 'README.md', x)):
            p = os.path.join(GUIDES, f)
            if not (f.endswith('.md') and os.path.isfile(p)):
                continue
            text = io.open(p, encoding='utf-8').read()
            m = re.search(r'^# (.+)$', text, re.M)
            out.append({'name': f, 'title': m.group(1).strip() if m else f, 'mtime': os.path.getmtime(p), 'text': text})
        return out

    def ver(self):
        if not os.path.isdir(GUIDES):
            return 0
        return max([os.path.getmtime(os.path.join(GUIDES, f)) for f in os.listdir(GUIDES) if f.endswith('.md')] or [0])

    def path(self, name):
        if not self.NAME.match(name or '') or not os.path.isfile(os.path.join(GUIDES, name)):
            raise ValueError('없는 레시피')
        return os.path.join(GUIDES, name)

    def save(self, name, text, base):
        p = self.path(name)
        if abs(os.path.getmtime(p) - float(base or 0)) > 0.001:
            return {'ok': False, 'conflict': True, 'error': '그새 누가(Claude 일 수 있다) 이 레시피를 고쳤습니다 — 새로 받은 판에서 다시 고치세요'}
        old = io.open(p, encoding='utf-8').read()
        if old == text:
            return {'ok': True, 'mtime': os.path.getmtime(p), 'same': True}
        h = os.path.join(GUIDES, '_history')
        os.makedirs(h, exist_ok=True)
        with io.open(os.path.join(h, f'{name[:-3]}_{time.strftime("%Y%m%d-%H%M%S")}.md'), 'w', encoding='utf-8', newline='') as f:
            f.write(old)
        with io.open(p, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
        return {'ok': True, 'mtime': os.path.getmtime(p)}

    def section(self, name, heading):
        """«## heading» 절 하나의 원문 — Claude 가 프롬프트를 쓸 때 읽는다"""
        try:
            text = io.open(self.path(name), encoding='utf-8').read()
        except ValueError:
            return ''
        out, on, fence = [], False, False
        for line in text.split('\n'):
            if line.startswith('```'):
                fence = not fence
            if not fence and line.startswith('## '):
                if on:
                    break
                on = line[3:].strip() == heading
            if on:
                out.append(line)
        return '\n'.join(out)


# ── 세션 ─────────────────────────────────────────────────────────────

class Session:
    def __init__(self, sid, brief='', store='', focus=None, preselect=None):
        self.sid, self.brief, self.store = sid, brief, store
        self.focus, self.preselect = focus or [], preselect or []
        self.events, self.read = [], 0       # 창이 보낸 것 · Claude 가 어디까지 읽었나
        self.rounds = []                      # Claude 가 띄운 그림 묶음
        self.boards = {}                      # 개념 키 → [{i, path, kind(올림|스케치)}] — 사람이 그림판에 올린 것
        self.board_dir = os.path.join(RUNS, f'{time.strftime("%Y-%m-%d")}_picker_{sid}', 'boards')
        self.cond = threading.Condition()
        self.created = time.time()
        # 주고받기 — 창에 «뭐가 왔다 갔나»를 한 줄씩 보인다. 🔴 그림판에 붙인 건 «보내기» 전까지 Claude 에게 안 간다 —
        # 사람이 붙이고 기다렸는데 아무것도 안 온 적이 있다(2026-10-10). 그래서 «안 보냄»도 줄로 남긴다
        self.log = []                         # [{at, who(나|Claude), what, imgs[번호], ev(보낸 것 번호)}]
        self.waiters, self.last_wait = 0, 0.0  # Claude 가 지금 design_wait 로 듣고 있나

    def note(self, who, what, imgs=None, ev=None):
        with self.cond:
            self.log.append({'at': time.strftime('%H:%M:%S'), 'who': who, 'what': what,
                             'imgs': list(imgs or []), 'ev': ev})

    def listening(self):
        """design_wait 안에 있거나, 막 끝나 다음 wait 를 부를 참(20초 안)이면 «듣는 중»"""
        return self.waiters > 0 or time.time() - self.last_wait < 20

    def public_log(self):
        out = []
        for x in self.log:
            y = dict(x)
            if x['ev'] is not None:
                e = self.events[x['ev']]
                y['got'] = e.get('got_at', '')   # Claude 가 받은 시각 — 비면 «아직 안 받음»
            out.append(y)
        return out


class Picker:
    def __init__(self):
        self.images = Images()
        self.tree = Tree(self.images)
        self.cols = Cols(self.images)
        self.recipes = Recipes()
        self.sessions = {}
        self.token = secrets.token_urlsafe(18)
        self.httpd = None
        self.port = None

    # 서버 ---------------------------------------------------------
    def start(self):
        if self.httpd:
            return
        picker = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):        # stdout 은 MCP 프로토콜 전용 — 아무것도 찍지 않는다
                pass

            def _ok_host(self):
                host = self.headers.get('Host', '')
                return host in (f'127.0.0.1:{picker.port}', f'localhost:{picker.port}')

            def _send(self, code, body, ctype='application/json; charset=utf-8', cache=False):
                if isinstance(body, (dict, list)):
                    body = json.dumps(body, ensure_ascii=False).encode('utf-8')
                elif isinstance(body, str):
                    body = body.encode('utf-8')
                self.send_response(code)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'max-age=3600' if cache else 'no-store')
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.end_headers()
                self.wfile.write(body)

            def _gate(self):
                u = urlparse(self.path)
                q = {k: v[0] for k, v in parse_qs(u.query).items()}
                if not self._ok_host() or not secrets.compare_digest(q.get('t', ''), picker.token):
                    self._send(403, {'error': 'forbidden'})
                    return None, None
                return u.path, q

            def do_GET(self):
                path, q = self._gate()
                if path is None:
                    return
                try:
                    if path == '/':
                        self._send(200, io.open(HTML, encoding='utf-8').read(), 'text/html; charset=utf-8')
                    elif path == '/api/tree':
                        picker.tree.get()
                        self._send(200, picker.tree.public())
                    elif path == '/api/recipes':
                        self._send(200, picker.recipes.list())
                    elif path == '/api/cols':
                        self._send(200, picker.cols.public())
                    elif path == '/api/session':
                        s = picker.sessions.get(q.get('s', ''))
                        if not s:
                            return self._send(404, {'error': 'no session'})
                        picker.cols.get()          # 모음 폴더가 바뀌었으면 ver 가 오른다 — 열린 창이 보고 다시 받는다
                        self._send(200, {'brief': s.brief, 'store': s.store, 'focus': s.focus,
                                         'preselect': s.preselect, 'rounds': s.rounds,
                                         'sent': len(s.events), 'read': s.read, 'tree_ver': picker.tree.ver,
                                         'log': s.public_log(), 'listening': s.listening(),
                                         'col_ver': picker.cols.ver, 'recipe_ver': picker.recipes.ver(),
                                         'boards': {k: [{'i': x['i'], 'kind': x['kind']} for x in v] for k, v in s.boards.items()}})
                    elif path == '/img':
                        p = picker.images.get(int(q.get('i', '-1')))
                        if not p or not os.path.isfile(p):
                            return self._send(404, {'error': 'no image'})
                        ext = os.path.splitext(p)[1].lower()
                        ctype = {'.png': 'image/png', '.webp': 'image/webp', '.gif': 'image/gif',
                                 '.svg': 'image/svg+xml'}.get(ext, 'image/jpeg')
                        self._send(200, open(p, 'rb').read(), ctype, cache=True)
                    else:
                        self._send(404, {'error': 'not found'})
                except Exception as e:  # noqa: BLE001 — 창 하나 때문에 서버가 죽으면 안 된다
                    self._send(500, {'error': f'{type(e).__name__}: {e}'})

            def do_POST(self):
                path, q = self._gate()
                if path is None:
                    return
                if self.headers.get('Origin') not in (f'http://127.0.0.1:{picker.port}', f'http://localhost:{picker.port}'):
                    return self._send(403, {'error': 'origin'})
                s = picker.sessions.get(q.get('s', ''))
                if path not in ('/api/submit', '/api/board', '/api/board_del', '/api/recipe_save') or not s:
                    return self._send(404, {'error': 'not found'})
                n = int(self.headers.get('Content-Length', '0'))
                if n > (30_000_000 if path == '/api/board' else 600_000 if path == '/api/recipe_save' else 200_000):
                    return self._send(413, {'error': 'too big'})
                try:
                    ev = json.loads(self.rfile.read(n).decode('utf-8'))
                except ValueError:
                    return self._send(400, {'error': 'bad json'})
                if path == '/api/board':
                    try:
                        return self._send(200, picker.board_add(s, ev.get('key', ''), ev.get('data', ''), ev.get('kind', '올림')))
                    except ValueError as e:
                        return self._send(400, {'error': str(e)})
                if path == '/api/recipe_save':
                    try:
                        r = picker.recipes.save(ev.get('name', ''), ev.get('text', ''), ev.get('base'))
                    except ValueError as e:
                        return self._send(400, {'error': str(e)})
                    if r.get('ok') and not r.get('same'):
                        s.note('나', f'레시피 «{ev.get("name")}» 의 «{ev.get("section") or "전체"}» 를 고쳤습니다 (옛 판은 guides/_history/)')
                    return self._send(409 if r.get('conflict') else 200, r)
                if path == '/api/board_del':
                    return self._send(200, picker.board_del(s, ev.get('key', ''), ev.get('i')))
                ev['at'] = time.strftime('%H:%M:%S')
                with s.cond:
                    s.events.append(ev)
                    n = len(s.events) - 1
                    s.cond.notify_all()
                s.note('나', _say(ev, picker.tree.by_key), ev=n)
                self._send(200, {'ok': True, 'n': len(s.events), 'listening': s.listening()})

        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def url(self, sid):
        return f'http://127.0.0.1:{self.port}/?t={self.token}&s={sid}'

    # 창 -----------------------------------------------------------
    def open_window(self, url):
        """앱 창(주소창 없는 창)으로 연다 — 엣지 → 크롬 → 기본 브라우저. 🔴 크롬 9222(디버그 프로필)는 건드리지 않는다"""
        for exe in BROWSERS:
            if os.path.isfile(exe):
                try:
                    subprocess.Popen([exe, f'--app={url}', '--window-size=1500,960', '--new-window'],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     creationflags=getattr(subprocess, 'DETACHED_PROCESS', 0))
                    return os.path.basename(exe)
                except OSError:
                    continue
        webbrowser.open(url)
        return 'default'

    # Claude 쪽 ----------------------------------------------------
    def open(self, brief='', store='', focus=None, preselect=None, window=True):
        self.start()
        self.tree.get()
        sid = secrets.token_hex(4)
        s = self.sessions[sid] = Session(sid, brief, store, focus, preselect)
        s.note('Claude', '창을 열었습니다' + (f' — {brief}' if brief else ''))
        url = self.url(sid)
        how = self.open_window(url) if window else 'none'
        return {'session': sid, 'url': url, 'window': how}

    def wait(self, sid, timeout=90):
        """창이 보낸 다음 것 하나 — 없으면 timeout 뒤 «waiting». 🔴 Claude Code 는 2분 넘는 도구를 백그라운드로 넘기므로 90초로 끊는다"""
        s = self.sessions.get(sid)
        if not s:
            return {'status': 'no-session', 'session': sid}
        with s.cond:
            s.waiters += 1
            try:
                s.cond.wait_for(lambda: len(s.events) > s.read, timeout=max(1, min(timeout, 110)))
            finally:
                s.waiters -= 1
                s.last_wait = time.time()
            if len(s.events) <= s.read:
                out = {'status': 'waiting', 'session': sid,
                       'hint': '사람이 아직 안 보냈다. design_wait 를 다시 불러 기다리거나, 다른 일을 하다 돌아와라.'}
                pend = {k: [x['path'] for x in v if x.get('after', 0) >= len(s.events)] for k, v in s.boards.items()}
                pend = {k: v for k, v in pend.items() if v}
                if pend:   # 판에는 붙였는데 안 보냈다 — 사람은 «보냈다»고 여길 수 있다. 물어볼 근거로 준다
                    out['board_unsent'] = pend
                    out['hint'] += ' 🔴 다만 그림판에 붙여 놓고 «보내기»를 안 누른 게 있다(board_unsent) — 사람에게 보냈는지 물어라.'
                return out
            ev = s.events[s.read]
            ev['got_at'] = time.strftime('%H:%M:%S')
            s.read += 1
        return self._enrich(s, ev)

    def _enrich(self, s, ev):
        kind = ev.get('kind')
        out = {'status': 'got', 'session': s.sid, 'kind': kind, 'at': ev.get('at')}
        if kind == 'picks':
            keys = [k for k in ev.get('picks', []) if isinstance(k, str)]
            notes = ev.get('notes') or {}
            chosen = ev.get('imgs') or {}
            memos = {str(k): str(v)[:300] for k, v in (ev.get('memos') or {}).items()}
            cols = [self.cols.detail(k[4:], {i for i in chosen.get(k, []) if isinstance(i, int)}, memos)
                    for k in keys if k.startswith('col:')]
            recipes = []
            for k in keys:
                if k.startswith('recipe:') and '#' in k:
                    name, head = k[7:].split('#', 1)
                    recipes.append({'key': k, 'recipe': name, 'section': head, 'file': os.path.join(GUIDES, name),
                                    'text': self.recipes.section(name, head)})
            details = [self.tree.detail(k) for k in keys if not k.startswith(('col:', 'recipe:')) and k != 'free']
            for d in details:
                # 오른쪽 창에서 사람이 콕 집은 그림 — 이 선택지 그림 중 «이거». 번호표는 그 개념의 그림일 때만 받는다
                node = self.tree.by_key.get(d['key']) or {'imgs': []}
                want = {i for i in chosen.get(d['key'], []) if isinstance(i, int)}
                d['chosen_files'] = [{'file': x['path'], 'kind': x['kind'], 'cap': x['cap'], 'own': x.get('own', ''),
                                      'memo': memos.get(str(x['i']), '')}
                                     for x in node['imgs'] if x['i'] in want]
            details += cols
            if 'free' in keys:
                details.append({'key': 'free', 'name': '자유 그림판', 'free': True})
            for d in details + recipes:   # 그림판은 어느 자리에든 붙는다 — 나무·모음·레시피·자유
                d['board_files'] = [{'file': x['path'], 'kind': x['kind']} for x in s.boards.get(d['key'], [])]
                d['board_note'] = notes.get(d['key'], '')
            store = (ev.get('store') or s.store or '').strip()
            engine = ev.get('engine') or 'gemini'
            outdir = os.path.join(RUNS, f'{time.strftime("%Y-%m-%d")}_{_safe(store) or "picker"}', 'picker')
            out.update({
                'store': store, 'note': ev.get('note', ''), 'feels': ev.get('feels', []),
                'engine': engine, 'count': int(ev.get('count') or 4),
                'picks': details,
                'recipes': recipes,
                'recipe_rule': 'recipes 는 사람이 «이 결로» 고른 레시피 절이다 — 프롬프트를 쓰기 전에 text 의 «해라»·«프롬프트 조각»을 따른다. '
                               '해 보고 새로 안 것은 그 절의 «겪은 것»에 날짜 박아 적는다(guides/README.md «한 건이 끝나면»).',
                'prompt_hint': ', '.join(d['prompt_fragments'] for d in details if d.get('prompt_fragments')),
                'out_dir': outdir,
                'board_rule': '그림판의 «스케치»는 사람이 그린 우리 것이라 --ref 로 넣어도 된다. «올림»은 출처를 모른다 — 남의 것일 수 있으니 결만 말로 옮겨라.',
                'chosen_rule': '«memo» 는 그 그림에 사람이 단 한 줄(어디가 좋은지)이다 — 프롬프트에 그대로 반영한다. chosen_files 는 사람이 «이 그림처럼»이라고 콕 집은 것이다 — 그 선택지의 다른 그림보다 먼저 본다(Read). '
                               '«샘플»은 우리 것이라 --ref 가능, «레퍼런스»·«본 것»은 남의 것일 수 있어 결만 말로 옮긴다.',
                'next': _next_steps(engine, outdir),
            })
        elif kind == 'review':
            r = next((x for x in s.rounds if x['round'] == ev.get('round')), None)
            chosen = [r['paths'][j] for j in ev.get('chosen', []) if r and 0 <= j < len(r['paths'])]
            out.update({'round': ev.get('round'), 'chosen_files': chosen, 'note': ev.get('note', ''),
                        'decision': ev.get('decision', ''),
                        'next': '«go»면 고른 그림으로 다음 단계(STAGES — 벡터화 `python -m ad vecc` 등). '
                                '«again»이면 note 를 반영해 다시 뽑고 design_show 로 띄운 뒤 design_wait.'})
        else:
            out['raw'] = ev
        return out

    # 그림판 --------------------------------------------------------
    def board_add(self, s, key, data, kind):
        """그림판은 어느 화면에서든 연다 (2026-10-11 사람: «어떤 창에서든지 그림판 열 수 있게»).
        key = 나무 개념 · 'col:<모음>' · 'recipe:<파일>#<절>' · 'free'(자유 그림판 — 어디에도 안 묶임)"""
        self.tree.get()
        tree = key in self.tree.by_key
        if not tree:
            ok = key == 'free' or (key.startswith('col:') and any(c['id'] == key[4:] for c in self.cols.get())) \
                or (key.startswith('recipe:') and '#' in key)
            if not ok:
                raise ValueError('그림판을 열 수 없는 자리')
        m = re.match(r'data:[\w/+.-]+;base64,(.*)$', data or '', re.S)
        raw = base64.b64decode(m.group(1)) if m else b''
        ext = next((e for mg, e in MAGIC.items() if raw.startswith(mg)), None)
        if not ext:
            raise ValueError('그림 파일이 아니다(png·jpg·webp·gif)')
        d = (os.path.join(s.board_dir, os.path.relpath(refs.safe(key), refs.ROOT)) if tree
             else os.path.join(s.board_dir, '_' + (_safe(key) or 'free')))
        os.makedirs(d, exist_ok=True)
        kind = '스케치' if kind == '스케치' else '올림'
        p = os.path.join(d, f'{time.strftime("%H%M%S")}_{len(os.listdir(d)):02d}_{"sketch" if kind == "스케치" else "upload"}{ext}')
        with open(p, 'wb') as f:
            f.write(raw)
        item = {'i': self.images.add(p), 'path': p, 'kind': kind, 'after': len(s.events)}   # after: 보낸 것 몇 개 뒤에 붙였나
        with s.cond:
            s.boards.setdefault(key, []).append(item)
        s.note('나', f'{_name(key)} 그림판에 {kind}을 붙였습니다 — 보내기 전까지 Claude 는 모릅니다', [item['i']])
        return {'ok': True, 'i': item['i'], 'kind': kind}

    def board_del(self, s, key, i):
        items = s.boards.get(key, [])
        keep = [x for x in items if x['i'] != i]
        with s.cond:
            s.boards[key] = keep
        if len(keep) < len(items):
            s.note('나', f'{_name(key)} 그림판에서 내렸습니다', [i])
        return {'ok': True, 'removed': len(items) - len(keep)}   # 파일은 안 지운다 — 창에서만 내린다

    def add_ref(self, key, images, src='', own='', why=''):
        """Claude 가 개념 하나에 레퍼런스를 올린다 → 비공개 창고(refs/)에 영구로 + 열린 창에 곧바로(나무 버전이 오른다).
        images 는 로컬 경로 또는 http(s) 주소. 🔴 «남의 것»이면 own 에 그렇게 적는다 — 창고는 비공개지만 --ref 로 닮게 뽑지 않는다"""
        self.tree.get()
        if key not in self.tree.by_key:
            near = [k for k in self.tree.by_key if key.split('/')[-1] in k][:5]
            return {'status': 'no-key', 'key': key, 'did_you_mean': near}
        dl = os.path.join(RUNS, '_dl')
        saved, failed = [], []
        for x in images:
            try:
                if re.match(r'https?://', x):
                    os.makedirs(dl, exist_ok=True)
                    req = urllib.request.Request(x, headers={'User-Agent': 'Mozilla/5.0 (research contact@example.com)'})
                    raw = urllib.request.urlopen(req, timeout=30).read()
                    ext = next((e for mg, e in MAGIC.items() if raw.startswith(mg)), None)
                    if not ext:
                        raise ValueError('그림이 아닌 응답')
                    name = re.sub(r'[^\w.-]+', '_', os.path.splitext(os.path.basename(urlparse(x).path))[0])[:50] or 'ref'
                    local = os.path.join(dl, name + ext)
                    with open(local, 'wb') as f:
                        f.write(raw)
                else:
                    local = x
                if not os.path.isfile(local):
                    raise ValueError('파일 없음')
                saved.append(refs.add(key, local, src or x, own or '모름', CLAUDE + (why or '')))
            except BaseException as e:   # noqa: BLE001 — refs.add 는 SystemExit 를 던진다. 서버가 죽으면 안 된다
                failed.append({'image': x, 'error': f'{type(e).__name__}: {e}'})
        self.tree.mtime = None           # 창고가 바뀌었다 → 다시 읽고 ver+1
        self.tree.get()
        if saved:
            ids = [self.images.add(p) for p in saved if isinstance(p, str) and os.path.isfile(p)]
            for s in self.sessions.values():
                s.note('Claude', f'{_name(key)} 에 레퍼런스 {len(saved)}장을 올렸습니다' + (f' — {why}' if why else ''), ids)
        return {'status': 'added', 'key': key, 'saved': saved, 'failed': failed, 'tree_ver': self.tree.ver,
                'hint': '열린 창은 몇 초 안에 그 개념 그림판에 «Claude 가 올림»으로 보인다.'}

    def show(self, sid, images, note=''):
        s = self.sessions.get(sid)
        if not s:
            return {'status': 'no-session'}
        paths = [os.path.abspath(p) for p in images if os.path.isfile(p)]
        missing = [p for p in images if not os.path.isfile(p)]
        r = {'round': len(s.rounds) + 1, 'note': note, 'imgs': [self.images.add(p) for p in paths],
             'names': [os.path.basename(p) for p in paths], 'paths': paths}
        with s.cond:
            s.rounds.append(r)
        s.note('Claude', f'그림 {len(paths)}장을 보냈습니다 ({r["round"]}번째)' + (f' — {note}' if note else ''), r['imgs'])
        return {'status': 'shown', 'round': r['round'], 'n': len(paths), 'missing': missing,
                'hint': '창에 떴다. design_wait 로 사람이 고른 것(kind=review)을 받아라.'}


def _name(key):
    if key == 'free':
        return '자유'
    if key.startswith('col:'):
        return '모음 ' + key[4:]
    if key.startswith('recipe:'):
        return '레시피 ' + key.split('#', 1)[-1]
    return key.rsplit('/', 1)[-1] or '나무'


def _say(ev, by_key):
    """보낸 것 한 줄 — 주고받기 칸에 사람 말로"""
    if ev.get('kind') == 'picks':
        names = [by_key[k]['name'] if k in by_key else _name(k)
                 for k in ev.get('picks', []) if isinstance(k, str)]
        s = f'고른 것 {len(names)}개를 보냈습니다: ' + ', '.join(names)
        ni = sum(len(v) for v in (ev.get('imgs') or {}).values() if isinstance(v, list))
        if ni:
            s += f' (콕 집은 그림 {ni}장)'
        if ev.get('note'):
            s += f' / 「{ev["note"]}」'
        return s
    if ev.get('kind') == 'review':
        s = ('이걸로 진행' if ev.get('decision') == 'go' else '다시 뽑아 달라') + f'고 보냈습니다 ({ev.get("round")}번째 그림, 고름 {len(ev.get("chosen", []))})'
        if ev.get('note'):
            s += f' / 「{ev["note"]}」'
        return s
    return '보냈습니다'


def _safe(name):
    return re.sub(r'[\\/:*?"<>|\s]+', '_', name).strip('_')[:40]


def _next_steps(engine, outdir):
    gens = ['gemini', 'chatgpt'] if engine == 'both' else [engine]
    lines = [f'1) picks 의 prompt_fragments·sample_prompts·desc 로 영어 프롬프트를 장마다 쓴다(SusannaDesigner/PROMPTS.md 규칙 — '
             f'글자가 들어가면 음절을 풀어 한 번 더, 금지 문장 포함). 남의 레퍼런스(ref_files)는 --ref 로 넣지 말고 결을 말로 옮긴다.',
             f'2) jobs.json([{{"name","prompt"}}…])을 {outdir} 에 쓴다.']
    for g in gens:
        lines.append(f'3) python "{GEN[g]}" --out "{outdir}\\{g}" --jobs "{outdir}\\jobs.json"   (크롬 9222 로그인 필요)')
    lines.append('4) 받은 PNG 를 Read 로 한 번 본 뒤 design_show(session, images=[…]) 로 창에 띄우고 design_wait.')
    return '\n'.join(lines)


PICKER = Picker()


def cli(store='', brief=''):
    """혼자 시험 — 창을 띄우고, 사람이 보낸 것을 하나 받아 JSON 으로 찍는다(Ctrl+C 로 끝)"""
    r = PICKER.open(brief=brief, store=store)
    print('창:', r['window'], r['url'], flush=True)
    while True:
        out = PICKER.wait(r['session'], 60)
        if out['status'] != 'waiting':
            print(json.dumps(out, ensure_ascii=False, indent=2), flush=True)
            if out.get('kind') == 'picks':
                break
