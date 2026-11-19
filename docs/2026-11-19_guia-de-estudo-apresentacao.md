# Guia de estudo do PyShooter (para a apresentação de 2026-11-24)

Este guia é para o Guilherme e o Pedro **entenderem o próprio código** antes da apresentação final do Trabalho 2, em 2026-11-24. Muita coisa foi escrita com ajuda de IA. O professor vai perguntar "como isso funciona?", e a resposta precisa sair da cabeça de vocês, não do slide.

**Como usar (cerca de 1 h 30):**

1. Leia as seções 1 a 3 (15 min). Elas dão a visão geral.
2. Abra o jogo e jogue uma fase enquanto lê a seção 4 (20 min).
3. Leia a seção 5 (multiplayer) com os arquivos abertos ao lado. É a parte que o professor mais vai cobrar (30 min).
4. Leia as seções 6 a 8 e tente responder às perguntas da seção 9 **sem olhar** as respostas (25 min).

Os caminhos entre colchetes são clicáveis. O número depois de `:` é a linha do arquivo, conferida em 2026-11-19.

---

## 1. O projeto em 1 minuto (dá para falar assim na abertura)

> "O PyShooter é um jogo de tiro em plataforma 2D, com rolagem lateral, feito em Python com pygame. O jogador atravessa quatro fases (floresta, neve, montanha e pântano), enfrenta soldados, snipers, robôs e esqueletos e, no fim, dois chefes: um demônio e um dragão.
> No Trabalho 2 nós acrescentamos o que foi pedido: menus completos, um editor de fases que grava as fases em CSV, multiplayer cooperativo em rede local usando UDP e threads, e os padrões de projeto documentados no GDD. Também colocamos checkpoints, progresso salvo e um Modo Desafio com recorde de tempo."

---

## 2. O que o professor pediu e onde está cada coisa

Enunciado em [docs/T2.pdf](T2.pdf): atualizar o GDD com os itens abaixo e apresentar em 2026-11-24.

| Pedido no T2 | Onde está no código | Onde está no GDD |
| :--- | :--- | :--- |
| Editor de fases | [ui/screens/level_editor.py](../ui/screens/level_editor.py) (gravar: linha 154, ler: linha 171) | Seção 1.6 |
| Multiplayer cliente/servidor em LAN | [network/server.py](../network/server.py), [network/client.py](../network/client.py), [network/protocol.py](../network/protocol.py) | Seção 1.7 |
| Padrões de projeto | Espalhados (tabela na seção 6 deste guia) | Seção 1.8 |
| Diagramas atualizados | [docs/uml/classes.puml](uml/classes.puml), [docs/uml/pacotes.puml](uml/pacotes.puml) | Seção 2 |
| Menus | [ui/screens/](../ui/screens/) (uma classe por tela) | Seção 1.5 |

O GDD completo está em [docs/GDD_Trabalho2.md](GDD_Trabalho2.md), e o PDF entregue em `docs/GDD_Trabalho2.pdf`.

**Quem fez o quê (pelo histórico do git):**

- **Pedro:** o jogo base em setembro de 2026, com as fases, os inimigos, os chefes, as artes, os sons, o menu de pausa e as opções de áudio.
- **Guilherme:** a refatoração em módulos (setembro) e, em novembro, o Trabalho 2, com multiplayer, editor integrado, menus, UML, GDD, checkpoints, Modo Desafio e os testes automáticos.

Cada um deve conseguir explicar as partes que o outro fez. O professor pode perguntar qualquer coisa a qualquer um.

---

## 3. Mapa das pastas (o que cada uma faz)

```
main.py              só chama game.main()
game.py              classe Game: guarda o estado e roda o loop principal
game_state.py        enum GameState (MENU, PLAYING, PAUSE, ...)
config.py            TODAS as constantes (tela, física, dano, velocidades)
asset_manager.py     carrega imagens e sons uma vez só (Singleton)
core/                o "motor": gameplay, desenho, teclado, carregamento de fase, save
entities/            tudo que aparece na tela: jogador, inimigos, chefes, balas, caixas
world/               level_builder.py: transforma o CSV em objetos do jogo
network/             servidor UDP, cliente UDP e formato das mensagens
ui/screens/          uma classe por tela (menu, pausa, game over, vitória, editor...)
levels/              level1_data.csv ... level5_data.csv (as fases)
tools/               bot que joga sozinho e teste automático do multiplayer
```

