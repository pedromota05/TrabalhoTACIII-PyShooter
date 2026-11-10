"""
network/server.py — Servidor UDP para partidas LAN do PyShooter.

Baseado na arquitetura de threads do professor (tac3/exemplos/threads/server.py),
suportando controle de timeout, broadcast de estado entre jogadores e
encerramento gracioso de thread.
"""

import socket
import threading
import time
from typing import Dict, Any, Tuple
from .protocol import DEFAULT_PORT, TIMEOUT_LIMIT, encode_remove


class GameServer:
    """
    Servidor UDP que gerencia conexões e repassa mensagens entre jogadores
    na mesma rede local (LAN).
    """

    def __init__(self, host: str = "0.0.0.0", port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.running = False
        self.server_thread: threading.Thread | None = None
        self.socket: socket.socket | None = None

        # clients: {player_id: {"address": (ip, port), "last_seen": timestamp}}
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def start(self) -> bool:
        """Inicia o servidor UDP em uma thread daemon."""
        if self.running:
            return True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind((self.host, self.port))
            self.socket.settimeout(1.0)  # Evita travamento no recvfrom
            self.running = True

            self.server_thread = threading.Thread(target=self._run_loop, daemon=True)
            self.server_thread.start()
            print(f"[SERVIDOR] Servidor PyShooter iniciado em {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[SERVIDOR ERRO] Falha ao iniciar na porta {self.port}: {e}")
            self.running = False
            if self.socket:
                try:
                    self.socket.close()
                except Exception:
                    pass
                self.socket = None
            return False

    def _run_loop(self) -> None:
        """Loop de escuta e gerenciamento de clientes em background."""
        while self.running:
            current_time = time.time()

            # 1. Recepção de pacotes
            try:
                if self.socket is None:
                    break
                data, client_address = self.socket.recvfrom(1024)
                message = data.decode("utf-8")

                parts = message.split(",")
                if len(parts) >= 2:
                    player_id = parts[0]
                    cmd = parts[1]

                    with self.lock:
                        if cmd == "quit":
                            if player_id in self.clients:
                                del self.clients[player_id]
                                disconnect_msg = encode_remove(player_id).encode("utf-8")
                                for c_id, c_info in self.clients.items():
                                    try:
                                        self.socket.sendto(disconnect_msg, c_info["address"])
                                    except Exception:
                                        pass
                                print(f"[SERVIDOR LOGOUT] {player_id} desconectou.")
                            continue

                        # Registra ou atualiza heartbeat do cliente
                        if player_id not in self.clients:
                            print(f"[SERVIDOR CONEXÃO] {player_id} conectado de {client_address}.")

                        self.clients[player_id] = {
                            "address": client_address,
                            "last_seen": current_time,
                        }

                        # Broadcast de dados para todos os outros clientes
                        for c_id, c_info in self.clients.items():
                            if c_id != player_id:
                                try:
                                    self.socket.sendto(data, c_info["address"])
                                except Exception:
                                    pass

            except socket.timeout:
                pass
            except Exception as e:
                if self.running:
                    print(f"[SERVIDOR ERRO LOOP] {e}")

            # 2. Verificação de timeout por inatividade
            with self.lock:
                inactive = [
                    p_id for p_id, p_info in self.clients.items()
                    if current_time - p_info["last_seen"] > TIMEOUT_LIMIT
                ]

                for p_id in inactive:
                    print(f"[SERVIDOR TIMEOUT] {p_id} desconectado por inatividade.")
                    del self.clients[p_id]
                    remove_msg = encode_remove(p_id).encode("utf-8")
                    for c_id, c_info in self.clients.items():
                        try:
                            if self.socket:
                                self.socket.sendto(remove_msg, c_info["address"])
                        except Exception:
                            pass

    def stop(self) -> None:
        """Encerra o servidor e libera recursos de rede."""
        if not self.running:
            return

        print("[SERVIDOR] Encerrando servidor...")
        self.running = False

        if self.socket:
            try:
                # Notifica todos os clientes que o servidor fechou
                with self.lock:
                    for c_info in self.clients.values():
                        try:
                            self.socket.sendto(b"server,remove", c_info["address"])
                        except Exception:
                            pass
                self.socket.close()
            except Exception:
                pass
            self.socket = None

        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.5)
        self.server_thread = None
        self.clients.clear()
        print("[SERVIDOR] Servidor encerrado.")
