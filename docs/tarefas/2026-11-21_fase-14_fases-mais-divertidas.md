# Tarefa: deixar as fases mais divertidas (sensação de jogo, pontos, combo e drops)

## Objetivo
Dar retorno visual e recompensa a cada ação: inimigo pisca branco ao levar tiro e mostra o dano flutuando; tela treme em explosões e na morte de chefe; inimigos mortos às vezes soltam munição/vida/granada; pontuação com combo (matar em sequência multiplica os pontos), mostrada no HUD e no fim da fase.

## Já feito (não refazer)
- Inimigos: `Enemy`, `Sniper` (`entities/enemies/standard.py`), `RobotEnemy`, `SkeletonEnemy` herdam `Character` (`entities/base.py`, que tem `draw(screen)` com `pygame.transform.flip(self.image, self.flip, False)`). Chefes `DragonBoss` e `Boss` (`entities/enemies/bosses.py`) têm `draw` próprio. Todos têm `rect`, `alive`, `health` e `target_id` (número igual nos dois PCs).
- Dano do tiro do jogador em `Bullet.update` (`entities/combat/projectiles.py`): inimigos (`enemy.health -= BULLET_DAMAGE_TO_ENEMY`) e chefes (`boss.health -= 25`). A granada explode criando `Explosion(x, y, scale)` em `Grenade.update` (procure onde a `Explosion` é criada e onde ela dá dano).
- `entities/items.py`: `ItemBox(item_type, x, y)` com tipos `'Ammo'`, `'Grenade'`, `'Health'`, `'Speed'`; `game.item_box_group` é atualizado/desenhado todo quadro e rola com a câmera. `PickupText(text, x, y)` é um texto flutuante que sobe e some (`update(screen_scroll)`), desenhado em `game.item_fx_group`.
- `core/gameplay.py`: `update_playing(game)` roda a cada quadro de jogo; `game.screen_scroll` é o deslocamento da câmera do quadro. `core/level_loader.py` `load_level` monta cada fase (e é chamado ao recomeçar/renascer no checkpoint).
- `core/renderer.py` `draw_game_entities(game)`: HUD no canto superior esquerdo (vida, "MUNIÇÃO:" em y=35, "GRANADA:" em y=60, "SPEED BOOST!" em y=85) e `_blit_shadowed(game, texto, cor, fonte, centro_x, topo)`.
- `game.py` `run()`: desenha a tela do estado, trata eventos, `draw_crosshair(self)` e `pygame.display.update()`.
- No multiplayer a morte dos inimigos chega pelo Host; os dois PCs veem `alive=False` no mesmo inimigo.

## Arquivos permitidos
- `entities/effects.py` (novo)
- `entities/base.py`
- `entities/enemies/bosses.py`
- `entities/combat/projectiles.py`
- `core/gameplay.py`
- `core/renderer.py`
- `core/level_loader.py`
- `game.py`
- `config.py`
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. `config.py` (bloco novo "Diversão"):
   ```python
   KILL_POINTS = {'Enemy': 100, 'Sniper': 200, 'RobotEnemy': 150, 'SkeletonEnemy': 150, 'Boss': 1500, 'DragonBoss': 2000}
   COMBO_WINDOW_FRAMES = 150   # 2,5 s para a próxima morte manter o combo
   COMBO_MAX = 5               # multiplicador máximo
   DROP_CHANCES = (('Ammo', 0.25), ('Health', 0.10), ('Grenade', 0.08))  # chance por morte, em ordem
   HIT_FLASH_FRAMES = 6
   ```
2. `entities/effects.py` (novo):
   - `class FloatingText(pygame.sprite.Sprite)`: `__init__(self, text, x, y, color, size=20)` renderiza com contorno preto (fonte `FONT_NAME` de config, negrito); sobe 1 px por quadro, some em 40 quadros (alpha caindo na segunda metade); `update(self, screen_scroll)` soma `screen_scroll` no x.
   - Estado do tremor: `_shake = [0, 0]` (quadros, intensidade); `shake(frames, power)` guarda o maior; `shake_offset()` devolve `(dx, dy)` aleatório em ±intensidade e decrementa os quadros (devolve `(0, 0)` quando acabou); `reset_shake()`.
   - Texto pendente criado de qualquer lugar: `_texts = []`; `damage_text(x, y, amount)` acrescenta `FloatingText(str(amount), x, y, (255, 230, 90), 18)` a `_texts`; `pop_texts()` devolve e limpa.
3. Piscar branco ao levar dano:
   - `entities/base.py` `Character`: atributo `hit_flash = 0` no `__init__`; em `update` decrementa se > 0; em `draw`, se `hit_flash > 0`, depois de desenhar o sprite normal desenhe por cima uma silhueta branca: `img = pygame.transform.flip(self.image, self.flip, False)`; `white = pygame.mask.from_surface(img).to_surface(setcolor=(255, 255, 255, 200), unsetcolor=(0, 0, 0, 0))`; `screen.blit(white, self.rect)`. NÃO aplicar no jogador (`Player` herda `Character`: use `if self.char_type != 'player'` ou o atributo que guarda o tipo — confira o nome no `__init__` da base).
   - `entities/enemies/bosses.py`: mesmo efeito no `draw` de `DragonBoss` e `Boss` (atributo `hit_flash`, decrementado no próprio `draw` ou `update`), usando a imagem que eles já desenham.
