"""
entities/combat/projectiles.py — Projéteis e efeitos de combate do PyShooter.

Contém as classes:
    - Bullet (tiro comum do jogador e soldados inimigos)
    - Grenade (granada lançada pelo jogador)
    - Explosion (efeito visual e temporal da explosão da granada)
    - RobotBullet (orbe de energia disparado pelo RobotEnemy)
    - Arrow (flecha disparada pelo SkeletonEnemy)
    - DragonFire (bola de fogo disparada pelo DragonBoss)
"""

import math
import pygame
from config import (
    GRAVITY, SCREEN_WIDTH, SCREEN_HEIGHT,
    BULLET_SPEED, BULLET_DAMAGE_TO_ENEMY, BULLET_DAMAGE_TO_PLAYER,
    GRENADE_SPEED, GRENADE_INITIAL_VEL_Y, GRENADE_TIMER,
    GRENADE_DAMAGE, GRENADE_BLAST_RADIUS,
    EXPLOSION_SPEED, EXPLOSION_SCALE,
)
from asset_manager import AssetManager


# ======================================================================
#  BULLET
# ======================================================================
class Bullet(pygame.sprite.Sprite):
    """Projétil linear padrão disparado pelo jogador e por soldados inimigos."""

    def __init__(self, x: float, y: float, direction: int):
        super().__init__()
        self.speed = BULLET_SPEED
        self.image = AssetManager().get_image('bullet')
        self.rect = self.image.get_rect()
        self.rect.center = (int(x), int(y))
        self.direction = direction
        self.has_hit = False
        self.hit_timer = 0

    def update(self, screen_scroll: int, obstacle_list: list, player,
               bullet_group, enemy_group, boss_group=None):
        # Lógica de Atraso de Destruição (Kill Delay)
        if self.has_hit:
            self.hit_timer += 1
            if self.hit_timer > 2:
                self.kill()
            # A bala acompanha o scroll da tela enquanto congela para feedback visual
            self.rect.x += screen_scroll
            return

        # Movimento normal
        self.rect.x += (self.direction * self.speed) + screen_scroll

        # Fora da tela
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
            return

        # Colisão com tiles
        for tile in obstacle_list:
            if tile[1].colliderect(self.rect):
                self.has_hit = True
                break

        # Colisão com jogador
        if not self.has_hit and pygame.sprite.collide_rect(self, player):
            if player.alive and getattr(player, 'invincible', 0) == 0:
                player.health -= BULLET_DAMAGE_TO_PLAYER
                player.invincible = 60  # Garante frames de invencibilidade para o player
                self.has_hit = True

        # Colisão com inimigos
        if not self.has_hit:
            for enemy in enemy_group:
                if pygame.sprite.collide_rect(self, enemy):
                    if enemy.alive:
                        enemy.health -= BULLET_DAMAGE_TO_ENEMY
                        # Feedback visual de hit (se a animação 4 "Hurt" existir)
                        if hasattr(enemy, 'animation_list') and len(enemy.animation_list) > 4:
                            enemy.update_action(4)
                        self.has_hit = True
                        break

        # Colisão com Bosses
        if not self.has_hit and boss_group:
            boss_hit_list = pygame.sprite.spritecollide(self, boss_group, False)
            for boss in boss_hit_list:
                if boss.alive:
                    self.kill()  # Bala some
                    boss.health -= 25
                    if boss.health <= 0:
                        boss.health = 0
                        boss.alive = False
                        boss.update_action(3)  # Troca para o estado 'Death'
                    self.has_hit = True
                    break


# ======================================================================
#  EXPLOSION
# ======================================================================
class Explosion(pygame.sprite.Sprite):
    """Animação temporizada da explosão da granada."""

    def __init__(self, x: float, y: float, scale: float):
        super().__init__()
        self.images = AssetManager().get_explosion_frames(scale)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (int(x), int(y))
        self.counter = 0

    def update(self, screen_scroll: int):
        self.rect.x += screen_scroll
        self.counter += 1
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]


