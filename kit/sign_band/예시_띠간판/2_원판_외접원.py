"""고객B 도장격자 → 원판 로고 (고객H 실물처럼 밝은 원판 안에 그림이 다 들어감)."""
import re, os, fitz, numpy as np
from PIL import Image

BASE = os.path.join(os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent')), 'users', os.environ.get('DEGAJA_USER', 'user'), 'domains', 'susanna', '시안', '2026-10_부대찌개')
OUT = os.path.join(BASE, 'circle')
os.makedirs(OUT, exist_ok=True)
s = open(os.path.join(BASE, r'final\Q3_도장격자\고객B_도장격자.svg'), encoding='utf-8').read()
G = dict(re.findall(r'<g id="([^"]+)">(.*?)</g>', s, re.S))
CONTENT = ['cauldron', 'letters', 'roof', 'line']


def mask(ids, scale=0.25):
    body = ''.join(G[i] for i in ids)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="4800" height="4800" viewBox="0 0 4800 4800">'
           '<rect width="4800" height="4800" fill="#fff"/>' + re.sub(r'fill="#[0-9A-Fa-f]+"', 'fill="#000"', body) + '</svg>')
    p = fitz.open(stream=svg.encode(), filetype='svg')[0].get_pixmap(matrix=fitz.Matrix(scale, scale))
    a = np.frombuffer(p.samples, np.uint8).reshape(p.height, p.width, p.n)[..., 0]
    ys, xs = np.nonzero(a < 128)
    return np.c_[xs, ys] / scale


def mec(P):
    c = P.mean(0)
    for k in range(4000):
        d = np.hypot(*(P - c).T); i = d.argmax(); c = c + (P[i] - c) / (k + 20)
    return c, np.hypot(*(P - c).T).max()


P = mask(CONTENT)
c, r = mec(P[::5])
print('content circle', c.round(1), round(r, 1))
np.save(os.path.join(OUT, '_mec.npy'), np.r_[c, r])
