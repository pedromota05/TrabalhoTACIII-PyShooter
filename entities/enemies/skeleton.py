"""
entities/enemies/skeleton.py — Inimigo Esqueleto com disparo de arco e flecha.
"""

import math
import random
import pygame
from config import TILE_SIZE, ENEMY_GRENADES
from asset_manager import AssetManager
from entities.base import Character
from entities.combat.projectiles import Arrow


class SkeletonEnemy(Character):
    """Inimigo esqueleto arqueiro com linha de visão (raycasting em tiles) e tiro temporizado."""

    def __init__(self, x: int, y: int, scale: float = 0.8, speed: int = 1,
                 ammo: int = 9999, grenades: int = ENEMY_GRENADES):
        super().__init__('enemy', x, y, scale, speed, ammo, grenades)
        self.move_counter = 0
        self.vision_radius = 400
        self.idling = False
        self.idling_counter = 0
        self.flip_cooldown = 0
        self.turn_after_idle = False
        self.shot_fired = False

        # Override animation list com o extrator de sprite strips do esqueleto
        self.animation_list = []
        animations = [
            'Idle',     # action 0
            'Walk',     # action 1
            'Shot_1',   # action 2
            'Dead',     # action 3
            'Hurt'      # action 4
        ]

        for anim in animations:
            img = pygame.image.load(f'img/skeleton/{anim}.png').convert_alpha()
            frame_height = img.get_height()
            frame_width = frame_height
            num_frames = img.get_width() // frame_width

            temp_list = []
            for i in range(num_frames):
                frame = img.subsurface((i * frame_width, 0, frame_width, frame_height))
                frame = pygame.transform.scale(
                    frame,
                    (int(frame_width * scale), int(frame_height * scale))
                )
                temp_list.append(frame)
            self.animation_list.append(temp_list)

        self.action = 0
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x + TILE_SIZE // 2, y + TILE_SIZE)

        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        super().update()
        self.flip = True if self.direction == -1 else False

    def _is_edge_ahead(self, obstacle_list: list) -> bool:
        if self.in_air:
            return False
        if self.direction == 1:
            check_x = self.rect.right + 2
        else:
            check_x = self.rect.left - 2
        test_rect = pygame.Rect(check_x - 1, self.rect.bottom + 1, 2, TILE_SIZE)
        for tile in obstacle_list:
            if tile[1].colliderect(test_rect):
                return False
        return True

    def _on_horizontal_collision(self):
        if self.flip_cooldown == 0:
            self.idling = True
            self.idling_counter = 60
            self.turn_after_idle = True
            self.move_counter = 0
            self.flip_cooldown = 60

    def move(self, moving_left: bool, moving_right: bool, obstacle_list: list, water_group):
        dx = self._calculate_movement(moving_left, moving_right)
        dy = 0
        self._apply_gravity()
        dy += self.vel_y
        dx, dy = self._check_tile_collisions(dx, dy, obstacle_list)
        self._check_environment(water_group)
        self.rect.x += dx
        self.rect.y += dy

    def update_animation(self):
        super().update_animation()
        if self.frame_index == 0:
            self.shot_fired = False

    def shoot(self, bullet_group, target_x: float, target_y: float):
        """Dispara a flecha APENAS quando a animação atingir o frame correto."""
        if self.action == 2 and self.frame_index == 9 and not self.shot_fired:
            self.shot_fired = True
            spawn_x = self.rect.centerx + (self.rect.width * 0.9 * self.direction)
            spawn_y = self.rect.centery - 15

            bullet = Arrow(spawn_x, spawn_y, target_x, target_y)
            bullet_group.add(bullet)
            self.ammo -= 1
            AssetManager().get_sound('skeleton_bow').play()

    def ai(self, player, screen_scroll: int, obstacle_list: list, water_group, bullet_group):
        if self.flip_cooldown > 0:
            self.flip_cooldown -= 1

        if self.alive and player.alive:
            dist_x = player.rect.centerx - self.rect.centerx
            dist_y = player.rect.centery - self.rect.centery
            dist = math.hypot(dist_x, dist_y)

            # Linha de visão limpa
            line_of_sight = False
            if dist < self.vision_radius:
                line_of_sight = True
                p1 = self.rect.center
                p2 = player.rect.center
                for tile in obstacle_list:
                    if tile[1].clipline(p1, p2):
                        line_of_sight = False
                        break

            if line_of_sight:
                if player.rect.centerx < self.rect.centerx:
                    self.direction = -1
                else:
                    self.direction = 1

                if self.ammo > 0:
                    self.update_action(2)  # Attack (Shot_1)
                    self.shoot(bullet_group, player.rect.centerx, player.rect.centery)
                else:
                    self.update_action(0)
            else:
                if not self.idling and random.randint(1, 200) == 1:
                    self.update_action(0)
                    self.idling = True
                    self.idling_counter = 50
                    self.turn_after_idle = False

                if not self.idling:
                    if self.direction == 1:
                        moving_right = True
                        moving_left = False
                    else:
                        moving_right = False
                        moving_left = True

                    self.update_action(1)  # Walk
                    self.move(moving_left, moving_right, obstacle_list, water_group)
                    self.move_counter += 1

                    if self._is_edge_ahead(obstacle_list):
                        if self.flip_cooldown == 0:
                            self.idling = True
                            self.idling_counter = 60
                            self.turn_after_idle = True
                            self.move_counter = 0
                            self.flip_cooldown = 60
                else:
                    self.update_action(0)
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
                        if self.turn_after_idle:
                            self.direction *= -1
                            self.turn_after_idle = False

        self.rect.x += screen_scroll
