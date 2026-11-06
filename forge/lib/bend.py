# -*- coding: utf-8 -*-
"""판을 «통으로 길게 따서» ㄴ자로 굽힐 때의 기하(아크릴·금속 판). 단위 mm.
처음 쓰인 곳: jobs/2026-10_고객K 5·6차. 중립축 k 0.45 는 열 굽힘 아크릴의 흔한 가정값(추정) — 공장 시험 굽힘으로 맞춘다.
"""
import math


def bend(t, r, angle=90.0, k=0.45):
    """t 두께, r 안쪽 반지름, angle 굽힘 각. 앞면이 굽힘 바깥이면 그 위 부재가 R(=r+t)만큼 올라간다.
    ba 는 굽힘 부분을 펼친 길이(전개도에 넣는 값)."""
    R = r + t
    return dict(t=t, r=r, R=R, rise=R, ba=math.radians(angle) * (r + k * t), angle=angle)


def lean(height, angle):
    """굽힘 각이 angle 일 때 높이 height 꼭대기가 앞뒤로 기우는 양(+ 뒤로). 1도면 808 높이에서 14."""
    return height * math.tan(math.radians(angle - 90.0))
