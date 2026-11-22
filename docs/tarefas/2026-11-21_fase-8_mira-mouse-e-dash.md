# Tarefa: mira com o mouse, tiro no botão esquerdo e dash no espaço

## Objetivo
O jogador mira com o mouse (mira desenhada na tela no lugar do cursor) e atira com o botão esquerdo na direção da mira, em qualquer ângulo. A tecla ESPAÇO deixa de atirar e passa a dar um dash horizontal rápido, com animação (rastro de "fantasmas" do boneco e poeira) e tempo de recarga.

## Já feito (não refazer)
- `core/input_handler.py`: ESPAÇO hoje liga/desliga `game.shoot` (KEYDOWN/KEYUP). `game.py` cria as flags de input (`self.shoot = False` etc., perto da linha 105).
- `core/gameplay.py` (~linha 510): `if game.shoot: game.player.shoot(game.bullet_group, network_client=net_client)`; logo depois vem a granada, `update_action` e `game.screen_scroll, level_complete = game.player.move(...)`. Mais abaixo (~linha 546) `game.network_client.send_state(x, y, action, direction, game.shoot, health)`.
- `entities/base.py`: `Character.shoot(self, bullet_group, network_client=None, bg_scroll=0)` cria `Bullet(spawn_x, spawn_y, self.direction, network_client=...)`. Inimigos também usam esse método: o comportamento padrão (sem alvo) TEM de continuar igual.
- `entities/combat/projectiles.py`: `Bullet.__init__(self, x, y, direction, network_client=None, visual_only=False)`; `update` move só no eixo x: `self.rect.x += (self.direction * self.speed) + screen_scroll`.
- `entities/player.py`: `Player.move(...)` calcula `dx`/`dy`, colide com tiles (`_check_tile_collisions`), aplica scroll da câmera e devolve `(screen_scroll, level_complete)`. `Player.draw` pisca quando `self.invincible > 0`.
- `entities/remote_player.py` (~linha 93): quando `data["shooting"]`, cria `Bullet(bullet_x, bullet_y, self.direction, visual_only=True)`.
- `network/protocol.py`: `encode_player_state(player_id, x, y, action, direction, shooting, health)` gera 7 campos CSV; o decodificador do estado (~linha 225) lê `parts[5]` (shooting) e `parts[6]` (health) com valores padrão se faltarem. `network/client.py` `send_state(self, x, y, action, direction, shooting, health)` chama `encode_player_state`.
- `ui/screens/instructions.py` (~linha 85): linha "ESPAÇO : Atirar" com a imagem `keys_ui['SPACE']`.
- `game.py` `run()` (~linha 304): desenha a tela do estado atual, chama `self._handle_events()` e depois `pygame.display.update()` (~linha 340).
- O bot `tools/bot_fases.py` joga sem janela: ele liga `g.shoot = True` e escolhe `g.player.direction`/`g.player.flip` sozinho. Ele NÃO pode passar a mirar no mouse.

## Arquivos permitidos
- `config.py`
- `game.py`
- `core/input_handler.py`
- `core/gameplay.py`
- `core/renderer.py`
- `entities/base.py`
- `entities/player.py`
- `entities/combat/projectiles.py`
- `entities/remote_player.py`
- `network/protocol.py`
- `network/client.py`
- `ui/screens/instructions.py`
- `tools/bot_fases.py` (só a linha do passo 10)
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. `config.py`: adicionar perto de `SHOOT_COOLDOWN`:
   ```python
   # Dash (tecla ESPAÇO)
   DASH_SPEED = 16          # pixels por quadro durante o dash
   DASH_FRAMES = 10         # duração do dash em quadros
   DASH_COOLDOWN = 50       # quadros até poder dar outro dash
   DASH_TRAIL = 6           # quantos "fantasmas" o rastro guarda
   ```
2. `entities/combat/projectiles.py` — `Bullet` com ângulo opcional:
   - Novo parâmetro no fim: `angle: float | None = None` (radianos, 0 = direita, positivo = para baixo, como no pygame).
   - Guardar `self.angle = angle`. Se `angle is not None`: `self.vel_x = math.cos(angle) * self.speed`, `self.vel_y = math.sin(angle) * self.speed`, guardar posição em float `self.fx, self.fy = float(x), float(y)` e girar a imagem: `self.image = pygame.transform.rotate(AssetManager().get_image('bullet'), -math.degrees(angle))`, recriando `self.rect` com `center=(int(x), int(y))`.
   - Em `update`, trocar só a linha do movimento normal por: se `self.angle is None` mantém `self.rect.x += (self.direction * self.speed) + screen_scroll`; senão `self.fx += self.vel_x + screen_scroll; self.fy += self.vel_y; self.rect.center = (int(self.fx), int(self.fy))`. No bloco `has_hit` (bala congelada), se tiver ângulo também somar `screen_scroll` em `self.fx`.
   - "Fora da tela": além de esquerda/direita, matar se `self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT` (importar `SCREEN_HEIGHT` de config se ainda não estiver).
   - Importar `math` no topo se faltar. Nenhuma outra classe deste arquivo muda.
