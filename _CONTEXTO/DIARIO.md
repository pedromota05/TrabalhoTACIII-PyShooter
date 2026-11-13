# Diário — PyShooter

## Resumo
- Implementado suporte multiplayer LAN UDP completo (Host e Cliente).
- Corrigida a sincronização de dano e morte de inimigos em rede (pacotes `hit` e `target_id`).
- Demanda aberta no Trilho para finalizar bateria de testes e correções até sábado (2026-11-14).

---

### 2026-11-12 — Sincronização de Inimigos no Multiplayer e Integração ao Trilho
- Identificado descompasso visual onde inimigos morriam na tela do atirador mas continuavam vivos na tela do outro jogador.
- Implementado sistema determinístico de IDs para inimigos e chefes em `core/level_loader.py`.
- Criado pacote UDP `hit` em `network/protocol.py` e fila thread-safe em `network/client.py`.
- Integrada transmissão de acertos em `entities/combat/projectiles.py` e consumo em `core/gameplay.py`.
- Alterações commitadas e enviadas ao repositório remoto GitHub (`trabalho-parte2`).
- Projeto vinculado ao Trilho com demanda registrada para sábado.
