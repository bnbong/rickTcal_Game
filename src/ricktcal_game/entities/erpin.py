from ..classes.student_entity import StudentEntity
from ..core.config import ANIMATION_FRAME_RATE, DEFAULT_ERPIN_POS


class Erpin(StudentEntity):
    """에르핀 캐릭터 클래스"""

    def __init__(self):
        super().__init__()
        self.name = "erpin"
