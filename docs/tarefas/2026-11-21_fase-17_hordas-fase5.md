# Fase 17 — Fase 5 vira arena de hordas (Modo Desafio)

Repositório: `C:\projetos_disco_C\faculdade\TrabalhoTACIII-PyShooter`, branch `melhorias-coop`. Python 3 + pygame-ce. Textos e comentários em português. Você NÃO tem terminal: só leia, busque e edite arquivos.

## Objetivo
Na fase 5 (só usada no Desafio), os inimigos chegam em ondas numeradas ("ONDA N/M") pelas bordas da tela; a última onda traz o Demônio (`Boss`) e o Dragão (`DragonBoss`) juntos. Vencer a última onda termina a fase (e o Desafio vai para a vitória).

## Já feito (não refazer)
- `levels/level5_data.csv` já foi preparado pelo Claude: é a arena da fase 4 SEM chefes e sem inimigos (não edite o CSV).
- Inimigos: `Enemy`, `Sniper` (`entities/enemies/standard.py`), `RobotEnemy` (`robot.py`), `SkeletonEnemy` (`skeleton.py`), `Boss` e `DragonBoss` (`bosses.py`); veja em `world/level_builder.py` como cada um é criado a partir de (x*TILE_SIZE, y*TILE_SIZE) e em qual grupo entra (`enemy_group` / `boss_group`); copie exatamente esse jeito de criar (inclusive qualquer atributo extra definido ali). Aranha: `entities/spider.py` `Spider(x_meio, y_pe)` em `game.spider_group` (local em cada PC).
- Sincronização: o Host manda o estado dos inimigos por `target_id` (`core/gameplay.py`, bloco "Se for Host no Multiplayer, envia lote"); o cliente aplica pelo `target_id` (bloco "Interpola e sincroniza estado dos inimigos"). Dano do cliente vai por `send_enemy_hit(target_id, dano)`. Por isso os inimigos das ondas precisam existir nos dois PCs com o MESMO `target_id`.
- `core/gameplay.py`: `is_level_complete(game, touched_exit)` decide o fim da fase; `update_boss_stages` controla chefes em etapas (não usar na fase 5); `update_fun` dá pontos.
- Mensagens de rede: modelo em `network/protocol.py` (`encode_lives`: formato `"{player_id},lives,..."`, sempre `player_id` primeiro e o comando depois; NÃO mude `network/server.py`) e `network/client.py` (`send_lives`/`get_host_lives`).

## Arquivos permitidos
- `config.py`, `core/gameplay.py`, `core/level_loader.py`, `core/renderer.py`, `network/protocol.py`, `network/client.py`, `core/horde.py` (NOVO)
- Qualquer outro: NÃO tocar (em especial `levels/*.csv`, `network/server.py`, `tools/`, `docs/`, `audio/`).

