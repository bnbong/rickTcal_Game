from ..classes.teacher_entity import TeacherEntity
from ..core.config import TEACHER_TURN_MAX_DELAY, TEACHER_TURN_MIN_DELAY


class Sherum(TeacherEntity):
    """선새임 캐릭터 클래스"""

    def __init__(self):
        super().__init__()
        self.name = "sherum"
