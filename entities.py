"""
entities.py — Classes de todas as entidades do jogo PyShooter.

Hierarquia principal:
    pygame.sprite.Sprite
        └── Character          (base: vida, animação, física, tiro)
              ├── Player       (input do jogador, scroll de câmera)
              └── Enemy        (IA: patrulha, visão, ataque)
        └── Bullet
        └── Grenade  → cria Explosion ao explodir
        └── Explosion
        └── ItemBox
        └── Water / Decoration / Exit

Utilitários (sem herança de Sprite):
    HealthBar, ScreenFade, World
"""
import math
import random
import pygame
from config import (
    GRAVITY, TERMINAL_VELOCITY, JUMP_VELOCITY,
    SCREEN_WIDTH, SCREEN_HEIGHT,
    TILE_SIZE, SCROLL_THRESH,
    BULLET_SPEED, BULLET_DAMAGE_TO_ENEMY, BULLET_DAMAGE_TO_PLAYER,
    SHOOT_COOLDOWN,
    GRENADE_SPEED, GRENADE_INITIAL_VEL_Y, GRENADE_TIMER,
    GRENADE_DAMAGE, GRENADE_BLAST_RADIUS,
    HEALTH_PICKUP, AMMO_PICKUP, GRENADE_PICKUP,
    ANIMATION_COOLDOWN, EXPLOSION_SPEED, EXPLOSION_SCALE,
    ENEMY_VISION_WIDTH, ENEMY_VISION_HEIGHT,
    PLAYER_SCALE, PLAYER_SPEED, PLAYER_START_AMMO, PLAYER_START_GRENADES,
    ENEMY_SCALE, ENEMY_SPEED, ENEMY_AMMO, ENEMY_GRENADES,
    RED, GREEN, BLACK,
)
from asset_manager import AssetManager

# ======================================================================
#  CHARACTER  — classe-base para Player e Enemy
# ======================================================================
class Character(pygame.sprite.Sprite):
    """Entidade animada com vida, física (gravidade + colisão) e tiro."""

    def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
        self.grenades = grenades
        self.health = 100
        self.max_health = self.health
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()

        self.base_speed = speed
        self.speed_boost = False
        self.speed_boost_timer = 0

        # Carregar animações via AssetManager (com cache)
        assets = AssetManager()
        self.animation_list = assets.load_character_animations(char_type, scale)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    # ------------------------------------------------------------------
    #  Atualização por frame
    # ------------------------------------------------------------------
    def update(self):
        self.update_animation()
        self.check_alive()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
            
        if self.speed_boost:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer <= 0:
                self.speed_boost = False
                self.speed = self.base_speed

    # ------------------------------------------------------------------
    #  Física compartilhada
    # ------------------------------------------------------------------
    def _calculate_movement(self, moving_left, moving_right):
        """Define dx com base nas flags de direção."""
        dx = 0
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1
        return dx

    def _apply_gravity(self):
        """Acumula gravidade e aplica clamping de velocidade terminal."""
        self.vel_y += GRAVITY
        if self.vel_y > TERMINAL_VELOCITY:
            self.vel_y = TERMINAL_VELOCITY          # ← FIX do bug original

    def _check_tile_collisions(self, dx, dy, obstacle_list):
        """Detecta e resolve colisões AABB com tiles sólidos."""
        # Cria uma margem de ~20% na largura para ignorar a ponta da arma/sprite solto
        margin = int(self.width * 0.2)
        col_width = self.width - (margin * 2)
        
        for tile in obstacle_list:
            # Colisão horizontal (usa hitbox mais fina)
            if tile[1].colliderect(self.rect.x + dx + margin, self.rect.y,
                                   col_width, self.height):
                dx = 0
                self._on_horizontal_collision()
                
            # Colisão vertical (ATENÇÃO: usar 'dx' resolvido para não bugar ao cair de quinas)
            if tile[1].colliderect(self.rect.x + dx + margin, self.rect.y + dy,
                                   col_width, self.height):
                if self.vel_y < 0:                  # subindo (pulo)
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                elif self.vel_y >= 0:               # caindo
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom
                    
        return dx, dy

    def _on_horizontal_collision(self):
        """Hook para subclasses reagirem a colisão com parede."""
        pass

    def _check_environment(self, water_group):
        """Verifica perigos ambientais (água e queda do mapa)."""
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

    # ------------------------------------------------------------------
    #  Combate
    # ------------------------------------------------------------------
    def shoot(self, bullet_group):
        """Dispara um projétil se houver munição e o cooldown permitir."""
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = SHOOT_COOLDOWN
            spawn_x = self.rect.centerx + (self.rect.width * 0.9 * self.direction)
            spawn_y = self.rect.centery - 5 
            
            bullet = Bullet(
                spawn_x,
                spawn_y,
                self.direction,
            )
            bullet_group.add(bullet)
            self.ammo -= 1
            AssetManager().get_sound('shot').play()

    # ------------------------------------------------------------------
    #  Animação
    # ------------------------------------------------------------------
    def update_animation(self):
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            if self.action == 3:        # Death: congela no último frame
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    # ------------------------------------------------------------------
    #  Renderização
    # ------------------------------------------------------------------
    def draw(self, screen):
        screen.blit(pygame.transform.flip(self.image, self.flip, False),
                     self.rect)

