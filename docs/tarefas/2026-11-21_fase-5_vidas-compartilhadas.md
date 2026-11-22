# Tarefa: vidas compartilhadas (campanha, 1 ou 2 jogadores)

## Objetivo
Hoje toda morte mostra GAME OVER. Passa a existir um contador de VIDAS (3) na campanha, compartilhado entre os dois jogadores no multiplayer. Morrer com vida sobrando gasta 1 vida e mostra "VOCÊ CAIU!" com o botão de continuar. Só quando as vidas acabam aparece o GAME OVER de verdade. O Modo Desafio NÃO muda.

## Regras
- Começo de partida (escolher fase no menu de fases, criar servidor, conectar): `game.lives = SHARED_LIVES` (3).
- As vidas passam de uma fase para a outra (não recarregam ao trocar de fase).
- Cada morte: se `lives > 0` -> `lives -= 1` e o jogador pode continuar (`game.death_had_life = True`). Se já era 0 -> sem vidas (`game.death_had_life = False`).
- 1 jogador sem vidas: GAME OVER + botão Restart recomeça a FASE do zero (sem checkpoint) com `lives = SHARED_LIVES`.
- Multiplayer: o HOST é a autoridade das vidas. Cliente que morre avisa o Host ("death"); o Host desconta e anuncia "lives" para todos. Quem fica sem vidas espera ("Aguardando o parceiro..."), sem botão. Se o Host está sem vidas e todos os jogadores estão mortos, depois de 3 s o Host recomeça a fase para todos com `lives = SHARED_LIVES` (contador `reset` no anúncio faz o cliente recarregar).

## Já feito (não refazer)
- A morte é detectada em `update_playing` (`core/gameplay.py`), no `else:` final do `if game.player.alive:` (`game.state = GameState.GAME_OVER`). Esse `else` roda UMA vez por morte (o estado sai de PLAYING).
- Host anuncia a fase a cada `LEVEL_ANNOUNCE_FRAMES` em `sync_multiplayer_level(game)` (`core/gameplay.py`), que roda todo quadro, inclusive no GAME_OVER. O cliente lê o anúncio no mesmo função.
- Tela de morte: `ui/screens/game_over.py`, `update` (desenha o GIF `self.go_frames` e o botão) e `restart(game)` (Desafio -> `start_challenge`; multiplayer -> `respawn_multiplayer`; 1 jogador -> `respawn(game)` no checkpoint). `restart` é usado pelo teste automático: manter o nome e o comportamento atual quando há vida.
- HUD: `draw_game_entities` em `core/renderer.py` (munição em y=35, granada y=60, speed boost y=85; "FASE N/4" no topo central).
- Rede: `network/protocol.py` (comandos novos ANTES do bloco final `try: x = float(parts[1])`), `network/client.py` (siga o padrão dos comandos `item`/`level` já existentes: lista/valor protegido por `self.lock`, `send_*` e `pop_*`/`get_*`, limpar no `disconnect`).
- Início das partidas: `start_multiplayer_host` e `start_multiplayer_client` em `game.py`; escolha de fase em `ui/screens/level_select.py` (bloco que faz `game.level = i + 1` e `game._load_level(game.level)`).

## Arquivos permitidos
- `config.py`
- `game.py`
- `core/gameplay.py`
- `core/renderer.py`
- `ui/screens/game_over.py`
- `ui/screens/level_select.py`
- `network/protocol.py`
- `network/client.py`
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. `config.py`: `SHARED_LIVES = 3  # vidas da campanha (compartilhadas no multiplayer)` e `LIVES_RESET_FRAMES = 180  # 3 s até o Host recomeçar a fase sem vidas`.
2. `game.py`:
   - no `__init__`: `self.lives = SHARED_LIVES`, `self.death_had_life = True`, `self.death_seq = 0`, `self.lives_reset_counter = 0`, `self.lives_reset_seen = 0`, `self.lives_reset_frames = 0`, `self.processed_deaths = set()`;
   - em `start_multiplayer_host` e `start_multiplayer_client`, junto de `self.level = 1`: `self.lives = SHARED_LIVES`, `self.lives_reset_counter = 0`, `self.lives_reset_seen = 0`, `self.processed_deaths = set()`.
3. `ui/screens/level_select.py`: no bloco que escolhe a fase (antes de `game._load_level(game.level)`), `game.lives = SHARED_LIVES`.
4. `network/protocol.py`:
   - `encode_death(player_id, seq)` -> `f"{player_id},death,{seq}"`; parse -> `{"type": "death", "player_id", "seq": int}`;
   - `encode_lives(player_id, lives, reset)` -> `f"{player_id},lives,{lives},{reset}"`; parse -> `{"type": "lives", "player_id", "lives": int, "reset": int}`.
5. `network/client.py`:
   - `__init__`: `self.pending_deaths: List[tuple[str, int]] = []` e `self.host_lives: tuple[int, int] | None = None`;
   - `_receive_loop`: `death` -> `self.pending_deaths.append((p_id, packet["seq"]))`; `lives` -> `self.host_lives = (packet["lives"], packet["reset"])`;
   - `send_death(self, seq)` envia 3 vezes; `pop_deaths()`; `send_lives(self, lives, reset)`; `get_host_lives()`;
   - limpar os dois no `disconnect`.
