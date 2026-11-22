# Diário — PyShooter

## Resumo
- Jogo: campanha com 4 fases (vitória ao matar os 2 chefes da fase 4), progresso salvo, menu de fases com selos, checkpoints nas fases 1-3 e Modo Desafio (fases 1 a 5 seguidas, com recorde).
- 2026-11-21, branch `melhorias-coop` (a partir de trabalho-parte2, ainda sem push): Ctrl+V no IP, caixas flutuando e sumindo no parceiro, colisão entre jogadores, placas interativas (tecla E), cor do boneco (salva e sincronizada), 3 vidas compartilhadas (Host decide), Host escolhe fase ou Desafio no multiplayer, castelinho na saída das fases 1-3.
- Validado em 2026-11-21: `python tools/bot_fases.py todas` e `--desafio --god` passam; `python tools/teste_multiplayer.py --porta 5601` 7/7 (o item 3 oscila entre 76% e 100%, também no código antigo: medição).
- Multiplayer pelo Radmin VPN: Host passa o IP 26.x; liberar UDP 5555 no Firewall do Host.
- "Fase 2 não terminou" (relato do Guilherme em 2026-11-21): não reproduzido; bot passa a fase 2 sozinho e no multiplayer. Falta saber o que aconteceu.
- Apresentação final do T2: 2026-11-24, com relatório em PDF no Classroom.
- 2026-11-21 (tarde): perder vida não mostra mais a tela vermelha; aparece "-1 VIDA" e o jogador renasce em 1 s ao lado do parceiro ou no último chão firme (GAME OVER só sem vidas). Saída das fases 1-3 movida para o chão plano do fim (coluna 186), com castelinho menor e linha de chegada.
- 2026-11-21 (noite): mira no mouse (tiro no botão esquerdo, em qualquer ângulo), ESPAÇO = dash com rastro azul; renascer não cai mais no buraco; editor com Modo Mover (M), checkpoint como tile 88 e castelo/linha de chegada visíveis; cor do boneco na seleção de fases e sem cor repetida no multi; chefes da fase 4 em etapas (Demônio, depois Dragão); vidas do HUD longe da pausa. Commit 3f399d0 com push.
- 2026-11-21 (noite, 2): arma acompanha a mira (tronco gira na cintura, até 55°; tiro sai do cano). Desafio em dupla com regra própria (uma vida por jogador, quem cai assiste, volta na fase seguinte com metade da vida; os dois caídos = DESAFIO ENCERRADO e o Host recomeça). Modo normal no multiplayer conferido com 2 processos: igual ao single.
- 2026-11-21 (noite, 3): arma separada do corpo por cor (só a arma gira, sem cortar o boneco); bala nunca acerta quem atirou; editor com desfazer/refazer (Ctrl+Z/Ctrl+Y e botões) e castelo na paleta; pontos, combo, drops de inimigos, piscar ao levar tiro, dano flutuando e tremor de tela. Ainda sem commit.
- Próximos passos: Guilherme testar na mão (mira, dash, editor); commit/push; teste no Radmin com o Pedro; esclarecer o problema da fase 2; atualizar slides/GDD (controles mudaram: ESPAÇO não atira mais).

---

### 2026-11-21 — Arma sem corte, autotiro, editor desfazer/refazer, diversão
- Pedido: sprite se cortava ao inclinar; tiro na diagonal acertava o próprio jogador; editor sem desfazer/refazer e sem castelo na paleta; deixar as fases mais divertidas e corrigir bugs.
- Feito: `entities/aim_pose.py` reescrito — cada quadro é separado em camada da arma (cores azuis/laranja, contorno e luvas no retângulo da arma, dedos) e do corpo (buraco do peito preenchido com a cor vizinha); só a arma gira em torno da empunhadura, no ângulo exato; cache por (ação, quadro, cor, escala). `Bullet(owner=...)` ignora quem atirou. Editor (roteiro fase-13): pilhas de desfazer/refazer (um arrasto = um passo), botões e atalhos, castelo nos ids 20/41 da paleta. Diversão (roteiro fase-14): `entities/effects.py` (texto flutuante, tremor), `update_fun` em `core/gameplay.py` (pontos por tipo em `config.KILL_POINTS`, combo até x5 em 2,5 s, drops determinísticos por `target_id`), piscar branco em inimigos/chefes, HUD "PONTOS" e "COMBO".
- Resultados: bot campanha 1-4 e Desafio OK; capturas da mira, do editor e do HUD de combo conferidas.
- Bot `--humano 3`: fases 1-2 100%, fase 3 67% (1 queda perto da coluna 100), fase 4 33% (2 mortes na água logo após o início). Poço de água da fase 4 estreitado de 5 para 3 blocos (`levels/level4_data.csv`, colunas 14-16; rampa na 17): `--humano 5` na fase 4 passou a 100%.
- Próximos passos: commit; testar à mão.

