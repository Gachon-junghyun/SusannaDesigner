# -*- coding: utf-8 -*-
"""변경 시계: 새 요구 하나(값 바꿈·새 부재·새 양식·결함 고침)가 받는 순간부터 넘길 때까지 몇 분 걸렸나.
사람은 같은 종류를 반복하면 로그처럼 줄어든다. 우리도 줄어드는지 «종류별 곡선»으로 본다(forge report).

- start: 요구를 받은 순간. 종류 넷 — value(값만), part(새 부재), format(새 양식·문서), fix(결함 고침)
- stop : 넘긴 순간. 그 사이 파이프라인이 돈 단계 수·초가 같이 묶인다.
"""
import json
import os
import statistics
import time
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, 'forge', 'data', 'changes.jsonl')
KINDS = {'value': '값만 바뀜', 'part': '새 부재', 'format': '새 양식', 'fix': '결함 고침'}


def _p(job):
    d = os.path.join(job, '.forge'); os.makedirs(d, exist_ok=True)
    return os.path.join(d, 'clock.json')


def start(job, kind, note, at=None):
    if kind not in KINDS: raise SystemExit(f'종류는 {list(KINDS)}')
    if os.path.exists(_p(job)): raise SystemExit('이미 열린 변경이 있다(forge clock stop 먼저)')
    t = time.time() if at is None else time.mktime(time.strptime(at, '%Y-%m-%d %H:%M'))
    c = dict(id=time.strftime('%m%d%H%M', time.localtime(t)), kind=kind, note=note, t0=t)
    json.dump(c, open(_p(job), 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'[시계] 시작 {KINDS[kind]}: {note}')


def stop(job, accepted=None, at=None):
    if not os.path.exists(_p(job)): raise SystemExit('열린 변경이 없다')
    c = json.load(open(_p(job), encoding='utf-8')); t1 = time.time() if at is None else time.mktime(time.strptime(at, '%Y-%m-%d %H:%M'))
    runs = []
    rl = os.path.join(job, '.forge', 'runlog.jsonl')
    if os.path.exists(rl):
        runs = [json.loads(l) for l in open(rl, encoding='utf-8') if c['id'] in l]
    row = dict(job=os.path.basename(job), id=c['id'], kind=c['kind'], note=c['note'], minutes=round((t1 - c['t0']) / 60, 1),
               stages_ran=sum(1 for r in runs if r.get('ran')), stage_sec=round(sum(r.get('sec', 0) for r in runs), 1),
               accepted=accepted, date=time.strftime('%Y-%m-%d', time.localtime(c['t0'])))
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, 'a', encoding='utf-8') as f:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')
    os.remove(_p(job))
    print(f'[시계] {KINDS[c["kind"]]} {row["minutes"]}분 (단계 {row["stages_ran"]}번, 기계 {row["stage_sec"]}초)')


def report():
    rows = [json.loads(l) for l in open(LEDGER, encoding='utf-8')] if os.path.exists(LEDGER) else []
    print('== 종류별 걸린 시간(분) — 줄어드는가 ==')
    for k, name in KINDS.items():
        r = [x for x in rows if x['kind'] == k]
        if not r: print(f'{name}: 기록 없음'); continue
        ms = [x['minutes'] for x in r]
        half = len(ms) // 2
        trend = f'앞 절반 중앙 {statistics.median(ms[:half]):.0f} → 뒤 절반 중앙 {statistics.median(ms[half:]):.0f}' if half else '기록 한 건'
        print(f'{name}: {len(r)}건, 차례로 {ms}  ({trend})')
        human = sum(1 for x in r if x.get('accepted') is False)
        if human: print(f'    그중 사람이 다시 하라고 한 것 {human}건')
    # 단계 시간: 어느 단계가 제일 오래 걸리나(빠르게 할 후보)
    tot = {}
    for rl in glob.glob(os.path.join(ROOT, 'jobs', '*', '.forge', 'runlog.jsonl')):
        for l in open(rl, encoding='utf-8'):
            r = json.loads(l)
            if r.get('ran'):
                a = tot.setdefault(r['stage'], [0, 0.0]); a[0] += 1; a[1] += r.get('sec', 0)
    if tot:
        print('== 단계별 기계 시간(돌린 횟수, 합 초) — 위가 빠르게 할 후보 ==')
        for n, (c, s) in sorted(tot.items(), key=lambda kv: -kv[1][1])[:8]:
            print(f'{n:<14} {c}번  {s:.0f}초  (한 번 {s / c:.0f}초)')
