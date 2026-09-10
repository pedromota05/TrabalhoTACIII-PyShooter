"""
entities.py — Ponto de entrada e compatibilidade retroativa para o pacote entities/.

Todas as entidades foram refatoradas e organizadas modularmente dentro da pasta entities/,
respeitando o princípio de responsabilidade única (SRP). Este arquivo atua como fachada,
reexportando todas as classes para que nenhum ponto de chamada existente seja quebrado.
"""

import os

# Define __path__ para que Python trate este módulo como o próprio pacote entities/
__path__ = [os.path.join(os.path.dirname(__file__), 'entities')]

from entities.base import Character
from entities.player import Player
from entities.enemies.standard import Enemy, Sniper
from entities.enemies.robot import RobotEnemy
from entities.enemies.skeleton import SkeletonEnemy
from entities.enemies.bosses import DragonBoss, Boss
from entities.combat.projectiles import (
    Bullet,
    Grenade,
    Explosion,
    RobotBullet,
    Arrow,
    DragonFire,
)
from entities.items import ItemBox
from entities.environment import Decoration, Water, Exit
from ui.hud import HealthBar
from ui.transitions import ScreenFade
from world.level_builder import World

__all__ = [
    'Character',
    'Player',
    'Enemy',
    'Sniper',
    'RobotEnemy',
    'SkeletonEnemy',
    'DragonBoss',
    'Boss',
    'Bullet',
    'Grenade',
    'Explosion',
    'RobotBullet',
    'Arrow',
    'DragonFire',
    'ItemBox',
    'Decoration',
    'Water',
    'Exit',
    'HealthBar',
    'ScreenFade',
    'World',
]
