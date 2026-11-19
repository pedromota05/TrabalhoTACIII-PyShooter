# PyShooter (TAC III)

## Objetivo
Jogo de ação 2D Run and Gun em Python e Pygame com suporte a campanha, editor de fases integrado e modo cooperativo multiplayer em LAN (UDP/threads).

## Frente
Acadêmico

## Mapa de Arquivos
- `main.py`: Ponto de entrada do jogo.
- `game.py`: Fachada (Facade) e orquestrador dos estados e loop principal.
- `core/`: Subsistemas desacoplados (`gameplay.py`, `renderer.py`, `input_handler.py`, `level_loader.py`) e `progress.py` (progresso salvo).
- `network/`: Arquitetura cliente/servidor UDP (`server.py`, `client.py`, `protocol.py`).
- `entities/`: Entidades de combate, personagens, inimigos e jogador remoto.
- `ui/screens/`: Máquina de telas e interfaces de usuário.
- `levels/`: Matrizes CSV das fases do jogo (1 a 4 da campanha; 5 é a arena do Modo Desafio).
- `tools/bot_fases.py`: Bot sem janela que joga as fases com A* (`--humano`, `--desafio`, `--capturas PASTA`).
- `tools/teste_multiplayer.py`: Teste automático do multiplayer com 2 processos (Host e Cliente) no mesmo PC; confere 7 itens. `--ip IPv4` conecta pela placa de rede; `--capturas PASTA` salva as duas telas.
- `docs/capturas/`: capturas de tela da gameplay usadas nos slides.
- `save/progresso.json`: Progresso do jogador (gerado ao jogar; não vai para o git).
- `docs/`: Documentação do Trabalho 2:
  - `T2.pdf`: enunciado (apresentação e relatório em 2026-11-24).
  - `GDD_Trabalho2.md` / `.pdf`: GDD atualizado.
  - `uml/`: diagramas PlantUML.
  - `checklist_teste_multiplayer.md`: teste manual em 2 PCs.
  - `apresentacao/2026-11-19_slides-pyshooter_v2.pptx`: slides atuais (17, com capturas); o arquivo sem `_v2` é o rascunho antigo.
  - `2026-11-19_guia-de-estudo-apresentacao.md`: guia para explicar o código na aula.

## Como rodar
- Dependências: `python -m pip install pygame-ce Pillow` (o PC da CLM não tem; testar no PC de casa).
- Jogo: `python main.py`.
- Branch de trabalho: `trabalho-parte2`; commits sem linha Co-Authored-By.
