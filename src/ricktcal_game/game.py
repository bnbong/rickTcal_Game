import time

import pygame
from pygame.locals import *

from .classes.sprites import SpriteManager
from .core.config import *
from .core.event_handler import EventHandler
from .core.game_state_manager import GameStateManager
from .core.position_manager import PositionManager
from .core.renderer import Renderer
from .entities.erpin import Erpin
from .entities.sherum import Sherum
from .scenes import *


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("[트릭컬 리바이브 팬 게임] 선새임 몰래 춤추기")
        self.clock = pygame.time.Clock()

        self.position_manager = PositionManager()
        self.state_manager = GameStateManager()
        self.event_handler = EventHandler(self)
        self.renderer = Renderer(self)

        self.initialize_fonts()

        self.scenes = {
            SCENE_TITLE: TitleScene(self),
            SCENE_LOADING: LoadingScene(self),
            SCENE_GAMEOVER: GameOverScene(self),
        }

        self.sherum = None
        self.erpin = None
        self.sprites = None

        self.running = True

    def initialize_fonts(self):
        """한글 폰트 초기화"""
        try:
            self.font_path = pygame.font.match_font(
                [
                    "malgun gothic",
                    "malgungothic",
                    "gulim",
                    "gungsuh",
                    "batang",
                    "applegothic",
                ]
            )
            if not self.font_path:
                self.font_path = pygame.font.get_default_font()

            self.font = pygame.font.Font(self.font_path, 36)
            self.big_font = pygame.font.Font(self.font_path, 72)
            print(f"사용 중인 폰트: {self.font_path}")
        except Exception as e:
            print(f"폰트 로딩 오류: {e}")
            # 폴백: 기본 폰트 사용
            self.font = pygame.font.Font(None, 36)
            self.big_font = pygame.font.Font(None, 72)

    def initialize_game_elements(self):
        """게임 요소 초기화"""
        self.sherum = Sherum()
        self.erpin = Erpin()
        self.sprites = SpriteManager(self.position_manager)
        self.state_manager.game_state = SCENE_PLAYING

    def update(self):
        """게임 상태 업데이트"""
        # 타이틀 화면에서 바로 게임 화면으로 전환
        if self.state_manager.game_state == "menu":
            pass  # 필요한 경우 타이틀 화면 업데이트 코드 추가
        elif self.state_manager.game_state == "playing":
            # 게임 요소가 초기화되지 않았으면 초기화
            if self.sherum is None or self.erpin is None:
                self.initialize_game_elements()
            self.update_gameplay()

    def update_gameplay(self):
        """게임 플레이 로직 업데이트"""
        current_time = pygame.time.get_ticks() / 1000  # 초 단위

        # 게임 오버 지연 체크
        if self.state_manager.check_game_over_delay(current_time):
            return

        if (
            not self.state_manager.game_over
            and not self.state_manager.game_over_triggered
        ):
            prev_state = self.sherum.facing_away
            self.sherum.update(current_time * 1000)

            if self.sherum.facing_away != prev_state:
                self.state_manager.last_turn_time = current_time

            # 게임 오버 조건 체크 (춤추다 들킨 경우)
            if self.erpin.dancing and not self.sherum.facing_away:
                elapsed = current_time - self.state_manager.last_turn_time
                if elapsed > GRACE_PERIOD:
                    self.state_manager.trigger_game_over(current_time, "caught")

            # 게이지 업데이트 및 게임 오버 체크 (게이지 소진 경우)
            if self.state_manager.update_gauge(self.erpin.dancing):
                self.state_manager.trigger_game_over(current_time, "no_energy")

            self.state_manager.update_score()

    def run(self):
        """게임 메인 루프"""
        while self.running:
            # 이벤트 처리
            self.running = self.event_handler.handle_events()

            # 게임 상태 업데이트
            self.update()

            # 화면 렌더링
            self.renderer.render()

            # 프레임 레이트 제한
            self.clock.tick(FPS)

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
