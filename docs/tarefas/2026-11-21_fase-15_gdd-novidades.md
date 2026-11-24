# Tarefa: atualizar o GDD com as novidades de 2026-11-21

## Objetivo
Atualizar `docs/GDD_Trabalho2.md` com tudo o que entrou no jogo em 2026-11-21, mantendo o estilo do documento (português formal, tabelas Markdown, fórmulas em `$$...$$`). Depois gerar o HTML a partir do Markdown no mesmo modelo do `docs/GDD_Trabalho2.html` atual.

## Já feito (não refazer)
- O GDD tem as seções 1.1 a 1.10, 2 (UML) e 3. O HTML `docs/GDD_Trabalho2.html` é o Markdown convertido (tabelas e blocos de código), com um `<head>` com `<style>` próprio (A4, Segoe UI). Eu gero o PDF depois.

## Arquivos permitidos
- `docs/GDD_Trabalho2.md`
- `docs/GDD_Trabalho2.html`
- Qualquer outro arquivo: NÃO tocar.

## Novidades (fatos do código; não invente nada além disto)
1. **Mira e tiro com o mouse:** a mira é desenhada no lugar do cursor durante a fase; o botão esquerdo atira na direção do cursor em qualquer ângulo (`Bullet` com ângulo: $v_x=\cos\theta\cdot V$, $v_y=\sin\theta\cdot V$). O soldado vira para o lado do cursor. A arma é separada do sprite pela cor dos pixels (azuis/laranja, contorno e luvas) e só ela gira em torno da empunhadura até o ângulo da mira; o corpo fica parado (`entities/aim_pose.py`). A bala sai da ponta do cano e nunca acerta quem atirou (`Bullet.owner`).
2. **Dash (ESPAÇO):** 10 quadros a 16 px/quadro, sem gravidade, recarga de 50 quadros, invencível durante o dash; rastro de 6 "fantasmas" azuis e poeira; barrinha de recarga abaixo da mira (`config.DASH_*`).
3. **Vidas (modo normal):** 3 vidas compartilhadas (também no multiplayer, Host é a autoridade: mensagens `death` e `lives`). Ao cair com vida sobrando aparece "-1 VIDA / Restam N" e o jogador renasce sozinho em 1 s: ao lado do parceiro vivo (multiplayer) ou na última posição segura (os dois pés no chão, cerca de 1 s antes da queda). Sem vidas: GAME OVER; com 1 jogador o Restart recomeça a fase com as vidas cheias; em dupla quem fica sem vidas espera e, com todos mortos, o Host recomeça a fase em 3 s. HUD: "VIDAS" com bolinhas no canto superior direito, antes do botão de pausa.
4. **Modo Desafio em dupla:** uma vida por jogador. Quem cai não renasce: vê "VOCÊ CAIU! Desafio: uma vida só. Aguardando o parceiro terminar a fase…" e a câmera acompanha o parceiro; se o parceiro terminar a fase, quem caiu volta na fase seguinte com metade da vida. Se os dois caírem: "DESAFIO ENCERRADO" nos dois PCs e só o Host tem o Restart, que recomeça o Desafio da fase 1 para ambos.
5. **Chefes em etapas (fase 4):** primeiro o Demônio; 1,5 s depois que ele morre o Dragão surge com explosões e o aviso "ETAPA 2/2"; HUD "CHEFE x/2". A vitória exige o último chefe morto.
6. **Diversão:** pontos por inimigo (`config.KILL_POINTS`: soldado 100, robô 150, esqueleto 150, sniper 200, Demônio 1500, Dragão 2000); combo: cada morte em até 2,5 s da anterior aumenta o multiplicador (até x5), pontos ganhos = base × combo; HUD "PONTOS" e "COMBO xN" com barra de tempo. Inimigos comuns podem soltar caixa (munição 25%, vida 10%, granada 8%), sorteio determinístico por `target_id` (igual nos dois PCs). Inimigo e chefe piscam branco ao levar dano e o dano aparece flutuando; granada e morte de chefe tremem a tela.
7. **Cor do boneco:** seletor (VERDE, AZUL, VERMELHO, AMARELO, ROXO) na Seleção de Fases e no Menu Multiplayer, salvo no progresso; no multiplayer o Cliente com a mesma cor do Host troca sozinho para a próxima livre e vê um aviso (mensagem `color`).
8. **Itens e placas:** caixas flutuam e mostram texto ao pegar; no multiplayer a caixa pega some no parceiro (mensagem `item`). Placas (tile 23) mostram dicas com a tecla **E**. Colisão entre os dois jogadores (dá para subir na cabeça do parceiro).
9. **Saída das fases 1-3:** castelinho desenhado pelo jogo (pedra na fase 1, forte de madeira na 2, gelo na 3) com linha de chegada 6 blocos antes, no chão plano do fim da fase.
10. **Multiplayer – seleção:** o Host escolhe a fase ou o Modo Desafio ao criar o servidor (mensagem `level` com 5º campo = Desafio). Campo de IP aceita Ctrl+V e seleciona tudo ao clicar.
11. **Editor de fases:** paleta com 89 tiles em 7 colunas; id 88 = bandeira de checkpoint (os checkpoints agora vêm do CSV; `config.CHECKPOINTS` só se a fase não tiver nenhum); ids 20/41 aparecem como castelo na paleta e no mapa (com a linha de chegada); **M** liga o Modo Mover (arrastar um objeto para outra célula; troca de lugar se a célula estiver ocupada; ESC ou botão direito cancelam); **Ctrl+Z / Ctrl+Y** (ou Ctrl+Shift+Z) e botões "Desfazer"/"Refazer" (um arrasto = um passo, até 100 passos).
12. **Protocolo – formatos atuais:** estado `player_id,x,y,action,direction,is_shooting,health,aim` (aim = ângulo da mira em radianos, usado para a bala e a pose do parceiro); `level` = `player_id,level,fase,vitória,desafio`; novos: `player_id,item,fase,item_id`, `player_id,color,indice`, `player_id,death,seq` (cliente avisa a morte ao Host, enviado 3 vezes), `player_id,lives,vidas,reset` (Host anuncia; `reset` crescente faz o cliente recomeçar a fase/Desafio).

