# 로고 결 레시피 — 뷰티는 어떻게, 선은 어떻게, 붓은 어떻게 (v0)

> **뭐냐:** 로고 «결»(뷰티·선·붓·고급·글자만·낙서·면·엠블럼·귀여움·입체)마다 **어떻게 뽑나**를 적은 레시피. 결마다 해라(단계) · 프롬프트 조각 · 통과 · 봐라 · 겪은 것 · 시도 대기열.
> 지난 건(고객A 네일 9/27 · 드로우사인 9/28 · 고객H 뷰티 10/3~4 · 고객I 10/6 · 고객B 부대찌개 10/10 · 붓구도 10/10)에서 **실제로 보낸 프롬프트와 사람 반응**만 옮겼다. 짐작은 «(추정)».
> **언제 읽나:** 고르기 창에서 결을 골랐을 때, 그리고 `/gemini-image`·`/chatgpt-image` 프롬프트를 쓰기 «전». 0단계 표 → `## 공통` → 고른 결 하나를 끝까지.
> 🔴 매 건마다 그 결의 «시도 대기열»에서 하나 이상 해 보고 결과를 «겪은 것»에 적는다([`README.md`](README.md) §작업할 때마다).
> **안 담는 것:** 상호 → 3안 → 간판 단계 순서 → [`../STAGES.md`](../STAGES.md) · 날짜별 팁 원본 → [`../TIPS.md`](../TIPS.md) · 분위기 → 문장 사전 원본 → [`../PROMPTS.md`](../PROMPTS.md) ·
> 고른 시안을 일러 벡터로 → [`logo_vector.md`](logo_vector.md) · 선만 보기 층 → [`../LESSONS_선정리.md`](../LESSONS_선정리.md) · 크롬 조작 함정 → DeGaJa `gemini-image`·`chatgpt-image` SKILL.md.

출처 줄임말: `TIPS 날짜` = `../TIPS.md` 그 날짜 줄 · `PROMPTS §n` · `STAGES n` · `벡터 §n` = `logo_vector.md` · `gemini`/`chatgpt` = DeGaJa `.claude/skills/<그것>-image/SKILL.md` · `sign-proof` = DeGaJa `.claude/skills/sign-proof/SKILL.md` · `메모리 <이름>` = DeGaJa 자동 메모리 · `runs/…`·`refs/…` = 이 폴더 기준.

---

## 0단계 — 어떤 결로 갈까

먼저 가른다: **손님이 시안(사진·AI 그림)을 줬으면 이 문서가 아니다** — 설계하지 말고 옮긴다(`/sign-proof` 원안 재현 · 메모리 sign-customer-draft-mode). 고른 시안을 벡터로 따는 건 `logo_vector.md`.

