import pygame
from pygame.locals import *

from .config import (
    SCENE_GAMEOVER,
    SCENE_LOADING,
    SCENE_PLAYING,
    SCENE_SETTINGS,
    SCENE_TITLE,
)


class EventHandler:
    """게임 이벤트 처리를 담당하는 클래스"""

    def __init__(self, game):
        self.game = game
        self.dance_state = False  # 춤 상태 추적용 변수

    def handle_events(self):
        """모든 게임 이벤트 처리"""
        for event in pygame.event.get():
            if event.type == QUIT:
                return False  # 게임 종료

            # ESC 키로 설정 화면 열기/닫기
            if (
                event.type == KEYDOWN
                and event.key == K_ESCAPE
                and self.game.state_manager.game_state != SCENE_SETTINGS
                and self.game.state_manager.game_state != SCENE_GAMEOVER
            ):
                self.game.previous_state = self.game.state_manager.game_state
                self.game.state_manager.game_state = SCENE_SETTINGS
                self.game.sound_manager.play_sfx("click")
                continue

            if self.game.state_manager.game_state == SCENE_TITLE:
                self.handle_title_events(event)
            elif self.game.state_manager.game_state == SCENE_PLAYING:
                self.handle_playing_events(event)
            elif self.game.state_manager.game_state == SCENE_GAMEOVER:
                self.handle_gameover_events(event)
            elif self.game.state_manager.game_state == SCENE_SETTINGS:
                self.handle_settings_events(event)

            # 게임 초기화 타이머 이벤트 (지연 초기화용)
            if event.type == pygame.USEREVENT + 10:
                self.game.initialize_game_elements()
                # 초기화 완료 후 게임 상태 변경
                self.game.state_manager.game_state = SCENE_PLAYING
                continue

        return True  # 계속 실행

    def handle_title_events(self, event):
        """타이틀 화면 이벤트 처리"""
        # 리소스 로딩이 완료되지 않았으면 게임 시작 무시
        if not self.game.resources_loaded and event.type == pygame.MOUSEBUTTONDOWN:
            return None

        # 리소스 로딩이 완료된 경우 정상 처리
        next_state = self.game.scenes[SCENE_TITLE].handle_events(event)
        if next_state:
            return next_state
        return None

    def handle_playing_events(self, event):
        """게임 플레이 중 이벤트 처리"""
        # 스킬 사용
        if event.type == KEYDOWN:
            if event.key == K_z and self.game.state_manager.skill_charges > 0:
                if self.game.state_manager.use_skill():
                    self.game.erpin.update_state(using_skill=True)
                    pygame.time.set_timer(USEREVENT + 1, 500, loops=1)
                    self.game.sound_manager.play_sfx("skill")

            # 춤추기 시작
            elif event.key == K_SPACE:
                self.game.erpin.update_state(dancing=True)
                self.game.sound_manager.play_sfx("dance")

        # 춤 멈추기
        if event.type == KEYUP and event.key == K_SPACE:
            self.game.erpin.update_state(dancing=False)
            self.game.sound_manager.stop_sfx("dance")

        # 스킬 효과 종료
        if event.type == USEREVENT + 1:
            self.game.erpin.update_state(using_skill=False)

    def handle_gameover_events(self, event):
        """게임 오버 화면 이벤트 처리"""
        next_state = self.game.scenes["game_over"].handle_events(event)
        if next_state:
            if next_state == "restart":
                # 게임 재시작
                self.game.restart_game()
            else:
                # 메뉴로 돌아가기
                self.game.state_manager.reset_game()
                self.game.state_manager.game_state = next_state

    def handle_settings_events(self, event):
        """설정 화면 이벤트 처리"""
        next_state = self.game.scenes["settings"].handle_events(event)
        if next_state:
            self.game.state_manager.game_state = next_state

    def handle_input(self, key_state):
        """매 프레임 키보드 입력 상태 처리"""
        if self.game.state_manager.game_state != "playing":
            return

        space_pressed = key_state[pygame.K_SPACE]

        if self.dance_state != space_pressed:
            self.dance_state = space_pressed
            self.game.erpin.update_state(dancing=space_pressed)

            if space_pressed:
                self.game.sound_manager.play_sfx("dance")
            else:
                self.game.sound_manager.stop_sfx("dance")
