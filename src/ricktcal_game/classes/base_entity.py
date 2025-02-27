class Entity:
    """모든 게임 엔티티의 기본 클래스"""

    def __init__(self):
        self.last_update = 0
        self.animation_frame = 0
        self.entity_type = "generic"  # 엔티티 타입 식별용

    def update(self, current_time):
        """엔티티 상태 업데이트 (모든 서브클래스에서 구현)"""
        pass
