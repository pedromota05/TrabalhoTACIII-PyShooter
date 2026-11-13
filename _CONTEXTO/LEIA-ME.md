# PyShooter (TAC III)

## Objetivo
Jogo de ação 2D Run and Gun em Python e Pygame com suporte a campanha, editor de fases integrado e modo cooperativo multiplayer em LAN (UDP/threads).

## Frente
Acadêmico

## Mapa de Arquivos
- `main.py`: Ponto de entrada do jogo.
- `game.py`: Fachada (Facade) e orquestrador dos estados e loop principal.
- `core/`: Subsistemas desacoplados (`gameplay.py`, `renderer.py`, `input_handler.py`, `level_loader.py`).
- `network/`: Arquitetura cliente/servidor UDP (`server.py`, `client.py`, `protocol.py`).
- `entities/`: Entidades de combate, personagens, inimigos e jogador remoto.
- `ui/screens/`: Máquina de telas e interfaces de usuário.
- `levels/`: Matrizes CSV das fases do jogo.
- `docs/`: Documentação e GDD do Trabalho 2.