6. `core/gameplay.py`:
   a. Nova função, chamada no `else:` da morte em `update_playing`, ANTES de `game.state = GameState.GAME_OVER`:
      ```python
      def register_death(game) -> None:
          """Gasta uma vida (campanha). No cliente, o Host confirma pelo anúncio 'lives'."""
          if getattr(game, 'challenge_mode', False):
              game.death_had_life = True  # Desafio tem regra própria
              return
          game.death_had_life = game.lives > 0
          game.lives = max(0, game.lives - 1)
          net = game.network_client if getattr(game, 'is_multiplayer', False) else None
          if net is None:
              return
          if game.is_host:
              net.send_lives(game.lives, game.lives_reset_counter)
          else:
              game.death_seq += 1
              net.send_death(game.death_seq)
      ```
   b. Em `sync_multiplayer_level`, no ramo do Host (antes do `return`):
      ```python
      for pid, seq in net.pop_deaths():
          if (pid, seq) not in game.processed_deaths and not getattr(game, 'challenge_mode', False):
              game.processed_deaths.add((pid, seq))
              game.lives = max(0, game.lives - 1)
              net.send_lives(game.lives, game.lives_reset_counter)
      if game.net_frames % LEVEL_ANNOUNCE_FRAMES == 1:
          net.send_lives(game.lives, game.lives_reset_counter)
      # Sem vidas e todos mortos: recomeça a fase para todos
      everyone_dead = (game.state == GameState.GAME_OVER and not game.player.alive
                       and all(not r.alive for r in game.remote_players_group))
      if everyone_dead and game.lives == 0 and not getattr(game, 'challenge_mode', False):
          game.lives_reset_frames += 1
          if game.lives_reset_frames >= LIVES_RESET_FRAMES:
              restart_level_with_lives(game)
              game.lives_reset_counter += 1
              net.send_lives(game.lives, game.lives_reset_counter)
              net.send_level(game.level)
      else:
          game.lives_reset_frames = 0
      ```
   c. No ramo do cliente de `sync_multiplayer_level`, logo no começo (depois de testar `net`): 
      ```python
      lives_info = net.get_host_lives()
      if lives_info is not None:
          game.lives, reset = lives_info
          if reset > game.lives_reset_seen:
              game.lives_reset_seen = reset
              restart_level_with_lives(game)
      ```
      Atenção: no cliente esse bloco vem ANTES do `announced = net.get_host_level()` e não pode impedir o resto da função de rodar.
   d. Função:
      ```python
      def restart_level_with_lives(game) -> None:
          """Recomeça a fase atual do zero (sem checkpoint) com as vidas cheias."""
          game.lives = SHARED_LIVES
          game.lives_reset_frames = 0
          game.start_intro = True
          game._load_level(game.level)
          game.game_over_screen.death_fade.fade_counter = 0
          game.state = GameState.PLAYING
      ```
      Importar `SHARED_LIVES`, `LIVES_RESET_FRAMES` de `config`.
7. `ui/screens/game_over.py`:
   - em `update`, depois do fade terminar: se `challenge_mode` -> comportamento atual inteiro (GIF, textos, botão), sem mudança;
   - senão, se `game.death_had_life`: NÃO desenhar o GIF; desenhar com `draw_text_with_outline` "VOCÊ CAIU!" (fonte `self.challenge_font`, branco, y = SCREEN_HEIGHT//2 - 120) e "Vidas restantes: N" (`self.info_font`, y = SCREEN_HEIGHT//2 - 50); botão Restart como hoje (chama `self.restart(game)`);
   - senão (sem vidas): desenhar o GIF como hoje e "SEM VIDAS" (`self.info_font`, CHALLENGE_RED, y=40). Em 1 jogador: botão Restart chama `restart_level_with_lives(game)` (de `core.gameplay`) e zera `self.death_fade.fade_counter`. Em multiplayer: sem botão; texto "Reiniciando a fase..." se `game.is_host and game.lives_reset_frames > 0`, senão "Aguardando o parceiro...".
   - `restart(game)` continua igual (é o caminho com vida).
8. `core/renderer.py`, em `draw_game_entities`, quando NÃO for `challenge_mode`: no canto superior direito, texto "VIDAS:" com `game.font_bold` em `(SCREEN_WIDTH - 200, 10)` e, à direita dele, `game.lives` círculos vermelhos (raio 8, contorno preto 2 px) espaçados 22 px, centro em y=22. Use `getattr(game, 'lives', 0)`.

## O que NÃO fazer
- Não mudar o Modo Desafio, `respawn`, `respawn_multiplayer`, `network/server.py`, `tools/`.
- Não mudar o formato dos pacotes existentes.
- Não rodar comandos, não instalar nada, não fazer commit.

## Verificação (eu rodo)
- `python tools/bot_fases.py todas` e `python tools/bot_fases.py --desafio --god` passam.
- `python tools/teste_multiplayer.py --porta 5601`: itens 6 e 7 OK.

## Critério de pronto
HUD mostra as vidas; morrer com vida mostra "VOCÊ CAIU!" e continua; sem vidas mostra GAME OVER; no multiplayer as vidas são as mesmas nos dois PCs.
