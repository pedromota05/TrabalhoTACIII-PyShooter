# PyShooter (TAC III)

## Objetivo
Jogo de ação 2D Run and Gun em Python e Pygame com suporte a campanha, editor de fases integrado e modo cooperativo multiplayer em LAN (UDP/threads).

## Frente
Acadêmico

## Mapa de Arquivos
- `main.py`: Ponto de entrada do jogo.
- `game.py`: Fachada (Facade) e orquestrador dos estados e loop principal.
- `core/`: Subsistemas desacoplados (`gameplay.py`, `renderer.py`, `input_handler.py`, `level_loader.py`), `progress.py` (progresso salvo), `horde.py` (ondas da fase 5 do Desafio) e `music.py` (música por tela/fase).
- `network/`: Arquitetura cliente/servidor UDP (`server.py`, `client.py`, `protocol.py`).
- `entities/`: Entidades de combate, personagens, inimigos (inclui a aranha) e jogador remoto; `aim_pose.py` (arma separada do sprite girando para a mira) e `effects.py` (texto flutuante e tremor de tela).
- `ui/screens/`: Máquina de telas e interfaces de usuário.
- `levels/`: Matrizes CSV das fases do jogo (1 a 4 da campanha; 5 é a arena do Modo Desafio).
- `tools/bot_fases.py`: Bot que joga as fases com A* (`--humano N`, `--desafio`, `--god`, `--visual` para assistir, `--capturas PASTA`).
- `tools/gerar_gdd.py`: gera `docs/GDD_Trabalho2.html` e `.pdf` a partir do Markdown.
- `audio/musicas/`: 14 músicas CC0 (MintoDog, OpenGameArt); créditos em `audio/CREDITOS.md`.
- `docs/tarefas/`: roteiros entregues ao Gemini (MCP `ponte-agy`) e planos.
- `tools/teste_multiplayer.py`: Teste automático do multiplayer com 2 processos (Host e Cliente) no mesmo PC; confere 7 itens. `--ip IPv4` conecta pela placa de rede; `--capturas PASTA` salva as duas telas.
- `docs/capturas/`: capturas de tela da gameplay usadas nos slides.
- `save/progresso.json`: Progresso do jogador (gerado ao jogar; não vai para o git).
- `docs/`: Documentação do Trabalho 2:
  - `T2.pdf`: enunciado (apresentação e relatório em 2026-11-24).
  - `gdd_completo/GDD_PyShooter_completo.pdf` (+ `.md`, `diagramas/`): GDD final, T1 + T2 no estilo do GDD 1, gerado por `tools/gerar_gdd_completo.py`; versão Word editável `.docx` por `tools/gerar_gdd_docx.py`.
  - `GDD_Trabalho2.md` / `.pdf`: versão anterior do GDD do T2 (mais longa).
  - `GDD - PyShoter (1).pdf`: GDD do Trabalho 1.
  - `uml/`: diagramas PlantUML (pacotes, classes em 2 partes, telas, sequência do multiplayer).
  - `checklist_teste_multiplayer.md`: teste manual em 2 PCs.
  - `apresentacao/2026-11-23_slides-pyshooter_v4.pptx`: slides atuais, versão enxuta de 13 slides (pedido do Guilherme em 2026-11-23: só o essencial do enunciado + arena dos chefes e Desafio); `_v3` (28 slides), `_v2` e o sem sufixo são versões antigas.
  - `2026-11-19_guia-de-estudo-apresentacao.md`: guia para explicar o código na aula.

## Como rodar
- Dependências: `python -m pip install pygame-ce Pillow` (o PC da CLM não tem; testar no PC de casa).
- Jogo: `python main.py`. Teste da fase 5: `python main.py --fase5` (Desafio direto na fase 5, sem gravar recorde).
- Branch de trabalho: `melhorias-coop` (desde 2026-11-21; saiu de `trabalho-parte2`); commits sem linha Co-Authored-By.
- Controles: A/D andar, W pular, mouse mira, botão esquerdo atira, botão direito golpe, ESPAÇO dash, Q/G granada, E placa, F11 tela cheia, ESC pausa.
