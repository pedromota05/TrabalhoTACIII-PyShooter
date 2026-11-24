# Plano — próximos passos do PyShooter (escrito em 2026-11-21)

Para a próxima conversa. Repositório: `C:\projetos_disco_C\faculdade\TrabalhoTACIII-PyShooter`, branch `melhorias-coop` (último commit enviado: `eee7afb`). Leia antes `_CONTEXTO/LEIA-ME.md`, o "Resumo" de `_CONTEXTO/DIARIO.md` e `_CONTEXTO/PENDENCIAS.md`. 

Forma de trabalho combinada com o Guilherme:
- Delegar ao Gemini (MCP `ponte-agy`, `delegar_tarefa`) tudo o que der, com roteiro em `docs/tarefas/AAAA-MM-DD_fase-N_*.md` (Objetivo, Já feito, Arquivos permitidos, Passos, O que NÃO fazer, Verificação, Critério de pronto). O Gemini só edita arquivos: testes, git e downloads ficam com o Claude. Revisar sempre o `git diff` (já apagou um bloco de fase sem pedir).
- Commits sem linha Co-Authored-By. Commit e push só quando o Guilherme pedir.
- Validar com `python tools/bot_fases.py todas`, `python tools/bot_fases.py --desafio --god`, `python tools/bot_fases.py todas --humano 3` (jogabilidade) e `python tools/teste_multiplayer.py --porta 56xx`. Os itens 2/3 do teste multiplayer oscilam quando o PC está carregado (também no commit antigo).
- Apresentação do T2: 2026-11-24.

## Estado no momento em que este plano foi escrito
- `docs/GDD_Trabalho2.md` foi atualizado pelo Gemini (roteiro `docs/tarefas/2026-11-21_fase-15_gdd-novidades.md`), mas a tarefa foi interrompida: **não revisado e não commitado**; `docs/GDD_Trabalho2.html` e `.pdf` ainda são os antigos.pra gerar usar python pra economizar token.

## O que falta (em ordem sugerida)

### 1. Renascer no início da fase ou depois da bandeira (pedido em 2026-11-21) — Claude faz (pequeno)
- Regra nova: ao perder uma vida, o jogador volta **exatamente ao início da fase** ou **logo depois da última bandeira de checkpoint** que passou (não mais "posição segura" nem ao lado do parceiro).
- Onde: `core/gameplay.py` `respawn_after_life_lost` / `_revive_at` (hoje: parceiro vivo → ao lado dele; senão `game.safe_pos`; senão `respawn`). Guardar o início em `core/level_loader.py` `load_level` (ex.: `game.level_start = (player.rect.centerx + game.bg_scroll, player.rect.bottom)` logo depois de `game.world.process_data`). O checkpoint guarda `game.checkpoint = {'x': flag.world_x, 'y': flag.ground_y, ...}`.
- Multiplayer: hoje `checkpoints_enabled` (level_loader) desliga bandeiras em LAN. Decidir com o Guilherme se no multiplayer também volta à bandeira/início (ligar as bandeiras em LAN) ou se continua ao lado do parceiro. Desafio não tem vidas (sem mudança).
- Atualizar a regra em `_CONTEXTO/DECISOES.md` (citar a decisão de 2026-11-21 sobre vidas).

### 2. Bater com a arma, quebrar caixas de madeira, aranhas e vida extra — delegar ao Gemini
- Golpe corpo a corpo (sugestão: botão direito do mouse): animação girando a arma (usar `entities/aim_pose.py`, somando um ângulo de "balanço" ao `aim_angle` enquanto dura o golpe) + arco branco de efeito; dano em inimigos na frente.
- Caixa de madeira = tile 12 (sólido, em `world/level_builder.py`). Guardar as caixas numa lista própria do mundo para poder removê-las de `obstacle_list`. Quebra com golpe (e com granada, opcional), com partículas.
- Conteúdo sorteado de forma determinística pela posição (igual nos dois PCs): item (munição/granada/vida), às vezes **vida extra** (novo tipo de `ItemBox`, ícone de coração desenhado no código; soma 1 em `game.lives`, com limite) ou uma **aranha**.
- Aranha: inimigo novo desenhado no código (corpo + 8 pernas animadas), anda e pula no jogador, dano por contato, poucos pontos de vida; num grupo próprio (`game.spider_group`) para não entrar na sincronização dos inimigos do Host. Pontos/combo via `update_fun` (`config.KILL_POINTS`). -  deve ser adicionada aos assets e funcionar no editor
- Multiplayer: mensagem nova para caixa quebrada (`crate,fase,col,linha`) para remover a caixa nos dois PCs; vida extra pega pelo Cliente precisa ir ao Host (ex.: `lifeup`), que é a autoridade das vidas. Aranhas podem ser locais em cada PC (documentar).
- Atualizar instruções (`ui/screens/instructions.py`) com o novo controle.

