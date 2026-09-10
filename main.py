"""
main.py — Ponto de entrada e loop principal do PyShooter (Refatorado).

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

import csv
import os
import pygame
from pygame import mixer

import button
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    ROWS, COLS, MAX_LEVELS, LEVELS_DIR,
    BG_COLOR, BLACK, WHITE, YELLOW,
    FONT_NAME, FONT_SIZE,
)
from asset_manager import AssetManager
from game_state import GameState
from entities import (
    Grenade,
    DragonBoss,
    ScreenFade,
    World,
)
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
        """Esvazia todos os grupos de sprites."""
        self.enemy_group.empty()
        self.boss_group.empty()
        self.bullet_group.empty()
        self.grenade_group.empty()
        self.explosion_group.empty()
        self.item_box_group.empty()
        self.decoration_group.empty()
        self.water_group.empty()
        self.exit_group.empty()

    def _load_level(self, level_number: int):
        """Carrega um nível a partir do arquivo CSV correspondente."""
        self._reset_groups()

        world_data = []
        for row in range(ROWS):
            r = [-1] * COLS
            world_data.append(r)

        level_file = os.path.join(LEVELS_DIR, f'level{level_number}_data.csv')
        if not os.path.exists(level_file):
            level_file = f'level{level_number}_data.csv'

        with open(level_file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for x, row in enumerate(reader):
                for y, tile in enumerate(row):
                    world_data[x][y] = int(tile)

        self.world = World()
        self.player, self.health_bar = self.world.process_data(
            world_data,
            self.enemy_group,
            self.item_box_group,
            self.decoration_group,
            self.water_group,
            self.exit_group,
            self.boss_group,
            level_number,
        )

    # ==================================================================
    #  Renderização auxiliar
    # ==================================================================
    def _draw_bg(self):
        """Desenha o background com parallax em camadas conforme a fase."""
        self.screen.fill(BG_COLOR)

        if self.level == 4:
            bg_swamp = self.assets.get_image('bg_swamp')
            swamp_width = bg_swamp.get_width()
            for i in range(5):
                self.screen.blit(bg_swamp, ((i * swamp_width) - self.bg_scroll * 0.5, 0))
        elif self.level == 2:
            bg2 = self.assets.get_image('back')
            w = bg2.get_width()
            for x in range(5):
                self.screen.blit(bg2, ((x * w) - self.bg_scroll * 0.5, 0))
        else:
            sky = self.assets.get_image('sky')
            mountain = self.assets.get_image('mountain')
            pine1 = self.assets.get_image('pine1')
            pine2 = self.assets.get_image('pine2')
            w = sky.get_width()
            for x in range(5):
                self.screen.blit(sky, ((x * w) - self.bg_scroll * 0.5, 0))
                self.screen.blit(mountain, ((x * w) - self.bg_scroll * 0.6,
                                           SCREEN_HEIGHT - mountain.get_height() - 300))
                self.screen.blit(pine1, ((x * w) - self.bg_scroll * 0.7,
                                         SCREEN_HEIGHT - pine1.get_height() - 150))
                self.screen.blit(pine2, ((x * w) - self.bg_scroll * 0.8,
                                         SCREEN_HEIGHT - pine2.get_height()))

    def _draw_text(self, text: str, text_col: tuple, x: int, y: int, custom_font: pygame.font.Font = None):
        f = custom_font if custom_font else self.font
        img = f.render(text, True, text_col)
        self.screen.blit(img, (x, y))

    # ==================================================================
    #  Atualização e Renderização das Entidades
    # ==================================================================
    def _update_game_entities(self):
        """Atualiza a física e a lógica de todas as entidades ativas."""
        self.player.update(self.enemy_group)

        for enemy in self.enemy_group:
            enemy.ai(
                self.player, self.screen_scroll,
                self.world.obstacle_list, self.water_group,
                self.bullet_group,
            )
            enemy.update()

        for boss in self.boss_group:
            boss.rect.x += self.screen_scroll
            if isinstance(boss, DragonBoss):
                boss.update(
                    self.player,
                    self.world.obstacle_list,
                    bullet_group=self.bullet_group,
                )
            else:
                boss.update(self.player, self.world.obstacle_list, 0.75)

        self.bullet_group.update(
            self.screen_scroll, self.world.obstacle_list,
            self.player, self.bullet_group, self.enemy_group, self.boss_group,
        )
        self.grenade_group.update(
            self.screen_scroll, self.world.obstacle_list,
            self.player, self.enemy_group, self.explosion_group,
            self.boss_group,
        )
        self.explosion_group.update(self.screen_scroll)
        self.item_box_group.update(self.screen_scroll, self.player)
        self.decoration_group.update(self.screen_scroll)
        self.water_group.update(self.screen_scroll)
        self.exit_group.update(self.screen_scroll)

    def _draw_game_entities(self):
        """Desenha todas as entidades, mapa e interface HUD na tela."""
        self._draw_bg()
        self.world.draw(self.screen, self.screen_scroll)

        self.player.draw(self.screen)
        for enemy in self.enemy_group:
            enemy.draw(self.screen)

        for boss in self.boss_group:
            boss.draw(self.screen)
            if hasattr(boss, 'draw_health_bar'):
                boss.draw_health_bar(self.screen)

        self.bullet_group.draw(self.screen)
        self.grenade_group.draw(self.screen)
        self.explosion_group.draw(self.screen)
        self.item_box_group.draw(self.screen)
        self.decoration_group.draw(self.screen)
        self.water_group.draw(self.screen)
        self.exit_group.draw(self.screen)

        # HUD
        self.health_bar.draw(self.screen, self.player.health)
        self._draw_text('MUNIÇÃO: ', WHITE, 10, 35)
        bullet_img = self.assets.get_image('bullet')
        for x in range(self.player.ammo):
            self.screen.blit(bullet_img, (125 + (x * 10), 40))

        self._draw_text('GRANADA: ', WHITE, 10, 60)
        grenade_img = self.assets.get_image('grenade')
        for x in range(self.player.grenades):
            self.screen.blit(grenade_img, (135 + (x * 15), 60))

        if self.player.speed_boost:
            self._draw_text('SPEED BOOST!', YELLOW, 10, 85, self.font_bold)

    # ==================================================================
    #  Tratamento de eventos
    # ==================================================================
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    self.moving_left = True
                if event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.moving_right = True
                if event.key == pygame.K_SPACE:
                    self.shoot = True
                if event.key in (pygame.K_q, pygame.K_g):
                    self.grenade_input = True
                if event.key in (pygame.K_w, pygame.K_UP) and self.player and self.player.alive:
                    self.player.jump = True
                    self.assets.get_sound('jump').play()
                if event.key == pygame.K_ESCAPE:
                    if self.state in (GameState.INSTRUCTIONS, GameState.LEVEL_SELECT):
                        self.state = GameState.MENU
                    elif self.state == GameState.OPTIONS:
                        self.state = self.previous_state if self.previous_state else GameState.MENU
                    elif self.state == GameState.PLAYING:
                        self.state = GameState.PAUSE
                    elif self.state == GameState.PAUSE:
                        self.state = GameState.PLAYING
                    else:
                        self.running = False

            if event.type == pygame.KEYUP:
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    self.moving_left = False
                if event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.moving_right = False
                if event.key == pygame.K_SPACE:
                    self.shoot = False
                if event.key in (pygame.K_q, pygame.K_g):
                    self.grenade_input = False
                    self.grenade_thrown = False

    # ==================================================================
    #  Lógica de Gameplay e Transição
    # ==================================================================
    def _update_playing(self):
        """Estado PLAYING: gameplay ativo."""
        self._update_game_entities()
        self._draw_game_entities()

        if self.start_intro:
            if self.intro_fade.fade(self.screen):
                self.start_intro = False
                self.intro_fade.fade_counter = 0

        if self.player.alive:
            if self.shoot:
                self.player.shoot(self.bullet_group)
            elif (self.grenade_input and not self.grenade_thrown
                    and self.player.grenades > 0):
                grenade_obj = Grenade(
                    self.player.rect.centerx + (0.5 * self.player.rect.size[0] * self.player.direction),
                    self.player.rect.top,
                    self.player.direction,
                )
                self.grenade_group.add(grenade_obj)
                self.player.grenades -= 1
                self.grenade_thrown = True

            # Atualizar ação de animação do jogador
            if self.player.in_air:
                self.player.update_action(2)  # Jump
            elif self.moving_left or self.moving_right:
                self.player.update_action(1)  # Run
            else:
                self.player.update_action(0)  # Idle

            # Movimentação e scroll da câmera
            self.screen_scroll, level_complete = self.player.move(
                self.moving_left, self.moving_right,
                self.world.obstacle_list, self.water_group,
                self.exit_group, self.bg_scroll, self.world.level_length,
                self.world.ramp_list,
            )
            self.bg_scroll -= self.screen_scroll

            if level_complete:
                self.state = GameState.LEVEL_TRANSITION
        else:
            self.screen_scroll = 0
            self.state = GameState.GAME_OVER

        if self.pause_button.draw(self.screen):
            self.state = GameState.PAUSE

    def _update_level_transition(self):
        """Estado LEVEL_TRANSITION: carrega a próxima fase."""
        self.screen.fill(BLACK)
        self.start_intro = True
        self.level += 1
        self.bg_scroll = 0
        if self.level <= MAX_LEVELS:
            self._load_level(self.level)
            self.state = GameState.PLAYING
        else:
            self.level = 3
            self._load_level(self.level)
            self.state = GameState.MENU

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
#  PONTO DE ENTRADA
# ======================================================================
if __name__ == '__main__':
    game = Game()
    game.run()
