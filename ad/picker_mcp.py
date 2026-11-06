# -*- coding: utf-8 -*-
"""
디자인 고르기 창의 MCP stdio 서버 — `python -m ad.picker_mcp` (cwd 또는 PYTHONPATH = SusannaDesigner).

도구 여섯: design_open(창 띄우기, 바로 돌아옴) · design_wait(사람이 보낸 것 받기, 최대 ~100초) ·
design_show(뽑은 그림을 창에 띄우기) · design_add_ref(선택지에 레퍼런스 올리기 → 창고 + 열린 창) ·
design_collect(레퍼런스 모음 만들기 — 나무 칸에 안 묶인 조사 묶음) · design_tree(창 없이 선택지 글로 보기).

- 서드파티 SDK 없이 JSON-RPC 2.0 줄 단위(DeGaJa_Agent module_mcp 와 같은 꼴). 🔴 stdout 은 프로토콜 전용 — 로그는 stderr.
- «열기»와 «받기»를 둘로 쪼갠 건 Claude Code 가 2분 넘는 MCP 호출을 백그라운드로 넘기기 때문이다(mcp.md, v2.1.212+).
"""
import json
import sys

from .picker import PICKER

NAME, VERSION, PROTOCOL = 'design-picker', '0.1.0', '2025-06-18'

TOOLS = [
    {
        'name': 'design_open',
        'description': (
            '드로우사인 디자인 나무 «고르기 창»(앱 창)을 사람 화면에 띄운다. 바로 돌아온다 — 고른 것은 design_wait 로 받는다. '
            '로고·간판 디자인을 시작할 때, 사람에게 말로 묻는 대신 이걸 먼저 띄워라. '
            'brief 는 창 맨 위에 보이는 한두 줄(무엇을 위한 고르기인지), focus 는 보여 줄 큰 질문 이름들(비우면 전부), '
            'preselect 는 미리 골라 둘 개념 키(«어떤 로고로 할까?/그림이냐 글자냐?/그림 하나로» 꼴).'),
        'inputSchema': {'type': 'object', 'properties': {
            'brief': {'type': 'string'}, 'store': {'type': 'string', 'description': '상호(가게 이름)'},
            'focus': {'type': 'array', 'items': {'type': 'string'}},
            'preselect': {'type': 'array', 'items': {'type': 'string'}}},
            'additionalProperties': False},
    },
    {
        'name': 'design_wait',
        'description': (
            '창에서 사람이 보낸 것 하나를 받는다. 최대 timeout 초(기본 90, 상한 110) 기다리고, 없으면 status=waiting 으로 돌아온다 — '
            '그러면 다시 부른다. kind=picks 면 고른 개념마다 설명·프롬프트 조각·샘플 프롬프트·그림 파일과 다음 할 일(next)을 준다. '
            'kind=review 면 design_show 로 띄운 그림 중 사람이 고른 파일과 메모(decision: go|again).'),
        'inputSchema': {'type': 'object', 'properties': {
            'session': {'type': 'string'}, 'timeout': {'type': 'integer'}},
            'required': ['session'], 'additionalProperties': False},
    },
    {
        'name': 'design_show',
        'description': '뽑은 그림(로컬 PNG/JPG 경로)을 같은 창에 «받은 그림»으로 띄워 사람이 고르고 메모하게 한다. 그다음 design_wait.',
        'inputSchema': {'type': 'object', 'properties': {
            'session': {'type': 'string'}, 'images': {'type': 'array', 'items': {'type': 'string'}},
            'note': {'type': 'string', 'description': '그림 위에 보일 한 줄(무엇을 어떻게 뽑았나)'}},
            'required': ['session', 'images'], 'additionalProperties': False},
    },
    {
        'name': 'design_add_ref',
        'description': (
            '디자인 나무의 개념(선택지) 하나에 레퍼런스 그림을 올린다 — 로컬 경로 또는 http(s) 주소. '
            '비공개 창고(SusannaDesigner/refs/<개념>/)에 영구로 들어가고(REFS.md 에 «[Claude] 왜» 한 줄), '
            '열린 고르기 창의 그 선택지 그림판에 «Claude 가 올림»으로 곧바로 뜬다. '
            'key 는 «어떤 로고로 할까?/그림이냐 글자냐?/그림 하나로» 꼴(design_tree 로 확인). '
            '🔴 남의 로고·사진이면 own="남의 것" 과 src(출처 URL)를 적어라 — 창고는 비공개지만 그 그림을 --ref 로 넣어 닮게 뽑지는 않는다.'),
        'inputSchema': {'type': 'object', 'properties': {
            'key': {'type': 'string'}, 'images': {'type': 'array', 'items': {'type': 'string'}},
            'src': {'type': 'string', 'description': '출처 URL (주소로 받으면 비워도 그 주소가 들어간다)'},
            'own': {'type': 'string', 'description': '우리 것 | 남의 것'},
            'why': {'type': 'string', 'description': '왜 이 선택지의 레퍼런스인가 — 창에 캡션으로 보인다'}},
            'required': ['key', 'images'], 'additionalProperties': False},
    },
    {
        'name': 'design_collect',
        'description': (
            '«레퍼런스 모음»(나무 칸에 안 묶인 그림 묶음 — 예: 수학 학원 로고 조사)을 만들거나 덧붙인다. '
            '비공개 창고 refs/_모음/<title>/ 에 그림과 items.json 이 쌓이고, 열린 고르기 창 왼쪽 «레퍼런스 모음»에 곧바로 뜬다. '
            '사람은 그 뷰어에서 크게 보고(← → 로 넘기고) 그림마다 고르고 한 줄 메모를 단다 — 보낸 건 design_wait 의 picks 에 key «col:<모음>» 으로 온다. '
            'items 의 image 는 로컬 경로 또는 http(s) 주소, note 는 «어떤 꼴인지» 한 줄, dark 는 흰 로고라 어두운 바탕이 필요할 때. '
            '🔴 남의 로고면 own="남의 것" — 창고는 비공개지만 --ref 로 닮게 뽑지 않는다.'),
        'inputSchema': {'type': 'object', 'properties': {
            'title': {'type': 'string'}, 'why': {'type': 'string'},
            'items': {'type': 'array', 'items': {'type': 'object', 'properties': {
                'image': {'type': 'string'}, 'name': {'type': 'string'}, 'note': {'type': 'string'},
                'site': {'type': 'string'}, 'region': {'type': 'string'}, 'dark': {'type': 'boolean'},
                'tags': {'type': 'array', 'items': {'type': 'string'}}, 'own': {'type': 'string'}},
                'required': ['image']}}},
            'required': ['title', 'items'], 'additionalProperties': False},
    },
    {
        'name': 'design_tree',
        'description': '디자인 나무를 글로 본다(창 없이). 질문·답 이름과 그림 수. 키를 알아야 preselect 할 때 쓴다.',
        'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False},
    },
]


