# Tarefa: escolher a cor do boneco (P1 e P2)

## Objetivo
Cada jogador escolhe a cor do próprio soldado na tela de Multiplayer (setas < >, com prévia). A cor fica salva, vale também no modo de 1 jogador e, no multiplayer, o parceiro vê o boneco na cor que o outro escolheu.

## Já feito (não refazer)
- Sprites do soldado: `img/player/{Idle,Run,Jump,Death}/N.png`, uniforme VERDE. Carregados por `AssetManager.load_character_animations(char_type, scale)` (`asset_manager.py`), com cache em `self._anim_cache[(char_type, scale)]`.
- `Character.__init__` (`entities/base.py`) faz `self.animation_list = assets.load_character_animations(char_type, scale)` e `self.image = self.animation_list[self.action][self.frame_index]`. `Player` (`entities/player.py`) herda de `Character` com `char_type='player'`.
- `RemotePlayer` (`entities/remote_player.py`) carrega `assets.load_character_animations('player', PLAYER_SCALE)` no `__init__`.
- Progresso salvo: `core/progress.py` (`_vazio()`, `carregar()`, `_salvar(dados)`). Siga o padrão de `marcar_campanha_zerada`.
- Rede: `network/protocol.py` (`encode_*` + `parse_packet`; comandos novos ANTES do bloco final `try: x = float(parts[1])`), `network/client.py` (`_receive_loop` com `elif packet["type"] == ...`, envio com `self._send`). Siga o padrão do comando `item` já existente.
- Jogadores remotos são criados/atualizados em `core/gameplay.py`, bloco com `remote_data = net_client.get_remote_players_snapshot()` e `game.remote_players_map[p_id].update_from_network(...)`.
- O estado do jogador é enviado em `update_playing` (`core/gameplay.py`) com `game.network_client.send_state(...)`.
- Tela: `ui/screens/multiplayer_menu.py` (`handle_event` e `update`; o bloco Host/IP/Conectar/Voltar fica centralizado em X).

## Arquivos permitidos
- `config.py`
- `asset_manager.py`
- `core/progress.py`
- `entities/player.py`
- `entities/remote_player.py`
- `network/protocol.py`
- `network/client.py`
- `core/gameplay.py`
- `ui/screens/multiplayer_menu.py`
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. `config.py` (perto de `PLAYER_SCALE`):
   ```python
   # Cores do soldado: (nome, matiz HSV de destino; None = original verde)
   PLAYER_COLORS = [('VERDE', None), ('AZUL', 215), ('VERMELHO', 0), ('AMARELO', 50), ('ROXO', 285)]
   ```
2. `asset_manager.py`:
   a. Função de módulo (fora da classe):
      ```python
      def recolor_surface(surf: pygame.Surface, target_hue: int) -> pygame.Surface:
          """Troca só os tons verdes (uniforme) pelo matiz pedido; pele e arma ficam iguais."""
          out = surf.copy()
          w, h = out.get_size()
          for x in range(w):
              for y in range(h):
                  c = out.get_at((x, y))
                  if c.a == 0:
                      continue
                  hue, sat, val, alpha = c.hsva
                  if 70 <= hue <= 170 and sat >= 20:
                      c.hsva = (target_hue, sat, val, alpha)
                      out.set_at((x, y), c)
          return out
      ```
   b. `load_character_animations(self, char_type, scale, color: int = 0)`: a chave do cache passa a ser `(char_type, scale, color)`. Se `color > 0`, carrega a lista base com `self.load_character_animations(char_type, scale, 0)` e devolve uma nova lista com cada frame passado por `recolor_surface(frame, PLAYER_COLORS[color][1])` (guardando no cache). Índice inválido -> usar 0. Importar `PLAYER_COLORS` de `config`.
