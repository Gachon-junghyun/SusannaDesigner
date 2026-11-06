# AD_README — `python -m ad` 잔손질 도구와 옛 작업 틀 안내 (옛 aidesigner README, 2026-10-19 수산나 디자이너로 이사)

> 🔴 일을 시작하는 입구는 이 문서가 아니라 [`CLAUDE.md`](CLAUDE.md) 다. 이 문서는 `ad` 명령과 옛 단계(STAGES·TIPS)의 근거로 남긴다.

> **뭐냐:** 상호 하나를 로고 3안 → 간판 판정 → 에디터 조립 → 일러스트 굽기까지 **정해진 단계로** 밟고, 한 건마다 배운 것을 쌓는 곳. 형제 `design-atlas`(나무) 옆.
> **언제 읽나:** 로고·간판 한 건을 시작할 때 — **[`TIPS.md`](TIPS.md) → [`STAGES.md`](STAGES.md) → 프롬프트 쓰기 전 [`PROMPTS.md`](PROMPTS.md)** 순서로.
> **안 담는 것:** 도구 코드 — 전부 이미 있는 것을 부른다(아래 표). 손잡이 수칙 원본 → `../design-atlas/tree/로고.md`.

| 파일 | 뭐냐 |
|---|---|
| 🟢 [`guides/`](guides/README.md) | **갈래 지도** — AI 디자이너 일을 갈래로 나누고 갈래마다 «해라» 가이드. 로고→간판(아래 STAGES) · **3D 모델링 v0**(`guides/modeling.md`). `/menu` «AI 디자이너 갈래» 로 연다 |
| [`STAGES.md`](STAGES.md) | 단계마다 입력·산출·통과 조건·사람 확인점 |
| [`TIPS.md`](TIPS.md) | 🔴 매 작업 끝에 날짜 박은 팁 한 줄 이상. 다음 작업은 여기부터 |
| [`SHARE.md`](SHARE.md) | 남에게 보여 줄 한 장의 틀 |
| [`PROMPTS.md`](PROMPTS.md) | 🔴 분위기 말 → 제미나이 문장 조각(실제로 준 프롬프트·나온 그림·사람 반응) · `--ref` 규칙 |
| `ad/` | 🔴 **잔손질 모듈** — `python -m ad vec·vecc·check·measure·clean·respace·squash·stack·preview3d·gradient·split·sheet·upscale·look·zoom·strip·export`. 사람이 짚던 디테일은 `ad check` 가 잡는다 |
| 🔴 [`NEXT_PROMPT_로고폼_정보수집.md`](NEXT_PROMPT_로고폼_정보수집.md) | **다음 세션 시작점**(2026-09-28) — 공식 로고 서비스들이 받는 정보 조사 → /logo 에 참고 이미지·1차/2차/포인트 색 받기. 지금 상태·되돌려진 것 |
| 🔴 [`NEXT_PROMPT_디자인나무.md`](NEXT_PROMPT_디자인나무.md) | 디자인 나무를 «고객이 보는 나무»로 다시 짜는 인계 — 보는 사람은 고객, 가지 = 고객의 질문 |
| 🔴 `refs/` | **레퍼런스 창고(비공개)** — 디자인 나무 개념마다 참고 그림(남의 것 포함) + 프롬프트 조각. `python -m ad refs …`. 사이트·깃·드라이브로 옮기지 않는다 → [`refs/README.md`](refs/README.md) |
| `sim/standoff_sheet.py` | 까치발(T9) 45° 원근 시뮬레이션 + 까치발 자동 배치 + A3 시안 세트 — STAGES 6-a |
| 🟢 **실제 홈페이지** | `HOMEPAGE_MAKER/sites/drawsign` — 랜딩(이 폴더 `web_proto/` 그대로) + 서비스 다섯(`/logo` `/sign` `/lettering` `/check` `/color`) + `/editor` (2026-09-28) |
| `runs/<날짜>_<상호>/` | 한 건의 단계별 산출물 + `LOG.md`(걸린 시간·막힌 곳·사람 손) |
| 🟢 `.claude/skills/` | **남이 만든 웹 화면 디자인 스킬 15개**(2026-10-14, 전부 MIT, 각 폴더에 `LICENSE.*`). TasteSkill 14개(`Leonxlnx/taste-skill` c924fad) + Design Motion Principles(`kylezantos/…` 4a9ca87). 🔴 **DeGaJa 세션에서는 사람이 `/add-dir <작업 폴더>` 를 쳐야 실린다.** 이 폴더에서 띄운 세션은 그냥 실린다. 기본 `taste-skill`(`/design-taste-frontend`) 스크립트는 Node 22+ 로 **자기 전용 헤드리스 크롬**을 임시 프로필로 띄운다(9222 로그인 크롬은 안 건드린다). 업데이트는 원 저장소를 다시 받아 덮어쓴다 — 손으로 고치지 마라 |
| 🟢 `design-md/<브랜드>/DESIGN.md` | **브랜드 디자인 시스템 84장**(`VoltAgent/awesome-design-md` c7c1bad, MIT). 인스타의 «Awesome Claude Design 68종»은 링크 모음일 뿐이고 실제 파일은 여기다. 브랜드 이름을 살짝 바꾼 «inspired» 판(Stripe → Stripi) |
| 🟢 `kit/design-md-chrome/` | **크롬 확장**(`bergside/design-md-chrome` 8e07614, MIT) — 열린 탭의 글꼴·색·간격 → DESIGN.md/SKILL.md. 웹스토어에 없어서 **사람이** `chrome://extensions` → 개발자 모드 → «압축해제된 확장 프로그램 로드» → 이 폴더. 에이전트는 확장 없이 `fast eval` 로 같은 값을 뽑을 수 있다 |