# ======================================================================
#  PLAYER
# ======================================================================
class Player(Character):
    """Personagem controlado pelo jogador; gerencia scroll de câmera."""

    def __init__(self, x, y, scale=PLAYER_SCALE, speed=PLAYER_SPEED,
                 ammo=PLAYER_START_AMMO, grenades=PLAYER_START_GRENADES):
        super().__init__('player', x, y, scale, speed, ammo, grenades)
        self.invincible = 0

    def update(self, enemy_group=None):
        super().update()
        
        # Lógica de I-Frames
        if self.invincible > 0:
            self.invincible -= 1
            
        # Dano de Contato
        if enemy_group and self.invincible == 0:
            for enemy in enemy_group:
                if type(enemy).__name__ == 'SkeletonEnemy':
                    continue  # Ignora o dano de contato para o esqueleto

                # Reduz drasticamente a largura do retângulo invisível para ignorar a transparência
                hitbox_inimigo = enemy.rect.inflate(-50, -10)
                if enemy.alive and self.rect.colliderect(hitbox_inimigo):
                    self.health -= 10
                    self.invincible = 60
                    break

    def draw(self, screen):
        # Efeito visual de piscar durante a invencibilidade
        if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            return  # Pula o frame, fazendo o personagem sumir
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

    def move(self, moving_left, moving_right, obstacle_list,
             water_group, exit_group, bg_scroll, level_length):
        """Processa movimento, colisão, scroll e retorna
        (screen_scroll, level_complete)."""
        screen_scroll = 0
        dx = self._calculate_movement(moving_left, moving_right)
        dy = 0

        # Pulo
        if self.jump and not self.in_air:
            self.vel_y = JUMP_VELOCITY
            self.jump = False
            self.in_air = True

        # Gravidade
        self._apply_gravity()
        dy += self.vel_y

        # Colisão com tiles
        dx, dy = self._check_tile_collisions(dx, dy, obstacle_list)

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

        return screen_scroll, level_complete

