# -*- coding: utf-8 -*-
"""파이프라인: 한 건의 단계(형상 → 치수도 → 전송 → 렌더 → 일러 → 시안 → 넘기기)를 jobs/<건>/pipeline.json 하나로 묶는다.

- 단계마다 «입력 지문»(명령 + 입력 파일 바이트)을 잰다. 지문이 같고 출력이 있으면 건너뛴다(캐시).
  값 하나를 바꾸면 그 값을 읽는 단계와, 그 단계 출력을 입력으로 받는 뒷단계만 다시 돈다.
  → 차수마다 스크립트를 복사(v3·v4·v5·v6)하고 손으로 따라 돌리던 것을 없앤다(10-22 60/70 사고가 이 틈에서 났다).
- confirm: 사람 확인이 필요한 단계(확대 그림 등). 그 지문으로 확인받기 전엔 뒤로 안 간다.
- outward: 바깥으로 나가는 단계(폰 전송·드라이브). `--send` 를 줄 때만 돈다(D11).
- gates: 단계가 끝나면 검사. 막는 검사가 실패하면 멈춘다. 보는 검사(zoom·diff)는 «볼 것» 그림을 만든다.
- graded: 바깥 단계 바로 앞에 두는 검수 확인 단계(명령 없음). 채점 보고서가 없으면 «입력이 없다»로, 낡았거나 «고칠 것 있음»이면 검사 실패로 멈춘다.
- 걸린 시간은 .forge/runlog.jsonl 에 남는다(forge report 가 읽는다).
"""
import glob
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # SusannaDesigner
LOCK = os.path.join(ROOT, 'kit', 'logo_vector', 'lock.py')


def job_dir(arg):
    for p in (arg, os.path.join(ROOT, 'jobs', arg)):
        if os.path.isfile(os.path.join(p, 'pipeline.json')):
            return os.path.abspath(p)
    raise SystemExit(f'pipeline.json 이 없다: {arg} (forge init 으로 만든다)')


def load(job):
    P = json.load(open(os.path.join(job, 'pipeline.json'), encoding='utf-8'))
    P['_work'] = os.path.join(job, P.get('workdir', '.'))
    return P


def _state_path(job):
    d = os.path.join(job, '.forge'); os.makedirs(d, exist_ok=True)
    return os.path.join(d, 'state.json')


def read_state(job):
    p = _state_path(job)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def write_state(job, st):
    json.dump(st, open(_state_path(job), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def log_run(job, row):
    row = dict(ts=time.strftime('%Y-%m-%d %H:%M:%S'), job=os.path.basename(job), **row)
    clock = os.path.join(job, '.forge', 'clock.json')
    if os.path.exists(clock):
        row['change'] = json.load(open(clock, encoding='utf-8')).get('id')
    with open(os.path.join(job, '.forge', 'runlog.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')


def expand(work, pats):
    out = []
    for p in pats:
        hits = sorted(glob.glob(os.path.join(work, p)))
        out += hits if hits else [os.path.join(work, p)]
    return out


def _file_sig(f):
    """파일 지문. .py 는 주석·설명문을 뺀 코드 구조(AST)로 잰다 — 주석 한 줄 고쳤다고 6분짜리 렌더가 다시 돌면 안 된다(10-22)."""
    b = open(f, 'rb').read()
    if f.endswith('.py'):
        import ast
        try:
            tree = ast.parse(b.decode('utf-8'))
            for node in ast.walk(tree):
                body = getattr(node, 'body', None)
                if isinstance(body, list) and body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], 'value', None), ast.Constant) and isinstance(body[0].value.value, str):
                    node.body = body[1:] or [ast.Pass()]
            return hashlib.sha1(ast.dump(tree, include_attributes=False).encode()).digest()
        except Exception:
            pass
    return hashlib.sha1(b).digest()


def key_of(P, s):
    h = hashlib.sha1(json.dumps([s.get('cmd'), s.get('lock')], ensure_ascii=False).encode())
    missing = []
    for f in expand(P['_work'], s.get('inputs', [])):
        if not os.path.exists(f):
            missing.append(os.path.relpath(f, P['_work'])); continue
        h.update(os.path.relpath(f, P['_work']).replace(os.sep, '/').encode())
        h.update(_file_sig(f))
    return h.hexdigest()[:16], missing


def outputs_ok(P, s):
    for p in s.get('outputs', []):
        if not glob.glob(os.path.join(P['_work'], p)):
            return False
    return True


