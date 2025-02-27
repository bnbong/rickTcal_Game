from ..core.config import (
    SCENE_GAMEOVER,
    SCENE_LOADING,
    SCENE_PLAYING,
    SCENE_SETTINGS,
    SCENE_TITLE,
)
from .gameover import GameOverScene
from .settings import SettingsScene
from .title import TitleScene

SCENE_TITLE = SCENE_TITLE
SCENE_PLAYING = SCENE_PLAYING
SCENE_GAMEOVER = SCENE_GAMEOVER
SCENE_SETTINGS = SCENE_SETTINGS

SCENE_CLASSES = {
    SCENE_TITLE: TitleScene,
    SCENE_GAMEOVER: GameOverScene,
    SCENE_SETTINGS: SettingsScene,
}