# ======================================================================
#  ENEMY
# ======================================================================
class Enemy(Character):
    """Soldado inimigo com IA de patrulha e ataque."""

    def __init__(self, x, y, scale=ENEMY_SCALE, speed=ENEMY_SPEED,
                 ammo=ENEMY_AMMO, grenades=ENEMY_GRENADES):
        super().__init__('enemy', x, y, scale, speed, ammo, grenades)
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, ENEMY_VISION_WIDTH, ENEMY_VISION_HEIGHT)
        self.idling = False
        self.idling_counter = 0
        self.flip_cooldown = 0

    def _on_horizontal_collision(self):
        """Inverte a direção ao colidir com uma parede."""
        if self.flip_cooldown == 0:
            self.direction *= -1
            self.move_counter = 0
            self.flip_cooldown = 30  # Força 30 frames antes de poder virar de novo

    def _is_edge_ahead(self, obstacle_list):
        """Detecta se não há chão sólido à frente dos pés do inimigo."""
        if self.in_air:
            return False  # Ignorar detecção de borda se já estiver no ar
        # Ponto de teste: logo além da borda dianteira, abaixo dos pés
        if self.direction == 1:
            check_x = self.rect.right + 2
        else:
            check_x = self.rect.left - 2
        # Rect estreito abaixo dos pés na direção do movimento
        test_rect = pygame.Rect(check_x - 1, self.rect.bottom + 1,
                                2, TILE_SIZE)
        for tile in obstacle_list:
            if tile[1].colliderect(test_rect):
                return False   # Chão encontrado — sem borda
        return True            # Sem chão à frente — borda detectada!

    def move(self, moving_left, moving_right, obstacle_list, water_group):
        """Movimento simplificado (sem scroll nem saída)."""
        dx = self._calculate_movement(moving_left, moving_right)
        dy = 0

        self._apply_gravity()
        dy += self.vel_y

        dx, dy = self._check_tile_collisions(dx, dy, obstacle_list)
        self._check_environment(water_group)

        self.rect.x += dx
        self.rect.y += dy

    def ai(self, player, screen_scroll, obstacle_list, water_group,
           bullet_group):
        """Lógica de IA: patrulha, detecção e ataque."""
        if self.flip_cooldown > 0:
            self.flip_cooldown -= 1

        if self.alive and player.alive:
            # Chance aleatória de parar (idling)
            if not self.idling and random.randint(1, 200) == 1:
                self.update_action(0)           # Idle
                self.idling = True
                self.idling_counter = 50

            # Jogador dentro do campo de visão → atirar
            if self.vision.colliderect(player.rect):
                # FIX: Vira para o jogador apenas dentro do bloco de visão
                if player.rect.centerx < self.rect.centerx:
                    self.direction = -1
                    self.flip = True
                else:
                    self.direction = 1
                    self.flip = False
                
                self.update_action(0)           # Idle (mira)
                self.shoot(bullet_group)
                # NOTA: self.move() NÃO é chamado aqui, evitando conflito!
            else:
                if not self.idling:
                    # Detecção de borda — inverter ANTES de cair
                    if self._is_edge_ahead(obstacle_list):
                        self.direction *= -1
                        self.move_counter = 0
                        self.flip_cooldown = 30  # Força 30 frames antes de poder virar de novo

                    ai_moving_right = (self.direction == 1)
                    ai_moving_left = not ai_moving_right
                    
                    # Lógica de patrulha separada do tiro
                    self.move(ai_moving_left, ai_moving_right,
                              obstacle_list, water_group)
                    self.update_action(1)       # Run
                    self.move_counter += 1
                    
                    # Inverter ao fim do percurso de patrulha
                    if self.move_counter > TILE_SIZE * 3:
                        if self.flip_cooldown == 0:
                            self.direction *= -1
                            self.move_counter = 0
                            self.flip_cooldown = 30  # Força 30 frames antes de poder virar de novo
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        # Scroll do mundo
        self.rect.x += screen_scroll
        
        # FIX: Atualizar retângulo de visão SEMPRE para acompanhar o inimigo e o scroll
        self.vision.center = (
            self.rect.centerx + 75 * self.direction,
            self.rect.centery,
        )