## Passos
1. `config.py`: `HORDE_LEVEL = 5`, `HORDE_PAUSE_FRAMES = 180` (3 s entre ondas), `HORDE_BANNER_FRAMES = 120`, e `HORDE_WAVES`, uma lista de ondas; cada onda é uma lista de `(tipo, lado)` com tipo em `'Enemy' | 'Sniper' | 'RobotEnemy' | 'SkeletonEnemy' | 'Spider' | 'Boss' | 'DragonBoss'` e lado `-1` (borda esquerda) ou `1` (direita). Sugestão (5 ondas): 1) 3 Enemy; 2) 2 Enemy + 2 SkeletonEnemy + 2 Spider; 3) 2 RobotEnemy + 2 Enemy + 1 Sniper + 2 Spider; 4) 3 RobotEnemy + 3 SkeletonEnemy + 2 Sniper + 3 Spider; 5) Boss + DragonBoss + 2 Enemy. Alterne os lados.
2. `core/horde.py` (novo), com funções que recebem `game`:
   - `start_horde(game)`: chamado por `load_level` quando `level_number == HORDE_LEVEL`: `game.horde_active = True`, `game.horde_wave = 0` (nenhuma ainda), `game.horde_total = len(HORDE_WAVES)`, `game.horde_pause = 90` (1,5 s antes da 1ª), `game.horde_banner = 0`, `game.horde_done = False`. Para as outras fases `game.horde_active = False`.
   - `spawn_wave(game, n, base_x)`: cria os inimigos da onda `n` (1..M). `base_x` = `bg_scroll` do Host no momento (posição do mundo da borda esquerda da tela). Cada inimigo i: x do mundo = `base_x + 40 + 25*k` (lado -1) ou `base_x + SCREEN_WIDTH - 40 - 25*k` (lado 1), onde k conta os inimigos do mesmo lado; o pé fica no topo do chão daquela coluna (procure em `game.world.obstacle_list` o rect de topo mais alto com `(rect.left + game.bg_scroll) // TILE_SIZE == coluna`; sem chão, use `SCREEN_HEIGHT - 2*TILE_SIZE`). Converta para a tela: `x_tela = x_mundo - game.bg_scroll`. Chefes: `Boss` no x do mundo `25*TILE_SIZE` e `DragonBoss` em `52*TILE_SIZE` com o pé em `11*TILE_SIZE` (posições originais da fase 4), também convertidos para a tela. `target_id = 1000 + n*50 + i` (i = índice na lista da onda). Aranhas vão para `game.spider_group` (sem target_id). Explosão (`Explosion(x, y, 2)` de `entities`) no ponto de cada chefe, como em `update_boss_stages`.
   - `update_horde(game)`: chamado a cada quadro em `_update_playing` (perto de `update_boss_stages`). Só age se `game.horde_active`. Decrementa `horde_banner`. Single ou Host: se não há inimigo/chefe vivo da onda atual (`enemy_group`, `boss_group` e `spider_group` sem ninguém `alive`), conta `horde_pause`; ao zerar: se `horde_wave == horde_total` → `game.horde_done = True`; senão `horde_wave += 1`, `spawn_wave(game, horde_wave, game.bg_scroll)`, `horde_banner = HORDE_BANNER_FRAMES`, `horde_pause = HORDE_PAUSE_FRAMES`, solta 1 `ItemBox` 'Ammo' e (ondas pares) 1 'Health' perto do jogador (marque `dropped = True`), e no Host: `net.send_wave(game.level, horde_wave, int(game.bg_scroll))`. Cliente: não decide nada; a cada quadro consome `net.pop_waves()` e, para cada `(lvl, n, base_x)` com `lvl == game.level` e `n > game.horde_wave`, faz `horde_wave = n`, `spawn_wave(game, n, base_x)` e mostra o banner; quando receber o fim da fase pelo anúncio normal de fase do Host, segue como hoje.
   - Mortos antigos: ao começar uma onda nova, remova de `enemy_group`/`boss_group` os sprites já mortos há tempo (`not alive`) para não acumular (NÃO remova os vivos).
3. `core/gameplay.py` `is_level_complete`: no começo, `if getattr(game, 'horde_active', False): return getattr(game, 'horde_done', False)` (só o Host/single decide; o cliente já segue o anúncio de fase do Host — confira que o cliente não chama a transição sozinho; se chamar, faça o cliente nunca completar a fase de hordas por conta própria).
4. `core/level_loader.py` `load_level`: no fim, `from core.horde import start_horde` e chamar `start_horde(game)` se `level_number == HORDE_LEVEL`, senão `game.horde_active = False`.
5. Rede: `network/protocol.py` `encode_wave(player_id, level, n, base_x)` → `f"{player_id},wave,{level},{n},{base_x}"` e o decode `{"type": "wave", "player_id", "level", "n", "base_x"}` (siga o padrão dos outros comandos com `command = parts[1]`). `network/client.py`: `send_wave` (envia 3 vezes; o cliente ignora repetidas porque compara `n > game.horde_wave`), `pending_waves` + `pop_waves()` com o lock, limpar a lista no mesmo lugar onde as outras listas são limpas.
6. `core/renderer.py`: no HUD, se `game.horde_active`: texto "ONDA N/M" (canto superior, perto do cronômetro do Desafio, sem cobrir vidas/pausa) e, enquanto `horde_banner > 0`, um aviso grande no centro "ONDA N" (na última: "ONDA FINAL!"), no mesmo estilo do aviso de etapa do chefe (`boss_stage_banner`). Durante a pausa entre ondas (sem inimigos vivos e `horde_wave < horde_total`), mostrar "PRÓXIMA ONDA EM X s" pequeno.

## O que NÃO fazer
- Não editar CSVs, `network/server.py`, `tools/`, `docs/`, `audio/`. Não rodar comandos.
- Não usar `random` global para escolher posições/tipos (precisa ser igual nos dois PCs).
- Não apagar nem reescrever blocos que não estão nos passos; mudanças mínimas.
- Não mexer nas fases 1-4 (a lógica só vale com `level_number == HORDE_LEVEL`).

## Verificação (o Claude roda)
- `python -c "import game, core.horde"`; `python tools/bot_fases.py --desafio --god`; `python tools/bot_fases.py 5 --humano 3`; `python tools/teste_multiplayer.py --fase 5 --porta 5621`.

## Critério de pronto
Passos 1-6 feitos; liste os arquivos alterados e o que não conseguiu fazer.
