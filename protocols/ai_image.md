# protocols/ai_image — AI 이미지 (ChatGPT·제미나이): 레터링·로고 뽑기, 다시 그리기, 렌더 사진화

> **뭐냐:** ChatGPT·제미나이로 그림을 뽑는 모든 일의 규칙. **반드시 스킬로 부른다** — `/chatgpt-image`(`DeGaJa_Agent/.claude/skills/chatgpt-image/gen.py`) · `/gemini-image`(`…/gemini-image/gen.py`). API 가 아니라 크롬(9222)을 조종한다.
> **언제 읽나:** 레터링·로고 후보를 뽑을 때, 흐린 원안을 다시 그릴 때, 3D 렌더를 실사로 바꿀 때, 실내 재질·현판을 만들 때.
> **안 담는 것:** 스킬의 조작 함정 원문 → 두 스킬의 SKILL.md(끝까지 읽고 쓴다) · 결별 프롬프트 → [`logo.md`](logo.md) §결.

---

## 부르는 법

```
python DeGaJa_Agent/.claude/skills/chatgpt-image/gen.py --out <폴더> --jobs <jobs.json> --per-chat 1 [--skip-done]
python DeGaJa_Agent/.claude/skills/gemini-image/gen.py  --out <폴더> --jobs <jobs.json> --per-chat 1 [--ref <화풍.png>]
```
- 잠금: `python SusannaDesigner/kit/logo_vector/lock.py img -- <위 명령>` (그림 뽑기는 한 번에 하나).
- jobs 의 `"ref"` 는 **절대 경로**(상대 경로면 첨부 없이 보내져 «원본이 첨부되지 않았다»로 실패).
- 서로 독립인 장은 `--per-chat 1`(같은 대화에서 앞 그림이 섞인다).
- 스킬이 자기 탭을 열고 닫는다. 돌던 묶음을 죽였으면 **남은 내 탭만** 닫는다. 남의 탭은 건드리지 않는다.
- 두 엔진을 동시에 돌리지 않는다(다운로드가 상대 폴더로 샌다). 대량 생성 금지.

## 엔진 고르기
| 일 | 엔진 | 왜 |
|---|---|---|
| 지시를 정확히(철자·구도 유지·사진화) | ChatGPT | 지시 따르기가 낫다 |
| 폭 넓은 후보(레퍼런스 판과 함께) | 제미나이 | 말로만 준 ChatGPT 는 한 결로 모인다 |
| 제미나이 «이미지 안 나옴» 연속 | ChatGPT 로 | 원인 미확인 |

## 프롬프트 공통
- ChatGPT 는 `Create an image:` 로 시작, 제미나이가 글로 답하면 `Generate an image.`.
- **지킬 것을 부품별로 한 문장씩**(목록 한 단어로 적으면 빠진다 — 고객I 액자).
- 한글은 음절을 풀어 한 번 더 · 쌍자음은 틀릴 모양을 이름 불러 금지.
- 평면 아트워크는 «NOT a mockup, NOT a photograph, pure white background, wide margin».
- 컷마다 **그 컷에 보이는 것만** 적는다. 안 보이는 컷엔 «이 화면엔 간판·글자가 없다, 넣지 마라».
- 사람 얼굴은 흐린 채 넣고 «얼굴을 그리거나 또렷하게 만들지 마라»(얼굴 사진을 AI 에 올리지 않는다).
- 창·옆 가게 글자는 «쓰인 그대로»를 예시로(고객J «토»가 «도»로 바뀜).

## 렌더 사진화 (3D → 실사)
1. 입력 = 3D 렌더(낮·밤 따로). 지킬 것: 글자 음절 · 서체 결 · 채널 깊이·옆면 색 · 스카시·판 · 조명(무엇이 켜지고 꺼지나, 빛 방향) · 건물·창 시트·차양·보도 «그대로» · «Output only the photo».
2. 받은 것은 **3D 와 간판 확대를 나란히** 서체·철자·위치·기울기·조명·창 글자를 대조한 것만 낸다. 틀린 장은 `버림/` 에 이유를 붙여 두고 다시.
3. **크기 판단에 AI 그림을 쓰지 않는다** — 간판을 28~39% 얇게 그렸다. 실제 비율 합성을 같이 낸다.
4. 옆 가게가 뭉개지면 우리 간판 상자만 남기고 원본 사진으로 되돌린다.

## 다시 그리기 (흐린 원안 → 깨끗하게)
- `ad redraw --engines chatgpt,gemini --change "<지킬 것 부품별 + 바꿀 것 하나>"` 또는 `--ref` + «AS FAITHFULLY AS POSSIBLE».
- 정확한 선을 첨부하면 새 선이 안 나온다 → 대략적인 밑그림 + «따라 그리지 마라».
- 남의 로고는 첨부하지 않는다(말로만 옮김). 넘으려면 사람 결정.

## 공개·납품
- 공개 그림은 `python -m ad unmark` 로 ✦ 표시를 지우고 «AI 로 만든 그림»이라 적는다. AI 초안과 최종 벡터를 둘 다 보관한다.
- «손으로 쓴 글씨»로 팔지 않는다(제미나이 약관: 사람이 만든 것으로 오도 금지).

## 겪은 것 → [`../LESSONS.md`](../LESSONS.md) `[AI이미지]`

---

## 변경 이력
- 2026-10-19 — 최초 작성. 사람: *«chatgpt·gemini 는 image-gemini 같은 스킬을 이용한다»*.
