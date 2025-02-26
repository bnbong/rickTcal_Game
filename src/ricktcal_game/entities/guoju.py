import random

import pygame

# from ..core.config import GYOJU_POS


class GyoJu:
    def __init__(self):
        self.facing_away = False
        self.next_turn_time = 0
        # self.position = GYOJU_POS

    def update(self, current_time):
        if current_time > self.next_turn_time:
            self.facing_away = not self.facing_away
            self.next_turn_time = current_time + random.randint(1000, 3000)
