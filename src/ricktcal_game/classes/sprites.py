import pygame
from ..core.config import *


class SpriteManager:
    def __init__(self):
        # 임시 도형으로 초기화 (이미지로 교체 가능)
        self.gyoju_image = pygame.Surface((50, 100))
        self.erpin_image = pygame.Surface((50, 100))

    def draw_gyoju(self, screen, facing_away):
        color = (255, 0, 0) if facing_away else (0, 255, 0)
        self.gyoju_image.fill(color)
        screen.blit(self.gyoju_image, GYOJU_POS)

    def draw_erpin(self, screen, dancing):
        color = (0, 0, 255) if dancing else (200, 200, 200)
        self.erpin_image.fill(color)
        screen.blit(self.erpin_image, ERPIN_POS)