# ======================================================================
#  GRENADE
# ======================================================================
class Grenade(pygame.sprite.Sprite):
    """Granada com trajetória parabólica, ricochete e dano em área."""

    def __init__(self, x: float, y: float, direction: int):
        super().__init__()
        self.timer = GRENADE_TIMER
        self.vel_y = GRENADE_INITIAL_VEL_Y
        self.speed = GRENADE_SPEED
        self.image = AssetManager().get_image('grenade')
        self.rect = self.image.get_rect()
        self.rect.center = (int(x), int(y))
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    def update(self, screen_scroll: int, obstacle_list: list, player,
               enemy_group, explosion_group, boss_group=None):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y

        # Colisão com tiles
        for tile in obstacle_list:
            # Paredes (rebate)
            if tile[1].colliderect(self.rect.x + dx, self.rect.y,
                                   self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
            # Chão / teto
            if tile[1].colliderect(self.rect.x, self.rect.y + dy,
                                   self.width, self.height):
                self.speed = 0
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom

        # Atualizar posição
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        # Temporizador
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            AssetManager().get_sound('grenade').play()
            explosion = Explosion(self.rect.x, self.rect.y, EXPLOSION_SCALE)
            explosion_group.add(explosion)
            # Dano em área
            if (abs(self.rect.centerx - player.rect.centerx) < GRENADE_BLAST_RADIUS
                    and abs(self.rect.centery - player.rect.centery) < GRENADE_BLAST_RADIUS):
                player.health -= GRENADE_DAMAGE
            for enemy in enemy_group:
                if (abs(self.rect.centerx - enemy.rect.centerx) < GRENADE_BLAST_RADIUS
                        and abs(self.rect.centery - enemy.rect.centery) < GRENADE_BLAST_RADIUS):
                    enemy.health -= GRENADE_DAMAGE
                    if enemy.health <= 0:
                        enemy.health = 0
                        enemy.alive = False
                        if hasattr(enemy, 'update_action'):
                            enemy.update_action(3)
            if boss_group:
                for boss in boss_group:
                    if (abs(self.rect.centerx - boss.rect.centerx) < GRENADE_BLAST_RADIUS
                            and abs(self.rect.centery - boss.rect.centery) < GRENADE_BLAST_RADIUS):
                        boss.health -= GRENADE_DAMAGE
                        if boss.health <= 0:
                            boss.health = 0
                            boss.alive = False
                            if hasattr(boss, 'update_action'):
                                boss.update_action(3)


# ======================================================================
#  ROBOT BULLET
# ======================================================================
class RobotBullet(pygame.sprite.Sprite):
    """Orbe de energia disparado pelo RobotEnemy com vetor float."""

    def __init__(self, x: float, y: float, vel_x: float, vel_y: float):
        super().__init__()
        self.image = pygame.image.load('img/robot/Ball1.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (int(x), int(y))

        self.vel_x = vel_x
        self.vel_y = vel_y

        self.x = float(x)
        self.y = float(y)

        self.has_hit = False
        self.hit_timer = 0

    def update(self, screen_scroll: int, obstacle_list: list, player,
               bullet_group, enemy_group, boss_group=None):
        if self.has_hit:
            self.hit_timer += 1
            if self.hit_timer > 2:
                self.kill()
            self.x += screen_scroll
            self.rect.centerx = int(self.x)
            return

        # Mover
        self.x += self.vel_x + screen_scroll
        self.y += self.vel_y
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

        # Fora da tela
        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
                self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()
            return

        # Colisão com tiles
        for tile in obstacle_list:
            if tile[1].colliderect(self.rect):
                self.has_hit = True
                break

        # Colisão com jogador
        if not self.has_hit and pygame.sprite.collide_rect(player, self):
            if player.alive and getattr(player, 'invincible', 0) == 0:
                player.health -= BULLET_DAMAGE_TO_PLAYER
                player.invincible = 60
                self.has_hit = True


# ======================================================================
#  SKELETON ARROW
# ======================================================================
class Arrow(pygame.sprite.Sprite):
    """Flecha disparada pelo esqueleto com cálculo de ângulo e rotação."""

    def __init__(self, x: float, y: float, target_x: float, target_y: float):
        super().__init__()
        self.speed = int(BULLET_SPEED * 0.75)  # 25% mais lento para balanceamento

        self.original_image = pygame.image.load('img/skeleton/Arrow.png').convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (60, 30))

        # Calcular ângulo
        dx = target_x - x
        dy = target_y - y
        angle = math.atan2(dy, dx)
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed

        # Posição real em float
        self.x = float(x)
        self.y = float(y)

        # Rotacionar a imagem
        self.image = pygame.transform.rotate(self.original_image, math.degrees(-angle))
        self.rect = self.image.get_rect(center=(int(x), int(y)))

        self.has_hit = False
        self.hit_timer = 0

    def update(self, screen_scroll: int, obstacle_list: list, player,
               bullet_group, enemy_group, boss_group=None):
        if self.has_hit:
            self.hit_timer += 1
            if self.hit_timer > 2:
                self.kill()
            self.x += screen_scroll
            self.rect.centerx = int(self.x)
            return

        # Mover
        self.x += self.dx + screen_scroll
        self.y += self.dy
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)

        # Fora da tela
        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
                self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()
            return

        # Colisão com tiles
        for tile in obstacle_list:
            if tile[1].colliderect(self.rect):
                self.has_hit = True
                break

        # Colisão com jogador
        if not self.has_hit and pygame.sprite.collide_rect(player, self):
            if player.alive and getattr(player, 'invincible', 0) == 0:
                player.health -= BULLET_DAMAGE_TO_PLAYER
                player.invincible = 60
                self.has_hit = True


