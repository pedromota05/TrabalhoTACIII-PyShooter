# Diário — PyShooter

## Resumo
- Jogo: campanha com 4 fases (vitória ao matar os 2 chefes da fase 4), progresso salvo, menu de fases com selos, checkpoints nas fases 1-3 e mapas ajustados (modo humano 80% nas fases 1-3).
- Plano de melhorias (C:\Users\guilh\.claude\plans\agile-purring-stonebraker.md): etapas 1 a 7 com código pronto na branch trabalho-parte2.
- 2026-11-19: etapa 6 (Modo Desafio, commit a8983ea) e etapa 7 (multiplayer, commit 58e26eb) feitas no PC da CLM, SEM pygame instalado (pedido para não baixar dependências).
- Validado no PC da CLM: lógica da transição do Desafio e da sincronização de fase (com módulos falsos) e mensagens de rede com sockets UDP reais (12/12 OK).
- NÃO validado ainda: bot --desafio jogando de verdade, capturas de tela do HUD/vitória e tools/teste_multiplayer.py (precisam de pygame).
- Multiplayer: nova mensagem "level"/"levelreq" (fase sincronizada), bala remota só visual (antes dava dano em dobro e fogo amigo), jogador morto não cai por timeout, Restart renasce ao lado do parceiro, Pausa -> Sair desconecta.
- GDD (docs/GDD_Trabalho2.md) atualizado com Vitória, Desafio, checkpoints e protocolo; checklist manual em docs/checklist_teste_multiplayer.md.
- 2026-11-19: rascunho dos slides da apresentação (15 slides) em https://claude.ai/artifact/RZB2ojfXmzJr6KcgQK63NL, com roteiro da demo nas notas.
- Próximos passos: no PC de casa rodar `python tools/bot_fases.py --desafio --capturas docs/capturas` e `python tools/teste_multiplayer.py`, corrigir o que falhar; teste manual em 2 PCs; revisar os slides, pôr capturas da gameplay e ensaiar (semana de 2026-11-23).

---