Se o professor perguntar "por onde o jogo começa?": [main.py](../main.py) chama `main()` em [game.py:324](../game.py:324), que cria um `Game` e chama `run()`.

---

## 4. Como o jogo funciona por dentro

### 4.1 O loop principal (o coração do jogo)

Arquivo: [game.py:279](../game.py:279), método `run()`.

O jogo roda a **60 quadros por segundo**. Em cada quadro ele faz sempre as mesmas 4 coisas:

1. `self.clock.tick(FPS)` espera o tempo certo para não passar de 60 fps.
2. Olha o estado atual (`self.state`) e chama a tela correspondente. Se é `MENU`, desenha o menu; se é `PLAYING`, roda um quadro de jogo.
3. `_handle_events()` lê teclado e mouse ([core/input_handler.py](../core/input_handler.py)).
4. `pygame.display.update()` mostra o quadro desenhado.

**Frase para a apresentação:** "Todo jogo é um laço: ler a entrada, atualizar o mundo e desenhar. O nosso faz isso 60 vezes por segundo, e o que acontece em cada volta depende do estado em que o jogo está."

### 4.2 Máquina de estados

Arquivo: [game_state.py](../game_state.py). Os estados são: `MENU`, `INSTRUCTIONS`, `LEVEL_SELECT`, `PLAYING`, `PAUSE`, `OPTIONS`, `GAME_OVER`, `LEVEL_TRANSITION`, `VICTORY`, `MULTIPLAYER_MENU` e `EDITOR`.

Trocar de tela é só mudar a variável: `game.state = GameState.PAUSE`. No próximo quadro, o loop chama a tela de pausa. Cada tela é uma classe em `ui/screens/` com um método `update(screen, game)`.

Exemplo real: apertar ESC durante o jogo, em [core/input_handler.py:38](../core/input_handler.py:38):

```python
elif game.state == GameState.PLAYING:
    game.state = GameState.PAUSE
```

### 4.3 Como uma fase é montada (CSV → objetos)

- Uma fase é uma **tabela de números** com 16 linhas e 200 colunas, salva em `levels/levelN_data.csv`.
- Cada número é um tipo de bloco (tile) de 40 × 40 pixels. A tela tem 640 px de altura, e 640 / 16 = 40. (O comentário em `config.py` diz 37, mas o valor calculado é 40.)
- `-1` é vazio, `0` a `8` é chão, `15` é onde o jogador nasce, `16` é um soldado inimigo, `17` a `19` são caixas (munição, granada, vida), `20` é a saída, `86` é o chefe Demônio e `87` é o Dragão.

O carregamento acontece em duas etapas:

1. [core/level_loader.py:35](../core/level_loader.py:35), `load_level`, lê o CSV para uma matriz `world_data[linha][coluna]`.
2. [world/level_builder.py:23](../world/level_builder.py:23), `World.process_data`, percorre a matriz e **cria o objeto certo para cada número**. Por exemplo, o número 16 vira `Enemy(x * TILE_SIZE, y * TILE_SIZE)`.

Esse é o padrão **Factory Method** (seção 6). O editor de fases só altera esse CSV; por isso uma fase feita no editor funciona no jogo sem mudar nenhum código.

Logo depois de criar os inimigos, cada um ganha um número fixo, o `target_id` ([core/level_loader.py:73](../core/level_loader.py:73)). Ele é essencial para o multiplayer (seção 5).

### 4.4 A câmera: o jogador quase não anda, o mundo é que anda

Esse é um conceito que confunde e que vale entender bem, porque o multiplayer depende dele.

Arquivo: [entities/player.py:116](../entities/player.py:116).

