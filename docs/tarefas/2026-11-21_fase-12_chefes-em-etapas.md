# Tarefa: chefes da fase 4 em etapas (um de cada vez)

## Objetivo
Na fase de chefes (fase 4 tem o Demônio, tile 86 na coluna 25, e o Dragão, tile 87 na coluna 52) o jogador enfrenta um chefe por vez: primeiro o mais à esquerda; quando ele morre, depois de ~1,5 s aparece o próximo com um aviso "ETAPA 2" e um efeito de entrada. A fase só termina quando o último chefe morre.

## Já feito (não refazer)
- `core/level_loader.py` `load_level(...)`: monta o mundo (bosses vão para `game.boss_group`), depois numera `target_id` de inimigos e chefes (~linha 86-92). `reset_groups(game)` (~linha 15-35) esvazia os grupos. `shift_world(game, offset)` (~linha 127) desloca blocos e os grupos de uma tupla `groups = (...)`; confira também `move_camera` no mesmo arquivo e faça o grupo novo ser deslocado em ambos.
- `core/gameplay.py`: `BOSS_DEATH_DELAY_FRAMES = int(1.5 * FPS)`; `is_level_complete(game, touched_exit)` (~linha 205) termina a fase sem saída quando todos de `game.boss_group` morrem e passa o atraso. Os grupos são rolados a cada quadro em `update_game_entities`/onde `game.decoration_group.update(game.screen_scroll)` é chamado (procure). No multiplayer o Host manda o estado dos chefes por `target_id` e o Cliente aplica (~linha 355-385) iterando `game.boss_group`.
- `core/renderer.py`: `draw_level_banner(game)` mostra "FASE N" enquanto `game.level_banner_frames > 0` (usa `_blit_shadowed` e `game.title_font`). `Explosion(x, y, scale)` existe em `entities/combat/projectiles.py` e `game.explosion_group` é atualizado/desenhado todo quadro.

## Arquivos permitidos
- `core/level_loader.py`
- `core/gameplay.py`
- `core/renderer.py`
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. `level_loader.py`:
   - Criar/esvaziar `game.boss_reserve_group` (um `pygame.sprite.Group`) em `reset_groups` (crie o atributo se não existir).
   - Em `load_level`, DEPOIS de numerar os `target_id` (os números não podem mudar): se `game.boss_group` tiver 2 ou mais chefes, ordenar por `rect.x`; manter só o primeiro em `game.boss_group` e mover os outros (na ordem) para `game.boss_reserve_group`. Guardar a ordem em `game.boss_queue = [lista dos reservados em ordem]`, `game.boss_stage = 1`, `game.boss_stage_total = número total de chefes`, `game.boss_stage_frames = 0`, `game.boss_stage_banner = 0`.
   - Incluir `game.boss_reserve_group` na tupla de grupos de `shift_world` e onde `move_camera` desloca os grupos.
2. `gameplay.py`:
   - Rolar o grupo de reserva junto com o mundo todo quadro: no mesmo lugar onde os outros grupos recebem `screen_scroll`, fazer `for b in game.boss_reserve_group: b.rect.x += game.screen_scroll` (os chefes reservados NÃO são atualizados nem desenhados).
   - Nova função `update_boss_stages(game)`, chamada uma vez por quadro em `update_playing` (perto de `update_checkpoints(game)`): se `getattr(game, 'boss_queue', None)` tem itens e `len(game.boss_group)` e nenhum chefe de `game.boss_group` está vivo: somar `game.boss_stage_frames`; ao chegar em `BOSS_DEATH_DELAY_FRAMES`, tirar o primeiro da fila, remover do `boss_reserve_group`, adicionar ao `game.boss_group`, `game.boss_stage += 1`, `game.boss_stage_banner = 150`, zerar `boss_stage_frames`, criar 3 `Explosion` (escala 2) espalhadas no `rect` do chefe novo em `game.explosion_group` e tocar `AssetManager().get_sound('grenade')`. Se algum chefe está vivo, `boss_stage_frames = 0`. Decrementar `game.boss_stage_banner` se > 0.
   - Remover os chefes mortos antigos do `boss_group` quando o próximo entra? NÃO: deixe-os (o corpo congela no último quadro de morte, e o sync do multiplayer usa o grupo). Mas `is_level_complete` precisa considerar a fila: se `getattr(game, 'boss_queue', None)` não estiver vazia, devolve `False` (antes de contar o atraso).
   - Cliente do multiplayer: a mesma `update_boss_stages` roda nele; como a morte do chefe chega pelo Host, as etapas avançam igual nos dois. Não mude o código de sincronização.
3. `renderer.py`: em `draw_game_entities`, depois de `draw_level_banner(game)`: se `getattr(game, 'boss_stage_banner', 0) > 0`, mostrar `f"ETAPA {game.boss_stage}/{game.boss_stage_total}"` com `game.title_font` em vermelho `(235, 60, 50)` centralizado em y=150 e, abaixo (y=210, `game.font_bold`, branco), "Um novo chefe apareceu!". Também, enquanto houver `boss_stage_total` >= 2, mostrar pequeno no topo (abaixo do "FASE N/M", y=40, `game.font_bold`) `f"CHEFE {game.boss_stage}/{game.boss_stage_total}"`.

## O que NÃO fazer
- Não mudar as classes dos chefes, os CSV, a numeração de `target_id`, nem a sincronização de rede.
- Não rodar comandos nem fazer commit.

## Verificação (eu rodo)
- `python -m py_compile` nos 3 arquivos; `python tools/bot_fases.py 4` e `python tools/bot_fases.py todas`; `python tools/teste_multiplayer.py --porta 5601`.

## Critério de pronto
Na fase 4 só o Demônio aparece no início; quando ele morre, ~1,5 s depois o Dragão surge com explosões e o aviso "ETAPA 2/2"; a vitória só vem com o Dragão morto.
