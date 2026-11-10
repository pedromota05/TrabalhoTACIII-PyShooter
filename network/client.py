"""
network/client.py — Cliente de rede UDP para multiplayer do PyShooter.

Baseado no exemplo de threads do professor (tac3/exemplos/threads/client.py),
com suporte a interpolação LERP, recepção assíncrona com threading e
sincronização de combate e animação.
"""

import socket
import threading
import time
from typing import Dict, Any
from .protocol import (
    DEFAULT_PORT,
    LERP_FACTOR,
    encode_player_state,
    encode_disconnect,
    parse_packet,
)


class NetworkClient:
    """
    Cliente UDP responsável por enviar os estados do jogador local
    e receber estados de outros jogadores em segundo plano.
    """

    def __init__(self, player_id: str, server_ip: str = "127.0.0.1", server_port: int = DEFAULT_PORT):
        self.player_id = player_id
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_address = (server_ip, server_port)

        self.socket: socket.socket | None = None
        self.running = False
        self.receive_thread: threading.Thread | None = None

        # Dicionário de jogadores remotos:
        # {player_id: {"current": [x, y], "target": [x, y], "action": int, "direction": int, "shooting": bool, "health": int}}
        self.remote_players: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def connect(self) -> bool:
        """Inicializa o socket UDP e a thread de escuta."""
        if self.running:
            return True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(1.0)
            self.running = True

            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            # Envia pacote inicial de presença
            self.send_state(0, 0, action=0, direction=1, shooting=False, health=100)
            print(f"[REDE CLIENTE] Conectado ao servidor em {self.server_ip}:{self.server_port}")
            return True
        except Exception as e:
            print(f"[REDE CLIENTE ERRO] Falha ao conectar: {e}")
            self.running = False
            return False

    def _receive_loop(self) -> None:
        """Loop de escuta UDP em background."""
        while self.running:
            try:
                if self.socket is None:
                    break
                data, _ = self.socket.recvfrom(1024)
                message = data.decode("utf-8")
                packet = parse_packet(message)

                if packet is None:
                    continue

                p_id = packet["player_id"]
                if p_id == self.player_id:
                    continue  # Ignora eco próprio

                with self.lock:
                    if packet["type"] in ("quit", "remove"):
                        if p_id in self.remote_players:
                            del self.remote_players[p_id]
                    elif packet["type"] == "state":
                        target_pos = [packet["x"], packet["y"]]
                        if p_id in self.remote_players:
                            entry = self.remote_players[p_id]
                            entry["target"] = target_pos
                            entry["action"] = packet["action"]
                            entry["direction"] = packet["direction"]
                            entry["shooting"] = packet["shooting"]
                            entry["health"] = packet["health"]
                            entry["last_seen"] = time.time()
                        else:
                            self.remote_players[p_id] = {
                                "current": list(target_pos),
                                "target": list(target_pos),
                                "action": packet["action"],
                                "direction": packet["direction"],
                                "shooting": packet["shooting"],
                                "health": packet["health"],
                                "last_seen": time.time(),
                            }
            except socket.timeout:
                pass
            except Exception:
                if not self.running:
                    break

    def send_state(
        self,
        x: float,
        y: float,
        action: int = 0,
        direction: int = 1,
        shooting: bool = False,
        health: int = 100
    ) -> None:
        """Envia o estado do jogador local para o servidor."""
        if not self.running or self.socket is None:
            return

        packet_str = encode_player_state(
            self.player_id, x, y, action, direction, shooting, health
        )
        try:
            self.socket.sendto(packet_str.encode("utf-8"), self.server_address)
        except Exception:
            pass

    def update_interpolation(self) -> None:
        """
        Executado a cada frame para aplicar interpolação linear (LERP)
        suavizando a movimentação dos jogadores remotos.
        """
        with self.lock:
            for p_id, data in self.remote_players.items():
                curr = data["current"]
                targ = data["target"]
                curr[0] += (targ[0] - curr[0]) * LERP_FACTOR
                curr[1] += (targ[1] - curr[1]) * LERP_FACTOR

    def get_remote_players_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Retorna uma cópia thread-safe dos dados atuais dos jogadores remotos."""
        with self.lock:
            return {
                p_id: {
                    "current": list(info["current"]),
                    "target": list(info["target"]),
                    "action": info["action"],
                    "direction": info["direction"],
                    "shooting": info["shooting"],
                    "health": info["health"],
                }
                for p_id, info in self.remote_players.items()
            }

    def disconnect(self) -> None:
        """Envia aviso de desconexão e fecha a conexão de forma graciosa."""
        if not self.running:
            return

        self.running = False
        if self.socket:
            try:
                logout_packet = encode_disconnect(self.player_id).encode("utf-8")
                self.socket.sendto(logout_packet, self.server_address)
                self.socket.close()
            except Exception:
                pass
            self.socket = None

        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        self.receive_thread = None
        with self.lock:
            self.remote_players.clear()
        print(f"[REDE CLIENTE] Desconectado.")