- Quando o jogador chega perto da borda da tela (a menos de `SCROLL_THRESH = 200` px), ele **para de andar na tela** e o **mundo inteiro é empurrado** na direção contrária.
- `screen_scroll` é quanto o mundo andou **neste quadro**. Todo objeto soma esse valor no próprio `x` (repare em `rect.x += screen_scroll` em vários `update`).
- `bg_scroll` é quanto a câmera andou **desde o começo da fase**. É o total acumulado.

Daí sai a conta mais importante do projeto:

```
posição no MUNDO = posição na TELA + bg_scroll
posição na TELA  = posição no MUNDO − bg_scroll
```

**Por que importa:** cada computador tem a sua câmera. Se o jogo mandasse a posição *na tela*, o outro jogador apareceria no lugar errado. Por isso o multiplayer **sempre manda a posição no mundo** ([core/gameplay.py:402](../core/gameplay.py:402)), e quem recebe converte para a própria tela ([entities/remote_player.py:79](../entities/remote_player.py:79)).

O fundo usa **paralaxe** ([core/renderer.py:6](../core/renderer.py:6)): o céu anda a 50% da velocidade, a montanha a 60% e os pinheiros a 70% e 80%. Camadas mais distantes andam mais devagar, o que dá a sensação de profundidade.

### 4.5 Física: gravidade e colisão

Arquivo: [entities/base.py](../entities/base.py), classe `Character` (base do jogador e dos inimigos).

**Gravidade** ([entities/base.py:83](../entities/base.py:83)):

```python
self.vel_y += GRAVITY          # 0.75 a cada quadro
if self.vel_y > TERMINAL_VELOCITY:
    self.vel_y = TERMINAL_VELOCITY   # nunca cai mais rápido que 10 px/quadro
```

O pulo põe `vel_y = -14` (negativo é para cima, porque no pygame o y cresce para baixo). A gravidade vai somando 0,75 até a velocidade virar positiva e o boneco começar a cair.

**Colisão** ([entities/base.py:89](../entities/base.py:89)), em duas etapas:

1. Calcula quanto o boneco **quer** andar (`dx`, `dy`).
2. Testa se o retângulo **na posição futura** bate em algum bloco sólido, separando horizontal e vertical.
   - Se bater de lado, `dx = 0`: o boneco não atravessa a parede.
   - Se bater caindo, encosta no topo do bloco e `in_air = False`: ele pode pular de novo.
   - Se bater subindo, encosta na base do bloco: bateu a cabeça.

Isso se chama colisão **AABB** (retângulos alinhados aos eixos), feita com `colliderect` do pygame. A hitbox horizontal é 20% mais fina de cada lado para a ponta da arma não prender na parede.

A água e cair para fora da tela zeram a vida ([entities/base.py:133](../entities/base.py:133)).

### 4.6 Inteligência dos inimigos

Arquivo: [entities/enemies/standard.py:70](../entities/enemies/standard.py:70), método `ai`.

O soldado comum é uma **máquina de estados simples**:

- **Patrulha:** anda para um lado. Vira quando bate na parede, quando vai cair de uma borda (`_is_edge_ahead` testa se há chão à frente) ou depois de andar 3 blocos.
- **Parado:** às vezes, com chance de 1 em 200 por quadro, para por 50 quadros. Isso o deixa menos robótico.
- **Ataque:** ele tem um **retângulo de visão** de 150 × 20 px à frente. Se o jogador entra nele ([standard.py:84](../entities/enemies/standard.py:84)), o soldado vira para o jogador e atira.

Sniper, robô e esqueleto medem a **distância real** até o jogador com `math.hypot` (distância euclidiana) para decidir quando atirar ([robot.py:104](../entities/enemies/robot.py:104), [skeleton.py:127](../entities/enemies/skeleton.py:127)). A flecha do esqueleto e o fogo do dragão miram com `atan2` ([projectiles.py:356](../entities/combat/projectiles.py:356)).

No multiplayer, cada inimigo persegue o **jogador vivo mais próximo**, seja ele local ou remoto ([core/gameplay.py:115](../core/gameplay.py:115)).

### 4.7 Combate

Os números ficam todos em [config.py](../config.py):

