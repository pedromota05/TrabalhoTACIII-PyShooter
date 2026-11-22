# Tarefa: checkpoint e castelo visíveis (e editáveis) no editor de fases

## Objetivo
Os elementos novos das fases precisam aparecer no editor: (1) o checkpoint vira um tile próprio (id 88) que se coloca/move/apaga no editor como qualquer outro; (2) a saída (tiles 20 e 41) aparece no editor como o castelinho da fase + linha de chegada, igual ao jogo.

## Já feito (não refazer)
- `config.py`: `TILE_TYPES = 87` (imagens `img/tile/0.png` a `86.png`); o id 87 é o DragonBoss (imagem montada à parte no editor). `CHECKPOINTS = {1: [48, 95], 2: [29, 89], 3: [19, 83], 4: []}` = colunas das bandeiras.
- `core/level_loader.py` (~linha 94): `for col in CHECKPOINTS.get(level_number, []): game.checkpoint_group.add(CheckpointFlag(col, _ground_top(game.world, col)))`. Logo abaixo, para fases em `CASTLE_THEMES`, cria `Castle(level_number, ex.rect)` e `FinishLine(ex.rect.centerx - 6 * TILE_SIZE, ex.rect.bottom)` para cada saída. A função lê o CSV da fase numa matriz antes de montar o mundo (procure onde `world_data`/a matriz é lida).
- `world/level_builder.py` ignora ids `>= len(assets.tile_images)` (87 em diante, exceto o 87 tratado à parte), então o id 88 no CSV não quebra o jogo.
- `entities/checkpoint.py`: `CheckpointFlag(col, ground_y)` — sprite com `image`/`rect`. `entities/castle.py`: `Castle(level, door_rect)` e `FinishLine(center_x, bottom)` são `Decoration` com `image`/`rect`; `CASTLE_THEMES` tem as fases 1-3.
- `ui/screens/level_editor.py`: `_init_tile_images` monta `self.img_list` (0..86 dos PNG + 87 dragão); a paleta lateral (`_init_palette_buttons`) cria um botão por imagem; `_draw_tiles` desenha `self.img_list[id]` em `px = c*TILE_SIZE - self.scroll`, `py = r*TILE_SIZE + (TILE_SIZE - img.get_height())`. Também já existe o Modo Mover (tecla M) feito hoje: não quebrar.

## Arquivos permitidos
- `config.py`
- `core/level_loader.py`
- `ui/screens/level_editor.py`
- Qualquer outro arquivo: NÃO tocar (os CSV das fases eu converto depois).

## Passos
1. `config.py`: logo abaixo de `TILE_TYPES`, `CHECKPOINT_TILE = 88  # bandeira de checkpoint (só editor/loader; o level_builder ignora)`.
2. `core/level_loader.py`:
   - Ler as colunas de checkpoint da matriz da fase: toda célula com valor `CHECKPOINT_TILE` vira uma bandeira na coluna dela (`CheckpointFlag(col, _ground_top(game.world, col))`), ordenadas por coluna e sem repetir coluna.
   - Se a matriz não tiver nenhuma célula `CHECKPOINT_TILE`, usar `CHECKPOINTS.get(level_number, [])` como hoje (compatibilidade).
   - Manter a condição `checkpoints_enabled(game)`.
3. `ui/screens/level_editor.py`:
   - Em `_init_tile_images`, depois do dragão (id 87), acrescentar a imagem do id 88: `CheckpointFlag(0, TILE_SIZE).image` (importe de `entities.checkpoint`); se a imagem for maior que um tile, mantenha a proporção e reduza para caber em `TILE_SIZE` de largura. Fallback em caso de erro: superfície `TILE_SIZE`x`TILE_SIZE` com um mastro e bandeira desenhados com `pygame.draw`. Assim ele aparece na paleta lateral automaticamente (confira que `_init_palette_buttons` percorre `self.img_list` inteira; se tiver número fixo, troque por `len(self.img_list)`).
   - Em `_draw_tiles`: o id 88 deve ser desenhado com a base da bandeira no fundo da célula (o mesmo cálculo de `py` já faz isso se a imagem for alta).
   - Castelo no editor: quando a fase atual (`self.level`) estiver em `CASTLE_THEMES` (importe de `entities.castle`), para cada célula com id 20 ou 41 desenhar, no lugar da imagem do tile, o castelo e a linha de chegada como no jogo: `door = pygame.Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE)` ajustado para o tamanho da imagem do tile de saída (mesmo `img_rect` que o `level_builder` usa: largura/altura da imagem, `bottom` no fundo da célula); `castle = Castle(self.level, door)` e `finish = FinishLine(door.centerx - 6 * TILE_SIZE, door.bottom)`; desenhar `finish.image` em `finish.rect.move(-self.scroll, 0)` e `castle.image` em `castle.rect.move(-self.scroll, 0)`. Guardar em cache por `(self.level, r, c)` para não recriar a cada quadro (limpar o cache ao trocar de fase e ao carregar/mover). Desenhe também, por cima, um contorno fino amarelo na célula do tile 20/41 para indicar onde fica a porta (é essa célula que se move/apaga).
   - Fases fora de `CASTLE_THEMES` continuam mostrando a imagem normal do tile de saída.
   - Botão Salvar: nada muda (o 88 é salvo no CSV como número).

## O que NÃO fazer
- Não mudar `Castle`, `FinishLine`, `CheckpointFlag`, `level_builder.py` nem os CSV.
- Não mudar o formato do CSV nem `TILE_TYPES`.
- Não rodar comandos nem fazer commit.

## Verificação (eu rodo)
- `python -m py_compile` nos 3 arquivos; bot das fases; abrir o editor nas fases 1-3.

## Critério de pronto
No editor, a paleta tem a bandeira de checkpoint (id 88); as saídas das fases 1-3 aparecem como castelo + linha de chegada; o jogo cria checkpoints a partir dos tiles 88 do CSV (ou da config se não houver).