## Passos
1. Seção 1.1: na lista do Trabalho 2, acrescentar um item curto "Combate e Diversão" resumindo mira no mouse, dash, vidas, pontos/combo e chefes em etapas.
2. Tabela 1.3 (Periféricos): "Teclado (movimento, pulo, dash, granada, placas) e Mouse (mira, tiro, menus e editor)".
3. 1.4.1 Controles de Gameplay: trocar a linha do Espaço por "**Espaço** | Dash (impulso rápido com invencibilidade; recarga de ~0,8 s)"; acrescentar "**Mouse** | Mirar (a arma acompanha o cursor)", "**Botão Esquerdo do Mouse** | Atirar na direção da mira (segurar para tiro contínuo)", "**E** | Ler placa próxima". Controles do Editor: acrescentar M, Ctrl+Z, Ctrl+Y/Ctrl+Shift+Z e os botões "Mover (M)", "Desfazer", "Refazer".
4. 1.5 Descrição das Telas: Seleção de Fase e Menu Multiplayer ganham o seletor de cor (e o Host escolhe fase/Desafio); Game Over passa a descrever as regras do item 3 e 4 (sem vidas / Desafio encerrado / aguardando o parceiro); a tela de jogo mostra "-1 VIDA".
5. "Progressão, Checkpoints e Modo Desafio": reescrever com os itens 3, 4, 5, 6 e 9 (checkpoints = tile 88 no CSV; desligados no Desafio e no multiplayer). Pode virar subtópicos em lista.
6. 1.6 Editor: atualizar paleta (89 tiles, 7 colunas, 88 checkpoint, 20/41 castelo, 22 Speed Boost, 23 placa) e acrescentar Modo Mover e Desfazer/Refazer.
7. 1.7.1 Protocolo: atualizar o formato do estado (com `aim`), o `level` (5º campo) e acrescentar os itens `item`, `color`, `death`, `lives` (item 12). 1.7.4 RemotePlayer: mostra a cor do parceiro e a arma girando para a mira dele.
8. 1.9: acrescentar "1.9.6 Mira do Jogador e Giro da Arma" (θ = atan2 do cursor; ângulo local limitado a ±89°; rotação da camada da arma em torno da empunhadura e ponto do cano: $P_{cano} = P_{pivô} + R(\theta)\,(P_{cano}^0 - P_{pivô}^0)$), "1.9.7 Dash" (deslocamento total = 10 × 16 = 160 px ≈ 4 blocos) e "1.9.8 Pontuação com Combo" ($\text{ganho} = \text{base} \times \min(5, c)$, com $c$ reiniciando após 150 quadros sem morte).
9. 1.10 RF: acrescentar RF-22 a RF-31: mira e tiro no mouse; dash; vidas compartilhadas com renascer automático; Desafio em dupla; chefes em etapas; pontos, combo e drops; cor do boneco sem repetir; itens/placas/colisão entre jogadores; castelo de saída; editor com mover, desfazer/refazer e checkpoint. RF-03 passa a dizer "com o botão esquerdo do mouse, na direção da mira".
10. HTML: regenerar `docs/GDD_Trabalho2.html` a partir do Markdown novo mantendo exatamente o `<head>`/`<style>` atual; o corpo deve refletir todo o Markdown (títulos, tabelas, listas, blocos de código, parágrafos; fórmulas podem ficar como texto `$$...$$`, como já estão).

## O que NÃO fazer
- Não apagar conteúdo correto que já existe (padrões de projeto, UML, requisitos antigos), só atualizar o que mudou.
- Não inventar números além dos listados. Não rodar comandos nem fazer commit.

## Critério de pronto
GDD (md e html) descreve todas as novidades acima com o mesmo estilo; RF-22 a RF-31 presentes.
