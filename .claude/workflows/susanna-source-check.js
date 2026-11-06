export const meta = {
  name: 'susanna-source-check',
  description: '수산나 시안의 손님 정보·사양 값을 손님 원본과 대조한다(손님 정보는 값마다 따로 + 반박 담당, 사양은 묶음으로)',
  whenToUse: '넘기기 직전 한 번. args: {job, proofs[], sources[], out, refs?[], limit?, batch?}',
  phases: [
    { title: 'Extract', detail: '시안에서 대조할 값 뽑기(두 눈 + 빠진 것) · 원본 색인 만들기' },
    { title: 'Verify', detail: '손님 정보는 값마다, 사양은 묶음으로 원본과 대조, 일치는 반박 담당이 다시' },
    { title: 'Report', detail: '보고서 파일 쓰기' },
  ],
}

// 근거: anthropics/claude-cookbooks claude_agent_sdk/08_Dynamic_workflows.ipynb
// («the fastest» 와 «one of the fastest» 차이를 잡은 건 더 센 모델이 아니라 따로 대조하고 반박해 본 구조였다)
// 10-24 첫 시험(고객K 6차 A4): 145항목을 뽑았는데 고유 값 118, 그중 우리 쪽 문구 57·사양 58·손님 정보 5.
// 항목마다 에이전트 둘이면 한 벌에 약 280개, 에이전트마다 카톡 기록 전체를 다시 읽어 약 10만 토큰 → 설계를 바꿨다:
// 같은 값은 한 번만, 원본은 색인을 먼저 만들어 필요한 줄만 열고, 손님 정보만 값마다 + 반박, 사양은 묶음, 우리 쪽 문구는 refs 가 있을 때만.
// 절차와 args 는 protocols/grade.md §3.

const A = args || {}
if (!A.job || !A.proofs || !A.proofs.length || !A.sources || !A.sources.length || !A.out) {
  throw new Error('args 가 모자란다: {job, proofs:[시안 파일], sources:[손님 원본·작업방 캡처·묻기 답 파일], out:보고서 폴더, refs?:[우리 회사 정보 등], limit?, batch?}')
}
const BATCH = A.batch || 8
const list = xs => xs.map(p => `- ${p}`).join('\n')
const ZOOM = `작은 글자·숫자는 반드시 좌표 확대로 읽는다(<작업 폴더> 에서):
  python -m ad zoom "<파일>" --out "${A.out}/zoom"          # 보는 판, 크기와 좌표계를 알려 준다
  python -m ad zoom "<보는 판 또는 확대판>" x1 y1 x2 y2      # 그 판 픽셀 구역을 원본에서 떼어 키움, 또 확대 가능
PDF·AI·SVG 글자는 PyMuPDF 로 뽑아 눈으로 읽은 것과 맞춰 본다. 파일은 고치지 않는다.`
const INDEX = `${A.out}/원본_색인.md`

const ITEM = {
  type: 'object',
  properties: {
    kind: { type: 'string', enum: ['text', 'number', 'color', 'count', 'logo'] },
    owner: { type: 'string', enum: ['client', 'ours', 'spec'], description: 'client=손님 정보(상호·전화·주소·영업시간·메뉴·로고 등), ours=수산나 회사 정보와 우리가 쓴 문구(표지 카피·설명 글), spec=치수·두께·재질·조명·색 번호·글꼴 같은 사양' },
    value: { type: 'string', description: '시안에 보이는 그대로(띄어쓰기·하이픈·대소문자·받침까지)' },
    where: { type: 'string', description: '파일, 쪽, 확대판 경로와 좌표' },
    context: { type: 'string', description: '무엇에 대한 값인가(예: 전면 상호, 정면도 전체 가로)' },
  },
  required: ['kind', 'owner', 'value', 'where', 'context'],
}
const ITEMS = { type: 'object', properties: { items: { type: 'array', items: ITEM } }, required: ['items'] }

const LENSES = [
  { key: 'words', ask: '글자: 상호(한글·영문), 부제, 전화번호, 주소, 영업시간, 메뉴·품목, URL·SNS, 문장.' },
  { key: 'numbers', ask: '숫자와 사양: 치수(가로·세로·두께·높이·이격), 축척, 수량, 재질, 조명 방식, 색 값(HEX·CMYK·도료 번호), 글꼴 이름.' },
]

