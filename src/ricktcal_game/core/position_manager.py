import json
import os


class PositionManager:
    def __init__(self):
        self.positions = {}
        self.load_positions()
        self.student_positions = {}
        self.update_student_positions()

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

    def update_student_positions(self):
        """학생 캐릭터들의 위치를 자동으로 계산"""
        base_x = 450
        base_y = 50
        spacing_x = 100  # 학생 간 가로 간격

        student_names = ["erpin", "joanne"]

        for i, name in enumerate(student_names):
            # 각 학생의 위치 계산 (에르핀은 가장 오른쪽, 죠안은 그 왼쪽)
            pos_x = base_x + (i * spacing_x)

            if name not in self.positions:
                self.positions[name] = {"x": pos_x, "y": base_y}

            self.student_positions[name] = (pos_x, base_y)

        self.save_positions()

    def get_position(self, entity_name):
        """지정된 엔티티의 위치 반환"""
        if entity_name in self.positions:
            pos = self.positions[entity_name]
            return (pos["x"], pos["y"])
        else:
            print(f"경고: {entity_name}의 위치 정보가 없습니다. 기본값 사용.")
            return (0, 0)

    def get_all_student_positions(self):
        """모든 학생의 위치 정보 반환"""
        return self.student_positions

    def save_positions(self):
        """변경된 위치 정보를 파일에 저장"""
        try:
            json_path = os.path.join("src", "ricktcal_game", "core", "position.json")
            with open(json_path, "w") as f:
                json.dump(self.positions, f, indent=2)
            print("위치 정보 저장 성공!")
        except Exception as e:
            print(f"위치 정보 저장 실패: {e}")
