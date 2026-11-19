# Diário — PyShooter

## Resumo
- Implementado suporte multiplayer LAN UDP completo (Host e Cliente).
- Corrigida a sincronização de dano e morte de inimigos em rede (pacotes `hit` e `target_id`).
- Demanda aberta no Trilho para finalizar bateria de testes e correções até sábado (2026-11-14).
- 2026-11-18: fases 1 a 4 testadas por bot automático (modo solo, dano real). Fases 1, 2 e 3 concluídas; na fase 4 os dois chefes foram mortos, mas o jogo não tem saída nem tela de vitória.
- Problemas abertos: fase 4 sem munição/vida extra (o Dragão costuma matar o bot); fase 5 será a arena do Modo Desafio (etapa 6).
- 2026-11-18: aprovado o plano de melhorias (C:\Users\guilh\.claude\plans\agile-purring-stonebraker.md): campanha com 4 fases e vitória ao matar os chefes da fase 4, progresso no menu de fases, checkpoints, edição dos mapas, Modo Desafio (maratona 1→5 com 1 vida) e, por último, teste do multiplayer.
- Etapa 1 concluída (2026-11-18): bot em tools/bot_fases.py; corrigido bug de câmera ao trocar de fase (core/level_loader.py zera screen_scroll e bg_scroll). Fases 1→2→3 passam em sequência; na fase 4 o Dragão às vezes mata o bot (balanceamento fica para a etapa 5).
- Etapa 2 concluída (2026-11-18): fase 4 termina 1,5 s após a morte dos 2 chefes e a campanha acaba na nova tela VITÓRIA (tempo da partida + botão de voltar ao menu).
- Etapa 3 concluída (2026-11-18): progresso salvo em save/progresso.json (fora do git) e menu de fases com selo CONCLUÍDA e botão MODO DESAFIO (bloqueado até zerar as 4 fases; o clique só funcionará na etapa 6).
- Etapa 4 concluída (2026-11-18): checkpoints com bandeira nas fases 1 a 3 (colunas em config.CHECKPOINTS); Restart da Game Over renasce na última bandeira. Modo humano sem checkpoint: 8% / 0% / 8% de sucesso (fases 1/2/3) — mapas precisam de ajuste na etapa 5.
- Próximos passos: registrar o resultado do modo humano com checkpoint e seguir para a etapa 5 (edição dos mapas); depois atualizar o GDD e preparar a apresentação da aula (semana de 2026-11-23).

---

### 2026-11-18 — Etapa 4 do plano: checkpoints
- Pedido: seguir para a etapa 4.
- Feito:
  - `config.py`: `CHECKPOINTS = {1: [48, 95], 2: [29, 89], 3: [19, 83], 4: []}` (colunas em tiles) e `CHECKPOINT_MSG_FRAMES = 90`.
  - `entities/checkpoint.py` (novo): `CheckpointFlag`, bandeira desenhada com pygame.draw (cinza → verde), apoiada no topo do bloco mais alto da coluna.
  - `core/gameplay.py`: `update_checkpoints` ativa a bandeira quando o centro do jogador passa dela e guarda `game.checkpoint` (col, x, y, munição, granadas, `target_id` dos inimigos mortos).
  - `core/level_loader.py`: `load_level(..., keep_checkpoint=False)` descarta o checkpoint (troca de fase, menu, pausa → sair); `shift_world(game, offset)` move a câmera num mundo recém-carregado; `respawn(game)` recarrega, remove inimigos já mortos, posiciona câmera (bandeira a 1/3 da tela) e jogador com vida cheia, munição salva e 1 s de invencibilidade. Checkpoints desligados no multiplayer e no Desafio (`checkpoints_enabled`).
  - `core/renderer.py`: desenha as bandeiras e o aviso "CHECKPOINT!" por 1,5 s. `ui/screens/game_over.py`: Restart chama `respawn`.
