# Fase 16 — Golpe com a arma, caixas quebráveis, aranhas e vida extra

Repositório: `C:\projetos_disco_C\faculdade\TrabalhoTACIII-PyShooter`, branch `melhorias-coop`. Python 3 + pygame-ce. Comentários e textos de tela em português.

## Objetivo
Também: aranha como tile 89 na paleta do editor (passo 12).
Botão direito do mouse = golpe corpo a corpo com a arma (gira a arma + arco branco), que fere inimigos na frente e quebra caixas de madeira (tile 12). Caixa quebrada solta um item, às vezes uma vida extra (coração) ou uma aranha (inimigo novo desenhado no código).

## Já feito (não refazer)
- `entities/aim_pose.py`: `draw_aiming(screen, rect, direction, aim_angle, ...)` desenha a arma girada; o jogador tem `player.aim_angle` (radianos).
- `core/gameplay.py` `update_fun(game)`: pontos por `config.KILL_POINTS[type(s).__name__]` para sprites em `game.enemy_group`/`game.boss_group` com `alive == False`; usa `effects.FloatingText` e `effects.shake`.
- `entities/items.py` `ItemBox(tipo, x, y)` com tipos 'Health', 'Ammo', 'Grenade', 'Speed'; imagens em `AssetManager().item_box_images[tipo]` (`asset_manager.py` ~linha 186). Caixas "dropped=True" não são sincronizadas pela rede.
- Vidas: `game.lives` (`config.SHARED_LIVES = 3`); no multiplayer o Host é a autoridade: `register_death` em `core/gameplay.py` e `net.send_lives(lives, reset_counter)`; o cliente recebe por `net.get_host_lives()`.
- Mensagens de rede: `network/protocol.py` (`encode_*` e o `decode` com `"type"`), `network/client.py` (`send_*`/`pop_*`); veja `encode_item_pickup` / `send_item_pickup` / `pop_item_pickups` como modelo.

## Arquivos permitidos
- `entities/player.py`, `entities/remote_player.py` (só se precisar mostrar o golpe do parceiro; opcional)
- `entities/aim_pose.py` (só se precisar de parâmetro extra)
- `entities/spider.py` (NOVO)
- `entities/items.py`, `asset_manager.py` (ícone do coração)
- `world/level_builder.py`
- `core/gameplay.py`, `core/level_loader.py`, `core/renderer.py`, `core/input_handler.py`
- `network/protocol.py`, `network/client.py`, `network/server.py` (só se o servidor filtrar tipos de mensagem)
- `config.py`, `game.py` (só criar grupos/atributos novos)
- `ui/screens/instructions.py`
- `ui/screens/level_editor.py` (só o tile da aranha, passo 12)
- `entities/effects.py` (só para criar `Debris`, se precisar)
- Qualquer outro arquivo: NÃO tocar. Em especial, NÃO editar `levels/*.csv` nem `tools/`.

## Passos
1. `config.py`: `MELEE_FRAMES = 14`, `MELEE_COOLDOWN = 24`, `MELEE_RANGE = 60` (px à frente), `MELEE_DAMAGE = 35`, `MAX_LIVES = 5`, `SPIDER_HEALTH = 30`, `SPIDER_DAMAGE = 10`, e `KILL_POINTS['Spider'] = 50` (acrescentar na dict existente). `CRATE_DROPS = [('Ammo', 0.3), ('Grenade', 0.15), ('Health', 0.2), ('Life', 0.1), ('Spider', 0.25)]` (resto = nada).
2. `core/input_handler.py`: `MOUSEBUTTONDOWN` com `event.button == 3` e estado PLAYING → `game.melee_input = True`. Iniciar `self.melee_input = False` em `game.py`.
3. `entities/player.py`: `start_melee()` (só se `alive`, sem cooldown) define `self.melee_timer = MELEE_FRAMES` e `self.melee_cooldown = MELEE_COOLDOWN`; `update()` decrementa os dois. No desenho, enquanto `melee_timer > 0`, some ao `aim_angle` um balanço: `swing = math.radians(-70 + 140 * (1 - melee_timer / MELEE_FRAMES)) * direção` (de cima para baixo) e passe o ângulo resultante a `draw_aiming`. Desenhe também um arco branco semitransparente (`pygame.draw.arc` numa Surface SRCALPHA, 3 px) à frente do jogador durante o golpe. Método `melee_rect()` → `pygame.Rect` de `MELEE_RANGE` x altura do jogador colado no lado para onde ele olha.
4. `core/gameplay.py` função nova `update_melee(game)`, chamada em `_update_playing` logo depois de `update_fun(game)`:
   - se `game.melee_input`: zera a flag e chama `player.start_melee()`; se o golpe começou, no MESMO quadro aplica o acerto (uma vez por golpe): inimigos/chefes vivos de `enemy_group`, `boss_group` e `spider_group` cujo `rect` colide com `melee_rect()` levam `MELEE_DAMAGE` (no multiplayer, para `enemy_group`/`boss_group` use o mesmo caminho do tiro: veja como o projétil chama `network_client.send_enemy_hit(target_id, dano)` no cliente; o Host aplica direto); `effects.shake(6, 4)`.
   - caixas: cada caixa de `game.world.crates` cujo rect colide com `melee_rect()` é quebrada por `break_crate(game, crate, sync=True)`.
