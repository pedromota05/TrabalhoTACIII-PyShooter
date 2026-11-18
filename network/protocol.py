"""
network/protocol.py — Definição do protocolo de comunicação UDP em LAN.

Inspirado no protocolo do repositório tac3 (threads/server.py e client.py),
suportando sincronização de coordenadas, ações de animação, direção e combate.
"""

from typing import Optional, Dict, Any


DEFAULT_PORT = 5555
TIMEOUT_LIMIT = 5.0
LERP_FACTOR = 0.20


def encode_player_state(
    player_id: str,
    x: float,
    y: float,
    action: int = 0,
    direction: int = 1,
    shooting: bool = False,
    health: int = 100
) -> str:
    """Serializa o estado do jogador em uma string CSV leve para envio via UDP."""
    shoot_flag = 1 if shooting else 0
    return f"{player_id},{round(x, 1)},{round(y, 1)},{action},{direction},{shoot_flag},{health}"


def encode_disconnect(player_id: str) -> str:
    """Codifica a mensagem de desconexão voluntária."""
    return f"{player_id},quit"


def encode_remove(player_id: str) -> str:
    """Codifica a mensagem enviada pelo servidor para remover um jogador."""
    return f"{player_id},remove"


def encode_enemy_hit(player_id: str, target_id: int, damage: int) -> str:
    """Codifica a notificação de dano a um inimigo sincronizado (enemy/boss)."""
    return f"{player_id},hit,{target_id},{damage}"


def encode_enemies_state(player_id: str, enemies_payload: str) -> str:
    """Codifica o lote de estados dos inimigos e chefes sincronizados pelo Host."""
    return f"{player_id},enemies,{enemies_payload}"


def encode_enemy_shoot(
    player_id: str,
    bullet_type: str,
    world_x: float,
    world_y: float,
    direction: int,
    vel_x: float = 0.0,
    vel_y: float = 0.0,
    target_wx: float = 0.0,
    target_wy: float = 0.0,
) -> str:
    """Codifica o disparo de um projétil de inimigo/chefe para sincronização."""
    return (
        f"{player_id},eshoot,{bullet_type},{round(world_x, 1)},{round(world_y, 1)},"
        f"{direction},{round(vel_x, 2)},{round(vel_y, 2)},{round(target_wx, 1)},{round(target_wy, 1)}"
    )


def parse_packet(raw_message: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica um pacote recebido na rede.
    Retorna um dicionário estruturado ou None se o pacote for inválido.
    """
    if not raw_message:
        return None

    parts = raw_message.strip().split(",")
    if len(parts) < 2:
        return None

    player_id = parts[0]
    command = parts[1]

    if command == "quit":
        return {"type": "quit", "player_id": player_id}
    if command == "remove":
        return {"type": "remove", "player_id": player_id}
    if command == "hit" and len(parts) >= 4:
        try:
            return {
                "type": "hit",
                "player_id": player_id,
                "target_id": int(parts[2]),
                "damage": int(parts[3]),
            }
        except ValueError:
            return None

    if command == "enemies" and len(parts) >= 3:
        raw_list = parts[2].split("|")
        enemies = []
        for item in raw_list:
            if not item:
                continue
            sub = item.split(":")
            if len(sub) >= 7:
                try:
                    enemies.append({
                        "target_id": int(sub[0]),
                        "world_x": float(sub[1]),
                        "world_y": float(sub[2]),
                        "action": int(sub[3]),
                        "direction": int(sub[4]),
                        "health": int(sub[5]),
                        "alive": bool(int(sub[6])),
                        "is_boss": bool(int(sub[7])) if len(sub) > 7 else False,
                    })
                except ValueError:
                    continue
        return {"type": "enemies", "player_id": player_id, "enemies": enemies}

    if command == "eshoot" and len(parts) >= 10:
        try:
            return {
                "type": "enemy_shoot",
                "player_id": player_id,
                "bullet_type": parts[2],
                "world_x": float(parts[3]),
                "world_y": float(parts[4]),
                "direction": int(parts[5]),
                "vel_x": float(parts[6]),
                "vel_y": float(parts[7]),
                "target_wx": float(parts[8]),
                "target_wy": float(parts[9]),
            }
        except (ValueError, IndexError):
            return None

    try:
        x = float(parts[1])
        y = float(parts[2])
        action = int(parts[3]) if len(parts) > 3 else 0
        direction = int(parts[4]) if len(parts) > 4 else 1
        shooting = bool(int(parts[5])) if len(parts) > 5 else False
        health = int(parts[6]) if len(parts) > 6 else 100

        return {
            "type": "state",
            "player_id": player_id,
            "x": x,
            "y": y,
            "action": action,
            "direction": direction,
            "shooting": shooting,
            "health": health,
        }
    except (ValueError, IndexError):
        return None
