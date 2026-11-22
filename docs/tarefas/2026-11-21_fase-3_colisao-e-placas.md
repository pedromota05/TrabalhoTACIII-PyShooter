# Tarefa: colisão entre jogadores e placas interativas

## Objetivo
(1) No multiplayer, o jogador local não atravessa mais o parceiro: bate nele de lado e pode ficar em pé na cabeça dele. (2) As placas de madeira do cenário (tiles 23 e 40) passam a ser interativas: perto delas aparece um "E" e, apertando E, abre um balão com uma dica.

## Já feito (não refazer)
- `Player.move(...)` em `entities/player.py` calcula `dx`/`dy`, chama `self._check_tile_collisions(dx, dy, obstacle_list, ramp_list)` e depois aplica limites de tela e posição. É chamado em `update_playing` (`core/gameplay.py`) e pelo bot em `tools/` (por isso o parâmetro novo tem que ser OPCIONAL, no fim).
- Jogador remoto: `RemotePlayer` (`entities/remote_player.py`), com `rect` já em coordenadas de tela e `alive`. Grupo: `game.remote_players_group`.
- Placas hoje são `Decoration` criadas em `world/level_builder.py`: `elif tile == 23:` e dentro de `elif tile in (36, 40, 42, 49):`.
- Fase atual: `game.level`. `load_level(game, level_number, keep_checkpoint=False)` em `core/level_loader.py` monta a fase.
- Teclas: `core/input_handler.py`, bloco `if event.key == ...` dentro de `if event.type == pygame.KEYDOWN:`.
- Texto com sombra no renderer: `_blit_shadowed(game, text, color, font, center_x, top)` em `core/renderer.py`; fontes `game.font`, `game.font_bold`.

## Arquivos permitidos
- `entities/player.py`
- `entities/sign.py` (novo)
- `world/level_builder.py`
- `core/level_loader.py`
- `core/gameplay.py`
- `core/input_handler.py`
- `core/renderer.py`
- `config.py`
- `game.py`
- Qualquer outro arquivo: NÃO tocar.

## Passos
### Parte A — colisão entre jogadores
1. `entities/player.py`, `move(...)`: acrescentar o parâmetro opcional no FIM da assinatura: `remote_players=None`.
2. Logo DEPOIS da linha `dx, dy = self._check_tile_collisions(dx, dy, obstacle_list, ramp_list)`, inserir:
   ```python
   # Colisão com o parceiro do multiplayer (hitbox estreita: ignora a arma).
   if remote_players:
       for other in remote_players:
           if not other.alive:
               continue
           body = other.rect.inflate(-other.rect.width // 2, -6)
           if self.rect.colliderect(body):
               continue  # já sobrepostos (ex.: renasceu ao lado): deixa sair
           if dx and self.rect.move(dx, 0).colliderect(body):
               dx = 0
           # Cai em cima da cabeça do parceiro
           if dy > 0 and self.rect.bottom <= body.top and self.rect.move(dx, dy).colliderect(body):
               dy = body.top - self.rect.bottom
               self.vel_y = 0
               self.in_air = False
   ```
3. `core/gameplay.py`, `update_playing`: na chamada `game.player.move(...)`, acrescentar o último argumento
   `game.remote_players_group if getattr(game, 'is_multiplayer', False) else None`.

### Parte B — placas interativas
4. `config.py`, logo abaixo de `LEVEL_BANNER_FRAMES = ...`:
   ```python
   SIGN_RANGE_X = 50   # distância horizontal (px) para interagir com a placa
   SIGN_TEXTS = {
       1: [
           'Água funda mata na hora! Pule com W ou seta para cima. Caixas de munição recarregam seus tiros.',
           'Soldados à frente. Atire com ESPAÇO e jogue granadas com Q ou G.',
           'Logo adiante tem uma bandeira: é um checkpoint. Se morrer, você volta nela.',
           'Robôs aguentam mais tiros. Mantenha distância e use granadas.',
           'A saída está perto. Siga em frente!',
       ],
       2: ['Pântano! A água mata. Pule de plataforma em plataforma.'],
       3: [
           'Fase de gelo: a água gelada também é mortal.',
           'Snipers atiram de longe. Avance pulando e use granadas.',
           'Últimos inimigos antes da saída. Pegue a munição!',
       ],
   }
   SIGN_DEFAULT_TEXT = 'Continue em frente e cuidado com os inimigos!'
   ```
5. Criar `entities/sign.py`:
   ```python
   """entities/sign.py — Placa de madeira interativa (tecla E mostra uma dica)."""
   from entities.environment import Decoration


   class Sign(Decoration):
       """Decoração com texto; o texto é definido em load_level pela ordem no mapa."""

       def __init__(self, img, x: int, y: int):
           super().__init__(img, x, y)
           self.text = ''
   ```
