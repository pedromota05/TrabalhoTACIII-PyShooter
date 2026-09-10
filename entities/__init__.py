"""
entities — Pacote de entidades do PyShooter.

Reexporta todas as classes para manter 100% de retrocompatibilidade com
as importações existentes no projeto.
"""

from .base import Character
from .player import Player
from .enemies import (
    Enemy,
    Sniper,
    RobotEnemy,
    SkeletonEnemy,
    DragonBoss,
    Boss,
)
from .combat import (
    Bullet,
    Grenade,
    Explosion,
    RobotBullet,
    SniperBullet,
    Arrow,
    DragonFire,
)
from .items import ItemBox
from .environment import Decoration, Water, Exit
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
    'SniperBullet',
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
