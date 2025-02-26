from .gameover import GameOverScene
from .loading import LoadingScene
from .title import TitleScene

# 씬 ID 상수 정의
SCENE_TITLE = "menu"
SCENE_LOADING = "loading"
SCENE_PLAYING = "playing"
SCENE_GAMEOVER = "game_over"

# 씬 클래스 맵핑
SCENE_CLASSES = {
    SCENE_TITLE: TitleScene,
    SCENE_LOADING: LoadingScene,
    SCENE_GAMEOVER: GameOverScene,
}