phase('Extract')
const indexP = agent(
  `손님 원본 자료의 색인을 만든다. 판정은 하지 않는다. 뒤에서 검증자들이 이 색인을 보고 «원본의 정확한 자리»로 바로 가게 하는 것이 목적이다.
원본:
${list(A.sources)}
할 일: 파일마다(압축은 풀어 보지 말고 안의 목록만, 대화 기록은 줄 번호와 함께) 무엇이 들어 있는지 한두 줄. 그리고 상호·연락처·주소·치수·재질·색·조명·글꼴·수량처럼
시안과 대조될 만한 값이 나오는 자리를 «값 · 파일 · 줄 번호나 쪽 · 원문 그대로 짧게 · 날짜시각» 표로 모은다. 같은 것이 여러 번 바뀌었으면 전부 시각 순서로(최신이 기준이다).
그림·벡터 원본은 무엇이 보이는지와 글자가 윤곽선인지만 적는다. 요약하지 말고 원문을 옮긴다.
결과를 "${INDEX}" 에 쓰고(폴더가 없으면 만든다), 경로와 파일 수만 답한다.`,
  { label: 'index:sources', phase: 'Extract' })

const found = await parallel(LENSES.map(l => () => agent(
  `수산나 디자인 시안에서 «원본과 대조할 수 있는 값»을 빠짐없이 뽑는다. 판정은 하지 않는다.
이번 눈: ${l.ask} 같은 값이 여러 자리에 나오면 자리마다 따로 적는다(뒤에서 묶는다).
시안 파일:
${list(A.proofs)}
${ZOOM}
값은 보이는 그대로 적는다. 흐려서 못 읽은 글자는 추측으로 채우지 말고 [?] 로 남긴다.`,
  { label: `extract:${l.key}`, phase: 'Extract', schema: ITEMS })))

const norm = v => v.replace(/\s+/g, ' ').trim()
const groups = new Map()
const add = it => {
  const k = `${it.owner}|${it.kind}|${norm(it.value)}`
  if (!groups.has(k)) groups.set(k, { owner: it.owner, kind: it.kind, value: norm(it.value), contexts: [], wheres: [] })
  const g = groups.get(k)
  if (!g.contexts.includes(it.context)) g.contexts.push(it.context)
  g.wheres.push(it.where)
}
let raw = 0
for (const r of found.filter(Boolean)) for (const it of r.items) { add(it); raw++ }

const extra = await agent(
  `아래는 시안에서 뽑은 대조 값 목록이다. 시안을 직접 다시 보고 «빠진 값»만 돌려준다. 이미 있는 값은 다시 넣지 않는다.
특히 작은 글자(바닥글, 치수선 글씨, 표 칸, 로고 옆 작은 글)와 그림 안 글자를 본다.
시안 파일:
${list(A.proofs)}
${ZOOM}
이미 뽑은 값:
${[...groups.values()].map((g, i) => `${i + 1}. [${g.kind}/${g.owner}] ${g.value}`).join('\n')}`,
  { label: 'extract:missing', phase: 'Extract', schema: ITEMS })
if (extra) for (const it of extra.items) { add(it); raw++ }

let all = [...groups.values()]
const ours = all.filter(g => g.owner === 'ours')
let checkable = all.filter(g => g.owner !== 'ours').concat(A.refs && A.refs.length ? ours : [])
let capped = 0
if (A.limit && checkable.length > A.limit) {                    // 시험용 상한. 뺀 것은 보고서에도 적는다(조용히 자르지 않는다)
  const order = g => (g.owner === 'client' ? 0 : g.owner === 'spec' ? 1 : 2)
  checkable.sort((a, b) => order(a) - order(b))
  capped = checkable.length - A.limit
  log(`limit ${A.limit}: ${capped}개는 대조하지 않음 — ${checkable.slice(A.limit).map(g => g.value).join(', ')}`)
  checkable = checkable.slice(0, A.limit)
}
await indexP

