# Diário — PyShooter

## Resumo
- Situação (2026-11-22): branch `melhorias-coop` em dia com o GitHub (último commit `570382a`). Apresentação e relatório do T2 em 2026-11-24.
- Jogo: campanha de 4 fases (vitória ao matar Demônio e depois Dragão, em etapas); Modo Desafio = fases 1 a 5, sendo a 5 uma arena de hordas (5 ondas, chefes na última); multiplayer LAN para 2.
- Combate: mira e tiro no mouse (só a arma gira, `entities/aim_pose.py`), ESPAÇO = dash, botão direito = golpe com a arma (quebra caixas de madeira: item, coração +1 vida ou aranha), granada Q/G.
- Vidas (normal): 3 compartilhadas, "-1 VIDA" e renasce no início da fase ou logo depois da última bandeira (também em dupla). Desafio: uma vida por jogador (regras em DECISOES).
- Diversão: pontos, combo até x5, drops, piscar e dano flutuando, tremor; músicas CC0 do MintoDog por tela/fase (`core/music.py`, `audio/musicas/`, créditos em `audio/CREDITOS.md`); tela cheia com F11.
- Editor: Modo Mover (M), desfazer/refazer (Ctrl+Z/Ctrl+Y), checkpoint (tile 88), castelo na saída, aranha (tile 89).
- Documentação: GDD (md/html/pdf, gerados por `tools/gerar_gdd.py`), slides `docs/apresentacao/2026-11-22_slides-pyshooter_v3.pptx`, guia de estudo atualizado.
- Testes: os itens de 2026-11-22 (golpe/caixas/aranha, hordas, tela cheia, músicas) só passaram na conferência rápida (compila e carrega); bot humano e teste_multiplayer não rodaram neles.
- Multiplayer pelo Radmin VPN: Host passa o IP 26.x; liberar UDP 5555 no Firewall do Host; os dois com `git pull origin melhorias-coop`.
- Forma de trabalho: delegar ao Gemini (`ponte-agy`) com roteiros em `docs/tarefas/`; commits sem Co-Authored-By, só quando o Guilherme pede.
- Próximos passos: Guilherme testar jogando (lista no fim da entrada de 2026-11-22); teste em dupla com o Pedro; revisar slides v3; ver se há coração demais nas caixas; "fase 2 não terminou" segue sem descrição.

---
### 2026-11-22 — Fechamento do plano e push
- Pedido: commit e push de tudo; GDD e slides sem "em desenvolvimento"; contexto atualizado.
- Feito: commits `0a5bf87` (renascer no início/bandeira, golpe, caixas, aranhas, vida extra, GDD, slides v3, músicas baixadas), `a65f7cb` (hordas na fase 5, tela cheia, músicas no código) e `570382a` (GDD/slides/guia finais), todos com push na `melhorias-coop`. Trabalho feito em sessões paralelas (plano, documentação, músicas, tela cheia). Entradas até 2026-11-20 movidas para `_CONTEXTO/arquivo/DIARIO_2026-11.md`.
- Para testar jogando: perder vida antes/depois da bandeira (sozinho e em dupla); botão direito em inimigos e caixas (fase 1, colunas 40 e 151-171), aranha e coração (e o coração sumindo no parceiro); aranha colocada no editor (tile 89); Desafio até a fase 5 (quantidade de inimigos, vitória no fim), sozinho e em dupla; F11 e opção de tela cheia (menu, fase, editor; volta em tela cheia ao reabrir); música de cada tela/fase, Climax na 2ª etapa do chefe, vinhetas e volume.
- Comando para ver o bot no Desafio: `python tools/bot_fases.py --desafio --god --visual`.

---

