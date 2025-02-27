import pygame

from ..core.config import *


class TitleScene:
    """타이틀 화면 클래스"""

    def __init__(self, game):
        self.game = game
        self.screen = game.screen

        # 폰트 관리자 사용
        if hasattr(game, "font_manager"):
            self.font_manager = game.font_manager
            self.title_font = self.font_manager.get_font("korean", "title")
            self.font = self.font_manager.get_font("korean", "normal")
            self.small_font = self.font_manager.get_font(
                "korean", "small"
            )  # 툴팁용 작은 폰트
        else:
            self.title_font = game.big_font
            self.font = game.font
            self.small_font = pygame.font.Font(None, 24)  # 툴팁용 작은 폰트

        button_width = 200
        button_height = 50

        self.start_button_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - button_width // 2, 450, button_width, button_height
        )

        self.bg_image = None
        self.load_background()

    def load_background(self):
        """배경 이미지 로드"""
        try:
            bg_path = "src/ricktcal_game/resources/images/main_title.png"
            import os

            if os.path.exists(bg_path):
                self.bg_image = pygame.image.load(bg_path).convert_alpha()
                self.bg_image = pygame.transform.scale(
                    self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT)
                )
                print("타이틀 배경 이미지 로드 완료")
            else:
                print("타이틀 배경 이미지 파일이 없습니다")
        except Exception as e:
            print(f"배경 이미지 로드 오류: {e}")

    def draw(self):
        """타이틀 화면 그리기"""
        self.screen.fill((50, 70, 100))

        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))

        if hasattr(self, "font_manager"):
            title_text = self.font_manager.render_text(
                "선새임 몰래 춤추기", "korean", "title", (255, 255, 255)
            )
        else:
            title_text = self.title_font.render(
                "선새임 몰래 춤추기", True, (255, 255, 255)
            )

        self.screen.blit(
            title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150)
        )

        self.draw_buttons()

        if not self.game.resources_loaded:
            loading_text = self.font.render(
                f"리소스 로딩 중... {self.game.loading_progress:.0f}%",
                True,
                (255, 255, 255),
            )

            loading_y = self.start_button_rect.bottom + 20  # 시작 버튼 아래 20픽셀 여백
            self.screen.blit(
                loading_text,
                (SCREEN_WIDTH // 2 - loading_text.get_width() // 2, loading_y),
            )

    def draw_buttons(self):
        """버튼 그리기 (시작 버튼만)"""
        mouse_pos = pygame.mouse.get_pos()

        resources_loading = not self.game.resources_loaded

        if hasattr(self, "font_manager"):
            start_text = self.font_manager.render_text(
                "게임 시작", "korean", "normal", (255, 255, 255)
            )
        else:
            start_text = self.font.render("게임 시작", True, (255, 255, 255))

        # 시작 버튼 - 로딩 중일 때는 비활성화
        if resources_loading:
            button_color = (100, 100, 150)  # 비활성화 색상
        else:
            button_color = (
                (100, 100, 250)
                if self.start_button_rect.collidepoint(mouse_pos)
                else (70, 70, 200)
            )

        pygame.draw.rect(
            self.screen, button_color, self.start_button_rect, border_radius=5
        )

        self.screen.blit(
            start_text,
            (
                self.start_button_rect.centerx - start_text.get_width() // 2,
                self.start_button_rect.centery - start_text.get_height() // 2,
            ),
        )

        # 설정 툴팁 (좌측 하단)
        if hasattr(self, "font_manager"):
            tooltip_text = self.font_manager.render_text(
                "설정 - ESC", "korean", "small", (200, 200, 255)
            )
        else:
            tooltip_text = self.small_font.render("설정 - ESC", True, (200, 200, 255))

        self.screen.blit(tooltip_text, (20, SCREEN_HEIGHT - 30))

    def handle_events(self, event):
        """이벤트 처리"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.start_button_rect.collidepoint(event.pos):
                # 리소스가 로드되었을 때만 게임 시작
                if self.game.resources_loaded:
                    self.game.sound_manager.play_sfx("click")
                    self.game.initialize_game_elements()
                    return "playing"
                else:
                    return None

        return None