- **Tiro:** a bala anda 10 px por quadro. Tira 25 de vida do inimigo e 5 do jogador. Depois de cada tiro há uma espera de 20 quadros (`SHOOT_COOLDOWN`), cerca de 3 tiros por segundo.
- **Granada:** sai com velocidade vertical de −11 e horizontal de 7, e a gravidade faz a parábola. Se bate numa parede, inverte a direção ([projectiles.py:174](../entities/combat/projectiles.py:174)). Explode depois de 100 quadros (cerca de 1,7 s) e tira 50 de vida de quem estiver a até 2 blocos.
- **Invencibilidade:** depois de levar um tiro, o jogador fica 60 quadros (1 s) sem tomar dano, para não perder toda a vida de uma vez.

### 4.8 Checkpoints, progresso salvo e Modo Desafio

- **Checkpoints** ([core/gameplay.py:94](../core/gameplay.py:94)): bandeiras nas fases 1 a 3 (colunas em `config.CHECKPOINTS`). Ao passar por uma, o jogo guarda posição, munição, granadas e **quais inimigos já morreram** (pelo `target_id`). O Restart recarrega a fase, remove esses inimigos e põe o jogador na bandeira ([core/level_loader.py:108](../core/level_loader.py:108)).
- **Progresso salvo** ([core/progress.py](../core/progress.py)): um arquivo `save/progresso.json` com as fases concluídas, se a campanha foi zerada e o recorde do Desafio. Se o arquivo estiver corrompido, o jogo continua com o progresso vazio em vez de travar.
- **Modo Desafio** ([game.py:202](../game.py:202) e [core/gameplay.py:426](../core/gameplay.py:426)): fases 1 a 5 seguidas com uma vida só e sem checkpoints. Vida, munição e granadas passam de uma fase para a outra. O tempo é contado em quadros (`run_frames / 60` = segundos) e o melhor tempo vira recorde.

---

## 5. Multiplayer em LAN (a parte mais importante para estudar)

### 5.1 A ideia geral em 3 frases

1. Um jogador clica em **Criar Servidor**. O jogo dele abre um **servidor UDP na porta 5555** e também se conecta a esse servidor como cliente. Esse jogador é o **Host (P1)**.
2. O outro clica em **Conectar** e digita o IP do Host. Ele vira o **Cliente (P2)**.
3. O servidor é só um **repetidor**: tudo que chega de um jogador ele reenvia para os outros.

```
   PC do Host                                    PC do Cliente
 ┌───────────────────────────┐                ┌──────────────────┐
 │ Jogo (P1) ── NetworkClient│                │ Jogo (P2)        │
 │                 │         │                │    │             │
 │                 ▼         │     UDP        │    ▼             │
 │          GameServer :5555 │◄──────────────►│ NetworkClient    │
 └───────────────────────────┘                └──────────────────┘
```

Código: `start_multiplayer_host` em [game.py:218](../game.py:218) e `start_multiplayer_client` em [game.py:242](../game.py:242).

### 5.2 Por que UDP e não TCP?

- **TCP** garante que tudo chega, e na ordem. Para isso, quando um pacote se perde, ele **segura os seguintes** até reenviar o perdido. Num jogo, isso causa travadinhas.
- **UDP** manda e esquece. Se a posição do quadro 100 se perde, não tem problema: a do quadro 101 chega logo depois e é mais nova.
- Como mandamos a posição **60 vezes por segundo**, perder uma de vez em quando nem aparece.
- O que **não pode** se perder, como "mudou de fase", nós **repetimos** a cada 0,5 s (seção 5.8).

### 5.3 Por que threads?

`recvfrom()` (receber um pacote) **bloqueia**: o programa fica parado esperando chegar algo. Se isso rodasse no loop do jogo, a tela congelaria até chegar um pacote.

A solução é uma **thread** (uma linha de execução paralela) só para escutar a rede:

- **Servidor** ([network/server.py:59](../network/server.py:59)): `_run_loop` roda numa thread `daemon`, que morre junto com o jogo.
- **Cliente** ([network/client.py:83](../network/client.py:83)): `_receive_loop` também roda numa thread e guarda o que chega em dicionários.
- O loop do jogo **lê** esses dicionários a cada quadro.

