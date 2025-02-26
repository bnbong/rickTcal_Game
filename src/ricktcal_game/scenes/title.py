import pygame

from ..core.config import *


class TitleScene:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.font = game.font
        self.big_font = game.big_font

        try:
            self.bg_image = pygame.image.load(
                "src/ricktcal_game/resources/images/main_title.png"
            )
            self.bg_image = pygame.transform.scale(
                self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        except Exception as e:
            print(f"배경 이미지 로드 실패: {e}")
            self.bg_image = None

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            button_rect = pygame.Rect(
                SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50
            )
            if button_rect.collidepoint(event.pos):
                # 로딩 화면 없이 바로 게임 시작
                return "playing"
        return None

    def draw(self):
        self.screen.fill((200, 230, 255))

        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((200, 230, 255))
        self.screen.blit(overlay, (0, 0))

        # 게임 타이틀
        title_text = self.big_font.render("선새임 몰래 춤추기", True, (50, 50, 150))
        self.screen.blit(
            title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150)
        )

        # 시작 버튼
        button_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50
        )
        pygame.draw.rect(self.screen, (100, 150, 200), button_rect)
        pygame.draw.rect(self.screen, (50, 100, 150), button_rect, 3)

        start_text = self.font.render("게임 시작", True, (255, 255, 255))
        self.screen.blit(
            start_text,
            (SCREEN_WIDTH // 2 - start_text.get_width() // 2, SCREEN_HEIGHT // 2 + 60),
        )
