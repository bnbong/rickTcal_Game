import os

import pygame
from PIL import Image, ImageSequence

from ..core.config import *


class SpriteManager:
    def __init__(self, position_manager, preload=False):
        self.position_manager = position_manager

        # 캐릭터 타입별 애니메이션 프레임 저장소
        self.animations = {"teachers": {}, "students": {}}

        if preload:
            self._preload_animations()

    def _preload_animations(self):
        """모든 애니메이션 프레임 사전 로드"""
        try:
            # 학생 캐릭터 애니메이션 로드
            self.animations["students"]["erpin"] = {
                "idle": self.load_animation_frames("erpin_idle.gif"),
                "dance": self.load_animation_frames("erpin_dance_1.gif"),
                "skill": self.load_animation_frames("erpin_skill.gif"),
            }

            # 죠안 애니메이션 추가
            self.animations["students"]["joanne"] = {
                "idle_1": self.load_animation_frames("joanne_idle_1.gif"),
                "idle_2": self.load_animation_frames("joanne_idle_2.gif"),
                "idle_3": self.load_animation_frames("joanne_idle_3.gif"),
                "dance_1": self.load_animation_frames("joanne_dance_1.gif"),
                "dance_2": self.load_animation_frames("joanne_dance_2.gif"),
            }

            # 선생님 캐릭터 애니메이션 로드
            self.animations["teachers"]["sherum"] = {
                "front": self.load_animation_frames(
                    "sherum_front.gif", flip=True, is_teacher=True
                ),
                "back": self.load_animation_frames("sherum_back.gif", is_teacher=True),
            }

            print("모든 애니메이션 프레임 로드 완료")
        except Exception as e:
            print(f"애니메이션 로드 오류: {e}")

    def load_animation_frames(self, filename, flip=False, is_teacher=False):
        try:
            gif_path = f"src/ricktcal_game/resources/animations/{filename}"

            if not os.path.exists(gif_path):
                print(f"애니메이션 파일 없음: {filename}")
                # 더미 프레임 생성하여 반환
                dummy = pygame.Surface((ENTITY_WIDTH, ENTITY_HEIGHT), pygame.SRCALPHA)
                dummy.fill((200, 200, 200, 128))
                return [dummy]

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
                        pygame_image, (TEACHER_DEFAULT_WIDTH, TEACHER_DEFAULT_HEIGHT)
                    )
                else:
                    pygame_image = pygame.transform.scale(
                        pygame_image, (STUDENT_DEFAULT_WIDTH, STUDENT_DEFAULT_HEIGHT)
                    )

                if flip:  # 설정 시 캐릭터 모션이 변하면 수직으로 뒤집어 뒤를 돌게 함
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

    def draw_entity(self, screen, entity):
        """엔티티 타입에 따라 적절한 렌더링 메서드 호출"""
        if entity.entity_type == "teacher":
            self.draw_teacher(screen, entity)
        elif entity.entity_type == "student":
            self.draw_student(screen, entity)
        else:
            print(f"알 수 없는 엔티티 타입: {entity.entity_type}")

    def draw_teacher(self, screen, teacher):
        """선생님 타입 엔티티 렌더링"""
        now = pygame.time.get_ticks()

        frames = None
        if teacher.name == "sherum":
            frames = (
                self.animations["teachers"]["sherum"]["back"]
                if teacher.facing_away
                else self.animations["teachers"]["sherum"]["front"]
            )
        # TODO : 이후 버전에 다른 선생님 (네르 등) 이 추가되면 여기에 추가

        if not frames:
            return

        if now - teacher.last_update > ANIMATION_FRAME_RATE * 1000:
            teacher.last_update = now
            teacher.animation_frame = (teacher.animation_frame + 1) % len(frames)

        if 0 <= teacher.animation_frame < len(frames):
            teacher_pos = self.position_manager.get_position(teacher.name)

            # 바운스 오프셋 적용 (y 좌표에만 적용)
            adjusted_pos = (teacher_pos[0], teacher_pos[1] + teacher.bounce_offset)

            screen.blit(frames[teacher.animation_frame], adjusted_pos)

    def draw_student(self, screen, student):
        """학생 타입 엔티티 렌더링"""
        now = pygame.time.get_ticks()

        # joanne은 animation_type 속성 사용, erpin은 기존 방식
        if student.name == "joanne":
            anim_type = getattr(student, "animation_type", "idle_1")
        else:
            if student.using_skill:
                anim_type = "skill"
            elif student.dancing:
                anim_type = "dance"
            else:
                anim_type = "idle"

        try:
            frames = self.animations["students"][student.name][anim_type]
        except KeyError:
            print(f"애니메이션 없음: {student.name}/{anim_type}")
            frames = [self._create_dummy_frame()]

        if now - student.last_update > ANIMATION_FRAME_RATE * 1000:
            student.last_update = now
            student.animation_frame = (student.animation_frame + 1) % len(frames)

        if 0 <= student.animation_frame < len(frames):
            student_pos = self.position_manager.get_position(student.name)
            # joanne의 idle_2만 좌우 반전
            if student.name == "joanne" and anim_type == "idle_2":
                flipped_frame = pygame.transform.flip(
                    frames[student.animation_frame], True, False
                )
                screen.blit(flipped_frame, student_pos)
            else:
                screen.blit(frames[student.animation_frame], student_pos)
