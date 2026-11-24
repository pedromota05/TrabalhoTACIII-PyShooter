# Tarefa: Host escolhe a fase ou o Modo Desafio antes da partida multiplayer

## Objetivo
Hoje "Criar servidor" já entra direto na fase 1. Passa a abrir a tela de seleção de fases (a mesma do modo 1 jogador, com o Modo Desafio se estiver liberado). O Host escolhe e a partida começa nessa fase ou no Desafio; o cliente segue o Host, inclusive no Desafio.

## Já feito (não refazer)
- Tela de fases: `ui/screens/level_select.py`, `update(screen, game)`: clique numa fase faz `game.level = i + 1 ... game._load_level(...)`; clique no Desafio chama `game.start_challenge()`; o Desafio só aparece liberado se `saved['campanha_zerada']`.
- `game.start_multiplayer_host(self, port=5555)` e `start_challenge(self)` em `game.py`. `start_multiplayer_host` cria servidor e cliente de rede, liga `is_multiplayer/is_host`, define `self.level = 1`, vidas (`self.lives = SHARED_LIVES` etc.: MANTER essas linhas) e carrega a fase.
- `ui/screens/multiplayer_menu.py`: o botão Host chama `game.start_multiplayer_host()` e mostra `self.status_msg`.
- ESC na tela de fases volta para o MENU: `core/input_handler.py` (`if game.state in (GameState.INSTRUCTIONS, GameState.LEVEL_SELECT, GameState.MULTIPLAYER_MENU): game.state = GameState.MENU`).
- Fase anunciada pelo Host: `encode_level(player_id, level, victory)` / `parse_packet` "level" em `network/protocol.py`; `send_level` e `get_host_level` em `network/client.py`; o cliente aplica em `sync_multiplayer_level` (`core/gameplay.py`), ramo do cliente: `level, victory = announced` e `elif level != game.level:` recarrega a fase.
- Transição do Desafio: `update_challenge_transition(game)` em `core/gameplay.py` (usa `game.challenge_index` e `game.challenge_levels`).
- Morte: `GameOverScreen.restart(game)` em `ui/screens/game_over.py` (Desafio -> `game.start_challenge()`; multiplayer -> `respawn_multiplayer`).

## Arquivos permitidos
- `game.py`
- `ui/screens/level_select.py`
- `ui/screens/multiplayer_menu.py`
- `ui/screens/game_over.py`
- `core/input_handler.py`
- `core/gameplay.py`
- `network/protocol.py`
- `network/client.py`
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. `game.py`:
   - no `__init__`: `self.mp_host_pick = False`;
   - `start_multiplayer_host(self, port: int = 5555, level: int = 1, challenge: bool = False)`: depois de configurar a rede e as variáveis (vidas, `is_multiplayer`, `is_host` etc.), se `challenge`: chamar `self.start_challenge()` e `return True`; senão usar `self.level = level` no lugar de `self.level = 1` (o resto igual).
2. `ui/screens/multiplayer_menu.py`: o clique no botão Host passa a fazer só
   ```python
   self.status_msg = ""
   game.mp_host_pick = True
   game.state = GameState.LEVEL_SELECT
   ```
   E desenhar uma linha de ajuda abaixo do subtítulo, com `self.font`, branco com contorno (`draw_text_with_outline`): "Quem cria o servidor escolhe a fase (ou o Desafio)". Ajuste o Y para não encostar no subtítulo nem no botão (subtítulo em `SUBTITLE_Y = 120`, botões começam em `STACK_START_Y = 190`; se não couber, aumente `STACK_START_Y` para 210).
