# -*- coding: utf-8 -*-
"""방법 대장: 일(task)마다 방법들의 상태(공식·시도·버림)와 승패. «더 빠르고 정확한 것을 남기고 공식으로»의 기계 쪽.

원본은 시도 기록(data/trials.jsonl) 하나다. 상태와 승패는 매번 거기서 다시 센다(손으로 숫자를 고치지 않는다).
규칙(CHALLENGES.md 규칙과 같다)
- 같은 입력으로 기존 방법과 나란히 해 보고 결과를 trial 로 적는다(win·loss·tie, 잰 값 한 줄).
  --vs 는 «그 자리에서 실제로 맞붙은» 방법만 적는다. 사람이 거절했을 뿐이면 --vs 없이 --human.
- «서로 다른 두 건»에서 이기고 진 적이 없으면 공식. 같은 일의 이전 공식은 시도로 내려간다(밀려남).
  (한 건 안에서 여러 번 이긴 것은 한 번으로 센다 — 10-22 처음 짰을 때 한 건의 거절 셋이 «3승»으로 부풀었다)
- 2패면 버림. 사람이 결과물에서 직접 거절한 방법은 한 번에 버림(--human).
- trial 을 적으면 CHALLENGES.md 결과 표에도 한 줄이 자동으로 들어간다(사람이 읽는 표와 기계 대장이 갈라지지 않게).
  --seed 는 CHALLENGES 표에 이미 있는 지난 기록을 대장에만 옮길 때.
"""
import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'forge', 'data')
MJ = os.path.join(DATA, 'methods.json')     # 설명·쓰는 법(how)만 사람이 적은 값, 나머지는 rebuild 가 채운다
TJ = os.path.join(DATA, 'trials.jsonl')
CH = os.path.join(ROOT, 'CHALLENGES.md')


def _load_meta():
    return json.load(open(MJ, encoding='utf-8')) if os.path.exists(MJ) else {'tasks': {}}


def trials():
    return [json.loads(l) for l in open(TJ, encoding='utf-8')] if os.path.exists(TJ) else []


def rebuild():
    """시도 기록에서 승패·상태를 다시 센다. 바뀐 상태(공식 오름·버림)를 돌려준다."""
    M = _load_meta(); old = {(t, m): v.get('status') for t, T in M['tasks'].items() for m, v in T['methods'].items()}
    for T in M['tasks'].values():
        for v in T['methods'].values():
            v.update(status='시도', wins=0, losses=0, ties=0, win_jobs=[])
    for r in trials():
        T = M['tasks'].setdefault(r['task'], {'desc': '', 'methods': {}})
        for nm in [r['method']] + ([r['vs']] if r.get('vs') else []):
            T['methods'].setdefault(nm, {'status': '시도', 'wins': 0, 'losses': 0, 'ties': 0, 'win_jobs': [], 'how': ''})
        a = T['methods'][r['method']]; b = T['methods'].get(r.get('vs')) if r.get('vs') else None
        res = r['result']
        if res == 'win':
            a['wins'] += 1; a['win_jobs'] = sorted(set(a['win_jobs']) | {r['job']})
            if b: b['losses'] += 1
        elif res == 'loss':
            a['losses'] += 1
            if r.get('human'): a['status'] = '버림'
            if b: b['wins'] += 1; b['win_jobs'] = sorted(set(b['win_jobs']) | {r['job']})
        else:
            a['ties'] += 1
            if b: b['ties'] += 1
        for nm in [r['method']] + ([r['vs']] if r.get('vs') else []):
            v = T['methods'][nm]
            if v['status'] == '버림': continue
            if v['losses'] >= 2: v['status'] = '버림'
            elif len(v['win_jobs']) >= 2 and v['losses'] == 0 and v['status'] != '공식':
                for o, ov in T['methods'].items():
                    if o != nm and ov['status'] == '공식': ov['status'] = '시도'
                v['status'] = '공식'
    os.makedirs(DATA, exist_ok=True)
    json.dump(M, open(MJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    notes = []
    for t, T in M['tasks'].items():
        for m, v in T['methods'].items():
            if old.get((t, m)) != v['status'] and v['status'] in ('공식', '버림'):
                notes.append(f'{t}: {m} → {v["status"]}' + (' — 해당 프로토콜 «해라» 칸에 한 줄 올리고 줄 끝에 {승격: …}' if v['status'] == '공식' else ''))
    return M, notes


def trial(task, method, result, vs=None, job='', metric='', how='', human=False, desc='', seed=False):
    M = _load_meta(); T = M['tasks'].setdefault(task, {'desc': desc, 'methods': {}})
    if desc and not T.get('desc'): T['desc'] = desc
    T['methods'].setdefault(method, {'status': '시도', 'how': ''})
    if how: T['methods'][method]['how'] = how
    os.makedirs(DATA, exist_ok=True)
    json.dump(M, open(MJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    row = dict(date=time.strftime('%Y-%m-%d'), job=job, task=task, method=method, vs=vs, result=result, metric=metric, human=human)
    with open(TJ, 'a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')
    if not seed: _challenges_row(row)
    M, notes = rebuild()
    for n in notes: print('[대장]', n)
    T = M['tasks'][task]
    print(f'[대장] {task}: ' + ', '.join(f'{k} {v["status"]}({v["wins"]}승 {v["losses"]}패 {v["ties"]}무, 이긴 건 {len(v["win_jobs"])})' for k, v in T['methods'].items()))


def _challenges_row(r):
    if not os.path.exists(CH): return
    s = open(CH, encoding='utf-8').read()
    head = '| 날짜 | 건 | 시도 | 기본 길 대비 | 근거 |\n|---|---|---|---|---|\n'
    if head not in s: return
    word = {'win': '나음', 'loss': '못함', 'tie': '같음'}[r['result']]
    line = f"| {r['date']} | {r['job']} | {r['task']}: {r['method']}" + (f" (대 {r['vs']})" if r['vs'] else '') + f" | {word}{' (사람 판정)' if r['human'] else ''} | {r['metric']} |\n"
    open(CH, 'w', encoding='utf-8').write(s.replace(head, head + line, 1))


def show(task=None, queue=False):
    M, _ = rebuild()
    for t, T in sorted(M['tasks'].items()):
        if task and t != task: continue
        off = [k for k, v in T['methods'].items() if v['status'] == '공식']
        print(f'{t} — {T.get("desc", "")}')
        for k, v in T['methods'].items():
            if queue and v['status'] != '시도': continue
            print(f'    {v["status"]:<3} {k:<22} {v["wins"]}승 {v["losses"]}패 {v["ties"]}무 (이긴 건 {len(v["win_jobs"])})  {v.get("how", "")}')
        if not off and not queue: print('    (공식 없음 — 다음 건에서 시도 하나를 기본 길과 나란히)')