### 2026-11-22 — Documentação sem "em desenvolvimento": GDD, slides v3 e guia (plano, item 5, rodada 2)
- **Pedido:** a sessão "Mira, disparo e dash do jogador" pediu, a mando do Guilherme, tirar do GDD, dos slides v3 e do guia tudo que estava "em desenvolvimento", pois já entrou nos commits 0a5bf87 e a65f7cb (branch melhorias-coop).
- **Feito:**
  - `docs/GDD_Trabalho2.md`: 1.1 (lista do Trabalho 2), Periféricos, controles (botão direito = golpe, F11 = tela cheia), Configurações com TELA CHEIA, HUD com "ONDA x/5", checkpoints ligados em LAN, regra nova de vidas (renasce no início ou um bloco depois da última bandeira, sem recarregar; coração até 5 vidas), seção "Em Desenvolvimento" trocada por "Golpe, Caixas, Aranhas, Hordas, Tela Cheia e Música", paleta com 90 tiles (12 = caixa, 89 = aranha), protocolo com `crate`, `lifeup` e `wave`, RF-19/RF-24 atualizados, RF-32 a RF-36 novos e seção 3.1 com os créditos das músicas (MintoDog, CC0, `audio/CREDITOS.md`). HTML e PDF regerados com `python tools/gerar_gdd.py` (PDF com 21 páginas).
  - Capturas novas em `docs/capturas/`: `v3_golpe_caixa.png`, `v3_golpe_zoom.png`, `v3_caixa_aranha.png`, `v3_caixa_aranha_zoom.png`, `v3_hordas_onda.png`, `v3_hordas_pausa.png`, `v3_opcoes_tela_cheia.png`.
  - `docs/apresentacao/2026-11-22_slides-pyshooter_v3.pptx` regerado a partir do `_v2` (agora 28 slides): novos slides "Fase 5 do Desafio" (arena de hordas), "Golpe e caixas" e "Tela cheia e música" (no lugar de "Em desenvolvimento"); slide de vidas com a regra nova; slide 10 (Desafio) e tabela do protocolo (slide 24) com as mensagens novas. Conferido renderizando no PowerPoint.
  - `docs/2026-11-19_guia-de-estudo-apresentacao.md`: regra nova de vidas e vida extra na 4.9, nova seção 4.10 (golpe, caixas, aranhas, hordas, tela cheia, música), mensagens `crate`, `lifeup` e `wave` na 5.4 e perguntas 20 a 22.
- **Resultados:** nada commitado.
- **Próximos passos:** o Guilherme revisar os slides 11, 14, 15, 24 e 27 do v3 e o GDD; slide 4 (roteiro da demo) ainda é o do v2.

### 2026-11-22 — Fase 5 vira arena de hordas do Desafio (plano, item 2b)
- Pedido: transformar a fase 5 (só do Desafio) numa arena de hordas de inimigos.
- Feito: `levels/level5_data.csv` = arena da fase 4 sem chefes (poço estreitado como na fase 4). Roteiro `docs/tarefas/2026-11-21_fase-17_hordas-fase5.md` executado pelo Gemini e revisado: `core/horde.py` (`start_horde`, `spawn_wave`, `update_horde`), `config.HORDE_WAVES` (5 ondas: soldados; + esqueletos e aranhas; + robôs e sniper; onda maior; Demônio + Dragão + 2 soldados), 3 s de pausa com munição (e vida nas ondas pares) perto do jogador, HUD "ONDA N/M", aviso "ONDA N"/"ONDA FINAL!" e "PRÓXIMA ONDA EM X s". Multiplayer: Host decide e manda `"{pid},wave,fase,n,base_x"`; o cliente cria a mesma onda (target_id = 1000 + n*50 + i) e nunca termina a fase sozinho. Ajuste do Claude: chefes nascem perto da tela do Host (base_x), não nas posições fixas da fase 4.
- Resultados: compila; teste rápido com SDL dummy (inimigos mortos à força) passa pelas 5 ondas e termina a fase (LEVEL_TRANSITION); HUD renderiza. Sem bot humano nem teste_multiplayer (Guilherme testa jogando).
- Próximos passos: Guilherme jogar a fase 5 no Desafio (só e em dupla) e ajustar a quantidade de inimigos se ficar fácil/difícil; commit quando ele pedir.

---

