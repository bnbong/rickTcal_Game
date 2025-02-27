import math

import pygame

from .config import (
    SCENE_GAMEOVER,
    SCENE_LOADING,
    SCENE_PLAYING,
    SCENE_SETTINGS,
    SCENE_TITLE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class Renderer:
    """게임 렌더링을 담당하는 클래스"""

    def __init__(self, game):
        self.game = game
        self.screen = game.screen

    def render(self):
        """현재 게임 상태에 따라 화면 렌더링"""
        current_state = self.game.state_manager.game_state

        if current_state == SCENE_TITLE:
            self.render_title()
        elif current_state == SCENE_LOADING:
            self.render_loading()
        elif current_state == SCENE_PLAYING:
            self.render_game()
        elif current_state == SCENE_GAMEOVER:
            self.render_gameover()
        elif current_state == SCENE_SETTINGS:
            self.render_settings()
        else:
            self.screen.fill((100, 0, 0))
            if hasattr(self.game, "font"):
                error_text = self.game.font.render(
                    f"알 수 없는 게임 상태: {current_state}", True, (255, 255, 255)
                )
                self.screen.blit(error_text, (100, 100))

        pygame.display.flip()

    def render_title(self):
        """타이틀 화면 렌더링"""
        try:
            if SCENE_TITLE in self.game.scenes:
                self.game.scenes[SCENE_TITLE].draw()
            else:
                # 기본 씬 (씬이 없는 경우)
                self.screen.fill((0, 0, 100))
                if hasattr(self.game, "font"):
                    error_text = self.game.font.render(
                        "타이틀 씬 없음", True, (255, 255, 255)
                    )
                    self.screen.blit(error_text, (100, 100))
        except Exception as e:
            print(f"타이틀 렌더링 오류: {e}")
            self.screen.fill((100, 0, 0))

    def render_loading(self):
        """로딩 화면 렌더링"""
        try:
            self.screen.fill((20, 30, 70))
            if SCENE_LOADING in self.game.scenes:
                self.game.scenes[SCENE_LOADING].draw()
            else:
                # 기본 씬 (씬이 없는 경우)
                loading_text = self.game.font.render(
                    "로딩 중...", True, (255, 255, 255)
                )
                self.screen.blit(
                    loading_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2)
                )
        except Exception as e:
            print(f"로딩 렌더링 오류: {e}")

    def render_game(self):
        """게임 화면 렌더링"""
        self.screen.fill((255, 255, 255))

        if self.game.sprites:
            # 선생님 엔티티 렌더링
            for teacher in self.game.entities["teachers"].values():
                self.game.sprites.draw_entity(self.screen, teacher)

            # 학생 엔티티 렌더링
            for student in self.game.entities["students"].values():
                self.game.sprites.draw_entity(self.screen, student)

            # 느낌표 렌더링 (게임 오버 트리거 시)
            if self.game.state_manager.show_exclamation:
                sherum_pos = self.game.position_manager.get_position("sherum")
                # 느낌표 위치 - 선생님 기준 오른쪽
                exclamation_pos = (sherum_pos[0] + 300, sherum_pos[1] + 100)
                self.draw_exclamation(exclamation_pos)

        self.render_ui()

    def render_ui(self):
        """UI 요소 렌더링"""
        gauge_x = 20
        gauge_y = 20
        gauge_width = 200
        gauge_height = 30

        # 게이지 바
        pygame.draw.rect(
            self.screen, (0, 0, 200), (gauge_x, gauge_y, gauge_width, gauge_height)
        )
        pygame.draw.rect(
            self.screen,
            (0, 200, 0),
            (gauge_x, gauge_y, self.game.state_manager.gauge * 2, gauge_height),
        )

        text_y = gauge_y + gauge_height + 10
        text_spacing = 35

        # 텍스트 배경 TODO : 텍스트 배경 이미지 리소스 추가
        pygame.draw.rect(
            self.screen,
            (0, 0, 0, 128),
            (gauge_x - 5, text_y - 5, 250, 150),
            border_radius=5,
        )

        # 점수 및 스킬 표시
        try:
            if hasattr(self.game, "font_manager"):
                # 점수 텍스트
                score_text = self.game.font_manager.render_text(
                    f"점수: {int(self.game.state_manager.score)}",
                    "korean",
                    "normal",
                    (255, 255, 255),
                )
                self.screen.blit(score_text, (gauge_x, text_y))

                # 스킬 텍스트
                skill_text = self.game.font_manager.render_text(
                    f"스킬: {self.game.state_manager.skill_charges}",
                    "korean",
                    "normal",
                    (255, 255, 255),
                )
                self.screen.blit(skill_text, (gauge_x, text_y + text_spacing))

                # 조작법 도움말 텍스트
                skill_help = self.game.font_manager.render_text(
                    "Z - 스킬", "korean", "small", (200, 200, 255)
                )
                dance_help = self.game.font_manager.render_text(
                    "스페이스바 - 춤추기", "korean", "small", (200, 200, 255)
                )
                self.screen.blit(skill_help, (gauge_x, text_y + text_spacing * 2))
                self.screen.blit(dance_help, (gauge_x, text_y + text_spacing * 3))

            else:
                # 기본 폰트 사용
                # 한글 폰트가 없는 경우 대비 (영문만 표시)
                score_text = self.game.font.render(
                    f"Score: {int(self.game.state_manager.score)}",
                    True,
                    (255, 255, 255),
                )
                self.screen.blit(score_text, (gauge_x, text_y))

                # 스킬 텍스트
                skill_text = self.game.font.render(
                    f"Skill: {self.game.state_manager.skill_charges}",
                    True,
                    (255, 255, 255),
                )
                self.screen.blit(skill_text, (gauge_x, text_y + text_spacing))

                # 조작법 도움말 텍스트
                skill_help = self.game.font.render("Z - Skill", True, (200, 200, 255))
                dance_help = self.game.font.render(
                    "Space - Dance", True, (200, 200, 255)
                )
                self.screen.blit(skill_help, (gauge_x, text_y + text_spacing * 2))
                self.screen.blit(dance_help, (gauge_x, text_y + text_spacing * 3))
        except Exception as e:
            print(f"UI 텍스트 렌더링 오류: {e}")
            error_text = self.game.font.render(f"Text Error: {e}", True, (255, 50, 50))
            self.screen.blit(error_text, (gauge_x, text_y))

    def render_gameover(self):
        """게임 오버 화면 렌더링"""
        self.game.scenes["game_over"].draw(self.game.state_manager.score)

    def draw_exclamation(self, pos):
        """게임 오버 느낌표"""
        # TODO : 느낌표 이미지 추가 및 애니메이션 재설정 (현재는 직접 그리는 버전)
        width = 14
        height = 60
        color = (255, 30, 30)
        gap = 10

        current_time = pygame.time.get_ticks() / 1000

        # 박동 효과 - 기둥
        rect_scale = 1.0 + 0.2 * abs(math.sin(current_time * 8))

        # 박동 효과 - 원
        circle_scale = 1.0 + 0.3 * abs(math.sin(current_time * 10 + 1))

        rect_height = int(height * rect_scale)

        circle_y = pos[1] + height + gap + width // 2

        # 느낌표의 윗부분 (직사각형)
        pygame.draw.rect(self.screen, color, (pos[0], pos[1], width, rect_height))

        # 느낌표의 아랫부분 (원)
        pygame.draw.circle(
            self.screen,
            color,
            (pos[0] + width // 2, circle_y),
            int(width // 2 * circle_scale),
        )

    def render_settings(self):
        """설정 화면 렌더링"""
        self.game.scenes["settings"].draw()
