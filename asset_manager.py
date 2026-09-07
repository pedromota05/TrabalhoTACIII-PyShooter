"""
asset_manager.py — Singleton para carregamento centralizado de assets.

Evita chamadas dispersas a pygame.image.load() e pygame.mixer.Sound()
ao longo do projeto, centralizando o carregamento e oferecendo cache
para animações de personagens e frames de explosão.
"""

import os
import pygame
from config import TILE_SIZE, TILE_TYPES, SCREEN_HEIGHT


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
        # Botões
        self.images['start_btn'] = pygame.transform.scale(pygame.image.load('img/start_button.png').convert_alpha(), (280, 80))
        self.images['instructions_btn'] = pygame.transform.scale(pygame.image.load('img/controls_button.png').convert_alpha(), (280, 80))
        self.images['exit_btn'] = pygame.transform.scale(pygame.image.load('img/exit_button.png').convert_alpha(), (280, 80))
        self.images['resume_btn'] = pygame.transform.scale(pygame.image.load('img/resume_button.png').convert_alpha(), (280, 80))
        self.images['options_btn'] = pygame.transform.scale(pygame.image.load('img/options_button.png').convert_alpha(), (280, 80))
        
        self.images['restart_btn'] = pygame.image.load('img/restart_btn.png').convert_alpha()

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

        # Tiles do cenário
        self.tile_images = []
        for x in range(TILE_TYPES):
            img = pygame.image.load(f'img/tile/{x}.png')
            img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
            self.tile_images.append(img)

        # Ícones
        self.images['bullet'] = pygame.image.load('img/icons/bullet.png').convert_alpha()
        self.images['grenade'] = pygame.image.load('img/icons/grenade.png').convert_alpha()

        # Caixas de itens
        self.images['health_box'] = pygame.image.load('img/icons/health_box.png').convert_alpha()
        self.images['ammo_box'] = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
        self.images['grenade_box'] = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
        self.images['speed_box'] = pygame.image.load('img/icons/speed_box.png').convert_alpha()
        self.item_box_images = {
            'Health':  self.images['health_box'],
            'Ammo':    self.images['ammo_box'],
            'Grenade': self.images['grenade_box'],
            'Speed':   self.images['speed_box'],
        }

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

    # ------------------------------------------------------------------
    #  Animações de personagens (cache por char_type + scale)
    # ------------------------------------------------------------------
    def load_character_animations(self, char_type: str, scale: float) -> list:
        """Carrega (ou retorna do cache) as sprite-sheets de um personagem."""
        cache_key = (char_type, scale)
        if cache_key in self._anim_cache:
            return self._anim_cache[cache_key]

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