# ======================================================================
#  SNIPER
# ======================================================================
class Sniper(Enemy):
    """Atirador de elite com visão ampliada, tiro mais rápido e cooldown maior."""
    
    def __init__(self, x, y, scale=1.2, speed=1, ammo=9999, grenades=0):
        super().__init__(x, y, scale, speed, ammo, grenades)
        self.vision = pygame.Rect(0, 0, 300, 20)
        
        # Override animation list com o extrator de sprite strips do sniper
        self.animation_list = []
        animations = [
            'Idle',     # action 0
            'Walk',     # action 1
            'Shot_1',   # action 2
            'Dead',     # action 3
            'Hurt'      # action 4
        ]
        
        for anim in animations:
            img = pygame.image.load(f'img/sniper/{anim}.png').convert_alpha()
            frame_height = img.get_height()
            frame_width = frame_height # Lógica de fatiamento: frames quadrados
            num_frames = img.get_width() // frame_width
            
            temp_list = []
            for i in range(num_frames):
                frame = img.subsurface((i * frame_width, 0, frame_width, frame_height))
                
                # Correção de escala durante a extração para altura equivalente ao Player
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
        
        # Alinhamento perfeito ao chão
        self.rect.midbottom = (x + TILE_SIZE // 2, y + TILE_SIZE)
        
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def shoot(self, bullet_group):
        """Dispara exatamente no frame 2 da animação de tiro (Shot_1)."""
        if self.shoot_cooldown == 0 and self.ammo > 0 and self.action == 2 and self.frame_index == 2:
            self.shoot_cooldown = 60
            spawn_x = self.rect.centerx + (self.rect.width * 0.9 * self.direction)
            spawn_y = self.rect.centery - 5
            
            bullet = Bullet(
                spawn_x,
                spawn_y,
                self.direction,
            )
            bullet.speed = 15
            bullet_group.add(bullet)
            self.ammo -= 1
            AssetManager().get_sound('shot').play()

    def ai(self, player, screen_scroll, obstacle_list, water_group, bullet_group):
        if self.flip_cooldown > 0:
            self.flip_cooldown -= 1

        if self.alive and player.alive:
            if not self.idling and random.randint(1, 200) == 1:
                self.update_action(0)           # Idle
                self.idling = True
                self.idling_counter = 50

            if self.vision.colliderect(player.rect):
                if player.rect.centerx < self.rect.centerx:
                    self.direction = -1
                    self.flip = True
                else:
                    self.direction = 1
                    self.flip = False
                
                self.update_action(2)           # Attack (Shot_1)
                self.shoot(bullet_group)
            else:
                if not self.idling:
                    # Proteção contra Jittering na detecção de borda
                    if self._is_edge_ahead(obstacle_list):
                        if self.flip_cooldown == 0:
                            self.direction *= -1
                            self.move_counter = 0
                            self.flip_cooldown = 30
                            self.flip = not self.flip

                    ai_moving_right = (self.direction == 1)
                    ai_moving_left = not ai_moving_right
                    
                    self.move(ai_moving_left, ai_moving_right, obstacle_list, water_group)
                    self.update_action(1)       # Walk
                    self.move_counter += 1
                    
                    if self.move_counter > TILE_SIZE * 3:
                        if self.flip_cooldown == 0:
                            self.direction *= -1
                            self.move_counter = 0
                            self.flip_cooldown = 30
                            self.flip = not self.flip
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        self.rect.x += screen_scroll
        self.vision.center = (
            self.rect.centerx + 75 * self.direction,
            self.rect.centery,
        )



# ======================================================================
#  BULLET
# ======================================================================
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = BULLET_SPEED
        self.image = AssetManager().get_image('bullet')
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.has_hit = False
        self.hit_timer = 0

    def update(self, screen_scroll, obstacle_list, player,
               bullet_group, enemy_group):
        
        # Lógica de Atraso de Destruição (Kill Delay)
        if self.has_hit:
            self.hit_timer += 1
            if self.hit_timer > 2:
                self.kill()
            # A bala acompanha o scroll da tela enquanto congela para o feedback
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
            if player.alive and player.invincible == 0:
                player.health -= BULLET_DAMAGE_TO_PLAYER
                player.invincible = 60 # Garante frame de invencibilidade para o player
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

# ======================================================================
#  GRENADE
# ======================================================================
class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = GRENADE_TIMER
        self.vel_y = GRENADE_INITIAL_VEL_Y
        self.speed = GRENADE_SPEED
        self.image = AssetManager().get_image('grenade')
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    def update(self, screen_scroll, obstacle_list, player,
               enemy_group, explosion_group):
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

# ======================================================================
#  EXPLOSION
# ======================================================================
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = AssetManager().get_explosion_frames(scale)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self, screen_scroll):
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
#  ITEM BOX
# ======================================================================
class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = AssetManager().item_box_images[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2,
                            y + (TILE_SIZE - self.image.get_height()))

    def update(self, screen_scroll, player):
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

