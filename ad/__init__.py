# -*- coding: utf-8 -*-
"""ad — AI 디자이너의 잔손질 도구 (2026-09-27, 고객A 네일 한 바퀴를 모듈로 옮김).

큰 동작(초안 그리기)은 클로드 + 제미나이, **잔손질은 여기** — 같은 걸 매번 새 스크립트로 짜지 않는다.
사람이 짚어 준 디테일은 `check.py` 가 자동으로 잡는다.

    cd SusannaDesigner
    python -m ad vec <png...>            # 그림 → 평평한 SVG (두 줄 부제 안 잃음 · 흰 배경 뺌)
    python -m ad check <svg> --w-mm 1500 # 사람이 짚던 디테일 자동 검사
    python -m ad clean <svg> --w-mm ...  # 겹침 합치기 · 굵게 · 잡티 빼기
    python -m ad respace|squash|stack    # 자간 · 상하 · 심벌+글자
    python -m ad preview3d|gradient|split
    python -m ad sheet <spec.json>       # 까치발 45° 시안 세트 (sim/standoff_sheet.py)
"""