---

### 2026-11-21 — Arma na mira e regras do Desafio em dupla
- Pedido: a arma acompanhar a mira na diagonal; no multiplayer as vidas não apareciam no HUD e aparecia a tela vermelha ao cair; garantir que o Desafio e o modo normal sigam as regras definidas.
- Diagnóstico: teste com Host e Cliente em 2 processos (script temporário) mostrou o modo normal igual ao single (aviso "-1 VIDA", renascer, vidas 3-2-1 nos dois). Os sintomas são do Desafio em multiplayer, que não tinha regra: HUD mostra o cronômetro (sem vidas, por regra) e a morte caía na tela "VOCÊ CAIU!" com Restart ao lado do parceiro. Outra causa possível: PC do parceiro com versão antiga.
- Feito: `entities/aim_pose.py` (corte na cintura, giro limitado a 55°, `muzzle_point`), usado em `entities/player.py` e `entities/remote_player.py`; `Character.shoot` sai do cano. Desafio em dupla: `game.challenge_spectating` em `core/gameplay.py` (câmera segue o parceiro), `restart_challenge_multiplayer` (Host recomeça e o Cliente segue pelo contador `reset` do anúncio "lives"), `ui/screens/game_over.py` mostra DESAFIO ENCERRADO também em dupla (só o Host tem Restart), aviso no HUD em `core/renderer.py`.
- Regras (registradas em DECISOES): normal = 3 vidas compartilhadas, aviso e renascer, sem vidas = GAME OVER; Desafio = uma vida por jogador, sem checkpoints, cronômetro no HUD.
- Resultados: bot campanha e Desafio OK; teste Desafio em dupla OK (cair, voltar na fase 2, os dois caídos, Restart do Host); teste_multiplayer: itens 2 e 3 oscilaram numa rodada com o PC carregado.
- Próximos passos: Guilherme e Pedro testarem com a mesma versão (`git pull`).

---

### 2026-11-21 — Mira no mouse, dash, editor, cor, chefes em etapas
- Pedido: mira e tiro com o mouse, dash no espaço com animação; mover objeto no editor; cor no single e sem repetir no multi; renascer caía no buraco sem parar; chefes da fase 4 um de cada vez; castelo/checkpoint/novos elementos no editor; HUD das vidas por baixo da pausa.
- Feito (roteiros `docs/tarefas/2026-11-21_fase-8_*.md` a `fase-12_*.md`, executados pelo Antigravity e revisados aqui): `Bullet` com ângulo e `Character.shoot(target=...)`; `Player.face_point/start_dash` com rastro e poeira; mira em `core/renderer.py` (`draw_crosshair`); ângulo da mira vai no 8º campo do estado de rede; `game.use_mouse_aim` (o bot desliga). Renascimento: `track_safe_position` exige os dois pés no chão e usa a posição de ~60 quadros antes. Editor (`ui/screens/level_editor.py`): Modo Mover (M), tile 88 = checkpoint (CSVs das fases 1-3 convertidos; `CHECKPOINTS` da config vira reserva), castelo/linha de chegada desenhados, paleta em 7 colunas. `ColorPicker` em `ui/screens/common.py` (seleção de fases e menu multi); o Cliente troca de cor se igual à do Host. Chefes: `game.boss_queue`/`boss_reserve_group` em `core/level_loader.py` e `update_boss_stages` em `core/gameplay.py`.
- Correção feita na revisão: o Antigravity tinha apagado um bloco da fase 1 (`level1_data.csv`), restaurado.
- Resultados: bot campanha 1-4 e Desafio OK; teste_multiplayer 7/7 (porta 5601). Mira/dash/editor conferidos só por captura de tela, não jogados à mão.
- Próximos passos: teste manual; commit.

---

### 2026-11-21 — Vidas sem tela vermelha e castelo no fim da fase
- Pedido: no teste com o Pedro as vidas pareciam não cair; trocar a tela vermelha por aviso e renascer na hora; castelo menor, no chão plano do fim, depois de uma linha de chegada.
- Diagnóstico: teste com 2 processos mostrou as vidas caindo certo (3-2-1-0 nos dois); provável versão antiga num dos PCs. Mesmo assim o cliente agora só aplica anúncio de vidas novo (`get_host_lives` consome o valor) em `network/client.py`.
- Feito: `core/gameplay.py` (`track_safe_position`, `respawn_after_life_lost`, `_revive_at`, morte com vida = aviso + renascer em 1 s); aviso "-1 VIDA / Restam N" em `core/renderer.py`; `tools/teste_multiplayer.py` registra a volta automática no item 6. `entities/castle.py`: castelo 2x2,6 blocos e `FinishLine`; saídas movidas em `levels/level1-3_data.csv` para (linha 14, coluna 186).
- Resultados: bot campanha 1-4 e Desafio passam; teste_multiplayer OK menos o item 3 (oscilação conhecida). Commits f48b6cb e seguinte, com push.
- Próximos passos: testar com o Pedro pelo Radmin.

