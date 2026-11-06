# TOOLS — 도구 지도 (경로로 부른다, 복사하지 않는다)

> **뭐냐:** 이 하네스가 쓰는 스크립트·스킬의 자리와 한 줄 쓰임.
> **언제 읽나:** 프로토콜 단계에서 도구를 부르기 전에. 새 도구를 만들면 같은 턴에 한 줄.
> **안 담는 것:** 단계 → `protocols/` · 도구 내부 함정 원문 → 각 도구 옆 문서.

`D` = `<홈>\DeGaJa_Agent` · `A` = `<작업 폴더>`(이 폴더, 옛 aidesigner) · `M` = `<홈>\STARTUP\model-lab\space\clientj`

---

## 공방 (모든 갈래)
| 도구 | 쓰임 |
|---|---|
| `python -m forge run·status·adopt·init·gate <건>` (A 에서) | 건마다 `pipeline.json` 하나: 바뀐 단계만 돌림, 검사, 확인 멈춤, 바깥 단계는 `--send`. 단계는 `protocols/forge.md` |
| `python -m forge zoom·diff` | 확대판 · 옵션 켬·끔 차이판 |
| `python -m forge trial·method·clock·report` | 방법 대장(두 건 승이면 공식) · 요구 종류별 시간 · 오래 걸리는 단계 |
| `python -m ad zoom <파일> [--grid 100]` → `python -m ad zoom <보는 판·확대판> x1 y1 x2 y2` (A 에서, `ad/zoom.py`) | 좌표 확대: Claude 가 볼 크기의 «보는 판»을 만들고, 그 판의 픽셀 구역을 원본에서 떼어 키운다(PDF·AI·SVG 는 벡터로 다시 그림). 확대판에서 또 확대. 기본 출력 `runs/zoom/` |
| `A\.claudegents\susanna-grader.md` · `A\_TEMPLATE\RUBRIC.md` | 독립 채점자(새 문맥, 읽기·측정만, 통과는 증거로) · 건마다 채점 기준 틀. 다른 폴더 세션은 general-purpose 에이전트에 이 파일을 읽혀 부른다 |
| `A\.claude\workflows\susanna-source-check.js` (Workflow) | 원본 대조: 시안 글자·숫자·색을 항목마다 따로 손님 원본과 대조 + 일치는 반박 담당이 다시. 넘기기 직전 한 번, 무겁다. 절차 `protocols/grade.md` §3 |
| `Aorge\lib\geom2d.py` · `bend.py` · `pdfphone.py` · `blshade.py` · `bldae.py` · `roundext.py` | 공용 부품: 필렛·둔각 구석·기둥 구석·꼭짓점 아래 받침·가장 좁은 폭 · 굽힘 펼친 길이 · 폰용 PDF · Blender 원형 마감 셰이더 · Blender 장면을 스케치업용 .dae(mm)로 쓰고 다시 읽기 · 둥근 앞 모서리 압출(원형 마감 형상) |
| `A\forge\lib\psdstack.py` `build(w,h,dpi,이름,[레이어…],psd,jpg)` | 판 크기 투명 PNG 여러 장 → 포토샵 COM 레이어 PSD(이름·불투명도·숨김·혼합). 포토샵을 먼저 띄우고, 자기 문서만 닫는다. 첫 사용 `jobs/2026-10_고객N/work/layers.py` |

## 받기
| 도구 | 쓰임 |
|---|---|
| `A\kit\sign_band\예시_띠간판\0_톡클라우드_새파일.py` · `0_톡클라우드_받기.py` | 톡클라우드 목록(방·시각·크기) → 링크 클릭 받기 → 크기 대조. 크롬 9222. 2단계 인증은 «이메일로 인증하기» + Gmail «newer_than:1d 인증번호» |
| Gmail MCP | 카톡 내보내기 메일(첨부는 `disp=attd`) |
| `D\module_browser` (`/errand`) | 사이트 직접 보기. 같은 사이트 연속은 3~9초 무작위 대기 |

