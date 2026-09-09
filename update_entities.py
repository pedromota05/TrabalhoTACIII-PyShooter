import sys

with open('entities.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
'''    def update(self, screen_scroll, obstacle_list, player,
               bullet_group, enemy_group):
        # We also need boss_group here, but wait, main.py passes bullet_group.update(...)
        pass''',
'''    def update(self, screen_scroll, obstacle_list, player,
               bullet_group, enemy_group, boss_group=None):'''
)

content = content.replace(
'''    def update(self, screen_scroll, obstacle_list, player,
               bullet_group, enemy_group):''',
'''    def update(self, screen_scroll, obstacle_list, player,
               bullet_group, enemy_group, boss_group=None):'''
)

old = '''                        # Feedback visual de hit (se a animação 4 "Hurt" existir)
                        if hasattr(enemy, 'animation_list') and len(enemy.animation_list) > 4:
                            enemy.update_action(4)
                        self.has_hit = True
                        break'''

new = '''                        # Feedback visual de hit (se a animação 4 "Hurt" existir)
                        if hasattr(enemy, 'animation_list') and len(enemy.animation_list) > 4:
                            enemy.update_action(4)
                        self.has_hit = True
                        break
        
        # Colisão com Bosses
        if not self.has_hit and boss_group:
            boss_hit_list = pygame.sprite.spritecollide(self, boss_group, False)
            for boss in boss_hit_list:
                if boss.alive:
                    self.kill() # Bala some
                    boss.health -= 25
                    # Verifica se o boss morreu
                    if boss.health <= 0:
                        boss.alive = False
                        boss.update_action(3) # Troca para o estado 'Death'
                    self.has_hit = True
                    break'''

content = content.replace(old, new)

with open('entities.py', 'w', encoding='utf-8') as f:
    f.write(content)