# ======================================================================
#  DRAGON FIRE
# ======================================================================
class DragonFire(pygame.sprite.Sprite):
    """Projétil animado disparado pelo DragonBoss."""

    def __init__(self, x: float, y: float, target_x: float, target_y: float, scale: float = 1.5):
        super().__init__()

        self.animation_list = []
        for frame_number in range(1, 7):
            image = pygame.image.load(
                f'img/enemy/Dragon/Fire_Attack{frame_number}.png'
            ).convert_alpha()
            image = image.subsurface(image.get_bounding_rect())
            image = pygame.transform.scale(
                image,
                (int(image.get_width() * scale),
                 int(image.get_height() * scale))
            )
            self.animation_list.append(image)

        self.frame_index = 0
        self.animation_timer = pygame.time.get_ticks()
        self.animation_cooldown = 80
        self.image = self.animation_list[self.frame_index]
        self.rect = self.image.get_rect(center=(int(x), int(y)))

        self.x = float(x)
        self.y = float(y)
        distance = math.hypot(target_x - x, target_y - y)
        if distance == 0:
            self.vel_x = 0.0
            self.vel_y = 0.0
        else:
            self.vel_x = (target_x - x) / distance * 6
            self.vel_y = (target_y - y) / distance * 6

    def update(self, screen_scroll: int, obstacle_list: list, player,
               bullet_group, enemy_group, boss_group=None):
        self.x += self.vel_x + screen_scroll
        self.y += self.vel_y
        self.rect.center = (int(self.x), int(self.y))

        if pygame.time.get_ticks() - self.animation_timer > self.animation_cooldown:
            self.animation_timer = pygame.time.get_ticks()
            self.frame_index = (self.frame_index + 1) % len(self.animation_list)
            center = self.rect.center
            self.image = self.animation_list[self.frame_index]
            self.rect = self.image.get_rect(center=center)

        if (self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or
                self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT):
            self.kill()
            return

        for tile in obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
                return

        if pygame.sprite.collide_rect(self, player):
            if player.alive and getattr(player, 'invincible', 0) == 0:
                player.health -= BULLET_DAMAGE_TO_PLAYER
                player.invincible = 60
            self.kill()
