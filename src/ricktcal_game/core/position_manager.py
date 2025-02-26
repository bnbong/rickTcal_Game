import json
import os


class PositionManager:
    def __init__(self):
        self.positions = {}
        self.load_positions()

    def load_positions(self):
        """position.json 파일에서 엔티티 위치 정보 로드"""
        try:
            json_path = os.path.join("src", "ricktcal_game", "core", "position.json")
            with open(json_path, "r") as f:
                self.positions = json.load(f)
            print("위치 정보 로드 성공!")
        except Exception as e:
            print(f"위치 정보 로드 실패: {e}")
            # 기본 위치 정보 설정
            self.positions = {
                "erpin": {"x": 600, "y": 50},
                "sherum": {"x": 100, "y": 300},
            }

    def get_position(self, entity_name):
        """지정된 엔티티의 위치 반환"""
        if entity_name in self.positions:
            pos = self.positions[entity_name]
            return (pos["x"], pos["y"])
        else:
            print(f"경고: {entity_name}의 위치 정보가 없습니다. 기본값 사용.")
            return (0, 0)

    def save_positions(self):
        """변경된 위치 정보를 파일에 저장"""
        try:
            json_path = os.path.join("src", "ricktcal_game", "core", "position.json")
            with open(json_path, "w") as f:
                json.dump(self.positions, f, indent=2)
            print("위치 정보 저장 성공!")
        except Exception as e:
            print(f"위치 정보 저장 실패: {e}")
