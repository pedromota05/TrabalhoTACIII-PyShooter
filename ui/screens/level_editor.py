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
from config import SCREEN_WIDTH, SCREEN_HEIGHT, ROWS, COLS, TILE_SIZE, TILE_TYPES, CHECKPOINT_TILE, WHITE, GREEN, RED, BLACK, EDITOR_MENU_BTN_SCALE, FONT_NAME
from asset_manager import AssetManager
from game_state import GameState
from entities.checkpoint import CheckpointFlag
from entities.castle import Castle, FinishLine, CASTLE_THEMES


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
        self._mouse_held_from_enter = False
        self.move_mode = False
        self.dragging: tuple[int, int, int] | None = None
        self._prev_left = False

        # Histórico de ações (Desfazer / Refazer)
        self.undo_stack: list[list[list[int]]] = []
        self.redo_stack: list[list[list[int]]] = []
        self._stroke_active = False

        self.font = pygame.font.SysFont(FONT_NAME, 24)
        self.font_bold = pygame.font.SysFont(FONT_NAME, 26, bold=True)
        self.font_small = pygame.font.SysFont(FONT_NAME, 18)

        # Cache de castelo e linha de chegada por (level, r, c)
        self._castle_cache: dict[tuple[int, int, int], tuple[Castle, FinishLine]] = {}

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
        self._castle_cache.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._stroke_active = False
        self.world_data = []
        for _ in range(ROWS):
            self.world_data.append([-1] * COLS)
        for c in range(COLS):
            self.world_data[ROWS - 1][c] = 0

    def _init_tile_images(self) -> None:
        """Carrega e escala os 88 tipos de tiles (cenários, inimigos e bosses) e os novos (88 checkpoint, 89 aranha)."""
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

        # Tile ID 88: Bandeira de Checkpoint
        try:
            flag_img = CheckpointFlag(0, TILE_SIZE).image.copy()
            if flag_img.get_width() > TILE_SIZE:
                scale = TILE_SIZE / flag_img.get_width()
                flag_img = pygame.transform.scale(
                    flag_img,
                    (TILE_SIZE, int(flag_img.get_height() * scale))
                )
            self.img_list.append(flag_img)
        except Exception:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.line(surf, (70, 50, 35), (TILE_SIZE // 4, 2), (TILE_SIZE // 4, TILE_SIZE - 2), 3)
            pygame.draw.polygon(surf, (150, 150, 150), [
                (TILE_SIZE // 4 + 2, 4),
                (TILE_SIZE * 3 // 4, 4 + TILE_SIZE // 4),
                (TILE_SIZE // 4 + 2, 4 + TILE_SIZE // 2)
            ])
            self.img_list.append(surf)

        # Tile ID 89: Aranha
        try:
            from entities.spider import spider_icon
            self.img_list.append(spider_icon(TILE_SIZE))
        except Exception:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.ellipse(surf, (20, 20, 20), (TILE_SIZE // 4, TILE_SIZE // 4, TILE_SIZE // 2, TILE_SIZE // 3))
            self.img_list.append(surf)

    def _init_buttons(self) -> None:
        """Inicializa botões da barra inferior de ferramentas."""
        save_img = self.assets.get_image('save_btn') if 'save_btn' in self.assets.images else pygame.image.load('img/save_btn.png').convert_alpha()
        load_img = self.assets.get_image('load_btn') if 'load_btn' in self.assets.images else pygame.image.load('img/load_btn.png').convert_alpha()

        base_y = SCREEN_HEIGHT + 25
        self.save_button = button.Button(EDITOR_VIEWPORT_WIDTH // 2 - 120, base_y, save_img, 0.9)
        self.load_button = button.Button(EDITOR_VIEWPORT_WIDTH // 2 + 30, base_y, load_img, 0.9)

        # Botão de retorno ao Menu (escala reduzida para alinhar à altura de SAVE/LOAD)
        menu_btn_img = (
            self.assets.get_image('editor_menu_btn')
            if 'editor_menu_btn' in self.assets.images
            else pygame.image.load('img/menu_button_new.png').convert_alpha()
        )
        self.back_button = button.Button(15, 0, menu_btn_img, EDITOR_MENU_BTN_SCALE)
        self.back_button.rect.centery = self.save_button.rect.centery

        # Botão Mover (M) no painel inferior (ao lado dos botões Salvar/Carregar)
        self.move_button_rect = pygame.Rect(EDITOR_VIEWPORT_WIDTH // 2 - 260, base_y, 120, 36)
        self.move_button_rect.centery = self.save_button.rect.centery

        # Botões Desfazer e Refazer no painel inferior
        self.undo_button_rect = pygame.Rect(585, base_y, 95, 36)
        self.undo_button_rect.centery = self.save_button.rect.centery

        self.redo_button_rect = pygame.Rect(690, base_y, 95, 36)
        self.redo_button_rect.centery = self.save_button.rect.centery

    def toggle_move_mode(self) -> None:
        """Alterna o modo mover e cancela arrastos pendentes."""
        self.move_mode = not self.move_mode
        self._cancel_drag()
        status_str = "LIGADO" if self.move_mode else "DESLIGADO"
        self.notification_msg = f"Modo Mover: {status_str}"
        self.notification_timer = 120

    def _cancel_drag(self) -> None:
        """Cancela o arrasto atual devolvendo o tile à célula de origem."""
        if self.dragging is not None:
            tile_id, orig_r, orig_c = self.dragging
            self.world_data[orig_r][orig_c] = tile_id
            self.dragging = None
            self._castle_cache.clear()
            if self.undo_stack:
                self.undo_stack.pop()

    def _snapshot(self) -> None:
        """Salva o estado atual do mapa no histórico de desfazer e limpa o refazer."""
        self.undo_stack.append([row[:] for row in self.world_data])
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self) -> None:
        """Desfaz a última alteração no mapa."""
        if self.dragging is not None:
            self._cancel_drag()

        if not self.undo_stack:
            self.notification_msg = "Nada para desfazer"
            self.notification_timer = 120
            return

        self.redo_stack.append([row[:] for row in self.world_data])
        if len(self.redo_stack) > 100:
            self.redo_stack.pop(0)

        self.world_data = self.undo_stack.pop()
        self._castle_cache.clear()
        self.notification_msg = "Desfeito"
        self.notification_timer = 120

    def redo(self) -> None:
        """Refaz a última alteração desfeita no mapa."""
        if self.dragging is not None:
            self._cancel_drag()

        if not self.redo_stack:
            self.notification_msg = "Nada para refazer"
            self.notification_timer = 120
            return

        self.undo_stack.append([row[:] for row in self.world_data])
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)

        self.world_data = self.redo_stack.pop()
        self._castle_cache.clear()
        self.notification_msg = "Refeito"
        self.notification_timer = 120

    def _init_palette_buttons(self) -> None:
        """Cria botões em grade (7 colunas) na barra lateral direita (cabem os 89 tiles)."""
        self.tile_buttons = []
        col = 0
        row = 0
        start_x = EDITOR_VIEWPORT_WIDTH + 15
        dummy_door = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        for i, tile_img in enumerate(self.img_list):
            if i == 20:
                btn_img = Castle(1, dummy_door).image
            elif i == 41:
                btn_img = Castle(3, dummy_door).image
            else:
                btn_img = tile_img

            scale = min(36 / max(1, btn_img.get_width()), 36 / max(1, btn_img.get_height()))
            scaled_img = pygame.transform.scale(btn_img, (max(1, int(btn_img.get_width() * scale)), max(1, int(btn_img.get_height() * scale))))
            
            btn_x = start_x + (40 * col)
            btn_y = 15 + (40 * row)
            self.tile_buttons.append(button.Button(btn_x, btn_y, scaled_img, 1.0))
            col += 1
            if col == 7:
                row += 1
                col = 0

    def on_enter(self, game) -> None:
        """Configura a janela para dimensões estendidas do editor."""
        game.screen = pygame.display.set_mode((EDITOR_TOTAL_WIDTH, EDITOR_TOTAL_HEIGHT))
        pygame.display.set_caption("PyShooter - Editor de Fases")
        self.scroll = 0
        self._mouse_held_from_enter = pygame.mouse.get_pressed()[0] == 1
        self._prev_left = self._mouse_held_from_enter
        self._cancel_drag()
        self.load_level_data(self.level)

    def on_exit(self, game) -> None:
        """Restaura as dimensões originais da janela do jogo."""
        self._cancel_drag()
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
        self._castle_cache.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._stroke_active = False
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
            ctrl_held = bool(event.mod & pygame.KMOD_CTRL)
            shift_held = bool(event.mod & pygame.KMOD_SHIFT)

            if ctrl_held and event.key == pygame.K_z:
                if shift_held:
                    self.redo()
                else:
                    self.undo()
            elif ctrl_held and event.key == pygame.K_y:
                self.redo()
            elif event.key == pygame.K_UP:
                self._cancel_drag()
                self.level += 1
                self.load_level_data(self.level)
            elif event.key == pygame.K_DOWN and self.level > 1:
                self._cancel_drag()
                self.level -= 1
                self.load_level_data(self.level)
            elif event.key == pygame.K_LEFT:
                self.scroll_left = True
            elif event.key == pygame.K_RIGHT:
                self.scroll_right = True
            elif event.key in (pygame.K_RSHIFT, pygame.K_LSHIFT):
                self.scroll_speed = 5
            elif event.key == pygame.K_m:
                self.toggle_move_mode()
            elif event.key == pygame.K_ESCAPE:
                if self.dragging is not None:
                    self._cancel_drag()
                else:
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
        self._draw_move_overlay(screen)

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

        # 4. Modificação da grade pelo mouse (Pintar / Apagar / Mover)
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0] == 0:
            self._mouse_held_from_enter = False

        if mouse_buttons[0] == 0 and mouse_buttons[2] == 0:
            self._stroke_active = False

        left = mouse_buttons[0] == 1
        pressed = left and not self._prev_left
        released = (not left) and self._prev_left

        mouse_pos = pygame.mouse.get_pos()
        in_map_area = mouse_pos[0] < EDITOR_VIEWPORT_WIDTH and mouse_pos[1] < SCREEN_HEIGHT
        tile_col = (mouse_pos[0] + self.scroll) // TILE_SIZE if in_map_area else -1
        tile_row = mouse_pos[1] // TILE_SIZE if in_map_area else -1
        valid_cell = in_map_area and (0 <= tile_row < ROWS and 0 <= tile_col < COLS)

        if self.move_mode:
            # Botão direito durante o arrasto: _cancel_drag()
            if mouse_buttons[2] == 1 and self.dragging is not None:
                self._cancel_drag()

            # pressed sobre célula válida com tile != -1 e sem arrasto
            if not self._mouse_held_from_enter and pressed and self.dragging is None:
                if valid_cell and self.world_data[tile_row][tile_col] != -1:
                    self._snapshot()
                    tile_id = self.world_data[tile_row][tile_col]
                    self.dragging = (tile_id, tile_row, tile_col)
                    self.world_data[tile_row][tile_col] = -1

            # released com arrasto: se célula válida na área do mapa, posiciona; se soltou fora, cancela
            if released and self.dragging is not None:
                if valid_cell:
                    tile_id, orig_r, orig_c = self.dragging
                    if (tile_row, tile_col) == (orig_r, orig_c):
                        self._cancel_drag()
                    else:
                        dest_tile = self.world_data[tile_row][tile_col]
                        self.world_data[tile_row][tile_col] = tile_id
                        if dest_tile != -1:
                            self.world_data[orig_r][orig_c] = dest_tile
                        self.dragging = None
                        self._castle_cache.clear()
                        self.notification_msg = f"Objeto movido para ({tile_row}, {tile_col})"
                        self.notification_timer = 120
                else:
                    self._cancel_drag()
        else:
            # Modo normal (Pintar / Apagar)
            if not self._mouse_held_from_enter and valid_cell:
                if mouse_buttons[0] == 1:  # Botão esquerdo: Pintar
                    if self.world_data[tile_row][tile_col] != self.current_tile:
                        if not self._stroke_active:
                            self._snapshot()
                            self._stroke_active = True
                        self.world_data[tile_row][tile_col] = self.current_tile
                        self._castle_cache.clear()
                elif mouse_buttons[2] == 1:  # Botão direito: Apagar
                    if self.world_data[tile_row][tile_col] != -1:
                        if not self._stroke_active:
                            self._snapshot()
                            self._stroke_active = True
                        self.world_data[tile_row][tile_col] = -1
                        self._castle_cache.clear()

        self._prev_left = left

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

        # Botão Mover (M)
        move_btn_bg = (60, 140, 70) if self.move_mode else (70, 75, 80)
        pygame.draw.rect(screen, move_btn_bg, self.move_button_rect, border_radius=4)
        pygame.draw.rect(screen, (120, 130, 140), self.move_button_rect, 2, border_radius=4)
        move_text = self.font.render("Mover (M)", True, WHITE)
        move_text_rect = move_text.get_rect(center=self.move_button_rect.center)
        screen.blit(move_text, move_text_rect)

        if self.move_button_rect.collidepoint(mouse_pos):
            button.Button._cursor_hovered = True

        if pressed and not self._mouse_held_from_enter and self.move_button_rect.collidepoint(mouse_pos):
            self.toggle_move_mode()

        # Botões Salvar e Carregar
        if self.save_button.draw(screen):
            self.save_level_data()
        if self.load_button.draw(screen):
            self._cancel_drag()
            self.load_level_data(self.level)

        # Botão Desfazer
        undo_has_history = len(self.undo_stack) > 0
        undo_bg = (70, 75, 80) if undo_has_history else (45, 48, 52)
        undo_border = (120, 130, 140) if undo_has_history else (70, 75, 80)
        undo_text_color = WHITE if undo_has_history else (130, 135, 140)
        pygame.draw.rect(screen, undo_bg, self.undo_button_rect, border_radius=4)
        pygame.draw.rect(screen, undo_border, self.undo_button_rect, 2, border_radius=4)
        undo_text = self.font.render("Desfazer", True, undo_text_color)
        undo_text_rect = undo_text.get_rect(center=self.undo_button_rect.center)
        screen.blit(undo_text, undo_text_rect)

        if self.undo_button_rect.collidepoint(mouse_pos):
            button.Button._cursor_hovered = True

        if pressed and not self._mouse_held_from_enter and self.undo_button_rect.collidepoint(mouse_pos):
            self.undo()

        # Botão Refazer
        redo_has_history = len(self.redo_stack) > 0
        redo_bg = (70, 75, 80) if redo_has_history else (45, 48, 52)
        redo_border = (120, 130, 140) if redo_has_history else (70, 75, 80)
        redo_text_color = WHITE if redo_has_history else (130, 135, 140)
        pygame.draw.rect(screen, redo_bg, self.redo_button_rect, border_radius=4)
        pygame.draw.rect(screen, redo_border, self.redo_button_rect, 2, border_radius=4)
        redo_text = self.font.render("Refazer", True, redo_text_color)
        redo_text_rect = redo_text.get_rect(center=self.redo_button_rect.center)
        screen.blit(redo_text, redo_text_rect)

        if self.redo_button_rect.collidepoint(mouse_pos):
            button.Button._cursor_hovered = True

        if pressed and not self._mouse_held_from_enter and self.redo_button_rect.collidepoint(mouse_pos):
            self.redo()

        # Informações de Nível e Atalhos
        info_x = 810
        lvl_text = self.font_bold.render(f"Fase Atual: {self.level}", True, WHITE)
        screen.blit(lvl_text, (info_x, SCREEN_HEIGHT + 14))
        hint_text_1 = self.font_small.render("Setas Cima/Baixo: Mudar Fase | Shift: Scroll Rápido", True, (200, 200, 200))
        screen.blit(hint_text_1, (info_x, SCREEN_HEIGHT + 40))
        hint_text_2 = self.font_small.render("M: Mover objeto | Ctrl+Z/Ctrl+Y: Desfazer/Refazer", True, (200, 200, 200))
        screen.blit(hint_text_2, (info_x, SCREEN_HEIGHT + 64))

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

                    # Saídas (tiles 20 e 41) em fases temáticas: desenha castelo e linha de chegada
                    if tile_id in (20, 41) and self.level in CASTLE_THEMES:
                        cache_key = (self.level, r_idx, c_idx)
                        if cache_key not in self._castle_cache:
                            door = img.get_rect()
                            door.midtop = (
                                c_idx * TILE_SIZE + TILE_SIZE // 2,
                                r_idx * TILE_SIZE + (TILE_SIZE - img.get_height())
                            )
                            castle = Castle(self.level, door)
                            finish = FinishLine(door.centerx - 6 * TILE_SIZE, door.bottom)
                            self._castle_cache[cache_key] = (castle, finish)
                        else:
                            castle, finish = self._castle_cache[cache_key]

                        finish_rect = finish.rect.move(-self.scroll, 0)
                        castle_rect = castle.rect.move(-self.scroll, 0)

                        if finish_rect.right >= 0 and finish_rect.left <= EDITOR_VIEWPORT_WIDTH:
                            screen.blit(finish.image, finish_rect)
                        if castle_rect.right >= 0 and castle_rect.left <= EDITOR_VIEWPORT_WIDTH:
                            screen.blit(castle.image, castle_rect)

                        # Contorno fino amarelo na célula do tile 20/41 (porta)
                        if -TILE_SIZE <= px <= EDITOR_VIEWPORT_WIDTH:
                            pygame.draw.rect(screen, (255, 255, 0), (px, r_idx * TILE_SIZE, TILE_SIZE, TILE_SIZE), 1)
                    else:
                        if -TILE_SIZE <= px <= EDITOR_VIEWPORT_WIDTH:
                            screen.blit(img, (px, py))

    def _draw_move_overlay(self, screen: pygame.Surface) -> None:
        """Desenha destaques visuais do modo mover e do tile sendo arrastado."""
        if not self.move_mode:
            return

        mouse_pos = pygame.mouse.get_pos()
        in_map = mouse_pos[0] < EDITOR_VIEWPORT_WIDTH and mouse_pos[1] < SCREEN_HEIGHT
        tile_col = (mouse_pos[0] + self.scroll) // TILE_SIZE
        tile_row = mouse_pos[1] // TILE_SIZE
        valid_cell = in_map and (0 <= tile_row < ROWS and 0 <= tile_col < COLS)

        # Contorno amarelo (255, 220, 60) de 2 px na célula sob o mouse (se dentro do mapa)
        if valid_cell:
            cell_x = (tile_col * TILE_SIZE) - self.scroll
            cell_y = tile_row * TILE_SIZE
            pygame.draw.rect(screen, (255, 220, 60), (cell_x, cell_y, TILE_SIZE, TILE_SIZE), 2)

        # Durante o arrasto
        if self.dragging is not None:
            tile_id, orig_r, orig_c = self.dragging
            # Retângulo vermelho simples (2 px) na célula de origem
            orig_px = (orig_c * TILE_SIZE) - self.scroll
            orig_py = orig_r * TILE_SIZE
            if -TILE_SIZE <= orig_px <= EDITOR_VIEWPORT_WIDTH:
                pygame.draw.rect(screen, (255, 50, 50), (orig_px, orig_py, TILE_SIZE, TILE_SIZE), 2)

            # Imagem do tile arrastado desenhada semi-transparente alinhada à célula sob o mouse
            if valid_cell and 0 <= tile_id < len(self.img_list):
                img = self.img_list[tile_id]
                drag_img = img.copy()
                drag_img.set_alpha(170)
                px = (tile_col * TILE_SIZE) - self.scroll
                py = (tile_row * TILE_SIZE) + (TILE_SIZE - drag_img.get_height())
                screen.blit(drag_img, (px, py))