def _call(name, a):
    if name == 'design_open':
        return PICKER.open(a.get('brief', ''), a.get('store', ''), a.get('focus'), a.get('preselect'))
    if name == 'design_wait':
        return PICKER.wait(a['session'], int(a.get('timeout') or 90))
    if name == 'design_show':
        return PICKER.show(a['session'], a.get('images') or [], a.get('note', ''))
    if name == 'design_add_ref':
        return PICKER.add_ref(a['key'], a.get('images') or [], a.get('src', ''), a.get('own', ''), a.get('why', ''))
    if name == 'design_collect':
        return PICKER.cols.add(a['title'], a.get('items') or [], a.get('why', ''))
    if name == 'design_tree':
        return '\n'.join(PICKER.tree.outline())
    raise ValueError(f'모르는 도구: {name}')


def handle(msg):
    method, mid = msg.get('method'), msg.get('id')
    params = msg.get('params') or {}
    if method == 'initialize':
        return {'protocolVersion': params.get('protocolVersion') or PROTOCOL,
                'capabilities': {'tools': {}}, 'serverInfo': {'name': NAME, 'version': VERSION}}
    if method == 'tools/list':
        return {'tools': TOOLS}
    if method == 'tools/call':
        try:
            out = _call(params.get('name', ''), params.get('arguments') or {})
            text = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, indent=2)
            return {'content': [{'type': 'text', 'text': text}]}
        except Exception as e:  # noqa: BLE001 — 도구 실패는 결과로 돌려준다(모델이 읽고 고친다)
            return {'content': [{'type': 'text', 'text': f'[실패] {type(e).__name__}: {e}'}], 'isError': True}
    if method == 'ping':
        return {}
    if mid is None:
        return None
    raise ValueError(f'모르는 메서드: {method}')


def serve():
    stdin = sys.stdin.buffer
    out = sys.stdout.buffer
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line.decode('utf-8'))
        except ValueError:
            continue
        mid = msg.get('id')
        try:
            result = handle(msg)
        except Exception as e:  # noqa: BLE001
            if mid is None:
                continue
            reply = {'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32603, 'message': f'{type(e).__name__}: {e}'}}
        else:
            if result is None:
                continue
            reply = {'jsonrpc': '2.0', 'id': mid, 'result': result}
        out.write((json.dumps(reply, ensure_ascii=False) + '\n').encode('utf-8'))
        out.flush()


if __name__ == '__main__':
    serve()
