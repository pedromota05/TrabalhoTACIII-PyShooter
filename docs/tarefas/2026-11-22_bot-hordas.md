# 2026-11-22 — Bot jogar a Fase 5 (hordas) do Modo Desafio

## Objetivo
`python tools/bot_fases.py --desafio --god` hoje passa nas fases 1 a 4, mas na Fase 5 (arena de hordas, `core/horde.py`) estoura o tempo (900 s) porque o bot fica parado na onda 1. Ensinar o bot a caçar os inimigos das hordas até `game.horde_done` ficar True.

## Já feito (não refazer)
- O jogo está certo: a onda 1 nasce (3 `Enemy`) e as ondas avançam quando ninguém está vivo (`core/horde.py`, `update_horde`). NÃO mexer no jogo.
- Causa no bot (`tools/bot_fases.py`, classe `Bot`, método `tick`): a Fase 5 não tem saída (`saida_x is None`) e sem chefes vivos `_caminho_chefe` devolve `[PARADO]`; `_inimigo_a_frente` só olha para a frente (`p.direction`), então inimigos atrás (ex.: x=209 com o jogador em x=379) nunca levam tiro.

## Arquivos permitidos
- `tools/bot_fases.py`
- Qualquer outro: não tocar.

## Passos
1. Na classe `Bot`, criar o método `_alvos_vivos(self)` que devolve a lista de sprites vivos (`e.alive`) de `self.g.enemy_group`, `self.g.boss_group` e, se existir, `self.g.spider_group` (use `getattr(self.g, 'spider_group', ())`).
2. Criar `_modo_horda(self)` que devolve `bool(getattr(self.g, 'horde_active', False))`.
3. Em `_caminho_chefe`, quando `self._modo_horda()` for True, usar `self._alvos_vivos()` no lugar de `self._chefes_vivos()` para escolher o alvo mais próximo (o resto do método fica igual).
4. No fim de `tick`, no bloco `if saida_x is None and chefes:` (mira no chefe), fazer valer também no modo horda: quando `self._modo_horda()` for True, usar `alvos = self._alvos_vivos()` em vez de `chefes`. Com alvo, virar o jogador para ele (`direction`/`flip`, como já é feito) e atirar quando o alvo estiver na altura do tiro. A checagem de altura do chefe (`b.rect.top < centery - mira < b.rect.bottom`) serve; para alvos baixos (aranha), aceitar também `abs(b.rect.centery - g.player.rect.centery) < 40`.
5. Granada: manter a regra atual só para chefes (não jogar granada em inimigo comum).
6. Sem alvo vivo no modo horda (pausa entre ondas): ficar `PARADO` e `g.shoot = False`.
7. Atualizar o docstring do topo do arquivo: uma linha dizendo que no Desafio o bot caça os inimigos das hordas na Fase 5.

## O que NÃO fazer
- Não mexer em `core/`, `entities/`, `game.py`, `config.py` nem nos mapas.
- Não mudar o comportamento das fases 1 a 4 (com saída): todo código novo só age quando `_modo_horda()` é True, salvo o passo 3/4 que já depende de `saida_x is None`.
- Não rodar comandos, não fazer git.

## Verificação (o Claude roda)
- `python tools/bot_fases.py 1 2 3 4` → 4 fases "passou".
- `python tools/bot_fases.py --desafio --god` → `"resultado"` de vitória e fase 5 "passou", `"problemas": []`.

## Critério de pronto
As duas verificações acima passam; diff só em `tools/bot_fases.py`.
