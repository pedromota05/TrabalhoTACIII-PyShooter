"""
game.py — Aplicação e loop principal do PyShooter.

Arquitetura:
    - Utiliza máquina de estados (GameState) delegando telas para ui/screens/.
    - Entidades e mundo delegados para os pacotes entities/ e world/.
    - Áudio e imagens centralizados no singleton AssetManager.
    - Configurações centralizadas em config.py.

Controles:
    A / ←   — mover para a esquerda
    D / →   — mover para a direita
    W / ↑   — pular
    Espaço  — atirar
    Q / G   — lançar granada
    ESC     — pausar / voltar
"""

import pygame
from pygame import mixer

import button
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BLACK,
    FONT_NAME, FONT_SIZE,
)
from asset_manager import AssetManager
from core.gameplay import update_game_entities, update_level_transition, update_playing
from core.input_handler import handle_events
from core.level_loader import load_level, reset_groups
from core.renderer import draw_background, draw_game_entities, draw_text
from game_state import GameState
from entities import ScreenFade
from ui.screens import (
    MainMenuScreen,
    InstructionsScreen,
    OptionsScreen,
    LevelSelectScreen,
    PauseOverlay,
    GameOverScreen,
)


# ======================================================================
#  GAME  — classe principal que orquestra o jogo
# ======================================================================
class Game:
    """Classe principal que encapsula o game loop, estados, grupos e gameplay."""

    def __init__(self):
        mixer.init()
        pygame.init()

        # ----- Display & Clock -----
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('PyShooter - TACIII')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
        self.font_bold = pygame.font.SysFont(FONT_NAME, FONT_SIZE, bold=True)
        self.title_font = pygame.font.SysFont(FONT_NAME, 50, bold=True)

        # ----- Assets -----
        self.assets = AssetManager()
        self.assets.load_all()

        # ----- Estado do jogo -----
        self.state = GameState.MENU
        self.running = True
        self.level = 1
        self.screen_scroll = 0
        self.bg_scroll = 0
        self.start_intro = False
        self.previous_state = None

        # ----- Volume -----
        self.music_vol = round(pygame.mixer.music.get_volume() * 12)
        sample_sfx = self.assets.get_sound('shot')
        self.sfx_vol = round(sample_sfx.get_volume() * 12)

        # ----- Flags de input -----
        self.moving_left = False
        self.moving_right = False
        self.shoot = False
        self.grenade_input = False
        self.grenade_thrown = False

        # ----- Grupos de sprites -----
        self.enemy_group = pygame.sprite.Group()
        self.boss_group = pygame.sprite.Group()
        self.bullet_group = pygame.sprite.Group()
        self.grenade_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.item_box_group = pygame.sprite.Group()
        self.decoration_group = pygame.sprite.Group()
        self.water_group = pygame.sprite.Group()
        self.exit_group = pygame.sprite.Group()

        # ----- Efeitos de fade e HUD -----
        self.intro_fade = ScreenFade(1, BLACK, 4)

        # ----- Botão de Pause no Gameplay -----
        pause_img = self.assets.get_image('pause_btn')
        pause_img = pygame.transform.scale(pause_img, (40, 40))
        self.pause_button = button.Button(SCREEN_WIDTH - 60, 10, pause_img, 1)

        # ----- Instâncias das Telas (SRP) -----
        self.menu_screen = MainMenuScreen(self.assets)
        self.instructions_screen = InstructionsScreen(self.assets, self.font, self.font_bold)
        self.options_screen = OptionsScreen(self.assets, self.font_bold)
        self.level_select_screen = LevelSelectScreen(self.assets, self.font, self.font_bold)
        self.pause_screen = PauseOverlay(self.assets, self.title_font)
        self.game_over_screen = GameOverScreen(self.assets)

        # ----- Objetos do jogo -----
        self.player = None
        self.health_bar = None
        self.world = None
        self._load_level(self.level)

    # ==================================================================
    #  Carregamento / Reset de nível  (DRY)
    # ==================================================================
    def _reset_groups(self):
        """Mantém a interface da sessão e delega a limpeza de grupos."""
        reset_groups(self)

    def _load_level(self, level_number: int):
        """Mantém a interface da sessão e delega o carregamento."""
        load_level(self, level_number)

    # ==================================================================
    #  Renderização auxiliar
    # ==================================================================
    def _draw_bg(self):
        """Desenha o background através do serviço de renderização."""
        draw_background(self)

    def _draw_text(self, text: str, text_col: tuple, x: int, y: int, custom_font: pygame.font.Font = None):
        """Desenha texto através do serviço de renderização."""
        draw_text(self, text, text_col, x, y, custom_font)

    # ==================================================================
    #  Atualização e Renderização das Entidades
    # ==================================================================
    def _update_game_entities(self):
        """Atualiza entidades através do serviço de gameplay."""
        update_game_entities(self)

    def _draw_game_entities(self):
        """Desenha entidades através do serviço de renderização."""
        draw_game_entities(self)

    # ==================================================================
    #  Tratamento de eventos
    # ==================================================================
    def _handle_events(self):
        """Delega teclado e eventos de janela ao manipulador de entrada."""
        handle_events(self)

    # ==================================================================
    #  Lógica de Gameplay e Transição
    # ==================================================================
    def _update_playing(self):
        """Executa o frame de gameplay pelo serviço dedicado."""
        update_playing(self)

    def _update_level_transition(self):
        """Executa a transição de fase pelo serviço dedicado."""
        update_level_transition(self)

    # ==================================================================
    #  GAME LOOP
    # ==================================================================
    def run(self):
        """Loop principal do jogo."""
        while self.running:
            self.clock.tick(FPS)
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            # Despacho conforme estado atual
            if self.state == GameState.MENU:
                self.menu_screen.update(self.screen, self)
            elif self.state == GameState.INSTRUCTIONS:
                self.instructions_screen.update(self.screen, self)
            elif self.state == GameState.OPTIONS:
                self.options_screen.update(self.screen, self)
            elif self.state == GameState.LEVEL_SELECT:
                self.level_select_screen.update(self.screen, self)
            elif self.state == GameState.PLAYING:
                self._update_playing()
            elif self.state == GameState.PAUSE:
                self.pause_screen.update(self.screen, self)
            elif self.state == GameState.LEVEL_TRANSITION:
                self._update_level_transition()
            elif self.state == GameState.GAME_OVER:
                self.game_over_screen.update(self.screen, self)

            self._handle_events()
            pygame.display.update()

        pygame.quit()


# ======================================================================
#  INICIALIZAÇÃO DA APLICAÇÃO
# ======================================================================
def main() -> None:
    """Cria e executa uma sessão do jogo."""
    game = Game()
    game.run()