def run_cmd(P, s):
    cmd = list(s['cmd'])
    if cmd and cmd[0] == 'python':
        cmd[0] = sys.executable
    if s.get('lock'):
        cmd = [sys.executable, LOCK, s['lock'], '--'] + cmd
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONPATH=os.pathsep.join([ROOT, os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent')), os.environ.get('PYTHONPATH', '')]))
    r = subprocess.run(cmd, cwd=P['_work'], env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    tail = (r.stdout or '').strip().splitlines()[-6:] + (r.stderr or '').strip().splitlines()[-6:]
    return r.returncode, tail


def run(job, only=None, start=None, force=False, send=False, dry=False, confirm=None):
    from . import _gates
    P = load(job); st = read_state(job)
    stages = P['stages']; names = [s['name'] for s in stages]
    if confirm:
        for c in confirm:
            if c not in names: raise SystemExit(f'없는 단계: {c}')
            k, _ = key_of(P, stages[names.index(c)])
            st.setdefault(c, {})['confirmed'] = k
            print(f'[확인] {c} — 지문 {k} 로 확인받음', flush=True)
        write_state(job, st)
    started = start is None
    upstream_ran = False
    for s in stages:
        n = s['name']
        if not started:
            started = (n == start)
            if not started: continue
        if only and n not in only: continue
        k, miss = key_of(P, s)
        if miss:
            print(f'[멈춤] {n}: 입력이 없다 {miss}', flush=True); return False
        prev = st.get(n, {})
        fresh = prev.get('key') == k and prev.get('ok') and outputs_ok(P, s)
        if fresh and not (force and (not only or n in only)):
            print(f'[그대로] {n} (마지막 {prev.get("at", "")})', flush=True)
            if not dry: log_run(job, dict(stage=n, ran=False, sec=0, ok=True))
        else:
            if s.get('outward') and not send:
                print(f'[멈춤] {n}: 바깥으로 나가는 단계({s.get("do", "")}). 보내려면 --send', flush=True); write_state(job, st); return False
            if dry:
                print(f'[돌 차례] {n}: {s.get("do", "")}', flush=True); upstream_ran = True; continue
            t0 = time.time()
            if s.get('cmd'):
                rc, tail = run_cmd(P, s)
            else:
                rc, tail = 0, []
            sec = time.time() - t0
            ok = rc == 0 and outputs_ok(P, s)
            print(f'[{"돌림" if ok else "실패"}] {n} {sec:.0f}초' + ('' if ok else f' 종료코드 {rc}'), flush=True)
            for line in tail[-4:] if not ok else tail[-2:]:
                print('    ' + line, flush=True)
            st[n] = dict(key=k, ok=ok, sec=round(sec, 1), at=time.strftime('%m-%d %H:%M'), confirmed=prev.get('confirmed'))
            log_run(job, dict(stage=n, ran=True, sec=round(sec, 1), ok=ok))
            write_state(job, st)
            if not ok:
                return False
            upstream_ran = True
        if dry and upstream_ran:
            continue
        if s.get('gates') and (not fresh or force):
            res = _gates.run_all(P, s)
            if not res['ok']:
                st[n]['ok'] = False; write_state(job, st)
                print(f'[멈춤] {n}: 검사 실패 — 고치고 다시 forge run', flush=True); return False
        if s.get('confirm') and st.get(n, {}).get('confirmed') != k:
            print(f'[확인 기다림] {n}: {s["confirm"]}\n    확인받으면: python -m forge run {os.path.basename(job)} --confirm {n}', flush=True)
            write_state(job, st); return False
    write_state(job, st)
    if dry:
        print('[끝, 미리보기] 위 «돌 차례»가 첫 바퀴다. 그 단계 출력이 실제로 바뀌면 뒤 단계도 돈다(미리보기는 그것까지는 모른다)', flush=True)
    else:
        print('[끝] 모든 단계가 최신이다', flush=True)
    return True


def status(job):
    P = load(job); st = read_state(job)
    for s in P['stages']:
        n = s['name']; k, miss = key_of(P, s); prev = st.get(n, {})
        if miss: tag = '입력 없음'
        elif prev.get('key') == k and prev.get('ok') and outputs_ok(P, s):
            tag = '최신' + ('' if not s.get('confirm') or prev.get('confirmed') == k else ', 확인 기다림')
        elif prev.get('key'): tag = '바뀜, 다시 돌 차례'
        else: tag = '아직 안 돎'
        flags = ''.join([' [바깥]' if s.get('outward') else '', ' [확인]' if s.get('confirm') else '', f' [잠금 {s["lock"]}]' if s.get('lock') else ''])
        print(f'{n:<14} {tag:<16} {prev.get("sec", "")!s:>6}초  {s.get("do", "")}{flags}')


def adopt(job, names=None):
    """지금 있는 출력을 현재 입력 지문의 결과로 인정한다(파이프라인을 처음 붙일 때, 이미 손으로 만든 결과가 있을 때)."""
    P = load(job); st = read_state(job)
    for s in P['stages']:
        n = s['name']
        if names and n not in names: continue
        k, miss = key_of(P, s)
        if miss or not outputs_ok(P, s):
            print(f'{n}: 못 받아들임(입력 없음 {miss} 또는 출력 없음)'); continue
        st[n] = dict(key=k, ok=True, sec=st.get(n, {}).get('sec', 0), at='adopt', confirmed=k if s.get('confirm') else None)
        print(f'{n}: 지금 출력을 지문 {k} 로 받아들임')
    write_state(job, st)


TEMPLATE = {
    "workdir": "work",
    "spec": ["spec.py"],
    "note": "값은 spec 한 곳에만 둔다. 차수가 바뀌어도 스크립트를 복사하지 않는다 — spec 값을 고치고 forge run 한다.",
    "stages": [
        {"name": "geom", "do": "형상(판·부재 윤곽)", "cmd": ["python", "geom.py"], "inputs": ["spec.py", "geom.py"], "outputs": ["parts.json"]},
        {"name": "preview", "do": "모양 바꾼 자리 확대 그림", "cmd": ["python", "preview.py"], "inputs": ["parts.json", "preview.py"],
         "outputs": ["preview.png"], "confirm": "확대 그림을 폰으로 보내 확인받았나"},
        {"name": "dims", "do": "치수도와 치수 글", "cmd": ["python", "dims.py"], "inputs": ["spec.py", "parts.json", "dims.py"], "outputs": ["dims/*.png", "dims/치수.txt"],
         "gates": [{"type": "text", "files": ["dims/치수.txt"]}]},
        {"name": "send_dims", "do": "치수 먼저 폰으로", "cmd": ["python", "send_dims.py"], "inputs": ["dims/*.png", "dims/치수.txt"], "outputs": [], "outward": True},
        {"name": "render", "do": "3D 렌더", "cmd": ["python", "render.py"], "inputs": ["parts.json", "spec.py", "render.py", "scene.py"], "outputs": ["render/*.png"],
         "gates": [{"type": "files", "glob": "render/*.png", "count": 6, "size": [2400, 1600]}, {"type": "zoom", "images": ["render/*.png"], "out": "_zoom_render.png"}]},
        {"name": "ai", "do": "1:1 일러 CS6", "cmd": ["python", "build_ai.py"], "lock": "illu", "inputs": ["spec.py", "parts.json", "build_ai.py"], "outputs": ["ai/*_CS6.ai"]},
        {"name": "a4", "do": "A4 시안", "cmd": ["python", "spec_a4.py"], "inputs": ["render/*.png", "ai/*_CS6.ai", "spec_a4.py"], "outputs": ["a4/*.pdf"],
         "gates": [{"type": "text", "files": ["a4/*_A4.pdf"], "forbid": [{"re": "작업자", "why": "손님 문서에 우리 쪽 사람 이름 금지(출처 포함)"}]}, {"type": "pdf_overlap", "files": ["a4/*_A4.pdf"]}]},
        {"name": "graded", "do": "독립 채점(·원본 대조) 확인 — protocols/grade.md", "inputs": ["a4/*.pdf", "render/*.png", "../grade/채점_*.md"], "outputs": [],
         "gates": [{"type": "graded", "after": ["a4/*.pdf", "ai/*_CS6.ai", "render/*.png"], "need_source": False}]},
        {"name": "deliver", "do": "드라이브와 폰", "cmd": ["python", "deliver.py"], "inputs": ["a4/*.pdf", "ai/*_CS6.ai", "render/*.png"], "outputs": [], "outward": True}
    ]
}


def init(path):
    os.makedirs(path, exist_ok=True)
    p = os.path.join(path, 'pipeline.json')
    if os.path.exists(p):
        raise SystemExit(f'이미 있다: {p}')
    json.dump(TEMPLATE, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{p} — 단계 이름·명령·입출력을 이 건에 맞게 고친다')
