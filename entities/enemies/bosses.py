"""
entities/enemies/bosses.py — Chefes do jogo: DragonBoss e Boss (Demon).
"""

import math
import pygame
from asset_manager import AssetManager
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, DRAGON_WAKE_RANGE
from entities import effects
from entities.combat.projectiles import DragonFire


# ======================================================================
#  DRAGON BOSS
# ======================================================================
class DragonBoss(pygame.sprite.Sprite):
    """Boss Dragão voador com perseguição dinâmica, transição de Fúria e 3 padrões de ataque."""

    def __init__(self, x: int, y: int, scale: float = 1.5):
        super().__init__()
        self.base_speed = 3.5
        self.enraged_speed = 4.5
        self.speed = self.base_speed
        self._fx = 0.0
        self._fy = 0.0
        self.action = 0
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.flip = False
        self.direction = 1
        self.max_health = 650
        self.health = self.max_health
        self.alive = True
        self.enraged = False
        self.invulnerable = False
        self.fury_transition_until = 0
        self.hit_flash = 0
        self.last_shot_time = 0
        self.last_contact_hit_time = 0
        self.shot_frame_fired = False
        # Adormecido até o jogador chegar à Arena 2 sem Demônios vivos (ver try_activate).
        # Enquanto False: fica em Idle ancorado no cenário e ignora dano.
        self.activated = False

        # Movimentação dinâmica e limites da Arena 2 (acompanham o screen_scroll)
        self.arena_min_x = x - 18 * TILE_SIZE
        self.arena_max_x = x + 6 * TILE_SIZE
        self.min_y = 65
        self.max_y = SCREEN_HEIGHT - 2 * TILE_SIZE - 20  # acima do chão/água
        self.patrol_side = 1  # +1 direita do jogador, -1 esquerda
        self.last_side_switch = pygame.time.get_ticks()

        # Máquina de estados de ataques na Fúria:
        # 'fly', 'burst', 'dive_telegraph', 'dive_rush', 'dive_recover'
        self.attack_state = 'fly'
        self.fury_cycle = 0
        self.burst_remaining = 0
        self.next_burst_time = 0
        self.last_dive_time = 0
        self.dive_telegraph_until = 0
        self.dive_target_x = float(x)
        self.dive_target_y = float(y)
        self.dive_vx = 0.0
        self.dive_vy = 0.0
        self.dive_end_time = 0

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
        self._expected_x = self.rect.x

    def _sync_scroll_bounds(self, screen_scroll: int) -> None:
        """Mantém limites da arena e alvo de mergulho sincronizados com qualquer scroll."""
        ext_scroll = self.rect.x - self._expected_x
        total_scroll = ext_scroll + screen_scroll
        if total_scroll:
            self.arena_min_x += total_scroll
            self.arena_max_x += total_scroll
            self.dive_target_x += total_scroll
        if screen_scroll:
            self.rect.x += screen_scroll

    def _move_smooth(self, vx: float, vy: float) -> None:
        """Aplica deslocamento float sem tremulação de arredondamento."""
        self._fx += vx
        mx = int(self._fx)
        self._fx -= mx
        self.rect.x += mx

        self._fy += vy
        my = int(self._fy)
        self._fy -= my
        self.rect.y += my

    def _clamp_to_arena(self) -> None:
        """Mantém o Dragão contido nos limites horizontais e verticais da Arena 2."""
        left_limit = max(20, min(self.arena_min_x, self.arena_max_x))
        right_limit = min(SCREEN_WIDTH - 20, max(self.arena_min_x, self.arena_max_x))
        if right_limit > left_limit + self.rect.width:
            if self.rect.centerx < left_limit:
                self.rect.centerx = int(left_limit)
            elif self.rect.centerx > right_limit:
                self.rect.centerx = int(right_limit)
        if self.rect.top < self.min_y:
            self.rect.top = self.min_y
        if self.rect.bottom > self.max_y:
            self.rect.bottom = self.max_y

    def _fire_projectile(self, bullet_group, tx: float, ty: float,
                         network_client=None, bg_scroll: int = 0) -> None:
        """Instancia um DragonFire (normal ou fúria) e replica na rede se Host."""
        if bullet_group is None:
            return
        bullet_group.add(DragonFire(
            self.rect.centerx,
            self.rect.centery,
            tx,
            ty,
            enraged=self.enraged,
        ))
        if network_client and getattr(network_client, 'running', False) and hasattr(self, 'target_id'):
            b_type = "dragon_fury" if self.enraged else "dragon"
            network_client.send_enemy_shoot(
                b_type,
                self.rect.centerx + bg_scroll,
                self.rect.centery,
                self.direction,
                target_wx=tx + bg_scroll,
                target_wy=ty,
            )

    def _apply_contact_damage(self, player, now: int) -> None:
        """Dano de contato do corpo do Dragão (20 normal, 35 fúria, 38 mergulho; cd 800 ms)."""
        if self.invulnerable or not player or not getattr(player, 'alive', False):
            return
        if now - self.last_contact_hit_time < 800:
            return
        body = self.rect.inflate(-30, -20)
        if body.colliderect(player.rect) and getattr(player, 'invincible', 0) == 0:
            if self.attack_state == 'dive_rush':
                dmg = 38
            elif self.enraged:
                dmg = 35
            else:
                dmg = 20
            player.health -= dmg
            player.invincible = 45
            self.last_contact_hit_time = now

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
            now = pygame.time.get_ticks()
            self.update_time = now
            self.last_side_switch = now
            self.last_dive_time = now
            return True
        return False

    def update(self, player, obstacle_list=None, gravity=None,
               bullet_group=None, screen_scroll: int = 0,
               network_client=None, bg_scroll: int = 0,
               can_activate: bool = True):
        self._sync_scroll_bounds(screen_scroll)

        if not self.alive:
            self.invulnerable = False
            self.update_animation(player, None)
            self._expected_x = self.rect.x
            return

        if not self.activated:
            # Adormecido: ancorado no cenário (acompanha o scroll), em Idle,
            # sem perseguir o jogador nem disparar DragonFire.
            self.update_action(0)
            self.update_animation(player, None)
            self.try_activate(player, can_activate)
            self._expected_x = self.rect.x
            return

        now = pygame.time.get_ticks()

        # Transição para Fúria (≤ 50% HP): 0.8s invulnerável + screen shake + som
        if not self.enraged and self.health <= self.max_health * 0.5:
            self.enraged = True
            self.invulnerable = True
            self.fury_transition_until = now + 800
            self.attack_state = 'fly'
            self.burst_remaining = 0
            self.last_dive_time = now
            effects.shake(22, 10)
            try:
                AssetManager().get_sound('grenade').play()
            except Exception:
                pass

        if self.invulnerable:
            if now < self.fury_transition_until:
                self.update_action(0)
                self.rect.y += int(round(math.sin(now * 0.05) * 2))
                self._clamp_to_arena()
                self.update_animation(player, None)
                self._expected_x = self.rect.x
                return
            self.invulnerable = False

        self.speed = self.enraged_speed if self.enraged else self.base_speed

        # Vira para o jogador (exceto durante a investida reta do mergulho)
        if self.attack_state != 'dive_rush':
            self.flip = player.rect.centerx < self.rect.centerx
            self.direction = -1 if self.flip else 1

        # ------------------------------------------------------------------
        # Ataque C — Mergulho Rasante (Dive Attack, na Fúria a cada ~4.5 s)
        # ------------------------------------------------------------------
        if (self.enraged and self.attack_state == 'fly'
                and now - self.last_dive_time >= 4500):
            self.attack_state = 'dive_telegraph'
            self.dive_telegraph_until = now + 450
            self.last_dive_time = now
            self.update_action(0)

        if self.attack_state == 'dive_telegraph':
            # Aviso de 0.45s: para no ar, sobe levemente e trava na posição do jogador
            self._move_smooth(0.0, -1.5)
            self._clamp_to_arena()
            self.dive_target_x = float(player.rect.centerx)
            self.dive_target_y = float(min(player.rect.centery, self.max_y - 30))
            if now >= self.dive_telegraph_until:
                dx = self.dive_target_x - self.rect.centerx
                dy = self.dive_target_y - self.rect.centery
                dist = max(1.0, math.hypot(dx, dy))
                dive_speed = 11.5
                self.dive_vx = (dx / dist) * dive_speed
                self.dive_vy = (dy / dist) * dive_speed
                self.flip = dx < 0
                self.direction = -1 if dx < 0 else 1
                self.dive_end_time = now + 850
                self.attack_state = 'dive_rush'
                self.update_action(2)

        elif self.attack_state == 'dive_rush':
            self._move_smooth(self.dive_vx, self.dive_vy)
            reached = (
                math.hypot(self.dive_target_x - self.rect.centerx,
                           self.dive_target_y - self.rect.centery) < 35
                or self.rect.bottom >= self.max_y
                or self.rect.centerx <= self.arena_min_x + 20
                or self.rect.centerx >= self.arena_max_x - 20
                or now >= self.dive_end_time
            )
            self._clamp_to_arena()
            if reached:
                self.attack_state = 'dive_recover'
                self.patrol_side *= -1  # cruza para o lado oposto da arena
                self.last_side_switch = now
                self.last_shot_time = now

        elif self.attack_state == 'dive_recover':
            # Sobe de volta para altura de voo enquanto cruza para o lado oposto
            target_x = player.rect.centerx + self.patrol_side * 280
            target_x = max(self.arena_min_x, min(self.arena_max_x, target_x))
            target_y = 175
            vx = self.speed if target_x > self.rect.centerx + 12 else (-self.speed if target_x < self.rect.centerx - 12 else 0.0)
            vy = -3.8 if self.rect.centery > target_y + 10 else 0.0
            self._move_smooth(vx, vy)
            self._clamp_to_arena()
            self.update_action(1)
            if self.rect.centery <= target_y + 18:
                self.attack_state = 'fly'

        else:
            # ------------------------------------------------------------------
            # Movimentação dinâmica (onda senoidal + troca periódica de lado)
            # ------------------------------------------------------------------
            switch_interval = 2400 if self.enraged else 3500
            if now - self.last_side_switch >= switch_interval:
                self.patrol_side *= -1
                self.last_side_switch = now

            target_x = player.rect.centerx + self.patrol_side * 250
            target_x = max(self.arena_min_x, min(self.arena_max_x, target_x))
            wave_amp = 60 if self.enraged else 45
            target_y = max(self.min_y + 50, min(self.max_y - 90, 195 + math.sin(now * 0.004) * wave_amp))

            dx = target_x - self.rect.centerx
            dy = target_y - self.rect.centery
            vx = max(-self.speed, min(self.speed, dx * 0.06))
            if abs(dx) > 25 and abs(vx) < self.speed * 0.65:
                vx = self.speed * 0.65 * (1 if dx > 0 else -1)
            vy = max(-3.0, min(3.0, dy * 0.08))
            self._move_smooth(vx, vy)
            self._clamp_to_arena()

            # Ataque B — Rajada Rápida Mirada (3 DragonFire a cada 180 ms)
            if self.attack_state == 'burst':
                self.update_action(2)
                if self.burst_remaining > 0 and now >= self.next_burst_time:
                    self._fire_projectile(
                        bullet_group, player.rect.centerx, player.rect.centery,
                        network_client=network_client, bg_scroll=bg_scroll,
                    )
                    self.burst_remaining -= 1
                    self.next_burst_time = now + 180
                if self.burst_remaining <= 0:
                    self.attack_state = 'fly'
                    self.last_shot_time = now
            else:
                attack_cooldown = 800 if self.enraged else 1200
                if now - self.last_shot_time >= attack_cooldown:
                    self.update_action(2)
                else:
                    self.update_action(1)

        # Dano de contato do corpo do Dragão
        self._apply_contact_damage(player, now)

        # Atualiza animação (dispara projéteis no frame 2 de Attack quando em 'fly')
        allow_anim_fire = (self.attack_state == 'fly')
        self.update_animation(
            player,
            bullet_group if allow_anim_fire else None,
            network_client=network_client,
            bg_scroll=bg_scroll,
        )
        self._expected_x = self.rect.x

    def update_animation(self, player, bullet_group=None, network_client=None, bg_scroll: int = 0):
        animation_cooldown = 85 if self.enraged else 100
        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx

        frame = self.animation_list[self.action][self.frame_index]
        self.image = pygame.transform.flip(frame, self.flip, False)
        self.rect = self.image.get_rect()
        self.rect.bottom = old_bottom
        self.rect.centerx = old_centerx

        now = pygame.time.get_ticks()
        shot_cooldown = 800 if self.enraged else 1200
        if self.action == 2 and self.frame_index == 2:
            if (not self.shot_frame_fired and bullet_group is not None and
                    now - self.last_shot_time >= shot_cooldown):
                if self.enraged:
                    # Alterna entre Ataque A (Leque de 5) e Ataque B (Burst de 3 mirados)
                    if self.fury_cycle % 2 == 0:
                        for dy in (-140, -70, 0, 70, 140):
                            self._fire_projectile(
                                bullet_group, player.rect.centerx, player.rect.centery + dy,
                                network_client=network_client, bg_scroll=bg_scroll,
                            )
                        self.last_shot_time = now
                    else:
                        self.attack_state = 'burst'
                        self.burst_remaining = 3
                        self.next_burst_time = now
                    self.fury_cycle += 1
                else:
                    self._fire_projectile(
                        bullet_group, player.rect.centerx, player.rect.centery,
                        network_client=network_client, bg_scroll=bg_scroll,
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
                elif self.action == 2:  # Fim do ataque → volta para Walk/Idle
                    self.action = 1 if self.activated else 0
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
        if self.alive and self.enraged:
            # Aura de fogo pulsante em volta do Dragão em Fúria
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.014)
            aura_w = draw_rect.width + 24
            aura_h = draw_rect.height + 24
            aura = pygame.Surface((aura_w, aura_h), pygame.SRCALPHA)
            pygame.draw.ellipse(aura, (255, 70, 15, int(45 + 45 * pulse)), aura.get_rect())
            screen.blit(aura, aura.get_rect(center=draw_rect.center))

        screen.blit(self.image, draw_rect)

        if self.alive and self.attack_state == 'dive_telegraph':
            # Pisca vermelho brilhante durante o aviso do Mergulho Rasante
            if (pygame.time.get_ticks() // 65) % 2 == 0:
                tele = pygame.mask.from_surface(self.image).to_surface(
                    setcolor=(255, 30, 30, 175), unsetcolor=(0, 0, 0, 0)
                )
                screen.blit(tele, draw_rect)
        elif self.alive and self.enraged:
            # Tint avermelhado pulsante sobre o sprite durante a Fúria
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.012)
            tint = pygame.mask.from_surface(self.image).to_surface(
                setcolor=(255, 55, 10, int(40 + 45 * pulse)), unsetcolor=(0, 0, 0, 0)
            )
            screen.blit(tint, draw_rect)

        if getattr(self, 'hit_flash', 0) > 0:
            self.hit_flash -= 1
            white = pygame.mask.from_surface(self.image).to_surface(
                setcolor=(255, 255, 255, 200), unsetcolor=(0, 0, 0, 0)
            )
            screen.blit(white, draw_rect)

    def draw_health_bar(self, surface: pygame.Surface):
        if self.health > 0:
            bar_width = 96 if self.enraged else 80
            bar_height = 9 if self.enraged else 8
            x = self.rect.centerx - (bar_width // 2)
            y = self.rect.top - 16
            ratio = max(0, self.health) / self.max_health
            is_enraged = self.enraged or (self.health <= self.max_health * 0.5)
            bg_col = (60, 10, 10) if is_enraged else (180, 0, 0)
            fill_col = (255, 35, 20) if is_enraged else (0, 255, 0)
            border_col = (255, 170, 40) if is_enraged else (0, 0, 0)
            pygame.draw.rect(surface, bg_col, (x, y, bar_width, bar_height))
            pygame.draw.rect(surface, fill_col, (x, y, bar_width * ratio, bar_height))
            pygame.draw.rect(surface, border_col, (x, y, bar_width, bar_height), 2 if is_enraged else 1)


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
