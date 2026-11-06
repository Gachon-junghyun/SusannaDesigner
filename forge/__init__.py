# -*- coding: utf-8 -*-
"""forge(공방) — 수산나 디자이너 하네스의 «빨라지는» 엔진. 쓰는 법은 protocols/forge.md.

공개 API
- 파이프라인: run · status · adopt · init           (_pipe)
- 검사:      zoom_sheet · diff_sheet               (_gates, 파이프라인 단계의 gates 로도 돈다)
- 방법 대장:  trial · show                          (_methods)
- 변경 시계:  clock_start · clock_stop · report     (_clock)
- 공용 부품:  forge.lib.geom2d · bend · pdfphone · blshade
"""
from ._pipe import run, status, adopt, init, job_dir
from ._gates import zoom_sheet, diff_sheet
from ._methods import trial, show
from ._clock import start as clock_start, stop as clock_stop, report
