"""
network/client.py — Cliente de rede UDP para multiplayer do PyShooter.

Baseado no exemplo de threads do professor (tac3/exemplos/threads/client.py),
com suporte a interpolação LERP, recepção assíncrona com threading e
sincronização de combate e animação.
"""

import socket
import threading
import time
from typing import Dict, Any, List
from .protocol import (
    DEFAULT_PORT,
    LERP_FACTOR,
    encode_player_state,
    encode_disconnect,
    encode_enemy_hit,
    encode_enemies_state,
    encode_enemy_shoot,
    encode_level,
    encode_level_request,
    encode_item_pickup,
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
        # Fila de eventos de dano em inimigos recebidos da rede: [(target_id, damage), ...]
        self.pending_enemy_hits: List[tuple[int, int]] = []
        # Dicionário de estados de inimigos sincronizados do Host:
        # {target_id: {"current": [wx, wy], "target": [wx, wy], "action": int, "direction": int, "health": int, "alive": bool, "is_boss": bool}}
        self.remote_enemies: Dict[int, Dict[str, Any]] = {}
        # Fila de disparos de inimigos disparados remotamente pelo Host
        self.pending_enemy_shoots: List[Dict[str, Any]] = []
        # Fase dos inimigos guardados em remote_enemies (lotes de outra fase limpam o dicionário)
        self.enemies_level = 0
        # Última fase anunciada pelo Host: (fase, vitória) ou None
        self.host_level: tuple[int, bool] | None = None
        # Pedidos de troca de fase recebidos dos clientes (só o Host consome)
        self.pending_level_requests: List[int] = []
        self.pending_item_pickups: List[tuple[int, int]] = []
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
                data, _ = self.socket.recvfrom(4096)
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
                    elif packet["type"] == "hit":
                        self.pending_enemy_hits.append((packet["target_id"], packet["damage"]))
                    elif packet["type"] == "level":
                        self.host_level = (packet["level"], packet["victory"])
                    elif packet["type"] == "level_request":
                        self.pending_level_requests.append(packet["level"])
                    elif packet["type"] == "enemies":
                        if packet.get("level", 0) != self.enemies_level:
                            # Fase nova: os target_id antigos não valem mais
                            self.remote_enemies.clear()
                            self.enemies_level = packet.get("level", 0)
                        for enemy_data in packet["enemies"]:
                            t_id = enemy_data["target_id"]
                            target_pos = [enemy_data["world_x"], enemy_data["world_y"]]
                            if t_id in self.remote_enemies:
                                entry = self.remote_enemies[t_id]
                                entry["target"] = target_pos
                                entry["action"] = enemy_data["action"]
                                entry["direction"] = enemy_data["direction"]
                                entry["health"] = enemy_data["health"]
                                entry["alive"] = enemy_data["alive"]
                                entry["is_boss"] = enemy_data.get("is_boss", False)
                                entry["last_seen"] = time.time()
                            else:
                                self.remote_enemies[t_id] = {
                                    "current": list(target_pos),
                                    "target": list(target_pos),
                                    "action": enemy_data["action"],
                                    "direction": enemy_data["direction"],
                                    "health": enemy_data["health"],
                                    "alive": enemy_data["alive"],
                                    "is_boss": enemy_data.get("is_boss", False),
                                    "last_seen": time.time(),
                                }
                    elif packet["type"] == "enemy_shoot":
                        self.pending_enemy_shoots.append(packet)
                    elif packet["type"] == "item":
                        self.pending_item_pickups.append((packet["level"], packet["item_id"]))
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
            except (socket.timeout, ConnectionResetError):
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

    def send_enemy_hit(self, target_id: int, damage: int) -> None:
        """Envia aviso de dano infligido a um inimigo para os demais clientes."""
        if not self.running or self.socket is None:
            return

        packet_str = encode_enemy_hit(self.player_id, target_id, damage)
        try:
            self.socket.sendto(packet_str.encode("utf-8"), self.server_address)
        except Exception:
            pass

    def pop_enemy_hits(self) -> List[tuple[int, int]]:
        """Consome e limpa a fila thread-safe de acertos em inimigos."""
        with self.lock:
            hits = list(self.pending_enemy_hits)
            self.pending_enemy_hits.clear()
            return hits

    def send_enemies_state(self, enemies_list: List[str], level: int = 0) -> None:
        """Envia o estado atualizado dos inimigos pelo Host para os clientes."""
        if not self.running or self.socket is None or not enemies_list:
            return

        payload = "|".join(enemies_list)
        packet_str = encode_enemies_state(self.player_id, payload, level)
        self._send(packet_str)

    def _send(self, packet_str: str) -> None:
        """Envia uma mensagem ao servidor, ignorando erros de rede."""
        if not self.running or self.socket is None:
            return
        try:
            self.socket.sendto(packet_str.encode("utf-8"), self.server_address)
        except Exception:
            pass

    # ---------------- Sincronização de fase ----------------
    def send_level(self, level: int, victory: bool = False) -> None:
        """Host: anuncia a fase atual (repetido periodicamente, pois UDP pode perder pacotes)."""
        self._send(encode_level(self.player_id, level, victory))

    def send_level_request(self, level: int) -> None:
        """Cliente: avisa o Host que chegou ao fim da fase `level`."""
        self._send(encode_level_request(self.player_id, level))

    def get_host_level(self) -> tuple[int, bool] | None:
        """Última fase anunciada pelo Host: (fase, vitória) ou None."""
        with self.lock:
            return self.host_level

    def pop_level_requests(self) -> List[int]:
        """Consome os pedidos de troca de fase enviados pelos clientes."""
        with self.lock:
            reqs = list(self.pending_level_requests)
            self.pending_level_requests.clear()
            return reqs

    def send_item_pickup(self, level: int, item_id: int) -> None:
        """Avisa que pegou uma caixa. Envia 3 vezes (UDP pode perder; remover é idempotente)."""
        msg = encode_item_pickup(self.player_id, level, item_id)
        for _ in range(3):
            self._send(msg)

    def pop_item_pickups(self) -> List[tuple[int, int]]:
        with self.lock:
            items = list(self.pending_item_pickups)
            self.pending_item_pickups.clear()
            return items

    def get_enemies_level(self) -> int:
        """Fase a que pertencem os inimigos guardados em remote_enemies."""
        with self.lock:
            return self.enemies_level

    def send_enemy_shoot(
        self,
        bullet_type: str,
        world_x: float,
        world_y: float,
        direction: int,
        vel_x: float = 0.0,
        vel_y: float = 0.0,
        target_wx: float = 0.0,
        target_wy: float = 0.0,
    ) -> None:
        """Envia aviso de disparo de projétil por um inimigo para os clientes."""
        if not self.running or self.socket is None:
            return

        packet_str = encode_enemy_shoot(
            self.player_id, bullet_type, world_x, world_y,
            direction, vel_x, vel_y, target_wx, target_wy
        )
        try:
            self.socket.sendto(packet_str.encode("utf-8"), self.server_address)
        except Exception:
            pass

    def pop_enemy_shoots(self) -> List[Dict[str, Any]]:
        """Consome e limpa a fila thread-safe de disparos de inimigos."""
        with self.lock:
            shoots = list(self.pending_enemy_shoots)
            self.pending_enemy_shoots.clear()
            return shoots

    def update_enemy_interpolation(self) -> None:
        """Interpola linearmente a posição dos inimigos remotos recebidos do Host."""
        with self.lock:
            for t_id, data in self.remote_enemies.items():
                curr = data["current"]
                targ = data["target"]
                # Teleporte rápido caso a distância seja excessiva (ex: spawn inicial)
                if abs(targ[0] - curr[0]) > 200 or abs(targ[1] - curr[1]) > 200:
                    curr[0] = targ[0]
                    curr[1] = targ[1]
                else:
                    curr[0] += (targ[0] - curr[0]) * LERP_FACTOR
                    curr[1] += (targ[1] - curr[1]) * LERP_FACTOR

    def get_remote_enemies_snapshot(self) -> Dict[int, Dict[str, Any]]:
        """Retorna uma cópia thread-safe dos dados atuais dos inimigos sincronizados."""
        with self.lock:
            return {
                t_id: {
                    "current": list(info["current"]),
                    "target": list(info["target"]),
                    "action": info["action"],
                    "direction": info["direction"],
                    "health": info["health"],
                    "alive": info["alive"],
                    "is_boss": info.get("is_boss", False),
                }
                for t_id, info in self.remote_enemies.items()
            }

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
            self.remote_enemies.clear()
            self.pending_enemy_shoots.clear()
            self.pending_enemy_hits.clear()
            self.pending_level_requests.clear()
            self.pending_item_pickups.clear()
            self.host_level = None
            self.enemies_level = 0
        print(f"[REDE CLIENTE] Desconectado.")
