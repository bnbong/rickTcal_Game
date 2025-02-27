import pygame


class SoundManager:
    """게임 사운드를 관리하는 클래스"""

    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        pygame.mixer.init()

        self.bgm = None
        self.sfx = {}
        self.current_dance_sound = None
        self.load_sounds()

    def load_sounds(self):
        """기본 사운드 파일 로드"""
        try:
            try:
                pygame.mixer.music.load("src/ricktcal_game/resources/sounds/bgm.mp3")
            except Exception as e:
                print(f"배경 음악 로드 실패: {e}")

            self.load_sfx("click", "click.wav")

        except Exception as e:
            print(f"사운드 로드 실패: {e}")

    def load_sfx(self, name, filename):
        """개별 효과음 로드 함수"""
        try:
            self.sfx[name] = pygame.mixer.Sound(
                f"src/ricktcal_game/resources/sounds/{filename}"
            )
        except Exception as e:
            print(f"{filename} 효과음 로드 실패: {e}")

    def load_gameplay_sounds(self):
        """게임 플레이 관련 사운드 로드"""
        # TODO : 효과음 추가 혹은 제거
        self.load_sfx("dance", "dance.wav")
        self.load_sfx("skill", "skill.wav")
        self.load_sfx("game_over", "game_over.wav")
        self.load_sfx("warning", "warning.wav")  # TODO : 경고음 추가 혹은 제거
        self.load_sfx(
            "turn", "turn.wav"
        )  # TODO : 선생님 방향 전환 효과음 추가 혹은 제거
        print("게임 플레이 사운드 로드 완료")

    def play_bgm(self):
        """배경 음악 재생"""
        try:
            pygame.mixer.music.set_volume(self.settings_manager.get_bgm_volume())
            pygame.mixer.music.play(-1)  # -1은 무한 반복
        except Exception as e:
            print(f"배경 음악 재생 실패: {e}")

    def stop_bgm(self):
        """배경 음악 중지"""
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            print(f"배경 음악 중지 실패: {e}")

    def play_sfx(self, sound_name):
        """효과음 재생"""
        if sound_name in self.sfx:
            try:
                self.sfx[sound_name].set_volume(self.settings_manager.get_sfx_volume())

                if sound_name == "dance":
                    # 이전에 재생 중이던 춤 효과음이 있으면 중지
                    if self.current_dance_sound:
                        self.current_dance_sound.stop()
                    # 새로운 춤 효과음 재생 및 추적
                    self.current_dance_sound = self.sfx[sound_name]
                    self.current_dance_sound.play()
                else:
                    # 일반 효과음 재생
                    self.sfx[sound_name].play()
            except Exception as e:
                print(f"{sound_name} 효과음 재생 실패: {e}")

    def stop_sfx(self, sound_name):
        """특정 효과음 중지"""
        if sound_name == "dance" and self.current_dance_sound:
            try:
                self.current_dance_sound.stop()
                self.current_dance_sound = None
            except Exception as e:
                print(f"{sound_name} 효과음 중지 실패: {e}")

    def update_volumes(self):
        """볼륨 설정 업데이트"""
        try:
            pygame.mixer.music.set_volume(self.settings_manager.get_bgm_volume())

            for sound in self.sfx.values():
                sound.set_volume(self.settings_manager.get_sfx_volume())
        except Exception as e:
            print(f"볼륨 업데이트 실패: {e}")

    def load_all_sounds(self):
        """모든 게임 사운드 로드"""
        self._sound_categories = {
            "ui": ["click"],
            "gameplay": ["dance", "skill", "game_over", "warning", "turn"],
        }

        for category, sounds in self._sound_categories.items():
            self._load_sound_category(category, sounds)

        self._load_background_music()

    def _load_sound_category(self, category, sound_list):
        """특정 카테고리의 사운드 효과 로드"""
        print(f"{category} 사운드 로드 중...")
        for sound_name in sound_list:
            self.load_sfx(sound_name, f"{sound_name}.wav")
        print(f"{category} 사운드 로드 완료")

    def stop_all_sounds(self, except_sounds=None):
        """모든 효과음 중지 (예외 리스트 제외)"""
        if except_sounds is None:
            except_sounds = []

        try:
            for sound_name, sound in self.sfx.items():
                if sound_name not in except_sounds:
                    sound.stop()

            if "dance" not in except_sounds:
                self.current_dance_sound = None

            if "bgm" not in except_sounds:
                self.stop_bgm()

            print("모든 사운드 중지 완료")
        except Exception as e:
            print(f"사운드 중지 오류: {e}")