## 일러스트
| 도구 | 쓰임 |
|---|---|
| `A\kit\logo_vector\lock.py illu -- <명령>` | 일러 잠금(`%TEMP%\aidesigner_illu.lock`) |
| `A\kit\logo_vector\save_cs6.py <in> <out_CS6.ai> [--cc]` | CS6(16.0) 저장. `undefined` 를 찍어도 성공 — 파일 머리로 판정 |
| `D\users\…\2026-10_부동산\work\inspect_ai.py` · `work\aunt2\finish_ai.py` · `export_full2.py` | 구조 세기 · PDF·미리보기 · 손님 .ai 대지 넓혀 400% 내보내기 |
| `A\kit\logo_vector\multitrace.py` | 색별 따기 |
| `A\kit\outline_view.py <pdf|ai> [쪽] [--clip x0,y0,x1,y1] [--out png]` | 일러 «외곽선 보기»처럼 선만 그림 + 겹친 윤곽(속공간이 아닌 부분 겹침) 세기. 0건이어야 통과(종료코드 0) |
| `python -m ad …` (A 에서) | redraw · upscale · retrace · straighten · cutfile · fabcheck · board · vec · vecc · check · respace · squash · unmark |
| 함정 | 일러는 COM 전에 `Start-Process` 로 띄우고 창 제목 확인 · 내 문서만 닫기 · 경로는 정슬래시 |

