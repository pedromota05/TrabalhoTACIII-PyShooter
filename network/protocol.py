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