Como duas threads mexem nos mesmos dicionários, usamos um **`threading.Lock()`**. É um cadeado: só uma thread por vez entra no trecho `with self.lock:`. Sem isso, o jogo poderia ler um dado pela metade enquanto a thread de rede escreve.

Os sockets têm `settimeout(1.0)`: o `recvfrom` desiste depois de 1 s sem pacote. Assim a thread confere de tempos em tempos se `self.running` ainda é verdadeiro e consegue terminar quando o jogador sai da partida.

Tudo isso segue os exemplos do professor (`tac3/exemplos/threads/`), como está comentado no topo dos arquivos.

### 5.4 O formato das mensagens

Arquivo: [network/protocol.py](../network/protocol.py). São textos curtos separados por vírgula, sempre começando por quem mandou.

| Mensagem | Exemplo | Quem manda |
| :--- | :--- | :--- |
| estado do jogador | `P2 (Cliente),1520.5,410.0,1,1,0,90` (x, y, animação, direção, atirando, vida) | cada jogador, todo quadro |
| `hit` | `P2 (Cliente),hit,7,25` (acertou o inimigo 7 com 25 de dano) | quem acertou |
| `enemies` | lote com todos os inimigos (posição, animação, vida, vivo) e a fase | Host |
| `eshoot` | um inimigo atirou (tipo, posição, direção) | Host |
| `level` | `P1 (Host),level,2,0` (estamos na fase 2, sem vitória) | Host, a cada 0,5 s |
| `levelreq` | `P2 (Cliente),levelreq,2` (cheguei na saída da fase 2) | Cliente |
| `quit` / `remove` | saiu por vontade própria / caiu por inatividade | jogador / servidor |

Quem recebe usa `parse_packet` para transformar o texto num dicionário.

### 5.5 O que acontece em um quadro

**No Host** ([core/gameplay.py:241](../core/gameplay.py:241) em diante):

1. Aplica os `hit` que chegaram do cliente na vida dos inimigos.
2. Roda a IA e a física de **todos** os inimigos.
3. Manda o lote `enemies` com a situação de cada inimigo.
4. Manda a própria posição.

**No Cliente** ([core/gameplay.py:154](../core/gameplay.py:154) em diante):

1. **Não roda a IA dos inimigos.** Só copia o que o Host mandou: posição, animação, vida e se está vivo.
2. Cria na tela os tiros de inimigo que o Host avisou (`eshoot`).
3. Manda a própria posição e, quando acerta alguém, um `hit`.

Por que só o Host decide? Se os dois rodassem a IA, cada inimigo faria coisas diferentes em cada tela (a IA usa números aleatórios). Com um único dono, as duas telas mostram o mesmo. Isso se chama **Host autoritativo**.

### 5.6 Como os dois sabem que é o mesmo inimigo? (`target_id`)

Os dois computadores carregam o **mesmo CSV**, na mesma ordem, então criam os inimigos na mesma ordem. Logo depois, cada inimigo recebe um número sequencial ([core/level_loader.py:73](../core/level_loader.py:73)): o primeiro soldado é 0, o segundo é 1, e assim por diante. "O inimigo 7" é o mesmo nos dois lados, sem precisar mandar nada para combinar.

Os números recomeçam em cada fase. Por isso o lote `enemies` também leva a fase, e o cliente **ignora lotes de outra fase** ([core/gameplay.py:186](../core/gameplay.py:186)).

### 5.7 LERP: por que o parceiro não "teleporta"

Os pacotes não chegam certinhos a cada 1/60 s: às vezes chegam dois juntos, às vezes atrasa um. Se o parceiro fosse desenhado exatamente na última posição recebida, ele daria pulinhos.

A solução é a **interpolação linear** ([network/client.py:310](../network/client.py:310)), com fator 0,20:

```
atual = atual + (alvo − atual) × 0,20
```

A cada quadro, o boneco anda **20% do que falta** até a posição recebida. Exemplo com o parceiro em x = 100 e um pacote dizendo x = 200:

