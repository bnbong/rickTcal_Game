import os

import pygame
from PIL import Image, ImageSequence

from ..core.config import *


class GameOverScene:
    """게임 오버 화면 클래스"""

    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.bg_image = None
        self.gameover_animations = {}
        self.current_frame = 0
        self.last_update = 0
        self.frame_rate = 100  # 밀리초 단위 (낮을수록 빠름)

        self.load_animations()

        self.load_background()

        button_width = 200
        button_height = 50

        # 재시작 버튼
        self.restart_button_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - button_width // 2, 400, button_width, button_height
        )

        # 타이틀로 돌아가기 버튼
        self.menu_button_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - button_width // 2, 470, button_width, button_height
        )

    def load_animations(self):
        """게임 오버 애니메이션 로드"""
        try:
            sherum_go_path = (
                "src/ricktcal_game/resources/animations/sherum_gameover.gif"
            )

            if os.path.exists(sherum_go_path):
                sherum_frames = []
                pil_img = Image.open(sherum_go_path)

                for frame in ImageSequence.Iterator(pil_img):
                    frame_copy = frame.convert("RGBA")
                    frame_data = frame_copy.tobytes()
                    size = frame_copy.size
                    mode = frame_copy.mode

                    py_img = pygame.image.frombuffer(
                        frame_data, size, mode
                    ).convert_alpha()
                    py_img = pygame.transform.scale(py_img, (300, 300))  # 크기 조정
                    sherum_frames.append(py_img)

                self.gameover_animations["sherum"] = sherum_frames
                print("선생님 게임오버 애니메이션 로드 완료")
            else:
                print("선생님 게임오버 애니메이션 파일 없음")
                # 더미 프레임 생성
                dummy = pygame.Surface((300, 300), pygame.SRCALPHA)
                dummy.fill((200, 0, 0, 128))
                self.gameover_animations["sherum"] = [dummy]
        except Exception as e:
            print(f"게임오버 애니메이션 로드 오류: {e}")

    def load_background(self):
        """배경 이미지 로드"""
        try:
            # 기본 게임오버 배경(게이지 소진 시)
            bg_path = "src/ricktcal_game/resources/images/gameover_bg.png"
            if os.path.exists(bg_path):
                self.bg_image = pygame.image.load(bg_path).convert_alpha()
                self.bg_image = pygame.transform.scale(
                    self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT)
                )
                print("게임 오버 배경 이미지 로드 완료")
            else:
                print("게임 오버 배경 이미지 파일 없음")
        except Exception as e:
            print(f"배경 이미지 로드 오류: {e}")

    def draw(self, score=0):
        """게임 오버 화면 그리기"""
        self.screen.fill((50, 50, 80))

        now = pygame.time.get_ticks()

        gameover_reason = self.game.state_manager.game_over_reason

        if gameover_reason == "caught":
            # 춤추다가 선생님한테 걸린 경우
            self.draw_caught_screen(now, score)
        else:
            # 게이지가 다 떨어진 경우 (gameover_reason == "no_energy")
            self.draw_no_energy_screen(score)

        # 버튼 그리기 (공통)
        self.draw_buttons()

    def draw_caught_screen(self, now, score):
        """선생님에게 걸린 게임오버 화면"""
        # 배경 이미지 있으면 표시
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))

        if "sherum" in self.gameover_animations:
            frames = self.gameover_animations["sherum"]

            if now - self.last_update > self.frame_rate:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(frames)

            frame = frames[self.current_frame]
            frame_rect = frame.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
            )
            self.screen.blit(frame, frame_rect)

        # 게임 오버 메시지
        if hasattr(self.game, "font_manager"):
            gameover_text = self.game.font_manager.render_text(
                "여왕님.. 뭐하시는 건가요?", "korean", "normal", (255, 100, 100)
            )
            score_text = self.game.font_manager.render_text(
                f"점수: {int(score)}", "korean", "normal", (255, 255, 255)
            )
        else:
            medium_font = pygame.font.Font(None, 36)
            gameover_text = medium_font.render("What the Hell?", True, (255, 100, 100))
            score_text = self.game.font.render(
                f"Score: {int(score)}", True, (255, 255, 255)
            )

        self.screen.blit(
            gameover_text, (SCREEN_WIDTH // 2 - gameover_text.get_width() // 2, 50)
        )
        self.screen.blit(
            score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 150)
        )

    def draw_no_energy_screen(self, score):
        """게이지가 다 떨어진 게임오버 화면"""
        # 배경 이미지 있으면 표시
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))

        # 게임 오버 메시지
        if hasattr(self.game, "font_manager"):
            gameover_text = self.game.font_manager.render_text(
                "당이 다 떨어진 에르핀은 교실을 뛰쳐나갔다...",
                "korean",
                "normal",
                (255, 100, 100),
            )
            score_text = self.game.font_manager.render_text(
                f"점수: {int(score)}", "korean", "normal", (255, 255, 255)
            )
        else:
            medium_font = pygame.font.Font(None, 36)
            gameover_text = medium_font.render(
                "당이 다 떨어진 에르핀은 교실을 뛰쳐나갔다...", True, (255, 100, 100)
            )
            score_text = self.game.font.render(
                f"점수: {int(score)}", True, (255, 255, 255)
            )

        self.screen.blit(
            gameover_text, (SCREEN_WIDTH // 2 - gameover_text.get_width() // 2, 100)
        )
        self.screen.blit(
            score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 200)
        )

    def draw_buttons(self):
        """버튼 그리기"""
        mouse_pos = pygame.mouse.get_pos()

        # 재시작 버튼
        if hasattr(self.game, "font_manager"):
            restart_text = self.game.font_manager.render_text(
                "다시 시작", "korean", "normal", (255, 255, 255)
            )
            menu_text = self.game.font_manager.render_text(
                "타이틀로", "korean", "normal", (255, 255, 255)
            )
        else:
            restart_text = self.game.font.render("다시 시작", True, (255, 255, 255))
            menu_text = self.game.font.render("타이틀로", True, (255, 255, 255))

        # 버튼 배경 색상
        restart_color = (
            (100, 100, 250)
            if self.restart_button_rect.collidepoint(mouse_pos)
            else (70, 70, 200)
        )
        menu_color = (
            (100, 100, 250)
            if self.menu_button_rect.collidepoint(mouse_pos)
            else (70, 70, 200)
        )

        # 버튼 그리기
        pygame.draw.rect(
            self.screen, restart_color, self.restart_button_rect, border_radius=5
        )
        pygame.draw.rect(
            self.screen, menu_color, self.menu_button_rect, border_radius=5
        )

        self.screen.blit(
            restart_text,
            (
                self.restart_button_rect.centerx - restart_text.get_width() // 2,
                self.restart_button_rect.centery - restart_text.get_height() // 2,
            ),
        )

        self.screen.blit(
            menu_text,
            (
                self.menu_button_rect.centerx - menu_text.get_width() // 2,
                self.menu_button_rect.centery - menu_text.get_height() // 2,
            ),
        )

    def handle_events(self, event):
        """이벤트 처리"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.restart_button_rect.collidepoint(event.pos):
                self.game.sound_manager.play_sfx("click")
                return "restart"

            elif self.menu_button_rect.collidepoint(event.pos):
                self.game.sound_manager.play_sfx("click")
                return "title"

        return None