3. `core/progress.py`:
   - `_vazio()` ganha `'cor_jogador': 0`;
   - em `carregar()`, ler `dados['cor_jogador'] = int(lido.get('cor_jogador', 0))`;
   - nova função `def salvar_cor(indice: int) -> None:` que carrega, troca `cor_jogador` e salva (padrão de `marcar_campanha_zerada`).
4. `entities/player.py`, no fim do `__init__` do `Player`:
   ```python
   from core import progress  # import local evita ciclo
   self.color = progress.carregar().get('cor_jogador', 0)
   if self.color:
       self.animation_list = AssetManager().load_character_animations('player', scale, self.color)
       self.image = self.animation_list[self.action][self.frame_index]
   ```
   (importar `AssetManager` se ainda não estiver importado.)
5. `entities/remote_player.py`: atributo `self.color = 0` no `__init__` e método
   ```python
   def set_color(self, color: int) -> None:
       if color == self.color:
           return
       self.color = color
       self.animation_list = AssetManager().load_character_animations('player', PLAYER_SCALE, color)
       self.frame_index = min(self.frame_index, len(self.animation_list[self.action]) - 1)
   ```
6. `network/protocol.py`: `encode_color(player_id, color) -> f"{player_id},color,{color}"` e no `parse_packet`: `{"type": "color", "player_id": ..., "color": int(parts[2])}` (com try/except ValueError, `len(parts) >= 3`).
7. `network/client.py`: `self.remote_colors: Dict[str, int] = {}` no `__init__`; no `_receive_loop`: `elif packet["type"] == "color": self.remote_colors[p_id] = packet["color"]`; métodos `send_color(self, color)` e `get_remote_color(self, player_id) -> int` (com lock, padrão 0); limpar `remote_colors` no `disconnect` e quando o jogador sai (bloco `"quit", "remove"`).
8. `core/gameplay.py`:
   a. Em `update_playing`, logo depois do `send_state(...)`: `if game.run_frames % 60 == 1: game.network_client.send_color(getattr(game.player, 'color', 0))`.
   b. No laço dos remotos, logo depois de `update_from_network(...)`: `game.remote_players_map[p_id].set_color(net_client.get_remote_color(p_id))`.
9. `ui/screens/multiplayer_menu.py`: seletor de cor à DIREITA da tela, sem mexer no bloco central:
   - no `__init__`: `self.color = progress.carregar().get('cor_jogador', 0)`; painel centrado em `(SCREEN_WIDTH - 150, STACK_START_Y + 110)`; retângulos clicáveis `self.color_left` e `self.color_right` (40x40) à esquerda e à direita da prévia;
   - em `update`: título "COR DO BONECO" acima, prévia = `AssetManager().load_character_animations('player', PLAYER_SCALE * 1.5, self.color)[0][0]` centrada no painel, setas "<" e ">" desenhadas nos retângulos, nome da cor (`PLAYER_COLORS[self.color][0]`) abaixo;
   - em `handle_event`, no `MOUSEBUTTONDOWN`: clicar numa seta muda `self.color` em ±1 (circular em `len(PLAYER_COLORS)`) e chama `progress.salvar_cor(self.color)`. Isso deve acontecer ANTES do Host/Conectar criar o jogador, então a cor nova já vale na partida.
   - imports: `from core import progress`, `PLAYER_COLORS`, `PLAYER_SCALE`.

## O que NÃO fazer
- Não alterar os PNGs, `network/server.py`, `tools/`, nem o formato dos pacotes existentes.
- Não recolorir inimigos (só `char_type == 'player'` usa cor; outros sempre 0).
- Não rodar comandos, não instalar nada, não fazer commit.

## Verificação (eu rodo)
- `python tools/bot_fases.py 1` passa; `python tools/teste_multiplayer.py --porta 5601` sem regressão.
- Abrir o jogo, Multiplayer, trocar a cor e entrar.

## Critério de pronto
Seletor funciona e salva; o boneco local e o remoto aparecem na cor escolhida por cada um.
