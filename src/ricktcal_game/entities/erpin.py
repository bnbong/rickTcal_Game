import pygame

from ..core.config import ANIMATION_FRAME_RATE, DEFAULT_ERPIN_POS


class Erpin:
    def __init__(self):
        self.dancing = False
        self.using_skill = False
        self.last_update = 0
        self.animation_frame = 0

    def update_state(self, dancing=None, using_skill=None):
        if dancing is not None:
            self.dancing = dancing
        if using_skill is not None:
            self.using_skill = using_skill