// 대조 단위: 손님 정보는 값 하나씩, 나머지는 BATCH 개씩
const units = []
checkable.filter(g => g.owner === 'client').forEach(g => units.push([g]))
const rest = checkable.filter(g => g.owner !== 'client')
for (let i = 0; i < rest.length; i += BATCH) units.push(rest.slice(i, i + BATCH))
log(`뽑은 자리 ${raw} → 고유 값 ${all.length}(손님 ${all.filter(g => g.owner === 'client').length} · 사양 ${all.filter(g => g.owner === 'spec').length} · 우리 쪽 ${ours.length}) → 대조 단위 ${units.length}`)

const VERDICTS = {
  type: 'object',
  properties: {
    results: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          n: { type: 'integer', description: '받은 목록의 번호' },
          verdict: { type: 'string', enum: ['confirmed', 'contradicted', 'unverifiable'] },
          proof_reading: { type: 'string', description: '시안을 확대해 다시 읽은 값' },
          source_value: { type: 'string', description: '원본에 적힌 값, 없으면 빈 문자열' },
          source_quote: { type: 'string', description: '원본의 정확한 문구와 자리(파일·줄·쪽·시각)' },
          note: { type: 'string' },
        },
        required: ['n', 'verdict', 'proof_reading', 'source_value', 'source_quote', 'note'],
      },
    },
  },
  required: ['results'],
}
const CHALLENGES = {
  type: 'object',
  properties: {
    results: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          n: { type: 'integer' },
          refuted: { type: 'boolean' },
          final: { type: 'string', enum: ['confirmed', 'contradicted', 'unverifiable'] },
          reason: { type: 'string' },
        },
        required: ['n', 'refuted', 'final', 'reason'],
      },
    },
  },
  required: ['results'],
}
const sources = list(A.sources) + (A.refs && A.refs.length ? `\n(우리 쪽 참고: ${A.refs.join(', ')})` : '')
const show = gs => gs.map((g, i) => `${i + 1}. [${g.kind}/${g.owner}] «${g.value}» (${g.contexts.join(' / ')}) @ ${g.wheres.slice(0, 3).join(' ; ')}${g.wheres.length > 3 ? ` 외 ${g.wheres.length - 3}곳` : ''}`).join('\n')

phase('Verify')
const done = await pipeline(units,
  (_, gs, u) => agent(
    `시안의 값${gs.length > 1 ? ' 여러 개' : ' 하나'}를 손님 원본과 대조한다. 받은 값만 본다.
${show(gs)}
시안 파일:
${list(A.proofs)}
원본(이것만 근거로 쓴다):
${sources}
원본 색인: ${INDEX} — 어디를 볼지 찾는 데만 쓴다. 판정 근거는 반드시 원본 파일의 그 자리를 직접 열어 확인한 문구다(색인 문구를 그대로 근거로 쓰지 않는다).
${ZOOM}
1. 값마다 먼저 시안의 그 자리를 확대해 다시 읽는다(proof_reading).
2. 원본에서 같은 값을 찾는다. 바뀐 이력이 있으면 가장 최신 것이 기준이다.
3. 판정: 글자 하나·띄어쓰기·하이픈·숫자 하나라도 다르면 contradicted. 원본에 없으면 unverifiable(추측으로 일치 처리하지 않는다).
   우리가 원본 값에서 계산한 값(예: 합친 높이)은 계산을 보이고, 원본 값이 맞으면 confirmed, 계산 근거가 원본에 없으면 unverifiable.
results 의 n 은 위 번호.`,
    { label: `verify:${u + 1}${gs.length > 1 ? `(${gs.length})` : ''}`, phase: 'Verify', schema: VERDICTS }),
  (v, gs, u) => {
    if (!v) return null
    const conf = v.results.filter(r => r.verdict === 'confirmed' && gs[r.n - 1])
    if (!conf.length) return { gs, v, c: null }
    return agent(
      `다른 검증자가 아래 값들을 «원본과 일치»로 판정했다. 너는 그 판정을 깨뜨리려고 본다. 확신이 없으면 refuted=true.
${conf.map(r => { const g = gs[r.n - 1]; return `${r.n}. [${g.kind}/${g.owner}] «${g.value}» (${g.contexts.join(' / ')}) @ ${g.wheres[0]}\n   검증자: 시안 «${r.proof_reading}», 원본 «${r.source_value}», 근거 ${r.source_quote}` }).join('\n')}
시안 파일:
${list(A.proofs)}
원본:
${sources}
${ZOOM}
볼 것: (a) 시안 글자를 더 크게 확대해 0/O, 1/l, 하이픈 종류, 띄어쓰기, 받침까지 같은가 (b) 근거 원본이 최신판인가, 더 새 파일이나 작업방 말로 바뀌지 않았나
(c) 같은 값이 시안 다른 자리에 다르게 적혀 있지 않나 (d) 단위와 기준(어디서 어디까지)이 같은가.
results 의 n 은 위 번호 그대로, final 은 네가 보기에 맞는 판정.`,
      { label: `challenge:${u + 1}`, phase: 'Verify', schema: CHALLENGES }).then(c => ({ gs, v, c }))
  })