부르는 것 (새로 짓지 않음): design-atlas `python -m datl lookup` · `/errand`·`/research`(레퍼런스) · `/gemini-image` `gen.py` ·
수산나 메이커 `/admin/maker/logo`·`/admin/maker/draw`(관리자 전용 베타, F26-k·l) · `proof.py vector`(vclean·fab) · `maker_up.py` · `maker_bake.py`.

🟢 **큰 동작은 클로드 + 제미나이, 잔손질은 `ad/`** (2026-09-27 사람 결정: *"자잘한 걸 계속 생성하지 말고 … 내가 챙긴 디테일은 모듈화해서 너가 더 디테일을 잘 챙길 수 있게"*).
같은 손질을 새 스크립트로 또 짜지 마라 — `ad` 에 없으면 거기에 한 칸 더한다. 벡터화기(vclean)·판정 자(FAB)는 새로 짓지 않고 부른다.

| `python -m ad …` | 무엇 | 어디서 배웠나 |
|---|---|---|
| `vec` | 그림 → 평평한 SVG (2배 · keep_text 끔 · 흰 배경 뺌) | 두 줄 부제가 사라짐(D-13) · 흰 배경 사각형 |
| `vecc` | 🟢 **여러 색 로고 → 색마다 층인 SVG(일러 시안)** — 원은 원, 띠는 반듯한 직사각형, 나머지는 모서리+직선+스플라인 곡선. `--engine potrace` = 둥근 로고용(곡선 가장 매끈, 끝은 뭉개짐) · `--no-snap` = 손글씨·낙서 레터링(«I» 가 막대로 펴지지 않게) | 아담 왕관: `vec` 로는 1px 요철이 오돌토돌·줄이 계단 |
| `check` | 흰 배경 · 빠진 조각 · 테두리 닿음 · 겹친 획 · 가는 획/테이퍼 · 좁은 틈 · 잡티 · 가까운 조각 · **줄끼리 닿음** · 자간(`--letters`) · 봉 안 들어감 | 고객A 네일에서 사람이 짚은 것 전부 |
| `measure` | 최소 획·속공간·조각·까치발 수 | sign-proof 와 같은 자 |
| `clean` | 겹침 합치기 · 굵게/가늘게(`--thicken`) · 잡티 빼기 | 겹선 고양이 237조각 → 15 |
| `respace` · `squash` · `stack` | 글자 작게+자간 · 상하 줄이기 · 심벌 위+글자 아래 | «모던·미니멀» · «덜 길쭉» · «고양이 그대로» |
| `preview3d` · `sheet` | 까치발 45° 입체 · 시안 세트(배치도·타공 본) | «원근 45°» · «자동 까치발» |
| `gradient` | 그라데이션 미리보기 + 만들 수 있는 톤 띠 SVG | 로고.md «채널은 면 하나 한 색» |
| `split` | 조각·줄·글자로 분리 | 제작·배치도용 낱개 |
| `draw` | 🟢 **한 획 마커 레터링 → 중심선 로고 + «펜으로 그리는» 애니메이션** — 뼈대를 따서 `stroke` 로 다시 그린다(굵기 `--weight`·세로 `--sy` 를 획 손상 없이). 정지 SVG · 애니메이션 SVG(`<img>` 로도 돔) · `--tsx` 사이트 부품(currentColor·var(--wine), `--cycle` 초마다 다시 그림, 움직임 줄이기면 멈춤). 🔴 채운 버블·블록 글자엔 안 맞는다 | 드로우사인 자체 로고(D안) |
| `upscale` | 작은 원본 → 4배(Real-ESRGAN, 로컬 GPU). `--model realesrgan-x4plus`(사진·자수, 기본) · `-anime`(평면 그림) | 아담 왕관 154px 자수 사진 — 키워서 `--ref` 로 주니 밑단이 원본처럼 나왔다 |
| `look` | SVG·PDF·AI·PNG 를 **2000px** 로 그려 보기 + `--zoom x0,y0,x1,y1` 확대 칸 | 🔴 1024 로 보고 «됐다» 했는데 크게 보니 오돌토돌 |
| `zoom` | 좌표 확대: 좌표 없이 부르면 Claude 가 볼 크기의 «보는 판», `x1 y1 x2 y2`(그 판 픽셀)를 주면 원본에서 떼어 한도까지 키움. 확대판에서 또 확대(옆 json 이 원본 좌표). PDF·AI·SVG 는 벡터로 다시 그림 | 비율 좌표·고정 격자로는 에이전트가 «보면서 고르기»가 안 됐다. claude-cookbooks crop_tool 근거. 절차 `protocols/grade.md` §1 |
| `strip` | 원본과 후보(벡터 포함)를 같은 높이로 한 줄에 | 사람에게 «뭐가 달라졌나»를 한 장으로 — 매번 손으로 붙였다 |
| `export` | SVG → `.pdf`·`.png`·**`.ai`**(이 PC 일러스트레이터로 «진짜» 저장) · `--phone` 이면 .ai·.pdf 를 텔레그램으로(끊기면 두 번 더) | 사람은 PC 앞에 없다 — 일러 파일을 폰으로 달라고 했다 |
| `flatfx` | 🟢 **평면 기법 한 벌** — 한 색 면 · 바탕 흐름 · 그림에만 흐름 · 톤 겹쳐 쌓기 · 반투명 겹침 · 롱섀도 · 테 · 그려 넣은 광택(아무 로고 SVG, 크롬 헤드리스로 PNG) | 앱스토어 아이콘 30개를 뜯어 본 평면 디테일(2026-09-28) |
| `render3d` | 🟢 **Blender 입체 한 장** — 크롬 · 먹색 광택 · 유리 · 전면 발광 · 후광 · 발광 흐름(씬 `sim/scene_logo3d.py`, DeGaJa_Agent `module_render` 로 돈다) | «블랜더 급으로 빛을 찍어» — 로고빛 실험 |
| `redraw` · `retrace` · `fabcheck` · `swap` · `board` · `straighten` · `cutfile` | 🟢 **로고 재작업 한 바퀴**(`ad/relogo.py`): 원안을 AI 두 곳이 그대로 다시 그림(원본 크기 다운로드, `--blunt` 선 끝만 둥글게) → 매끈한 SVG(potrace, 티끌·워터마크 제거, 무리별 그라디언트) → 실제 mm 에서 가는 곳·뾰족한 끝 표시 → 한 무리만 교체 → 한 .ai 묶음(외곽선) → 사람이 조립한 .ai 의 곧은 획 테두리 꺾임 펴기·위아래 줄맞춤·테두리 사이 모서리 층 정리(`straighten [--humps]`, 일러 COM) → 따낼 재단선 파일(`cutfile`: 그라디언트 네모·대지 밖 사본 없이 외곽선만). 순서는 DeGaJa `/sign-proof` «로고 재작업 모드» | 고객H 뷰티(2026-10-03): vclean 1,266 곡선 울퉁불퉁 → potrace 257 매끈, 벡터 불리기는 울퉁불퉁해서 폐기 |
| `refs` | 레퍼런스 창고: `scaffold`·`list`·`prompt <개념>`(조상부터 조각을 이어 줌)·`add` | 디자인 나무를 레퍼런스·샘플로 쌓자는 사람 결정(2026-09-28) |
| `picker` | 🟢 **고르기 창**(앱 창) — 디자인 나무를 그림과 함께 띄워 사람이 고르고(단계별·나무 전체·인상 거름), 고른 개념의 설명·프롬프트 조각·샘플/레퍼런스 파일을 Claude 에 넘긴다. 뽑은 그림을 같은 창에 띄워 «이걸로 진행/다시» 를 받는다. 선택지마다 **그림판**(모든 그림·올리기/붙여넣기/끌어놓기·펜 스케치·«위에 그리기»·남길 말 → `runs/<날짜>_picker_<세션>/boards/`), Claude 는 `design_add_ref` 로 선택지에 레퍼런스를 올린다(→ `refs/` 영구, REFS.md «[Claude] …»). MCP 는 `ad/picker_mcp.py`(DeGaJa_Agent `.mcp.json` 의 `design-picker`) · 혼자 시험 `python -m ad picker`. 127.0.0.1 전용·토큰 | 사람: «말로 하지 말고 앱 띄워서 고르게»(2026-10-10). 조사 DeGaJa `research/2026-10-10_claude-design-oss` |

