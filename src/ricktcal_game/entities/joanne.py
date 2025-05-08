from ..classes.student_entity import StudentEntity
import random
from typing import Optional


class Joanne(StudentEntity):
    """조안 캐릭터 클래스 (플레이어의 친구 역할)"""

    def __init__(self) -> None:
        super().__init__()
        self.name: str = "joanne"
        self.animation_type: str = "idle_1"  # joanne_idle_1.gif
        self.last_dance_end_time: Optional[int] = None
        self.dancing: bool = False
        self._last_erpin_dancing: bool = False
        self.current_dance_anim: Optional[str] = None  # 현재 dance 애니메이션 타입
        # TODO : 조안 춤추는 속성 추가, 선생님이 뒤도는 타이밍을 알고 있는 설정으로 절대 춤추는 걸 걸리지 않음

    def update(
        self,
        current_time: float,
        erpin: Optional[StudentEntity] = None,
        game_time: int = 0,
    ) -> None:
        """
        joanne의 상태를 인게임 경과 시간, erpin의 상태에 따라 업데이트
        :param current_time: 현재 시간(ms)
        :param erpin: 플레이어 캐릭터 엔티티
        :param game_time: 인게임 경과 시간(초)
        """
        # 60초(1분) 이후에는 erpin이 춤출 때 joanne도 같이 춤
        if game_time >= 60:
            if erpin and erpin.dancing:
                self.dancing = True
                # 춤을 새로 시작할 때만 랜덤 애니메이션 선택
                if not self._last_erpin_dancing or self.current_dance_anim is None:
                    self.current_dance_anim = random.choice(["dance_1", "dance_2"])
                self.animation_type = self.current_dance_anim
                self._last_erpin_dancing = True
            else:
                self.dancing = False
                self.animation_type = "idle_1"
                self.current_dance_anim = None
                self._last_erpin_dancing = False
            return

        # 60초 이전: 상태 전환 로직
        if erpin:
            if erpin.dancing:
                self.animation_type = "idle_2"
                self._last_erpin_dancing = True
                self.last_dance_end_time = None
            else:
                if self._last_erpin_dancing:
                    self.last_dance_end_time = game_time
                    self._last_erpin_dancing = False
                # 춤 멈춘 후 5초간 idle_3, 그 후 idle_1
                if self.last_dance_end_time is not None:
                    if game_time - self.last_dance_end_time < 5:
                        self.animation_type = "idle_3"
                    else:
                        self.animation_type = "idle_1"
                        self.last_dance_end_time = None
                else:
                    self.animation_type = "idle_1"
        else:
            self.animation_type = "idle_1"
