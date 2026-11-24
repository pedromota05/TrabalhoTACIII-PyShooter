"""
entities/items.py — Itens coletáveis do PyShooter.
"""

import math
import pygame
from config import (
    TILE_SIZE, HEALTH_PICKUP, AMMO_PICKUP, GRENADE_PICKUP, FONT_NAME,
)
from asset_manager import AssetManager


PICKUP_LABELS = {'Health': '+VIDA', 'Ammo': '+MUNIÇÃO', 'Grenade': '+GRANADA', 'Speed': 'VELOCIDADE!', 'Life': '+1 VIDA'}


class PickupText(pygame.sprite.Sprite):
    """Texto que sobe e some em 40 quadros quando uma caixa é pega."""
    _font = None

    def __init__(self, text: str, x: int, y: int):
        super().__init__()
        if PickupText._font is None:
            PickupText._font = pygame.font.SysFont(FONT_NAME, 20, bold=True)
        self.base = PickupText._font.render(text, True, (255, 255, 120))
        self.image = self.base.copy()
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.timer = 40

    def update(self, screen_scroll: int):
        self.rect.x += screen_scroll
        self.rect.y -= 1
        self.timer -= 1
        self.image = self.base.copy()
        self.image.set_alpha(int(255 * self.timer / 40))
        if self.timer <= 0:
            self.kill()


class ItemBox(pygame.sprite.Sprite):
    """Caixa de suprimentos coletável (Health, Ammo, Grenade, Speed)."""

    def __init__(self, item_type: str, x: int, y: int):
        super().__init__()
        self.item_type = item_type
        self.image = AssetManager().item_box_images[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2,
                            y + (TILE_SIZE - self.image.get_height()))
        # Id estável da caixa (coluna*1000 + linha): igual no Host e no cliente.
        self.item_id = (x // TILE_SIZE) * 1000 + (y // TILE_SIZE)
        self.base_y = self.rect.y
        self.bob_tick = self.item_id % 60   # fase diferente para cada caixa

    def update(self, screen_scroll: int, player, network_client=None, level: int = 0, fx_group=None):
        self.rect.x += screen_scroll
        self.bob_tick += 1
        self.rect.y = self.base_y + round(3 * math.sin(self.bob_tick * 0.08))
        if pygame.sprite.collide_rect(self, player):
            if self.item_type == 'Health':
                player.health += HEALTH_PICKUP
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += AMMO_PICKUP
            elif self.item_type == 'Grenade':
                player.grenades += GRENADE_PICKUP
            elif self.item_type == 'Speed':
                player.speed_boost = True
                player.speed = player.base_speed * 2
                player.speed_boost_timer = 300
            elif self.item_type == 'Life':
                player.pending_life_up = getattr(player, 'pending_life_up', 0) + 1
            if fx_group is not None and self.item_type != 'Life':
                fx_group.add(PickupText(PICKUP_LABELS[self.item_type], self.rect.centerx, self.rect.top))
            if network_client is not None:
                network_client.send_item_pickup(level, self.item_id)
            self.kill()
