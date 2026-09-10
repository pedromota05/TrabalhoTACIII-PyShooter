"""Estados compartilhados pela máquina de estados do jogo."""

from enum import Enum


class GameState(Enum):
    """Estados possíveis do jogo."""

    MENU = "menu"
    INSTRUCTIONS = "instructions"
    LEVEL_SELECT = "level_select"
    PLAYING = "playing"
    PAUSE = "pause"
    OPTIONS = "options"
    GAME_OVER = "game_over"
    LEVEL_TRANSITION = "level_transition"
