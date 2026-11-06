# PROMPTS — 분위기 → 제미나이 프롬프트 사전 (실제로 준 말과 나온 그림으로 적었다)

> **뭐냐:** «고급스럽게»·«부드럽고 우아하게»·«귀엽게» 같은 분위기 말을 **제미나이에 넣을 문장 조각**으로 옮기는 사전. 전부 고객A 네일(2026-09-27)에서 **실제로 보낸 프롬프트 43장과 나온 그림, 사람 반응**을 다시 보고 적었다.
> **언제 읽나:** `/gemini-image` 프롬프트를 쓰기 «전». 분위기 말을 받으면 여기서 조각을 고르고, 아래 «쓰기 전 체크»를 지킨다.
> **안 담는 것:** 제미나이 조작 함정(탭·첨부·전송) → `DeGaJa_Agent/.claude/skills/gemini-image/SKILL.md` · 손잡이 수칙 → `../design-atlas/tree/로고.md` · 뽑은 뒤 잔손질 → `ad/`(README).
> 증거: 한 장 도감 `runs/2026-09-27_고객A네일/_atlas_symbol.png`·`_atlas_lettering.png` · 원문 프롬프트는 각 폴더의 `jobs*.json`.

---

## 0. 쓰기 전 체크 (전부 실측으로 먹힌 것)

1. **분위기 말 하나를 «눈에 보이는 수치·모양»으로 바꾼다** — «부드럽게»가 아니라 `LIGHT weight · thin even strokes (about 2% of the image height) · WIDE and LOW · VERY generous letter-spacing · NO swashes`. 형용사만 주면 제미나이의 «기본 고급»(스와시 달린 길쭉한 로만)이 나온다.
2. **«안 낼 것»을 같이 적는다** — `NOT a cartoon, NOT a kawaii emoji` 한 줄이 «귀엽게 → 이모지»를 막았다. `NO swashes, NO flourishes` 가 «꾸밈 없는 명조»를 만들었다.
3. **글자는 철자를 풀어 적는다** — `exactly "고객A네일" (five syllables: 고 객 A 네 일, no space)`. 한글 16장·영문 20장 전부 철자 맞음. ⚠️ **«no space» 는 한 번 어겼다**(10_plain brush2) — 띄어쓰기는 뽑은 뒤 눈으로.
4. **평면·여백을 못박는다** — `Flat vector …, solid black on a pure white background, NO gradient, NO texture, NO shadow, NOT a mockup, NOT a photograph` + `fills about the central 50–60%, clear wide white margin, nothing touches the edge`. 43장 중 테두리에 닿은 것 0.
5. **굵기는 % 로** — `thick stems about 4.5% of the image height, thin parts never hairline (at least 1.3%)`. 말로만 «살짝 굵게»보다 잘 먹혔다(8_kr).
6. **`--per-chat 1`** — 서로 독립인 안은 대화를 가른다(앞 그림이 섞임 — gemini-image 함정 ⑫).
7. **`--ref` 는 «유지»에만 쓴다** (아래 §3).
8. **간판이면 만들 수 있는 말부터** (아래 §4) — 예쁘게 뽑고 나서 굵히면 손맛이 죽는다.

## 1. 분위기 → 문장 조각 (글자)