---

### 2026-11-21 — Melhorias do cooperativo (delegadas ao Gemini)
- Pedido: passo a passo do Radmin VPN; Ctrl+V no IP; colisão entre jogadores; cor do boneco P1/P2; coletáveis com animação e sumindo no parceiro; analisar fase 2; vidas compartilhadas; placas interativas; escolher fase/Desafio no multiplayer; castelinho no fim da fase.
- Feito na branch `melhorias-coop` (7 commits, 09127fd a f3c0e81). Roteiros em `docs/tarefas/2026-11-21_fase-2_*.md` a `fase-7_*.md`, executados pelo Antigravity (ponte-agy) e revisados/testados aqui. Ctrl+V feito direto em `ui/screens/multiplayer_menu.py`.
- Novos comandos de rede: `item`, `color`, `death`, `lives`; o `level` ganhou 5º campo (Desafio). Arquivos novos: `entities/sign.py`, `entities/castle.py`.
- Resultados: bot campanha e Desafio OK; teste_multiplayer 7/7 (item 3 oscila). Fase 2: bot passou sozinho e no multiplayer; problema não reproduzido.
- Próximos passos: push e teste com o Pedro; descobrir o que houve na fase 2.

---

### 2026-11-19 — PowerPoint v2 com as capturas
- Pedido: exportar o .pptx de novo. O navegador do app não estava logado no claude.ai, então o .pptx foi editado direto no PowerPoint instalado (automação COM pelo PowerShell, sem instalar nada).
- Feito: `docs/apresentacao/2026-11-19_slides-pyshooter_v2.pptx` a partir do original (que ficou intacto): slide 9 novo "Quatro fases, quatro cenários" (capturas recortadas no formato 816:290), slide 10 Desafio com as capturas do HUD e da vitória no lugar da caixa ilustrativa, slide 13 novo "A mesma luta nas duas telas", notas dos slides novos e do slide 15 (Correções) iguais às do deck no Claude. Script descartável em %TEMP%\claude_caps\montar_v2.ps1 (precisa de UTF-8 com BOM no PowerShell 5.1, senão os acentos quebram).
- Resultados: 17 slides, conferidos por imagens exportadas pelo próprio PowerPoint; acentos e notas OK. O recorte da fase 1 não mostra o aviso CHECKPOINT (só a bandeira).
- Próximos passos: se mudar o deck no Claude de novo, exportar pelo Share › Export (ou repetir a edição no PowerPoint).

---

### 2026-11-19 — Multiplayer pela rede e capturas nos slides
- Pedido: testar o multiplayer e colocar as capturas nos slides.
- Feito:
  - `tools/teste_multiplayer.py`: opções `--ip ENDERECO` (cliente conecta pelo IP da placa de rede em vez de 127.0.0.1) e `--capturas PASTA` (salva a tela do host e do cliente a cada 5 s, no mesmo segundo do relógio).
  - Item 2 (posição dos inimigos) agora compara o cliente com o host 0 a 0,15 s antes (atraso do LERP 0,2 + rede) e escolhe o atraso com menor erro, exigindo pelo menos metade das comparações. Atraso medido: 0,05 s; com ele a mediana cai de 7 px para 1,4-3 px.
  - Item 4 (inimigo morto nos dois lados) compara os dois lados no mesmo instante (0,5 s antes do primeiro sair da fase) com 0,4 s de folga para o outro lado registrar a morte. Antes falhava quando o inimigo morria no último quadro da fase (foto de um lado antes do tiro, do outro depois).
  - Rodado 2 vezes com `--ip 192.168.15.8` (IP do Wi-Fi do PC de casa): 7/7 OK. As 5 execuções salvas reanalisadas com a regra nova: 7/7 em todas.
  - Capturas novas em docs/capturas/: campanha_fase1_checkpoint, campanha_fase2, campanha_fase3, campanha_fase4_chefes (tiradas por um script descartável com o bot em god), multiplayer_host_fase4 e multiplayer_cliente_fase4 (mesmo segundo).
  - Deck https://claude.ai/artifact/RZB2ojfXmzJr6KcgQK63NL (agora 17 slides): novo slide "fases" (Quatro fases, quatro cenários) depois de "campanha"; novo slide "multitelas" (A mesma luta nas duas telas) depois de "multiplayer"; "desafio" trocou a caixa ilustrativa pelas capturas do HUD e da vitória; notas do slide "correcoes" dizem que o teste automático confirmou as correções. Conferido por prévia local (Edge headless), sem a fonte Oswald.
