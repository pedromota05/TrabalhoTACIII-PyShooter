"""
ui/screens/level_editor.py — Tela modular do Editor de Fases do PyShooter.

Refatorado com base em level-editor.py e nos padrões do tac3 (modules/maker),
integrando-se à máquina de estados (GameState.EDITOR), com salvamento/carregamento
de CSV em levels/, paleta de 88 tiles, rolagem e retorno ao menu principal.
"""

import os
import csv
import pygame
import button
from config import SCREEN_WIDTH, SCREEN_HEIGHT, ROWS, COLS, TILE_SIZE, TILE_TYPES, WHITE, GREEN, RED, BLACK
from asset_manager import AssetManager
from game_state import GameState


EDITOR_LOWER_MARGIN = 100
EDITOR_SIDE_MARGIN = 300
EDITOR_VIEWPORT_WIDTH = SCREEN_WIDTH - EDITOR_SIDE_MARGIN  # 900
EDITOR_TOTAL_WIDTH = SCREEN_WIDTH                         # 1200
EDITOR_TOTAL_HEIGHT = SCREEN_HEIGHT + EDITOR_LOWER_MARGIN # 740


class LevelEditorScreen:
    """Tela do editor de fases integrado à arquitetura do jogo."""

    def __init__(self, assets: AssetManager):
        self.assets = assets
        self.level = 1
        self.current_tile = 0
        self.scroll = 0
        self.scroll_speed = 1
        self.scroll_left = False
        self.scroll_right = False
        self.notification_msg = ""
        self.notification_timer = 0

        self.font = pygame.font.SysFont('Futura', 24)
        self.font_bold = pygame.font.SysFont('Futura', 26, bold=True)
        self.font_small = pygame.font.SysFont('Futura', 18)

        # Matriz vazia de tiles (16 linhas x 200 colunas)
        self.world_data: list[list[int]] = []
        self._reset_grid()

        # Carrega lista completa de tiles para a paleta (0 a 87)
        self.img_list: list[pygame.Surface] = []
        self._init_tile_images()

        # Botões de controle inferiores
        self._init_buttons()

        # Botões da paleta lateral
        self.tile_buttons: list[button.Button] = []
        self._init_palette_buttons()

    def _reset_grid(self) -> None:
        """Reinicia o grid vazio com chão na base."""
        self.world_data = []
        for _ in range(ROWS):
            self.world_data.append([-1] * COLS)
        for c in range(COLS):
            self.world_data[ROWS - 1][c] = 0

    def _init_tile_images(self) -> None:
        """Carrega e escala os 88 tipos de tiles (cenários, inimigos e bosses)."""
        self.img_list = []
        for x in range(TILE_TYPES):
            try:
                img = pygame.image.load(f'img/tile/{x}.png').convert_alpha()
                if x == 82:
                    scale_factor = 1.0
                    img = pygame.transform.scale(img, (int(img.get_width() * scale_factor), int(img.get_height() * scale_factor)))
                elif x in (71, 72):
                    scale_factor = 1.5
                    img = pygame.transform.scale(img, (int(img.get_width() * scale_factor), int(img.get_height() * scale_factor)))
                elif x in (78, 79, 80, 81):
                    tamanho_decor = int(TILE_SIZE * 0.6)
                    img = pygame.transform.scale(img, (tamanho_decor, tamanho_decor))
                else:
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                self.img_list.append(img)
            except Exception:
                surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
                surf.fill((100, 100, 100))
                self.img_list.append(surf)

        # Tile ID 87: Spawn do DragonBoss
        try:
            dragon_img = pygame.image.load('img/enemy/Dragon/Idle1.png').convert_alpha()
            dragon_img = dragon_img.subsurface(dragon_img.get_bounding_rect())
            dragon_img = pygame.transform.scale(
                dragon_img,
                (int(dragon_img.get_width() * 1.5), int(dragon_img.get_height() * 1.5))
            )
            self.img_list.append(dragon_img)
        except Exception:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
            surf.fill((200, 50, 50))
            self.img_list.append(surf)

    def _init_buttons(self) -> None:
        """Inicializa botões da barra inferior de ferramentas."""
        save_img = self.assets.get_image('save_btn') if 'save_btn' in self.assets.images else pygame.image.load('img/save_btn.png').convert_alpha()
        load_img = self.assets.get_image('load_btn') if 'load_btn' in self.assets.images else pygame.image.load('img/load_btn.png').convert_alpha()

        base_y = SCREEN_HEIGHT + 25
        self.save_button = button.Button(EDITOR_VIEWPORT_WIDTH // 2 - 120, base_y, save_img, 0.9)
        self.load_button = button.Button(EDITOR_VIEWPORT_WIDTH // 2 + 30, base_y, load_img, 0.9)

        # Botão de retorno ao Menu
        back_surf = pygame.Surface((140, 42), pygame.SRCALPHA)
        pygame.draw.rect(back_surf, (180, 40, 40), (0, 0, 140, 42), border_radius=6)
        pygame.draw.rect(back_surf, WHITE, (0, 0, 140, 42), 2, border_radius=6)
        text_surf = self.font_bold.render("<- Menu", True, WHITE)
        back_surf.blit(text_surf, text_surf.get_rect(center=(70, 21)))
        self.back_button = button.Button(15, base_y + 5, back_surf, 1.0)

    def _init_palette_buttons(self) -> None:
        """Cria botões em grade (6 colunas) na barra lateral direita."""
        self.tile_buttons = []
        col = 0
        row = 0
        start_x = EDITOR_VIEWPORT_WIDTH + 15
        for i, tile_img in enumerate(self.img_list):
            btn_img = tile_img
            scale = min(36 / max(1, btn_img.get_width()), 36 / max(1, btn_img.get_height()))
            scaled_img = pygame.transform.scale(btn_img, (max(1, int(btn_img.get_width() * scale)), max(1, int(btn_img.get_height() * scale))))
            
            btn_x = start_x + (45 * col)
            btn_y = 15 + (45 * row)
            self.tile_buttons.append(button.Button(btn_x, btn_y, scaled_img, 1.0))
            col += 1
            if col == 6:
                row += 1
                col = 0

    def on_enter(self, game) -> None:
        """Configura a janela para dimensões estendidas do editor."""
        game.screen = pygame.display.set_mode((EDITOR_TOTAL_WIDTH, EDITOR_TOTAL_HEIGHT))
        pygame.display.set_caption("PyShooter - Editor de Fases")
        self.scroll = 0
        self.load_level_data(self.level)

    def on_exit(self, game) -> None:
        """Restaura as dimensões originais da janela do jogo."""
        game.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("PyShooter - TACIII")

    def save_level_data(self) -> None:
        """Salva a matriz atual no arquivo CSV correspondente."""
        level_dir = 'levels'
        os.makedirs(level_dir, exist_ok=True)
        level_file = os.path.join(level_dir, f'level{self.level}_data.csv')
        try:
            with open(level_file, 'w', newline='') as f:
                writer = csv.writer(f, delimiter=',')
                for row in self.world_data:
                    writer.writerow(row)
            self.notification_msg = f"Fase {self.level} salva com sucesso!"
            self.notification_timer = 120
            print(f"[EDITOR] Dados salvos em {level_file}")
        except Exception as e:
            self.notification_msg = f"Erro ao salvar: {e}"
            self.notification_timer = 120

    def load_level_data(self, level_num: int) -> None:
        """Carrega a matriz do arquivo CSV correspondente."""
        level_file = os.path.join('levels', f'level{level_num}_data.csv')
        if not os.path.exists(level_file):
            self.notification_msg = f"Fase {level_num} não encontrada (grid resetado)."
            self.notification_timer = 120
            self._reset_grid()
            return

        try:
            self.scroll = 0
            with open(level_file, newline='') as f:
                reader = csv.reader(f, delimiter=',')
                for r_idx, row in enumerate(reader):
                    if r_idx < ROWS:
                        for c_idx, val in enumerate(row):
                            if c_idx < COLS:
                                self.world_data[r_idx][c_idx] = int(val)
            self.notification_msg = f"Fase {level_num} carregada!"
            self.notification_timer = 120
            print(f"[EDITOR] Dados carregados de {level_file}")
        except Exception as e:
            self.notification_msg = f"Erro ao carregar: {e}"
            self.notification_timer = 120

    def handle_event(self, event: pygame.event.Event, game) -> None:
        """Processa eventos de teclado exclusivos do editor."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.level += 1
                self.load_level_data(self.level)
            elif event.key == pygame.K_DOWN and self.level > 1:
                self.level -= 1
                self.load_level_data(self.level)
            elif event.key == pygame.K_LEFT:
                self.scroll_left = True
            elif event.key == pygame.K_RIGHT:
                self.scroll_right = True
            elif event.key in (pygame.K_RSHIFT, pygame.K_LSHIFT):
                self.scroll_speed = 5
            elif event.key == pygame.K_ESCAPE:
                self.on_exit(game)
                game.state = GameState.MENU

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                self.scroll_left = False
            elif event.key == pygame.K_RIGHT:
                self.scroll_right = False
            elif event.key in (pygame.K_RSHIFT, pygame.K_LSHIFT):
                self.scroll_speed = 1

    def update(self, screen: pygame.Surface, game) -> None:
        """Ciclo principal de atualização e renderização do editor."""
        # 1. Rolagem do mapa
        if self.scroll_left and self.scroll > 0:
            self.scroll -= 5 * self.scroll_speed
        if self.scroll_right and self.scroll < (COLS * TILE_SIZE) - EDITOR_VIEWPORT_WIDTH:
            self.scroll += 5 * self.scroll_speed

        # 2. Desenho do cenário de fundo e grid
        screen.fill(GREEN)
        self._draw_background(screen)
        self._draw_grid(screen)
        self._draw_tiles(screen)

        # 3. Desenho e interação com a paleta lateral
        pygame.draw.rect(screen, (35, 45, 55), (EDITOR_VIEWPORT_WIDTH, 0, EDITOR_SIDE_MARGIN, SCREEN_HEIGHT))
        pygame.draw.line(screen, WHITE, (EDITOR_VIEWPORT_WIDTH, 0), (EDITOR_VIEWPORT_WIDTH, SCREEN_HEIGHT), 2)

        for idx, btn in enumerate(self.tile_buttons):
            if btn.draw(screen):
                self.current_tile = idx

        # Destaque do tile ativo selecionado
        if 0 <= self.current_tile < len(self.tile_buttons):
            active_rect = self.tile_buttons[self.current_tile].rect
            pygame.draw.rect(screen, RED, active_rect.inflate(4, 4), 3)

        # 4. Modificação da grade pelo mouse (Pintar / Apagar)
        mouse_pos = pygame.mouse.get_pos()
        if mouse_pos[0] < EDITOR_VIEWPORT_WIDTH and mouse_pos[1] < SCREEN_HEIGHT:
            tile_col = (mouse_pos[0] + self.scroll) // TILE_SIZE
            tile_row = mouse_pos[1] // TILE_SIZE
            if 0 <= tile_row < ROWS and 0 <= tile_col < COLS:
                mouse_buttons = pygame.mouse.get_pressed()
                if mouse_buttons[0] == 1:  # Botão esquerdo: Pintar
                    self.world_data[tile_row][tile_col] = self.current_tile
                elif mouse_buttons[2] == 1:  # Botão direito: Apagar
                    self.world_data[tile_row][tile_col] = -1

        # 5. Painel Inferior de Controle
        pygame.draw.rect(
            screen, (25, 30, 35),
            (0, SCREEN_HEIGHT, EDITOR_TOTAL_WIDTH, EDITOR_LOWER_MARGIN)
        )
        pygame.draw.line(screen, (80, 90, 100), (0, SCREEN_HEIGHT), (EDITOR_TOTAL_WIDTH, SCREEN_HEIGHT), 2)

        # Botão Voltar
        if self.back_button.draw(screen):
            self.on_exit(game)
            game.state = GameState.MENU
            return

        # Botões Salvar e Carregar
        if self.save_button.draw(screen):
            self.save_level_data()
        if self.load_button.draw(screen):
            self.load_level_data(self.level)

        # Informações de Nível e Atalhos
        info_x = EDITOR_VIEWPORT_WIDTH // 2 + 200
        lvl_text = self.font_bold.render(f"Fase Atual: {self.level}", True, WHITE)
        screen.blit(lvl_text, (info_x, SCREEN_HEIGHT + 18))
        hint_text = self.font_small.render("Setas Cima/Baixo: Mudar Fase | Shift: Scroll Rápido", True, (200, 200, 200))
        screen.blit(hint_text, (info_x, SCREEN_HEIGHT + 48))

        # Mensagem temporária de notificação
        if self.notification_timer > 0:
            self.notification_timer -= 1
            notif_surf = self.font_bold.render(self.notification_msg, True, (255, 255, 100))
            screen.blit(notif_surf, (200, SCREEN_HEIGHT + 65))

    def _draw_background(self, screen: pygame.Surface) -> None:
        """Renderiza o fundo parallax no editor."""
        sky = self.assets.get_image('sky')
        mountain = self.assets.get_image('mountain')
        pine1 = self.assets.get_image('pine1')
        pine2 = self.assets.get_image('pine2')

        w = sky.get_width()
        for x in range(5):
            screen.blit(sky, ((x * w) - self.scroll * 0.5, 0))
            screen.blit(mountain, ((x * w) - self.scroll * 0.6, SCREEN_HEIGHT - mountain.get_height() - 250))
            screen.blit(pine1, ((x * w) - self.scroll * 0.7, SCREEN_HEIGHT - pine1.get_height() - 120))
            screen.blit(pine2, ((x * w) - self.scroll * 0.8, SCREEN_HEIGHT - pine2.get_height()))

    def _draw_grid(self, screen: pygame.Surface) -> None:
        """Desenha a grade de marcação do editor."""
        for c in range(COLS + 1):
            px = c * TILE_SIZE - self.scroll
            if 0 <= px <= EDITOR_VIEWPORT_WIDTH:
                pygame.draw.line(screen, (200, 200, 200, 100), (px, 0), (px, SCREEN_HEIGHT), 1)
        for r in range(ROWS + 1):
            py = r * TILE_SIZE
            pygame.draw.line(screen, (200, 200, 200, 100), (0, py), (EDITOR_VIEWPORT_WIDTH, py), 1)

    def _draw_tiles(self, screen: pygame.Surface) -> None:
        """Desenha todos os tiles colocados no mapa."""
        for r_idx, row in enumerate(self.world_data):
            for c_idx, tile_id in enumerate(row):
                if 0 <= tile_id < len(self.img_list):
                    img = self.img_list[tile_id]
                    px = (c_idx * TILE_SIZE) - self.scroll
                    py = (r_idx * TILE_SIZE) + (TILE_SIZE - img.get_height())
                    if -TILE_SIZE <= px <= EDITOR_VIEWPORT_WIDTH:
                        screen.blit(img, (px, py))