| 분위기(사람 말) | 넣은 조각 | 나온 것 | 사람 반응 · 폴더 |
|---|---|---|---|
| **부드럽고 우아하게 · 미니멀** («PEONIA 느낌») | `soft, elegant, airy modern display sans-serif — LIGHT weight with thin even strokes (about 2% …), letters WIDE and LOW (not tall, not condensed), VERY generous letter-spacing … NO swashes, NO flourishes` + 부제 `much smaller, extremely wide letter-spacing, thin geometric sans` | 가늘고 낮은 산세리프, 둥근 U, 넓은 자간 — 4/4 | 🟢 원하던 방향. 다만 까치발 봉이 안 들어감(§4) · `14_en_soft` |
| 고급 · 럭셔리 디스플레이 (형용사만) | `refined modern luxury display lettering … long sweeping curves or subtle ligatures` | 스와시 달린 **길쭉한 로만** | «3번 좋은데 너무 길쭉» · `5_lettering` |
| 넓게 · 덜 길쭉하게 | `WIDE, OPEN proportions — each capital about as wide as it is tall … NOT condensed` | 조금 넓어짐, 여전히 약간 김 | 스와시는 호평 · `7_v3`. ⚠️ 비율은 뽑은 뒤 `ad squash` 가 확실하다 |
| 한글 · 고급 명조 + 스와시 | `Custom Korean logotype … designed to match an elegant high-contrast roman with calligraphic swashes (thick vertical stems, thin hairline-like joins, flared serif ends)` + 스와시 자리 지정(ㅈ 첫 획 말림 · ㄹ 끝 스와시 · 지에서 흐르는 스와시) | 명조 + 스와시 4/4, 철자 4/4 | «한국어 계속» · `8_kr` |
| **꾸밈 없이 · 정직한 비율** | `PLAIN and HONEST: absolutely NO swashes, NO curls, NO flourishes, NO extended strokes … every stroke ends normally within its own syllable. Honest standard proportions: each syllable fits a square, even spacing` | 깨끗한 명조 3/3 | 🟢 D안 · `10_plain` |
| **그림 낙서 같은 굵은 글자**(DRAWSIGN 2026-09-28) | 공통: `The word must read exactly "DRAWSIGN" (eight capital letters in this exact order: D R A W S I G N) … one single line` + 결 넷: ① `bold hand-drawn doodle logotype — fat, heavy, squarish block capitals drawn by hand with a thick marker and filled in solid, each letter a slightly different height and slightly tilted, edges a little wobbly` ② `doodle bubble lettering … puffy, rounded, inflated capitals filled solid black` ③ `bold comic-book doodle lettering — heavy hand-drawn capitals with a slight dynamic slant … brush pen` ④ `very fat round felt-tip marker … bold monoline capitals with rounded stroke ends, bouncy baseline` | 철자 8/8 · ①은 «poster·hand-painted» 로 쓰면 이미지가 안 나왔다(앞에 `Generate an image.`) · ④는 «WIDE» 를 넣어도 길쭉 | `runs/2026-09-28_드로우사인로고` |
| 모던·심플하게(자간) | — 다시 뽑지 않음 | `ad respace --scale 0.86 --track 0.22` | 🟢 글자 모양 그대로 · `12_tracking` |

## 2. 분위기 → 문장 조각 (심벌)

| 분위기 | 넣은 조각 | 나온 것 | 반응 · 폴더 |
|---|---|---|---|
| 사진의 분위기(졸린 고양이) + «장미 같은 줄 일러스트» | `The attached photo is the SUBJECT … hand-drawn LINE ILLUSTRATION … loose sketchy pen drawing … contour lines drawn two or three times slightly offset … open unfinished line ends, varying line weight` | 분위기 최고, **선 0.8mm·잡티 130~190** | 분위기◎ 간판✕ · `4_symbol/cat/out` |
| 굵게만 | `The attached drawing is FINAL — redraw EXACTLY … change ONLY the line weight` | 그림 그대로 굵기만 바뀜 | 🟢 `--ref` 로 «굵기만»은 된다 · `cat/bold` |
| 귀엽게 · 획 줄이기 | `CUTE, ARTISTIC LOGO MARK with FEWER strokes: about 7 strokes … round soft head … short muzzle` | **이모지 같은 고양이** | 🔴 «안 이뻐» · `cat/cute` |
| **예쁘게 · 고양이답게** | `a pretty, elegant cat … real-looking graceful cat with natural cat proportions (not a cartoon, not a kawaii emoji) … drawn with the SAME pen as a luxury high-contrast serif logotype` | 우아한 앉은 고양이(선) | 🟢 글씨와 짝이 맞음 · `7_v3/brush3` |
| 잠든 · 웅크린 | `lying down curled and dozing, head resting on the front paws, the fluffy tail wrapping around the body in one elegant swash` | **면(실루엣) 고양이** — 선으로 달라 했는데 면이 나옴 | 🟢 «까치발로 할 거라 이게 좋다» · `7_v3/retro1` |
| 모노그램 · 고급 | `monogram of J and N interlocked, thin high-contrast didone … enclosed in a thin elegant vertical oval ring` | JN 오벌 | 한국 레퍼런스 결과 맞음 · `4_symbol/refine2` |
| 스케치 다듬기 | `The attached black sketch is the SHAPE to keep …` | 스케치의 **투박함까지** 유지 | 🔴 «너무 별로» · `4_symbol/refine` |

