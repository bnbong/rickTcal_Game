import threading
import time
from typing import Optional

import pygame
from pygame.locals import *

from .classes.sprites import SpriteManager
from .core.config import *
from .core.event_handler import EventHandler
from .core.font_manager import FontManager
from .core.game_state_manager import GameStateManager
from .core.position_manager import PositionManager
from .core.renderer import Renderer
from .core.settings_manager import SettingsManager
from .core.sound_manager import SoundManager
from .entities.erpin import Erpin
from .entities.sherum import Sherum
from .entities.joanne import Joanne
from .scenes import *


class Game:
    """
    게임 전체의 상태와 루프를 관리하는 메인 클래스
    """

    def __init__(self) -> None:
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        pygame.display.set_caption("[트릭컬 리바이브 팬 게임] 선새임 몰래 춤추기")
        self.clock: pygame.time.Clock = pygame.time.Clock()

        self.position_manager: PositionManager = PositionManager()
        self.state_manager: GameStateManager = GameStateManager(self)
        self.event_handler: EventHandler = EventHandler(self)

        self.font_manager: FontManager = FontManager()
        self.font: pygame.font.Font = self.font_manager.get_font()
        self.big_font: pygame.font.Font = self.font_manager.get_font(size_type="title")

        self.settings_manager: SettingsManager = SettingsManager()
        self.sound_manager: SoundManager = SoundManager(self.settings_manager)

        self.previous_state: str = SCENE_TITLE

        # 리소스 로딩 상태 추적
        self.resources_loaded: bool = False
        self.loading_progress: int = 0
        self.loading_message: str = "리소스 로딩 준비 중..."

        # 모든 씬 초기화
        self.scenes: dict = {
            SCENE_TITLE: TitleScene(self),
            SCENE_GAMEOVER: GameOverScene(self),
            SCENE_SETTINGS: SettingsScene(self),
        }

        # 렌더러는 씬 초기화 후에 생성
        self.renderer: Renderer = Renderer(self)

        # 캐릭터 스프라이트
        self.sherum: Optional[Sherum] = None
        self.erpin: Optional[Erpin] = None
        self.joanne: Optional[Joanne] = None

        # 스프라이트 관리자
        self.sprites: Optional[SpriteManager] = None

        # 리소스 준비 상태 플래그
        self.sprites_ready: bool = False
        self.characters_ready: bool = False
        self.sounds_ready: bool = False

        # 백그라운드 로딩 스레드
        self.start_background_loading()

        self.running: bool = True
        self.sound_manager.play_bgm()

        # 초기화 진행 플래그
        self.initializing: bool = False

        # 초기 게임 상태 설정
        self.state_manager.game_state = SCENE_TITLE
        print(f"초기 게임 상태 설정: {self.state_manager.game_state}")

        self.play_start_ticks: Optional[int] = None  # 게임 플레이 시작 시각 (ms)
        self.play_elapsed_time: int = 0  # 누적 경과 시간 (초)

        self._character_data: dict = {"sherum": {}, "erpin": {}}
        self.entities: dict = {}

    def start_background_loading(self) -> None:
        """백그라운드에서 리소스 로딩 시작"""
        loading_thread = threading.Thread(target=self.load_all_resources, daemon=True)
        loading_thread.start()

    def load_all_resources(self) -> None:
        """모든 게임 리소스 로드 (백그라운드 스레드에서 실행)"""
        try:
            self.loading_message = "스프라이트 준비 중..."
            self._prepare_sprite_data()
            self.loading_progress = 30
            time.sleep(0.05)

            self.loading_message = "캐릭터 초기화 중..."
            self._prepare_character_data()
            self.loading_progress = 60
            time.sleep(0.05)

            self.loading_message = "효과음 로드 중..."
            self._prepare_sound_data()
            self.loading_progress = 90
            time.sleep(0.05)

            self.loading_message = "그래픽 로드 중..."
            self._create_sprite_manager()

            self.loading_progress = 100
            self.resources_loaded = True
            self.loading_message = "로딩 완료! 게임을 시작하세요."
            print("모든 리소스 로딩 완료!")
        except Exception as e:
            print(f"리소스 로딩 오류: {e}")
            self.loading_message = "일부 리소스 로딩 실패"
            self.resources_loaded = True

    def _prepare_sprite_data(self) -> None:
        """스프라이트 데이터 준비"""
        try:
            self._sprite_data = {
                "erpin_idle": "erpin_idle.gif",
                "erpin_dance": "erpin_dance_1.gif",
                "erpin_skill": "erpin_skill.gif",
                "sherum_front": "sherum_front.gif",
                "sherum_back": "sherum_back.gif",
                "joanne_idle_1": "joanne_idle_1.gif",
                "joanne_idle_2": "joanne_idle_2.gif",
                "joanne_idle_3": "joanne_idle_3.gif",
                "joanne_dance_1": "joanne_dance_1.gif",
                "joanne_dance_2": "joanne_dance_2.gif",
            }
            self.sprites_ready = True
            print("스프라이트 데이터 준비 완료")
        except Exception as e:
            print(f"스프라이트 준비 오류: {e}")

    def _prepare_character_data(self) -> None:
        """캐릭터 데이터 준비"""
        try:
            self.characters_ready = True
            print("캐릭터 데이터 준비 완료")
        except Exception as e:
            print(f"캐릭터 준비 오류: {e}")

    def _prepare_sound_data(self) -> None:
        """사운드 데이터 준비"""
        try:
            self._sound_list = ["dance", "skill", "game_over", "warning", "turn"]
            for sound in self._sound_list:
                self.sound_manager.load_sfx(sound, f"{sound}.wav")
            self.sounds_ready = True
            print("사운드 로드 완료")
        except Exception as e:
            print(f"사운드 로드 오류: {e}")

    def _create_sprite_manager(self) -> None:
        """스프라이트 매니저 초기화"""
        try:
            self.sprites = SpriteManager(self.position_manager, preload=True)
            print("스프라이트 매니저 초기화 완료")
        except Exception as e:
            print(f"스프라이트 매니저 초기화 오류: {e}")

    def initialize_game_elements(self) -> None:
        """게임 요소 초기화 (메인 스레드에서 실행)"""
        self.initializing = True
        try:
            start_time = time.time()
            self.entities = {"teachers": {}, "students": {}}
            self.sherum = Sherum()
            self.entities["teachers"]["sherum"] = self.sherum
            self.erpin = Erpin()
            self.entities["students"]["erpin"] = self.erpin
            self.joanne = Joanne()
            self.entities["students"]["joanne"] = self.joanne
            self.state_manager.game_state = SCENE_PLAYING
            self.play_start_ticks = pygame.time.get_ticks()  # 게임 시작 시각(ms)
            self.play_elapsed_time = 0
            print(f"게임 요소 초기화 완료: {time.time() - start_time:.3f}초")
        except Exception as e:
            print(f"게임 요소 초기화 오류: {e}")
        finally:
            self.initializing = False

    def update(self) -> None:
        """게임 상태 업데이트"""
        if self.state_manager.game_state == SCENE_TITLE:
            pass
        elif self.state_manager.game_state == SCENE_PLAYING:
            if self.sherum is None or self.erpin is None or self.initializing:
                return
            self.update_gameplay()

    def update_gameplay(self) -> None:
        """게임 플레이 로직 업데이트"""
        current_time = pygame.time.get_ticks() / 1000  # 초 단위
        if self.state_manager.check_game_over_delay(current_time):
            return
        if (
            not self.state_manager.game_over
            and not self.state_manager.game_over_triggered
        ):
            self.update_teachers(current_time)
            self.update_students(current_time)
            self.state_manager.update_score()

    def update_teachers(self, current_time: float) -> None:
        """모든 선생님 엔티티 업데이트"""
        for teacher_id, teacher in self.entities["teachers"].items():
            prev_facing = teacher.facing_away
            teacher.update(current_time * 1000)
            if teacher.facing_away != prev_facing:
                self.state_manager.last_turn_time = current_time
                self.sound_manager.play_sfx("turn")

    def update_students(self, current_time: float) -> None:
        """모든 학생 엔티티 업데이트"""
        active_student = self.erpin
        if self.play_start_ticks is not None:
            play_elapsed_sec = (pygame.time.get_ticks() - self.play_start_ticks) // 1000
        else:
            play_elapsed_sec = 0
        if active_student is not None and self.sherum is not None:
            if active_student.dancing and not self.sherum.facing_away:
                elapsed = current_time - self.state_manager.last_turn_time
                if elapsed > GRACE_PERIOD:
                    self.state_manager.trigger_game_over(current_time, "caught")
            if self.state_manager.update_gauge(active_student.dancing):
                self.state_manager.trigger_game_over(current_time, "no_energy")
        for student_id, student in self.entities["students"].items():
            if student_id == "joanne":
                student.update(
                    current_time * 1000, erpin=self.erpin, game_time=play_elapsed_sec
                )
            else:
                student.update(current_time * 1000)

    def restart_game(self) -> None:
        """게임을 처음부터 다시 시작"""
        self.state_manager.reset_game()
        self.sound_manager.stop_all_sounds()
        for student in self.entities["students"].values():
            student.dancing = False
            student.using_skill = False
        for teacher in self.entities["teachers"].values():
            teacher.facing_away = True
        self.initialize_game_elements()
        self.state_manager.game_state = SCENE_PLAYING
        print("게임 재시작 완료")

    def run(self) -> None:
        """게임 메인 루프"""
        print(f"게임 시작 상태: {self.state_manager.game_state}")
        print(f"사용 가능한 씬: {list(self.scenes.keys())}")
        while self.running:
            self.running = self.event_handler.handle_events()
            self.update()
            self.renderer.render()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
