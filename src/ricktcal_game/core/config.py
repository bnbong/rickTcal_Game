# 게임 설정 상수
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GAUGE_DECREASE = 0.25  # 0.1에서 0.25로 증가 (더 빠른 게이지 감소)
GAUGE_INCREASE = 0.5
SKILL_CHARGE = 30
GRACE_PERIOD = 0.3  # 0.3초의 유예 시간

# 위치 상수는 position.json으로 이동
# 참조를 위한 기본값만 남김
DEFAULT_ERPIN_POS = (600, 50)  # 오른쪽 상단
DEFAULT_SHERUM_POS = (100, 300)  # 왼쪽 중앙

# 애니메이션 프레임 속도 (값을 낮출수록 더 빨라짐)
ANIMATION_FRAME_RATE = 0.05

# 엔티티 크기 설정
ENTITY_WIDTH = 250
ENTITY_HEIGHT = 250

# 쉐럼 엔티티 크기를 따로 설정
SHERUM_WIDTH = 350
SHERUM_HEIGHT = 350

# 폰트 경로 (시스템 폰트 사용)
FONT_PATH = None  # 기본 시스템 폰트를 사용

# 게임 초기 상태 값
INITIAL_GAME_STATE = "menu"  # 초기 게임 상태
INITIAL_SCORE = 0  # 초기 점수
INITIAL_GAUGE = 100  # 초기 게이지
INITIAL_SKILL_CHARGES = 2  # 초기 스킬 충전량
GAME_OVER_DELAY = 0.2  # 게임 오버 지연 시간 (초)

# 선생님 행동 관련 설정
TEACHER_TURN_MIN_DELAY = 2000  # 최소 방향 전환 지연 시간 (ms)
TEACHER_TURN_MAX_DELAY = 5000  # 최대 방향 전환 지연 시간 (ms)

# 로딩 화면 설정
LOADING_DURATION = 5.0  # 로딩 화면 지속 시간 (초)
