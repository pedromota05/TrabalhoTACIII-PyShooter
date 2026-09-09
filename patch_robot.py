import math

with open('entities.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update RobotBullet to use vel_x and vel_y
content = content.replace(
    '''class RobotBullet(pygame.sprite.Sprite):
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
            return''',
    '''class RobotBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, vel_x, vel_y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/robot/Ball1.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        
        self.vel_x = vel_x
        self.vel_y = vel_y
        
        self.x = float(x)
        self.y = float(y)
        
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

        # Mover (teleguiado/vetores)
        self.x += self.vel_x + screen_scroll
        self.y += self.vel_y
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        
        # Fora da tela
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH or self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()
            return'''
)

# 2. Update RobotEnemy.shoot to take target_x, target_y and compute vectors
content = content.replace(
    '''    def shoot(self, bullet_group):
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
            AssetManager().get_sound('robot_shoot').play()''',
    '''    def shoot(self, bullet_group, target_x, target_y):
        """Sobrescreve tiro para usar RobotBullet e mira vetorial."""
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = SHOOT_COOLDOWN
            spawn_x = self.rect.centerx + (self.rect.width * 0.9 * self.direction)
            spawn_y = self.rect.centery - 5
            
            dx = target_x - spawn_x
            dy = target_y - spawn_y
            distancia = math.hypot(dx, dy)
            
            if distancia > 0:
                vel_x = (dx / distancia) * BULLET_SPEED
                vel_y = (dy / distancia) * BULLET_SPEED
            else:
                vel_x = self.direction * BULLET_SPEED
                vel_y = 0
            
            bullet = RobotBullet(spawn_x, spawn_y, vel_x, vel_y)
            bullet_group.add(bullet)
            self.ammo -= 1
            AssetManager().get_sound('robot_shoot').play()'''
)

# 3. Update RobotEnemy.ai to pass player coords to shoot
content = content.replace(
    '''                self.update_action(2)  # Attack animation (action 2)
                self.shoot(bullet_group)''',
    '''                self.update_action(2)  # Attack animation (action 2)
                self.shoot(bullet_group, player.rect.centerx, player.rect.centery)'''
)

with open('entities.py', 'w', encoding='utf-8') as f:
    f.write(content)

