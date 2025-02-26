import pygame
from pygame.locals import *


class EventHandler:
    """게임 이벤트 처리를 담당하는 클래스"""

    def __init__(self, game):
        self.game = game

    def handle_events(self):
        """모든 게임 이벤트 처리"""
        for event in pygame.event.get():
            if event.type == QUIT:
                return False  # 게임 종료

            # 현재 게임 상태에 따라 이벤트 처리
            if self.game.state_manager.game_state == "menu":
                self.handle_title_events(event)
            elif self.game.state_manager.game_state == "playing":
                self.handle_playing_events(event)
            elif self.game.state_manager.game_state == "game_over":
                self.handle_gameover_events(event)

        return True  # 계속 실행

    def handle_title_events(self, event):
        """타이틀 화면 이벤트 처리"""
        next_state = self.game.scenes["menu"].handle_events(event)
        if next_state:
            # 로딩 화면 대신 바로 게임 상태로 설정
            self.game.state_manager.game_state = next_state
            if next_state == "playing":
                self.game.initialize_game_elements()

    def handle_playing_events(self, event):
        """게임 플레이 중 이벤트 처리"""
        # 스킬 사용
        if event.type == KEYDOWN:
            if event.key == K_z and self.game.state_manager.skill_charges > 0:
                if self.game.state_manager.use_skill():
                    self.game.erpin.update_state(using_skill=True)
                    pygame.time.set_timer(USEREVENT + 1, 500, loops=1)

            # 춤추기
            elif event.key == K_SPACE:
                self.game.erpin.update_state(dancing=True)

        # 춤 멈추기
        if event.type == KEYUP and event.key == K_SPACE:
            self.game.erpin.update_state(dancing=False)

        # 스킬 효과 종료
        if event.type == USEREVENT + 1:
            self.game.erpin.update_state(using_skill=False)

    def handle_gameover_events(self, event):
        """게임 오버 화면 이벤트 처리"""
        next_state = self.game.scenes["game_over"].handle_events(event)
        if next_state:
            self.game.state_manager.reset_game()
            self.game.state_manager.game_state = next_state
