import math

import pygame


class Renderer:
    """게임 렌더링을 담당하는 클래스"""

    def __init__(self, game):
        self.game = game
        self.screen = game.screen

    def render(self):
        """현재 게임 상태에 따라 화면 렌더링"""
        if self.game.state_manager.game_state == "menu":
            self.render_title()
        elif self.game.state_manager.game_state == "loading":
            self.render_loading()
        elif self.game.state_manager.game_state == "playing":
            self.render_game()
        elif self.game.state_manager.game_state == "game_over":
            self.render_gameover()

        pygame.display.flip()

    def render_title(self):
        """타이틀 화면 렌더링"""
        self.game.scenes["menu"].draw()

    def render_loading(self):
        """로딩 화면 렌더링"""
        """로딩 화면은 필요시 추가 예정"""
        self.game.scenes["loading"].draw()

    def render_game(self):
        """게임 화면 렌더링"""
        self.screen.fill((255, 255, 255))

        # 엔티티 렌더링
        if self.game.sprites:
            self.game.sprites.draw_sherum(self.screen, self.game.sherum)
            self.game.sprites.draw_erpin(self.screen, self.game.erpin)

            # 느낌표 렌더링 (게임 오버 트리거 시)
            if self.game.state_manager.show_exclamation:
                # 선생님 위치 가져오기
                sherum_pos = self.game.position_manager.get_position("sherum")
                # 느낌표 위치는 선생님 기준 오른쪽으로 조정
                exclamation_pos = (sherum_pos[0] + 300, sherum_pos[1] + 100)
                self.draw_exclamation(exclamation_pos)

        # UI 요소 렌더링
        self.render_game_ui()

    def render_game_ui(self):
        """게임 UI 렌더링"""
        # 게이지 바
        pygame.draw.rect(self.screen, (0, 0, 200), (20, 20, 200, 30))
        pygame.draw.rect(
            self.screen, (0, 200, 0), (20, 20, self.game.state_manager.gauge * 2, 30)
        )

        # 점수 및 스킬 표시
        score_text = self.game.font.render(
            f"점수: {int(self.game.state_manager.score)}", True, (0, 0, 0)
        )
        skill_text = self.game.font.render(
            f"스킬: {self.game.state_manager.skill_charges}", True, (0, 0, 0)
        )
        self.screen.blit(score_text, (20, 70))
        self.screen.blit(skill_text, (20, 110))

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