const rows = []
let lost = 0
done.forEach((d, u) => {
  if (!d) { lost += units[u].length; return }
  const seenN = new Set()
  for (const r of d.v.results) {
    const g = d.gs[r.n - 1]; if (!g || seenN.has(r.n)) continue
    seenN.add(r.n)
    const c = d.c && d.c.results.find(x => x.n === r.n)
    rows.push({ ...g, verdict: c ? c.final : r.verdict, reading: r.proof_reading, source: r.source_value, quote: r.source_quote,
      note: [r.note, c && c.refuted ? `반박: ${c.reason}` : ''].filter(Boolean).join(' / ') })
  }
  lost += d.gs.length - seenN.size
})
const by = k => rows.filter(r => r.verdict === k)
const bad = by('contradicted'), unk = by('unverifiable'), ok = by('confirmed')
const cell = s => (s || '').replace(/\|/g, '/').replace(/\n/g, ' ')
const line = r => `| ${r.kind}/${r.owner} | ${cell(r.contexts.join(' / '))} | ${cell(r.reading || r.value)} | ${cell(r.source)} | ${cell(r.wheres.slice(0, 2).join(' ; '))}${r.wheres.length > 2 ? ` 외 ${r.wheres.length - 2}곳` : ''} | ${cell(r.quote)} | ${cell(r.note)} |`
const table = rs => rs.length ? `| 종류 | 무엇 | 시안 | 원본 | 시안 자리 | 원본 근거 | 메모 |\n|---|---|---|---|---|---|---|\n${rs.map(line).join('\n')}` : '없음'
const oursNote = A.refs && A.refs.length ? '' : `\n## 우리 쪽 문구 (대조 원본 없음, ${ours.length}개)\n손님 원본과 대조할 값이 아니다. 회사 정보 파일을 refs 로 주면 대조한다. 기호·말투는 forge text 검사로.\n${ours.map(g => `- ${g.value}`).join('\n')}\n`
const md = `# 원본 대조 보고 (${A.job})

대조 ${rows.length}값: 불일치 ${bad.length}, 원본 없음 ${unk.length}, 일치 ${ok.length}${lost ? `, 처리 못 함 ${lost}` : ''}${capped ? `, 상한으로 대조 안 함 ${capped}` : ''}.
판정: ${bad.length ? '고칠 것 있음' : unk.length ? '사람 확인 필요' : '넘김 가능'}
(시안에서 뽑은 자리 ${raw}, 고유 값 ${all.length}, 대조 단위 ${units.length}. 원본 색인: ${INDEX})

시안: ${A.proofs.join(', ')}
원본: ${A.sources.join(', ')}

## 불일치
${table(bad)}

## 원본에서 찾지 못함 (사람 확인)
${table(unk)}

## 일치 (반박 담당까지 통과)
${table(ok)}
${oursNote}`

phase('Report')
await agent(
  `아래 마크다운을 한 글자도 바꾸지 말고 "${A.out}/원본대조_보고.md" 에 그대로 쓴다(폴더가 없으면 만든다). 쓰고 나서 경로만 답한다.\n\n${md}`,
  { label: 'report:write', phase: 'Report', effort: 'low' })

return { job: A.job, spots: raw, unique: all.length, units: units.length, total: rows.length, contradicted: bad.length,
  unverifiable: unk.length, confirmed: ok.length, lost, capped, report: `${A.out}/원본대조_보고.md`,
  contradictions: bad.map(r => ({ context: r.contexts.join(' / '), proof: r.reading || r.value, source: r.source })),
  unverified: unk.map(r => ({ context: r.contexts.join(' / '), proof: r.reading || r.value })) }
