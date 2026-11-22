# 2026-11-22 — Seta para o inimigo restante (hordas) e escolher a fase do Desafio depois de zerado

## Objetivo
1. Na Fase 5 (hordas), se o jogador passar 8 s sem matar nenhum inimigo com a onda ainda ativa, mostrar uma seta perto do jogador apontando para o inimigo vivo mais próximo.
2. Depois que o Desafio for zerado (existe recorde), a tela de seleção de fase deixa escolher em qual fase o Desafio começa (treino; não grava recorde).

## Já feito (não refazer)
- `core/horde.py`: `start_horde(game)` e `update_horde(game)` (chamada todo quadro em `core/gameplay.py`, linha ~823, em todos os papéis: solo, Host e cliente). Inimigos vivos = `e.alive` em `game.enemy_group`, `game.boss_group` e `game.spider_group` (este com `getattr`).
- `core/renderer.py`, função `draw_game_entities` (HUD; linha ~134 desenha `ONDA x/5` quando `game.horde_active`). Coordenadas de inimigos e de `game.player.rect` são de TELA (as duas no mesmo sistema).
- `game.py`: `Game.start_challenge(start_index=0)` já existe; com `start_index > 0` liga `challenge_cheat` e o recorde não é gravado (`core/gameplay.py`, `update_challenge_transition`).
- `core/progress.py`: `progress.carregar()['recorde_desafio']` é `None` enquanto o Desafio nunca foi zerado.
- `ui/screens/level_select.py`: botão `MODO DESAFIO` (`self.challenge_open`) e o texto do recorde em `self.challenge_open.rect.bottom + 8`.

## Arquivos permitidos
- `core/horde.py`
- `core/renderer.py`
- `config.py` (só as constantes do passo 1)
- `ui/screens/level_select.py`
- Qualquer outro: não tocar.

## Passos

### Parte A — seta
1. `config.py`, junto das constantes `HORDE_*`: `HORDE_HINT_FRAMES = 480  # 8 s sem matar ninguém: mostra a seta para o inimigo mais próximo`.
2. `core/horde.py`, `start_horde`: `game.horde_idle = 0` e `game.horde_last_alive = 0`.
3. `core/horde.py`, no INÍCIO de `update_horde` (logo depois do `return` de `horde_active`, antes da separação cliente/Host): contar os vivos (`n`). Se `n == 0` ou `n < game.horde_last_alive`: `game.horde_idle = 0`; senão `game.horde_idle += 1`. Depois `game.horde_last_alive = n`. Usar `getattr(game, 'horde_idle', 0)`/`getattr(game, 'horde_last_alive', 0)` para não quebrar se faltar o atributo.
4. `core/renderer.py`: nova função `draw_enemy_arrow(game)`:
   - só age se `game.horde_active`, `getattr(game, 'horde_idle', 0) >= HORDE_HINT_FRAMES`, `game.player` existe e `game.player.alive`;
   - alvo = inimigo vivo mais próximo (distância euclidiana entre `rect.center`s) dos três grupos; sem alvo, não desenha;
   - desenhar um triângulo amarelo (`YELLOW`) com contorno preto (2 px), comprimento ~26 px e base ~18 px, com o centro a 60 px do centro do jogador na direção do alvo (use `math.atan2`); a ponta aponta para o alvo;
   - piscar suave: desenhar só quando `(pygame.time.get_ticks() // 300) % 2 == 0` OU fazer a distância oscilar entre 55 e 65 px com `math.sin` (escolha uma; prefira a oscilação, sem sumir);
   - logo abaixo do texto `ONDA x/5`, enquanto a seta aparece, escrever `Siga a seta!` em `YELLOW` com `_blit_shadowed` no `top` 136 (não pode colidir com `PRÓXIMA ONDA EM` em 114).
5. Chamar `draw_enemy_arrow(game)` no fim do bloco `if getattr(game, 'horde_active', False):` de `draw_game_entities`, onde já está o texto `ONDA`.
6. Importar `math` e `HORDE_HINT_FRAMES` onde precisar (sem duplicar imports).

### Parte B — escolher a fase do Desafio
7. `ui/screens/level_select.py`, `__init__`: criar `self.challenge_start_buttons` com 5 `button.Button`, um por fase (1 a 5), usando uma função `_small_button_surface(texto, fill, font)` (retângulo arredondado 52x40, mesma ideia de `_challenge_surface`; fill `CHALLENGE_RED`, fonte `self.badge_font`, texto `'1'`…`'5'`). Posicionar centralizados horizontalmente em linha, 12 px de espaço entre eles, com `rect.top = self.challenge_open.rect.bottom + 62`.
8. Em `update`, dentro de `if saved['campanha_zerada']:`, quando `saved['recorde_desafio'] is not None` E não for `mp_host_pick`: escrever `'Treino: começar na fase'` com `draw_text_with_outline(..., self.small_font, WHITE, SCREEN_WIDTH // 2, self.challenge_open.rect.bottom + 36)` e desenhar os 5 botões; clique no botão de índice `i` chama `game.start_challenge(start_index=i)`.
9. Atualizar a docstring do topo de `level_select.py` com uma frase sobre o treino.

## O que NÃO fazer
- Não mudar a lógica das ondas (spawn, pausa, `horde_done`).
- Não mostrar os botões de treino no multiplayer (`mp_host_pick`) nem antes de existir recorde.
- Não gravar recorde no treino (já garantido por `challenge_cheat`; não mexer nisso).
- Não rodar comandos, não fazer git.

## Verificação (o Claude roda)
- `python -m compileall -q core ui config.py`
- Script headless na fase 5: depois de 480 quadros sem matar, `horde_idle >= 480` e `draw_enemy_arrow` desenha sem erro; matando um inimigo, `horde_idle` volta a 0.
- Captura da tela de seleção com recorde salvo (botões 1-5 visíveis sem sobrepor o texto `Pressione ESC...`).
- `python tools/bot_fases.py 1` continua "passou".

## Critério de pronto
Verificações OK; diff só nos arquivos permitidos.