3. `entities/base.py` — `Character.shoot` ganha alvo opcional:
   - Assinatura: `def shoot(self, bullet_group, network_client=None, bg_scroll: int = 0, target=None):`.
   - Se `target is None`: código atual sem nenhuma mudança.
   - Se `target` (tupla de tela `(x, y)`): `cx, cy = self.rect.centerx, self.rect.centery - 5`; `angle = math.atan2(target[1] - cy, target[0] - cx)`; `spawn_x = cx + math.cos(angle) * self.rect.width * 0.9`; `spawn_y = cy + math.sin(angle) * self.rect.width * 0.9`; criar `Bullet(spawn_x, spawn_y, self.direction, network_client=network_client, angle=angle)`. Cooldown, munição, som e o `send_enemy_shoot` (só para quem tem `target_id`) iguais ao caso sem alvo.
4. `entities/player.py` — mira e dash:
   - Importar `DASH_SPEED, DASH_FRAMES, DASH_COOLDOWN, DASH_TRAIL` de config.
   - No `__init__`: `self.aim_angle = 0.0`, `self.dash_timer = 0`, `self.dash_cooldown = 0`, `self.dash_dir = 1`, `self.dash_trail = []` (lista de `[imagem, flip, x, y, vida]`), `self.dash_dust = []` (lista de `[x, y, raio, vida]`).
   - Método `face_point(self, x, y)`: `self.direction = 1 if x >= self.rect.centerx else -1`; `self.flip = self.direction == -1`; `self.aim_angle = math.atan2(y - (self.rect.centery - 5), x - self.rect.centerx)`.
   - Método `start_dash(self, moving_left, moving_right)`: só se `self.alive and self.dash_cooldown == 0 and self.dash_timer == 0`. `self.dash_dir` = -1 se `moving_left` e não `moving_right`; 1 se `moving_right` e não `moving_left`; senão `self.direction`. `self.dash_timer = DASH_FRAMES`, `self.dash_cooldown = DASH_COOLDOWN`, `self.invincible = max(self.invincible, DASH_FRAMES)`. Criar 6 partículas de poeira em `self.rect.midbottom` (x com deslocamento aleatório de -10 a 10, raio 4 a 8, vida 18). Tocar `AssetManager().get_sound('jump')` (som existente). Devolve `True` se começou.
   - Em `update`: decrementar `self.dash_cooldown` se > 0; envelhecer o rastro (vida -1, remover vida <= 0) e a poeira (vida -1, raio +0.4, y -0.5, remover vida <= 0).
   - Em `move`: logo após o bloco de movimento horizontal e ANTES do air control, se `self.dash_timer > 0`: `dx = self.dash_dir * DASH_SPEED`, `self.vel_y = 0` e pular a gravidade neste quadro (não chamar `_apply_gravity`, `dy` fica 0); `self.dash_timer -= 1`; a cada quadro do dash acrescentar em `self.dash_trail` o item `[self.image.copy(), self.flip, self.rect.x, self.rect.y, DASH_TRAIL * 2]` e cortar a lista para os últimos `DASH_TRAIL`. O air control (`* 0.7`) NÃO se aplica durante o dash. Pulo durante o dash: ignorar (`self.jump` fica como está até o dash acabar).
   - Ainda em `move`, depois que `screen_scroll` foi calculado: somar `screen_scroll` no x de cada item de `self.dash_trail` e de `self.dash_dust` (assim o rastro acompanha a câmera).
   - Em `draw`: antes do boneco, desenhar a poeira (`pygame.draw.circle` cor `(200, 190, 170)` numa superfície com alpha proporcional à vida) e o rastro: para cada item, `img = pygame.transform.flip(imagem, flip, False).copy()`, tingir de azul-claro com `img.fill((90, 160, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)`, `img.set_alpha(int(160 * vida / (DASH_TRAIL * 2)))` e `screen.blit(img, (x, y))`. O efeito de piscar da invencibilidade NÃO deve esconder o boneco enquanto `self.dash_timer > 0` (no dash ele aparece sempre).
5. `game.py`:
   - Nas flags de input: `self.dash_input = False` e `self.use_mouse_aim = True` (o bot desliga).
   - Em `run()`, logo antes de `pygame.display.update()`: chamar `draw_crosshair(self)` (importado de `core.renderer`).
