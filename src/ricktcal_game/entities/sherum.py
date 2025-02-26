import random

import pygame

from ..core.config import TEACHER_TURN_MAX_DELAY, TEACHER_TURN_MIN_DELAY


class Sherum:
    """선생님 엔티티 클래스"""

    def __init__(self):
        # 기본 상태 초기화
        self.facing_away = True
        self.last_update = 0
        self.animation_frame = 0

        # 방향 전환 타이밍 관련 변수
        self.last_turn_time = pygame.time.get_ticks()
        self.turn_delay = random.uniform(TEACHER_TURN_MIN_DELAY, TEACHER_TURN_MAX_DELAY)

    def update(self, current_time):
        """선생님 상태 업데이트"""
        # 일정 시간마다 방향 전환
        if current_time - self.last_turn_time > self.turn_delay:
            self.facing_away = not self.facing_away
            self.last_turn_time = current_time
            self.turn_delay = random.uniform(
                TEACHER_TURN_MIN_DELAY, TEACHER_TURN_MAX_DELAY
            )
