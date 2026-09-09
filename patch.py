import sys
import math

with open('entities.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add sounds
content = content.replace(
    '''            bullet = RobotBullet(
                spawn_x,
                spawn_y,
                self.direction,
            )
            bullet_group.add(bullet)
            self.ammo -= 1''',
    '''            bullet = RobotBullet(
                spawn_x,
                spawn_y,
                self.direction,
            )
            bullet_group.add(bullet)
            self.ammo -= 1
            AssetManager().get_sound('robot_shoot').play()'''
)

content = content.replace(
    '''            bullet = Arrow(spawn_x, spawn_y, target_x, target_y)
            bullet_group.add(bullet)
            self.ammo -= 1''',
    '''            bullet = Arrow(spawn_x, spawn_y, target_x, target_y)
            bullet_group.add(bullet)
            self.ammo -= 1
            AssetManager().get_sound('skeleton_bow').play()'''
)

# 2. Air control and Explicit DX
content = content.replace(
    '''        screen_scroll = 0
        dx = self._calculate_movement(moving_left, moving_right)
        dy = 0

        # Pulo''',
    '''        screen_scroll = 0
        
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

        # Aplica o modificador de controle no ar (Air Control)
        if self.in_air:
            dx = int(dx * 0.7) # Reduz o ganho horizontal no ar para manter a precisão das plataformas

        # Pulo'''
)

# 3. Process Data Boss logic
content = content.replace(
    '''    def process_data(self, data, enemy_group, item_box_group,
                     decoration_group, water_group, exit_group):''',
    '''    def process_data(self, data, enemy_group, item_box_group,
                     decoration_group, water_group, exit_group, level=1):'''
)

content = content.replace(
    '''                    elif tile == 85:
                        # Guarda a rampa numa lista separada para não usar a colisão quadrada normal
                        self.ramp_list.append(tile_data)
                    elif tile == 70:''',
    '''                    elif tile == 85:
                        # Guarda a rampa numa lista separada para não usar a colisão quadrada normal
                        self.ramp_list.append(tile_data)
                    elif tile == 90 and level == 4:
                        boss = Boss(x * TILE_SIZE, y * TILE_SIZE)
                        enemy_group.add(boss)
                    elif tile == 70:'''
)

with open('entities.py', 'w', encoding='utf-8') as f:
    f.write(content)