## 3. `--ref` 규칙 (가장 비싸게 배운 것)

| 참고를 붙이고 시킨 것 | 결과 |
|---|---|
| «이 글씨체로 새 낱말을» (10_plain brush1) | 🟢 글씨체 유지 |
| «그림 그대로, 선 굵기만» (cat/bold) | 🟢 굵기만 바뀜 |
| «그대로, **비율만** 넓게» (5_lettering/v2) | 🔴 **거의 똑같이 돌려줌** — 참고를 빼고 말로 다시 해야 바뀜 |
| «이 스케치 모양을 지켜서 예쁘게» (4_symbol/refine) | 🔴 투박함까지 지킴 |

→ **유지·굵기는 `--ref`, 비율·구도·«예쁘게»는 참고를 빼고 말로.** 남의 로고를 `--ref` 로 넣지 않는다(상표 — 레퍼런스는 «말»로 옮긴다).

## 4. 만들 수 있게 (까치발·채널)

- **까치발 철문자** — `every stroke BOLD with a harmonious, consistent weight (thinnest part at least 2.5% of the image width, no hairlines, no tapered needle tips, rounded stroke ends)` + `strokes should TOUCH or CONNECT … as few separate pieces as possible (ideally 1 to 3), no tiny floating dots` → 7획·10획 고양이가 **한 조각**. 면(실루엣)이면 더 좋다(최소 두께 39mm).
- 🔴 **가는 우아한 글자(§1 첫 줄)는 레이저로는 잘리지만 10mm 봉이 안 들어간다** — 봉 규격(스터드)을 먼저 정하거나, 글자 높이를 키우거나, `ad clean --thicken` 으로 조금만.
- **채널** — 그라데이션·수채·3D 광택 금지(면 하나 한 색). 톤이 필요하면 `ad gradient --bands 3`(조각이 는다는 것까지 알려 줌).
- 부제(작은 영문)는 거의 늘 봉이 안 들어간다 → 처음부터 «부제만 시트»를 대안으로.

## 5. 레퍼런스 찾기 (프롬프트 전에)

- 🔴 **한국 가게면 구글 이미지를 한국어로** — «네일샵 로고 감성»·«네일샵 간판 까치발». 비핸스(해외 브랜딩) 10곳만 보고 뽑은 안은 «너무 별로»였다. 한국 결 = 가는 겹친 모노그램 · 그레이지·금 · 넓은 자간 · 까치발은 가는 세리프 후광.
- 사람이 보내 준 레퍼런스(PEONIA 캡처·고양이 사진·장미 선화)는 **무엇을 가리키는지 한 줄로** 되묻지 말고 해석해 둘 다 보여 준다 — «장미를 넣으란 게 아니라 줄 느낌» · «고양이를 빼라는 게 아니라 고양이는 위에».
- 색은 처음부터 레퍼런스 퍼스널 컬러 세 벌로 입혀 보인다(흰 바탕·검정만 내면 따로 요구함).

## 6. 뽑은 뒤 (클로드가 눈으로 놓치던 것 → 자동)

```
python -m ad vec <png…> --out <폴더>                # 두 줄 부제 안 잃음 · 흰 배경 뺌
python -m ad check <svg> --w-mm <실제 가로> --raster <원본 png> [--letters N]
```
+ 🔴 **다운로드가 검은 사각형으로 올 때가 있다**(cat/cute retro1) — 잉크 비율이 1.0 이면 다시 뽑는다.
+ 🔴 **철자는 사람 눈으로 한 자씩**(자동 판정기는 없다 — font-ai PITFALLS B-1).

---

## 7. 원본 재현 (손님 로고 사진 → 깨끗한 평면 로고, 2026-09-28 아담 왕관)