6. `core/renderer.py` — nova função `draw_crosshair(game)`:
   - `aim = game.state == GameState.PLAYING and getattr(game, 'use_mouse_aim', False) and game.player is not None and game.player.alive`.
   - `pygame.mouse.set_visible(not aim)` só quando o valor mudar (guardar em `game._cursor_hidden`).
   - Se `aim`: em `(mx, my) = pygame.mouse.get_pos()` desenhar círculo de raio 10 e espessura 2, quatro tracinhos de 6 px saindo do círculo (cima, baixo, esquerda, direita) e um ponto central de raio 2. Cor branca com contorno preto (desenhar primeiro em preto com espessura +2). Se `game.player.shoot_cooldown > 0` o círculo fica amarelo `(255, 220, 60)`.
   - Abaixo da mira, barrinha de recarga do dash (24x4 px, centralizada, 16 px abaixo): fundo cinza escuro, preenchimento azul-claro `(90, 160, 255)` proporcional a `1 - dash_cooldown / DASH_COOLDOWN`; só desenhar enquanto `dash_cooldown > 0`.
   - Importar `GameState` e `DASH_COOLDOWN` se ainda não estiverem importados.
7. `core/input_handler.py`:
   - ESPAÇO no KEYDOWN: `game.dash_input = True` (remover `game.shoot = True`). ESPAÇO no KEYUP: remover o `game.shoot = False`.
   - Novo: `if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game.state == GameState.PLAYING: game.shoot = True`; `if event.type == pygame.MOUSEBUTTONUP and event.button == 1: game.shoot = False` (o UP vale em qualquer estado, para não ficar atirando preso ao voltar do pause).
8. `core/gameplay.py`:
   - Antes de `if game.shoot:` (dentro de `if game.player.alive:`): `target = pygame.mouse.get_pos() if getattr(game, 'use_mouse_aim', False) else None`; se `target`: `game.player.face_point(*target)`.
   - Chamada do tiro: `game.player.shoot(game.bullet_group, network_client=net_client, target=target)`.
   - Logo depois do tiro/granada: `if getattr(game, 'dash_input', False): game.player.start_dash(game.moving_left, game.moving_right); game.dash_input = False`.
   - IMPORTANTE: `Player.move` muda `flip`/`direction` quando anda. Com `use_mouse_aim`, depois do `game.player.move(...)` chamar de novo `game.player.face_point(*target)` (se `target`) para o boneco continuar virado para a mira.
   - No `send_state(...)` do multiplayer, passar também `aim=game.player.aim_angle`.
   - Conferir que `pygame` está importado no arquivo.
9. Rede (tiro do parceiro sai no ângulo certo):
   - `network/protocol.py`: `encode_player_state(..., health: int = 100, aim: float = 0.0)` acrescenta 8º campo `round(aim, 3)`. No decodificador do estado: `aim = float(parts[7]) if len(parts) > 7 else None` e incluir `"aim": aim` no dicionário. Nada mais no protocolo muda.
   - `network/client.py`: `send_state(..., health: int = 100, aim: float = 0.0)` repassa `aim`. Onde o cliente guarda o estado de cada jogador remoto (~linha 165-180, dicionário com `"shooting"`), guardar também `"aim": packet.get("aim")`. As outras chamadas de `send_state` sem `aim` continuam funcionando pelo valor padrão.
   - `entities/remote_player.py`: ao criar a bala visual, `aim = data.get("aim")`; se `aim is not None`, `Bullet(cx, cy, self.direction, visual_only=True, angle=aim)` saindo de `cx = self.rect.centerx + math.cos(aim) * self.rect.width * 0.75`, `cy = self.rect.centery - 5 + math.sin(aim) * self.rect.width * 0.75`; senão o código atual.
10. `tools/bot_fases.py`: na função `novo_jogo()` (~linha 336, hoje `return Game()`), trocar por `g = Game()`, `g.use_mouse_aim = False`, `return g`. Mais nada no bot.
11. `ui/screens/instructions.py`: a linha do ESPAÇO passa a dizer `": Dash"`. Acrescentar abaixo uma linha de texto `"MOUSE : Mirar  |  BOTÃO ESQUERDO : Atirar"` com a mesma fonte, centralizada; se não couber, empurre as linhas seguintes (Q/G e ESC) 50 px para baixo cada uma.

## O que NÃO fazer
- Não mudar o tiro dos inimigos nem `SniperBullet`, `RobotBullet`, `Arrow`, `DragonFire`, `Grenade`.
- Não mudar dano, munição, cooldown do tiro, nem `Bullet.rect` quando não há ângulo.
- Não remover campos do protocolo de rede nem mudar a ordem dos 7 primeiros.
- Não criar imagens novas: o rastro usa a imagem atual do boneco.
- Não usar `pygame.mouse.get_pos()` dentro de `entities/` (o alvo chega por parâmetro).
- Não rodar comandos nem fazer commit.

## Verificação (eu rodo)
- `python -m py_compile` em todos os arquivos alterados.
- `python tools/bot_fases.py todas` e `python tools/bot_fases.py --desafio --god`.
- `python tools/teste_multiplayer.py --porta 5601`.

## Critério de pronto
Todos os passos feitos só nos arquivos permitidos; o bot continua passando as fases; no jogo, a mira aparece no lugar do cursor durante a fase, o botão esquerdo atira na direção dela e o ESPAÇO dá o dash com rastro azul e poeira.
