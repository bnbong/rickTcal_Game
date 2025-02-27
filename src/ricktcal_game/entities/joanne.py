from ..classes.student_entity import StudentEntity


class Joanne(StudentEntity):
    """조안 캐릭터 클래스"""

    def __init__(self):
        super().__init__()
        self.name = "joanne"
        # TODO : 죠안 춤추는 속성 추가, 선생님이 뒤도는 타이밍을 알고 있는 설정으로 절대 춤추는 걸 걸리지 않음