| Quadro | Falta | Anda (20%) | Nova posição |
| :---: | :---: | :---: | :---: |
| 1 | 100 | 20 | 120 |
| 2 | 80 | 16 | 136 |
| 3 | 64 | 12,8 | 148,8 |
| 4 | 51,2 | 10,2 | 159,0 |

Ele chega rápido no começo e vai desacelerando, o que parece natural. O custo é um pequeno atraso visual. Os inimigos no cliente usam a mesma conta, mas se a diferença passar de 200 px (por exemplo, quando a fase começa) eles pulam direto para o lugar certo ([network/client.py:286](../network/client.py:286)).

### 5.8 Heartbeat, timeout e troca de fase

- **Heartbeat / timeout** ([network/server.py:112](../network/server.py:112)): o servidor anota quando ouviu cada jogador pela última vez. Quem fica **5 s calado** é removido, e os outros recebem `remove`. É assim que o jogo percebe que alguém fechou o jogo ou caiu da rede, já que UDP não tem "conexão" para fechar.
- **Jogador morto continua mandando sinal** ([core/gameplay.py:145](../core/gameplay.py:145)). Antes, quem morria parava de mandar posição e era removido em 5 s. Corrigido.
- **Troca de fase sincronizada** ([core/gameplay.py:20](../core/gameplay.py:20)): o **Host decide** a fase.
  - O Host anuncia `level` a cada 30 quadros (0,5 s). Se o anúncio se perder, o próximo chega.
  - Quando o **cliente** chega à saída, ele **não troca sozinho**: manda `levelreq`, o Host troca e anuncia, e o cliente obedece.
  - Quando o **Host** chega à saída, ele troca e anuncia na hora.
- **Renascer no multiplayer** ([core/gameplay.py:56](../core/gameplay.py:56)): o Restart põe o jogador ao lado do parceiro, sem recarregar a fase, com 2 s de invencibilidade.

### 5.9 Problemas que encontramos e como corrigimos (bom para contar)

| Problema | Causa | Correção |
| :--- | :--- | :--- |
| Dano em dobro | A bala do parceiro tirava vida no Host **e** o `hit` tirava de novo | Bala de jogador remoto é só visual: `Bullet(visual_only=True)` ([projectiles.py:73](../entities/combat/projectiles.py:73)) |
| Jogador morto sumia | Na tela de Game Over ele parava de mandar pacotes e caía por timeout | Continua mandando um sinal com vida 0 |
| Fases desencontradas | Cada lado trocava de fase sozinho | O Host decide (`level` e `levelreq`) |
| Câmera errada ao trocar de fase | O deslocamento do último quadro empurrava o mundo novo | `load_level` zera `screen_scroll` e `bg_scroll` |

---

## 6. Padrões de projeto (o que dizer de cada um)

| Padrão | Onde | Explicação em 1 frase |
| :--- | :--- | :--- |
| **Singleton** | `AssetManager`, [asset_manager.py:19](../asset_manager.py:19) | Só existe **uma** instância: o `__new__` devolve sempre o mesmo objeto, então cada imagem e som é carregado do disco uma única vez. |
| **State** | `GameState` + classes em `ui/screens/` | O comportamento do loop muda conforme o estado, e cada estado tem sua classe com `update()`. |
| **Factory Method** | `World.process_data`, [world/level_builder.py:23](../world/level_builder.py:23) | Recebe um número do CSV e decide qual classe criar (16 → `Enemy`, 86 → `Boss`...). |
| **Facade** | classe `Game`, [game.py:52](../game.py:52) | O `Game` oferece métodos simples (`_update_playing`, `_load_level`) e delega o trabalho aos módulos de `core/`. |
| **Observer (orientado a eventos)** | fila de eventos do pygame e thread de rede | Teclado, mouse e pacotes chegam como eventos e são despachados para quem trata, sem travar o jogo. |
| **Proxy (remoto)** | `RemotePlayer`, [entities/remote_player.py](../entities/remote_player.py) | É um "representante" local do jogador do outro PC: parece um sprite comum, mas os dados vêm da rede. |

**Como o Singleton funciona por dentro:**