**재설계가 아니라 옮기기다.** 짧게, 금지는 «바뀌는 건 이것뿐»으로 적는다. 대화 셋에 한 장씩 뽑아 고른다(`--per-chat 1`).

```
The attached photo is an embroidered crown logo. Recreate this logo AS FAITHFULLY AS POSSIBLE to the original — same shapes,
same proportions, same colors, same positions. Do not redesign, do not simplify, do not add anything.
Copy exactly: <부품을 색과 함께 하나씩 — 회색 몸통(윤곽선 없음) · 두 갈래 뾰족한 끝과 빨간 구슬 · 가운데 U 자 · 금색 별과 위 십자 · 밑단 세 줄(빨강 위, 노랑 가운데 양옆으로 조금 더, 초록 아래)>.
The ONLY changes: remove the Korean letters completely (no text anywhere), render it as a clean flat logo without embroidery
thread texture, and put it on a pure white background. No shadow, no gradient, no watermark, not a mockup. Centered with a clear white margin.
```

| 준 것 | 결과 | 사람 반응 |
|---|---|---|
| 사진 + 부품 설명 + «글자만 빼» (1차) | 모양은 맞는데 **밑단이 네 줄**(검정 추가)·노랑 돌출 사라짐 | «무지개쪽이 다르다» |
| 파이썬으로 잰 그림 + 사진 나란히 | 잰 그림을 **복사만** 함(가장자리만 다듬음) | 🔴 «완전 별로» |
| 사진만 + 위 프롬프트, 대화 셋 | 3/3 비율 맞음. 밑단이 가늘게 떨어짐 | «해상도 문제 같다» |
| **`ad upscale` 한 사진** + 위 프롬프트, 대화 셋 | 3/3 — 밑단이 원본처럼 붙은 두툼한 띠 | 🟢 첫 번째로 시안 |

- 🔴 **작은 원본(200px 미만)은 먼저 `ad upscale`** — 사진 모델(`realesrgan-x4plus`). 그림 모델은 자수 별을 찌그러뜨렸다.
- 사람이 «채워», «윤곽선 빼» 같은 **한 가지 손질**만 말하면 다시 뽑지 말고 그림에서 바로 고친다(모양이 안 흔들린다).
- 뽑은 뒤 일러 시안은 `ad vecc` → `ad look`(크게) → `ad export --phone`. README «손님 원본 로고» 단락.

## 8. 그라데이션 샘플 (2026-09-28 — 제미나이 13 · ChatGPT 12, 25/25 쓸 만함)

- 🔴 **«gradient» 한 낱말로 두지 말고 «무엇이 바뀌나»를 말한다** — 색(`smooth gradient from deep navy at the top to light sky blue at the bottom, same hue, only lightness changes`) · 회색(`achromatic … no hue at all`) · 그림자(`sun from the upper left casting soft shadows that fade and blur`) · 빛 번짐(`the gradient is ONLY in the light on the wall`) · 재료(`rust streaks running down the wall below each letter`).
- **«어디에»를 박는다** — `the gradient is ONLY on the moon symbol` · `sides (returns) are plain solid dark grey` 가 그대로 지켜졌다.
- **비교 한 장**(보색 탁해짐 · 핫스팟 · 드롭 섀도)은 `two panels side by side … Left: … Right: …` 로. 드롭 섀도는 옅게 나온다 — 캡션으로 어느 쪽인지 말해 준다.
- 조각은 창고에 있다: `python -m ad refs prompt "색은?/그라데이션을 쓸까?/무엇이 흐르나?/빛 번짐"`.

## 변경 이력
- 2026-09-28 (이어서) — §8 그라데이션 샘플(무엇이 바뀌나를 말하기 · 어디에 · 비교 한 장).
- 2026-09-28 — §7 «원본 재현» 추가(아담 왕관: 사진→평면 로고, 네 번의 시도와 사람 반응).
- 2026-09-27 — 최초 작성. 사람 요청 *"제미나이에게 준 프롬프트와 이미지를 보고 … 분위기 적으면 사전 프롬프트 작성하기 전에 참고하게"*. 43장·11묶음을 도감 두 장으로 다시 보고 적었다.
