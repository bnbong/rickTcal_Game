import time

import pygame

from ..core.config import *


class GameStateManager:
    """게임 상태와 관련된 로직을 관리하는 클래스"""

    def __init__(self):
        # 게임 상태 초기화
        self.game_state = INITIAL_GAME_STATE
        self.game_over = False
        self.game_over_triggered = False
        self.game_over_time = 0
        self.game_over_reason = None
        self.show_exclamation = False  # 느낌표 표시 상태
        self.score = INITIAL_SCORE
        self.gauge = INITIAL_GAUGE
        self.skill_charges = INITIAL_SKILL_CHARGES
        self.last_turn_time = 0
        self.prev_facing_state = False

        # 로딩 관련 상태
        self.loading_start_time = 0
        self.loading_progress = 0

    def reset_game(self):
        """게임 상태를 초기값으로 리셋"""
        self.game_state = INITIAL_GAME_STATE
        self.game_over = False
        self.game_over_triggered = False
        self.game_over_time = 0
        self.game_over_reason = None
        self.show_exclamation = False  # 느낌표 표시 상태 초기화
        self.score = INITIAL_SCORE
        self.gauge = INITIAL_GAUGE
        self.skill_charges = INITIAL_SKILL_CHARGES
        self.last_turn_time = 0
        self.prev_facing_state = False

    def start_loading(self):
        """로딩 과정 시작"""
        """로딩 화면은 필요시 추가 예정"""
        self.loading_start_time = time.time()
        self.loading_progress = 0
        self.game_state = "loading"

    def update_loading(self):
        """로딩 진행 상태 업데이트"""
        """로딩 화면은 필요시 추가 예정"""
        elapsed = time.time() - self.loading_start_time
        self.loading_progress = min(100, elapsed * (100 / LOADING_DURATION))

        # 로딩 완료 확인
        if self.loading_progress >= 100:
            return True
        return False

    def trigger_game_over(self, current_time, reason=None):
        """게임 오버 트리거 (지연 후 실제 게임 오버로 전환)"""
        if not self.game_over_triggered:
            self.game_over_triggered = True
            self.game_over_time = current_time
            self.game_over_reason = reason

            # 춤추다 들킨 경우에만 느낌표 표시
            self.show_exclamation = reason == "caught"

    def check_game_over_delay(self, current_time):
        """게임 오버 지연 시간이 지났는지 확인"""
        if self.game_over_triggered and not self.game_over:
            if current_time - self.game_over_time >= GAME_OVER_DELAY:
                self.game_over = True
                self.game_state = "game_over"
                return True
        return False

    def update_gauge(self, dancing):
        """게이지 상태 업데이트"""
        if dancing:
            self.gauge = min(100, self.gauge + GAUGE_INCREASE)
        else:
            self.gauge = max(0, self.gauge - GAUGE_DECREASE)

        # 게이지 소진 시 게임 오버
        if self.gauge <= 0:
            return True
        return False

    def use_skill(self):
        """스킬 사용"""
        if self.skill_charges > 0:
            self.gauge = min(100, self.gauge + SKILL_CHARGE)
            self.skill_charges -= 1
            return True
        return False

    def update_score(self):
        """점수 업데이트"""
        self.score += 0.1
