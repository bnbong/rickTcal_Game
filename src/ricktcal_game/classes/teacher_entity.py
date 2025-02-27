import math
import random

import pygame

from ..core.config import TEACHER_TURN_MAX_DELAY, TEACHER_TURN_MIN_DELAY
from .base_entity import Entity


class TeacherEntity(Entity):
    """선생님 타입 엔티티의 기본 클래스"""

    def __init__(self):
        super().__init__()
        self.entity_type = "teacher"

        # 선생님 공통 속성
        self.facing_away = True

        # 방향 전환 타이밍 관련 변수
        self.last_turn_time = pygame.time.get_ticks()
        self.turn_delay = random.uniform(TEACHER_TURN_MIN_DELAY, TEACHER_TURN_MAX_DELAY)

        # 바운스(튀어오르기) 애니메이션 관련 변수
        self.is_bouncing = False
        self.bounce_start_time = 0
        self.bounce_duration = 300  # 바운스 지속 시간 (밀리초)
        self.bounce_height = 15  # 바운스 최대 높이 (픽셀)
        self.bounce_offset = 0  # 현재 Y축 오프셋

    def update(self, current_time):
        """선생님 상태 업데이트"""
        # 일정 시간마다 방향 전환
        if current_time - self.last_turn_time > self.turn_delay:
            # 방향 전환 시 바운스 애니메이션 시작
            self.facing_away = not self.facing_away
            self.last_turn_time = current_time
            self.turn_delay = random.uniform(
                TEACHER_TURN_MIN_DELAY, TEACHER_TURN_MAX_DELAY
            )

            self.start_bounce(current_time)

        self.update_bounce(current_time)

    def start_bounce(self, current_time):
        """바운스 애니메이션 시작"""
        self.is_bouncing = True
        self.bounce_start_time = current_time
        self.bounce_offset = 0

    def update_bounce(self, current_time):
        """바운스 애니메이션 업데이트"""
        if not self.is_bouncing:
            return

        # 바운스 진행 정도 계산 (0.0 ~ 1.0)
        elapsed = current_time - self.bounce_start_time
        progress = min(1.0, elapsed / self.bounce_duration)

        if progress >= 1.0:
            # 바운스 종료
            self.is_bouncing = False
            self.bounce_offset = 0
            return

        # 사인 함수를 사용하여 자연스러운 바운스 효과 생성
        bounce_factor = math.sin(math.pi * progress)

        # 바운스 높이 계산 (위로 올라가는 것이므로 음수)
        self.bounce_offset = -int(self.bounce_height * bounce_factor)
