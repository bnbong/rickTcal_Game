import time

import pygame

from ..core.config import *


class GameStateManager:
    """게임 상태와 관련된 로직을 관리하는 클래스"""

    def __init__(self, game=None):
        self.game = game
        self.game_state = SCENE_TITLE

        self.game_over = False
        self.game_over_triggered = False
        self.game_over_time = 0
        self.game_over_reason = None
        self.show_exclamation = False  # 느낌표 표시 상태
        self.score = 0
        self.gauge = INITIAL_GAUGE
        self.skill_charges = INITIAL_SKILL_CHARGES
        self.last_turn_time = 0
        self.prev_facing_state = False

        # 로딩 관련 상태
        self.loading_start_time = 0
        self.loading_progress = 0

    def reset_game(self):
        """게임 상태를 초기값으로 리셋"""
        self.game_state = SCENE_TITLE
        self.game_over = False
        self.game_over_triggered = False
        self.game_over_time = 0
        self.game_over_reason = None
        self.show_exclamation = False  # 느낌표 표시 상태 초기화
        self.score = 0
        self.gauge = INITIAL_GAUGE
        self.skill_charges = INITIAL_SKILL_CHARGES
        self.last_turn_time = 0
        self.prev_facing_state = False

    def start_loading(self):
        """로딩 과정 시작"""
        self.loading_start_time = time.time()
        self.loading_progress = 0
        self.game_state = SCENE_LOADING

    def update_loading(self):
        """로딩 진행 상태 업데이트"""
        elapsed = time.time() - self.loading_start_time
        self.loading_progress = min(100, elapsed * (100 / LOADING_DURATION))

        # 로딩 완료 확인
        if self.loading_progress >= 100:
            return True
        return False

    def trigger_game_over(self, current_time, reason="caught"):
        """게임 오버 상태를 트리거"""
        if not self.game_over and not self.game_over_triggered:
            self.game_over_triggered = True
            self.game_over_time = current_time
            self.game_over_reason = reason
            self.show_exclamation = reason == "caught"

            # 다른 모든 효과음 중지
            if hasattr(self.game, "sound_manager"):
                self.game.sound_manager.stop_all_sounds(except_sounds=["game_over"])
                self.game.sound_manager.play_sfx("game_over")

    def check_game_over_delay(self, current_time):
        """게임 오버 지연 시간이 지났는지 확인"""
        if self.game_over_triggered and not self.game_over:
            if current_time - self.game_over_time >= GAME_OVER_DELAY:
                self.game_over = True
                self.game_state = "game_over"
                return True
        return False

    def update_gauge(self, is_dancing):
        """게이지 업데이트 및 게임 오버 체크"""
        # TODO : 게이지 고갈 경고음 추가 / 제거 여부 결정
        current_time = pygame.time.get_ticks() / 1000  # 초 단위

        # 에너지 고갈 경고음 (20% 이하일 때)
        if (
            self.gauge <= 20
            and self.gauge > 0
            and is_dancing
            and int(current_time) % 2 == 0
        ):
            # 저에너지 경고음 효과 (0.5초 간격)
            if (
                hasattr(self, "game")
                and hasattr(self.game, "sound_manager")
                and not hasattr(self, "_last_warning")
            ):
                self.game.sound_manager.play_sfx("warning")
                self._last_warning = current_time

        if is_dancing:
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

    def update_gameplay(self):
        """게임 플레이 로직 업데이트"""
        # TODO : 선생님 방향 전환 sfx 추가 여부 결정
        current_time = pygame.time.get_ticks() / 1000  # 초 단위

        # 게임 오버 지연 체크
        if self.check_game_over_delay(current_time):
            return

        if not self.game_over and not self.game_over_triggered:
            # 선생님(들) 업데이트
            for teacher_name, teacher in self.game.entities["teachers"].items():
                prev_state = teacher.facing_away
                teacher.update(current_time * 1000)

                # 방향 전환 감지 및 효과음 재생
                if teacher.facing_away != prev_state:
                    self.last_turn_time = current_time
                    # 선생님 방향 전환 효과음 재생
                    if hasattr(self.game, "sound_manager"):
                        self.game.sound_manager.play_sfx("turn")

            # 모든 학생 상태 확인
            active_student = self.game.erpin  # 현재 활성화된 학생

            # 게임 오버 조건 체크 (춤추다 들킨 경우)
            if active_student.dancing and not self.game.sherum.facing_away:
                elapsed = current_time - self.last_turn_time
                if elapsed > GRACE_PERIOD:
                    self.trigger_game_over(current_time, "caught")

            # 게이지 업데이트 및 게임 오버 체크
            if self.update_gauge(active_student.dancing):
                self.trigger_game_over(current_time, "no_energy")

            # 점수 업데이트
            self.update_score()

    def show_warning(self, text):
        """경고 메시지 표시"""
        if hasattr(self.game, "font_manager"):
            warning_text = self.game.font_manager.render_text(
                text, "korean", "normal", (255, 50, 50)
            )
        else:
            warning_text = self.game.font.render(text, True, (255, 50, 50))