- Resultados: teste pela rede do mesmo PC não substitui 2 PCs (não passa pelo firewall de outro computador nem pelo roteador entre máquinas).
- Próximos passos: checklist manual em 2 PCs; exportar o .pptx de novo (Share › Export) para docs/apresentacao/.

---

### 2026-11-19 — Validação com pygame no PC de casa (bot, Desafio e multiplayer)
- Pedido: fazer o pull e continuar os testes que ficaram pendentes por falta de pygame no PC da CLM.
- Feito: `git pull` (até f6211ac). Rodados `tools/bot_fases.py --desafio --capturas docs/capturas`, `tools/bot_fases.py --desafio --god --capturas docs/capturas`, `tools/bot_fases.py todas` e `tools/teste_multiplayer.py` (3 vezes).
- Resultados:
  - Campanha (bot): fases 1 a 4 passam.
  - Desafio sem --god: fases 1-3 passam e o bot morre para o DragonBoss na fase 4 (dificuldade do chefe para o bot, não erro de lógica; "problemas" vazio). Com --god: fases 1-5 passam, vida/munição/granadas levadas entre fases, recorde 01:22.7 gravado, campanha não marcada.
  - Multiplayer: itens 1 e 3 a 7 e porta liberada OK desde a 1ª execução. O item 2 (posição dos inimigos) falhava (95% até 18-47 px; tolerância 12 px). Medido o tempo de cada quadro: 100% dos quadros lentos (até ~630 ms) eram o A* do bot (`bot.tick`), não o jogo (p99 do quadro sem o bot: 10-15 ms). Com o processo parado, a comparação fica injusta. Ajuste em `tools/teste_multiplayer.py`: o log grava `ms_bot`/`ms_quadro` e o item 2 descarta 1 s após cada quadro > 50 ms. Resultado: 95% até 11 px, máx 16,5 px -> 7/7 OK.
  - Bug corrigido em `core/renderer.py` (`draw_challenge_hud`): atrás da tela de vitória o HUD mostrava "FASE 6/5"; agora limita em 5/5.
  - Capturas salvas em `docs/capturas/` (desafio_hud_fase1..5.png, desafio_game_over.png, desafio_vitoria.png).
- Próximos passos: commit; teste manual em 2 PCs com o checklist; usar as capturas nos slides.

---

### 2026-11-19 — Guia de estudo para a apresentação
- Pedido: um documento para Guilherme e Pedro lerem e conseguirem explicar o projeto na aula, já que muita coisa foi feita com IA.
- Feito: `docs/2026-11-19_guia-de-estudo-apresentacao.md`, escrito a partir da leitura do código (game.py, core/, entities/, world/, network/, tools/) e do docs/T2.pdf. Seções: discurso de 1 minuto; pedidos do T2 e onde estão; mapa das pastas; loop principal; máquina de estados; fase CSV → `World.process_data`; câmera (`bg_scroll`/`screen_scroll`, mundo × tela); física e colisão AABB; IA dos inimigos; combate; checkpoints, save e Desafio; multiplayer (UDP, threads e Lock, protocolo, quadro do Host × cliente, `target_id`, LERP com exemplo numérico, heartbeat, troca de fase, bugs corrigidos); padrões de projeto com ressalvas honestas (Observer e Proxy não são a forma clássica); bot A* e teste de 2 processos; limitações; 15 perguntas prováveis com respostas; glossário; sugestão de divisão da fala. Links com número de linha conferidos em 2026-11-19.
- Resultados: observado que o comentário de `TILE_SIZE` em config.py diz 37, mas o valor é 40 (640 / 16); não alterado. A data da apresentação no T2.pdf é 2026-11-24.
- Próximos passos: os dois lerem o guia e explicarem a seção 5 (multiplayer) um para o outro; ajustar a divisão da fala.

### 2026-11-19 — Rascunho dos slides da apresentação
- Pedido: começar os slides da apresentação no PC da CLM.
- Feito: deck de 15 slides no Claude (https://claude.ai/artifact/RZB2ojfXmzJr6KcgQK63NL, privado até ser compartilhado pelo menu Share): capa com a arte da fase 1, o jogo, o que entrou no Trabalho 2, demo ao vivo, arquitetura (fachada e core/), máquina de estados, padrões de projeto, campanha, Modo Desafio, bot de testes (8%/0%/8% -> 80%), multiplayer, protocolo, correções, fórmulas e encerramento. Notas do apresentador em cada slide, com o roteiro da demo no slide 4. Conteúdo tirado do docs/GDD_Trabalho2.md e deste diário.
- Exportado para PowerPoint pelo menu Share › Export do deck e salvo em `docs/apresentacao/2026-11-19_slides-pyshooter.pptx` (15 slides).
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