## 간판
| 도구 | 쓰임 |
|---|---|
| `M\tools\aunt_to_svg.py <full.pdf> <띠> <폴더>` | 손님 .ai → 색별 실물 mm SVG(채널·테 몸통·스카시·판·검은 글자) + meta.json |
| `M\tools\build_ai.py <띠폴더> <out.svg>` | 1:10 일러용 SVG(그룹 이름 = 부재) |
| `M\tools\font_variants.py <띠> <ttf>` | 서체를 손님 배치에 맞춰 바꾸기 |
| `A\jobs6-10_고객L\workB4\glyphs.py` · `build_logo.py` · `edit_proposal.py` · `tidy_layout.py` · `redo_3d.py` · `overlay_1024.py` | 서체 윤곽 → 일러 JSX(글자 높이·자간을 시트 자리에 맞춤) · 1:1 로고 CS6 · 남의 제안서 .ai 글자·색·치수선·없는 글꼴 바꾸기 · 띠·꼬리 간격을 잉크 기준으로 맞추기 · 3D 캡처에 원근 글자 얹기·색 옮기기 · 서체 겹쳐 보기 |
| `D\.claude\skills\sign-proof\compare_a4.py <spec.json>` | 수산나 A4 세로 «안 비교» 시트(글자·크기 안). 각 안 제안서 PDF 의 정면도 구역을 벡터로 옮기고 숫자 표를 붙인다. 글꼴 `A
efsonts\`(고운바탕·본고딕 정적). 본보기 spec `A\jobs6-10_고객L\workB4\compare_spec_1024.json` |
| `D\.claude\skills\sign-proof\` | `proof.py`(contact·vector·sheet·pack·flatten·pdfvec) · `trace_orig.py` · `elevation.py` · `maker_up.py`·`maker_bake.py` · `proposal.py`(A4) |
| `D\users\…\2026-10_부동산\work\ratio_check.py` · `fontcmp.py` | 비율 점검표 · 현장 글자와 글꼴 IoU |
| `A\kit\sign_band\예시_띠간판\1~5_*.py` | 띠 간판 색 바꾸기·원판·축척 PDF·실제 비율 합성 |

## 3D
| 도구 | 쓰임 |
|---|---|
| `python -m module_render run M\scene\doan.py -- …` (D 에서) | `--cam A/B/C --mode after/mask/night --face A/B/AB --center --signk K --sign3d <폴더> --nobar --downlight` |
| `M\scene\sign3d.py` | 입체 간판(채널·스카시·판·라인박스) |
| `M\tools\composite.py` · `fix_tilt.py` · `clear_old.py` | 낮 합성(`--wallref`·`--k`) · 기울기(높이 유지) · 옛 간판 지우기 |
| `M\tools\batch_이모수정3*.sh` | 렌더 묶음 본보기 |
| `A\jobs\2026-10_수산나포스터\work\scene_s.py` · `scene_ribbon.py` · `compose.py` | 입체 포스터 본보기: 마크 SVG 압출 / 중심선 띠 → 검정 무대 Cycles(투명 배경) → 번짐·그라데이션·글자 조립. 재현 명령은 그 폴더 `JOB.md` |
| `A\jobs\2026-10_수산나포스터\work\smooth_s.py` · `bumps.py` | 래스터에서 딴 윤곽을 «잘린 끝 곧은 선 + 옆선 스플라인 + 둥근 모서리» 베지어로 다시 그리기 · 윤곽 곡률 그래프(울퉁불퉁 판정) |
| `python -m ad fluted <그림> --out <png>` (A 에서, `ad/fluted.py`) | 골유리(세로 골 유리) 굴절: 띠 폭·눌러 담기 배수·경계 그늘·앞뒤 흐림. 기법 카드 `techniques/골유리_굴절.md` |
| `python -m ad liquid --text "S U|SAN|N A" --font <ttf> --out <png> [--glow]` (A 에서, `ad/liquid.py`) | 평면 판 위 액체 크롬 덮개(굴절·반사·흰 테·강조·박막 간섭) + 글자 뒤 역광(후광·빛줄기). 기법 카드 `techniques/액체_크롬_반사.md`·`무지개_테.md`·`역광_후광.md` |
| `D\.claude\skills\analyze-poster-design\` (`/analyze-poster-design`) | 포스터 한 장 해부를 끝까지 한 번에: 방향 바로잡기 → pgrid detect·fix·analyze → 글꼴 확대 → 꼬리표·모음표·INDEX → styles·techniques 카드 → 다섯 절 보고 |
| `python -m ad pgrid detect·fix·analyze·summary` (A 에서) | 포스터 레퍼런스 해부: OCR + 잉크 높이로 글줄, 바탕색 차이로 그림 상자 → `fix` 로 눈으로 고친 것 반영 → 단·행 그리드 맞추기 · 글자 크기 사다리 · 그림 자리 · 글↔그림 관계 · 색·모양·질감 → `grid.png`·`style.png`·`REPORT.md` / 여러 장 모음표·열지도·색 띠. 창고 `A\refs\_모음\포스터_그리드\`. 단계는 `protocols/promo.md` §포스터 레퍼런스 해부 |
| `python -m ad pgrid tag·table·types·check·pick·picks·embed·similar·picker·layout` (A 에서, `ad/pdata.py`·`ad/playout.py`) | 레퍼런스를 데이터로: 꼬리표, 전체 표(table.csv·elements.csv), 유형 기준(types.json), 우리 시안 검사(CHECK.md), 고른 기록(picks.csv), 그림 지문 찾기(CLIP), 고르기 창 모음(items.json), 유형 규격 첫 판(PNG·SVG). 단계는 `protocols/promo.md` §레퍼런스를 데이터로 쓰기 |
| `A\jobs\2026-10_학교포스터\work\ascii.py` · `cells.py` | 문자 아트: 렌더·서체를 고정폭 격자로 재서 윤곽(방향 문자)·명암(밝기 단계)·빛·글자를 색별 레이어 PNG + 원문 txt / 정사각형 칸 쌓기 배치와 서체 후보 비교판(`cells.py compare`) |
| `A\jobs\2026-10_학교포스터\work\scene_inf.py` · `layers.py` · `build_psd.jsx` | 중심선 → 타원 관(꼬임·가로 홈·점조명) Blender 렌더 / 판 크기 레이어(점조명만 골라 번짐) / 포토샵 COM 으로 새 문서 + 글자마다 문자 레이어(시험 글자 잉크 높이로 크기 맞춤) + PSD·PNG·JPG·PDF. 재현은 그 폴더 `JOB.md` |
| `A\jobs\2026-10_수산나포스터\work\grid_overlay.py` · `make_psd.jsx` | 칸 격자(행,열 번호) 덮개 PNG·미리보기 → 포토샵 COM 으로 안내선 + 번호 레이어 PSD |
| 함정 | 한 번에 하나(GPU 하나), 종료코드 + 파일 수 확인, `D\module_render\BLENDER.md` |

## AI 이미지 (스킬로)
| 도구 | 쓰임 |
|---|---|
| `D\.claude\skills\chatgpt-image\gen.py` | ChatGPT(`--jobs --per-chat 1 --skip-done`, jobs `ref` 절대 경로) |
| `D\.claude\skills\gemini-image\gen.py` | 제미나이(`--ref`, 원본 크기 다운로드) |
| `A\kit\logo_vector\lock.py img -- <명령>` | 그림 뽑기 잠금 |

## 서류
| 도구 | 쓰임 |
|---|---|
| `D\.claude\skills\make-document\` | 양식 재현(SKILL·LESSONS·tools) |

## 넘기기
| 도구 | 쓰임 |
|---|---|
| `G:\내 드라이브\SUSANNA\<YYYY-MM>_<상호>\` | 복사(드라이브 MCP 업로드 금지) |
| `D\module_voice` `push_text`·`push_photo`·`push_file` · `bot='approval'` | 폰 보고·결재(사람이 «폰 금지»면 쓰지 않는다) |

---

## 변경 이력
- 2026-10-24 (이어서) — «공방»에 검수 셋 세 줄(`ad zoom` · 독립 채점자 · 원본 대조 워크플로).
- 2026-10-24 — 간판 표에 고객L 10/24 도구 한 줄(글꼴 윤곽 → 일러, 제안서 고치기, 3D 글자).
- 2026-10-22 — «공방» 절(`forge/`).
- 2026-10-19 (이어서) — aidesigner 이사로 `A` 가 이 폴더가 됐다.
- 2026-10-19 — 최초 작성.