### 2026-11-21 — Tela cheia (F11) e músicas por tela/fase (plano, item 3 + músicas)
- Pedido: item 3 do plano (tela cheia) e ligar as 14 músicas CC0 do MintoDog (`audio/musicas/`, roteiro `docs/tarefas/2026-11-22_musicas-ligar-no-codigo.md`), sem mexer nos arquivos da fase 5 de hordas.
- Feito: `game.py` ganhou `set_display_mode(size)` (único ponto que troca o modo de vídeo; tela cheia = `pygame.SCALED | pygame.FULLSCREEN`, resolução lógica mantida), `toggle_fullscreen()` e `_handle_fullscreen_key()` (F11 lido antes de `core/input_handler.py`, os outros eventos voltam à fila na ordem). `ui/screens/level_editor.py` `on_enter`/`on_exit` usam `game.set_display_mode` (editor 1200x740 também em tela cheia). `ui/screens/options.py`: botão "TELA CHEIA: LIGADA/DESLIGADA (F11)". `core/progress.py`: campo `tela_cheia` e `salvar_tela_cheia()`. Novo `core/music.py` (`MusicPlayer.update(game)` chamado a cada quadro no `game.py`): menu/instruções/seleção/multiplayer/editor = `menu_titulo.ogg`; Opções abertas pela pausa mantêm a música da fase; fases 1-4 com a sua música, fase 4 com `boss_stage >= 2` = Climax, fase 5 = hordas; GAME_OVER = vinheta e depois loop; VICTORY = `vitoria_final.ogg`. Vinhetas como `pygame.mixer.Sound`: "perdeu vida" (quando `life_lost_frames` sobe) e "fase concluída" (PLAYING -> LEVEL_TRANSITION). Volume = `game.music_vol` das Opções. `asset_manager.py` ainda carrega `audio/music2.mp3` na abertura, mas no primeiro quadro ela é trocada pela do menu.
- Resultados: compila; teste com SDL dummy (script no scratchpad) passou por menu, Opções, fases 1-4, chefe etapa 2, Desafio fase 5, game over, vitória e editor com a música certa em cada um; F11 no jogo e no editor. Troca janela <-> tela cheia conferida com janela real (lógica 1200x640/1200x740 mantida). Bot das fases não rodado (pedido do Guilherme: ele testa jogando).
- Próximos passos: Guilherme testar à mão: F11 no menu, numa fase e no editor; botão nas Opções (e se volta ligado ao abrir o jogo); ouvir a música de cada tela/fase e as vinhetas; volume das Opções.

---

### 2026-11-22 — Golpe com a arma, caixas quebráveis, aranhas e vida extra (plano, item 2)
- Pedido: item 2 do plano (golpe corpo a corpo, quebrar caixas de madeira, aranhas, vida extra); a aranha também como tile do editor.
- Feito: roteiro `docs/tarefas/2026-11-21_fase-16_golpe-caixas-aranhas.md` executado pelo Gemini e revisado. Botão direito = golpe (`Player.start_melee`/`melee_rect`, arma gira e arco branco; `update_melee` em `core/gameplay.py`). Caixas tile 12 quebráveis (`World.crates`; não quebram as da última linha nem as que têm bloco em cima) com lascas (`effects.Debris`) e conteúdo sorteado pela posição (`config.CRATE_DROPS`): munição, granada, vida, coração (+1 vida, até `MAX_LIVES = 5`) ou aranha. Aranha em `entities/spider.py` (desenhada no código, local em cada PC), tile 89 no editor e nos assets. Rede: `"{pid},crate,fase,col,linha"` e `"{pid},lifeup,seq"` (Host soma a vida; seq evita contar repetido). Correções do Claude: protocolo no formato padrão (o Gemini tinha mudado `network/server.py`; revertido), item da caixa com id do mundo para sumir nos dois PCs, aranha some ao cair no buraco. Caixas novas colocadas pelo Claude: fase 1 colunas 151/155/166/171, fase 2 43/157/161/168, fase 3 95/167/172.
- Resultados: compila; golpe na caixa da fase 1 (col 40) quebra e solta item; bot `todas` 4/4 e `--desafio --god` sem problemas (antes das caixas novas só o `todas`); fases 1-5 carregam e rodam 3 s. Testes longos (bot humano e multiplayer) pulados a pedido do Guilherme: ele testa jogando.
- Próximos passos: Guilherme testar golpe/caixas/aranha/coração (também no multiplayer); fase 5 de hordas (roteiro fase-17).

---