5. `world/level_builder.py`: tile 12 continua sólido, mas guarde também `self.crates.append({'col': x, 'row': y, 'tile': tile_data})` (iniciar `self.crates = []` em `__init__`). EXCEÇÃO: caixas na última linha (`y == ROWS - 1`) ou com outra caixa/bloco sólido em cima NÃO são quebráveis (não entram em `crates`): a fase 3 tem uma pirâmide de caixas e não pode abrir buraco no chão.
6. `core/gameplay.py` `break_crate(game, crate, sync)`: remove `crate['tile']` de `game.world.obstacle_list` e de `game.world.crates`; partículas: 8 lascas marrons (`effects` — crie uma classe `Debris` simples em `entities/effects.py` SE não existir nada parecido; esse arquivo também fica permitido) no grupo `game.fun_fx_group`; conteúdo sorteado com `random.Random(crate['col'] * 1000 + crate['row'] + game.level * 7)` sobre `CRATE_DROPS`:
   - 'Ammo'/'Grenade'/'Health' → `ItemBox` com `dropped = True` no lugar da caixa;
   - 'Life' → `ItemBox('Life', ...)` com `dropped = True`;
   - 'Spider' → `Spider(x, y)` em `game.spider_group`.
   Se `sync` e multiplayer: `game.network_client.send_crate(game.level, col, row)`.
   Recebimento: em `_update_playing`, `for lvl, col, row in net.pop_crates()`: se `lvl == game.level`, quebra a caixa daquela col/linha com `sync=False` (o sorteio é o mesmo nos dois PCs).
   Lembrete: a posição na tela de uma caixa = `crate['tile'][1]` (já rolada pela câmera); use esse rect.
7. Vida extra: em `entities/items.py`, tipo 'Life' com ícone de coração vermelho desenhado com `pygame.draw` (dois círculos + triângulo, contorno preto) criado em `asset_manager.py` junto com as outras imagens. Ao pegar: NÃO soma no player; marque `player.pending_life_up += 1` (iniciar 0 em `Player.__init__`). Em `core/gameplay.py`, consuma: single ou Host → `game.lives = min(MAX_LIVES, game.lives + 1)` e (Host) `net.send_lives(game.lives, game.lives_reset_counter)`; cliente → `net.send_lifeup()`; o Host, ao receber (`net.pop_lifeups()`), soma e anuncia. Texto flutuante "+1 VIDA" verde.
8. Rede (`network/protocol.py` e `network/client.py`): `encode_crate(pid, level, col, row)` → `"crate,{pid},{level},{col},{row}"` decodificado como `{"type": "crate", ...}`; `send_crate`/`pop_crates` (lista protegida pelo mesmo lock das outras). `encode_lifeup(pid)` → `"lifeup,{pid}"`, `send_lifeup`/`pop_lifeups`. Confira em `network/server.py` se ele repassa qualquer tipo; se houver lista de tipos, inclua os dois.
9. `entities/spider.py`: classe `Spider(pygame.sprite.Sprite)` desenhada no código (corpo oval preto 22x14, olhos vermelhos, 8 pernas com `pygame.draw.line` que oscilam com `math.sin`). Atributos: `alive`, `health = SPIDER_HEALTH`, `target_id = None`. `update(screen_scroll, player, obstacle_list)`: anda em direção ao jogador (velocidade 2), gravidade e colisão com `obstacle_list` (copie o padrão de colisão simples de um inimigo de `entities/enemies/standard.py`), pula (vel_y = -9) quando o jogador está a menos de 120 px na horizontal e ela está no chão, com recarga de 60 quadros; contato com o jogador vivo e sem `invincible` → `player.health -= SPIDER_DAMAGE` e recarga de 45 quadros. `health <= 0` → `alive = False` e some depois de 20 quadros. Leva dano de balas: em `update_melee` e onde as balas acertam inimigos (procure em `entities/combat/projectiles.py`), inclua `game.spider_group` — se for complicado passar o grupo, faça a checagem bala×aranha em `core/gameplay.py` depois do update das balas (bala acerta → aranha perde 25, bala `kill()`).
   Pontos: em `update_fun`, inclua `list(game.spider_group)` na lista (sem drop para aranha: condicione o drop a `s not in game.spider_group`).
   Aranhas são locais em cada PC (não sincronizadas): escreva isso num comentário no topo de `spider.py`.
