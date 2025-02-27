import pygame

from .base_entity import Entity


class StudentEntity(Entity):
    """학생 타입 엔티티의 기본 클래스"""

    def __init__(self):
        super().__init__()
        self.entity_type = "student"

        # 학생 공통 속성
        self.dancing = False
        self.using_skill = False

    def update(self, current_time):
        """학생 상태 업데이트 (서브클래스에서 오버라이드 가능)"""
        pass

    def update_state(self, dancing=None, using_skill=None):
        """학생 상태 업데이트"""
        if dancing is not None:
            self.dancing = dancing
        if using_skill is not None:
            self.using_skill = using_skill