### 2b. Fase 5 = arena de hordas do Desafio (pedido em 2026-11-21) — delegar ao Gemini depois do item 2
- Arena plana e fechada (mapa da 5 com o poço estreitado como na fase 4: água nas colunas 14-16, rampa na 17), sem os chefes no CSV.
- Ondas "ONDA N/M" com ~3 s de pausa; inimigos nascem pelas bordas, cada onda com mais inimigos e tipos variados (soldado, robô, esqueleto, sniper, aranha); a última traz o Demônio e o Dragão juntos. Caixas de munição/vida entre as ondas.
- Fase termina (Desafio vai à vitória) quando a última onda é vencida; HUD mostra a onda. Pontos/combo continuam (update_fun).
- Multiplayer: Host anuncia a onda; target_id das ondas determinísticos (iguais nos dois PCs). Testar com teste_multiplayer e bot (--desafio --god, --humano).

### 3. Tela cheia — Claude faz (pequeno)
- F11 alterna tela cheia (`pygame.display.set_mode(..., pygame.SCALED | pygame.FULLSCREEN)`), e uma opção na tela de Configurações (`ui/screens/options.py`) salva no progresso (`core/progress.py`).
- Cuidado: o editor troca a resolução para 1200x740 (`on_enter`/`on_exit` em `ui/screens/level_editor.py`); manter o modo tela cheia ao entrar e sair.

### 4. Músicas novas por fase — Claude faz (precisa da web e de permissão para baixar)
- O Guilherme acha a música atual chata. Procurar músicas livres (CC0 ou CC-BY, ex.: OpenGameArt) que combinem: fase 1 floresta, fase 2 pântano, fase 3 neve, fase 4 chefes, menu, e Desafio.
- Antes de baixar: mostrar ao Guilherme nome, fonte, licença e tamanho de cada uma e esperar o "pode baixar". Guardar em `audio/` e os créditos (autor, link, licença) num arquivo `audio/CREDITOS.md` e no GDD.
- Código: tocar a música da fase em `core/level_loader.py`/`game.py` (hoje `audio/music2.mp3` para tudo).
- A busca foi interrompida pelo Guilherme em 2026-11-21: confirmar se ainda quer antes de começar.

### 5. Documentação final — GDD e slides
- Revisar o diff do `docs/GDD_Trabalho2.md` feito pelo Gemini, completar com os itens 1-4 acima quando prontos, gerar `docs/GDD_Trabalho2.html` (mesmo `<head>`/`<style>`, Markdown → HTML com `python -m markdown` e extensão de tabelas) e o PDF (Edge headless: `msedge --headless --print-to-pdf=... docs/GDD_Trabalho2.html`).
- Slides: criar `docs/apresentacao/AAAA-MM-DD_slides-pyshooter_v3.pptx` a partir do `_v2` (não sobrescrever), com: mira no mouse e arma girando, dash, vidas e "-1 VIDA", Desafio em dupla, chefes em etapas, pontos/combo/drops, cor do boneco, editor (mover, desfazer/refazer, checkpoint e castelo), e o que entrar dos itens 1-4. Capturas novas em `docs/capturas/` (o bot tira com `--capturas PASTA`).
- Atualizar `docs/2026-11-19_guia-de-estudo-apresentacao.md` com as partes novas do código (aim_pose, effects, regras de vida).

### 6. Teste real com o Pedro (Radmin)
- Os dois com `git pull origin melhorias-coop`. Conferir o checklist `docs/checklist_teste_multiplayer.md` e as novidades (cor sem repetir, mira do parceiro, Desafio em dupla, chefes em etapas).

## Pendências antigas
- "Fase 2 não terminou" (2026-11-21): não reproduzido; aguarda o Guilherme descrever.
- Fase 3: o bot humano caiu 1 vez em 3 perto da coluna 100 (x 4000-4399); observar se humanos também caem.