4. `entities/combat/projectiles.py` `Bullet.update`: onde a bala do jogador dá dano num inimigo, fazer `enemy.hit_flash = HIT_FLASH_FRAMES` e `effects.damage_text(enemy.rect.centerx, enemy.rect.top, BULLET_DAMAGE_TO_ENEMY)`; no chefe, `boss.hit_flash = HIT_FLASH_FRAMES` e `effects.damage_text(boss.rect.centerx, boss.rect.top, 25)`. Balas `visual_only` (do parceiro) também marcam `hit_flash` no que acertarem (só visual, sem texto de dano). Na explosão da granada: `effects.shake(12, 6)` e, para cada inimigo/chefe atingido, `hit_flash` + texto do dano que a granada já aplica.
5. `core/gameplay.py`:
   - Nova função `update_fun(game)` chamada uma vez por quadro em `update_playing` (perto de `update_checkpoints(game)`), e também quando o jogador está morto (os efeitos continuam):
     - Mortes: para cada sprite de `game.enemy_group` e `game.boss_group` com `not alive` e sem `getattr(s, '_counted', False)`: marcar `s._counted = True`; pontos base = `KILL_POINTS.get(type(s).__name__, 100)`; combo: se `game.combo_timer > 0`, `game.combo = min(COMBO_MAX, game.combo + 1)`, senão `game.combo = 1`; `game.combo_timer = COMBO_WINDOW_FRAMES`; `ganho = base * game.combo`; `game.score += ganho`; `game.level_score += ganho`; texto flutuante `f"+{ganho}"` (branco; se `game.combo >= 2`, amarelo e `f"+{ganho}  x{game.combo}"`) em cima do inimigo, adicionado em `game.fun_fx_group`. Chefe: `effects.shake(30, 10)`.
     - Drop: só para inimigos comuns (não chefes). Sorteio determinístico, igual nos dois PCs: `rng = random.Random(s.target_id * 7919 + game.level)`; `r = rng.random()`; percorre `DROP_CHANCES` acumulando; se cair num tipo, criar `ItemBox(tipo, x, y)` com o `rect.midbottom` no `s.rect.midbottom` (ajuste para não ficar dentro do chão: alinhe `bottom` com o `rect.bottom` do inimigo) e adicionar em `game.item_box_group`. Marque `box.dropped = True` (para não confundir com as caixas do mapa).
     - `game.combo_timer` diminui 1 por quadro; ao zerar, `game.combo = 0`.
     - Transferir `effects.pop_texts()` para `game.fun_fx_group` e chamar `game.fun_fx_group.update(game.screen_scroll)`.
   - Caixas soltas por inimigo no multiplayer: o código atual de coleta de `ItemBox` pode mandar uma mensagem de rede com um id; confira em `entities/items.py` (só leia) como o id é calculado. Se a coleta usa um id baseado na posição/ordem do mapa, NÃO mande mensagem de rede para caixas com `dropped = True` (cada jogador pega a sua). Se isso exigir mudar `entities/items.py`, pare e escreva na resposta o que precisaria mudar.
6. `core/level_loader.py` `load_level`: criar/esvaziar `game.fun_fx_group` (um `pygame.sprite.Group`), zerar `game.combo`, `game.combo_timer`, `game.level_score` e chamar `effects.reset_shake()`. NÃO zerar `game.score` aqui.
7. `game.py`: `self.score = 0`, `self.combo = 0`, `self.combo_timer = 0`, `self.level_score = 0`, `self.fun_fx_group = pygame.sprite.Group()` no `__init__`. Zerar `self.score` quando começa uma partida nova: no início de `start_challenge`, de `start_multiplayer_host`, de `start_multiplayer_client` e onde a seleção de fases começa a campanha (procure `game.lives = SHARED_LIVES` em `ui/screens/level_select.py` — você NÃO pode editar esse arquivo; em vez disso zere `self.score` em `game.py` quando `self.state` muda de `LEVEL_SELECT` para `PLAYING`, guardando o estado anterior do laço em `run()`). Tremor: em `run()`, logo antes de `draw_crosshair(self)`, se `self.state == GameState.PLAYING`, `dx, dy = effects.shake_offset()` e, se não for (0, 0), `self.screen.scroll(dx, dy)`.
8. `core/renderer.py` `draw_game_entities`:
   - Desenhar `game.fun_fx_group` depois das entidades (antes do HUD).
   - HUD: `f"PONTOS: {game.score}"` em (10, 85) com `game.font_bold` branco; mover "SPEED BOOST!" para y=110. Enquanto `game.combo >= 2`: `f"COMBO x{game.combo}"` em amarelo logo à direita dos pontos, com uma barrinha embaixo (60x4 px) proporcional a `game.combo_timer / COMBO_WINDOW_FRAMES`.
   - Na tela de banner/transição não é preciso nada.

## O que NÃO fazer
- Não mudar dano, vida, munição inicial, IA dos inimigos, mapas nem rede.
- Não mexer em `ui/`, `entities/items.py`, `entities/player.py`, `tools/`.
- Não rodar comandos nem fazer commit.

## Verificação (eu rodo)
- `python -m py_compile` nos arquivos; `python tools/bot_fases.py todas`; `python tools/bot_fases.py --desafio --god`; captura de tela com combo e drops.

## Critério de pronto
Inimigo pisca e mostra o dano; mortes dão pontos com combo no HUD; alguns inimigos soltam caixas; granada e morte de chefe tremem a tela; o bot continua passando.
