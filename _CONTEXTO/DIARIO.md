# Diário — PyShooter

## Resumo
- Implementado suporte multiplayer LAN UDP completo (Host e Cliente).
- Corrigida a sincronização de dano e morte de inimigos em rede (pacotes `hit` e `target_id`).
- Demanda aberta no Trilho para finalizar bateria de testes e correções até sábado (2026-11-14).
- 2026-11-18: fases 1 a 4 testadas por bot automático (modo solo, dano real). Fases 1, 2 e 3 concluídas; na fase 4 os dois chefes foram mortos, mas o jogo não tem saída nem tela de vitória.
- Problemas abertos: fase 4 sem condição de vitória; fase 5 inacessível (MAX_LEVELS = 4); fim da campanha volta para a fase 3; fase 4 sem munição extra.
- 2026-11-18: aprovado o plano de melhorias (C:\Users\guilh\.claude\plans\agile-purring-stonebraker.md): campanha com 4 fases e vitória ao matar os chefes da fase 4, progresso no menu de fases, checkpoints, edição dos mapas, Modo Desafio (maratona 1→5 com 1 vida) e, por último, teste do multiplayer.
- Etapa 1 concluída (2026-11-18): bot em tools/bot_fases.py; corrigido bug de câmera ao trocar de fase (core/level_loader.py zera screen_scroll e bg_scroll). Fases 1→2→3 passam em sequência; na fase 4 o Dragão às vezes mata o bot (balanceamento fica para a etapa 5).
- Próximos passos: seguir o plano a partir da etapa 2; depois atualizar o GDD e preparar a apresentação da aula (semana de 2026-11-23).

---

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
