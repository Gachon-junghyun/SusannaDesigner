# 모든 패스 마디에서 들어오는/나가는 접선 각도 차(°)를 잰다 — 0 이면 매끈(G1)
import sys, re, math
s = open(sys.argv[1], encoding='utf-8').read()
lim = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
def tang(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])
for gid, body in re.findall(r'<g id="(\w+)">(.*?)</g>', s, re.S):
    for d in re.findall(r' d="([^"]+)"', body):
        for sub in re.findall(r'M[^M]+', d):
            toks = re.findall(r'([MLCZ])([^MLCZ]*)', sub)
            segs = []; cur = None; start = None
            for c, v in toks:
                n = list(map(float, v.split()))
                if c == 'M': cur = start = (n[0], n[1])
                elif c == 'L': segs.append(('L', cur, (n[0], n[1]))); cur = (n[0], n[1])
                elif c == 'C': segs.append(('C', cur, (n[0], n[1]), (n[2], n[3]), (n[4], n[5]))); cur = (n[4], n[5])
            bad = []
            for i in range(len(segs)):
                a = segs[i]; b = segs[(i + 1) % len(segs)]
                tin = tang(a[3], a[4]) if a[0] == 'C' and math.dist(a[3], a[4]) > 1e-6 else tang(a[1], a[-1])
                tout = tang(b[1], b[2]) if b[0] == 'C' and math.dist(b[1], b[2]) > 1e-6 else tang(b[1], b[-1])
                ang = abs((math.degrees(tout - tin) + 180) % 360 - 180)
                if ang > lim: bad.append((round(a[-1][0], 1), round(a[-1][1], 1), round(ang, 1), a[0] + b[0]))
            print(gid, 'segs', len(segs), 'kinks>%.1f°:' % lim, len(bad), bad[:12])
