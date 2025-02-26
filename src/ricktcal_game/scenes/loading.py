"""로딩 화면은 필요시 추가 예정"""

import random

import pygame

from ..core.config import *


class LoadingScene:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.font = game.font
        self.progress = 0

        self.tip_text = "스페이스바 - 춤추기 / Z - 스킬"

        # TODO : 배경이미지 추가 혹은 그냥 두기
        try:
            self.bg_image = pygame.image.load(
                "src/ricktcal_game/resources/images/loading_bg.png"
            )
            self.bg_image = pygame.transform.scale(
                self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
        except Exception as e:
            print(f"로딩 배경 이미지 로드 실패: {e}")
            self.bg_image = None

    def update(self, progress):
        self.progress = progress
        if progress >= 100:
            return "playing"
        return None

    def draw(self):
        self.screen.fill((200, 230, 255))

        # TODO : 배경이미지 추가 혹은 그냥 두기
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))

        pygame.draw.rect(
            self.screen,
            (100, 100, 150),
            (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50, 300, 30),
            2,
        )
        pygame.draw.rect(
            self.screen,
            (100, 150, 250),
            (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50, self.progress * 3, 30),
        )

        loading_text = self.font.render(
            f"로딩 중... {int(self.progress)}%", True, (50, 50, 150)
        )
        self.screen.blit(
            loading_text,
            (SCREEN_WIDTH // 2 - loading_text.get_width() // 2, SCREEN_HEIGHT // 2),
        )

        tip = self.font.render(self.tip_text, True, (50, 50, 150))
        self.screen.blit(
            tip, (SCREEN_WIDTH // 2 - tip.get_width() // 2, SCREEN_HEIGHT - 100)
        )