6. `world/level_builder.py`:
   - importar `from entities.sign import Sign`;
   - em `elif tile == 23:` trocar `Decoration(...)` por `Sign(...)` (mesmos argumentos, continua indo para `decoration_group`);
   - tirar o `40` da tupla `(36, 40, 42, 49)` e criar logo antes dela `elif tile == 40:` igual ao do 23 (Sign no `decoration_group`).
7. `core/level_loader.py`, no fim de `load_level` (depois que o mundo e os grupos estão montados):
   ```python
   # Placas: textos pela ordem da esquerda para a direita
   signs = sorted((d for d in game.decoration_group if isinstance(d, Sign)), key=lambda s: s.rect.x)
   texts = SIGN_TEXTS.get(level_number, [])
   for i, sign in enumerate(signs):
       sign.text = texts[i] if i < len(texts) else SIGN_DEFAULT_TEXT
   game.signs = signs
   game.near_sign = None
   game.open_sign = None
   game.sign_toggle = False
   ```
   com os imports `from entities.sign import Sign` e `SIGN_TEXTS, SIGN_DEFAULT_TEXT` de `config`.
8. `game.py`, no `__init__` junto dos outros atributos de estado: `self.signs = []`, `self.near_sign = None`, `self.open_sign = None`, `self.sign_toggle = False`.
9. `core/input_handler.py`: dentro do bloco KEYDOWN, adicionar
   ```python
   if event.key == pygame.K_e and game.state == GameState.PLAYING:
       game.sign_toggle = True
   ```
10. `core/gameplay.py`: criar a função e chamá-la em `update_playing` logo depois de `update_checkpoints(game)` (dentro do `if game.player.alive:`):
    ```python
    def update_signs(game) -> None:
        """Marca a placa perto do jogador e abre/fecha o balão com a tecla E."""
        player = game.player
        near = None
        for sign in getattr(game, 'signs', []):
            if (abs(sign.rect.centerx - player.rect.centerx) <= SIGN_RANGE_X
                    and abs(sign.rect.bottom - player.rect.bottom) <= 80):
                near = sign
                break
        game.near_sign = near
        if near is None:
            game.open_sign = None
        if getattr(game, 'sign_toggle', False):
            game.sign_toggle = False
            if near is not None:
                game.open_sign = None if game.open_sign is near else near
    ```
    (importar `SIGN_RANGE_X` de `config`.)
11. `core/renderer.py`: criar e chamar no FIM de `draw_game_entities`:
    ```python
    def draw_sign_ui(game) -> None:
        """'E' sobre a placa próxima; balão com a dica quando aberta."""
        sign = getattr(game, 'near_sign', None)
        if sign is None:
            return
        if getattr(game, 'open_sign', None) is not sign:
            key = game.font_bold.render('E', True, WHITE)
            box = key.get_rect(midbottom=(sign.rect.centerx, sign.rect.top - 6)).inflate(12, 6)
            pygame.draw.rect(game.screen, (20, 20, 30), box, border_radius=5)
            pygame.draw.rect(game.screen, WHITE, box, 2, border_radius=5)
            game.screen.blit(key, key.get_rect(center=box.center))
            return
        # Balão no topo da tela com quebra de linha
        width = 620
        words, lines, line = sign.text.split(), [], ''
        for w in words:
            test = (line + ' ' + w).strip()
            if game.font.size(test)[0] > width - 30:
                lines.append(line)
                line = w
            else:
                line = test
        if line:
            lines.append(line)
        lh = game.font.get_height() + 4
        height = 20 + lh * len(lines) + lh
        rect = pygame.Rect(0, 0, width, height)
        rect.midtop = (SCREEN_WIDTH // 2, 70)
        pygame.draw.rect(game.screen, (245, 232, 200), rect, border_radius=10)
        pygame.draw.rect(game.screen, (90, 60, 30), rect, 3, border_radius=10)
        y = rect.top + 10
        for text in lines:
            surf = game.font.render(text, True, (40, 25, 10))
            game.screen.blit(surf, surf.get_rect(midtop=(rect.centerx, y)))
            y += lh
        hint = game.font.render('E para fechar', True, (110, 80, 50))
        game.screen.blit(hint, hint.get_rect(midtop=(rect.centerx, y)))
    ```
    Garantir `import pygame` e `SCREEN_WIDTH`, `WHITE` importados (alguns já estão no import de `config`).

## O que NÃO fazer
- Não mudar a física (gravidade, pulo, `_check_tile_collisions`).
- Não mudar `tools/`, `network/`, `entities/remote_player.py`.
- Não rodar comandos, não instalar nada, não fazer commit.

## Verificação (eu rodo)
- `python tools/bot_fases.py todas` passa.
- `python tools/teste_multiplayer.py --porta 5601` sem regressão.

## Critério de pronto
Jogador não atravessa o parceiro; perto de uma placa aparece "E"; E abre e fecha o balão; afastar fecha.