# ======================================================================
#  CENÁRIO: Decoration, Water, Exit
# ======================================================================
class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2,
                            y + (TILE_SIZE - self.image.get_height()))

    def update(self, screen_scroll):
        self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
    def __init__(self, x, y, images_list):
        pygame.sprite.Sprite.__init__(self)
        self.animation_list = images_list
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image = self.animation_list[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2,
                            y + (TILE_SIZE - self.image.get_height()))

    def update(self, screen_scroll):
        # Mover com a tela
        self.rect.x += screen_scroll
        
        # Animação (apenas se houver mais de 1 frame)
        if len(self.animation_list) > 1:
            if pygame.time.get_ticks() - self.update_time > 150:
                self.update_time = pygame.time.get_ticks()
                self.frame_index += 1
                if self.frame_index >= len(self.animation_list):
                    self.frame_index = 0
                self.image = self.animation_list[self.frame_index]

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2,
                            y + (TILE_SIZE - self.image.get_height()))

    def update(self, screen_scroll):
        self.rect.x += screen_scroll

# ======================================================================
#  HEALTH BAR  (HUD)
# ======================================================================
class HealthBar:
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, screen, health):
        self.health = health
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

# ======================================================================
#  SCREEN FADE  (transição visual)
# ======================================================================
class ScreenFade:
    def __init__(self, direction, colour, speed):
        self.direction = direction
        self.colour = colour
        self.speed = speed
        self.fade_counter = 0

    def fade(self, screen):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:     # Fade "abrindo" (4 retângulos)
            pygame.draw.rect(screen, self.colour,
                             (0 - self.fade_counter, 0,
                              SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour,
                             (SCREEN_WIDTH // 2 + self.fade_counter, 0,
                              SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.colour,
                             (0, 0 - self.fade_counter,
                              SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pygame.draw.rect(screen, self.colour,
                             (0, SCREEN_HEIGHT // 2 + self.fade_counter,
                              SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2:     # Fade vertical (cortina)
            pygame.draw.rect(screen, self.colour,
                             (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True
        return fade_complete

# ======================================================================
#  WORLD  — fábrica que interpreta o CSV e instancia entidades
# ======================================================================
class World:
    def __init__(self):
        self.obstacle_list = []
        self.level_length = 0

    def process_data(self, data, enemy_group, item_box_group,
                     decoration_group, water_group, exit_group):
        """Lê a matriz de tiles e cria todas as entidades do nível.

        Retorna (player, health_bar).
        """
        assets = AssetManager()
        self.level_length = len(data[0])
        player = None
        health_bar = None

        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = assets.tile_images[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    # A imagem 'cresce' para cima se for maior que o TILE_SIZE
                    img_rect.y = y * TILE_SIZE + (TILE_SIZE - img.get_height())
                    tile_data = (img, img_rect)

                    if (0 <= tile <= 8) or (24 <= tile <= 35) or tile in (12, 47, 48, 50, 58, 59, 60, 61, 65, 66, 73, 74, 75, 76, 77):  # Obstáculo sólido
                        self.obstacle_list.append(tile_data)
                    elif tile == 70:                 # Skeleton Enemy
                        skeleton = SkeletonEnemy(x * TILE_SIZE, y * TILE_SIZE)
                        enemy_group.add(skeleton)
                    elif tile in (51, 52, 53, 54, 55):  # Água de superfície animada (Fase 2)
                        water = Water(x * TILE_SIZE, y * TILE_SIZE, [
                            assets.tile_images[51],
                            assets.tile_images[52],
                            assets.tile_images[53],
                            assets.tile_images[54],
                            assets.tile_images[55]
                        ])
                        water_group.add(water)
                    elif tile in (9, 62, 63, 64, 67):  # Água de superfície animada (Fase 1/Pântano)
                        water = Water(x * TILE_SIZE, y * TILE_SIZE, [
                            assets.tile_images[9],
                            assets.tile_images[62],
                            assets.tile_images[63],
                            assets.tile_images[64],
                            assets.tile_images[67]
                        ])
                        water_group.add(water)
                    elif tile in (10, 56, 57, 68):  # Água profunda estática (Fase 1/2)
                        water = Water(x * TILE_SIZE, y * TILE_SIZE, [assets.tile_images[tile]])
                        water_group.add(water)
                    elif tile in (11, 13, 14, 71, 72, 78, 79, 80, 81, 82, 83, 84): # Decoração
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:                 # Spawn do jogador
                        player = Player(x * TILE_SIZE, y * TILE_SIZE)
                        health_bar = HealthBar(10, 10, player.health,
                                               player.health)
                    elif tile == 16:                 # Spawn de inimigo
                        enemy = Enemy(x * TILE_SIZE, y * TILE_SIZE)
                        enemy_group.add(enemy)
                    elif tile == 17:                 # Caixa de munição
                        item_box = ItemBox('Ammo', x * TILE_SIZE,
                                           y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18:                 # Caixa de granada
                        item_box = ItemBox('Grenade', x * TILE_SIZE,
                                           y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19:                 # Caixa de vida
                        item_box = ItemBox('Health', x * TILE_SIZE,
                                           y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile in (20, 41):                 # Saída da fase (Fase 1/2 e Fase 3)
                        exit_obj = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit_obj)
                    elif tile == 21:                 # Sniper (Fase 3)
                        sniper = Sniper(x * TILE_SIZE, y * TILE_SIZE)
                        enemy_group.add(sniper)
                    elif tile == 69:                 # Inimigo Robô
                        robot = RobotEnemy(x * TILE_SIZE, y * TILE_SIZE)
                        enemy_group.add(robot)
                    elif tile == 22:                 # Caixa de Speed Boost
                        item_box = ItemBox('Speed', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 23:                 # Placa de Aviso (Warning Sign)
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile in (36, 40, 42, 49):  # Decorações de neve (boneco, placa, árvores)
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile in (37, 38, 43, 44, 45):  # Água gelada de superfície
                        water = Water(x * TILE_SIZE, y * TILE_SIZE, [
                            assets.tile_images[37],
                            assets.tile_images[43],
                            assets.tile_images[44],
                            assets.tile_images[45]
                        ])
                        water_group.add(water)
                    elif tile in (39, 46):            # Água gelada profunda
                        water = Water(x * TILE_SIZE, y * TILE_SIZE, [assets.tile_images[tile]])
                        water_group.add(water)

        return player, health_bar

    def draw(self, screen, screen_scroll):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])

# ======================================================================
#  ROBOT BULLET
# ======================================================================
class RobotBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = BULLET_SPEED
        self.image = pygame.image.load('img/robot/Ball1.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction
        self.has_hit = False
        self.hit_timer = 0

    def update(self, screen_scroll, obstacle_list, player,
               bullet_group, enemy_group):
        
        if self.has_hit:
            self.hit_timer += 1
            if self.hit_timer > 2:
                self.kill()
            self.rect.x += screen_scroll
            return

        # Mover
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
        if not self.has_hit and pygame.sprite.collide_rect(player, self):
            if player.alive and player.invincible == 0:
                player.health -= BULLET_DAMAGE_TO_PLAYER
                player.invincible = 60
                self.has_hit = True

# ======================================================================
#  ROBOT ENEMY
# ======================================================================
class RobotEnemy(Character):
    def __init__(self, x, y, scale=ENEMY_SCALE, speed=1,
                 ammo=ENEMY_AMMO, grenades=ENEMY_GRENADES):
        super().__init__('enemy', x, y, scale, speed, ammo, grenades)
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, ENEMY_VISION_WIDTH, ENEMY_VISION_HEIGHT)
        self.idling = False
        self.idling_counter = 0
        self.flip_cooldown = 0
        self.turn_after_idle = False
        
        # Override animation list com o extrator de sprite strips do robô
        self.animation_list = []
        animations = [
            ('Idle', 4),    # action 0
            ('Walk', 4),    # action 1
            ('Attack', 4),  # action 2
            ('Death', 4),   # action 3
            ('Hurt', 2)     # action 4
        ]
        
        for anim, num_frames in animations:
            img = pygame.image.load(f'img/robot/{anim}.png').convert_alpha()
            frame_width = img.get_width() // num_frames
            frame_height = img.get_height()
            
            temp_list = []
            for i in range(num_frames):
                # Extrai cada frame usando subsurface
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
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def _is_edge_ahead(self, obstacle_list):
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

    def move(self, moving_left, moving_right, obstacle_list, water_group):
        dx = self._calculate_movement(moving_left, moving_right)
        dy = 0
        self._apply_gravity()
        dy += self.vel_y
        dx, dy = self._check_tile_collisions(dx, dy, obstacle_list)
        self._check_environment(water_group)
        self.rect.x += dx
        self.rect.y += dy

    def shoot(self, bullet_group):
        """Sobrescreve tiro para usar RobotBullet."""
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = SHOOT_COOLDOWN
            spawn_x = self.rect.centerx + (self.rect.width * 0.9 * self.direction)
            spawn_y = self.rect.centery - 5
            
            bullet = RobotBullet(
                spawn_x,
                spawn_y,
                self.direction,
            )
            bullet_group.add(bullet)
            self.ammo -= 1

    def ai(self, player, screen_scroll, obstacle_list, water_group, bullet_group):
        if self.flip_cooldown > 0:
            self.flip_cooldown -= 1

        if self.alive and player.alive:
            # Jogador dentro do campo de visão -> atirar
            if self.vision.colliderect(player.rect):
                if player.rect.centerx < self.rect.centerx:
                    self.direction = -1
                    self.flip = True
                else:
                    self.direction = 1
                    self.flip = False
                
                self.update_action(2)  # Attack animation (action 2)
                self.shoot(bullet_group)
            else:
                if not self.idling and random.randint(1, 200) == 1:
                    self.update_action(0)  # Idle
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

                    self.update_action(1)  # Walk animation (action 1)
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
                    self.update_action(0)  # Garante que continua em animação de idle
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
                        if self.turn_after_idle:
                            self.direction *= -1
                            self.turn_after_idle = False

        self.rect.x += screen_scroll
        self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

# ======================================================================
#  SKELETON ARROW
# ======================================================================
class Arrow(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        pygame.sprite.Sprite.__init__(self)
        self.speed = int(BULLET_SPEED * 0.75)  # 25% mais lento para balancear
        
        self.original_image = pygame.image.load('img/skeleton/Arrow.png').convert_alpha()
        self.original_image = pygame.transform.scale(self.original_image, (60, 30))
        
        # Calcular ângulo
        dx = target_x - x
        dy = target_y - y
        angle = math.atan2(dy, dx)
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed
        
        # Guardar posição real em float
        self.x = float(x)
        self.y = float(y)
        
        # Rotacionar a imagem
        self.image = pygame.transform.rotate(self.original_image, math.degrees(-angle))
        self.rect = self.image.get_rect(center=(x, y))

        self.has_hit = False
        self.hit_timer = 0

    def update(self, screen_scroll, obstacle_list, player,
               bullet_group, enemy_group):
        
        if self.has_hit:
            self.hit_timer += 1
            if self.hit_timer > 2:
                self.kill()
            self.x += screen_scroll
            self.rect.centerx = int(self.x)
            return

        # Mover - multidirecional com float
        self.x += self.dx + screen_scroll
        self.y += self.dy
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        
        # Fora da tela
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()
            return
            
        # Colisão com tiles
        for tile in obstacle_list:
            if tile[1].colliderect(self.rect):
                self.has_hit = True
                break
                
        # Colisão com jogador
        if not self.has_hit and pygame.sprite.collide_rect(player, self):
            if player.alive and player.invincible == 0:
                player.health -= BULLET_DAMAGE_TO_PLAYER
                player.invincible = 60
                self.has_hit = True

# ======================================================================
#  SKELETON ENEMY
# ======================================================================
class SkeletonEnemy(Character):
    # Ajuste fino: scale 0.8 parece o ideal para bater com o tamanho do player
    def __init__(self, x, y, scale=0.8, speed=1,
                 ammo=9999, grenades=ENEMY_GRENADES):
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
            # Lógica de fatiamento dinâmico baseada em quadrados perfeitos
            frame_height = img.get_height()
            frame_width = frame_height
            num_frames = img.get_width() // frame_width
            
            temp_list = []
            for i in range(num_frames):
                frame = img.subsurface((i * frame_width, 0, frame_width, frame_height))
                # Correção de escala durante a extração
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
        
        # Correção de Posicionamento - alinhar os pés ao chão
        self.rect.midbottom = (x + TILE_SIZE // 2, y + TILE_SIZE)
        
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        super().update()
        # Atualizar variável de flip baseada na direção a cada frame
        self.flip = True if self.direction == -1 else False

    def _is_edge_ahead(self, obstacle_list):
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

    def move(self, moving_left, moving_right, obstacle_list, water_group):
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
        # Reset da trava no início de cada ciclo de animação
        if self.frame_index == 0:
            self.shot_fired = False

    def shoot(self, bullet_group, target_x, target_y):
        """Dispara a flecha APENAS quando a animação atingir o frame correto."""
        # Trava Blindada: Frame exato e flag False
        if self.action == 2 and self.frame_index == 9 and not self.shot_fired:
            self.shot_fired = True # Bloqueia imediatamente
            
            spawn_x = self.rect.centerx + (self.rect.width * 0.9 * self.direction)
            spawn_y = self.rect.centery - 15  # Elevação do arco um pouco mais alta para evitar chão imediato
                
            bullet = Arrow(spawn_x, spawn_y, target_x, target_y)
            bullet_group.add(bullet)
            self.ammo -= 1

    def ai(self, player, screen_scroll, obstacle_list, water_group, bullet_group):
        if self.flip_cooldown > 0:
            self.flip_cooldown -= 1

        if self.alive and player.alive:
            dist_x = player.rect.centerx - self.rect.centerx
            dist_y = player.rect.centery - self.rect.centery
            dist = math.hypot(dist_x, dist_y)
            
            # Verifica raio e linha de visão
            line_of_sight = False
            if dist < self.vision_radius:
                line_of_sight = True
                p1 = self.rect.center
                p2 = player.rect.center
                # Itera sobre os tiles sólidos (obstacle_list)
                for tile in obstacle_list:
                    if tile[1].clipline(p1, p2):
                        line_of_sight = False
                        break
            
            # Jogador dentro do raio de visão E sem paredes bloqueando
            if line_of_sight:
                if player.rect.centerx < self.rect.centerx:
                    self.direction = -1
                else:
                    self.direction = 1
                
                if self.ammo > 0:
                    self.update_action(2)  # Attack animation (action 2 -> Shot_1)
                    self.shoot(bullet_group, player.rect.centerx, player.rect.centery)
                else:
                    self.update_action(0)  # Fica parado olhando sem atirar
            else:
                if not self.idling and random.randint(1, 200) == 1:
                    self.update_action(0)  # Idle
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

                    self.update_action(1)  # Walk animation (action 1)
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
                    self.update_action(0)  # Garante que continua em animação de idle
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
                        if self.turn_after_idle:
                            self.direction *= -1
                            self.turn_after_idle = False

        self.rect.x += screen_scroll
