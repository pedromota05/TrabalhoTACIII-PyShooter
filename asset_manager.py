"""
asset_manager.py — Singleton para carregamento centralizado de assets.

Evita chamadas dispersas a pygame.image.load() e pygame.mixer.Sound()
ao longo do projeto, centralizando o carregamento e oferecendo cache
para animações de personagens e frames de explosão.
"""

import os
import pygame
from config import TILE_SIZE, TILE_TYPES, SCREEN_HEIGHT, SCREEN_WIDTH, PLAYER_COLORS, BOSS_GATE_TILE


def recolor_surface(surf: pygame.Surface, target_hue: int) -> pygame.Surface:
    """Troca só os tons verdes (uniforme) pelo matiz pedido; pele e arma ficam iguais."""
    out = surf.copy()
    w, h = out.get_size()
    for x in range(w):
        for y in range(h):
            c = out.get_at((x, y))
            if c.a == 0:
                continue
            hue, sat, val, alpha = c.hsva
            if 70 <= hue <= 170 and sat >= 20:
                c.hsva = (target_hue, sat, val, alpha)
                out.set_at((x, y), c)
    return out


def create_heart_icon(size: int = 36) -> pygame.Surface:
    """Ícone de coração vermelho desenhado com pygame.draw (dois círculos + triângulo, contorno preto)."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    # Contorno preto
    r = size // 5 + 1
    c1 = (size // 3, size // 3 + 1)
    c2 = (size * 2 // 3, size // 3 + 1)
    pygame.draw.circle(surf, (0, 0, 0), c1, r)
    pygame.draw.circle(surf, (0, 0, 0), c2, r)
    pygame.draw.polygon(surf, (0, 0, 0), [
        (size // 8 - 1, size // 3 + 2),
        (size * 7 // 8 + 1, size // 3 + 2),
        (size // 2, size * 7 // 8 + 2)
    ])
    # Interior vermelho
    r_in = size // 5
    pygame.draw.circle(surf, (235, 40, 40), c1, r_in)
    pygame.draw.circle(surf, (235, 40, 40), c2, r_in)
    pygame.draw.polygon(surf, (235, 40, 40), [
        (size // 8, size // 3 + 2),
        (size * 7 // 8, size // 3 + 2),
        (size // 2, size * 7 // 8)
    ])
    return surf


def create_boss_gate_tile(size: int = TILE_SIZE) -> pygame.Surface:
    """Tile procedural do Portão de Boss: grade metálica escura com energia vermelha (pixel art).

    Desenhado só com retângulos (sem antialiasing) numa grade de 'pixels' de
    size/16, para combinar com os demais tiles em pixel art.
    """
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    p = max(1, size // 16)  # tamanho de um "pixel" da arte

    def px(x: int, y: int, w: int, h: int, color: tuple) -> None:
        pygame.draw.rect(surf, color, (x * p, y * p, w * p, h * p))

    dark, metal, light, black = (28, 30, 38), (62, 66, 80), (112, 118, 136), (10, 10, 14)
    red_dark, red, red_glow = (110, 12, 18), (210, 30, 40), (255, 120, 90)
    n = size // p  # nº de pixels por lado (16)

    # Fundo escuro translúcido (o cenário aparece levemente através da grade)
    px(0, 0, n, n, (12, 6, 10, 150))
    # Moldura superior/inferior
    px(0, 0, n, 2, dark)
    px(0, n - 2, n, 2, dark)
    px(0, 0, n, 1, metal)
    px(0, n - 1, n, 1, black)

    # Barras verticais com brilho à esquerda e sombra à direita
    for bx in (1, 5, 9, 13):
        px(bx, 1, 2, n - 2, metal)
        px(bx, 1, 1, n - 2, light)
        px(bx + 1, 1, 1, n - 2, (44, 46, 58))

    # Travessa central com faixa de energia vermelha
    mid = n // 2 - 1
    px(0, mid - 1, n, 4, dark)
    px(0, mid, n, 2, red_dark)
    px(0, mid, n, 1, red)
    for gx in range(1, n, 4):
        px(gx, mid, 1, 1, red_glow)

    # Rebites nas interseções das barras com a travessa
    for bx in (1, 5, 9, 13):
        px(bx, mid - 1, 2, 1, light)
        px(bx, mid + 2, 2, 1, black)

    # Pontas afiadas no topo das barras e brilho vermelho na base
    for bx in (1, 5, 9, 13):
        px(bx, 0, 2, 1, light)
        px(bx, n - 2, 2, 1, red_dark)
    return surf


def load_boss_gate_tile(size: int = TILE_SIZE) -> pygame.Surface:
    """Carrega img/tile/{BOSS_GATE_TILE}.png ou gera o tile proceduralmente se não existir."""
    path = f'img/tile/{BOSS_GATE_TILE}.png'
    if os.path.exists(path):
        try:
            return pygame.transform.scale(pygame.image.load(path).convert_alpha(), (size, size))
        except pygame.error:
            pass
    return create_boss_gate_tile(size)


class AssetManager:
    """Gerenciador centralizado de assets do jogo (Singleton)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.images: dict[str, pygame.Surface] = {}
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.tile_images: list[pygame.Surface] = []
        self.item_box_images: dict[str, pygame.Surface] = {}
        self._anim_cache: dict[tuple, list] = {}
        self._explosion_cache: dict[float, list] = {}

    # ------------------------------------------------------------------
    #  Carregamento principal
    # ------------------------------------------------------------------
    def load_all(self) -> None:
        """Carrega todos os assets estáticos do jogo."""
        self._load_images()
        self._load_sounds()
        self._load_music()

    # ------------------------------------------------------------------
    #  Imagens
    # ------------------------------------------------------------------
    def _load_images(self) -> None:
        # Botões em resolução NATIVA (sem pygame.transform.scale forçado).
        # Cada arte tem largura/altura próprias; a escala uniforme é aplicada
        # pela classe Button na tela que instancia o botão.
        button_files = {
            'menu_start_btn':    'img/start_button_new.png',
            'menu_multi_btn':    'img/multiplayer-removebg-preview.png',
            'menu_editor_btn':   'img/leve_editor_button_new.png',
            'menu_controls_btn': 'img/controls_button_new.png',
            'menu_options_btn':  'img/options_button_new.png',
            'editor_menu_btn':   'img/menu_button_new.png',
            'settings_btn':      'img/settings_button_new.png',
            'menu_exit_btn':     'img/exit_button_new.png',
            'restart_btn':       'img/restart_button_new.png',
            'resume_btn':        'img/resume_button_new.png',
            # Menu Multiplayer LAN
            'lan_host_btn':      'img/create_server_button_new.png',
            'lan_join_btn':      'img/conect_ip_button_new.png',
            'lan_back_btn':      'img/back_menu_button_new.png',
        }
        for key, path in button_files.items():
            self.images[key] = pygame.image.load(path).convert_alpha()

        # Aliases usados pela tela de Pause (mesma Surface; o Button cria
        # sua própria cópia escalada, então compartilhar é seguro).
        self.images['options_btn'] = self.images['menu_options_btn']
        self.images['exit_btn'] = self.images['menu_exit_btn']
        
        # Assets da tela Options
        opt_bg = pygame.image.load('img/icons/LargeBoxMenuBanner.png').convert_alpha()
        self.images['opt_bg'] = pygame.transform.scale(opt_bg, (600, 400))
        
        bar_base = pygame.image.load('img/icons/Dotted12_Base.png').convert_alpha()
        self.images['bar_base'] = pygame.transform.scale(bar_base, (400, 40))
        
        bar_fill = pygame.image.load('img/icons/Dotted12_Contents.png').convert_alpha()
        self.images['bar_fill'] = pygame.transform.scale(bar_fill, (400, 40))
        
        slider_knob = pygame.image.load('img/icons/slider_knob.png').convert_alpha()
        self.images['slider_knob'] = pygame.transform.scale(slider_knob, (30, 60))
        

        # Ícones de Áudio
        self.images['music_on'] = pygame.transform.scale(pygame.image.load('img/icons/music_on.png').convert_alpha(), (40, 40))
        self.images['music_off'] = pygame.transform.scale(pygame.image.load('img/icons/music_off.png').convert_alpha(), (40, 40))
        self.images['sound_on'] = pygame.transform.scale(pygame.image.load('img/icons/sound_on.png').convert_alpha(), (40, 40))
        self.images['sound_off'] = pygame.transform.scale(pygame.image.load('img/icons/sound_off.png').convert_alpha(), (40, 40))

        # Botões de seleção de fase (gamepads)
        for i in range(1, 5):
            self.images[f'gamepad{i}'] = pygame.image.load(f'img/icons/gamepad{i}.png').convert_alpha()

        # Spritesheets do teclado
        letters_sheet = pygame.image.load('img/icons/keyboard_letters.png').convert_alpha()
        extras_sheet = pygame.image.load('img/icons/keyboard_extras.png').convert_alpha()

        def get_key_image(sheet, x, y, width, height, scale):
            image = pygame.Surface((width, height), pygame.SRCALPHA)
            image.blit(sheet, (0, 0), (x, y, width, height))
            return pygame.transform.scale(image, (int(width * scale), int(height * scale)))

        self.keys_ui = {
            'A': get_key_image(letters_sheet, 0, 32, 16, 16, 3.5),
            'D': get_key_image(letters_sheet, 48, 32, 16, 16, 3.5),
            'W': get_key_image(letters_sheet, 96, 64, 16, 16, 3.5),
            'Q': get_key_image(letters_sheet, 0, 64, 16, 16, 3.5),
            'G': get_key_image(letters_sheet, 96, 32, 16, 16, 3.5),
            'LEFT': get_key_image(letters_sheet, 32, 0, 16, 16, 3.5),
            'RIGHT': get_key_image(letters_sheet, 48, 0, 16, 16, 3.5),
            'UP': get_key_image(letters_sheet, 0, 0, 16, 16, 3.5),
            'SPACE': get_key_image(extras_sheet, 64, 32, 32, 16, 3.5),
            'ESC': get_key_image(extras_sheet, 32, 0, 32, 16, 3.5)
        }

        # Ícones de mouse e coração para a tela de controles.
        # Escalados com transform.scale (sem suavização) para manter o pixel art nítido,
        # com altura igual à altura visível das teclas (~42 px).
        key_height = self.keys_ui['A'].get_bounding_rect().height

        def scale_to_height(image: pygame.Surface, height: int) -> pygame.Surface:
            width = max(1, round(image.get_width() * height / image.get_height()))
            return pygame.transform.scale(image, (width, height))

        mouse_left = pygame.image.load('img/icons/mouse/left.png').convert_alpha()
        mouse_right = pygame.image.load('img/icons/mouse/right.png').convert_alpha()

        heart_sheet = pygame.image.load('img/icons/heartDisplay.png').convert_alpha()
        heart_frame = heart_sheet.subsurface((0, 0, heart_sheet.get_width() // 3, heart_sheet.get_height()))
        heart_frame = heart_frame.subsurface(heart_frame.get_bounding_rect())

        self.keys_ui['MOUSE_LEFT'] = scale_to_height(mouse_left, key_height)
        self.keys_ui['MOUSE_RIGHT'] = scale_to_height(mouse_right, key_height)
        self.keys_ui['HEART'] = scale_to_height(heart_frame, key_height)

        # Botão Pause
        self.images['pause_btn'] = pygame.image.load('img/icons/pause_button.png').convert_alpha()

        # Background (parallax)
        self.images['pine1'] = pygame.image.load('img/background/pine1.png').convert_alpha()
        self.images['pine2'] = pygame.image.load('img/background/pine2.png').convert_alpha()
        self.images['mountain'] = pygame.image.load('img/background/mountain.png').convert_alpha()
        self.images['sky'] = pygame.image.load('img/background/sky_cloud.png').convert_alpha()
        
        # Background Level 2
        bg2 = pygame.image.load('img/background/back.png').convert_alpha()
        scale2 = SCREEN_HEIGHT / bg2.get_height()
        bg2 = pygame.transform.scale(bg2, (int(bg2.get_width() * scale2), SCREEN_HEIGHT))
        self.images['back'] = bg2
        
        # Background Level 4
        bg_swamp = pygame.image.load('img/background/background4.png').convert_alpha()
        scale_ratio = SCREEN_HEIGHT / bg_swamp.get_height()
        new_width = int(bg_swamp.get_width() * scale_ratio)
        self.images['bg_swamp'] = pygame.transform.scale(bg_swamp, (new_width, SCREEN_HEIGHT))


        # Tiles do cenário
        self.tile_images = []
        for x in range(TILE_TYPES):
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
            self.tile_images.append(img)

        # Portão da Arena de Chefes (tile BOSS_GATE_TILE, fora da faixa 0..TILE_TYPES-1)
        self.boss_gate_image = load_boss_gate_tile(TILE_SIZE)

        # Ícones
        self.images['bullet'] = pygame.image.load('img/icons/bullet.png').convert_alpha()
        self.images['grenade'] = pygame.image.load('img/icons/grenade.png').convert_alpha()

        # Caixas de itens
        self.images['health_box'] = pygame.image.load('img/icons/health_box.png').convert_alpha()
        self.images['ammo_box'] = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
        self.images['grenade_box'] = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
        self.images['speed_box'] = pygame.image.load('img/icons/speed_box.png').convert_alpha()
        self.images['life_box'] = create_heart_icon(36)
        self.item_box_images = {
            'Health':  self.images['health_box'],
            'Ammo':    self.images['ammo_box'],
            'Grenade': self.images['grenade_box'],
            'Speed':   self.images['speed_box'],
            'Life':    self.images['life_box'],
        }

        # Ícone da Aranha (passo 12)
        from entities.spider import spider_icon
        self.spider_icon = spider_icon(TILE_SIZE)
        self.images['spider_icon'] = self.spider_icon

    # ------------------------------------------------------------------
    #  Áudio
    # ------------------------------------------------------------------
    def _load_sounds(self) -> None:
        self.sounds['jump'] = pygame.mixer.Sound('audio/jump.wav')
        self.sounds['jump'].set_volume(0.05)
        self.sounds['shot'] = pygame.mixer.Sound('audio/shot.wav')
        self.sounds['shot'].set_volume(0.05)
        self.sounds['grenade'] = pygame.mixer.Sound('audio/grenade.wav')
        self.sounds['grenade'].set_volume(0.05)
        
        self.sounds['robot_shoot'] = pygame.mixer.Sound('audio/robot_shoot.wav')
        self.sounds['robot_shoot'].set_volume(0.05)
        
        self.sounds['skeleton_bow'] = pygame.mixer.Sound('audio/skeleton_bow.wav')
        self.sounds['skeleton_bow'].set_volume(0.05)

    def _load_music(self) -> None:
        pygame.mixer.music.load('audio/music2.mp3')
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1, 0.0, 5000)

    # ------------------------------------------------------------------
    #  Acesso público
    # ------------------------------------------------------------------
    def get_image(self, key: str) -> pygame.Surface:
        """Retorna uma imagem previamente carregada."""
        return self.images[key]

    def get_sound(self, key: str) -> pygame.mixer.Sound:
        """Retorna um efeito sonoro previamente carregado."""
        return self.sounds[key]

    def set_sfx_volume(self, volume: float) -> None:
        """Atualiza o volume de todos os efeitos sonoros."""
        for sound in self.sounds.values():
            sound.set_volume(volume)

    # ------------------------------------------------------------------
    #  Animações de personagens (cache por char_type + scale + color)
    # ------------------------------------------------------------------
    def load_character_animations(self, char_type: str, scale: float, color: int = 0) -> list:
        """Carrega (ou retorna do cache) as sprite-sheets de um personagem."""
        if char_type != 'player' or color < 0 or color >= len(PLAYER_COLORS):
            color = 0

        cache_key = (char_type, scale, color)
        if cache_key in self._anim_cache:
            return self._anim_cache[cache_key]

        if color > 0:
            target_hue = PLAYER_COLORS[color][1]
            base_animations = self.load_character_animations(char_type, scale, 0)
            recolored_list: list[list[pygame.Surface]] = []
            for anim in base_animations:
                recolored_list.append([recolor_surface(frame, target_hue) for frame in anim])
            self._anim_cache[cache_key] = recolored_list
            return recolored_list

        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        animation_list: list[list[pygame.Surface]] = []

        for animation in animation_types:
            temp_list: list[pygame.Surface] = []
            folder = f'img/{char_type}/{animation}'
            num_of_frames = len(os.listdir(folder))
            for i in range(num_of_frames):
                img = pygame.image.load(f'{folder}/{i}.png').convert_alpha()
                img = pygame.transform.scale(
                    img,
                    (int(img.get_width() * scale), int(img.get_height() * scale)),
                )
                temp_list.append(img)
            animation_list.append(temp_list)

        self._anim_cache[cache_key] = animation_list
        return animation_list

    # ------------------------------------------------------------------
    #  Frames de explosão (cache por escala)
    # ------------------------------------------------------------------
    def get_explosion_frames(self, scale: float) -> list:
        """Carrega (ou retorna do cache) os frames da animação de explosão."""
        if scale in self._explosion_cache:
            return self._explosion_cache[scale]

        frames: list[pygame.Surface] = []
        for num in range(1, 6):
            img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(
                img,
                (int(img.get_width() * scale), int(img.get_height() * scale)),
            )
            frames.append(img)

        self._explosion_cache[scale] = frames
        return frames