### 2026-11-19 — Rascunho dos slides da apresentação
- Pedido: começar os slides da apresentação no PC da CLM.
- Feito: deck de 15 slides no Claude (https://claude.ai/artifact/RZB2ojfXmzJr6KcgQK63NL, privado até ser compartilhado pelo menu Share): capa com a arte da fase 1, o jogo, o que entrou no Trabalho 2, demo ao vivo, arquitetura (fachada e core/), máquina de estados, padrões de projeto, campanha, Modo Desafio, bot de testes (8%/0%/8% -> 80%), multiplayer, protocolo, correções, fórmulas e encerramento. Notas do apresentador em cada slide, com o roteiro da demo no slide 4. Conteúdo tirado do docs/GDD_Trabalho2.md e deste diário.
- Resultados: sem capturas de gameplay (o PC da CLM não tem pygame); o slide de correções afirma correções do multiplayer que ainda não foram validadas com o teste completo.
- Próximos passos: revisar textos, incluir capturas de tela da gameplay, dividir a fala entre Guilherme e Pedro e ensaiar.

### 2026-11-19 — Etapas 6 (Modo Desafio) e 7 (teste do multiplayer)
- Pedido: fazer as etapas 6 e 7 do plano no PC da CLM, evitando baixar dependências (pygame-ce não está instalado nesta máquina).
- Feito (etapa 6, commit a8983ea):
  - `game.py`: `challenge_mode`, `challenge_levels = [1, 2, 3, 4, 5]`, `challenge_index`, `challenge_new_record` e `Game.start_challenge()`; `challenge_mode = False` ao iniciar multiplayer.
  - `core/gameplay.py`: `update_challenge_transition` leva vida (máx. 100), munição e granadas para a fase seguinte; depois da fase 5 grava `progress.registrar_tempo_desafio(run_frames / FPS)` e vai para VICTORY; não marca fases nem campanha.
  - `core/renderer.py`: `draw_challenge_hud` (cronômetro mm:ss.d e "FASE x/5" no topo central).
  - `ui/screens/game_over.py`: "DESAFIO ENCERRADO" + fase/tempo; Restart recomeça o Desafio na fase 1 (lógica do botão agora em `GameOverScreen.restart`).
  - `ui/screens/victory.py`: "Desafio concluído", tempo, recorde e "NOVO RECORDE!".
  - `ui/screens/level_select.py` (botão chama `game.start_challenge()`, fase normal desliga o Desafio) e `ui/screens/pause.py` (Sair desliga o Desafio).
  - `tools/bot_fases.py`: opção `--desafio` (com `--capturas PASTA`), que passa pelas transições reais e confere vida/munição levadas, checkpoints desligados, recorde gravado e campanha não marcada.
- Feito (etapa 7, commit 58e26eb):
  - `network/protocol.py` e `network/client.py`: mensagens `level` (Host -> clientes, fase e vitória, repetida a cada 0,5 s) e `levelreq` (cliente -> Host ao chegar na saída); lote `enemies` leva a fase e o cliente descarta lotes de outra fase.
  - `core/gameplay.py`: `sync_multiplayer_level` (chamada a cada quadro, inclusive em Game Over e Vitória); cliente pede a troca de fase em vez de trocar sozinho; jogador morto continua mandando sinal (antes caía por timeout em 5 s); `respawn_multiplayer` renasce ao lado do parceiro sem recarregar a fase (`core/level_loader.py`: `move_camera`).
  - `entities/combat/projectiles.py` + `entities/remote_player.py`: bala de jogador remoto é só visual (`visual_only`); antes o Host aplicava o dano duas vezes e a bala do parceiro feria o jogador local.
  - `ui/screens/pause.py`: Sair no multiplayer chama `clean_multiplayer()`.
  - `tools/teste_multiplayer.py` (novo): host e cliente headless em 2 processos (subprocess, sem fork), guiados pelo Bot, com 7 verificações (se veem, posição dos inimigos por target_id, tiro do cliente, morte de inimigo, tiros inimigos, morte de jogador, troca de fase/vitória) e checagem da porta liberada.
  - `docs/checklist_teste_multiplayer.md` (novo) e `docs/GDD_Trabalho2.md` (Vitória, Desafio, checkpoints, protocolo, RF-17 a RF-21).
- Resultados: tudo compila; testes no PC da CLM sem pygame passaram — transição do Desafio (fases 1->5, vida/munição/granadas, recorde novo/não novo, campanha intacta), `sync_multiplayer_level` (anúncio, pedido, carga em Game Over, vitória) e rede com sockets UDP reais em 127.0.0.1 (12/12, porta liberada). O analisador do teste multiplayer foi conferido com logs sintéticos. Nenhuma captura de tela foi gerada (sem pygame).
- Próximos passos: no PC de casa, `python -m pip install pygame-ce Pillow` se faltar; rodar `python tools/bot_fases.py --desafio --capturas docs/capturas` (conferir capturas e recorde) e `python tools/teste_multiplayer.py` (permitir o Python no Firewall se pedir); corrigir o que falhar; teste manual em 2 PCs com o checklist; slides.

### 2026-11-18 — Etapa 5 do plano: edição dos mapas
- Pedido: seguir para a etapa 5 enquanto o teste da etapa 4 rodava.
- Bot (`tools/bot_fases.py`): o modo humano agora erra o pulo de -6 a +6 quadros (metade adiantado, metade atrasado; antes só atrasava) e só hesita no chão. O teste humano com `--checkpoint` iniciado na etapa 4 foi interrompido (usava o modelo e os mapas antigos) e não foi refeito.
- Mapas editados (só tiles de terreno/caixas; spawn e saídas intactos):
  - `levels/level1_data.csv`: col 32 virou pilar (poço de água 2→1 bloco); plataforma estendida até col 37 (buraco 2→1); blocos 61 em (10,117), (12,119), (12,137), (10,144).
  - `levels/level2_data.csv`: pedra em (14,12); plataformas estendidas (13,18) e (11,27); degraus da escada final alargados para 2 blocos (cols 42/44, 47, 50, 53, 56); apoios em (12,85), (9,94), (8,97).
  - `levels/level3_data.csv`: blocos de gelo alargados (10,54), (9,57), (10,154), (9,157), (8,161); degrau (11,153); pilares 98/102/106/110/114 com 2 blocos (cols 99, 103, 107, 111, 115).
  - `levels/level4_data.csv`: munição (14,33) e (14,48), vida (14,40), granada (14,30), plataforma tile 73 em (13,44-47).
  - `levels/level5_data.csv`: mesmas caixas e plataforma; Demônio de (14,37) trocado pelo Dragão em (10,52).
- Resultados (modo humano, sem checkpoint): fase 1 80% (10 tentativas), fase 2 80% (10), fase 3 80% (20); nenhum trecho com mais de 30% das mortes na fase 3 final. Bot normal sementes 0 e 1: fases 1-5 passam em sequência (fase 4 vida 40/90, fase 5 vida 90/95). Capturas dos trechos editados conferidas.
- Próximos passos: etapa 6 (Modo Desafio).

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
- Pendente: resultado do modo humano com `--checkpoint` (interrompido; ver etapa 5).

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
