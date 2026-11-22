# 2026-11-22 — Atalho de teste: abrir o Desafio direto na Fase 5

## Objetivo
Permitir `python main.py --fase5` para abrir o jogo já no Modo Desafio, na Fase 5 (hordas), sem passar pelo menu e pelas fases 1 a 4. Serve só para teste; não grava recorde.

## Já feito (não refazer)
- `game.py`: `Game.start_challenge()` (linha ~270) começa o Desafio em `self.challenge_levels[0]`; `main()` (linha ~415) cria `Game()` e chama `game.run()`.
- `core/gameplay.py`, `update_challenge_transition` (linha ~923): depois da última fase chama `progress.registrar_tempo_desafio(...)` e vai para `GameState.VICTORY`.

## Arquivos permitidos
- `game.py`
- `core/gameplay.py`
- Qualquer outro: não tocar.

## Passos
1. `game.py`, no `__init__` de `Game`, junto de `self.challenge_new_record = False` (linha ~103): adicionar `self.challenge_cheat = False  # Desafio aberto por atalho de teste: não grava recorde`.
2. `game.py`, `start_challenge`: mudar a assinatura para `def start_challenge(self, start_index: int = 0) -> None:`; definir `self.challenge_index = start_index` e `self.level = self.challenge_levels[start_index]`; definir `self.challenge_cheat = start_index > 0`. O resto igual. Atualizar a docstring com uma frase sobre `start_index`.
3. `game.py`, `main()`: depois de `game = Game()`, se `'--fase5' in sys.argv`, chamar `game.start_challenge(start_index=game.challenge_levels.index(5))` e imprimir `print('[atalho] Desafio direto na fase 5 (recorde não é gravado)')`. Garantir `import sys` no topo do arquivo (se já existir, não duplicar).
4. `core/gameplay.py`, `update_challenge_transition`: trocar a linha do recorde por
   `game.challenge_new_record = False if getattr(game, 'challenge_cheat', False) else progress.registrar_tempo_desafio(game.run_frames / FPS)`.

## O que NÃO fazer
- Não mudar o comportamento sem `--fase5` (start_challenge() sem argumento deve ficar igual).
- Não mexer no menu, no multiplayer nem em `tools/`.
- Não rodar comandos, não fazer git.

## Verificação (o Claude roda)
- `python -m compileall -q game.py core/gameplay.py`
- Script headless: `Game().start_challenge(4)` → `level == 5`, `horde_active` True, `challenge_cheat` True; `start_challenge()` → `level == 1`, `challenge_cheat` False.
- `python tools/bot_fases.py 1` continua "passou".

## Critério de pronto
Verificações OK; diff só nos dois arquivos permitidos.
