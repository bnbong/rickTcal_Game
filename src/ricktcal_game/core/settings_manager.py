import json
import os


class SettingsManager:
    """게임 설정을 관리하는 클래스"""

    def __init__(self):
        self.settings = {
            "bgm_volume": 0.7,  # 배경 음악 볼륨 (0.0 ~ 1.0)
            "sfx_volume": 0.8,  # 효과음 볼륨 (0.0 ~ 1.0)
        }
        self.load_settings()

    def load_settings(self):
        """설정 파일에서 설정 로드"""
        try:
            settings_path = os.path.join(
                "src", "ricktcal_game", "core", "settings.json"
            )
            if os.path.exists(settings_path):
                with open(settings_path, "r") as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
                print("설정 로드 성공!")
        except Exception as e:
            print(f"설정 로드 실패: {e}")

    def save_settings(self):
        """설정을 파일에 저장"""
        try:
            settings_path = os.path.join(
                "src", "ricktcal_game", "core", "settings.json"
            )
            with open(settings_path, "w") as f:
                json.dump(self.settings, f, indent=2)
            print("설정 저장 성공!")
        except Exception as e:
            print(f"설정 저장 실패: {e}")

    def get_setting(self, key, default=None):
        """설정 값 조회"""
        return self.settings.get(key, default)

    def update_setting(self, key, value):
        """설정 값 업데이트"""
        self.settings[key] = value
        self.save_settings()

    def get_bgm_volume(self):
        """배경 음악 볼륨 조회"""
        return self.settings.get("bgm_volume", 0.7)

    def get_sfx_volume(self):
        """효과음 볼륨 조회"""
        return self.settings.get("sfx_volume", 0.8)

    def set_bgm_volume(self, volume):
        """배경 음악 볼륨 설정"""
        self.settings["bgm_volume"] = max(0.0, min(1.0, volume))
        self.save_settings()

    def set_sfx_volume(self, volume):
        """효과음 볼륨 설정"""
        self.settings["sfx_volume"] = max(0.0, min(1.0, volume))
        self.save_settings()