| 결 | 이럴 때 (업종 · 인상) | 근거 두께 |
|---|---|---|
| [뷰티 — 가늘고 우아하게](#뷰티--가늘고-우아하게) | 네일·왁싱·피부과·스파 · «부드럽고 우아하게», «미니멀» | 두 건(고객A 네일 · 고객H) + 레퍼런스 20 |
| [선 — 라인아트](#선--라인아트) | 얼굴 옆선·꽃·잎·동물 심벌 · 섬세함 | 두 건 |
| [붓 — 붓글씨·캘리](#붓--붓글씨캘리) | 한식·노포·«사람 냄새 나는 가게» | 세 건 + 진행 중 하나 |
| [고급 — 세리프·스와시·모노그램](#고급--세리프스와시모노그램) | 고급 네일·부티크 · «럭셔리» | 한 건(고객A 네일, 43장) |
| [글자만 — 워드마크](#글자만--워드마크) | 상호가 주인공 · 대부분의 가게 | 여러 건 |
| [굵은 손글씨 — 낙서·마커](#굵은-손글씨--낙서마커) | 친근한 서비스·브랜드 · «그림 낙서 같은 굵은 체» | 한 건(드로우사인) + 버튼 글씨 |
| [면 — 큰 면 몇 개·실루엣](#면--큰-면-몇-개실루엣) | 작게 쓰는 마크 · 까치발 · «디자인이지 일러스트가 아니다» | 두 건 |
| [엠블럼·배지·도장](#엠블럼배지도장) | 한식 프랜차이즈 · 공공·금융 «현판형» · 정사각 실루엣 | 두 건(얇음) |
| [귀여움·마스코트](#귀여움마스코트) | 카페·아이 업종 (추정) | 얇음 |
| [입체·광택 — 화면용 한 벌](#입체광택--화면용-한-벌) | 앱 아이콘·홈페이지 머리 · 간판 재단 아님 | 한 건(로고빛) |

결은 하나만 고르고, **3안은 그 결 안에서 한 손잡이(글꼴 / 색 / 락업)만** 바꾼다 — 둘 이상 바꾸면 비교가 안 된다(STAGES 5).

---

## 공통 — 모든 결에 먼저

### 굵기 — 숫자로 박지 말고 그때그때 알맞게 정한다 (사람 지시 2026-10-10)
> *«굵기는 다이나믹하게 너가 알아서 잘 딱 알맞게 정해야 한다고»* — 아래 «2%»·«13.4mm» 같은 숫자는 **그 건에서 맞았던 값**이지 정답이 아니다.

- **매 건 먼저 «어디에 얼마나 크게 쓰이나»를 정하고 거기서 굵기를 거꾸로 잡아라.** 간판이면 실제 가로 mm → `ad check --w-mm` 의 최소 획·봉 규격이 바닥이다. 화면이면 가장 작게 쓰일 크기(폰 아이콘 48px·명함 2cm)에서 가장 가는 획이 안 사라질 만큼이 바닥이다.
- **결이 위쪽을 정한다** — 뷰티·고급은 «가는 쪽 끝», 볼드·낙서·면은 «굵은 쪽 끝». 같은 결 안에서도 글자 수가 많거나 획이 빽빽한 글자(받침 많은 한글)는 한 단계 가늘게, 짧고 성긴 이름은 한 단계 굵게 잡아라 — 속공간이 막히지 않게.
- **굵기 «대비»도 같이 정해라** — 붓·세리프는 굵은 획 대비 가는 획 비율을, 단선은 «고르게»를. 가장 가는 곳이 굵은 획의 1/3 아래로 가면 간판에서 끊긴다(붓 6단계 고객I).
- **심벌과 글자는 같은 굵기 계열로 맞춰라**(면 2단계) — 따로 정하면 한 로고 안에서 따로 논다.
- **정한 값과 이유를 프롬프트와 기록에 한 줄로 남겨라** — `stroke weight about N% of the letter height (because: …)`. 받은 뒤 그 쓰임 크기로 줄여 보고(`ad check`·축소 미리보기) 너무 가늘거나 뭉치면 **그 장만** 굵기만 바꿔 다시 뽑아라(`--ref` + `change ONLY the line weight`, 선 5단계).
- 사람이 «더 굵게/가늘게»라고 하면 숫자를 묻지 말고 한 단계(대략 ×1.3 / ×0.75)씩 움직여 나란히 보여라 (추정 — 단계 폭은 아직 실측 없음).

### 해라 — 받기 전에
- 상호 · 현장 사진 · 원하는 샘플 사진 · **컨셉 한 줄**부터 받는다. 인상 1~2개와 «안 낼 인상» 하나를 적는다. — 왜: 간판 디자이너가 «이 셋이면 상담 절반», «가장 어려운 건 컨셉»(TIPS 2026-09-28 [1]) · STAGES 1.
- 모호한 말은 두 안을 나란히 보인다. 손님 그림과 짧은 말이 같이 오면 **그림이 답**이다. — 왜: «공사»가 상호였다(TIPS 2026-09-26) · 고객I 렌더 두 번 다시 돌림(메모리 client-image-wins-ambiguity).
- 레퍼런스는 **실제로 열어 크게** 본다. 한국 가게면 **구글 이미지를 한국어로**, 넘기는 예시는 **셋 이하**. — 왜: 비핸스만 보고 뽑은 안이 «너무 별로»(TIPS 2026-09-27) · 더 주면 베낀다(STAGES 3) · 썸네일만 보고 «참고했다»가 AI 티(메모리 design-no-ai-look).

### 해라 — 프롬프트
- 첫머리: ChatGPT 는 `Create an image:`, 제미나이가 글로 답하면 `Generate an image.` — 왜: «hand-painted poster lettering» 3/3 이미지 안 나옴 → 앞에 붙이고 poster 빼니 2/2(TIPS 2026-09-28 [2]) · chatgpt «되물을 때».
- **분위기 말을 수치·모양으로** 바꾸고 **안 낼 것을 같이** 적는다(`NO swashes`, `NOT a kawaii emoji`). — 왜: 형용사만 주면 제미나이 «기본 고급»(스와시 달린 길쭉한 로만)이 나온다(PROMPTS §0-1·2).
- 글자는 **음절을 풀어 한 번 더** 적는다. 쌍자음은 «NOT 지»처럼 틀릴 모양을 이름 불러 막는다. — 왜: 수산나디자인 9/9, 고객B 부대찌개 6/6(ㅉ 포함) · 고객A네일 16장 철자 맞음, 단 «no space»는 한 번 어김(gemini · PROMPTS §0-3). ⚠️ 쌍자음 표본은 한 단어 — ㅆ·ㄲ·ㄸ·ㅃ 로 넓히지 마라.
- 한 장에 로고 하나, 평면, 여백을 못박는다(아래 조각). 심벌이면 `NO text, NO letters` — 안 넣으면 한글이 깨져 박힌다(gemini). 테두리에 닿은 덩이는 벡터화가 버린다(TIPS 2026-09-23).
- 서로 독립인 안은 `--per-chat 1` — 같은 대화면 앞 그림이 섞인다(gemini ⑫).

```
Flat vector logo, solid black on a pure white background, NO gradient, NO texture, NO shadow, NOT a mockup, NOT a photograph,
fills about the central 50-60%, clear wide white margin, nothing touches the edge.
ONE single logo only — NOT a set, NOT several variations, NOT a sheet or grid.
The Korean text must read exactly "고객A네일" (five syllables: 고 객 A 네 일, no space), spelled correctly, nothing else written.
```
(첫 줄 = `refs/어떤 로고로 할까_/REFS.md`, 43장 중 테두리 닿음 0 · 둘째 줄 = `runs/2026-09-28_후보샘플` 에 보낸 틀 · 셋째 줄 = PROMPTS §0-3)

### 해라 — 투명 배경이 필요하면 마젠타
`completely flat solid magenta background, exact color #FF00FF, no shadows, no gradient.` → 받아서 `r>150 and b>150 and g<110 and (r+b)/2-g>80` 을 투명으로. 제미나이는 알파 PNG 를 안 준다. 실측 인물 시트 62% · 아이콘 시트 90% 깨끗(gemini). ⚠️ 로고 건에서 써 본 기록은 없다(흰 바탕이 기본).

### 해라 — 레퍼런스 첨부(`--ref`) 규칙
- **사람 «자기» 스케치는 첨부해도 된다** — `The attached image is my own rough hand sketch … keeping its composition exactly … Do not add, remove or change any characters`(`runs/2026-10-10_붓구도로고/jobs.json`). 🔴 단 혼자 첨부하면 **투박함까지** 지킨다(TIPS 2026-09-27 «너무 별로») → 판에 **«LAYOUT»이라 써 붙이니** 거친 선이 안 따라왔다(TIPS 2026-10-10).
- **남의 로고는 말로만 옮긴다 — 첨부하지 않는다.** 선 굵기·구도·색 수 같은 «손잡이»를 한 줄로(PROMPTS §3 · `refs/README.md`). 그림 없이 손잡이만 줘도 10/10 이 그 결을 따랐다(TIPS 2026-10-10, ChatGPT). ⚠️ 2026-10-10 고객B 건에서 **사람 결정으로** 남의 로고 판을 한 번 첨부했다 — 다시 하려면 사람 결정이 먼저다.
- **유지·굵기는 `--ref`, 비율·구도·«예쁘게»는 참고를 빼고 말로.** «그대로, 비율만 넓게»는 거의 똑같이 돌려줬다(PROMPTS §3 · TIPS 2026-09-27 [5]).

### 해라 — AI 티 빼기 (전부 사람이 되돌린 것)
- 선 끝이 전부 둥글고 굵기가 일정한 단선(monoline + round cap) = «AI 같다»·«캡슐 같다»(TIPS 2026-10-10). 문구는 [붓](#붓--붓글씨캘리) 조각.
- 모티프를 «그림 그대로»(타일 한 장씩 그린 기와) 그리지 말고 **생략 수준을 손님 원안에서 재서** 곡선 몇 줄로(TIPS 2026-10-10 «뻔하고 이상하다»).
- 처음부터 «면 몇 개»가 기본, 장식은 사람이 더해 달라 할 때(TIPS 2026-10-10 «잔선이 많다»).
- 색은 한 계열 안에서 명도·채도만, 보색 포인트를 임의로 넣지 않는다(메모리 design-no-ai-look). 흰 바탕·검정만 내지 말고 **퍼스널 컬러 세 벌**을 처음부터(TIPS 2026-09-27).
- «그라데이션»은 색만이 아니다 — 회색 광택·그림자·빛 번짐·재료. «무엇이 흐르나»·«어디에»를 말한다(TIPS 2026-09-28 · PROMPTS §8). 간판 채널이면 그라데이션·수채·3D 광택은 불가(STAGES 6).

### 해라 — 엔진 고르기
- 제미나이 «이미지 안 나옴»이 연달아 나면 ChatGPT 로 넘긴다(gemini ⑰, 10/1·10/10 같은 시각 ChatGPT 4/4·10/10).
- 둘을 동시에 돌리면 원본 다운로드가 상대 폴더로 샌다 — 끝나고 `Gemini_Generated_Image_*.png` 를 짝지어 되돌리거나 차례로 돌린다(gemini ⑲).
- 제미나이는 «원본 크기 다운로드» 2266px, 미리보기는 1024px(gemini ⑱). ChatGPT 가 «어느 이미지가 더…» 두 장을 띄우면 `_a`·`_b` 둘 다 받힌다 — 고르는 건 사람(chatgpt).
- 말로만 준 ChatGPT 11장은 한 결로 모였다(«빨강 바탕 흰 붓글씨») — 폭이 필요하면 제미나이 + 레퍼런스 판(TIPS 2026-10-10). 지시 따르기(선 끝 둥글게)는 ChatGPT 가 나았다(TIPS 2026-10-03).
- 대량 금지 — 한 번에 수십 장 돌리지 않는다(gemini · chatgpt).

### 통과 · 봐라 (모든 결)
- 받은 PNG 를 **`Read` 로 직접 본다** — 파일이 생겼다고 맞는 그림이 아니다(gemini ⑦). 검은 사각형(잉크 비율 1.0)이면 다시(PROMPTS §6).
- **철자를 음절마다 사람 눈으로** — 자동 판정기 없다(PROMPTS §6). 원안에 없던 띠·도장·글자를 «지어 넣었나»(벡터 §3).
- 벡터로 딴 건 **2000px 이상**으로 키워 본다 — 1024 로는 오돌토돌이 안 보인다(TIPS 2026-09-28 [5]).
- 공개할 그림이면 ✦ 를 `python -m ad unmark` 로 지우고 «AI 로 만든 그림»이라 적는다(gemini 절차 7).
- 손님에게 가는 시안집엔 **되는 안 하나와 고를 몇 줄만** — 판정 수치·안 되는 안·작업 사정은 내부용(메모리 client-deliverable-result-only).

---

## 뷰티 — 가늘고 우아하게

### 해라(단계)
1. 레퍼런스를 한국어로 뜬다(«네일샵 로고 감성»). 한국 뷰티 결 = **가는 겹친 모노그램 · 그레이지·금 · 넓은 자간**. — 왜: 비핸스 10곳으로 뽑은 안이 «너무 별로», 한국 결은 한국어 검색에서만 나옴(TIPS 2026-09-27 · PROMPTS §5).
2. 라인아트 뷰티 레퍼런스 20장(`refs/_모음/2026-10-03_라인아트뷰티20/refs.json`)의 되풀이 손잡이에서 고른다: **얼굴 옆선 + 잎 · 일부러 덜 닫은 원 · 한 획 얼굴 · 선 굵기 = 세리프의 가는 획 · 딥 세이지그린 + 아이보리 세리프 · 로즈골드**. 말로만 옮긴다.
3. 글자는 «부드럽고 우아하게»를 수치로 — 가늘고 **낮고 넓은** 산세리프, 아주 넓은 자간, 꾸밈 없음. — 왜: 사람이 «촌스럽다»고 한 게 스와시·고대비 세리프였고 되돌린 방향이 이것(TIPS 2026-09-27 [5] · PROMPTS §1 4/4 🟢).
4. 색은 처음부터 세 벌(블러시·로즈브라운 / 올리브+크림 / 토프·코코아), 한 계열 1~2색. — 왜: 흑백만 냈더니 따로 요구(TIPS 2026-09-27) · 네일 10곳 중 원색 무지개 0(`runs/2026-09-27_고객A네일/3_refs.md`).
5. «조금 작게 · 자간 넓게»는 다시 뽑지 말고 `ad respace`, 애매하면 두 단계(86%·22% / 76%·38%) 나란히. — 왜: 모양이 한 점도 안 바뀐다(TIPS 2026-09-27 12_tracking).
6. 간판이면 봉 규격부터 묻는다 — 가는 글자는 레이저(3mm↑)는 되지만 10mm 봉이 안 들어간다. 부제는 처음부터 «부제만 시트». — 왜: 190mm 글자에서 «좁음», 4mm 스터드면 본 글자 통과(TIPS 2026-09-27 [6-a]).

### 프롬프트 조각
```
soft, elegant, airy modern display sans-serif — LIGHT weight with thin even strokes (about 2% of the image height),
letters WIDE and LOW (not tall, not condensed), VERY generous letter-spacing, NO swashes, NO flourishes
```
```
subtitle much smaller, extremely wide letter-spacing, thin geometric sans
```
(둘 다 `runs/2026-09-27_고객A네일/14_en_soft` — 4/4, 사람 «원하던 방향»)
⚠️ 위 «about 2%» 는 고객A 네일(간판 190mm 글자)에서 맞았던 값이다 — 매번 [공통 «굵기»](#굵기--숫자로-박지-말고-그때그때-알맞게-정한다-사람-지시-2026-10-10) 대로 쓰임 크기·글자 수를 보고 N% 를 새로 정해 넣어라.

### 통과
- 획 굵기가 **이번에 정한 값**(공통 «굵기») 근처이고 가장 작게 쓰일 크기에서도 안 사라진다, 스와시가 몰래 안 붙었다, 길쭉해지지 않았다.
- 넓은 자간이 실제로 넓다 — ChatGPT 는 «넓은 자간»을 잘 안 지킨다(sign-proof 로고 재작업).
- 간판이면 `ad check --w-mm <실제 가로>` 로 최소 획·봉(TIPS 2026-09-27).

### 봐라
- 가장 가는 선이 작게 줄였을 때 사라지나(레퍼런스 노트 «가장 가는 선, 간판에선 사라질 위험»).
- 흔한가 — «분위기 가장 비슷, 그만큼 흔함»(로즈골드 백합 잔가지). 흔하면 한 손잡이만 바꾼 안을 하나 더(STAGES 4).
- 세밀한 그림을 로고에 다 넣었나 — 레퍼런스는 «세밀한 그림은 로고에서 빼고 패턴으로» 갔다.

### 겪은 것
- 2026-10-03 · 고객H 뷰티: 원안이 작고 흐려 그대로 따면 상업용이 안 됨 → AI 두 곳에 `--ref` «그대로 깨끗하게» → 원본 크기(제미나이 2266px) → `ad upscale` → potrace(흐림 2·opttolerance 0.8). vclean 1,266 곡선 → potrace 257, 세리프·잎 끝은 alphamax 1.0 으로 안 뭉개짐 (TIPS 2026-10-03)
- 2026-10-03 · 일러 «컨셉을 벡터로»와 겨루려 했으나 크레딧 부족 — 사람 결정 «크레딧 못 쓴다, 우리 기능 쓴다» (`../DUELS.md`)
- 2026-09-27 · 고객A 네일: 스와시·고대비 세리프 «촌스럽다» → PEONIA 결(가늘고 낮고 넓게) 🟢 · 흑백만 냈더니 색 요구 (TIPS 2026-09-27)

### 시도 대기열
- [ ] 라인아트 뷰티 20의 손잡이를 «한 줄씩» 10안으로 — 고객B 건에서 그림 없이 손잡이만 줘서 10/10 따른 방법을 뷰티에 (TIPS 2026-10-10, 뷰티엔 미시도)
- [ ] 가는 산세리프와 라인아트 심벌을 `drawn with the SAME pen` 으로 짝짓기 — 고양이에서 «글씨와 짝이 맞음» 🟢(PROMPTS §2), 얼굴·잎엔 미시도
- [ ] 같은 안을 봉 10mm / 4mm 스터드로 `ad sheet` 두 번 — 어느 쪽이 «가는 우아함»을 살리나

---

## 선 — 라인아트

### 해라(단계)
1. 선 결을 셋 중 하나로 정한다 — **가는 선 / 굵고 고른 선 / 겹선 스케치**(`refs/그림은 어떤 느낌으로_/무엇으로 그릴까_/선으로/`). 간판으로 가느냐가 가른다.
2. 간판(까치발)으로 가면 처음부터 **굵고 고른 선 · 끝 둥글게 · 획끼리 닿게(1~3조각)**. — 왜: 7획·10획 고양이가 한 조각으로 나옴(PROMPTS §4 · TIPS 2026-09-27). 예쁘게 뽑고 나서 굵히면 손맛이 죽는다(PROMPTS §0-8).
3. 겹선 스케치는 화면·인쇄 전용으로 쓴다 — 분위기는 최고지만 선 0.8mm·잡티 130~190, 굵기만 키운 판도 끝이 1.8mm 에서 걸림(TIPS 2026-09-27 · PROMPTS §2).
4. «선 일러스트» 요청이어도 까치발이면 **면 안을 한 장 같이** 낸다. — 왜: 사람이 결국 고른 게 면 고양이(최소 두께 39mm · 2조각)(TIPS 2026-09-27).
5. 선 굵기 «만» 바꿀 땐 `--ref` + `change ONLY the line weight`. — 왜: 그림 그대로 굵기만 바뀜 🟢(PROMPTS §2 cat/bold).
6. «귀엽게·획 줄이기»로 시키지 말고 «예쁘게 · 실제 비율 · 만화 아님 · 글씨와 같은 펜». — 왜: 앞은 이모지 고양이 «안 이뻐», 뒤는 🟢(PROMPTS §2).
7. «뾰족하면 시공이 안 된다»를 **벡터를 불려서 고치지 않는다** — 원본을 `--ref` 로 «선 끝만 둥근 마감·고른 굵기»로 다시 뽑는다(`ad redraw --blunt`). — 왜: 굵기 들쭉날쭉한 라인아트를 불리니 «울퉁불퉁». ChatGPT 끝 2.2 → 7.5mm, 제미나이 3.1mm(TIPS 2026-10-03 [시공]).
8. 둥근 선 로고는 `ad vecc --engine potrace`, 각진 로고는 `vecc`(기본). — 왜: Potrace 가 곡선은 가장 매끈, 대신 뾰족한 끝이 뭉개짐(TIPS 2026-09-28 [5]).

### 프롬프트 조각
```
LINE ILLUSTRATION, even line weight, NO fills
```
```
every stroke BOLD with a harmonious, consistent weight (thinnest part at least 2.5% of the image width, no hairlines,
no tapered needle tips, rounded stroke ends), strokes should TOUCH or CONNECT … as few separate pieces as possible
(ideally 1 to 3), no tiny floating dots
```
```
a pretty, elegant cat … real-looking graceful cat with natural cat proportions (not a cartoon, not a kawaii emoji) …
drawn with the SAME pen as a luxury high-contrast serif logotype
```
```
The attached drawing is FINAL — redraw EXACTLY … change ONLY the line weight
```
(겹선 스케치를 원하면: `loose sketchy pen drawing, contour lines drawn two or three times slightly offset, open unfinished line ends, varying line weight` — PROMPTS §2, 간판✕)

### 통과
- 실제 크기 가정에서 `ad fabcheck <svg> --h <mm> --min <mm>` — 가장 가는 곳·뾰족한 끝 0(벡터 §7 · sign-proof).
- 조각 수 · 떨어진 점 0 · 티끌 0.

### 봐라
- 선 끝 바늘, 열린 끝이 의도인가 실수인가, 작게 줄였을 때 선이 사라지나.
- 선 끝이 전부 둥근 캡슐이 됐나 — 시공엔 좋지만 «AI 같다» 소리가 나는 바로 그 모양이다(TIPS 2026-10-10).

### 겪은 것
- 2026-10-10 · 고객B: monoline + round cap 이 «AI 같다»로 되돌려짐 (TIPS 2026-10-10)
- 2026-10-03 · 고객H: 벡터 기하로 불리기 → 울퉁불퉁, `--blunt` 재뽑기가 깨끗 (TIPS 2026-10-03)
- 2026-09-27 · 고객A 네일 고양이: 겹선 분위기◎ 간판✕ · 굵게만 🟢 · 귀엽게 🔴 · 예쁘게 🟢 · «선으로» 시켰는데 면이 나와 사람이 고름 (PROMPTS §2)

### 시도 대기열
- [ ] 시공(둥근 끝·고른 굵기)과 «AI 티 없음»(깎인 끝·굵기 대비)이 부딪힌다 — 같은 선 로고를 «둥근 끝» / «사선 끝» 두 벌로 뽑아 사람이 어느 쪽을 고르나
- [ ] `--blunt` 를 제미나이·ChatGPT 둘로 같은 원안에 다시 — 끝 mm 비교가 한 건뿐이다

---

## 붓 — 붓글씨·캘리

### 해라(단계)
1. «붓글씨»를 한 덩이로 보지 않는다 — **굵은 붓 / 마른 붓**을 나눠 시킨다. — 왜: 같은 상호 굵은 붓 73.7mm 통과, 마른 붓 15.4mm(절곡하려면 1.6m 글자)(sign-proof 5단계 · TIPS 2026-09-23).
2. 상용 글꼴을 먼저 대 본다 — 붓 글꼴은 «굵고 끝이 깎인 붓맛»을 자주 못 낸다. 안 맞으면 AI 레터링. 라이선스는 OFL 원문·눈누 BI/CI 칸까지. — 왜: 세 안 다 글꼴로 안 됐고 이유를 그림으로 남겼다(벡터 §2 · TIPS 2026-10-10 [글꼴]).
3. 캡슐 결을 이름 불러 막는다(아래 첫 조각). 실루엣을 장마다 다르게 박는다(지붕 덩어리 · 가른 원 · 세로 현판 · 글자 속에 녹이기 · 목판 조각). — 왜: 처음으로 서로 안 닮은 다섯이 나옴(TIPS 2026-10-10).
4. 잔선(기와 빗금·붓 튀김)이 걸리면 «GRAPHIC DESIGN, NOT an illustration: 3~4 큰 면 + 이름»으로. — 왜: 다섯 다 큰 면과 여백만 남음(TIPS 2026-10-10).
5. 사람 스케치가 있으면 `--ref` + «composition exactly · 글자 바꾸지 마라»(`runs/2026-10-10_붓구도로고`). 스케치 혼자면 투박함이 따라온다 → «LAYOUT» 판(공통).
6. 간판이면 **«붓끝 그대로» + «`--blunt` 시공안» 두 벌**을 같이 낸다. `--change` 에 «가장 가는 곳이 굵은 획의 1/3 아래로 가지 않게». — 왜: 2.4m 폭에서 13.4mm·뾰족한 끝 9곳 ↔ 46mm·0곳, 획 배치는 그대로(sign-proof 2026-10-06 고객I).
7. 벡터로 딸 땐 **둥근 붓 글씨에 `ad straighten` 금지**, 열린 고리(감기는 ㅇ)는 닫지 않는다, 바늘 끝은 그 구역만 «열기». — 왜: 세 작업자가 따로 돌려 셋 다 버림(ㅇ 속이 곧은 선, ㄴ 이 네모)(벡터 §5·6 · TIPS 2026-10-10).
8. 붓글씨풍 «발·귀·혹»은 디자인일 수 있다 — 유지 / 펴기 두 안으로(sign-proof · LESSONS §3).

### 프롬프트 조각
```
NO rounded capsule-like stroke ends, NO uniform monoline — sharp, chiseled, tapered or obliquely cut ends with strong
thick-and-thin contrast, like a confident brush or a carving knife
```
(TIPS 2026-10-10, 제미나이 + 붓·도장 결 판)
```
GRAPHIC DESIGN, NOT an illustration: only 3 or 4 large flat shapes plus the name. NO fine lines, NO hatching,
NO roof-tile strokes, NO outlines
```
(TIPS 2026-10-10 — «모티프는 모양으로만 암시» + 색 2~3개를 같이)
```
The attached image is my own rough hand sketch of a Korean brush-calligraphy logo. Turn it into a finished, beautiful logo
while keeping its composition exactly: the same strokes in the same places … Do not add, remove or change any characters,
and do not write any other text. Style: elegant black sumi ink brush calligraphy, confident strokes with dry-brush texture
at the stroke ends, thick-thin contrast … One small red square seal stamp near the lower right as the only accent.
```
(`runs/2026-10-10_붓구도로고/jobs.json` B1 — 받았으나 사람 판정 전)

### 통과
- 철자 음절마다(«근» 의 ㄴ 붙음·떨어짐까지 — 벡터 봐라 목록).
- 간판이면 시공안의 최소 획이 판정 통과, 붓끝 그대로 안은 «불가»를 내부 시트에만.
- 마른 붓 텍스처가 잡티로 안 남는다(벡터화 전 확인 — 크레용·긁힌 질감은 잡티가 된다, `runs/2026-09-28_드로우사인로고/3_refs.md`).

### 봐라
- 꼬리·찢긴 붓끝·실꼬리 · 도장 속 깨진 잡글자(«천/첟» — 빼고 사람에게 묻는다, 벡터 §3) · 엔진이 지어 넣은 띠.

### 겪은 것
- 2026-10-10 · 붓구도로고 굵기 다시: 사람 *«굵기 니가 알아서 잘 바꾸라고 왜 똑같은걸 가져와»*(규칙만 적고 시안에 안 적용했다). ① 앞 결과를 `--ref` + «change ONLY the stroke weight» + 결마다 % → **골드·수채는 확실히 굵고 살아남, 먹붓은 조금, 로즈와인·가는 펜은 거의 그대로** — 결과물을 붙이면 ChatGPT 가 거의 베껴 돌려준다(PROMPTS §3 과 같은 고장). ② 스케치만 붙이고 «LAYOUT only» + 더 센 숫자(9%/6%/3%) → **먹붓은 굵고 가는 대비가 뚜렷**, 가는 펜은 눌림이 보임, **로즈와인은 대비는 늘었지만 전체는 오히려 가늘어졌다**. → 굵기를 확 바꾸려면 앞 결과 대신 **스케치 + 숫자**가 낫다(한 건) (`runs/2026-10-10_붓구도로고/jobs_weight*.json`) — 사람 판정 전
- 2026-10-10 · 붓구도로고: 사람 스케치 `--ref` + 다섯 결(먹붓 · 로즈와인 그라데이션 · 골드/네이비 · 수채 파스텔 · 가는 펜) ChatGPT, **5/5 받음**(장당 35~42초, B3 는 두 장 비교로 `_a`/`_b`, 5번째는 첨부가 한 번 빠져 다시 넣음). 다섯 장 모두 스케치 구도·획 자리를 그대로 지켰다(Claude 가 나란히 대조). B1 낙관 안 글자는 지어낸 글자 — **사람 판정 전** (`runs/2026-10-10_붓구도로고/gen.log`)
- 2026-10-10 · 고객B: 붓·목판 결 → 잔선 지적 → «면 몇 개»로 해결 · 캡슐 지적 → 깎인 끝 문구로 해결 · 말로만 준 ChatGPT 11장이 한 결로 모임 (TIPS 2026-10-10)
- 2026-10-10 · 세로 현판: 글자만 흑백으로 떼어 redraw → 제미나이가 갈라짐·실꼬리를 정리, ChatGPT 는 갈라짐을 베낌 (벡터 겪은 것)
- 2026-10-06 · 고객I: 붓끝 그대로 13.4mm ↔ `--blunt` 46mm (sign-proof)
- 2026-10-04 · 고객H «메»: 붓글씨풍 모서리가 potrace 에서 불거지거나 처진 발 — 곡선 다시 맞추기는 효과 없음, 원호로 (TIPS 2026-10-04 · LESSONS §1·2)

### 시도 대기열
- [ ] 붓구도로고 다섯 결을 사람에게 보여 판정 받기 → 그라데이션·수채 결은 간판 채널 불가라 고르면 `ad gradient --bands 3` 톤 띠로(STAGES 6, 미시도)
- [ ] 같은 스케치·같은 다섯 프롬프트를 제미나이로 — 엔진 차이를 붓에서 한 번 더
- [ ] «굵은 붓 / 마른 붓»을 같은 상호로 나란히 뽑아 판정 mm 비교(09-23 이후 다시 안 함)

---

## 고급 — 세리프·스와시·모노그램

### 해라(단계)
1. «고급스럽게»를 형용사로 주지 않는다 — 원하는 손잡이(고대비 세리프 / 꾸밈 없는 명조 / 스와시 자리)를 말한다. — 왜: `refined modern luxury display lettering` 만 주니 스와시 달린 **길쭉한 로만**(PROMPTS §1 «너무 길쭉»).
2. 한글 명조 + 스와시면 **스와시 자리를 지정**한다(ㅈ 첫 획 말림 · ㄹ 끝 스와시). — 왜: 4/4, 철자 4/4(PROMPTS §1 8_kr).
3. 꾸밈을 빼려면 «PLAIN and HONEST»로 끝을 음절 안에 가둔다. — 왜: 깨끗한 명조 3/3 🟢(PROMPTS §1 10_plain).
4. 비율(덜 길쭉하게)은 말로 조금, 확실한 건 뽑은 뒤 `ad squash`. — 왜: `WIDE, OPEN proportions` 로 조금만 넓어짐(PROMPTS §1 7_v3).
5. 한국 고급 네일 결 = **고대비 세리프 + 넓은 자간 부제**, 놀이 결 = 둥근 산세리프 + 스크립트(`runs/2026-09-27_고객A네일/3_refs.md` 공통점 2).
6. 까치발 철문자는 «가는 선이 되는» 간판이라 고급 세리프·모노그램이 산다 — 단 조각마다 까치발이니 획이 닿게(TIPS 2026-09-27 [4·6]).

### 프롬프트 조각
```
Custom Korean logotype … designed to match an elegant high-contrast roman with calligraphic swashes (thick vertical stems,
thin hairline-like joins, flared serif ends)
```
```
PLAIN and HONEST: absolutely NO swashes, NO curls, NO flourishes, NO extended strokes … every stroke ends normally within
its own syllable. Honest standard proportions: each syllable fits a square, even spacing
```
```
monogram of J and N interlocked, thin high-contrast didone … enclosed in a thin elegant vertical oval ring
```
(전부 `runs/2026-09-27_고객A네일` — PROMPTS §1·2)

### 통과
- 길쭉하지 않다(가로÷세로를 원하는 비율과 대조), 스와시가 이웃 줄·부제에 **안 닿는다** — `ad check` 가 한글4안 스와시와 부제가 0mm 로 닿은 걸 사람보다 먼저 잡았다(TIPS 2026-09-27 [6]).

### 봐라
- 헤어라인(가는 이음)이 실제 크기에서 사라지나 · 스와시가 «촌스러움» 쪽으로 넘어갔나 — 같은 건에서 스와시는 «호평»(7_v3)과 «촌스럽다»(TIPS) 둘 다 들었다.

### 겪은 것
- 2026-09-27 · 고객A 네일: 형용사만 → 길쭉 로만 · 스와시 자리 지정 4/4 · PLAIN 3/3 🟢 · JN 오벌 모노그램이 한국 레퍼런스 결과 맞음 · `--ref` + «비율만» 안 먹힘 (PROMPTS §1~3)

### 시도 대기열
- [ ] 같은 상호로 «스와시 하나만» / «스와시 없음» 두 안 — 어디부터 «촌스럽다»가 되나 경계 찾기
- [ ] 스와시 글자를 까치발 봉 4mm 로 판정(가는 이음이 몇 조각으로 갈리나)

---

## 글자만 — 워드마크

### 해라(단계)
1. 글꼴부터 대 본다 — 라이선스 원문 있는 후보 5~10개를 원안과 같은 배치로 한 장에. 안 쓰면 «왜»를 비교 그림으로 남긴다. — 왜: 벡터 §2 · TIPS 2026-10-10 [글꼴]. STAGES 0 도 «로고의 글자는 글꼴로 조판»이 기본.
2. 사람이 «AI 레터링»을 원하거나 글꼴로 안 되면 AI 레터링을 뽑아 **원본을 옮기기만** 한다(충실한 벡터화 + 제작에 걸리는 곳만 국소 수정). — 왜: 2026-10-07 사람 판정 «제미나이가 만든 정답 말고는 못 쓴다» — 선·함수로 다시 그린 것은 전부 탈락(메모리 stroke-lettering-study).
3. «조금 다듬기»는 **한 획·한 글자만** 손댄다. — 왜: 앱 아이콘 30 중 «조금 다듬기»가 전부 그랬다(티머니 T 머리 · CGV 폭죽 한 점)(`refs/_모음/2026-09-28_앱스토어_아이콘30/INDEX.md` 4).
4. 같은 결로 새 낱말이 필요하면 앞 결과를 `--ref` 로 «NEW lettering, not the reference word … EXACTLY the same style». — 왜: «이 글씨체로 새 낱말» 🟢(PROMPTS §3) · 버튼 글씨 넷을 이렇게 보냈다(`runs/2026-09-29_버튼글씨/jobs.json`).
5. 상호 + 부제 두 줄이면 `ad vec`(또는 `keep_text` 끈 옛 길). — 왜: 부제가 조용히 사라졌다(TIPS 2026-09-27 [5]).
6. 바탕(틀)과 글씨를 따로 뽑아 «갈아 끼우기». — 왜: 같은 바탕에 글씨만 10장, 붙이기는 20장 몇 초(TIPS 2026-10-10 [5]).
7. «모던·미니멀하게»는 `ad respace`(뷰티 5 참고).

### 프롬프트 조각
```
Create an image: a wordmark logo lettering. The text must read exactly "DRAWSIGN" (8 capital letters in this exact order:
D R A W S I G N), spelled correctly, one single line, nothing else written. … Solid near-black ink (#1b1d1c) on a pure white
background. Flat vector artwork, NO mockup, NO sign, NO shadow, NO texture, NO paper, NO 3D, NO decoration around it.
Wide horizontal composition, the word fills about the central 70% of the width with generous white margin.
```
(`runs/2026-09-28_드로우사인글씨/jobs.json` 공통 틀 — 결 자리에 넣은 넷: `Custom bold geometric sans-serif, tight even spacing … all strokes the same thickness` · `Heavy rounded sans-serif lettering with soft corners, warm and approachable` · `Bold condensed sans-serif lettering, tall and narrow` · 마커는 아래 낙서 절. 결별 사람 반응은 기록 없음)
```
Create an image: NEW lettering, not the reference word. Hand-lettered text in EXACTLY the same style as the reference image: …
The text must read exactly "의뢰하기" (4 characters in this exact order: 의 뢰 하 기) … Korean Hangul must be correct and fully legible.
```

### 통과
- 글자 대비 3↑(STAGES 5) · 영문 철자 4/4·한글 8/8 수준으로 맞았나(TIPS 2026-09-27) · 판정은 «앉힌 글자 높이»로(TIPS 2026-09-23).

### 봐라
- 띄어쓰기(«no space»를 어긴 적 있음) · 자간이 들쭉날쭉(원래 글자 높이의 8~15%로 흔들렸다, TIPS 2026-09-27).

### 겪은 것
- 2026-10-10 · 고객B: 글꼴 10여 종 비교 → 맞춤 배치·붓맛이 안 맞아 세 안 다 «원안 글씨 AI 고해상 재작성» (TIPS 2026-10-10)
- 2026-10-07 · 함수로 다시 그린 레터링 전부 탈락 — AI 원본만 씀 (메모리 stroke-lettering-study)
- 2026-09-27 · 고객A 네일: 자간을 음절 떼어 옮기기로 고침, 모양 그대로 🟢 (TIPS 2026-09-27)

### 시도 대기열
- [ ] 드로우사인글씨 네 결(마커·기하·둥근·좁은)을 다른 상호로 다시 — 사람 반응이 기록 안 된 걸 채우기
- [ ] 바탕/글씨 갈아 끼우기를 두 번째 건에서 — 되면 `ad` 로 올림(TIPS 2026-10-10)

---

## 굵은 손글씨 — 낙서·마커

### 해라(단계)
1. 레퍼런스는 **영어 브랜드명**으로 찾는다(Oatly · Ben & Jerry's · 드리블 워드마크 모음). — 왜: 한국어 «낙서 손글씨 로고 굵은»은 스톡 낙서 요소뿐(TIPS 2026-09-28 [3]). 한국 가게 결이 아니라 «글자 결»을 찾을 때의 예외.
2. 공통 결 셋을 지킨다 — **굵기는 거의 고르다 · 글자마다 크기·기울기가 조금씩 흔들린다 · 한 색**. 크레용·긁힌 질감은 안 쓴다(잡티가 된다). — 왜: `runs/2026-09-28_드로우사인로고/3_refs.md`.
3. 결을 넷으로 나눠 뽑는다(블록 · 버블 · 만화 · 마커, 아래 조각). «poster»·«hand-painted»는 빼고 `Generate an image.` 를 앞에. — 왜: 3/3 이미지 안 나옴 → 2/2(LOG 2단계).
4. 마커는 «WIDE»를 넣어도 길쭉하게 나온다 → 뽑은 뒤 `ad squash`(LOG · PROMPTS §1).
5. 벡터는 `ad vecc --engine potrace --no-snap`. — 왜: 기본 vecc 가 «I» 를 자로 그은 막대로 폈다(TIPS 2026-09-28 [4]).
6. «그리는 애니메이션»을 원하면 마커(고른 굵기) 안을 고르고 중심선으로 다시 세운다(`ad draw`). — 왜: 굵기 ×1.35 · 세로 ×0.8 해도 획이 안 가늘어짐, 정지 로고와 애니메이션이 같은 선(TIPS 2026-09-28 [5]). 채운 면 안은 «닦아 드러내기»만 된다(LOG).

### 프롬프트 조각
```
The word must read exactly "DRAWSIGN" (eight capital letters in this exact order: D R A W S I G N) … one single line
```
```
① bold hand-drawn doodle logotype — fat, heavy, squarish block capitals drawn by hand with a thick marker and filled in solid,
   each letter a slightly different height and slightly tilted, edges a little wobbly
② doodle bubble lettering … puffy, rounded, inflated capitals filled solid black
③ bold comic-book doodle lettering — heavy hand-drawn capitals with a slight dynamic slant … brush pen
④ very fat round felt-tip marker … bold monoline capitals with rounded stroke ends, bouncy baseline
```
(PROMPTS §1 · 철자 8/8)

### 통과
- 철자 · 중심선 뼈대가 획 수만큼(18획) — 뼈대가 118조각으로 부서지면 계단 픽셀부터 걷는다(TIPS 2026-09-28 [5]).

### 봐라
- 닫힌 고리(D)가 점 하나로 줄었나(선 단순화 함정) · 애니메이션은 진짜 브라우저 앞 탭에서(헤드리스는 transform 을 안 돌린다)(TIPS 2026-09-28 [5]·[8]).

### 겪은 것
- 2026-09-28 · 드로우사인: 4결 × 2 = 8장 철자 8/8 · 블록이 «이미지 안 나옴» 3연속 · 사람이 «그리는 애니메이션 만들기 좋은 걸로» → 마커 D 안 → 사이트 머리 로고로 배포 (`runs/2026-09-28_드로우사인로고/LOG.md`)
- 2026-09-29 · 버튼 글씨 넷을 같은 마커 결로 `--ref` 해 보냄(결과 판정 기록 없음) (`runs/2026-09-29_버튼글씨`)

### 시도 대기열
- [ ] 한글 상호(드로우사인)로 같은 네 결 — 이번엔 «한글은 이번 판에 안 넣음»(가정)이었다(`1_input.md`)
- [ ] 마커 D 를 아이콘용으로 획만 굵힌 판(오프셋) — 한 색 면·테 룩에서 가볍다는 지적(`runs/2026-09-28_로고빛/LOG.md`)

---

## 면 — 큰 면 몇 개·실루엣

### 해라(단계)
1. 기본을 «면 몇 개»로 둔다 — `GRAPHIC DESIGN, NOT an illustration` + 3~4 큰 면 + 색 2~3개, 모티프는 모양으로만 암시. — 왜: 사람 요구가 «그림 그대로 → 캡슐 선 → 잔선 → 도형»으로 옮겨 갔다(TIPS 2026-10-10 [4]).
2. 모티프는 «들린 곡선 두 줄»처럼 줄이고 다른 부분과 **같은 선 굵기·같은 곡선**으로 맞춘다. — 왜: 기와 한 장씩·뚜껑까지 다 그린 솥이 «뻔하고 이상하다»(TIPS 2026-10-10 [4·5]).
3. 작게 쓰는 마크면 «재료 가득한 그림» 대신 실루엣만. — 왜: 재료 가득한 냄비 안이 작게 쓰면 뭉개짐(TIPS 2026-10-10 [3·4]).
4. 까치발이면 면 실루엣이 가장 유리하다(최소 두께 39mm · 2조각)(TIPS 2026-09-27).
5. 도형은 가장 단순하게, 차이는 색으로 — AI 앱 셋이 전부 가운데 대칭 도형 하나, 갈린 건 색뿐(`INDEX.md` 1). 빈 자리에 숨긴 그림(O 구멍 = 렌즈)은 간판에선 «속공간» 판정 대상(INDEX 5, 추정).
6. 업종에서 흔한 심벌이면(상표 부담) 표현·모티프 한 손잡이만 바꾼 안을 하나 더(STAGES 4).
7. 벡터: 각진 면(별·왕관·십자) = `vecc`, 둥근 면(동물) = `vecc --engine potrace`(TIPS 2026-09-28 [5]).

### 프롬프트 조각
```
flat vector logo symbol, solid fills only, NO gradient, NO text, NO letters, pure white background, centered with wide white margin
```
(STAGES 4 — 프롬프트에 반드시)
```
solid silhouette in one flat color, no inner lines except simple negative-space cuts
```
```
lying down curled and dozing, head resting on the front paws, the fluffy tail wrapping around the body in one elegant swash
```
(PROMPTS §2 — 선으로 달라 했는데 면이 나왔고 사람이 «이게 좋다» 🟢)

### 통과
- 큰 면 개수 3~4 · 잔선 0 · 작게(앱 아이콘 크기) 줄여도 읽힌다(STAGES 8-a 통과 조건).

### 봐라
- 속공간(고양이 눈·발 흰 선)이 판정을 끌어내리나 — 글자 탓으로 적지 말고 심벌 없는 안과 비교(TIPS 2026-09-27 [6], 8mm vs 91mm).

### 겪은 것
- 2026-10-10 · 고객B: 면 몇 개로 바꾸자 다섯 다 큰 면과 여백 · 모티프 생략은 원안 배지가 처음부터 그 결이었다 (TIPS 2026-10-10)
- 2026-09-27 · 고객A 네일: 면 고양이를 사람이 고름(까치발) (TIPS 2026-09-27)

### 시도 대기열
- [ ] 같은 모티프를 «면 3개 / 면 5개»로 — 몇 개부터 «일러스트»로 읽히나
- [ ] 면 마크에 `ad flatfx --style tone`(톤 겹쳐 쌓기)로 입체감만 — 간판 겹 아크릴로 그대로 난다는 관찰(TIPS 2026-09-28 [8-a])을 마크로

---

## 엠블럼·배지·도장

### 해라(단계)
1. 간판 로고면 **«한눈에 정사각형 실루엣, 단 얇은 테두리 배지는 아님»**. — 왜: 사람 요구(TIPS 2026-10-10 [4]).
2. 이름을 판·병 안에 가두는 배지는 피한다 — 간판 크기에서 글자가 작아지고 원호 글자는 까치발로 못 만든다(`runs/2026-09-27_고객A네일/3_refs.md` «안 쓸 것»).
3. 도장(낙관)은 «작은 붉은 네모 하나»로만 — 붓 B1 조각. 엔진이 도장 속에 넣는 글자는 깨진 잡글자일 수 있다 → 빼고 사람에게 묻는다(벡터 §3).
4. 손님 엠블럼(사진·자수)을 평면으로 옮기는 건 원본 재현이다 — 작으면 `ad upscale` 뒤 «AS FAITHFULLY AS POSSIBLE … The ONLY changes: …», 대화 셋에 한 장씩. — 왜: 3/3 밑단이 원본처럼 붙은 띠 🟢(PROMPTS §7 아담 왕관). 잰 그림을 같이 주면 복사만 해서 «완전 별로»(TIPS 2026-09-28, 취소선).
5. 색이 여럿인 엠블럼은 `ad retrace` 로 따지 않는다 — 한 색만 따고 그라디언트를 건다 → 색별 마스크 `multitrace.py`(벡터 §4 · TIPS 2026-10-10 [벡터]).
6. 그라디언트 금색 엠블럼은 **색 시안과 재단 파일을 나눈다**(`ad cutfile`) — PDF 를 거치면 윤곽 클립 + 큰 네모가 따라온다(TIPS 2026-10-04 · LESSONS §1).

### 프롬프트 조각
```
circular badge: text and symbol inside a single round ring
```
```
symbol and two lines of text arranged to fill a square block
```
(둘 다 `refs/어떻게 묶을까_/한 덩어리로/` · 후보 샘플에 보낸 판: `A circular badge logo: the words MOON COFFEE curved along a thin ring around a crescent moon symbol in the middle, one navy color` — 결과 판정 기록 없음)

### 통과
- SVG 칠 색 수 = 팔레트 수 · 그라디언트 0(재단 파일) · 흰 바탕 네모 0(벡터 §4 통과).

### 봐라
- 링 글자·작은 부제가 실제 크기에서 판정 걸리나(부제는 거의 늘 봉이 안 들어간다, PROMPTS §4) · 선만 보기에서 숨은 다른 색 조각(겹선)(벡터 §6).

### 겪은 것
- 2026-10-10 · 고객B: 정사각 실루엣 요구 · 도장 속 잡글자 빼고 물음 · multitrace 신설 (TIPS 2026-10-10 · 벡터 §3·4)
- 2026-10-03~04 · 고객H 골드 엠블럼: retrace 가 무리(emblem·wordmark·beauty)별 3단 금색 그라디언트로 땀 → 재단선은 `cutfile` (`runs/2026-10-03_duel_고객HA/base_측정.json` · LESSONS)
- 2026-09-28 · 아담 왕관: 자수 엠블럼에서 글자만 빼기 `--ref` 2/2 · 업스케일 후 원본 재현 3/3 (PROMPTS §7)

### 시도 대기열
- [ ] 정사각 실루엣 엠블럼을 «도장 격자 / 원 / 팔각» 세 실루엣으로 같은 상호에 — 한 손잡이(실루엣)만 바꾼 3안
- [ ] 한식 엠블럼 도장 결을 손잡이 한 줄로(TIPS 2026-10-10 디테일 빌리기)만 주고 몇 장이 «얇은 테두리 배지»로 새나 세기

---

## 귀여움·마스코트

### 해라(단계)
1. «귀엽게»·«획 줄이기»를 그대로 넣지 않는다 — 이모지가 나온다. «예쁘게 · 자연스러운 비율 · NOT a cartoon, NOT a kawaii emoji»로 시작해 귀여움을 수치로 더한다. — 왜: PROMPTS §2(🔴 «안 이뻐» / 🟢).
2. 캐릭터는 귀여움 비율을 **숫자로** 넣는다 — 머리÷몸 ≥0.8, 눈 중심 55~65%. — 왜: STAGES 4(design-atlas `tree/로고.md` 수칙 — 로고 건에서 결과를 잰 기록은 없다, 추정).
3. 캐릭터와 글씨는 같은 펜으로(`drawn with the SAME pen as the logotype` — `refs/…/캐릭터/REFS.md`).
4. 간판으로 갈 거면 흰 눈·연한 색의 대비를 본다 — 듀오링고 흰 눈 2.1:1 은 폰에선 되지만 간판 거리에선 약하다(INDEX 6, 잰 값).

### 프롬프트 조각
```
a pretty, elegant subject with natural proportions (not a cartoon, not a kawaii emoji), drawn with the SAME pen as the logotype
```
(`refs/어떤 로고로 할까_/어떤 모양새로_/캐릭터/REFS.md`. 후보 샘플에 보낸 판: `A cute mascot character logo: a round friendly moon character with a small smiling face holding a tiny coffee cup, with the word MOON below it, two colors navy and mustard` — 결과 판정 기록 없음)

### 통과 · 봐라
- 이모지처럼 보이지 않나(사람 반응이 기준) · 작게 줄였을 때 얼굴이 읽히나 · 대비 3↑.

### 겪은 것
- 2026-09-27 · 고객A 네일: «귀엽게, 약 7획» → 이모지 고양이 «안 이뻐» · «예쁘게, 실제 고양이 비율» 🟢 (PROMPTS §2)

### 시도 대기열
- [ ] 귀여움 비율 숫자(머리÷몸 0.8 · 눈 55~65%)를 실제로 넣고 / 빼고 두 장 — 수칙이 먹히나 처음 재기
- [ ] 마스코트 한 장을 «면 실루엣» 결로도 — 까치발·채널 판정 비교

---

## 입체·광택 — 화면용 한 벌

### 해라(단계)
1. **평면 SVG 가 원본이다.** 입체는 홈페이지·SNS·앱 아이콘용 파생 한 벌 — `ad flatfx`(평면 기법) 또는 `ad render3d`(Blender)(STAGES 8-a).
2. 앱 아이콘 결로 갈 땐 평면 기법 먼저 — 렌더는 옆에 두면 혼자 튄다. 평면 결을 안 깨는 입체는 **톤 겹쳐 쌓기**(TIPS 2026-09-28 [8-a] · 사람 «너무 렌더링스럽긴 한데 이쁘긴 하다»).
3. 크롬은 앞면 반사선 위에 띠 조명, 먹색 광택은 그 자리를 비운다 — 둘 다 첫 판이 거꾸로였다(TIPS 2026-09-28 [8-a]).
4. 유리·반사광 아이콘은 대부분 «그린 것»이 아니라 iOS Icon Composer 가 입힌 것(요약만 봄)(TIPS 2026-09-28 [8-a]).

### 통과 · 봐라
- 대표색이 틀어지지 않았나 — 와인 `#8E3A4D` 가 광택 렌더에서 `#CC8893`(분홍)로 떴다(`runs/2026-09-28_로고빛/LOG.md`, 잰 값). 평면판과 나란히 본다.

### 겪은 것
- 2026-10-17 · 수산나 앱 심벌(원 안의 S): 🔴 **AI 에 «내 정확한 선»을 첨부하면 새 선이 안 나온다**(사람: «창의적인 라인이 안 나온다») → 흔들리는 펜 선 + 칠할 곳에만 빗금 친 «대충 밑그림» + 느낌(공식 로고 이름으로) + «따라 그리지 마라, 곡선·가늘어짐·기울기는 네가 정해라» 로 주니 ChatGPT 3/3 이 바로 S 로 읽혔다. 고른 뒤 «끝만 바꿔라»(원본 첨부)는 몸통·색 띠를 5/5 지켰다. 그라데이션 아이콘 PNG 는 256색으로 줄이면 띠에 계단이 생긴다 — 크기(192)로 줄여라 (`runs/2026-10-17_수산나_앱로고/LOG.md`)
- 2026-09-28 · 로고빛: 워드마크 7종 + D 4종 렌더 · 평면 여덟 가지 · 브랜드색 분홍 문제 미해결 (`runs/2026-09-28_로고빛/LOG.md`)

### 시도 대기열
- [ ] 광택 렌더에서 브랜드색 역보정(재질 색을 더 짙게) — 미해결로 남아 있다

---

## 아직 모르는 것

- **결별 사람 반응이 빈 칸이 많다** — 드로우사인글씨 네 결 · 후보 샘플(MOON 카페 22장) · 버튼 글씨 · 붓구도로고 다섯 결은 «보낸 프롬프트»만 있고 사람 판정 기록이 없다. 조각을 «먹힌 것»으로 올리지 않았다.
- **시공과 «AI 티 없음»이 부딪힌다** — 까치발은 «굵고 고른 선 + 둥근 끝»을 원하고, 사람은 «캡슐 같다»를 싫어한다. 어디서 타협하나 한 건도 재지 않았다.
- **«로고 글자는 AI 가 그리지 않는다»(STAGES 0)와 «AI 원본만 쓴다»(2026-10-07 사람 판정) 사이** — 지금은 «글꼴 먼저, 안 맞으면 AI 레터링을 옮기기만»으로 읽었다. 둘을 한 문장으로 확정한 사람 결정은 없다.
- **귀여움·마스코트**는 한 건(고양이)뿐이고 사람 얼굴형 마스코트·동물 외 캐릭터는 없다. 귀여움 비율 수칙은 미검증.
- **뷰티 라인아트 «얼굴 옆선»을 우리가 직접 뽑은 기록**은 레퍼런스 20장 정리뿐이고, 고객H는 손님 원안 재작업이었다 — 처음부터 설계한 뷰티 라인아트 로고는 아직 없다.
- **마젠타 투명 배경을 로고에** 쓴 기록 없음(게임·인물 시트에서만 잼).
- 쌍자음 한글 레터링은 «찌» 한 단어만 확인. ㅆ·ㄲ·ㄸ·ㅃ 는 모른다.
- **따뜻함·볼드, 레트로, 네온** 같은 결은 근거가 없어 절을 만들지 않았다(드로우사인 `c_warm`·고객A `retro1` 이름만 있다).

---

## 변경 이력
- 2026-10-17 — «입체·광택» 겪은 것 한 줄(대충 밑그림 + 느낌으로 AI 선 살리기, 수산나 앱 심벌).
- 2026-10-10 (이어서) — 공통에 «굵기 — 숫자로 박지 말고 그때그때 알맞게» 절(고르기 창에서 저장). 뷰티의 «2%» 를 예시로 낮췄다. 사람: *«굵기는 다이나믹하게 너가 알아서 잘 딱 알맞게 정해야 한다고»*.
- 2026-10-10 — 최초 작성(v0). 사람: *«이제 레시피를 만들건데 뷰티는 어떻게 선은 어떻게 뭔 어떻게 이걸 다 담은 단계 및 팁 md를 만들자»*. TIPS·PROMPTS·STAGES·logo_vector·LESSONS·DUELS·runs(고객A네일·드로우사인·로고빛·후보샘플·고객H duel·붓구도로고)·refs(라인아트뷰티20·앱스토어30·개념 폴더 조각)·gemini/chatgpt SKILL·sign-proof 로고 재작업·메모리 디자인 항목에서 실제로 보낸 프롬프트와 사람 반응만 옮겼다. 결 열 개, 공통 한 절.