- Como as colunas foram escolhidas: modo humano sem checkpoint (12 tentativas, `--max-seg 90`): fase 1 8% (mortes em x1200-1599 queda/água), fase 2 0% (quedas em x400-1199), fase 3 8% (água em x2000-2399). Script listou colunas com chão plano de 3 tiles acima da água e sem inimigo a menos de 5 colunas; escolhidas uma por volta de 1/3 e outra antes do trecho difícil seguinte. Capturas das 6 bandeiras conferidas.
- Resultados: bot normal (sementes 0 e 1) segue passando nas fases 1-3; teste de checkpoint na fase 1 (col 60 provisória) renasceu em x=2420 com vida 100, munição salva e o inimigo morto removido.
- Observação: nas bandeiras 1-48 e 3-83 há caixa de item no mesmo lugar; ao renascer a caixa volta.
- Pendente: resultado do modo humano com `--checkpoint` (rodando quando o commit foi feito).

### 2026-11-18 — Etapa 3 do plano: progresso salvo e menu de fases
- Pedido: seguir para a etapa 3.
- Feito:
  - `core/progress.py` (novo): `carregar()`, `marcar_fase(n)`, `marcar_campanha_zerada()`, `registrar_tempo_desafio(seg)` (devolve True se for recorde). Arquivo `save/progresso.json`, leitura/gravação protegidas (arquivo ausente ou corrompido = progresso vazio); releitura só quando o arquivo muda. Variável `PYSHOOTER_SAVE` troca o caminho. `save/` no `.gitignore`.
  - `core/gameplay.py` (`update_level_transition`): marca a fase concluída; ao vencer a fase 4 marca a campanha zerada só se as fases 1 a 4 estiverem concluídas (escolher a fase 4 direto no menu não libera o Desafio).
  - `ui/screens/level_select.py`: contorno verde, medalha com visto e texto "CONCLUÍDA" nas fases vencidas; botão de texto "MODO DESAFIO" (cinza + "Zere a campanha para liberar", ou vermelho + recorde/"Sem recorde ainda"). O clique chama `game.start_challenge()` se existir (será criado na etapa 6). Gamepads subiram 60 px para caber o botão.
  - `tools/bot_fases.py`: grava o progresso num arquivo temporário (`%TEMP%/pyshooter_bot_progresso.json`) para não mexer no save real.
- Resultados: teste com save temporário (vazio → 2 fases → campanha zerada → recorde; recorde pior não substitui; arquivo corrompido volta vazio). Capturas do menu conferidas. Fluxo fase 3 → 4 → vitória grava [3, 4] e não libera o Desafio.
- Observação: a tela de vitória diz "Campanha concluída" mesmo quando a pessoa começou pela fase 4.
- Próximos passos: etapa 4 (checkpoints).

### 2026-11-18 — Etapa 2 do plano: fim da campanha e vitória
- Pedido: seguir para a etapa 2 (vitória e fim da campanha).
- Feito:
  - `core/gameplay.py`: `is_level_complete(game, touched_exit)` (saída tocada, ou fase sem saída com chefes e todos mortos há 1,5 s — `BOSS_DEATH_DELAY_FRAMES`); `update_level_transition` vai para `GameState.VICTORY` depois da fase `MAX_LEVELS` (4) em vez de `game.level = 3` + MENU; contador `game.run_frames` (quadros em PLAYING).
  - `game_state.py`: estado `VICTORY`. `ui/screens/victory.py` (nova, `VictoryScreen`): véu escuro semitransparente sobre o cenário, "VITÓRIA!" com contorno, "Campanha concluída", tempo mm:ss.d e botão `lan_back_btn` (volta ao MENU, carrega a fase 1 e encerra o multiplayer se ativo). Ligada em `ui/screens/__init__.py` e em `game.py` (instância + despacho no `run`).
  - `run_frames` zera ao escolher fase no menu de fases e ao iniciar partida multiplayer. `core/level_loader.py` zera `boss_clear_frames`. `core/renderer.py`: fundo de pântano para `level >= 4`.
- Resultados: bot `--god` na fase 4 conclui em 9,0 s; teste 3 → transição → 4 → transição chega em `VICTORY` (captura conferida). Sem `--god`, sementes 0 e 1: fases 1-3 passam e o Dragão mata o bot na fase 4 em 3,8 s (fica para a etapa 5).
- Observação para a etapa 7: no multiplayer cada lado decide a vitória sozinho (sem mensagem de fase na rede).
- Próximos passos: etapa 3 (core/progress.py e selos no menu de fases).

