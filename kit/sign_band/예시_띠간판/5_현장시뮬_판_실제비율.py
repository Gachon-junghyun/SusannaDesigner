"""현장 시뮬 준비 — (1) ChatGPT 에 줄 «현장 사진 + 간판 평면» 묶음 판과 jobs.json, (2) 실제 비율 그대로 붙인 합성.
고객B 2026-10-11 에 bash 안에서 돌린 것을 옮겼다. 경로·표시선 좌표(파란 6m = x729~1165)는 그 건 것이다 — 복사해서 고쳐라.
usage: python 5_현장시뮬_판_실제비율.py   (cwd = 그 건 폴더 `시안/2026-10_부대찌개`)
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

NAMES = ['1_원판_3색', '2_네모_3색', '3_원판_4색', '4_네모_4색']
SPAN_PX, SPAN_M, SIGN_M = 436, 6.0, 5.8          # 파란 표시 436px = 6m, 간판 5.8m
X0, CY = 736, 705                                # 붙일 왼쪽 끝 · 띠 가운데 y (1920x1440 사진 기준)

site = Image.open('ref/site_marked_full.png').convert('RGB')
font = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 34)

# (1) 묶음 판 + jobs — 사진은 위, 간판 평면은 아래. 프롬프트는 «위 사진만 내보내라»
jobs = []
for n in NAMES:
    s = Image.open(f'sim1011/flat_{n}_white.png'); s = s.resize((1800, round(s.height * 1800 / s.width)), Image.LANCZOS)
    b = Image.new('RGB', (1920, 1440 + 80 + s.height + 40), 'white'); b.paste(site, (0, 0))
    ImageDraw.Draw(b).text((60, 1460), 'SIGN ARTWORK (install exactly this, 5.8 m wide):', fill='black', font=font)
    b.paste(s, (60, 1520)); p = os.path.abspath(f'sim1011/board_{n}.png'); b.save(p)
    prompt = ("Create an image: a photorealistic photo of THIS exact building facade (the TOP part of the attached image) — same camera angle, "
              "same framing, same 4:3 crop, same daylight and shadows, all other existing shop signs unchanged. Install the sign shown in the "
              "BOTTOM part ('SIGN ARTWORK') exactly where the blue hand-drawn line marks it. Remove the blue line and the handwritten '6m'. "
              "Copy the artwork exactly — same layout, colors, Korean letters, lettering shapes; do not redesign it. Long thin band about "
              "5.8 m x 0.3 m (19:1). Spell every syllable; 찌 has the double consonant ㅉ. Output ONLY the facade photo. No watermark, no people.")
    jobs.append({'name': f'sim_{n}', 'prompt': prompt, 'ref': p})
json.dump(jobs, open('sim1011/jobs_sim.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# (2) 실제 비율 합성 — 파란 표시는 깨끗한 사진으로 메우고(fix_composite.py 와 같은 법) 평면을 그대로 붙인다
W, H = 1920, 1440
clean = Image.open('src/1010_0951_2_i_c77ea29b6d99.jpg').convert('RGB').resize((W, H), Image.LANCZOS)
m, c = np.asarray(site).astype(int), np.asarray(clean).astype(int)
blue = ndimage.binary_dilation(m[..., 2] - np.maximum(m[..., 0], m[..., 1]) > 60, iterations=4)
base = m.copy(); base[blue] = c[blue]; base = Image.fromarray(base.astype(np.uint8))
for n in NAMES:
    s = Image.open(f'sim1011/flat_{n}.png')                      # 투명 배경 평면, 폭 = 띠 폭
    w = round(SPAN_PX * SIGN_M / SPAN_M); h = round(s.height * w / s.width)
    s2 = s.resize((w, h), Image.LANCZOS); im = base.copy(); im.paste(s2, (X0, CY - h // 2), s2)
    im.save(f'sim1011/real_{n}.jpg', quality=93)
    im.crop((560, 560, 1500, 860)).resize((1880, 600), Image.LANCZOS).save(f'sim1011/real_{n}_zoom.jpg', quality=92)
print('판·jobs·실제 비율 합성 끝 →', 'python .claude/skills/chatgpt-image/gen.py --out sim1011/gpt --jobs sim1011/jobs_sim.json --per-chat 1')
