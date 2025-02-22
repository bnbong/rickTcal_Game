import pygame
from ..core.config import ERPIN_POS


class Erpin:
    def __init__(self):
        self.dancing = False
        self.position = ERPIN_POS

    def update_dance_state(self, dancing):
        self.dancing = dancing
