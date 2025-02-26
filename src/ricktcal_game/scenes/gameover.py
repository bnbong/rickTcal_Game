import pygame
from PIL import Image, ImageSequence

from ..core.config import *


class GameOverScene:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.font = game.font
        self.big_font = game.big_font

        try:
            self.caught_frames = self.load_animation_frames("sherum_gameover.gif")
            self.current_frame = 0
            self.last_update = 0
        except Exception as e:
            print(f"게임오버 애니메이션 로드 실패: {e}")
            self.caught_frames = []

        # TODO : 에르핀 게이지 소진 애니메이션 혹은 이미지 추가
        try:
            self.no_energy_frames = self.load_animation_frames("erpin_noenergy.gif")
        except Exception as e:
            print(f"에너지 소진 애니메이션 로드 실패: {e}")
            self.no_energy_frames = []

    def load_animation_frames(self, filename):
        try:
            gif_path = f"src/ricktcal_game/resources/animations/{filename}"

            pil_img = Image.open(gif_path)
            frames = []

            for frame in ImageSequence.Iterator(pil_img):
                frame_copy = frame.convert("RGBA")
                pygame_image = pygame.image.fromstring(
                    frame_copy.tobytes(), frame_copy.size, frame_copy.mode
                )

                pygame_image = pygame.transform.scale(pygame_image, (400, 400))

                frames.append(pygame_image)

            return frames
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            dummy = pygame.Surface((400, 400), pygame.SRCALPHA)
            return [dummy]

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            button_rect = pygame.Rect(
                SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 40
            )
            if button_rect.collidepoint(event.pos):
                return "menu"

        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            return "menu"

        return None

    def draw(self, score):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        now = pygame.time.get_ticks()

        if now - self.last_update > 100:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % max(
                1, len(self.caught_frames)
            )

        # 게임 오버 원인에 따른 화면 분기
        game_over_reason = self.game.state_manager.game_over_reason

        if game_over_reason == "no_energy":
            # 게이지 소진으로 인한 게임 오버
            self.draw_no_energy_screen(score)
        else:
            # 선생님에게 들킨 경우 (기본값)
            self.draw_caught_screen(score)

        game_over_text = self.big_font.render("게임 오버!", True, (255, 50, 50))
        self.screen.blit(
            game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 80)
        )

        score_text = self.font.render(f"최종 점수: {int(score)}", True, (255, 255, 255))
        self.screen.blit(
            score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 150)
        )

        button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 40)
        pygame.draw.rect(self.screen, (100, 100, 150), button_rect)

        restart_button = self.font.render("메뉴로 돌아가기", True, (255, 255, 255))
        self.screen.blit(
            restart_button,
            (SCREEN_WIDTH // 2 - restart_button.get_width() // 2, SCREEN_HEIGHT - 95),
        )

    def draw_caught_screen(self, score):
        """선생님에게 들켰을 때의 화면"""
        if self.caught_frames:
            frame = self.caught_frames[self.current_frame]
            self.screen.blit(frame, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 250))

        # 말풍선
        bubble_rect = pygame.Rect(SCREEN_WIDTH // 2 - 175, SCREEN_HEIGHT - 180, 350, 70)
        pygame.draw.rect(self.screen, (255, 255, 255), bubble_rect, border_radius=15)
        pygame.draw.rect(self.screen, (0, 0, 0), bubble_rect, 2, border_radius=15)

        # 말풍선 꼬리
        points = [
            (SCREEN_WIDTH // 2 - 20, SCREEN_HEIGHT - 180),
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 200),
            (SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT - 180),
        ]
        pygame.draw.polygon(self.screen, (255, 255, 255), points)
        pygame.draw.polygon(self.screen, (0, 0, 0), points, 2)

        # 말풍선 텍스트
        speech_text = self.font.render("여왕님, 뭐하시는 건가요?", True, (0, 0, 0))
        self.screen.blit(
            speech_text,
            (SCREEN_WIDTH // 2 - speech_text.get_width() // 2, SCREEN_HEIGHT - 155),
        )

    def draw_no_energy_screen(self, score):
        """게이지가 소진되었을 때의 화면"""
        if self.no_energy_frames:
            frame = self.no_energy_frames[
                self.current_frame % len(self.no_energy_frames)
            ]
            self.screen.blit(frame, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 200))

        # 메시지 박스
        message_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT - 180, 500, 70
        )
        pygame.draw.rect(self.screen, (200, 200, 200), message_rect, border_radius=10)
        pygame.draw.rect(
            self.screen, (100, 100, 100), message_rect, 2, border_radius=10
        )

        # 메시지 텍스트
        message_text = self.font.render(
            "당이 다 떨어진 에르핀은 교실을 뛰쳐나갔다...", True, (50, 50, 50)
        )
        self.screen.blit(
            message_text,
            (SCREEN_WIDTH // 2 - message_text.get_width() // 2, SCREEN_HEIGHT - 155),
        )