```python
_instance = None
def __new__(cls):
    if cls._instance is None:          # primeira vez: cria
        cls._instance = super().__new__(cls)
        cls._instance._initialized = False
    return cls._instance               # outras vezes: devolve o mesmo
```

O `_initialized` evita que o `__init__` rode de novo e apague o cache. Qualquer arquivo pode chamar `AssetManager()` e recebe o mesmo objeto.

**Cuidado se o professor apertar:**

- **Observer:** não temos a forma "clássica" do livro, com uma lista de observadores e `subscribe`/`notify`. O que temos é um modelo orientado a eventos. Se ele perguntar, diga isso com honestidade: "a ideia é a mesma, quem produz o evento não conhece quem trata, mas não implementamos a interface clássica".
- **Proxy:** o `RemotePlayer` não repassa chamadas para o objeto real no outro PC. Ele espelha o estado recebido. É um proxy no sentido de "representante local".

---

## 7. As ferramentas de teste (diferencial para mencionar)

- **Bot que joga sozinho** ([tools/bot_fases.py](../tools/bot_fases.py)): roda o jogo **sem janela** e decide as teclas a cada quadro.
  - Para achar o caminho até a saída, usa o algoritmo **A\*** ([tools/bot_fases.py:100](../tools/bot_fases.py:100)), testando ações como "andar à direita", "pular" e "pular para a direita".
  - Cada ação é simulada com **a mesma física do jogo**, então o caminho encontrado funciona de verdade.
  - A heurística é a distância em x até a saída.
  - O modo `--humano` coloca erros aleatórios no controle, para ver onde uma pessoa morreria. Foi assim que escolhemos onde pôr os checkpoints.
- **Teste automático do multiplayer** ([tools/teste_multiplayer.py](../tools/teste_multiplayer.py)): abre **dois processos** do jogo no mesmo PC, um Host e um Cliente, cada um jogado pelo bot. No fim, compara os registros e confere 7 itens:
  1. os dois se veem;
  2. os inimigos estão na mesma posição;
  3. o tiro do cliente tira vida no Host;
  4. o inimigo morto aparece morto nos dois lados;
  5. os tiros dos inimigos aparecem no cliente;
  6. a morte de um jogador não derruba o outro;
  7. a troca de fase e a vitória acontecem nos dois lados.
- **Checklist manual com 2 PCs:** [docs/checklist_teste_multiplayer.md](checklist_teste_multiplayer.md).

---

## 8. Limitações (melhor vocês falarem antes que perguntem)

- Funciona só em **rede local**. Pela internet precisaria de redirecionamento de porta, e o atraso maior apareceria.
- **Sem predição:** o cliente vê os inimigos com um pequeno atraso (o do LERP mais o da rede). Jogos comerciais "adivinham" o movimento para esconder isso.
- O Host manda pacotes **todo quadro** (60 por segundo). Em LAN tudo bem; na internet seria preciso mandar menos vezes.
- O protocolo é texto simples, **sem criptografia nem verificação**. Qualquer um na rede poderia mandar pacotes falsos. Para um jogo de LAN de trabalho acadêmico é aceitável.
- Se o Host sair, a partida acaba para todos, porque o servidor está no PC dele.

---

## 9. Perguntas que o professor pode fazer (tente responder antes de ler)

1. **Por que UDP?**
   Menor atraso. Um pacote de posição perdido é substituído pelo próximo, e o TCP seguraria os seguintes esperando o reenvio.
2. **O que acontece se um pacote se perder?**
   Para posição, nada perceptível, porque chega outro em 1/60 s. Para a troca de fase, o Host repete o anúncio a cada 0,5 s e o cliente repete o pedido.
3. **Para que serve o Lock?**
   A thread de rede escreve nos dicionários enquanto o loop do jogo lê. O Lock garante que só uma das duas mexe por vez.
4. **Por que a thread é `daemon`?**
   Para ela terminar sozinha quando o programa fecha, sem prender o processo aberto.
5. **Quem decide se um inimigo morreu?**
   O Host. O cliente manda `hit` e o Host aplica o dano e devolve o estado no lote `enemies`.
