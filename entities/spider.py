"""
entities/spider.py — Inimigo Aranha (desenhado via código).

Aranhas são locais em cada PC (não sincronizadas via rede).
"""

import math
import pygame
from config import (
    GRAVITY, TERMINAL_VELOCITY, SCREEN_HEIGHT,
    SPIDER_HEALTH, SPIDER_DAMAGE,
)


def draw_spider_surface(direction: int = 1, tick: int = 0, hit_flash: int = 0) -> pygame.Surface:
    """Desenha a aranha em uma Surface SRCALPHA (34x22)."""
    surf = pygame.Surface((34, 22), pygame.SRCALPHA)
    cx, cy = 17, 11

    leg_color = (255, 255, 255) if hit_flash > 0 else (20, 20, 20)
    body_color = (255, 255, 255) if hit_flash > 0 else (15, 15, 15)

    # 8 pernas (4 de cada lado): oscilam com math.sin
    for i in range(4):
        offset_x = (i - 1.5) * 5.0
        knee_x = cx + offset_x * 1.3
        knee_y = cy - 4
        anim = math.sin(tick * 0.25 + i * 1.5) * 3 if tick > 0 else 0
        leg_tip_x = cx + offset_x * 1.8 + anim
        leg_tip_y = cy + 9

        # Articulação: corpo -> joelho -> ponta no chão
        pygame.draw.line(surf, leg_color, (int(cx + offset_x), int(cy)), (int(knee_x), int(knee_y)), 2)
        pygame.draw.line(surf, leg_color, (int(knee_x), int(knee_y)), (int(leg_tip_x), int(leg_tip_y)), 2)

    # Corpo oval preto 22x14
    body_rect = pygame.Rect(cx - 11, cy - 6, 22, 14)
    pygame.draw.ellipse(surf, body_color, body_rect)

    # Olhos vermelhos na frente conforme a direção
    eye_color = (255, 255, 255) if hit_flash > 0 else (255, 30, 30)
    if direction == 1:
        pygame.draw.circle(surf, eye_color, (cx + 8, cy - 1), 1.5)
        pygame.draw.circle(surf, eye_color, (cx + 8, cy + 3), 1.5)
    else:
        pygame.draw.circle(surf, eye_color, (cx - 8, cy - 1), 1.5)
        pygame.draw.circle(surf, eye_color, (cx - 8, cy + 3), 1.5)

    return surf


def spider_icon(size: int) -> pygame.Surface:
    """Ícone da aranha parada cabendo em size x size (para o AssetManager e LevelEditor)."""
    base = draw_spider_surface(direction=1, tick=0)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    # Centraliza o desenho na superfície de destino
    bx = (size - base.get_width()) // 2
    by = (size - base.get_height()) // 2
    surf.blit(base, (bx, by))
    return surf


class Spider(pygame.sprite.Sprite):
    """Inimigo Aranha: persegue o jogador, pula e ataca no contato."""

    def __init__(self, x: float, y: float):
        super().__init__()
        self.alive = True
        self.health = SPIDER_HEALTH
        self.max_health = SPIDER_HEALTH
        self.target_id = None  # aranhas são locais, sem sincronização UDP

        self.direction = 1
        self.vel_y = 0.0
        self.in_air = True
        self.jump_cooldown = 0
        self.attack_cooldown = 0
        self.death_timer = 20
        self.tick = 0
        self.hit_flash = 0

        self.image = draw_spider_surface(self.direction, self.tick, self.hit_flash)
        self.rect = pygame.Rect(0, 0, 30, 18)
        self.rect.midbottom = (int(x), int(y))

    def update(self, screen_scroll: int, player=None, obstacle_list=None):
        if obstacle_list is None:
            obstacle_list = []

        if getattr(self, 'hit_flash', 0) > 0:
            self.hit_flash -= 1

        if not self.alive:
            self.death_timer -= 1
            self.rect.x += screen_scroll
            if self.death_timer <= 0:
                self.kill()
            return

        self.tick += 1

        # Lógica de perseguição e pulo em relação ao jogador
        if player and getattr(player, 'alive', False):
            # Anda em direção ao jogador (velocidade 2)
            if player.rect.centerx < self.rect.centerx:
                self.direction = -1
            else:
                self.direction = 1

            # Pula (vel_y = -9) quando jogador está a menos de 120 px na horizontal e ela está no chão
            if self.jump_cooldown > 0:
                self.jump_cooldown -= 1
            dist_x = abs(player.rect.centerx - self.rect.centerx)
            if dist_x < 120 and not self.in_air and self.jump_cooldown == 0:
                self.vel_y = -9
                self.in_air = True
                self.jump_cooldown = 60

            # Contato com o jogador vivo e sem invincible -> causa dano
            if self.attack_cooldown > 0:
                self.attack_cooldown -= 1
            if self.attack_cooldown == 0 and self.rect.colliderect(player.rect):
                if player.alive and getattr(player, 'invincible', 0) == 0:
                    player.health -= SPIDER_DAMAGE
                    player.invincible = 60
                    self.attack_cooldown = 45

        # Física e Colisão
        dx = 2 * self.direction
        self.vel_y += GRAVITY
        if self.vel_y > TERMINAL_VELOCITY:
            self.vel_y = TERMINAL_VELOCITY
        dy = self.vel_y

        # Colisão com tiles de cenário (padrão de inimigo de standard.py)
        for tile in obstacle_list:
            # Horizontal
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height):
                dx = 0
                self.direction *= -1

            # Vertical
            if tile[1].colliderect(self.rect.x + dx, self.rect.y + dy, self.rect.width, self.rect.height):
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        self.rect.x += dx + screen_scroll
        self.rect.y += dy
        if self.rect.top > SCREEN_HEIGHT:  # caiu num buraco
            self.kill()

    def draw(self, screen: pygame.Surface):
        surf = draw_spider_surface(self.direction, self.tick, self.hit_flash)
        if not self.alive:
            surf.set_alpha(max(0, int(255 * self.death_timer / 20)))
        draw_rect = surf.get_rect(center=self.rect.center)
        screen.blit(surf, draw_rect)
