# Checklist — teste manual do multiplayer em 2 PCs

Use este roteiro para testar o modo cooperativo em LAN com duas pessoas. Marque cada item com [x] e anote o que falhar.

## Antes de começar

- [ ] Os dois PCs estão na mesma rede (mesmo Wi-Fi ou cabo no mesmo roteador).
- [ ] Os dois têm a mesma versão do projeto (branch `trabalho-parte2`, mesmo commit: `git log --oneline -1`).
- [ ] Os dois têm Python e pygame-ce instalados (`python -m pip install pygame-ce Pillow`).
- [ ] No PC que vai ser o Host, descubra o IP: abra o PowerShell e rode `ipconfig`. Anote o "Endereço IPv4" (ex.: 192.168.0.15).
- [ ] Na primeira vez que o Host criar o servidor, o Firewall do Windows pode perguntar se o Python pode usar a rede. Marque **Redes privadas** e clique em **Permitir acesso**. Se a rede estiver como "Pública", o cliente não vai conseguir conectar.

## 1. Conexão

- [ ] PC 1 (Host): Menu → Multiplayer → **Criar Servidor**. O jogo começa na fase 1.
- [ ] PC 2 (Cliente): Menu → Multiplayer → digite o IP do Host → **Conectar**. O jogo começa na fase 1.
- [ ] Cada um vê o outro soldado com a etiqueta (P1/P2) e a barrinha de vida em cima.
- [ ] Ao andar e pular, o outro acompanha sem teleportes grandes.

## 2. Inimigos

- [ ] Os inimigos estão no mesmo lugar nas duas telas (diferença de poucos pixels é normal).
- [ ] O Cliente atira em um inimigo: a vida dele cai nas **duas** telas.
- [ ] Um inimigo morto pelo Cliente aparece morto também no Host (e o contrário).
- [ ] O inimigo morre com a quantidade normal de tiros (não com metade: isso indicaria dano em dobro).
- [ ] Os tiros dos inimigos (balas, flechas, robôs) aparecem na tela do Cliente.
- [ ] Um tiro do parceiro **não** tira vida de você (sem fogo amigo).

## 3. Morte de um jogador

- [ ] Deixe o Cliente morrer. O Host continua jogando normalmente.
- [ ] Espere mais de 5 segundos na tela de Game Over do Cliente: o Host continua vendo o soldado do Cliente caído (não some).
- [ ] O Cliente clica em **Restart**: renasce ao lado do Host, na mesma fase, com os inimigos já mortos continuando mortos.
- [ ] Repita com o Host morrendo: o Cliente continua jogando e os inimigos continuam se mexendo na tela do Cliente.

## 4. Troca de fase

- [ ] O Host chega à placa de saída: os **dois** vão para a fase 2 ao mesmo tempo.
- [ ] Na fase 2, o Cliente chega à saída primeiro: os **dois** vão para a fase 3 (o Cliente pede ao Host).
- [ ] Se um dos dois estiver na tela de Game Over quando o outro trocar de fase, ele renasce na fase nova.
- [ ] Na fase nova, os inimigos aparecem no lugar certo nas duas telas (sem inimigos "mortos" herdados da fase anterior).

## 5. Vitória

- [ ] Na fase 4, matem os dois chefes. Cerca de 1,5 s depois, a tela **VITÓRIA!** aparece nas **duas** telas.
- [ ] O botão de voltar ao menu funciona nos dois PCs e o multiplayer é encerrado.

## 6. Saída e reconexão

- [ ] O Cliente sai pela Pausa → Sair: o Host continua jogando e, em até 5 s, o soldado do Cliente some.
- [ ] O Cliente consegue conectar de novo na mesma partida e cai na fase em que o Host está.
- [ ] Fechar o jogo do Host e abrir de novo: **Criar Servidor** funciona (a porta 5555 foi liberada).

## Resultado

| Data | Host (PC/IP) | Cliente (PC/IP) | Itens com falha | Observações |
|---|---|---|---|---|
|  |  |  |  |  |

Teste automático no mesmo PC (sem rede externa): `python tools/teste_multiplayer.py` (veja o cabeçalho do arquivo para as opções).
