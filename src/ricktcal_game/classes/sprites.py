import io
from pathlib import Path

import pygame
from PIL import Image, ImageSequence

from ..core.config import *


class SpriteManager:
    def __init__(self, position_manager):
        self.position_manager = position_manager

        self.erpin_idle = self.load_animation_frames("erpin_idle.gif")
        self.erpin_dance = self.load_animation_frames("erpin_dance_1.gif")
        self.erpin_skill = self.load_animation_frames("erpin_skill.gif")

        self.sherum_front = self.load_animation_frames(
            "sherum_front.gif", flip=True, is_teacher=True
        )
        self.sherum_back = self.load_animation_frames(
            "sherum_back.gif", is_teacher=True
        )

    def load_animation_frames(self, filename, flip=False, is_teacher=False):
        try:
            gif_path = f"src/ricktcal_game/resources/animations/{filename}"

            pil_img = Image.open(gif_path)
            frames = []

            for frame in ImageSequence.Iterator(pil_img):
                frame_copy = frame.convert("RGBA")
                pygame_image = pygame.image.fromstring(
                    frame_copy.tobytes(), frame_copy.size, frame_copy.mode
                )

                # 크기 조정 (선생님은 더 큰 크기 적용)
                if is_teacher:
                    pygame_image = pygame.transform.scale(
                        pygame_image, (SHERUM_WIDTH, SHERUM_HEIGHT)
                    )
                else:
                    pygame_image = pygame.transform.scale(
                        pygame_image, (ENTITY_WIDTH, ENTITY_HEIGHT)
                    )

                # 필요한 경우 이미지 뒤집기
                if flip:
                    pygame_image = pygame.transform.flip(pygame_image, True, False)

                frames.append(pygame_image)

            # 프레임이 없으면 더미 프레임 추가
            if not frames:
                dummy = pygame.Surface((ENTITY_WIDTH, ENTITY_HEIGHT), pygame.SRCALPHA)
                frames.append(dummy)

            return frames
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            dummy = pygame.Surface((ENTITY_WIDTH, ENTITY_HEIGHT), pygame.SRCALPHA)
            return [dummy]

    def draw_erpin(self, screen, erpin):
        now = pygame.time.get_ticks()

        if erpin.using_skill:
            frames = self.erpin_skill
        elif erpin.dancing:
            frames = self.erpin_dance
        else:
            frames = self.erpin_idle

        # 프레임 리스트가 비어있지 않은지 확인
        if not frames:
            return

        # 애니메이션 프레임 업데이트
        if now - erpin.last_update > ANIMATION_FRAME_RATE * 1000:
            erpin.last_update = now
            erpin.animation_frame = (erpin.animation_frame + 1) % len(frames)

        # 유효한 인덱스인지 확인
        if 0 <= erpin.animation_frame < len(frames):
            # position.json에서 위치 가져오기
            erpin_pos = self.position_manager.get_position("erpin")
            screen.blit(frames[erpin.animation_frame], erpin_pos)

    def draw_sherum(self, screen, sherum):
        now = pygame.time.get_ticks()
        frames = self.sherum_back if sherum.facing_away else self.sherum_front

        # 프레임 리스트가 비어있지 않은지 확인
        if not frames:
            return

        # 애니메이션 프레임 업데이트
        if now - sherum.last_update > ANIMATION_FRAME_RATE * 1000:
            sherum.last_update = now
            sherum.animation_frame = (sherum.animation_frame + 1) % len(frames)

        # 유효한 인덱스인지 확인
        if 0 <= sherum.animation_frame < len(frames):
            # position.json에서 위치 가져오기
            sherum_pos = self.position_manager.get_position("sherum")
            screen.blit(frames[sherum.animation_frame], sherum_pos)