### 2026-11-18 — Etapa 1 do plano: correção da troca de fase
- Pedido: continuar o plano a partir do fim da etapa 1; o bot morria na fase 2 ao jogar fases seguidas no mesmo Game.
- Causa: `game.screen_scroll` guardava o valor do último quadro da fase anterior. No 1º quadro da fase nova, `update_playing` movia inimigos, água, saída e blocos (`world.draw`) por esse valor enquanto `bg_scroll` já era 0, deixando o mundo alguns px deslocado da câmera (bot caía em x≈1891 da fase 2). Afeta também o jogo real (troca de fase, Restart, menu).
- Feito: `core/level_loader.py` (`load_level`) agora zera `screen_scroll` e `bg_scroll`. `tools/bot_fases.py`: `random.seed(seed)` por fase (IA dos inimigos usa random; teste reproduzível) e correção da leitura de argumentos (`--seed 1` pulava a fase 1).
- Resultados: `python tools/bot_fases.py 1 2 3 4 --seed N` (N = 0, 1, 2): fases 1, 2 e 3 passam; fase 4 sem vitória (esperado, etapa 2) e às vezes morte pelo DragonBoss em x≈1063 (etapa 5: caixas de vida/munição).
- Próximos passos: etapa 2 (vitória/fim da campanha).

### 2026-11-18 — Teste automático das fases (modo solo)
- Pedido: testar as fases jogando e passando por elas.
- Feito: criado um bot headless (SDL dummy, tempo fixo de 60 FPS) que planeja o caminho com A* usando a colisão real do `Player` e joga o loop real (`update_playing`), atirando nos inimigos. Script fora do repositório, na pasta temporária da sessão (`scratchpad/bot.py`); não foi versionado.
- Resultados com dano real: fase 1 passou em 21,7 s (vida 90); fase 2 passou em 19,4 s (vida 75); fase 3 passou em 24,2 s (vida 65); fase 4 os dois chefes (Demônio e Dragão) foram mortos em 7 s (vida 45).
- Problemas encontrados no código:
  - `levels/level4_data.csv` não tem tile de saída (20/41) e nada no código detecta chefes mortos: após vencer a fase 4 o jogo fica parado em PLAYING.
  - `config.py`: `MAX_LEVELS = 4`, então `levels/level5_data.csv` nunca é carregada.
  - `core/gameplay.py`, `update_level_transition`: ao fim da campanha faz `game.level = 3` (provavelmente deveria ser 1).
  - Fase 4 não tem caixa de munição; quem errar muitos tiros no Dragão (que voa acima da linha de tiro quando longe) fica sem como vencer.
  - Observação: ao cair de uma beirada sem pular, `in_air` continua False e o jogador pode pular no ar.
- Próximos passos: corrigir o fim da campanha e testar o multiplayer.
- Na mesma conversa: aprovado o plano de melhorias (decisões: 4 fases na campanha, fase 5 como arena final do Modo Desafio, desafio = maratona com 1 vida e recorde de tempo, permitido editar CSVs e criar checkpoints). Criado tools/bot_fases.py (bot reutilizável com modo humano `--humano N` e mapa de mortes). Registrada a pendência de preparar a apresentação da aula (código, gameplay, slides e GDD atualizado).

### 2026-11-12 — Sincronização de Inimigos no Multiplayer e Integração ao Trilho
- Identificado descompasso visual onde inimigos morriam na tela do atirador mas continuavam vivos na tela do outro jogador.
- Implementado sistema determinístico de IDs para inimigos e chefes em `core/level_loader.py`.
- Criado pacote UDP `hit` em `network/protocol.py` e fila thread-safe em `network/client.py`.
- Integrada transmissão de acertos em `entities/combat/projectiles.py` e consumo em `core/gameplay.py`.
- Alterações commitadas e enviadas ao repositório remoto GitHub (`trabalho-parte2`).
- Projeto vinculado ao Trilho com demanda registrada para sábado.
