"""
entities/enemies/bosses.py — Chefes do jogo: DragonBoss e Boss (Demon).
"""

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from entities.combat.projectiles import DragonFire


# ======================================================================
#  DRAGON BOSS
# ======================================================================
class DragonBoss(pygame.sprite.Sprite):
    """Boss Dragão voador com perseguição aérea e baforada de fogo."""

    def __init__(self, x: int, y: int, scale: float = 1.5):
        super().__init__()
        self.speed = 2
        self.action = 0
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.flip = False
        self.direction = 1
        self.max_health = 150
        self.health = self.max_health
        self.alive = True
        self.last_shot_time = 0
        self.shot_frame_fired = False

        self.animation_list = []
        for prefix in ('Idle', 'Walk', 'Attack', 'Death'):
            frames = []
            for frame_number in range(1, 15):
                try:
                    image = pygame.image.load(
                        f'img/enemy/Dragon/{prefix}{frame_number}.png'
                    ).convert_alpha()
                except FileNotFoundError:
                    break
                image = image.subsurface(image.get_bounding_rect())
                image = pygame.transform.scale(
                    image,
                    (int(image.get_width() * scale),
                     int(image.get_height() * scale))
                )
                frames.append(image)
            self.animation_list.append(frames)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect(midbottom=(x, y))

    def update(self, player, obstacle_list=None, gravity=None,
               bullet_group=None, screen_scroll: int = 0):
        if not self.alive:
            self.update_animation(player, bullet_group)
            return

        distance_x = abs(player.rect.centerx - self.rect.centerx)

        if distance_x > 250:
            self.update_action(1)

            target_y = player.rect.centery - 150
            if self.rect.bottom < target_y:
                self.rect.y += 2
            elif self.rect.bottom > target_y:
                self.rect.y -= 2

            if player.rect.centerx > self.rect.centerx:
                self.rect.x += self.speed
                self.flip = False
                self.direction = 1
            else:
                self.rect.x -= self.speed
                self.flip = True
                self.direction = -1
        else:
            self.update_action(2)

            target_y = player.rect.bottom
            if self.rect.bottom < target_y:
                self.rect.y += 4
            elif self.rect.bottom > target_y:
                self.rect.y -= 2

        self.rect.x += screen_scroll
        self.update_animation(player, bullet_group)

    def update_animation(self, player, bullet_group=None):
        animation_cooldown = 100
        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx

        frame = self.animation_list[self.action][self.frame_index]
        self.image = pygame.transform.flip(frame, self.flip, False)
        self.rect = self.image.get_rect()
        self.rect.bottom = old_bottom
        self.rect.centerx = old_centerx

        now = pygame.time.get_ticks()
        if self.action == 2 and self.frame_index == 2:
            if (not self.shot_frame_fired and bullet_group is not None and
                    now - self.last_shot_time > 2000):
                bullet_group.add(DragonFire(
                    self.rect.centerx,
                    self.rect.centery,
                    player.rect.centerx,
                    player.rect.centery,
                ))
                self.last_shot_time = now
                self.shot_frame_fired = True
        elif self.action != 2 or self.frame_index != 2:
            self.shot_frame_fired = False

        if now - self.update_time > animation_cooldown:
            self.update_time = now
            self.frame_index += 1
            if self.frame_index >= len(self.animation_list[self.action]):
                if self.action == 3:
                    self.frame_index = len(self.animation_list[self.action]) - 1
                else:
                    if self.action == 2:
                        self.update_action(0)
                    self.frame_index = 0

    def update_action(self, new_action: int):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)

    def draw_health_bar(self, surface: pygame.Surface):
        if self.health > 0:
            bar_width = 80
            bar_height = 8
            x = self.rect.centerx - (bar_width // 2)
            y = self.rect.top - 15
            ratio = max(0, self.health) / self.max_health
            pygame.draw.rect(surface, (255, 0, 0),
                             (x, y, bar_width, bar_height))
            pygame.draw.rect(surface, (0, 255, 0),
                             (x, y, bar_width * ratio, bar_height))
            pygame.draw.rect(surface, (0, 0, 0),
                             (x, y, bar_width, bar_height), 1)


# ======================================================================
#  BOSS (DEMON)
# ======================================================================
class Boss(pygame.sprite.Sprite):
    """Boss Demônio com ataque corporal devastador e gravidade."""

    def __init__(self, x: int, y: int, scale: float = 1.5):
        super().__init__()
        self.speed = 2
        self.dy = 0

        # Máquina de Estados: 0='Idle', 1='Walk', 2='Attack', 3='Death'
        self.action = 0
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

        self.flip = False
        self.direction = 1

        self.max_health = 100
        self.health = self.max_health
        self.alive = True
        self.last_hit_time = 0

        self.animation_list = []
        prefixes = ['Idle', 'Walk', 'Attack', 'Death']
        for prefix in prefixes:
            temp_list = []
            for i in range(1, 15):
                try:
                    img = pygame.image.load(f'img/enemy/Demon/{prefix}{i}.png').convert_alpha()
                    bounding_box = img.get_bounding_rect()
                    img = img.subsurface(bounding_box)
                    img = pygame.transform.scale(
                        img,
                        (int(img.get_width() * scale), int(img.get_height() * scale))
                    )
                    temp_list.append(img)
                except FileNotFoundError:
                    break
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x, y)

    def update(self, player, obstacle_list: list, GRAVITY: float):
        if not self.alive:
            self.update_animation(player)
            return

        dx = 0
        dist_x = player.rect.centerx - self.rect.centerx
        abs_dist_x = abs(dist_x)

        if abs_dist_x <= 100:
            self.update_action(2)
        elif abs_dist_x < 250:
            self.update_action(1)
            dx = self.speed * self.direction
        else:
            self.update_action(0)

        if self.action != 2:
            if dist_x > 0:
                self.direction = 1
                self.flip = False
            elif dist_x < 0:
                self.direction = -1
                self.flip = True

        self.rect.x += dx
        self.dy += GRAVITY

        for tile in obstacle_list:
            if tile[1].colliderect(self.rect.x, self.rect.y + self.dy, self.rect.width, self.rect.height):
                if self.dy >= 0:
                    self.dy = 0
                    self.rect.bottom = tile[1].top

        self.rect.y += self.dy
        self.update_animation(player)

    def update_animation(self, player):
        ANIMATION_COOLDOWN = 100
        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx

        self.image = pygame.transform.flip(self.animation_list[self.action][self.frame_index], self.flip, False)
        self.rect = self.image.get_rect()

        self.rect.bottom = old_bottom
        self.rect.centerx = old_centerx

        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

            if self.action == 2 and self.frame_index in [2, 3]:
                if pygame.time.get_ticks() - self.last_hit_time > 1500:
                    dist_x_hit = abs(player.rect.centerx - self.rect.centerx)
                    if dist_x_hit <= 130:
                        olhando_direita = (not self.flip and player.rect.centerx >= self.rect.centerx)
                        olhando_esquerda = (self.flip and player.rect.centerx <= self.rect.centerx)
                        if olhando_direita or olhando_esquerda:
                            player.health -= 35
                            self.last_hit_time = pygame.time.get_ticks()

            if self.frame_index >= len(self.animation_list[self.action]):
                if self.action == 3:
                    self.frame_index = len(self.animation_list[self.action]) - 1
                else:
                    if self.action == 2:
                        self.update_action(0)
                    self.frame_index = 0

    def update_action(self, new_action: int):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)

    def draw_health_bar(self, surface: pygame.Surface):
        if self.health > 0:
            bar_width = 80
            bar_height = 8

            x = self.rect.centerx - (bar_width // 2)
            y = self.rect.top - 15

            vida_atual = max(0, self.health)
            ratio = vida_atual / self.max_health

            pygame.draw.rect(surface, (255, 0, 0), (x, y, bar_width, bar_height))
            pygame.draw.rect(surface, (0, 255, 0), (x, y, bar_width * ratio, bar_height))
            pygame.draw.rect(surface, (0, 0, 0), (x, y, bar_width, bar_height), 1)
