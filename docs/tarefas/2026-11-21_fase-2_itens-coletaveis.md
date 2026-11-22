# Tarefa: coletáveis com animação e sincronizados no multiplayer

## Objetivo
As caixas coletáveis (`ItemBox`) hoje ficam paradas e, no multiplayer, quando um jogador pega uma caixa ela continua na tela do outro. Fazer: (1) as caixas flutuarem devagar para cima e para baixo; (2) um texto curto subir e sumir ao pegar ("+VIDA" etc.); (3) quem pega avisa a rede e a caixa some na tela do parceiro.

## Já feito (não refazer)
- `ItemBox` em `entities/items.py`: `update(self, screen_scroll, player)` aplica o efeito e chama `self.kill()`.
- Caixas são criadas em `world/level_builder.py` com `ItemBox(tipo, x * TILE_SIZE, y * TILE_SIZE)` (x = coluna, y = linha). Não alterar esse arquivo.
- Protocolo em texto: `network/protocol.py` (funções `encode_*` e `parse_packet`). Em `parse_packet`, o bloco final `try: x = float(parts[1]) ...` é o pacote de posição e pega tudo que não foi reconhecido antes: comandos novos devem ser tratados ANTES desse bloco.
- Cliente de rede: `network/client.py`, recebe em `_receive_loop` (bloco `with self.lock:` com `elif packet["type"] == ...`) e envia com `self._send(texto)`. Siga o padrão de `send_level_request` / `pop_level_requests`.
- O servidor (`network/server.py`) já repassa qualquer pacote aos outros jogadores. Não alterar.

## Arquivos permitidos
- `entities/items.py`
- `network/protocol.py`
- `network/client.py`
- `core/gameplay.py`
- `core/renderer.py`
- `core/level_loader.py`
- `game.py`
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. `entities/items.py`, classe `ItemBox`:
   a. No `__init__`, depois de posicionar o `rect`, adicionar:
      ```python
      # Id estável da caixa (coluna*1000 + linha): igual no Host e no cliente.
      self.item_id = (x // TILE_SIZE) * 1000 + (y // TILE_SIZE)
      self.base_y = self.rect.y
      self.bob_tick = self.item_id % 60   # fase diferente para cada caixa
      ```
   b. Trocar a assinatura para `def update(self, screen_scroll: int, player, network_client=None, level: int = 0, fx_group=None):`.
   c. No início do `update`, depois de `self.rect.x += screen_scroll`, fazer a flutuação:
      ```python
      self.bob_tick += 1
      self.rect.y = self.base_y + round(3 * math.sin(self.bob_tick * 0.08))
      ```
      (adicionar `import math` no topo).
   d. Dentro do `if pygame.sprite.collide_rect(self, player):`, antes de `self.kill()`:
      ```python
      if fx_group is not None:
          fx_group.add(PickupText(PICKUP_LABELS[self.item_type], self.rect.centerx, self.rect.top))
      if network_client is not None:
          network_client.send_item_pickup(level, self.item_id)
      ```
   e. Criar no mesmo arquivo:
      ```python
      PICKUP_LABELS = {'Health': '+VIDA', 'Ammo': '+MUNIÇÃO', 'Grenade': '+GRANADA', 'Speed': 'VELOCIDADE!'}


      class PickupText(pygame.sprite.Sprite):
          """Texto que sobe e some em 40 quadros quando uma caixa é pega."""
          _font = None

          def __init__(self, text: str, x: int, y: int):
              super().__init__()
              if PickupText._font is None:
                  PickupText._font = pygame.font.SysFont(FONT_NAME, 20, bold=True)
              self.base = PickupText._font.render(text, True, (255, 255, 120))
              self.image = self.base.copy()
              self.rect = self.image.get_rect(midbottom=(x, y))
              self.timer = 40

          def update(self, screen_scroll: int):
              self.rect.x += screen_scroll
              self.rect.y -= 1
              self.timer -= 1
              self.image = self.base.copy()
              self.image.set_alpha(int(255 * self.timer / 40))
              if self.timer <= 0:
                  self.kill()
      ```
      Importar `FONT_NAME` de `config` (somar ao import existente).
2. `network/protocol.py`: adicionar
   ```python
   def encode_item_pickup(player_id: str, level: int, item_id: int) -> str:
       """Qualquer jogador -> outros: pegou a caixa `item_id` da fase `level`."""
       return f"{player_id},item,{level},{item_id}"
   ```
   e em `parse_packet`, junto dos outros comandos (antes do bloco final de posição):
   ```python
   if command == "item" and len(parts) >= 4:
       try:
           return {"type": "item", "player_id": player_id,
                   "level": int(parts[2]), "item_id": int(parts[3])}
       except ValueError:
           return None
   ```
   Exportar `encode_item_pickup` em `network/__init__.py` NÃO é necessário; importe direto de `network.protocol` no client.py, no import já existente.
3. `network/client.py`:
   a. No `__init__`: `self.pending_item_pickups: List[tuple[int, int]] = []`.
   b. No `_receive_loop`: `elif packet["type"] == "item": self.pending_item_pickups.append((packet["level"], packet["item_id"]))`.
   c. Métodos:
      ```python
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
      ```
   d. No `disconnect`, no bloco que limpa estado (onde está `self.host_level = None`), adicionar `self.pending_item_pickups.clear()`.
4. `game.py`: junto de `self.item_box_group = pygame.sprite.Group()`, criar `self.item_fx_group = pygame.sprite.Group()`.
5. `core/level_loader.py`, `reset_groups(game)`: esvaziar também `game.item_fx_group` (use `getattr(game, 'item_fx_group', None)` e só chame `.empty()` se existir).
6. `core/gameplay.py`, em `update_game_entities`, trocar a linha `game.item_box_group.update(game.screen_scroll, game.player)` por:
   ```python
   net_items = game.network_client if getattr(game, 'is_multiplayer', False) else None
   if net_items is not None:
       # Caixas que o parceiro pegou somem aqui também (sem dar o efeito).
       for lvl, item_id in net_items.pop_item_pickups():
           if lvl != game.level:
               continue
           for box in list(game.item_box_group):
               if box.item_id == item_id:
                   box.kill()
   fx_group = getattr(game, 'item_fx_group', None)
   game.item_box_group.update(game.screen_scroll, game.player, net_items, game.level, fx_group)
   if fx_group is not None:
       fx_group.update(game.screen_scroll)
   ```
7. `core/renderer.py`, em `draw_game_entities`: logo depois da linha que desenha `game.item_box_group`, desenhar `game.item_fx_group` do mesmo jeito (com `getattr(game, 'item_fx_group', None)` e só se existir).

## O que NÃO fazer
- Não mudar o formato dos pacotes já existentes nem `network/server.py`.
- Não alterar `world/level_builder.py`, `tools/`, nem o efeito das caixas (vida, munição etc.).
- Não rodar comandos, não instalar nada, não fazer commit.

## Verificação (eu rodo)
- `python tools/bot_fases.py 1 2` passa.
- `python tools/teste_multiplayer.py --porta 5601` dá 7/7.

## Critério de pronto
Caixas flutuam, mostram o texto ao pegar e, no multiplayer, somem nas duas telas.
