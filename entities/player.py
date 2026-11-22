"""
entities/player.py — Jogador (Player) do PyShooter.
"""

import math
import random
import pygame
from config import (
    JUMP_VELOCITY, SCREEN_WIDTH, SCREEN_HEIGHT,
    TILE_SIZE, SCROLL_THRESH,
    PLAYER_SCALE, PLAYER_SPEED, PLAYER_START_AMMO, PLAYER_START_GRENADES,
    DASH_SPEED, DASH_FRAMES, DASH_COOLDOWN, DASH_TRAIL,
)
from asset_manager import AssetManager
from .aim_pose import draw_aiming, muzzle_point
from .base import Character


class Player(Character):
    """Personagem controlado pelo jogador; gerencia scroll de câmera e invencibilidade."""

    def __init__(self, x: int, y: int, scale: float = PLAYER_SCALE,
                 speed: int = PLAYER_SPEED, ammo: int = PLAYER_START_AMMO,
                 grenades: int = PLAYER_START_GRENADES):
        super().__init__('player', x, y, scale, speed, ammo, grenades)
        self.scale_used = scale
        self.invincible = 0
        self.aim_angle = 0.0
        self.aim_pose = False  # liga no primeiro face_point (mira no mouse)
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_dir = 1
        self.dash_trail = []  # [imagem, flip, x, y, vida]
        self.dash_dust = []   # [x, y, raio, vida]
        self.color = -1
        from core import progress  # import local evita ciclo
        self.set_color(progress.carregar().get('cor_jogador', 0))

    def set_color(self, color: int) -> None:
        """Altera a cor do soldado e recarrega as animações correspondentes."""
        if color == self.color:
            return
        self.color = color
        assets = AssetManager()
        if self.color != 0:
            self.animation_list = assets.load_character_animations('player', self.scale_used, self.color)
        else:
            self.animation_list = assets.load_character_animations('player', self.scale_used)

        self.action = min(self.action, len(self.animation_list) - 1)
        self.frame_index = min(self.frame_index, len(self.animation_list[self.action]) - 1)
        self.image = self.animation_list[self.action][self.frame_index]

    def face_point(self, x: float, y: float) -> None:
        self.direction = 1 if x >= self.rect.centerx else -1
        self.flip = self.direction == -1
        self.aim_angle = math.atan2(y - (self.rect.centery - 5), x - self.rect.centerx)
        self.aim_pose = True

    def muzzle_pos(self) -> tuple[float, float]:
        """Ponta do cano na tela, com a arma inclinada para a mira."""
        if not self.aim_pose:
            return (self.rect.centerx + self.rect.width * 0.9 * self.direction, self.rect.centery - 5)
        return muzzle_point(self.rect, self.direction, self.aim_angle, self.scale_used)

    def start_dash(self, moving_left: bool, moving_right: bool) -> bool:
        if not (self.alive and self.dash_cooldown == 0 and self.dash_timer == 0):
            return False
        if moving_left and not moving_right:
            self.dash_dir = -1
        elif moving_right and not moving_left:
            self.dash_dir = 1
        else:
            self.dash_dir = self.direction

        self.dash_timer = DASH_FRAMES
        self.dash_cooldown = DASH_COOLDOWN
        self.invincible = max(self.invincible, DASH_FRAMES)

        mb_x, mb_y = self.rect.midbottom
        for _ in range(6):
            px = mb_x + random.uniform(-10, 10)
            py = float(mb_y)
            raio = random.uniform(4, 8)
            vida = 18
            self.dash_dust.append([px, py, raio, vida])

        AssetManager().get_sound('jump').play()
        return True

    def update(self, enemy_group=None):
        super().update()

        # Lógica de I-Frames
        if self.invincible > 0:
            self.invincible -= 1

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # Envelhecer rastro
        for item in self.dash_trail:
            item[4] -= 1
        self.dash_trail = [item for item in self.dash_trail if item[4] > 0]

        # Envelhecer poeira
        for p in self.dash_dust:
            p[3] -= 1
            p[2] += 0.4
            p[1] -= 0.5
        self.dash_dust = [p for p in self.dash_dust if p[3] > 0]

        # Dano de Contato
        if enemy_group and self.invincible == 0:
            for enemy in enemy_group:
                if type(enemy).__name__ in ('SkeletonEnemy', 'Sniper'):
                    continue  # Ignora o dano de contato passivo

                # Reduz a largura do retângulo invisível para ignorar a transparência
                hitbox_inimigo = enemy.rect.inflate(-50, -10)
                if enemy.alive and self.rect.colliderect(hitbox_inimigo):
                    self.health -= 10
                    self.invincible = 60
                    break

    def draw(self, screen: pygame.Surface):
        # Poeira
        for p in self.dash_dust:
            x, y, raio, vida = p
            alpha = int(255 * (vida / 18))
            alpha = max(0, min(255, alpha))
            r = max(1, int(raio))
            dust_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(dust_surf, (200, 190, 170, alpha), (r + 1, r + 1), r)
            screen.blit(dust_surf, (int(x - r - 1), int(y - r - 1)))

        # Rastro
        for item in self.dash_trail:
            img_item, flip_item, ix, iy, vida = item
            img = pygame.transform.flip(img_item, flip_item, False).copy()
            img.fill((90, 160, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
            alpha = int(160 * vida / (DASH_TRAIL * 2))
            img.set_alpha(max(0, min(255, alpha)))
            screen.blit(img, (ix, iy))

        # Efeito visual de piscar durante a invencibilidade (no dash ele aparece sempre)
        if self.dash_timer <= 0 and self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            return  # Pula o frame, fazendo o personagem sumir
        if self.aim_pose and self.alive and self.action != 3:
            image = pygame.transform.flip(self.image, self.flip, False)
            draw_aiming(screen, image, self.rect, self.direction, self.aim_angle, self.scale_used)
        else:
            super().draw(screen)

    def _check_environment(self, water_group):
        """Verifica perigos ambientais com hitbox perdoável para água.

        O jogador só morre se o centro do corpo estiver abaixo da
        superfície da água, evitando mortes injustas por encostar 1 pixel.
        """
        for water in water_group:
            if (water.rect.colliderect(self.rect)
                    and self.rect.centery > water.rect.top):
                self.health = 0
                break
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

    def move(self, moving_left: bool, moving_right: bool, obstacle_list: list,
             water_group, exit_group, bg_scroll: int, level_length: int,
             ramp_list: list = None, remote_players=None):
        if ramp_list is None:
            ramp_list = []

        screen_scroll = 0
        dx = 0
        dy = 0

        # Movimento horizontal constante (base)
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        if self.dash_timer > 0:
            dx = self.dash_dir * DASH_SPEED
            self.vel_y = 0
            dy = 0
            self.dash_timer -= 1
            self.dash_trail.append([self.image.copy(), self.flip, self.rect.x, self.rect.y, DASH_TRAIL * 2])
            if len(self.dash_trail) > DASH_TRAIL:
                self.dash_trail = self.dash_trail[-DASH_TRAIL:]
        else:
            # Modificador de controle no ar (Air Control)
            if self.in_air:
                dx = int(dx * 0.7)  # Reduz ganho horizontal no ar para precisão de plataformas

            # Pulo
            if self.jump and not self.in_air:
                self.vel_y = JUMP_VELOCITY
                self.jump = False
                self.in_air = True

            # Gravidade
            self._apply_gravity()
            dy += self.vel_y

        # Colisão com tiles
        dx, dy = self._check_tile_collisions(dx, dy, obstacle_list, ramp_list)

        # Colisão com o parceiro do multiplayer (hitbox estreita: ignora a arma).
        if remote_players:
            for other in remote_players:
                if not other.alive:
                    continue
                body = other.rect.inflate(-other.rect.width // 2, -6)
                if self.rect.colliderect(body):
                    continue  # já sobrepostos (ex.: renasceu ao lado): deixa sair
                if dx and self.rect.move(dx, 0).colliderect(body):
                    dx = 0
                # Cai em cima da cabeça do parceiro
                if dy > 0 and self.rect.bottom <= body.top and self.rect.move(dx, dy).colliderect(body):
                    dy = body.top - self.rect.bottom
                    self.vel_y = 0
                    self.in_air = False

        # Perigos ambientais
        self._check_environment(water_group)

        # Saída de fase
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        # Limites da tela
        if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
            dx = 0

        # Atualizar posição
        self.rect.x += dx
        self.rect.y += dy

        # Scroll da câmera
        if ((self.rect.right > SCREEN_WIDTH - SCROLL_THRESH
                and bg_scroll < (level_length * TILE_SIZE) - SCREEN_WIDTH)
                or (self.rect.left < SCROLL_THRESH
                    and bg_scroll > abs(dx))):
            self.rect.x -= dx
            screen_scroll = -dx

        if screen_scroll != 0:
            for item in self.dash_trail:
                item[2] += screen_scroll
            for p in self.dash_dust:
                p[0] += screen_scroll

        return screen_scroll, level_complete