6. **Como os dois PCs sabem qual inimigo é qual?**
   Pelo `target_id`, um número dado na ordem de criação. Como os dois leem o mesmo CSV, a ordem é igual.
7. **Por que mandar posição no mundo e não na tela?**
   Cada PC tem sua câmera (`bg_scroll`). Na tela, a mesma posição seria diferente em cada um.
8. **O que é LERP e por que 0,2?**
   Andar uma fração do caminho até o alvo a cada quadro. 0,2 é um meio-termo: um valor menor deixa mais suave e mais atrasado, um maior deixa mais preciso e mais tremido.
9. **Como o servidor percebe que alguém saiu?**
   Pelo `quit`, se a pessoa saiu pelo menu, ou por timeout de 5 s sem pacotes, se o jogo fechou ou a rede caiu.
10. **Como funciona a gravidade?**
    A cada quadro, `vel_y += 0.75`, com limite de 10. O pulo começa em −14.
11. **Como a fase é carregada?**
    Lê o CSV numa matriz 16 × 200 e `World.process_data` cria um objeto para cada número (Factory Method).
12. **Onde está o Singleton e o que ele resolve?**
    No `AssetManager`. Evita carregar a mesma imagem várias vezes, economizando memória e tempo.
13. **Como funciona a câmera?**
    Quando o jogador chega a 200 px da borda, o mundo é que se move. `bg_scroll` guarda o deslocamento total.
14. **Como o inimigo "vê" o jogador?**
    O soldado tem um retângulo de 150 × 20 px à frente e atira se o jogador estiver dentro. Sniper, robô e esqueleto usam a distância euclidiana (`math.hypot`).
15. **Como vocês testaram o multiplayer?**
    Com o teste automático de dois processos, que confere 7 itens, e com o checklist em 2 PCs.

---

## 10. Glossário rápido

- **Quadro (frame):** uma volta do loop; o jogo faz 60 por segundo.
- **Sprite:** objeto desenhável do pygame, com imagem e retângulo (`rect`).
- **Tile:** bloco de 40 × 40 px da fase.
- **Host:** quem criou a partida; roda o servidor e a IA dos inimigos.
- **Socket:** a "porta" do programa para mandar e receber dados pela rede.
- **Thread:** um trecho de código rodando em paralelo dentro do mesmo programa.
- **Lock (mutex):** cadeado para duas threads não mexerem no mesmo dado ao mesmo tempo.
- **Heartbeat:** sinal periódico de "ainda estou aqui".
- **LERP:** interpolação linear, para andar aos poucos até um alvo.
- **AABB:** colisão entre retângulos alinhados aos eixos.
- **Paralaxe:** camadas de fundo andando em velocidades diferentes para dar profundidade.
- **A\*:** algoritmo de busca de caminho que usa custo já gasto mais uma estimativa do que falta.

---

## 11. Sugestão de divisão da fala (ajustem entre vocês)

Ordem dos slides em `docs/apresentacao/2026-11-19_slides-pyshooter.pptx`.

| Parte | Slides | Sugestão |
| :--- | :--- | :--- |
| Conceito, jogo base, inimigos e chefes, demonstração | capa, conceito, demo, campanha | Pedro (fez a base) |
| O que mudou no T2, arquitetura, estados, padrões | trabalho2, arquitetura, estados, padroes | Guilherme |
| Desafio, bot e testes | desafio, bot | Pedro (para os dois falarem de código) |
| Multiplayer, protocolo e correções | multiplayer, protocolo, correcoes | Guilherme |
| Matemática e perguntas | matematica, fim | os dois |

**Antes do dia:**

1. Rodar o jogo e jogar uma fase do começo ao fim.
2. Testar o multiplayer em 2 PCs com o checklist.
3. Abrir os 5 arquivos centrais e ler com calma:
   - [game.py](../game.py)
   - [core/gameplay.py](../core/gameplay.py)
   - [entities/base.py](../entities/base.py)
   - [network/server.py](../network/server.py)
   - [network/client.py](../network/client.py)
4. Cada um explicar a seção 5 para o outro em voz alta. Se travar em algum ponto, é ali que precisa reler.
