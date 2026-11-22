# Músicas: ligar no código (item 4 do plano de 2026-11-21)

## Objetivo
Trocar a música única (`audio/music2.mp3`, carregada em `asset_manager.py` `_load_music`) por uma música para cada tela ou fase. Os arquivos já estão baixados em `audio/musicas/`. Os créditos estão em `audio/CREDITOS.md` e também precisam entrar no GDD.

## Qual arquivo toca em qual tela/fase
Todos são `.ogg` (Vorbis), CC0 e feitos para tocar em loop (`pygame.mixer.music.play(-1)`).

| Tela / momento | Arquivo | Observação |
|---|---|---|
| Menu principal e telas de menu (seleção de fase, opções, instruções, multiplayer) | `audio/musicas/menu_titulo.ogg` | Não reiniciar ao trocar entre telas de menu se já estiver tocando. |
| Fase 1 (floresta) | `audio/musicas/fase1_floresta.ogg` | |
| Fase 2 (pântano) | `audio/musicas/fase2_pantano.ogg` | |
| Fase 3 (neve) | `audio/musicas/fase3_neve.ogg` | |
| Fase 4 (chefes) | `audio/musicas/fase4_chefe.ogg` | Chefes em etapas: `game.boss_stage` / `game.boss_stage_total`. |
| Fase 4, última etapa do chefe (opcional) | `audio/musicas/fase4_chefe_climax.ogg` | Trocar quando `game.boss_stage == game.boss_stage_total` (incremento em `core/gameplay.py` ~linha 334). Se der trabalho, pode ficar só a `fase4_chefe.ogg`. |
| Fase 5 / Modo Desafio (hordas) | `audio/musicas/fase5_desafio_hordas.ogg` | `game.challenge_mode` em `core/level_loader.py`. |
| Editor de fases (teste) | a da fase testada, ou `menu_titulo.ogg` | Decisão livre. |
| Tela de game over (`ui/screens/game_over.py`) | `audio/musicas/gameover_vinheta.ogg` uma vez (`play(0)`), depois `gameover_loop.ogg` em loop | Para encadear: `pygame.mixer.music.queue(gameover_loop.ogg)` não repete em loop; mais simples é tocar a vinheta e, quando `get_busy()` virar False, tocar o loop com `play(-1)`. Se der trabalho, só o loop. |
| Tela de vitória (`ui/screens/victory.py`, fim do jogo) | `audio/musicas/vitoria_final.ogg` | Em loop. |
| Fase concluída (ao tocar a linha de chegada, antes da próxima fase) | `audio/musicas/vinheta_fase_concluida_curta.ogg` (ou `_longa`) | Vinheta, tocar uma vez. Opcional. |
| Perdeu uma vida ("-1 VIDA") | `audio/musicas/vinheta_perdeu_vida.ogg` | Curta (~2 s). Melhor como `pygame.mixer.Sound` (efeito) para não cortar a música da fase. Opcional. |
| Invencível (se existir power-up/estado de invencibilidade) | `audio/musicas/invencivel_loop.ogg` | Opcional; só se o jogo tiver esse estado. |

## Como ligar (sugestão)
1. Em `asset_manager.py`: trocar `_load_music` por uma função `play_music(path)` que só chama `pygame.mixer.music.load(path)` e `play(-1, 0.0, fade_ms)` quando `path` for diferente do que já está tocando, e guardar o volume atual (`game.music_vol`, ajustado em `ui/screens/options.py`), sem voltar para 0.2 a cada troca.
2. Em `core/level_loader.py` `load_level`: escolher o arquivo pelo número da fase (dicionário `{1: ..., 2: ..., 3: ..., 4: ..., 5: ...}`) e pelo `challenge_mode`.
3. Nas telas de menu (`ui/screens/menu.py`, etc.) chamar `play_music(menu_titulo.ogg)` ao entrar.
4. Respeitar o botão de música ligada/desligada que já existe (ícones `music_on`/`music_off`).
5. Multiplayer: cada computador toca a sua música localmente; não precisa mandar nada pela rede.

## Verificação
Rodar o jogo, passar por menu → fase 1 → 2 → 3 → 4 → Desafio, perder até o game over e vencer o jogo, e conferir que cada uma troca a música e que o volume das Opções se mantém.
