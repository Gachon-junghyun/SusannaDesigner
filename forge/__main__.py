# -*- coding: utf-8 -*-
"""python -m forge <명령> — 수산나 디자이너 공방. 자세한 쓰임은 protocols/forge.md.

  run <건> [--only a,b] [--from a] [--force] [--send] [--dry] [--confirm a]   바뀐 단계만 돌린다
  status <건>                     단계마다 최신·바뀜·확인 기다림
  adopt <건> [단계…]              지금 출력을 현재 입력의 결과로 인정(처음 붙일 때)
  init <폴더>                     pipeline.json 뼈대
  gate <건> <단계>                그 단계 검사만 다시
  zoom <출력.png> <그림…>          확대판
  diff <켬.png> <끔.png> <출력.png> 옵션 켬·끔 차이판
  trial <일> <방법> win|loss|tie [--vs 다른방법] [--job] [--metric] [--how] [--human] [--desc]
  method [일] [--queue]           방법 대장(공식·시도·버림)
  clock start <건> <value|part|format|fix> <메모> [--at "YYYY-MM-DD HH:MM"] · clock stop <건> [--accepted yes|no] [--at]
  report                          종류별 시간 곡선 + 오래 걸리는 단계
"""
import argparse
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from . import _pipe, _gates, _methods, _clock


def main():
    ap = argparse.ArgumentParser(prog='forge')
    sp = ap.add_subparsers(dest='cmd', required=True)
    r = sp.add_parser('run'); r.add_argument('job'); r.add_argument('--only'); r.add_argument('--from', dest='start'); r.add_argument('--force', action='store_true')
    r.add_argument('--send', action='store_true'); r.add_argument('--dry', action='store_true'); r.add_argument('--confirm')
    s = sp.add_parser('status'); s.add_argument('job')
    a = sp.add_parser('adopt'); a.add_argument('job'); a.add_argument('stages', nargs='*')
    i = sp.add_parser('init'); i.add_argument('path')
    g = sp.add_parser('gate'); g.add_argument('job'); g.add_argument('stage')
    z = sp.add_parser('zoom'); z.add_argument('out'); z.add_argument('images', nargs='+')
    d = sp.add_parser('diff'); d.add_argument('a'); d.add_argument('b'); d.add_argument('out'); d.add_argument('--thresh', type=int, default=24)
    t = sp.add_parser('trial'); t.add_argument('task'); t.add_argument('method'); t.add_argument('result', choices=['win', 'loss', 'tie'])
    t.add_argument('--vs'); t.add_argument('--job', default=''); t.add_argument('--metric', default=''); t.add_argument('--how', default='')
    t.add_argument('--human', action='store_true'); t.add_argument('--desc', default=''); t.add_argument('--seed', action='store_true')
    m = sp.add_parser('method'); m.add_argument('task', nargs='?'); m.add_argument('--queue', action='store_true')
    c = sp.add_parser('clock'); c.add_argument('act', choices=['start', 'stop']); c.add_argument('job'); c.add_argument('kind', nargs='?'); c.add_argument('note', nargs='?', default='')
    c.add_argument('--accepted', choices=['yes', 'no']); c.add_argument('--at')
    sp.add_parser('report')
    A = ap.parse_args()
    if A.cmd == 'run':
        ok = _pipe.run(_pipe.job_dir(A.job), only=A.only.split(',') if A.only else None, start=A.start, force=A.force, send=A.send, dry=A.dry,
                       confirm=A.confirm.split(',') if A.confirm else None)
        sys.exit(0 if ok else 1)
    if A.cmd == 'status': _pipe.status(_pipe.job_dir(A.job))
    elif A.cmd == 'adopt': _pipe.adopt(_pipe.job_dir(A.job), A.stages or None)
    elif A.cmd == 'init': _pipe.init(A.path)
    elif A.cmd == 'gate':
        job = _pipe.job_dir(A.job); P = _pipe.load(job)
        st = [x for x in P['stages'] if x['name'] == A.stage]
        if not st: raise SystemExit('없는 단계')
        sys.exit(0 if _gates.run_all(P, st[0])['ok'] else 1)
    elif A.cmd == 'zoom': print(_gates.zoom_sheet(A.images, A.out))
    elif A.cmd == 'diff': print(_gates.diff_sheet(A.a, A.b, A.out, A.thresh))
    elif A.cmd == 'trial': _methods.trial(A.task, A.method, A.result, A.vs, A.job, A.metric, A.how, A.human, A.desc, A.seed)
    elif A.cmd == 'method': _methods.show(A.task, A.queue)
    elif A.cmd == 'clock':
        job = _pipe.job_dir(A.job)
        if A.act == 'start': _clock.start(job, A.kind, A.note, A.at)
        else: _clock.stop(job, None if A.accepted is None else A.accepted == 'yes', A.at)
    elif A.cmd == 'report': _clock.report()


if __name__ == '__main__':
    main()
