# Tarefa: castelinho na saída de cada fase (visual muda por fase)

## Objetivo
No fim das fases 1, 2 e 3 a saída vira um castelinho desenhado pelo próprio jogo (sem PNG novo), com porta escura onde o jogador entra e uma bandeirinha balançando. Cada fase tem um estilo: fase 1 de pedra, fase 2 forte de madeira, fase 3 castelo de gelo. A fase 4 (chefes, sem saída) não muda.

## Já feito (não refazer)
- A saída é `Exit` em `entities/environment.py` (sprite com `image` e `rect`), criada em `world/level_builder.py` para os tiles 20 e 41 e guardada em `game.exit_group`. O jogador termina a fase quando toca no `rect` da saída (`Player.move`). O bot (`tools/bot_fases.py`) também usa `e.rect` das saídas: NÃO mudar o `rect` da `Exit`.
- `Decoration` (`entities/environment.py`) é um sprite que só rola com a câmera (`update(screen_scroll)`); `game.decoration_group` é desenhado e rolado em todo quadro e também é deslocado no renascimento.
- `load_level(game, level_number, keep_checkpoint=False)` em `core/level_loader.py` monta a fase; no fim dela já existe o bloco das placas (`signs = sorted(...)`).
- `TILE_SIZE` = 40 (config).

## Arquivos permitidos
- `entities/castle.py` (novo)
- `core/level_loader.py`
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. Criar `entities/castle.py`:
   ```python
   """entities/castle.py — Castelinho desenhado na saída da fase (estilo por fase)."""
   import pygame
   from config import TILE_SIZE
   from entities.environment import Decoration

   # (parede, sombra/linhas, porta, bandeira, detalhe do topo ou None)
   CASTLE_THEMES = {
       1: ((150, 150, 160), (100, 100, 112), (25, 20, 30), (60, 200, 90), None),            # pedra
       2: ((125, 88, 52), (80, 55, 30), (20, 14, 8), (240, 200, 40), None),                 # madeira
       3: ((190, 225, 245), (120, 170, 210), (20, 40, 70), (40, 80, 200), (255, 255, 255)), # gelo + neve
   }
   ```
2. No mesmo arquivo, função `def _draw_castle(theme, flag_frame: int) -> pygame.Surface` que devolve uma `Surface` com `SRCALPHA` de largura `3 * TILE_SIZE` e altura `4 * TILE_SIZE` (W x H), desenhando:
   - corpo: retângulo da parede de `(0.15W, 0.40H)` até a base (`H`), largura `0.70W`;
   - duas torres laterais: retângulos de largura `0.22W`, de `y = 0.25H` até a base, encostadas nas bordas esquerda (x=0) e direita (x=W-0.22W);
   - torre central: largura `0.30W`, centrada, de `y = 0.15H` até a base;
   - ameias: em cima de cada torre, pequenos quadrados de lado `0.06W` alternando cheio/vazio;
   - linhas de tijolo/tábua: linhas horizontais na cor de sombra a cada `TILE_SIZE // 3` px dentro do corpo e das torres (para a fase 2, também linhas verticais espaçadas `TILE_SIZE // 2`, parecendo tábuas);
   - janelinhas: um retângulo de porta-cor `0.06W x 0.10H` no meio de cada torre lateral;
   - porta: arco escuro centrado embaixo, largura = `TILE_SIZE`, altura = `int(1.4 * TILE_SIZE)`, base em `H` (retângulo + `pygame.draw.ellipse` no topo para o arco);
   - neve (só se o 5º item do tema não for `None`): faixa branca de 4 px no topo de cada torre;
   - mastro: linha escura de 2 px saindo do topo da torre central, 0.5 TILE de altura; bandeira: triângulo na cor da bandeira preso no mastro; quando `flag_frame == 1`, a ponta do triângulo fica 3 px mais baixa (balanço).
   - Contorno: `pygame.draw.rect(..., 2)` na cor de sombra em volta de cada torre e do corpo.
3. No mesmo arquivo:
   ```python
   class Castle(Decoration):
       """Castelinho decorativo centrado na porta (rect da Exit)."""

       def __init__(self, level: int, door_rect: pygame.Rect):
           theme = CASTLE_THEMES.get(level, CASTLE_THEMES[1])
           self.frames = [_draw_castle(theme, 0), _draw_castle(theme, 1)]
           pygame.sprite.Sprite.__init__(self)
           self.image = self.frames[0]
           self.rect = self.image.get_rect(midbottom=door_rect.midbottom)
           self.tick = 0

       def update(self, screen_scroll: int):
           self.rect.x += screen_scroll
           self.tick += 1
           self.image = self.frames[(self.tick // 20) % 2]
   ```
4. `core/level_loader.py`, no fim de `load_level`, ANTES do bloco das placas:
   ```python
   # Castelinho na saída (fases com tema). A Exit continua sendo o gatilho;
   # a imagem dela fica invisível e o castelo é só desenho (decoração).
   if level_number in CASTLE_THEMES:
       for ex in game.exit_group:
           game.decoration_group.add(Castle(level_number, ex.rect))
           ex.image = pygame.Surface(ex.rect.size, pygame.SRCALPHA)
   ```
   com `from entities.castle import Castle, CASTLE_THEMES` e `import pygame` (se faltar).

## O que NÃO fazer
- Não alterar `Exit`, `Player`, `world/level_builder.py`, `tools/`, os CSVs das fases nem criar PNGs.
- Não reproduzir castelos de outros jogos: é um desenho simples próprio (torres, ameias, porta e bandeira).
- Não rodar comandos, não instalar nada, não fazer commit.

## Verificação (eu rodo)
- `python tools/bot_fases.py todas` passa (a saída é a mesma).
- Captura da tela no fim de cada fase 1, 2 e 3.

## Critério de pronto
Cada fase 1-3 termina num castelinho com estilo próprio; entrar pela porta termina a fase como antes.