10. `game.py`: `self.spider_group = pygame.sprite.Group()`; `core/level_loader.py` `reset_groups`: esvaziar `spider_group`; `move_camera` e `shift_world`: incluir `spider_group` nos grupos deslocados. `core/renderer.py`: desenhar `spider_group` junto dos inimigos.
11. `ui/screens/instructions.py`: acrescentar "Botão direito: golpe com a arma (quebra caixas de madeira)" e "Coração: +1 vida (até 5)".

12. Aranha como tile do editor (pedido do Guilherme): `config.py` → `SPIDER_TILE = 89` (o 88 já é o checkpoint; o 87 é o Dragão; NÃO mudar `TILE_TYPES`).
   - `entities/spider.py`: função `spider_icon(size: int) -> pygame.Surface` (mesmo desenho da aranha, parada, cabendo em size x size). `asset_manager.py`: guardar `self.spider_icon = spider_icon(TILE_SIZE)` junto das outras imagens (a aranha passa a fazer parte dos assets).
   - `ui/screens/level_editor.py` `_init_tile_images`: DEPOIS do bloco do "Tile ID 88" (a ordem da lista = id), acrescentar `# Tile ID 89: Aranha` com `self.img_list.append(spider_icon(TILE_SIZE))`. Conferir que salvar/carregar o CSV aceita 89 (procure onde o editor limita ids, ex.: `len(self.img_list)` ou `CHECKPOINT_TILE`) e que a paleta mostra o item novo.
   - `world/level_builder.py` `process_data`: antes do `if 0 <= tile < len(assets.tile_images)`, `if tile == SPIDER_TILE: self.spider_spawns.append((x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE)); continue` (iniciar `self.spider_spawns = []` em `__init__`).
   - `core/level_loader.py` `load_level`: depois do `process_data`, criar `Spider` para cada ponto de `game.world.spider_spawns` em `game.spider_group` (o construtor da aranha deve aceitar o ponto midbottom no mundo, com bg_scroll = 0).

## O que NÃO fazer
- Não apagar nem reescrever blocos existentes que não estejam nos passos (já aconteceu de um bloco de fase sumir). Mudanças mínimas e localizadas.
- Não mexer em `levels/*.csv`, `tools/`, git, nem instalar nada. Não rodar o jogo.
- Não usar imagens novas em arquivo: tudo desenhado com `pygame.draw`.
- Não usar `random` global para o sorteio da caixa (tem de ser igual nos dois PCs).

## Verificação (o Claude roda)
- `python -c "import game, core.gameplay, entities.spider"`
- `python tools/bot_fases.py todas`, `--desafio --god`, `todas --humano 3`
- `python tools/teste_multiplayer.py --porta 5611`
- Script de teste: golpe na frente de uma caixa da fase 1 (col 40, linha 8) quebra a caixa e solta item/aranha; o mesmo sorteio no Host e no cliente.

## Critério de pronto
Passos 1-12 feitos, imports sem erro, nenhum arquivo fora da lista alterado; ao terminar, liste os arquivos alterados e qualquer passo que não conseguiu fazer.
