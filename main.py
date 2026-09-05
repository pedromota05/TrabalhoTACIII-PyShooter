"""
main.py — Loop principal do PyShooter (refatorado).

Usa uma máquina de estados (GameState) para gerenciar as telas do jogo
e delega toda a lógica de entidades para entities.py.

Controles:
    A / ←   — mover para a esquerda
    D / →   — mover para a direita
    W / ↑   — pular
    Espaço  — atirar
    Q / G   — lançar granada
    ESC     — sair
"""

import csv
from enum import Enum

import pygame
from pygame import mixer

import button
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    ROWS, COLS, MAX_LEVELS,
    BG_COLOR, BLACK, PINK, WHITE, YELLOW,
    FONT_NAME, FONT_SIZE,
)
from asset_manager import AssetManager
from entities import (
    Player, Enemy, Grenade,
    HealthBar, ScreenFade, World,
)


# ======================================================================
#  GAME STATE  — enumerador dos estados da máquina de estados
# ======================================================================
class GameState(Enum):
    """Estados possíveis do jogo."""
    MENU = "menu"
    INSTRUCTIONS = "instructions"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    LEVEL_TRANSITION = "level_transition"


# ======================================================================
#  GAME  — classe principal que gerencia tudo
# ======================================================================
class Game:
    """Classe principal que encapsula o game loop, estado, grupos e UI."""

    def __init__(self):
        mixer.init()
        pygame.init()

        # ----- Display & Clock -----
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('PyShooter - TACIII')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
        self.font_bold = pygame.font.SysFont(FONT_NAME, FONT_SIZE, bold=True)

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

        # ----- Flags de input -----
        self.moving_left = False
        self.moving_right = False
        self.shoot = False
        self.grenade_input = False
        self.grenade_thrown = False

        # ----- Grupos de sprites -----
        self.enemy_group = pygame.sprite.Group()
        self.bullet_group = pygame.sprite.Group()
        self.grenade_group = pygame.sprite.Group()
        self.explosion_group = pygame.sprite.Group()
        self.item_box_group = pygame.sprite.Group()
        self.decoration_group = pygame.sprite.Group()
        self.water_group = pygame.sprite.Group()
        self.exit_group = pygame.sprite.Group()

        # ----- Efeitos de fade -----
        self.intro_fade = ScreenFade(1, BLACK, 4)
        self.death_fade = ScreenFade(2, PINK, 12)

        # ----- Botões de UI -----
        self.start_button = button.Button(
            SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 200,
            self.assets.get_image('start_btn'), 1,
        )
        self.instructions_button = button.Button(
            SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 50,
            self.assets.get_image('instructions_btn'), 1,
        )
        self.exit_button = button.Button(
            SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 100,
            self.assets.get_image('exit_btn'), 1,
        )
        self.restart_button = button.Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50,
            self.assets.get_image('restart_btn'), 2,
        )

        # ----- Objetos do jogo -----
        self.player = None
        self.health_bar = None
        self.world = None
        self._load_level(self.level)

    # ==================================================================
    #  Carregamento / Reset de nível  (DRY — única implementação)
    # ==================================================================
    def _reset_groups(self):
        """Esvazia todos os grupos de sprites."""
        self.enemy_group.empty()
        self.bullet_group.empty()
        self.grenade_group.empty()
        self.explosion_group.empty()
        self.item_box_group.empty()
        self.decoration_group.empty()
        self.water_group.empty()
        self.exit_group.empty()

    def _load_level(self, level_number):
        """Carrega um nível a partir do CSV correspondente.

        Substitui as 3 duplicações do bloco csv.reader no código original.
        """
        self._reset_groups()

        # Criar matriz vazia
        world_data = []
        for row in range(ROWS):
            r = [-1] * COLS
            world_data.append(r)

        # Ler dados do CSV
        with open(f'level{level_number}_data.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for x, row in enumerate(reader):
                for y, tile in enumerate(row):
                    world_data[x][y] = int(tile)

        # Construir o mundo e instanciar entidades
        self.world = World()
        self.player, self.health_bar = self.world.process_data(
            world_data,
            self.enemy_group,
            self.item_box_group,
            self.decoration_group,
            self.water_group,
            self.exit_group,
        )

    # ==================================================================
    #  Renderização auxiliar
    # ==================================================================
    def _draw_bg(self):
        """Desenha o background com parallax em 4 camadas."""
        self.screen.fill(BG_COLOR)
        
        if self.level == 2:
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
                self.screen.blit(sky,
                                 ((x * w) - self.bg_scroll * 0.5, 0))
                self.screen.blit(mountain,
                                 ((x * w) - self.bg_scroll * 0.6,
                                  SCREEN_HEIGHT - mountain.get_height() - 300))
                self.screen.blit(pine1,
                                 ((x * w) - self.bg_scroll * 0.7,
                                  SCREEN_HEIGHT - pine1.get_height() - 150))
                self.screen.blit(pine2,
                                 ((x * w) - self.bg_scroll * 0.8,
                                  SCREEN_HEIGHT - pine2.get_height()))

    def _draw_text(self, text, text_col, x, y, custom_font=None):
        f = custom_font if custom_font else self.font
        img = f.render(text, True, text_col)
        self.screen.blit(img, (x, y))

    def _render_game_scene(self):
        """Desenha e atualiza TODAS as entidades do jogo.

        Chamado tanto no estado PLAYING quanto no GAME_OVER para manter
        a cena visível atrás dos efeitos de fade.
        """
        # Background + Mundo
        self._draw_bg()
        self.world.draw(self.screen, self.screen_scroll)

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

        # Jogador
        self.player.update(self.enemy_group)
        self.player.draw(self.screen)

        # Inimigos
        for enemy in self.enemy_group:
            enemy.ai(
                self.player, self.screen_scroll,
                self.world.obstacle_list, self.water_group,
                self.bullet_group,
            )
            enemy.update()
            enemy.draw(self.screen)

        # Atualizar grupos de sprites
        self.bullet_group.update(
            self.screen_scroll, self.world.obstacle_list,
            self.player, self.bullet_group, self.enemy_group,
        )
        self.grenade_group.update(
            self.screen_scroll, self.world.obstacle_list,
            self.player, self.enemy_group, self.explosion_group,
        )
        self.explosion_group.update(self.screen_scroll)
        self.item_box_group.update(self.screen_scroll, self.player)
        self.decoration_group.update(self.screen_scroll)
        self.water_group.update(self.screen_scroll)
        self.exit_group.update(self.screen_scroll)

        # Desenhar grupos de sprites
        self.bullet_group.draw(self.screen)
        self.grenade_group.draw(self.screen)
        self.explosion_group.draw(self.screen)
        self.item_box_group.draw(self.screen)
        self.decoration_group.draw(self.screen)
        self.water_group.draw(self.screen)
        self.exit_group.draw(self.screen)

    # ==================================================================
    #  Tratamento de eventos
    # ==================================================================
    def _handle_events(self):
        for event in pygame.event.get():
            # Fechar janela
            if event.type == pygame.QUIT:
                self.running = False

            # Teclas pressionadas
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    self.moving_left = True
                if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    self.moving_right = True
                if event.key == pygame.K_SPACE:
                    self.shoot = True
                if event.key == pygame.K_q or event.key == pygame.K_g:
                    self.grenade_input = True
                if ((event.key == pygame.K_w or event.key == pygame.K_UP)
                        and self.player and self.player.alive):
                    self.player.jump = True
                    self.assets.get_sound('jump').play()
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.INSTRUCTIONS:
                        self.state = GameState.MENU
                    else:
                        self.running = False

            # Teclas soltas
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                    self.moving_left = False
                if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                    self.moving_right = False
                if event.key == pygame.K_SPACE:
                    self.shoot = False
                if event.key == pygame.K_q or event.key == pygame.K_g:
                    self.grenade_input = False
                    self.grenade_thrown = False

    # ==================================================================
    #  ESTADOS  — cada método cuida de um estado da máquina
    # ==================================================================
    def _update_menu(self):
        """Estado MENU: tela inicial com botões."""
        self.screen.fill(BG_COLOR)
        if self.start_button.draw(self.screen):
            self.state = GameState.PLAYING
            self.start_intro = True
        if self.instructions_button.draw(self.screen):
            self.state = GameState.INSTRUCTIONS
        if self.exit_button.draw(self.screen):
            self.running = False

    def _update_instructions(self):
        """Estado INSTRUCTIONS: exibe os controles do jogo."""
        self.screen.fill(BG_COLOR)
        
        # Criar fundo semi-transparente para as instruções
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(180) # Transparência (0-255)
        overlay.fill((0, 0, 0)) # Fundo preto
        self.screen.blit(overlay, (0, 0))
        
        # Título
        self._draw_text('CONTROLES DO JOGO', WHITE, SCREEN_WIDTH // 2 - 180, 100, self.font_bold)
        
        # Comandos
        comandos = [
            'A ou ESQUERDA : Mover para a esquerda',
            'D ou DIREITA : Mover para a direita',
            'W ou CIMA : Pular',
            'ESPAÇO : Atirar',
            'Q ou G : Lançar granada',
            'ESC : Fechar o jogo / Voltar ao menu'
        ]
        
        for i, cmd in enumerate(comandos):
            self._draw_text(cmd, WHITE, SCREEN_WIDTH // 2 - 250, 200 + (i * 40))
            
        self._draw_text('Pressione ESC para voltar', PINK, SCREEN_WIDTH // 2 - 200, 500, self.font_bold)

    def _update_playing(self):
        """Estado PLAYING: gameplay principal."""
        self._render_game_scene()

        # Efeito de abertura de fase
        if self.start_intro:
            if self.intro_fade.fade(self.screen):
                self.start_intro = False
                self.intro_fade.fade_counter = 0

        # Lógica do jogador (somente se vivo)
        if self.player.alive:
            # --- Ações de combate ---
            if self.shoot:
                self.player.shoot(self.bullet_group)
            elif (self.grenade_input and not self.grenade_thrown
                    and self.player.grenades > 0):
                grenade_obj = Grenade(
                    self.player.rect.centerx
                    + (0.5 * self.player.rect.size[0]
                       * self.player.direction),
                    self.player.rect.top,
                    self.player.direction,
                )
                self.grenade_group.add(grenade_obj)
                self.player.grenades -= 1
                self.grenade_thrown = True

            # --- Atualizar animação conforme estado ---
            if self.player.in_air:
                self.player.update_action(2)        # Jump
            elif self.moving_left or self.moving_right:
                self.player.update_action(1)        # Run
            else:
                self.player.update_action(0)        # Idle

            # --- Movimentação + scroll ---
            self.screen_scroll, level_complete = self.player.move(
                self.moving_left, self.moving_right,
                self.world.obstacle_list, self.water_group,
                self.exit_group, self.bg_scroll, self.world.level_length,
            )
            self.bg_scroll -= self.screen_scroll

            # --- Mudança de fase ---
            if level_complete:
                self.state = GameState.LEVEL_TRANSITION
        else:
            # Jogador morreu
            self.screen_scroll = 0
            self.state = GameState.GAME_OVER

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
            # Todas as fases concluídas → voltar ao menu
            self.level = 3
            self._load_level(self.level)
            self.state = GameState.MENU

    def _update_game_over(self):
        """Estado GAME_OVER: fade de morte + botão de restart."""
        self.screen_scroll = 0
        self._render_game_scene()

        if self.death_fade.fade(self.screen):
            if self.restart_button.draw(self.screen):
                self.death_fade.fade_counter = 0
                self.start_intro = True
                self.bg_scroll = 0
                self._load_level(self.level)
                self.state = GameState.PLAYING

    # ==================================================================
    #  GAME LOOP
    # ==================================================================
    def run(self):
        """Loop principal do jogo."""
        while self.running:
            self.clock.tick(FPS)

            # Despachar para o estado atual
            if self.state == GameState.MENU:
                self._update_menu()
            elif self.state == GameState.INSTRUCTIONS:
                self._update_instructions()
            elif self.state == GameState.PLAYING:
                self._update_playing()
            elif self.state == GameState.LEVEL_TRANSITION:
                self._update_level_transition()
            elif self.state == GameState.GAME_OVER:
                self._update_game_over()

            # Processar eventos (mesma posição do loop original)
            self._handle_events()

            pygame.display.update()

        pygame.quit()


# ======================================================================
#  PONTO DE ENTRADA
# ======================================================================
if __name__ == '__main__':
    game = Game()
    game.run()
