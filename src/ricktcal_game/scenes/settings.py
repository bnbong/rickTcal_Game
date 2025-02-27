import pygame

from ..core.config import *


class SettingsScene:
    """설정 화면 클래스"""

    def __init__(self, game):
        self.game = game
        self.screen = game.screen

        # 폰트 관리자 사용
        self.font_manager = game.font_manager
        self.title_font = self.font_manager.get_font("korean", "title")
        self.font = self.font_manager.get_font("korean", "normal")

        # 슬라이더 위치 및 크기
        self.bgm_slider_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 150, 200, 20)
        self.sfx_slider_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 220, 200, 20)

        # 슬라이더 핸들 크기
        self.handle_size = 24

        # 버튼 설정
        self.back_button_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 40
        )
        self.credits_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 300, 200, 40)

        # 크레딧 표시 여부
        self.show_credits = False

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos

            if self.show_credits:
                # 크레딧 화면에서 아무 곳이나 클릭하면 설정 화면으로 돌아감
                self.show_credits = False
                self.game.sound_manager.play_sfx("click")
                return None

            # 뒤로 가기 버튼
            if self.back_button_rect.collidepoint(mouse_pos):
                self.game.sound_manager.play_sfx("click")
                return self.game.previous_state

            # 크레딧 버튼
            if self.credits_button_rect.collidepoint(mouse_pos):
                self.show_credits = True
                self.game.sound_manager.play_sfx("click")
                return None

            # BGM 볼륨 슬라이더
            if self.bgm_slider_rect.collidepoint(mouse_pos):
                volume = (
                    mouse_pos[0] - self.bgm_slider_rect.x
                ) / self.bgm_slider_rect.width
                self.game.settings_manager.set_bgm_volume(volume)
                self.game.sound_manager.update_volumes()

            # SFX 볼륨 슬라이더
            if self.sfx_slider_rect.collidepoint(mouse_pos):
                volume = (
                    mouse_pos[0] - self.sfx_slider_rect.x
                ) / self.sfx_slider_rect.width
                self.game.settings_manager.set_sfx_volume(volume)
                self.game.sound_manager.update_volumes()
                self.game.sound_manager.play_sfx("click")  # 볼륨 변경 시 효과음 재생

        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            mouse_pos = event.pos

            # 드래그로 슬라이더 조절
            if self.bgm_slider_rect.collidepoint(mouse_pos):
                volume = (
                    mouse_pos[0] - self.bgm_slider_rect.x
                ) / self.bgm_slider_rect.width
                volume = max(0, min(1, volume))  # 0과 1 사이로 제한
                self.game.settings_manager.set_bgm_volume(volume)
                self.game.sound_manager.update_volumes()

            if self.sfx_slider_rect.collidepoint(mouse_pos):
                volume = (
                    mouse_pos[0] - self.sfx_slider_rect.x
                ) / self.sfx_slider_rect.width
                volume = max(0, min(1, volume))  # 0과 1 사이로 제한
                self.game.settings_manager.set_sfx_volume(volume)
                self.game.sound_manager.update_volumes()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.sound_manager.play_sfx("click")
                return self.game.previous_state

        return None

    def draw(self):
        # 기본 배경
        self.screen.fill((200, 230, 255))

        if self.show_credits:
            self.draw_credits()
        else:
            self.draw_settings()

    def draw_settings(self):
        # 제목
        title_text = self.title_font.render("설정", True, (50, 50, 150))
        self.screen.blit(
            title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50)
        )

        # BGM 볼륨 슬라이더
        bgm_text = self.font.render("배경 음악:", True, (50, 50, 150))
        self.screen.blit(
            bgm_text, (self.bgm_slider_rect.x - 150, self.bgm_slider_rect.y)
        )

        # 슬라이더 배경
        pygame.draw.rect(self.screen, (100, 100, 150), self.bgm_slider_rect)

        # 슬라이더 채우기
        bgm_volume = self.game.settings_manager.get_bgm_volume()
        fill_width = int(self.bgm_slider_rect.width * bgm_volume)
        pygame.draw.rect(
            self.screen,
            (100, 150, 250),
            (
                self.bgm_slider_rect.x,
                self.bgm_slider_rect.y,
                fill_width,
                self.bgm_slider_rect.height,
            ),
        )

        # 슬라이더 핸들
        handle_x = self.bgm_slider_rect.x + fill_width - self.handle_size // 2
        pygame.draw.circle(
            self.screen,
            (200, 200, 250),
            (handle_x, self.bgm_slider_rect.y + self.bgm_slider_rect.height // 2),
            self.handle_size // 2,
        )

        # SFX 볼륨 슬라이더
        sfx_text = self.font.render("효과음:", True, (50, 50, 150))
        self.screen.blit(
            sfx_text, (self.sfx_slider_rect.x - 150, self.sfx_slider_rect.y)
        )

        # 슬라이더 배경
        pygame.draw.rect(self.screen, (100, 100, 150), self.sfx_slider_rect)

        # 슬라이더 채우기
        sfx_volume = self.game.settings_manager.get_sfx_volume()
        fill_width = int(self.sfx_slider_rect.width * sfx_volume)
        pygame.draw.rect(
            self.screen,
            (100, 150, 250),
            (
                self.sfx_slider_rect.x,
                self.sfx_slider_rect.y,
                fill_width,
                self.sfx_slider_rect.height,
            ),
        )

        # 슬라이더 핸들
        handle_x = self.sfx_slider_rect.x + fill_width - self.handle_size // 2
        pygame.draw.circle(
            self.screen,
            (200, 200, 250),
            (handle_x, self.sfx_slider_rect.y + self.sfx_slider_rect.height // 2),
            self.handle_size // 2,
        )

        # 크레딧 버튼
        pygame.draw.rect(self.screen, (100, 100, 150), self.credits_button_rect)
        credits_text = self.font.render("크레딧", True, (255, 255, 255))
        self.screen.blit(
            credits_text,
            (
                self.credits_button_rect.x
                + self.credits_button_rect.width // 2
                - credits_text.get_width() // 2,
                self.credits_button_rect.y
                + self.credits_button_rect.height // 2
                - credits_text.get_height() // 2,
            ),
        )

        # 뒤로 가기 버튼
        pygame.draw.rect(self.screen, (100, 100, 150), self.back_button_rect)
        back_text = self.font.render("뒤로 가기", True, (255, 255, 255))
        self.screen.blit(
            back_text,
            (
                self.back_button_rect.x
                + self.back_button_rect.width // 2
                - back_text.get_width() // 2,
                self.back_button_rect.y
                + self.back_button_rect.height // 2
                - back_text.get_height() // 2,
            ),
        )

    def draw_credits(self):
        # 크레딧 배경
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((30, 30, 70))
        self.screen.blit(overlay, (0, 0))

        # 타이틀
        title_text = self.title_font.render("크레딧", True, (255, 255, 255))
        self.screen.blit(
            title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 80)
        )

        # 제작자 정보
        info_texts = [
            "제작자: 당신의 이름",
            "이메일: your.email@example.com",
            "GitHub: github.com/yourusername",
            "",
            "트릭컬 리바이브 팬게임",
            "© 2023 All Rights Reserved",
            "",
            "아무 곳이나 클릭하여 돌아가기",
        ]

        y_pos = 160
        for text in info_texts:
            rendered_text = self.font.render(text, True, (200, 200, 255))
            self.screen.blit(
                rendered_text,
                (SCREEN_WIDTH // 2 - rendered_text.get_width() // 2, y_pos),
            )
            y_pos += 40
