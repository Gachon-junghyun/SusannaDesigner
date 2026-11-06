"""PDF·.ai(PDF 호환) 한 쪽을 «일러 외곽선 보기»처럼 선만 그려 PNG 로 내고, 겹친 윤곽(합치면 줄어드는 면)을 센다.
사람이 외곽선 보기에서 잡은 결함(2026-10-24 고객L: Noto 가변 글꼴 A 가로획이 따로 겹친 사각형)을 넘기기 전에 먼저 잡으려고 만든 검사.
usage: python outline_view.py <파일.pdf|.ai> [쪽 번호 0부터] [--clip x0,y0,x1,y1] [--zoom 2] [--out 그림.png]
출력: 겹친 윤곽 수(0 이어야 통과)와 그 위치 · 선만 그린 그림"""
import sys, argparse
import fitz
import pathops


def faces(page, clip=None):
    """채운 면(path)마다 pathops Path 로 — 같은 그림 덩이(fill)의 하위 윤곽을 함께 담는다"""
    out = []
    for g in page.get_drawings():
        if not g.get('fill') or (clip and not g['rect'].intersects(clip)):
            continue
        pp = pathops.Path(); pen = pathops.PathPen(pp); open_ = False; last = None
        for it in g['items']:
            if it[0] == 'l':
                a, b = it[1], it[2]
                if not open_ or last != a:
                    if open_: pen.closePath()
                    pen.moveTo((a.x, a.y)); open_ = True
                pen.lineTo((b.x, b.y)); last = b
            elif it[0] == 'c':
                a, c1, c2, b = it[1:5]
                if not open_ or last != a:
                    if open_: pen.closePath()
                    pen.moveTo((a.x, a.y)); open_ = True
                pen.curveTo((c1.x, c1.y), (c2.x, c2.y), (b.x, b.y)); last = b
            elif it[0] == 're':
                if open_: pen.closePath(); open_ = False
                r = it[1]; pen.moveTo((r.x0, r.y0)); pen.lineTo((r.x1, r.y0)); pen.lineTo((r.x1, r.y1)); pen.lineTo((r.x0, r.y1)); pen.closePath()
        if open_: pen.closePath()
        out.append((g['rect'], pp))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('page', nargs='?', type=int, default=0)
    ap.add_argument('--clip'); ap.add_argument('--zoom', type=float, default=2.0); ap.add_argument('--out')
    a = ap.parse_args()
    d = fitz.open(a.src); p = d[a.page]
    clip = fitz.Rect(*map(float, a.clip.split(','))) if a.clip else p.rect
    bad = []
    for r, pp in faces(p, clip):
        cs = []
        for c in pp.contours:
            q = pathops.Path(); c.draw(q.getPen()) if hasattr(c, 'draw') else None
            cs.append(q if hasattr(c, 'draw') else pathops.Path(c))
        # 두 윤곽이 «조금만» 겹치면 결함: 한쪽이 다른 쪽 안에 통째로 있으면(속공간) 괜찮다
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                inter = pathops.op(cs[i], cs[j], pathops.PathOp.INTERSECTION, fix_winding=True)
                ai, aj, ax = abs(cs[i].area), abs(cs[j].area), abs(inter.area)
                if ax > 0.01 and ax < min(ai, aj) - 0.01:
                    bad.append((r, round(ax, 2))); break
    print(f'겹친 윤곽 {len(bad)}건' + (' (통과)' if not bad else ''))
    for r, ax in bad[:20]:
        print(f'  위치 {[round(v, 1) for v in r]}  겹친 넓이 {ax} pt²')
    if a.out:
        z = a.zoom; nd = fitz.open(); np_ = nd.new_page(width=clip.width * z, height=clip.height * z); sh = np_.new_shape()
        T = lambda q: fitz.Point((q.x - clip.x0) * z, (q.y - clip.y0) * z)
        for g in p.get_drawings():
            if not g['rect'].intersects(clip):
                continue
            for it in g['items']:
                if it[0] == 'l': sh.draw_line(T(it[1]), T(it[2]))
                elif it[0] == 'c': sh.draw_bezier(T(it[1]), T(it[2]), T(it[3]), T(it[4]))
                elif it[0] == 're': sh.draw_rect(fitz.Rect(T(it[1].tl), T(it[1].br)))
        sh.finish(color=(0, 0, 0), width=0.6, fill=None); sh.commit()
        np_.get_pixmap(dpi=72).save(a.out); print('그림', a.out)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
