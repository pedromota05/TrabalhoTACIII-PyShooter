"""
entities/items.py — Itens coletáveis do PyShooter.
"""

import pygame
from config import (
    TILE_SIZE, HEALTH_PICKUP, AMMO_PICKUP, GRENADE_PICKUP,
)
from asset_manager import AssetManager


class ItemBox(pygame.sprite.Sprite):
    """Caixa de suprimentos coletável (Health, Ammo, Grenade, Speed)."""

    def __init__(self, item_type: str, x: int, y: int):
        super().__init__()
        self.item_type = item_type
        self.image = AssetManager().item_box_images[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2,
                            y + (TILE_SIZE - self.image.get_height()))

    def update(self, screen_scroll: int, player):
        self.rect.x += screen_scroll
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
            self.kill()
