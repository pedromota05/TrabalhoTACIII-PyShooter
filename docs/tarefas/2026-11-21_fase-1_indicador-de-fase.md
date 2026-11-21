# Tarefa: mostrar no HUD qual fase está sendo jogada

## Objetivo
Hoje, na campanha, o jogador termina uma fase e cai na próxima sem saber que mudou. Mostrar (1) um texto fixo "FASE N/4" no HUD da campanha e (2) um aviso grande "FASE N" centralizado por 2 segundos sempre que uma fase começa.

## Já feito (não refazer)
- No Modo Desafio já existe "FASE x/5" fixo no topo central: `draw_challenge_hud()` em `core/renderer.py`. Não alterar essa função.
- O aviso "CHECKPOINT!" (em `draw_game_entities`, `core/renderer.py`) já usa um contador de quadros `game.checkpoint_msg_frames`, decrementado em `update_checkpoints()` (`core/gameplay.py`). Copie esse padrão.

## Arquivos permitidos
- `config.py`
- `core/level_loader.py`
- `core/gameplay.py`
- `core/renderer.py`
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. `config.py`: logo abaixo da linha `CHECKPOINT_MSG_FRAMES = 90 ...`, adicionar:
   ```python
   LEVEL_BANNER_FRAMES = 120  # aviso "FASE N" no início de cada fase (2 s)
   ```
2. `core/level_loader.py`, função `load_level(game, level_number, keep_checkpoint=False)`: logo depois da linha `game.checkpoint_msg_frames = 0`, adicionar:
   ```python
   # Aviso "FASE N" só quando a fase começa do zero (não ao renascer no checkpoint).
   game.level_banner_frames = 0 if keep_checkpoint else LEVEL_BANNER_FRAMES
   ```
   e importar `LEVEL_BANNER_FRAMES` de `config` no import já existente de `config` desse arquivo.
3. `core/gameplay.py`, função `update_checkpoints(game)`: logo depois do bloco
   ```python
   if game.checkpoint_msg_frames > 0:
       game.checkpoint_msg_frames -= 1
   ```
   adicionar:
   ```python
   if getattr(game, 'level_banner_frames', 0) > 0:
       game.level_banner_frames -= 1
   ```
4. `core/renderer.py`:
   a. Adicionar `MAX_LEVELS` ao import de `config` no topo.
   b. Criar a função (depois de `draw_challenge_hud`):
   ```python
   def level_label(game) -> tuple[int, int]:
       """(fase atual, total) para o HUD: no Desafio conta pela lista do desafio."""
       if getattr(game, 'challenge_mode', False):
           total = len(game.challenge_levels)
           return min(game.challenge_index + 1, total), total
       return game.level, MAX_LEVELS


   def draw_level_banner(game) -> None:
       """Aviso grande 'FASE N' centralizado enquanto level_banner_frames > 0."""
       if getattr(game, 'level_banner_frames', 0) <= 0:
           return
       fase, total = level_label(game)
       _blit_shadowed(game, f'FASE {fase}', WHITE, game.title_font,
                      SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)
       _blit_shadowed(game, f'de {total}', WHITE, game.font_bold,
                      SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
   ```
   c. Em `draw_game_entities`, trocar
   ```python
   if getattr(game, 'challenge_mode', False):
       draw_challenge_hud(game)
   ```
   por
   ```python
   if getattr(game, 'challenge_mode', False):
       draw_challenge_hud(game)
   else:
       fase, total = level_label(game)
       _blit_shadowed(game, f'FASE {fase}/{total}', WHITE, game.font_bold,
                      SCREEN_WIDTH // 2, 8)
   draw_level_banner(game)
   ```

## O que NÃO fazer
- Não mudar `draw_challenge_hud`, `update_level_transition`, `update_challenge_transition`, nem nada de multiplayer/rede.
- Não criar arquivos novos, não mexer em `tools/`, `ui/`, `game.py`, `save/`.
- Não trocar fontes, cores nem posições do HUD já existente (vida, munição, granada, checkpoint).
- Não rodar git (commit, add, branch): isso fica comigo.

## Verificação (eu rodo)
- `python tools/bot_fases.py todas --god` → as 4 fases com "passou".
- `python tools/bot_fases.py --desafio --god` → sem erro.
- `python tools/bot_fases.py 1 --visual` → ver "FASE 1/4" no topo e o aviso "FASE 1" no início.

## Critério de pronto
Os 4 passos aplicados só nos 4 arquivos permitidos, sem outras mudanças.