🟢 **손님 원본 로고를 «그대로» 일러 시안으로** (아담 왕관 2026-09-28 — 사람이 여섯 번 되돌리며 정한 순서):
`ad upscale 원본 --out up.png` → `/gemini-image` 로 **대화 셋**에 `up.png` 를 `--ref` + PROMPTS §7 «원본 재현» 프롬프트 → `ad strip` 로 원본과 나란히 보여 고르게 →
`ad vecc 고른.png --out 시안.svg` → `ad look 시안.svg --out x.png --zoom …` 로 **크게** 확인 → `ad export 시안.svg --phone`.
🔴 **하지 말 것:** 사진을 파이썬으로 재서 그린 그림을 레퍼런스로 주기(«완전 별로» — 제미나이가 그 딱딱함을 복사만 한다) · 1024 로 보고 끝내기.

🔴 **손님 자료(사진·시안·연락처)는 `runs/` 에 두되 이 폴더를 어디에도 올리지 않는다**(git 아님 · P7). 상호와 그림까지만.

---

## 변경 이력
- 2026-10-24 — `ad zoom`(좌표 확대) 한 줄. 절차는 `protocols/grade.md`.
- 2026-10-14 (이어서2) — 금융 홈페이지 첫 판을 지었다(`HOMEPAGE_MAKER/sites/degaja-finance`). 웹 화면 갈래 첫 가이드 `guides/web.md` v0.
- 2026-10-14 — 남이 만든 웹 화면 디자인 도구 넷을 들였다: `.claude/skills/`(TasteSkill 14 + 모션 1) · `design-md/`(84장) · `kit/design-md-chrome/`. 인스타 캐러셀(sdk.kim.builds × _dot.move)을 보고 사람이 «다 쥐어줘». 다섯째인 UI UX Pro Max 는 이미 `~/.claude/skills` 에 있다. 전역이 아니라 이 폴더에 둔 이유: 평소 DeGaJa 세션에 스킬 설명 15개를 싣지 않으려고.
- 2026-10-10 (이어서) — 고르기 창 «그림판»(선택지마다) + MCP `design_add_ref`(Claude 가 레퍼런스를 `refs/` 에 올리고 열린 창에 바로 보임). 사람이 올린 그림·스케치는 창고가 아니라 그 건의 `runs/…/boards/` 에만 둔다.
- 2026-10-10 (이어서4) — 고르기 창 **«레시피»**: `guides/*.md` 를 왼쪽에서 열어 마크다운으로 보고, 절(## )마다 «고치기»로 바로 고친다 (옛 판은 `guides/_history/`, 그새 Claude 가 고쳤으면 충돌로 막고 새 판을 받는다 — Claude 가 파일을 고치면 창이 몇 초 안에 새로 받는다). «이 결로 쓰기»로 고른 절은 보낼 때 `recipes`(절 원문)로 Claude 에게 간다. 나무 칸 오른쪽에 이름·인상이 맞는 레시피 절 링크. 첫 레시피: `guides/logo_looks.md`(결 열 개).
- 2026-10-10 (이어서3) — **레퍼런스 모음 뷰어.** 나무 칸에 안 묶인 조사 묶음(`refs/_모음/<이름>/items.json`)을 왼쪽 «레퍼런스 · …»으로 연다 — 갈래 거르기(국내·해외·글자만·도형…) · 흰 로고는 어두운 바탕 · 사이트 첫 화면 캡처 · 출처 링크. MCP `design_collect` 로 만든다. 같이 손에 닿게 고친 것: **← → 넘기기 · 스페이스 고르기**, 고른 그림마다 **한 줄 메모**(«어디가 좋은지» → `memo` 로 Claude 에게), **나란히 보기**(고른 그림 한 판에), 바탕 바꾸기(알아서·흰·어두운·체크), 보내기 버튼에 개수. 첫 모음: 수학 학원 로고 23(국내 13·해외 10).
- 2026-10-10 (이어서2) — **호버로 오른쪽이 안 바뀐다.** 가운데 카드는 «눌러서 오른쪽에 열기»만 하고, 고르기는 오른쪽에서 한다: «이 선택지 고르기» + 그림마다 «이 그림 고르기»(썸네일 모서리 네모). 고른 그림은 아래 칸에 작은 그림으로 쌓이고 `design_wait` 에 `chosen_files` 로 온다. 큰 그림은 오른쪽 위에 붙어 있어 아래 썸네일을 눌러도 안 사라진다. 사람: «레퍼런스를 보려는데 다른 데 호버되면 바로 바뀐다».
- 2026-10-10 (이어서) — 고르기 창에 **주고받기** 칸. 누가 언제 뭘 보냈고 상대가 받았나(«Claude 가 받음 22:02 / 아직 안 받음»), 머리에 «Claude 가 듣는 중 / 안 듣는 중» 불, 보내기 옆 «아직 안 보냄». `design_wait` 가 빈손일 때 그림판에 붙이고 안 보낸 게 있으면 `board_unsent` 로 알려 준다. 사람이 스케치를 붙이고 «보내기»를 안 눌러 Claude 가 아무것도 못 받은 일이 있었다.
- 2026-10-10 — `ad picker`(고르기 창) + `ad/picker_mcp.py`(MCP 도구 넷). 나무는 design-tree.ts 를 읽기만 한다(사이트 파서와 같은 규칙), 프롬프트 조각은 `refs.prompt()` 를 부른다.
- 2026-10-07 — `guides/` 신설(갈래 지도 + 3D 모델링 가이드 v0). 로고→간판은 STAGES.md 를 그대로 첫 갈래로 가리켰다. `/menu` «AI 디자이너 갈래» 묶음과 연결.
- 2026-10-04 (이어서2) — `straighten` 모서리 정리(`_corners`, `--humps`). 곡선 다시 맞추기(`fair`)는 넣었다가 뺐다 — 일러 화면에서 효과가 없었다.
- 2026-10-04 (이어서) — `straighten` 2차(가로 이음을 사이에 둔 테두리 줄맞춤 · 최소제곱 직선 · 이음새 35°) · `cutfile` 추가 · PDF 는 `_보기용`. 고객H «메».
- 2026-10-04 — `ad straighten`(relogo.py): 선만 보기에서 «두 줄로 꺾인» 수직·수평 획 테두리를 직선 한 줄로. 고객H 간판 시안 «메» 에서 일회용 스크립트로 한 것을 옮겼고, 같은 원본으로 돌려 전달본과 0px 차이임을 확인.
- 2026-10-03 — `ad/relogo.py` 다섯 명령(redraw·retrace·fabcheck·swap·board). 오늘 일회용 스크립트를 옮겼고 같은 파일로 돌려 결과가 같음을 확인(곡선 257·139·133).
- 2026-09-28 (이어서9) — `ad flatfx`·`ad render3d`(`ad/finish.py` · `sim/scene_logo3d.py`) — 로고를 화면용 한 벌(평면 기법 8 · 입체 7)로. STAGES 8-a · TIPS 다섯 줄. 실험은 `runs/2026-09-28_로고빛/`.
- 2026-09-28 (이어서8) — 다음 세션 인계 `NEXT_PROMPT_로고폼_정보수집.md`.
- 2026-09-28 (이어서7) — `ad draw`(중심선 로고 + 그리기 애니메이션 + 사이트 부품). 드로우사인 D안을 사이트 머리에 올렸다.
- 2026-09-28 (이어서6) — `vecc --no-snap`(손글씨·낙서 레터링은 원·직사각형으로 펴지 않음). 드로우사인 자체 로고에서.
- 2026-09-28 (이어서5) — `vecc --engine potrace`(자글자글 제거의 정석) 추가. 비교해 보니 각진 로고는 own 이 낫다 — 기본은 own.
- 2026-09-28 (이어서4) — `ad upscale·look·strip·export` 와 «손님 원본 로고 → 일러 시안» 흐름 한 단락. `vecc` 본체를 `ad/vecc.py` 로 뺐다(CLI 에 있던 것).
- 2026-09-28 (이어서3) — `ad vecc`(여러 색 로고 → 일러 시안 SVG) 한 줄.
- 2026-09-28 (이어서2) — 디자인 나무 재구성 인계 문서 한 줄(사람: «보는 사람은 고객»).
- 2026-09-28 (이어서) — `refs/` 레퍼런스 창고 + `ad refs` 명령(개념 64개 폴더 · 프롬프트 조각 13개).
- 2026-09-28 — 실제 홈페이지 경로 한 줄(`HOMEPAGE_MAKER/sites/drawsign`).
- 2026-09-27 (이어서2) — `ad/` 잔손질 모듈 · `PROMPTS.md` 추가(사람 요청: 모듈화 · 프롬프트 사전 · 디테일 자동 검사).
- 2026-09-27 (이어서) — `sim/standoff_sheet.py` 추가(까치발 시뮬·자동 배치·시안).
- 2026-09-27 — 최초 작성(사람 요청 «startup sign AI designer»).