3. `ui/screens/level_select.py`, em `update`:
   - título: `'MULTIPLAYER: ESCOLHA A FASE'` quando `getattr(game, 'mp_host_pick', False)`, senão o atual;
   - clique numa fase com `mp_host_pick`: `game.mp_host_pick = False` e `ok = game.start_multiplayer_host(level=i + 1)`; se não `ok`: `game.multiplayer_screen.status_msg = "Erro ao iniciar o servidor na porta 5555."`, `game.multiplayer_screen.status_color = RED` e `game.state = GameState.MULTIPLAYER_MENU`. Sem `mp_host_pick`, o código atual continua igual;
   - clique no Desafio com `mp_host_pick`: igual, mas `game.start_multiplayer_host(challenge=True)`;
   - dica de baixo: com `mp_host_pick`, "ESC volta para o Multiplayer".
4. `core/input_handler.py`: no ESC, antes da regra que manda para o MENU:
   ```python
   if game.state == GameState.LEVEL_SELECT and getattr(game, 'mp_host_pick', False):
       game.mp_host_pick = False
       game.state = GameState.MULTIPLAYER_MENU
   elif ... (regra atual)
   ```
   Também: ao sair da tela de fases para o menu por qualquer outro caminho, nada muda.
5. `network/protocol.py`: `encode_level(player_id, level, victory=False, challenge=False)` acrescenta um 5º campo `1`/`0` (`f"{player_id},level,{level},{1 if victory else 0},{1 if challenge else 0}"`); no parse de "level", `"challenge": len(parts) >= 5 and parts[4] == "1"` (continua exigindo só `len(parts) >= 4`).
6. `network/client.py`: `send_level(self, level, victory=False, challenge=False)`; no `__init__` `self.host_challenge = False`; no `_receive_loop` do "level" guardar também `self.host_challenge = packet.get("challenge", False)` (a tupla `host_level` continua `(level, victory)`); método `get_host_challenge()` com lock; zerar no `disconnect`.
7. `core/gameplay.py`:
   a. Em TODAS as chamadas `send_level(` deste arquivo, passar `challenge=getattr(game, 'challenge_mode', False)` (procure todas; há em `sync_multiplayer_level`, `update_level_transition` e nas vidas).
   b. Em `update_level_transition`, no ramo do Desafio, depois de `update_challenge_transition(game)` e antes do `return`: se for Host em multiplayer, `host_net.send_level(game.level, game.state == GameState.VICTORY, challenge=True)` (calcule `host_net` antes, como já é feito mais abaixo na função).
   c. Ramo do cliente em `sync_multiplayer_level`: depois de `level, victory = announced`:
      ```python
      challenge = net.get_host_challenge()
      mode_changed = challenge != getattr(game, 'challenge_mode', False)
      if mode_changed:
          game.challenge_mode = challenge
          if challenge:
              game.run_frames = 0
      if challenge and level in game.challenge_levels:
          game.challenge_index = game.challenge_levels.index(level)
      ```
      e trocar `elif level != game.level:` por `elif level != game.level or mode_changed:` (recarregar a fase tira as bandeiras de checkpoint no Desafio).
8. `ui/screens/game_over.py`, `restart(game)`: testar `is_multiplayer` ANTES do Desafio (no multiplayer, mesmo no Desafio, renasce ao lado do parceiro com `respawn_multiplayer`; recomeçar o Desafio sozinho dessincroniza). Em `update`, o texto "DESAFIO ENCERRADO" só em 1 jogador.

## O que NÃO fazer
- Não mudar o fluxo do modo 1 jogador (menu de fases sem `mp_host_pick` funciona igual).
- Não mudar `network/server.py`, `tools/`, nem o cliente "Conectar" (ele continua entrando e seguindo o Host).
- Não rodar comandos, não instalar nada, não fazer commit.

## Verificação (eu rodo)
- `python tools/teste_multiplayer.py --porta 5601` (chama `start_multiplayer_host(porta)` direto: tem que continuar funcionando com os parâmetros novos opcionais).
- `python tools/bot_fases.py --desafio --god`.

## Critério de pronto
Criar servidor abre a tela de fases; escolher fase ou Desafio inicia a partida; o cliente entra na mesma fase/modo; ESC volta para o Multiplayer.
