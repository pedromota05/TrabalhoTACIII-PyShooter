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
    LEVEL_SELECT = "level_select"
    PLAYING = "playing"
    PAUSE = "pause"
    OPTIONS = "options"
    GAME_OVER = "game_over"
    LEVEL_TRANSITION = "level_transition"


# ======================================================================
#  UTILITÁRIOS
# ======================================================================
def render_text_with_spacing(text, font, color, spacing):
    """Renderiza texto adicionando um espaçamento customizado entre as letras (letter spacing)."""
    # Calcula a largura total da superfície necessária
    total_width = sum([font.size(char)[0] for char in text]) + spacing * (len(text) - 1)
    height = font.size(text)[1]

    # Cria uma superfície transparente
    surface = pygame.Surface((total_width, height), pygame.SRCALPHA)

    current_x = 0
    for char in text:
        char_surface = font.render(char, True, color)
        surface.blit(char_surface, (current_x, 0))
        current_x += char_surface.get_width() + spacing

    return surface

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
        # A largura verdadeira dos botões escalados no AssetManager é 280
        btn_width = 280
        center_x = SCREEN_WIDTH // 2 - btn_width // 2
        center_y = SCREEN_HEIGHT // 2
        
        self.start_button = button.Button(
            center_x, center_y - 120,
            self.assets.get_image('start_btn'), 1,
        )
        self.instructions_button = button.Button(
            center_x, center_y,
            self.assets.get_image('instructions_btn'), 1,
        )
        self.exit_button = button.Button(
            center_x, center_y + 120,
            self.assets.get_image('exit_btn'), 1,
        )
        self.restart_button = button.Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50,
            self.assets.get_image('restart_btn'), 2,
        )

        # Botões de seleção de fase (gamepads alinhados no centro)
        self.level_buttons: list[button.Button] = []
        gamepad_spacing = 20  # espaço entre botões
        # Calcular largura total para centralizar
        sample_img = self.assets.get_image('gamepad1')
        total_width = (sample_img.get_width() * 4) + (gamepad_spacing * 3)
        start_x = (SCREEN_WIDTH - total_width) // 2
        btn_y = SCREEN_HEIGHT // 2 - sample_img.get_height() // 2
        for i in range(1, 5):
            btn_x = start_x + (i - 1) * (sample_img.get_width() + gamepad_spacing)
            btn = button.Button(
                btn_x, btn_y,
                self.assets.get_image(f'gamepad{i}'), 1,
            )
            self.level_buttons.append(btn)
            
        # Botão de Pause no Gameplay
        # Redimensiona para 40x40 se a imagem original for diferente
        pause_img = self.assets.get_image('pause_btn')
        pause_img = pygame.transform.scale(pause_img, (40, 40))
        self.pause_button = button.Button(SCREEN_WIDTH - 60, 10, pause_img, 1)

        # Botão de Settings para o Menu (canto superior direito)
        self.settings_button = button.Button(SCREEN_WIDTH - 80, 20, self.assets.get_image('settings_btn'), 1)
        
        # Variáveis globais de volume e estado anterior
        self.music_vol = 12
        self.sfx_vol = 12
        self.previous_state = None

        # Botões do Menu de Pause
        self.pause_resume_btn = button.Button(center_x, center_y - 120, self.assets.get_image('resume_btn'), 1)
        self.pause_options_btn = button.Button(center_x, center_y, self.assets.get_image('options_btn'), 1)
        self.pause_exit_btn = button.Button(center_x, center_y + 120, self.assets.get_image('exit_btn'), 1)

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

    def _draw_text_with_shadow(self, text, custom_font, text_color, x, y):
        # Desenha a sombra preta deslocada
        shadow_surf = custom_font.render(text, True, (0, 0, 0))
        shadow_rect = shadow_surf.get_rect(centerx=x + 3, top=y + 3)
        self.screen.blit(shadow_surf, shadow_rect)

        # Desenha o texto principal por cima
        text_surf = custom_font.render(text, True, text_color)
        text_rect = text_surf.get_rect(centerx=x, top=y)
        self.screen.blit(text_surf, text_rect)

    def _draw_volume_bar(self, x, y, current_vol, max_vol, base_img, fill_img, knob_img):
        # Desenha a base vazia
        self.screen.blit(base_img, (x, y)) 

        # Desenha o preenchimento com clipping
        fill_width = int((current_vol / max_vol) * fill_img.get_width())
        crop_rect = pygame.Rect(0, 0, fill_width, fill_img.get_height())
        self.screen.blit(fill_img, (x, y), crop_rect) 

        # Calcula a posição do Knob (centralizado verticalmente e na ponta da barra cheia)
        knob_x = x + fill_width - (knob_img.get_width() // 2)
        knob_y = y + (base_img.get_height() // 2) - (knob_img.get_height() // 2)
        self.screen.blit(knob_img, (knob_x, knob_y))

        return pygame.Rect(x, y, base_img.get_width(), base_img.get_height())

    def _update_game_entities(self):
        """Atualiza a lógica e a física de todas as entidades do jogo (Usado apenas no estado PLAYING)."""
        # Jogador
        self.player.update(self.enemy_group)

        # Inimigos
        for enemy in self.enemy_group:
            enemy.ai(
                self.player, self.screen_scroll,
                self.world.obstacle_list, self.water_group,
                self.bullet_group,
            )
            enemy.update()

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

    def _draw_game_entities(self):
        """Apenas desenha as entidades e o cenário na tela (Usado no PLAYING e no PAUSE)."""
        # Background + Mundo
        self._draw_bg()
        self.world.draw(self.screen, self.screen_scroll)

        # Jogador e Inimigos (Desenho)
        self.player.draw(self.screen)
        for enemy in self.enemy_group:
            enemy.draw(self.screen)

        # Desenhar grupos de sprites
        self.bullet_group.draw(self.screen)
        self.grenade_group.draw(self.screen)
        self.explosion_group.draw(self.screen)
        self.item_box_group.draw(self.screen)
        self.decoration_group.draw(self.screen)
        self.water_group.draw(self.screen)
        self.exit_group.draw(self.screen)

        # HUD (Por cima de tudo)
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
                    if self.state in (GameState.INSTRUCTIONS,
                                      GameState.LEVEL_SELECT):
                        self.state = GameState.MENU
                    elif self.state == GameState.OPTIONS:
                        self.state = self.previous_state if self.previous_state else GameState.MENU
                    elif self.state == GameState.PLAYING:
                        self.state = GameState.PAUSE
                    elif self.state == GameState.PAUSE:
                        self.state = GameState.PLAYING
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
        self._draw_bg()
        
        if self.start_button.draw(self.screen):
            self.state = GameState.LEVEL_SELECT
        if self.instructions_button.draw(self.screen):
            self.state = GameState.INSTRUCTIONS
        if self.exit_button.draw(self.screen):
            self.running = False
        if self.settings_button.draw(self.screen):
            self.previous_state = self.state
            self.state = GameState.OPTIONS

    def _update_options(self):
        """Estado OPTIONS: exibe o menu de opções."""
        self._draw_bg()
        
        # Fundo do Options centralizado
        opt_bg = self.assets.get_image('opt_bg')
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        bg_x = center_x - (opt_bg.get_width() // 2)
        bg_y = center_y - (opt_bg.get_height() // 2)
        self.screen.blit(opt_bg, (bg_x, bg_y))

        # Título na Aba com Letter Spacing
        options_surf = render_text_with_spacing('OPTIONS', self.font_bold, WHITE, 5)
        options_text_rect = options_surf.get_rect(topleft=(bg_x + 30, bg_y + 20))
        self.screen.blit(options_surf, options_text_rect)
        
        bar_base = self.assets.get_image('bar_base')
        bar_fill = self.assets.get_image('bar_fill')
        slider_knob = self.assets.get_image('slider_knob')
        
        bar_x = center_x - (bar_base.get_width() // 2) + 20
        
        # MUSIC
        music_y = bg_y + 140
        music_rect = self._draw_volume_bar(
            bar_x, music_y, self.music_vol, 12, bar_base, bar_fill, slider_knob
        )
        music_icon = self.assets.get_image('music_on') if self.music_vol > 0 else self.assets.get_image('music_off')
        music_icon_rect = music_icon.get_rect(center=(bar_x - 50, music_y + 20))
        self.screen.blit(music_icon, music_icon_rect)
        
        # SOUNDS
        sfx_y = bg_y + 260
        sfx_rect = self._draw_volume_bar(
            bar_x, sfx_y, self.sfx_vol, 12, bar_base, bar_fill, slider_knob
        )
        sfx_icon = self.assets.get_image('sound_on') if self.sfx_vol > 0 else self.assets.get_image('sound_off')
        sfx_icon_rect = sfx_icon.get_rect(center=(bar_x - 50, sfx_y + 20))
        self.screen.blit(sfx_icon, sfx_icon_rect)
        
        # Lógica de interação com o mouse
        pos = pygame.mouse.get_pos()
        left_click = pygame.mouse.get_pressed()[0]
        
        if left_click:
            # Lógica de arrastar a barra (permite chegar a zero real tirando o + 1)
            if music_rect.collidepoint(pos):
                self.music_vol = int(((pos[0] - music_rect.left) / music_rect.width) * 12)
                self.music_vol = max(0, min(self.music_vol, 12))
                pygame.mixer.music.set_volume(self.music_vol / 12.0)
            elif sfx_rect.collidepoint(pos):
                self.sfx_vol = int(((pos[0] - sfx_rect.left) / sfx_rect.width) * 12)
                self.sfx_vol = max(0, min(self.sfx_vol, 12))
                self.assets.set_sfx_volume(self.sfx_vol / 12.0)
            
            # Lógica de clique único nos ícones (Mute/Unmute)
            if not getattr(self, '_options_click_lock', False):
                self._options_click_lock = True
                if music_icon_rect.collidepoint(pos):
                    self.music_vol = 0 if self.music_vol > 0 else 12
                    pygame.mixer.music.set_volume(self.music_vol / 12.0)
                elif sfx_icon_rect.collidepoint(pos):
                    self.sfx_vol = 0 if self.sfx_vol > 0 else 12
                    self.assets.set_sfx_volume(self.sfx_vol / 12.0)
        else:
            self._options_click_lock = False
        
        self._draw_text_with_shadow('Pressione ESC para voltar', self.font_bold, PINK, center_x, bg_y + opt_bg.get_height() + 20)

    def _update_instructions(self):
        """Estado INSTRUCTIONS: exibe os controles do jogo."""
        self._draw_bg()
        
        # Criar fundo semi-transparente para as instruções
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(180) # Transparência (0-255)
        overlay.fill((0, 0, 0)) # Fundo preto
        self.screen.blit(overlay, (0, 0))
        
        # Título
        self._draw_text_with_shadow('CONTROLES DO JOGO', self.font_bold, WHITE, SCREEN_WIDTH // 2, 100)
        
        center_x = SCREEN_WIDTH // 2
        keys_ui = self.assets.keys_ui
        font = self.font

        # --- A ou ESQUERDA : Mover para a esquerda ---
        y_pos = 200
        desc_surf = font.render(": Mover para a esquerda", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        self.screen.blit(desc_surf, desc_rect)

        key2_rect = keys_ui['LEFT'].get_rect(midright=(center_x - 10, y_pos))
        self.screen.blit(keys_ui['LEFT'], key2_rect)

        ou_surf = font.render("ou", True, WHITE)
        ou_rect = ou_surf.get_rect(midright=(key2_rect.left - 15, y_pos))
        self.screen.blit(ou_surf, ou_rect)

        key1_rect = keys_ui['A'].get_rect(midright=(ou_rect.left - 15, y_pos))
        self.screen.blit(keys_ui['A'], key1_rect)

        # --- D ou DIREITA : Mover para a direita ---
        y_pos = 270
        desc_surf = font.render(": Mover para a direita", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        self.screen.blit(desc_surf, desc_rect)

        key2_rect = keys_ui['RIGHT'].get_rect(midright=(center_x - 10, y_pos))
        self.screen.blit(keys_ui['RIGHT'], key2_rect)

        ou_surf = font.render("ou", True, WHITE)
        ou_rect = ou_surf.get_rect(midright=(key2_rect.left - 15, y_pos))
        self.screen.blit(ou_surf, ou_rect)

        key1_rect = keys_ui['D'].get_rect(midright=(ou_rect.left - 15, y_pos))
        self.screen.blit(keys_ui['D'], key1_rect)

        # --- W ou CIMA : Pular ---
        y_pos = 340
        desc_surf = font.render(": Pular", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        self.screen.blit(desc_surf, desc_rect)

        key2_rect = keys_ui['UP'].get_rect(midright=(center_x - 10, y_pos))
        self.screen.blit(keys_ui['UP'], key2_rect)

        ou_surf = font.render("ou", True, WHITE)
        ou_rect = ou_surf.get_rect(midright=(key2_rect.left - 15, y_pos))
        self.screen.blit(ou_surf, ou_rect)

        key1_rect = keys_ui['W'].get_rect(midright=(ou_rect.left - 15, y_pos))
        self.screen.blit(keys_ui['W'], key1_rect)

        # --- ESPAÇO : Atirar ---
        y_pos = 410
        desc_surf = font.render(": Atirar", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        self.screen.blit(desc_surf, desc_rect)

        key_rect = keys_ui['SPACE'].get_rect(midright=(center_x - 10, y_pos))
        self.screen.blit(keys_ui['SPACE'], key_rect)

        # --- Q ou G : Lançar granada ---
        y_pos = 480
        desc_surf = font.render(": Lançar granada", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        self.screen.blit(desc_surf, desc_rect)

        key2_rect = keys_ui['G'].get_rect(midright=(center_x - 10, y_pos))
        self.screen.blit(keys_ui['G'], key2_rect)

        ou_surf = font.render("ou", True, WHITE)
        ou_rect = ou_surf.get_rect(midright=(key2_rect.left - 15, y_pos))
        self.screen.blit(ou_surf, ou_rect)

        key1_rect = keys_ui['Q'].get_rect(midright=(ou_rect.left - 15, y_pos))
        self.screen.blit(keys_ui['Q'], key1_rect)

        # --- ESC : Voltar ao menu ---
        y_pos = 550
        desc_surf = font.render(": Voltar ao menu", True, WHITE)
        desc_rect = desc_surf.get_rect(midleft=(center_x + 10, y_pos))
        self.screen.blit(desc_surf, desc_rect)

        key_rect = keys_ui['ESC'].get_rect(midright=(center_x - 10, y_pos))
        self.screen.blit(keys_ui['ESC'], key_rect)

    def _update_level_select(self):
        """Estado LEVEL_SELECT: exibe os botões de seleção de fase."""
        self._draw_bg()
        
        hovering_button = False

        # Título centralizado
        self._draw_text_with_shadow('SELECIONE A FASE', self.font_bold, WHITE, SCREEN_WIDTH // 2, 80)

        # Rótulos das fases acima de cada botão
        for i, btn in enumerate(self.level_buttons):
            label = f'Fase {i + 1}'
            self._draw_text_with_shadow(label, self.font, WHITE, btn.rect.centerx, btn.rect.top - 35)

        # Desenhar botões e checar cliques e hover
        for i, btn in enumerate(self.level_buttons):
            if btn.draw(self.screen):
                self.level = i + 1
                self.bg_scroll = 0
                self.start_intro = True
                self._load_level(self.level)
                self.state = GameState.PLAYING

        # Dica de voltar centralizada
        self._draw_text_with_shadow('Pressione ESC para voltar ao menu', self.font_bold, PINK, SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60)

    def _update_playing(self):
        """Estado PLAYING: gameplay principal."""
        self._update_game_entities()
        self._draw_game_entities()

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

        # Botão de Pause
        if self.pause_button.draw(self.screen):
            self.state = GameState.PAUSE

    def _update_pause(self):
        """Estado PAUSE: congela o jogo e exibe o menu de opções."""
        # 1. Continua desenhando a tela congelada do jogo SEM rodar a física/updates
        self._draw_game_entities()

        # 2. Desenha o fundo escurecido
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        # 3. Título grande centralizado
        center_y = SCREEN_HEIGHT // 2
        paused_surf = self.title_font.render('PAUSED', True, WHITE)
        paused_rect = paused_surf.get_rect(centerx=SCREEN_WIDTH // 2, top=center_y - 220)
        
        # Sombra deslocada manualmente (já que a função de sombra customizada usava centerx)
        shadow_surf = self.title_font.render('PAUSED', True, BLACK)
        shadow_rect = shadow_surf.get_rect(centerx=SCREEN_WIDTH // 2 + 4, top=center_y - 216)
        self.screen.blit(shadow_surf, shadow_rect)
        self.screen.blit(paused_surf, paused_rect)

        # 4. Botões do Menu
        if self.pause_resume_btn.draw(self.screen):
            self.state = GameState.PLAYING
            
        if self.pause_options_btn.draw(self.screen):
            self.previous_state = self.state
            self.state = GameState.OPTIONS
            
        if self.pause_exit_btn.draw(self.screen):
            self.state = GameState.LEVEL_SELECT
            # Reset de fase para não continuar de onde parou depois
            self.bg_scroll = 0
            self.start_intro = True
            self._load_level(self.level)

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
        self._update_game_entities()
        self._draw_game_entities()

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
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

            # Despachar para o estado atual
            if self.state == GameState.MENU:
                self._update_menu()
            elif self.state == GameState.INSTRUCTIONS:
                self._update_instructions()
            elif self.state == GameState.OPTIONS:
                self._update_options()
            elif self.state == GameState.LEVEL_SELECT:
                self._update_level_select()
            elif self.state == GameState.PLAYING:
                self._update_playing()
            elif self.state == GameState.PAUSE:
                self._update_pause()
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
