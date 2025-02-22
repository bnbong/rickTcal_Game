import pygame
import random
from pygame.locals import *
from .core.config import *
from .entities.guoju import GyoJu
from .entities.erpin import Erpin
from .classes.sprites import SpriteManager


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)

        # 게임 요소 초기화
        self.gyoju = GyoJu()
        self.erpin = Erpin()
        self.sprites = SpriteManager()

        # 게임 상태 변수
        self.running = True
        self.game_over = False
        self.score = 0
        self.gauge = 100
        self.skill_charges = 2
        self.last_turn_time = 0  # 마지막 방향 전환 시간
        self.prev_facing_state = False  # 이전 교주 상태

    def reset_game(self):
        self.__init__()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

            if event.type == KEYDOWN:
                if event.key == K_z and self.skill_charges > 0:
                    self.gauge = min(100, self.gauge + SKILL_CHARGE)
                    self.skill_charges -= 1
                if event.key == K_r and self.game_over:
                    self.reset_game()

                # 스페이스바 입력 허용 (항상 받음)
                if event.key == K_SPACE:
                    self.erpin.update_dance_state(True)

            if event.type == KEYUP:
                if event.key == K_SPACE:
                    self.erpin.update_dance_state(False)

    def update(self):
        current_time = pygame.time.get_ticks() / 1000  # 초 단위

        # 교주 상태 업데이트
        prev_state = self.gyoju.facing_away
        self.gyoju.update(current_time * 1000)

        # 방향 변경 감지 시 시간 기록
        if self.gyoju.facing_away != prev_state:
            self.last_turn_time = current_time

        # 게임 오버 조건 수정
        if self.erpin.dancing and not self.gyoju.facing_away:
            elapsed = current_time - self.last_turn_time
            if elapsed > GRACE_PERIOD:
                self.game_over = True

        # 게이지 관리
        if self.erpin.dancing:
            self.gauge = min(100, self.gauge + GAUGE_INCREASE)
        else:
            self.gauge = max(0, self.gauge - GAUGE_DECREASE)

        # 점수 업데이트
        self.score += 0.1

    def draw(self):
        self.screen.fill((255, 255, 255))

        # 엔티티 그리기
        self.sprites.draw_gyoju(self.screen, self.gyoju.facing_away)
        self.sprites.draw_erpin(self.screen, self.erpin.dancing)

        # UI 요소 그리기 (게이지, 점수 등)
        pygame.draw.rect(self.screen, (0, 0, 200), (20, 20, 200, 30))
        pygame.draw.rect(self.screen, (0, 200, 0), (20, 20, self.gauge * 2, 30))

        # 점수 및 스킬 표시
        score_text = self.font.render(f"Score: {int(self.score)}", True, (0, 0, 0))
        skill_text = self.font.render(f"Skills: {self.skill_charges}", True, (0, 0, 0))
        self.screen.blit(score_text, (20, 70))
        self.screen.blit(skill_text, (20, 110))

        # 게임 오버 화면
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))

            game_over_text = self.font.render(
                f"Game Over! Final Score: {int(self.score)}", True, (255, 255, 255)
            )
            restart_text = self.font.render("Press R to restart", True, (255, 255, 255))
            self.screen.blit(
                game_over_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 30)
            )
            self.screen.blit(
                restart_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 30)
            )

    def run(self):
        while self.running:
            self.handle_events()
            if not self.game_over:
                self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
