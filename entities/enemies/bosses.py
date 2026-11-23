"""
entities/enemies/bosses.py — Chefes do jogo: DragonBoss e Boss (Demon).
"""

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, DRAGON_WAKE_RANGE
from entities.combat.projectiles import DragonFire


# ======================================================================
#  DRAGON BOSS
# ======================================================================
class DragonBoss(pygame.sprite.Sprite):
    """Boss Dragão voador com perseguição aérea e baforada de fogo."""

    def __init__(self, x: int, y: int, scale: float = 1.5):
        super().__init__()
        self.base_speed = 3.5
        self.enraged_speed = 4.5
        self.speed = self.base_speed
        self._fx = 0.0  # acumulador fracionário para movimento float sem tremulação
        self.action = 0
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.flip = False
        self.direction = 1
        self.max_health = 450
        self.health = self.max_health
        self.alive = True
        self.enraged = False
        self.hit_flash = 0
        self.last_shot_time = 0
        self.shot_frame_fired = False
        # Adormecido até o jogador chegar à Arena 2 sem Demônios vivos (ver try_activate).
        # Enquanto False: fica em Idle ancorado no cenário e ignora dano.
        self.activated = False

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

    def try_activate(self, player, can_activate: bool = True) -> bool:
        """Desperta o Dragão quando permitido e o jogador entra na Arena 2.

        Usa só distâncias relativas na tela (rect do Dragão x rect do jogador),
        então funciona com qualquer valor de screen_scroll / bg_scroll.
        Retorna True apenas no quadro em que o Dragão desperta.
        """
        if self.activated or not self.alive or not can_activate or player is None:
            return False
        near = abs(self.rect.centerx - player.rect.centerx) <= DRAGON_WAKE_RANGE
        on_screen = self.rect.left <= SCREEN_WIDTH - 60 and self.rect.right >= 60
        if near or on_screen:
            self.activated = True
            self.update_time = pygame.time.get_ticks()
            return True
        return False

    def update(self, player, obstacle_list=None, gravity=None,
               bullet_group=None, screen_scroll: int = 0,
               network_client=None, bg_scroll: int = 0,
               can_activate: bool = True):
        if not self.alive:
            self.update_animation(player, bullet_group, network_client=network_client, bg_scroll=bg_scroll)
            return

        if not self.activated:
            # Adormecido: ancorado no cenário (acompanha o scroll), em Idle,
            # sem perseguir o jogador nem disparar DragonFire.
            self.rect.x += screen_scroll
            self.update_action(0)
            self.update_animation(player, None)
            self.try_activate(player, can_activate)
            return

        if not self.enraged and self.health <= self.max_health * 0.5:
            self.enraged = True
        self.speed = self.enraged_speed if self.enraged else self.base_speed

        distance_x = abs(player.rect.centerx - self.rect.centerx)

        if distance_x > 250:
            self.update_action(1)

            target_y = player.rect.centery - 150
            if self.rect.bottom < target_y:
                self.rect.y += 2
            elif self.rect.bottom > target_y:
                self.rect.y -= 2

            step = self.speed if player.rect.centerx > self.rect.centerx else -self.speed
            self.flip = step < 0
            self.direction = -1 if step < 0 else 1
            self._fx += step
            move_x = int(self._fx)
            self._fx -= move_x
            self.rect.x += move_x
        else:
            self.update_action(2)

            # Permite que o Dragão vire caso o player passe para as costas dele
            if player.rect.centerx > self.rect.centerx:
                self.flip = False
                self.direction = 1
            else:
                self.flip = True
                self.direction = -1

            target_y = player.rect.bottom
            if self.rect.bottom < target_y:
                self.rect.y += 4
            elif self.rect.bottom > target_y:
                self.rect.y -= 2

        self.rect.x += screen_scroll
        self.update_animation(player, bullet_group, network_client=network_client, bg_scroll=bg_scroll)

    def update_animation(self, player, bullet_group=None, network_client=None, bg_scroll: int = 0):
        animation_cooldown = 100
        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx

        frame = self.animation_list[self.action][self.frame_index]
        self.image = pygame.transform.flip(frame, self.flip, False)
        self.rect = self.image.get_rect()
        self.rect.bottom = old_bottom
        self.rect.centerx = old_centerx

        now = pygame.time.get_ticks()
        shot_cooldown = 900 if self.enraged else 1300
        if self.action == 2 and self.frame_index == 2:
            if (not self.shot_frame_fired and bullet_group is not None and
                    now - self.last_shot_time > shot_cooldown):
                y_offsets = (0, -70, 70) if self.enraged else (0,)
                for dy in y_offsets:
                    ty = player.rect.centery + dy
                    bullet_group.add(DragonFire(
                        self.rect.centerx,
                        self.rect.centery,
                        player.rect.centerx,
                        ty,
                    ))
                    if network_client and getattr(network_client, 'running', False) and hasattr(self, 'target_id'):
                        network_client.send_enemy_shoot(
                            "dragon",
                            self.rect.centerx + bg_scroll,
                            self.rect.centery,
                            self.direction,
                            target_wx=player.rect.centerx + bg_scroll,
                            target_wy=ty,
                        )
                self.last_shot_time = now
                self.shot_frame_fired = True
        elif self.action != 2 or self.frame_index != 2:
            self.shot_frame_fired = False

        if now - self.update_time > animation_cooldown:
            self.update_time = now
            self.frame_index += 1
            if self.frame_index >= len(self.animation_list[self.action]):
                if self.action == 3:  # Morte
                    self.frame_index = len(self.animation_list[self.action]) - 1
                elif self.action == 2:  # Fim do ataque → volta para Idle
                    self.action = 0
                    self.frame_index = 0
                else:
                    self.frame_index = 0

    def update_action(self, new_action: int):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self, screen: pygame.Surface):
        draw_rect = self.image.get_rect(midbottom=self.rect.midbottom)
        screen.blit(self.image, draw_rect)
        if getattr(self, 'hit_flash', 0) > 0:
            self.hit_flash -= 1
            white = pygame.mask.from_surface(self.image).to_surface(
                setcolor=(255, 255, 255, 200), unsetcolor=(0, 0, 0, 0)
            )
            screen.blit(white, draw_rect)

    def draw_health_bar(self, surface: pygame.Surface):
        if self.health > 0:
            bar_width = 80
            bar_height = 8
            x = self.rect.centerx - (bar_width // 2)
            y = self.rect.top - 15
            ratio = max(0, self.health) / self.max_health
            is_enraged = self.enraged or (self.health <= self.max_health * 0.5)
            bg_col = (90, 15, 15) if is_enraged else (255, 0, 0)
            fill_col = (255, 120, 0) if is_enraged else (0, 255, 0)
            pygame.draw.rect(surface, bg_col, (x, y, bar_width, bar_height))
            pygame.draw.rect(surface, fill_col, (x, y, bar_width * ratio, bar_height))
            pygame.draw.rect(surface, (0, 0, 0), (x, y, bar_width, bar_height), 1)


# ======================================================================
#  BOSS (DEMON)
# ======================================================================
class Boss(pygame.sprite.Sprite):
    """Boss Demônio com ataque corporal devastador e gravidade."""

    def __init__(self, x: int, y: int, scale: float = 1.5):
        super().__init__()
        self.base_speed = 3
        self.enraged_speed = 4
        self.speed = self.base_speed
        self.dy = 0
        self.in_air = False
        self.last_jump_time = 0

        # Máquina de Estados: 0='Idle', 1='Walk', 2='Attack', 3='Death'
        self.action = 0
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()

        self.flip = False
        self.direction = 1

        self.max_health = 350
        self.health = self.max_health
        self.alive = True
        self.hit_flash = 0
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
        # Hitbox fixa baseada no frame Idle[0] (largura ajustada ao corpo, sem a ponta
        # do tridente) para que animações de ataque não empurrem a colisão contra paredes.
        base_w, base_h = self.animation_list[0][0].get_size()
        hitbox_w = max(40, int(base_w * 0.65))
        self.rect = pygame.Rect(0, 0, hitbox_w, base_h)
        self.rect.midbottom = (x, y)

    def update(self, player, obstacle_list: list, GRAVITY: float):
        if not self.alive:
            self.update_animation(player)
            return

        now = pygame.time.get_ticks()
        enraged = self.health <= self.max_health * 0.5
        self.speed = self.enraged_speed if enraged else self.base_speed

        dx = 0
        dist_x = player.rect.centerx - self.rect.centerx
        abs_dist_x = abs(dist_x)
        abs_dist_y = abs(player.rect.centery - self.rect.centery)

        # Jogador fora da Arena 1 (ex.: renasceu no penhasco elevado inicial):
        # mantém o Demônio em Idle dentro da arena em vez de pular contra a parede.
        player_outside_arena = (
            (player.rect.bottom < self.rect.top - TILE_SIZE * 4
             or player.rect.bottom < self.rect.bottom - TILE_SIZE * 5)
            and abs_dist_x > TILE_SIZE * 4
        )

        # Vira para o jogador quando não está no meio da animação de golpe
        if self.action != 2 and not player_outside_arena:
            if dist_x > 0:
                self.direction = 1
                self.flip = False
            elif dist_x < 0:
                self.direction = -1
                self.flip = True

        # Persegue continuamente dentro da arena (<= 700 px), sem o antigo limite de 250 px
        if player_outside_arena or abs_dist_x > 700:
            self.update_action(0)
        elif abs_dist_x <= 100 and abs_dist_y <= 90:
            self.update_action(2)
        else:
            self.update_action(1)
            dx = self.speed * self.direction
            # Contra-ataque a quem fica parado em plataforma: só salta se estiver no chão
            # e não houver obstáculo sólido logo acima da cabeça.
            if (player.rect.bottom < self.rect.top - 20
                    and not self.in_air
                    and now - self.last_jump_time >= 2500):
                head_probe = pygame.Rect(self.rect.x, self.rect.top - TILE_SIZE, self.rect.width, TILE_SIZE)
                blocked_above = any(tile[1].colliderect(head_probe) for tile in obstacle_list)
                if not blocked_above:
                    self.dy = -13
                    self.in_air = True
                    self.last_jump_time = now

        # Passo A — Resolução de colisão no Eixo X (Horizontal)
        if dx != 0:
            for tile in obstacle_list:
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.rect.width, self.rect.height):
                    if dx > 0:
                        dx = min(dx, tile[1].left - self.rect.right)
                    elif dx < 0:
                        dx = max(dx, tile[1].right - self.rect.left)
        self.rect.x += dx

        # Passo B — Resolução de colisão no Eixo Y (Vertical)
        self.dy = min(self.dy + GRAVITY, 12)
        on_ground = False
        for tile in obstacle_list:
            if tile[1].colliderect(self.rect.x, self.rect.y + self.dy, self.rect.width, self.rect.height):
                if self.dy > 0:
                    self.rect.bottom = tile[1].top
                    self.dy = 0
                    on_ground = True
                elif self.dy < 0:
                    self.rect.top = tile[1].bottom
                    self.dy = 0

        if on_ground:
            self.in_air = False
        else:
            self.rect.y += self.dy
            self.in_air = True

        self.update_animation(player)

    def update_animation(self, player):
        ANIMATION_COOLDOWN = 100
        # Atualiza apenas o sprite visual; self.rect (hitbox fixa) não muda por frame.
        self.image = pygame.transform.flip(self.animation_list[self.action][self.frame_index], self.flip, False)

        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

            if self.action == 2 and self.frame_index in [2, 3]:
                if pygame.time.get_ticks() - self.last_hit_time > 950:
                    dist_x_hit = abs(player.rect.centerx - self.rect.centerx)
                    dist_y_hit = abs(player.rect.centery - self.rect.centery)
                    if dist_x_hit <= 130 and dist_y_hit <= 90:
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
        draw_rect = self.image.get_rect(midbottom=self.rect.midbottom)
        screen.blit(self.image, draw_rect)
        if getattr(self, 'hit_flash', 0) > 0:
            self.hit_flash -= 1
            white = pygame.mask.from_surface(self.image).to_surface(
                setcolor=(255, 255, 255, 200), unsetcolor=(0, 0, 0, 0)
            )
            screen.blit(white, draw_rect)

    def draw_health_bar(self, surface: pygame.Surface):
        if self.health > 0:
            bar_width = 80
            bar_height = 8

            x = self.rect.centerx - (bar_width // 2)
            y = self.rect.top - 15

            vida_atual = max(0, self.health)
            ratio = vida_atual / self.max_health

            enraged = self.health <= self.max_health * 0.5
            bg_col = (90, 15, 15) if enraged else (255, 0, 0)
            fill_col = (255, 120, 0) if enraged else (0, 255, 0)
            pygame.draw.rect(surface, bg_col, (x, y, bar_width, bar_height))
            pygame.draw.rect(surface, fill_col, (x, y, bar_width * ratio, bar_height))
            pygame.draw.rect(surface, (0, 0, 0), (x, y, bar_width, bar_height), 1)