### 2026-11-21 — Documentação: GDD revisado, gerar_gdd.py, slides v3 e guia (plano, item 5)
- **Pedido:** item 5 do plano (`docs/tarefas/2026-11-21_plano-proximos-passos.md`), em sessão paralela, mexendo só em `docs/` e no novo `tools/gerar_gdd.py`.
- **Feito:**
  - `docs/GDD_Trabalho2.md`: revisado o diff do Gemini contra o roteiro `docs/tarefas/2026-11-21_fase-15_gdd-novidades.md` e o código. Corrigido: "360°" (a arma gira até ±89° e o soldado vira), cronômetro do Desafio é mm:ss.d (não milissegundos), voltou "o Desafio não marca a campanha como zerada", direção do dash (tecla apertada ou lado do olhar), dash invencível a dano (não a "perigos de fase"), vida perdida também por vida zerada, RF-19 (checkpoints no CSV, tile 88), RF-30 (linha de chegada). Nova subseção "Em Desenvolvimento" em 1.5 com o que ainda está entrando.
  - `tools/gerar_gdd.py` (novo): `python tools/gerar_gdd.py [--sem-pdf]` converte o .md (markdown: tables, fenced_code, nl2br, toc), mantém o `<head>`/`<style>` do HTML atual, impede quebra de linha nas células de ID (RF-xx) e gera `docs/GDD_Trabalho2.pdf` com o Edge headless. Resultado: PDF com 19 páginas, tabelas conferidas.
  - Capturas novas em `docs/capturas/v3_*.png` (mira, mira ampliada, dash, -1 VIDA, chefes ETAPA 2/2, pontos, seletor de cor, editor com Modo Mover/checkpoint e castelo). Script usado (fora do repositório, SDL dummy + Bot do bot_fases): scratchpad da sessão, `captura_slides.py`.
  - `docs/apresentacao/2026-11-22_slides-pyshooter_v3.pptx` (26 slides, o `_v2` intacto): 9 slides novos no estilo do v2 (mira, dash, vidas, chefes, pontos/combo/drops, cor, editor, Desafio em dupla e "Em desenvolvimento") com notas do apresentador; cartão de checkpoints do slide 8 atualizado. Conferido renderizando no PowerPoint.
  - `docs/2026-11-19_guia-de-estudo-apresentacao.md`: nova seção 4.9 (aim_pose, dash, regras de vida, chefes em etapas, pontos/combo/drops, effects.py, cor, editor), tabela de mensagens 5.4 com `aim`, `level` com Desafio, `item`, `color`, `death`, `lives`; perguntas 16 a 19.
- **Resultados:** nada commitado. A regra nova de renascer (início/bandeira, item 1) ficou marcada como "em desenvolvimento" no GDD, slides e guia.
- **Próximos passos:** quando os itens 1-4 forem commitados, tirar do "Em desenvolvimento" o que entrou (GDD + `python tools/gerar_gdd.py`, slide 25 do v3, guia 4.9); slide 4 (roteiro da demo) e slide 14 (protocolo) do v3 ainda são os do v2.

### 2026-11-21 — Renascer no início da fase ou depois da bandeira (plano, item 1)
- Pedido: ao perder uma vida, voltar exatamente ao início da fase ou logo depois da última bandeira de checkpoint. Guilherme escolheu a mesma regra no multiplayer.
- Feito: `core/gameplay.py` — `respawn_after_life_lost` usa `respawn_point` (um bloco depois da bandeira ativa, no topo do chão daquela coluna; sem bandeira, `game.level_start`); `track_safe_position`/`safe_pos` removidos; `update_checkpoints` ativa a bandeira quando qualquer jogador da dupla passa. `core/level_loader.py` — `game.level_start` guardado após `process_data`; `checkpoints_enabled` agora só desliga no Desafio (bandeiras em LAN). Regra em `_CONTEXTO/DECISOES.md`.
- Resultados: teste direto na fase 1 (sem bandeira renasce em x=40; com a bandeira em 1940 renasce em 1980); bot `todas` 4/4, `--desafio --god` sem problemas, `--humano 3` igual a antes (fase 3 67%, queda perto de x 4000); `teste_multiplayer` itens 1, 2, 4-7 OK, item 3 em 76% (oscilação conhecida).
- Roteiro do item 2 escrito: `docs/tarefas/2026-11-21_fase-16_golpe-caixas-aranhas.md` (inclui a aranha como tile 89 no editor).
- Próximos passos: Guilherme testar o renascer na mão; Gemini executar a fase 16.

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

