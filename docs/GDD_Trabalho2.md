# GDD TAC III — PyShooter (Atualizado - Trabalho 2)

**Fundação Universidade Federal da Grande Dourados (UFGD)**  
**Faculdade de Engenharia (FAEN) — Engenharia de Computação**  
**Disciplina:** Tópicos Avançados em Computação III (TAC III)  
**Professor:** Vanderson Hafemann Fragal  

**Desenvolvedores:**  
- **Guilherme Silva Sampaio:** Arquitetura de software, multiplayer LAN (UDP/threads), integração do editor de fases, implementação de padrões de projeto, diagramas UML, refatoração segura e documentação do GDD.  
- **Pedro Henrique Gonçalves Mota:** Concepção da base do jogo, obtenção e adaptação de assets gráficos/sonoros, mecânicas de gameplay, chefes, fases e testes.  

---

## 1. Game Design Document (GDD)

### 1.1 Conceito Principal
**PyShooter** é um jogo de ação 2D *side-scrolling* no estilo *Run and Gun*, desenvolvido em **Python** e **Pygame**. O jogador assume o controle de um soldado em missão de combate através de biomas naturais hostis (florestas de pinheiros, cordilheiras nevadas e pântanos densos). O personagem avança horizontalmente enfrentando soldados de infantaria, snipers, atiradores robóticos, esqueletos arqueiros e chefes colossais (Demon Boss e Dragon Boss), coletando suprimentos (munição, kits médicos e granadas) e superando armadilhas de terreno. O objetivo de cada fase é sobreviver aos combates e alcançar o portal de extração para avançar na campanha.

No **Trabalho 2**, o jogo expandiu suas fronteiras com a inclusão de:
1. **Navegação Completa por Menus**: Menu Principal, Seleção de Fases, Menu Multiplayer LAN, Editor de Fases, Instruções, Configurações de Áudio com sliders e Telas de Pausa/Fim de Jogo.
2. **Editor de Fases Integrado**: Ferramenta modular que permite criar, inspecionar, salvar e carregar mapas personalizados diretamente na matriz de arquivos CSV (`levels/`).
3. **Multiplayer em LAN (Cliente e Servidor)**: Partidas cooperativas locais em tempo real via sockets UDP não-bloqueantes com threads em background, controle de *heartbeat/timeout*, sincronização de combate e interpolação linear (LERP) para eliminar saltos visuais.
4. **Formalização de Padrões de Projeto (GoF e Arquiteturais)**: Aplicação explícita dos padrões Singleton, State, Factory Method, Facade, Observer e Remote Proxy.
5. **Combate e Diversão**: Mira e disparo com o mouse em qualquer ângulo (só a arma gira; o corpo fica parado), mecânica de *dash* com invencibilidade, sistema de vidas compartilhadas com renascimento automático, pontuação dinâmica com multiplicador de combo e batalhas de chefes em etapas sequenciais.

---

### 1.2 Estilo e Gênero

| Aspecto | Classificação |
| :--- | :--- |
| **Gênero primário** | Run and Gun / 2D Platformer Shooter |
| **Subgênero** | Side-scrolling Action / Co-op Multiplayer |
| **Perspectiva** | Vista lateral 2D (Side-view) |
| **Referências clássicas** | *Metal Slug*, *Contra*, *Mega Man*, *Ghosts 'n Goblins* |

O foco do jogo é a precisão de movimento, agilidade de esquiva e combate estratégico com armas de tiro reto e arremessos parabólicos de granadas contra agrupamentos de inimigos.

---

### 1.3 Plataforma Alvo

| Requisito | Especificação |
| :--- | :--- |
| **Sistema Operacional** | Windows 10/11, Linux ou macOS |
| **Linguagem / Versão** | Python 3.10+ (compatível com 3.12+) |
| **Dependências Principais** | `pygame` (2.5+), `Pillow` |
| **Resolução de Tela** | 1200 × 640 pixels (Modo Editor: 1200 × 740 pixels) |
| **Periféricos** | Teclado (movimento, pulo, dash, granada, placas) e Mouse (mira, tiro, menus e editor) |
| **Rede** | Conexão Ethernet ou Wi-Fi em LAN (UDP porta 5555) |

---

### 1.4 Mecânicas e Controles

#### 1.4.1 Mapa de Controles

##### Controles de Gameplay (In-Game)
| Tecla / Controle | Ação |
| :--- | :--- |
| **A** ou **←** | Mover para a esquerda |
| **D** ou **→** | Mover para a direita |
| **W** ou **↑** | Pular |
| **Espaço** | Dash (impulso rápido com invencibilidade; recarga de ~0,8 s) |
| **Mouse** | Mirar (a arma acompanha o cursor) |
| **Botão Esquerdo do Mouse** | Atirar na direção da mira (segurar para tiro contínuo) |
| **Q** ou **G** | Lançar granada (arco parabólico com dano em área) |
| **E** | Ler placa próxima |
| **ESC** | Pausar partida / Retornar ao menu |

##### Controles do Editor de Fases (Level Editor)
| Controle | Ação |
| :--- | :--- |
| **Botão Esquerdo do Mouse** | Pintar o tile selecionado na grade |
| **Botão Direito do Mouse** | Apagar tile da grade (define como vazio `-1`) |
| **M** | Alternar Modo Mover (arrastar objeto para outra célula; troca de lugar se ocupada; ESC ou botão direito cancelam) |
| **Ctrl+Z** | Desfazer última alteração (histórico de até 100 passos) |
| **Ctrl+Y** ou **Ctrl+Shift+Z** | Refazer alteração desfeita |
| **← / →** | Rolar a visão horizontal do mapa no editor |
| **Shift Esquerdo / Direito** | Multiplicador de velocidade de rolagem (5x mais rápido) |
| **↑ / ↓** | Alternar número da fase ativa (Fase 1, 2, 3...) |
| **Botão "Mover (M)"** | Ativa ou desativa a ferramenta de movimentação de blocos |
| **Botão "Desfazer"** | Desfaz a última ação realizada na grade |
| **Botão "Refazer"** | Refaz a última ação desfeita |
| **Botão "Salvar"** | Persiste a matriz editada em `levels/level{N}_data.csv` |
| **Botão "Carregar"** | Recarrega os dados do arquivo CSV correspondente |
| **Botão "<- Menu" / ESC** | Restaura a resolução padrão e retorna ao Menu Principal |

##### Controles de Interface e Menus
- **Mouse (Clique Esquerdo):** Interage com botões de navegação, caixas de diálogo, seletor de cor, caixas de texto de IP e seleção de fases.
- **Sliders de Áudio:** Arraste interativo para ajuste contínuo de volume da música de fundo e efeitos sonoros (SFX).

---

### 1.5 Arquitetura de Menus e Telas

A interface do PyShooter é estruturada sob o padrão **State**, onde o loop central do jogo delega a captura de eventos, atualização de estados e renderização visual para telas especializadas localizadas em `ui/screens/`.

```mermaid
graph TD
    Menu[Menu Principal] --> NovoJogo[Seleção de Fase]
    Menu --> MultiMenu[Menu Multiplayer LAN]
    Menu --> Editor[Editor de Fases]
    Menu --> Instr[Instruções e Controles]
    Menu --> Opcoes[Opções de Áudio]
    Menu --> Sair[Encerrar Jogo]

    NovoJogo --> Playing[Gameplay Campanha]
    NovoJogo --> Desafio[Modo Desafio: fases 1 a 5]
    MultiMenu --> Host[Criar Servidor LAN] --> PlayingMulti[Gameplay Cooperativo]
    MultiMenu --> Join[Conectar via IP LAN] --> PlayingMulti

    Playing --> Pause[Menu de Pausa]
    Playing --> GameOver[Tela de Game Over]
    Playing --> Vitoria[Tela de Vitória]
    Desafio --> GameOver
    Desafio --> Vitoria
    PlayingMulti --> Vitoria
    Vitoria --> Menu
    PlayingMulti --> Pause
    PlayingMulti --> GameOver
    Pause --> Menu
    GameOver --> Menu
    Editor --> Menu
    Instr --> Menu
    Opcoes --> Menu
```

#### Descrição das Telas:
1. **Menu Principal (`MainMenuScreen`):** Tela inicial elegante com o título do jogo e acesso direto a todas as áreas (Novo Jogo, Multiplayer, Editor de Fases, Instruções, Configurações e Sair).
2. **Seleção de Fase (`LevelSelectScreen`):** Exibe os gamepads interativos para escolha de fases da campanha (Fases 1 a 4). As fases já vencidas ganham contorno verde e o selo **CONCLUÍDA** (progresso salvo em `save/progresso.json` por `core/progress.py`). Conta com o **Seletor de Cor do Personagem** (VERDE, AZUL, VERMELHO, AMARELO, ROXO), que persiste no arquivo de progresso. Abaixo fica o botão **MODO DESAFIO**, liberado depois de zerar a campanha, com o recorde de tempo.
3. **Menu Multiplayer LAN (`MultiplayerMenuScreen`):** Interface dedicada que permite:
   - **Criar Servidor (Host):** Inicializa o socket UDP local e conecta automaticamente o hospedeiro como Jogador 1. O Host seleciona a fase inicial da campanha ou o Modo Desafio cooperativo.
   - **Conectar via IP (Join LAN):** Campo de entrada de texto interativo com cursor piscante para informar o endereço IP do Host (padrão `127.0.0.1`, porta `5555`) e botão de conexão como Jogador 2. O campo de IP suporta colagem rápida via `Ctrl+V` e seleciona automaticamente todo o conteúdo ao clicar.
   - **Seletor de Cor do Personagem:** Escolha de cor individual (VERDE, AZUL, VERMELHO, AMARELO, ROXO); caso o Cliente selecione a mesma cor do Host, o sistema avança automaticamente para a próxima cor livre e exibe um aviso em tela (mensagem `color`).
   - Exibição em tempo real de mensagens de status da rede.
4. **Editor de Fases (`LevelEditorScreen`):** Ambiente de edição de fases completo com grade, paleta de tiles, atalhos de teclado (Modo Mover, Desfazer/Refazer) e botões de I/O em disco.
5. **Configurações (`OptionsScreen`):** Ajuste de volume de música e efeitos sonoros através de barras com botões deslizantes (*knobs*) proporcionais.
6. **Pausa (`PauseOverlay`):** Overlay escurecido sobre a partida em andamento permitindo continuar ou sair para o menu.
7. **Tela de Jogo Ativo / HUD:** O cursor padrão é substituído por uma mira visual própria, com uma barra de recarga do dash logo abaixo. No canto superior direito, antes do botão de pausa, o HUD exibe o contador **VIDAS** com marcadores circulares. O HUD exibe também o mostrador **PONTOS** e o indicador **COMBO xN** com barra de tempo. Ao sofrer queda com vidas restantes, a tela exibe o aviso central **"-1 VIDA / Restam N"**, renascendo o combatente após 1 segundo.
8. **Game Over (`GameOverScreen`):** Exibida quando as vidas do soldado se esgotam. No modo solo, o botão Restart recomeça a fase com as 3 vidas cheias. Em dupla cooperativa normal, o jogador que esgota as vidas aguarda como espectador enquanto o parceiro estiver vivo; caso ambos morram, o Host recomeça a fase automaticamente após 3 segundos. No Modo Desafio em dupla (vida única por jogador), o jogador derrotado não renasce na fase e visualiza o aviso *"VOCÊ CAIU! Desafio: uma vida só. Aguardando o parceiro terminar a fase…"* com a câmera acompanhando o parceiro (se o parceiro terminar a fase, quem caiu retorna na fase seguinte com 50% de HP); se ambos caírem, a tela exibe *"DESAFIO ENCERRADO"* em ambos os PCs e apenas o Host tem acesso ao botão Restart, que reinicia o Modo Desafio a partir da fase 1 para ambos.
9. **Vitória (`VictoryScreen`):** Véu escuro sobre o jogo congelado com "VITÓRIA!" e o tempo da partida. Aparece ao matar os dois chefes da fase 4 (fim da campanha) ou ao terminar a fase 5 no Desafio, quando mostra também o recorde e o aviso **NOVO RECORDE**.

#### Progressão, Checkpoints e Modo Desafio
- **Campanha e Saída das Fases 1 a 3:** A campanha é estruturada nas fases 1 a 4. As fases 1 a 3 são finalizadas em um castelo temático desenhado no encerramento do mapa (castelo de pedra na fase 1, forte de madeira na fase 2 e castelo de gelo na fase 3), com a linha de chegada posicionada 6 blocos antes, no terreno plano final.
- **Checkpoints:** Mapeados através do tile `88` (bandeira de checkpoint) configurado diretamente na matriz CSV da fase (a lista em `config.CHECKPOINTS` é utilizada apenas se a fase não possuir nenhum tile de bandeira). Ao alcançar uma bandeira, o jogo registra as coordenadas, a contagem de munição, granadas e a lista de inimigos derrotados; o reinício via checkpoint recupera o soldado no local com vida cheia. Os checkpoints são desativados no Modo Desafio e no multiplayer.
- **Sistema de Vidas (Campanha Solo e Co-op):** A equipe possui 3 vidas compartilhadas (com o Host atuando como autoridade central no multiplayer via mensagens `death` e `lives`). Ao morrer (queda ou vida zerada) com vidas restantes, surge o aviso "-1 VIDA / Restam N" e o personagem renasce em 1 s: ao lado do parceiro vivo (no co-op) ou na última posição segura (com ambos os pés no chão, cerca de 1 s antes da queda, no modo solo). Se não houver posição segura nem parceiro, volta à última bandeira de checkpoint ou ao início da fase. O esgotamento das 3 vidas resulta em Game Over.
- **Modo Desafio:** Maratona ininterrupta das fases 1 a 5 com vida única por combatente e checkpoints desativados. Vida, munição e granadas transitam entre fases (vida máxima limitada a 100). O HUD exibe o cronômetro (mm:ss.d) e o marcador "FASE x/5". A fase 5 é a arena final; ao terminá-la, o melhor tempo fica salvo como recorde. O Desafio não marca a campanha como zerada. Em partidas em dupla, a queda de um jogador o mantém como espectador acompanhando a câmera do parceiro vivo; se o parceiro concluir a fase, o jogador caído renasce na fase subsequente com metade da vida. A queda de ambos encerra a maratona com o aviso "DESAFIO ENCERRADO", permitindo que o Host reinicie o Desafio a partir da fase 1.
- **Chefes em Etapas (Fase 4):** A arena da fase 4 ocorre em duas etapas sucessivas: enfrenta-se primeiro o Demônio terrestre (*Demon Boss*); exatamente 1,5 s após sua derrota, o Dragão voador (*Dragon Boss*) surge em meio a explosões e ao aviso na tela "ETAPA 2/2" (com o HUD registrando "CHEFE x/2"). A tela de Vitória da campanha é ativada apenas após a morte do último chefe.
- **Sistema de Pontuação, Combo e Drops:**
  - **Pontos por Inimigo (`config.KILL_POINTS`):** Soldado: 100 pts, Robô: 150 pts, Esqueleto: 150 pts, Sniper: 200 pts, Demônio: 1500 pts, Dragão: 2000 pts.
  - **Multiplicador de Combo:** Mortes consecutivas ocorridas em até 2,5 s da eliminação anterior incrementam o multiplicador progressivamente até x5 ($\text{pontos} = \text{base} \times \text{combo}$). O HUD apresenta os contadores "PONTOS" e "COMBO xN" com barra regressiva de tempo.
  - **Drops Determinísticos de Suprimentos:** Inimigos comuns eliminados possuem probabilidade de soltar caixas de suprimentos (munição: 25%, vida: 10%, granadas: 8%), utilizando sorteio determinístico calculado pelo `target_id` da entidade para garantir paridade total entre Host e Cliente.
  - **Efeitos de Impacto:** Inimigos e chefes piscam em branco e exibem texto de dano flutuante ao serem alvejados; detonações de granadas e mortes de chefes geram tremor de tela (*screen shake*).
- **Interatividade de Cenário e Colisão Co-op:** Caixas de itens flutuam no terreno e apresentam texto informativo ao serem coletadas (com sincronização de remoção imediata no cliente parceiro via mensagem `item`). Placas no cenário (tile 23) exibem caixas de diálogo com instruções e dicas ao pressionar a tecla **E**. Jogadores em rede possuem colisão física recíproca, permitindo subir na cabeça do companheiro de equipe para alcançar plataformas elevadas.


#### Em Desenvolvimento (após 2026-11-21)
As novidades abaixo estão sendo implementadas e ainda não fazem parte desta versão do documento: renascer no início da fase ou logo após a última bandeira, golpe corpo a corpo com a arma, caixas quebráveis, inimigos aranha, vida extra, tela cheia, músicas por fase e uma fase 5 de hordas.

---

### 1.6 O Editor de Fases (Level Editor)

O editor de fases foi refatorado de um script procedural legado (`level-editor.py`) para uma classe modular de alta coesão (`LevelEditorScreen` em `ui/screens/level_editor.py`), perfeitamente integrada ao ciclo de vida do jogo.

#### Especificações Técnicas do Editor:
- **Resolução de Tela Estendida:** Ao entrar no editor, a janela é redimensionada dinamicamente para `1200 × 740` pixels (oferecendo 900 pixels de largura de visão de mapa, 300 pixels de barra lateral direita para a paleta de blocos e 100 pixels de margem inferior para a barra de ferramentas). Ao retornar ao menu, a resolução nativa de `1200 × 640` é restabelecida sem falhas.
- **Estrutura Matricial:** O mapa é composto por uma matriz bidimensional de dimensões fixas:
  $$\text{Linhas} = 16, \quad \text{Colunas} = 200, \quad \text{Tamanho do Bloco} = 40 \times 40\text{ px}$$
- **Paleta de 89 Tiles Mapeados (em 7 Colunas):**
  - `0 a 8, 24 a 35, 47 a 48, 50, 58 a 61, 65 a 66, 73 a 77, 83 a 84`: Terrenos e plataformas sólidas (terra, grama, pedra e neve).
  - `85`: Rampa com colisão diagonal/inclinada.
  - `9 a 10, 37 a 39, 42 a 46, 51 a 57, 62 a 64, 67 a 68`: Água profunda (perigo ambiental letal).
  - `11 a 14, 36, 40, 49, 71 a 72, 78 a 82`: Decorações visuais sem colisão física (árvores gigantes, pinheiros, grama decorativa).
  - `20, 41`: Castelo de saída / término da fase (exibido como castelo na paleta e no mapa, integrando a linha de chegada).
  - `22`: Propulsor de velocidade (*Speed Boost*).
  - `23`: Placa de dica e instruções (interagível no jogo via tecla E).
  - `88`: Bandeira de Checkpoint (salvamento de estado na fase).
  - `15`: Ponto de geração (*Spawn*) do Jogador.
  - `16`: Spawn de Soldado patrulheiro básico.
  - `69`: Spawn de Inimigo Robô atirador.
  - `70`: Spawn de Inimigo Esqueleto arqueiro.
  - `86`: Spawn do Demônio Chefe terrestre (*Demon Boss*).
  - `87`: Spawn do Dragão Chefe voador (*Dragon Boss*).
  - `17, 18, 19`: Caixas de suprimentos (Munição +15, Granada +3, Kit Médico +25 HP).
- **Modo Mover (Tecla M e Botão "Mover (M)"):** Permite selecionar e arrastar objetos e blocos de uma célula para outra na grade; caso a célula de destino já esteja ocupada, os blocos trocam de posição automaticamente. Pressionar ESC ou o botão direito do mouse cancela a movimentação.
- **Sistema de Histórico (Desfazer / Refazer):** Histórico com capacidade de até 100 passos reversíveis através dos atalhos **Ctrl+Z** (desfazer) e **Ctrl+Y** ou **Ctrl+Shift+Z** (refazer), além dos botões dedicados "Desfazer" e "Refazer" na barra inferior. Cada operação de pintura ou arrasto de objeto é gravada atomicamente como um passo.
- **Sistema de Persistência em Disco:** Gravação e leitura atômica em arquivos CSV no diretório `levels/level{N}_data.csv`.

---

### 1.7 Multiplayer em LAN (Cliente e Servidor UDP)

Baseado nos modelos desenvolvidos pelo professor Vanderson em `tac3/exemplos/threads/`, o sistema de rede do PyShooter adota o protocolo **UDP (User Datagram Protocol)** associado a **threads assíncronas em segundo plano**.

```mermaid
sequenceDiagram
    autonumber
    participant Client1 as Jogador 1 (Host)
    participant Server as GameServer (UDP :5555)
    participant Client2 as Jogador 2 (Cliente)

    Note over Client1,Server: Client1 inicia GameServer na porta 5555
    Client2->>Server: Pacote de Estado (x, y, action, dir, shoot, hp, aim)
    Server->>Client1: Broadcast do Estado de Client2
    Client1->>Server: Pacote de Estado (x, y, action, dir, shoot, hp, aim)
    Server->>Client2: Broadcast do Estado de Client1
    Note over Client1,Client2: Renderização com Interpolação Linear (LERP)
    Client2->>Server: Pacote de Desconexão (player_id,quit)
    Server->>Client1: Notificação de Remoção (player_id,remove)
    Note over Client1: Remove sprite de Client2 sem travar gameplay
```

#### 1.7.1 Protocolo de Comunicação de Pacotes
Os pacotes são transmitidos em strings CSV de baixa sobrecarga de dados:
1. **Sincronização de Estado:**
   $$\text{Formato: } \texttt{"player\_id,x,y,action,direction,is\_shooting,health,aim"}$$
   - `player_id`: Identificador único da sessão (ex.: `"P1 (Host)"`, `"P2 (Cliente)"`).
   - `x, y`: Posição absoluta do personagem no mundo (compensando a rolagem de câmera `bg_scroll`).
   - `action`: Índice de animação ativo (0: Parado, 1: Correndo, 2: Pulando, 3: Morte).
   - `direction`: Orientação horizontal (`1` para a direita, `-1` para a esquerda).
   - `is_shooting`: Flag booleana (`1` ou `0`) indicando disparo de projéteis.
   - `health`: Pontos de vida atuais do combatente remoto.
   - `aim`: Ângulo da mira em radianos, utilizado para determinar a trajetória da bala e a inclinação da pose da arma do parceiro remoto.
2. **Desconexão Voluntária:**
   $$\text{Formato: } \texttt{"player\_id,quit"}$$
3. **Remoção pelo Servidor:**
   $$\text{Formato: } \texttt{"player\_id,remove"}$$
4. **Dano em Inimigo:** `player_id,hit,target_id,dano` — quem acertou avisa; o Host aplica o dano (é a autoridade sobre os inimigos).
5. **Estado dos Inimigos (Host → clientes):** `player_id,enemies,lote,fase`, em que o lote tem itens `target_id:x:y:ação:direção:vida:vivo:chefe` separados por `|`. O cliente descarta lotes de outra fase, já que os `target_id` recomeçam em cada fase.
6. **Tiro de Inimigo (Host → clientes):** `player_id,eshoot,tipo,x,y,direção,vx,vy,alvo_x,alvo_y`.
7. **Fase Atual e Modo de Jogo (Host → clientes):**
   $$\text{Formato: } \texttt{"player\_id,level,fase,vitória,desafio"}$$
   repetida periodicamente a cada 0,5 s. O 5º campo `desafio` informa se a partida está no Modo Desafio cooperativo. O cliente carrega a fase anunciada (mesmo na tela de Game Over) ou avança para a Vitória.
8. **Pedido de Troca de Fase (cliente → Host):** `player_id,levelreq,fase`, enviado quando o cliente alcança a saída da fase.
9. **Coleta de Suprimento:** `player_id,item,fase,item_id`, transmitido quando um jogador recolhe uma caixa de suprimento, sincronizando sua remoção imediata no mapa do parceiro.
10. **Sincronização de Cor do Soldado:** `player_id,color,indice`, informando o índice de cor escolhido para renderização das texturas customizadas.
11. **Aviso de Morte do Cliente (cliente → Host):** `player_id,death,seq`, emitido pelo cliente ao cair em abismo ou ter a vida zerada (enviado 3 vezes consecutivas para garantir recepção sobre UDP).
12. **Saldo de Vidas Compartilhadas (Host → clientes):** `player_id,lives,vidas,reset`, transmitido pelo Host para anunciar o total de vidas da equipe; o incremento sequencial de `reset` comanda o reinício da fase ou do Desafio no cliente.

As balas disparadas por um jogador remoto são estritamente visuais (`Bullet(visual_only=True)`): o dano real é processado exclusivamente pela mensagem `hit` de quem atirou, o que evita duplicação de dano no Host e fogo amigo.

#### 1.7.2 O Servidor de Jogo (`GameServer`)
- **Socket UDP com Timeout Seguro:** Configurado com `settimeout(1.0)` em um loop de execução contínuo numa thread *daemon*. Isso garante que a thread possa ser cancelada graciosamente ao sair da partida sem travar o processo principal do Pygame.
- **Tabela de Sessões Ativas:**
  $$\texttt{clients[player\_id]} = \{\text{"address"}: (\text{ip}, \text{port}), \text{"last\_seen"}: \text{timestamp}\}$$
- **Broadcast Seletivo:** Todo pacote de movimentação recebido de um jogador é imediatamente retransmitido para todos os demais jogadores registrados.
- **Tratamento de Inatividade (Heartbeat & Timeout):** A cada segundo, o servidor verifica se algum cliente não enviou pacotes por mais de `TIMEOUT_LIMIT = 5.0` segundos. Caso detectado, o cliente inativo é expulso da tabela e um comando `remove` é transmitido aos demais clientes.

#### 1.7.3 O Cliente de Rede (`NetworkClient`)
- **Thread Receptora Assíncrona:** Uma thread independente escuta a porta UDP continuamente e alimenta um dicionário compartilhado protegido por semáforo de exclusão mútua (`threading.Lock()`).
- **Suavização de Movimento com LERP (Linear Interpolation):** Para evitar que flutuações de rede e jitter causem "teleportes" na tela, o cliente atualiza a posição exibida a cada quadro através da fórmula de interpolação linear:
  $$x_{\text{atual}} = x_{\text{atual}} + (x_{\text{alvo}} - x_{\text{atual}}) \times \alpha$$
  $$y_{\text{atual}} = y_{\text{atual}} + (y_{\text{alvo}} - y_{\text{atual}}) \times \alpha$$
  onde $\alpha = 0.20$ ($\text{LERP\_FACTOR}$), garantindo uma movimentação extremamente fluida e natural.

#### 1.7.4 A Entidade de Jogador Remoto (`RemotePlayer`)
Representa visualmente o combatente conectado via LAN:
- Utiliza o conjunto de texturas coloridas correspondentes à cor do parceiro (sincronizada via pacote `color`) através do cache do `AssetManager`.
- Renderiza a arma rotacionando dinamicamente em torno do ponto de empunhadura para coincidir com o ângulo da mira (`aim`) transmitido pelo parceiro.
- Converte a coordenada absoluta do mundo para a coordenada relativa da câmera local:
  $$\text{rect.center} = (\text{int}(x_{\text{mundo}} - \text{bg\_scroll}), \text{int}(y_{\text{mundo}}))$$
- Renderiza uma **Tag com o Nome do Jogador** e uma **Mini Barra de Vida** sobre a cabeça do personagem.
- Reproduz disparos visuais sincronizados na tela local.
- Possui colisão física ativa com o jogador local, possibilitando que um jogador suba na cabeça do outro para alcançar áreas elevadas.

---

### 1.8 Padrões de Projeto Utilizados (Design Patterns)

A refatoração do PyShooter consolidou uma arquitetura robusta, aplicando formalmente padrões clássicos do *Gang of Four (GoF)* e arquiteturais:

#### 1. Singleton (`AssetManager`)
- **Problema:** Múltiplas entidades chamando `pygame.image.load()` e `pygame.mixer.Sound()` repetidamente, gerando desperdício de memória RAM e sobrecarga de I/O em disco.
- **Solução:** Implementação do `AssetManager` com controle de instância única no método `__new__` e cache de texturas e animações (`_anim_cache`).
- **Benefício:** Centralização de recursos, carregamento único na inicialização e consumo de memória rigorosamente controlado.

#### 2. State (`GameState` e Máquina de Telas)
- **Problema:** Lógica de menus, jogo ativo, editor e pausa misturadas em um único laço condicional gigantesco (*God Method*).
- **Solução:** Enumeração `GameState` operando em conjunto com classes de tela especializadas (`MainMenuScreen`, `MultiplayerMenuScreen`, `LevelEditorScreen`, etc.), cada uma contendo seus próprios métodos de captura de eventos e renderização.
- **Benefício:** Desacoplamento completo entre menus, editor e o motor de combate, facilitando a adição de novos modos sem risco de efeitos colaterais.

#### 3. Factory Method (`World.process_data`)
- **Problema:** Necessidade de instanciar dezenas de tipos distintos de sprites (jogador, soldados, chefes, armadilhas, itens) a partir de matrizes numéricas arbitrárias salvas em CSV.
- **Solução:** O método `process_data()` da classe `World` funciona como uma fábrica de entidades, interpretando o ID do bloco e instanciando dinamicamente a classe polimórfica correta com escala, velocidade e atributos balanceados.
- **Benefício:** Facilidade de expansão do jogo; novos inimigos ou blocos podem ser adicionados ao editor sem modificar o motor físico do jogo.

#### 4. Facade (`Game` e subsistemas em `core/`)
- **Problema:** Acoplamento excessivo entre renderização gráfica, detecção de colisões, controle de entrada de teclado e ciclo de vida do Pygame.
- **Solução:** A classe `Game` atua como uma Fachada unificada, orquestrando subsistemas modulares de responsabilidade única:
  - `core/input_handler.py`: Processamento de periféricos.
  - `core/gameplay.py`: Atualização física e combate.
  - `core/renderer.py`: Desenho de cenários, entidades e HUD.
  - `core/level_loader.py`: Carregamento e reset de fases.
- **Benefício:** Código legível, altamente modular e em estrita conformidade com o princípio de Responsabilidade Única (SRP).

#### 5. Observer / Event-Driven (Manipulação de Eventos e Rede)
- **Problema:** Ações do usuário e mensagens de rede ocorrem de forma assíncrona.
- **Solução:** O laço de eventos do Pygame e a thread de escuta UDP (`NetworkClient._receive_loop`) funcionam sob o modelo de observador/notificador, despachando eventos de clique, tecla e pacotes de rede para os tratadores apropriados.
- **Benefício:** Resposta imediata a comandos do usuário e mensagens de rede sem bloquear a taxa de quadros (60 FPS).

#### 6. Remote Proxy (`RemotePlayer`)
- **Problema:** O jogo precisa renderizar e simular jogadores remotos como se fossem entidades locais normais, sem que eles possuam teclado ou lógica de física local conectada.
- **Solução:** A classe `RemotePlayer` atua como um representante local (*Proxy*) do jogador remoto, espelhando sua posição via interpolação LERP e renderizando suas ações no mundo.
- **Benefício:** Compatibilidade perfeita com o sistema de renderização e grupos de sprites do Pygame.

---

### 1.9 Fórmulas e Mecânicas Matemáticas

#### 1.9.1 Física de Movimentação e Gravidade
Aplicada a entidades terrestres (Jogador, Inimigos, Caixas de Itens e Granadas):
$$\text{Velocidade\_Y}_{t+1} = \min(\text{Velocidade\_Y}_t + \text{Gravidade}, \; \text{Velocidade\_Terminal})$$
$$\text{Gravidade} = 0.75, \quad \text{Velocidade\_Terminal} = 10, \quad \text{Força\_do\_Pulo} = -14$$

#### 1.9.2 Interpolação Linear (LERP) do Multiplayer
Suavização espacial por quadro para jogadores remotos:
$$P_{\text{atual}} = P_{\text{atual}} + (P_{\text{alvo}} - P_{\text{atual}}) \times 0.20$$

#### 1.9.3 Visão da Inteligência Artificial (Distância Euclidiana)
Medição da proximidade entre os centros de massa para disparo e perseguição:
$$d = \sqrt{(X_{\text{jogador}} - X_{\text{inimigo}})^2 + (Y_{\text{jogador}} - Y_{\text{inimigo}})^2}$$

#### 1.9.4 Mira e Projéteis Vetoriais (Trigonometria)
Utilizada pelos Esqueletos Arqueiros e projéteis guiados do Dragon Boss:
$$\theta = \operatorname{atan2}(Y_{\text{alvo}} - Y_{\text{origem}}, \; X_{\text{alvo}} - X_{\text{origem}})$$
$$v_x = \cos(\theta) \times V_{\text{projétil}}, \quad v_y = \sin(\theta) \times V_{\text{projétil}}$$

#### 1.9.5 Física Parabólica e Quique de Granadas
A granada avança horizontalmente com conservação de velocidade linear e sofre aceleração vertical:
$$x_{t+1} = x_t + (\text{Direção} \times 7)$$
$$y_{t+1} = y_t + v_{y, t}, \quad v_{y, t+1} = v_{y, t} + 0.75$$
Ao colidir lateralmente com uma parede ou obstáculo:
$$\text{Direção} = \text{Direção} \times (-1)$$

#### 1.9.6 Mira do Jogador e Giro da Arma
O cálculo do ângulo de mira do soldado em direção ao cursor do mouse em coordenadas de tela é dado por:
$$\theta = \operatorname{atan2}(Y_{\text{cursor}} - Y_{\text{ombro/pivô}}, \; X_{\text{cursor}} - X_{\text{ombro/pivô}})$$
O soldado vira horizontalmente para o lado do cursor ($\text{direção} = 1$ para $X_{\text{cursor}} \ge X_{\text{jogador}}$ ou $-1$ para o quadrante oposto). Para preservar uma postura anatômica crível da sprite, o ângulo local da arma é limitado a $\pm 89^\circ$ em relação ao plano horizontal. A arma é desacoplada da textura do corpo do soldado através de separação por cor de pixels (`entities/aim_pose.py`) e rotacionada isoladamente em torno da empunhadura ($P_{\text{pivô}}$). O ponto exato de ejeção do projétil na ponta do cano ($P_{\text{cano}}$) é determinado pela transformação de rotação 2D:
$$P_{\text{cano}} = P_{\text{pivô}} + R(\theta) \cdot (P_{\text{cano}}^0 - P_{\text{pivô}}^0)$$
$$R(\theta) = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix}$$
O projétil (`Bullet`) é instanciado na ponta do cano e lançado com o vetor de velocidade:
$$v_x = \cos(\theta) \times V_{\text{bala}}, \quad v_y = \sin(\theta) \times V_{\text{bala}}$$
O atributo `Bullet.owner` garante imunidade ao soldado atirador, prevenindo detecções espúrias de autodano na saída imediata do cano.

#### 1.9.7 Mecânica de Deslocamento Rápido (Dash)
Acionado pela tecla **Espaço**, o *dash* desloca o personagem na direção da tecla de movimento pressionada (ou, sem tecla, para o lado em que está virado) por um período contínuo de $T = 10\text{ quadros}$ com velocidade horizontal fixa de $V_{\text{dash}} = 16\text{ px/quadro}$, sob suspensão total de aceleração gravitacional ($g = 0$):
$$\Delta x_{\text{total}} = 10 \times 16 = 160\text{ px} \quad (\approx 4\text{ blocos de } 40\text{ px})$$
Durante os 10 quadros de deslocamento, o combatente usufrui de invulnerabilidade a dano, projetando um rastro estético de 6 silhuetas fantasmagóricas azuis e partículas de poeira. A recarga da habilidade ocorre em $50\text{ quadros}$ (~0,83 s a 60 FPS), monitorada por uma barra indicadora acoplada à mira visual do jogador.

#### 1.9.8 Sistema de Pontuação com Multiplicador de Combo
A pontuação atribuída pela eliminação de um adversário combina a pontuação-base definida em `config.KILL_POINTS` e o índice multiplicador de combo ativo $c$:
$$\text{Pontos\_Ganhos} = \text{Pontos\_Base} \times \min(5, \; c)$$
onde $c \in \{1, 2, 3, 4, 5\}$. O combo é iniciado com $c=1$ na primeira baixa. Cada abate subsequente concretizado dentro de uma janela temporal estrita de até $2.5\text{ segundos}$ ($150\text{ quadros}$ a 60 FPS) adiciona $+1$ ao multiplicador e restabelece a contagem regressiva da barra de combo. Decorridos os 150 quadros sem novos abates, o multiplicador regride automaticamente para o patamar base $c=1$.

---

### 1.10 Engenharia de Requisitos Atualizada

#### Requisitos Funcionais (RF)
| ID | Descrição |
| :--- | :--- |
| **RF-01** | Movimentação horizontal do jogador (esquerda/direita) via teclado (A/D ou setas). |
| **RF-02** | Salto do jogador ao pressionar W ou seta para cima com simulação gravitacional. |
| **RF-03** | Disparo de projéteis com o botão esquerdo do mouse, na direção da mira, com munição limitada e cooldown de tiro de 20 frames. |
| **RF-04** | Lançamento de granadas com trajetória parabólica, timer de pavio e explosão em área. |
| **RF-05** | Detecção de colisões com aplicação de dano diferenciado (inimigos, jogador e chefes). |
| **RF-06** | Carregamento de fases através de matrizes em arquivos CSV (`levels/levelN_data.csv`). |
| **RF-07** | Inteligência Artificial para inimigos com patrulha, detecção e ataque. |
| **RF-08** | Coleta de suprimentos em caixas (vida +25, munição +15, granadas +3). |
| **RF-09** | HUD gráfico exibindo barra de vida dinâmica, contagem de munição e granadas. |
| **RF-10** | Transição suave de fases com efeito de fade na tela. |
| **RF-11** | **[T2] Navegação Completa por Menus:** Suporte a menus integrados de Novo Jogo, Multiplayer, Editor de Fases, Instruções, Configurações e Sair. |
| **RF-12** | **[T2] Configurações de Áudio:** Sliders interativos com knob para ajuste contínuo do volume da música e dos efeitos sonoros. |
| **RF-13** | **[T2] Editor de Fases Integrado:** Ferramenta gráfica para edição da matriz de blocos (pintar e apagar), rolagem de mapa, seleção de 88 tiles e I/O de arquivos CSV. |
| **RF-14** | **[T2] Hospedagem de Servidor LAN:** Criação de servidor local UDP na porta 5555 via thread em background no modo Host. |
| **RF-15** | **[T2] Conexão Cliente LAN:** Conexão a partidas via endereço IP informado pelo usuário com recepção contínua em thread daemon. |
| **RF-16** | **[T2] Sincronização e LERP:** Sincronização em tempo real de coordenadas, ações, direção e tiros entre jogadores em rede local com suavização por LERP. |
| **RF-17** | **[T2] Fim da Campanha:** Vitória ao derrotar os dois chefes da fase 4, com tela de Vitória e tempo da partida. |
| **RF-18** | **[T2] Progresso Salvo:** Fases concluídas, campanha zerada e recorde do Desafio gravados em `save/progresso.json`. |
| **RF-19** | **[T2] Checkpoints:** Bandeiras (tile 88 no CSV da fase) guardam posição, munição, granadas e inimigos mortos; usadas para renascer quando não há posição segura nem parceiro. |
| **RF-20** | **[T2] Modo Desafio:** Fases 1 a 5 seguidas com uma vida, cronômetro, "FASE x/5" e recorde de tempo. |
| **RF-21** | **[T2] Fase sincronizada no multiplayer:** Host e cliente trocam de fase e chegam à vitória juntos (mensagens `level` e `levelreq`). |
| **RF-22** | **[T2] Mira e Tiro com o Mouse:** Rotação dinâmica da arma em torno da empunhadura acompanhando a coordenada do cursor do mouse, com disparo vetorial de projéteis em qualquer ângulo e orientação do soldado. |
| **RF-23** | **[T2] Mecânica de Dash:** Impulso horizontal de esquiva (tecla Espaço) com velocidade de 16 px/frame durante 10 frames, gravidade zero, invulnerabilidade, efeito de rastro fantasma e cooldown de 50 frames. |
| **RF-24** | **[T2] Sistema de Vidas Compartilhadas:** 3 vidas compartilhadas na campanha (solo e co-op com autoridade do Host); renascimento automático em 1 s ao lado do parceiro vivo ou na última posição segura de solo firme. |
| **RF-25** | **[T2] Modo Desafio em Dupla:** Modo cooperativo de vida única por jogador; queda permanente na fase com modo espectador na câmera do parceiro e renascimento na fase seguinte com 50% de HP; Game Over definitivo ("DESAFIO ENCERRADO") com morte de ambos. |
| **RF-26** | **[T2] Batalhas de Chefes em Etapas:** Fase 4 com combate em duas etapas sequenciais (Demon Boss seguido de transição explosiva de 1,5 s para o Dragon Boss), HUD com indicador de etapa e vitória vinculada à queda do último chefe. |
| **RF-27** | **[T2] Sistema de Pontuação, Combo e Drops:** Atribuição de pontuação por inimigo, multiplicador de combo acumulativo (até x5) com janela de 2,5 s, e drops determinísticos de caixas de suprimentos (munição 25%, vida 10%, granadas 8%). |
| **RF-28** | **[T2] Personalização de Cor do Combatente:** Seletor de cores (Verde, Azul, Vermelho, Amarelo, Roxo) salvo no perfil de progresso, com resolução automática anti-colisão de cor entre Host e Cliente via pacote `color`. |
| **RF-29** | **[T2] Interatividade de Cenário, Itens e Colisão Co-op:** Coleta sincronizada de suprimentos via rede, leitura de placas informativas (tecla E) e colisão física entre os dois soldados (permitindo suporte de elevação). |
| **RF-30** | **[T2] Estrutura de Saída em Castelo:** Representação arquitetônica de castelo temático ao final das fases 1 a 3 com a linha de chegada 6 blocos antes, no chão plano do fim da fase. |
| **RF-31** | **[T2] Ferramentas Avançadas do Editor:** Modo Mover (tecla M) para realocação/troca de blocos, sistema de histórico com Desfazer/Refazer (Ctrl+Z / Ctrl+Y até 100 passos) e posicionamento de checkpoints pelo tile 88. |

#### Requisitos Não-Funcionais (RNF)
| ID | Descrição |
| :--- | :--- |
| **RNF-01** | **Desempenho:** Manutenção de taxa estável de 60 quadros por segundo (FPS). |
| **RNF-02** | **Portabilidade:** Execução limpa em qualquer sistema operacional compatível com Python 3.10+ e Pygame. |
| **RNF-03** | **Usabilidade:** Telas intuitivas com feedback visual de botões e atalhos claros. |
| **RNF-04** | **Manutenibilidade:** Separação estrita de responsabilidades (SRP) e eliminação de código duplicado (DRY). |
| **RNF-05** | **Economia de Recursos:** Gerenciamento único de assets na memória via Singleton `AssetManager`. |
| **RNF-06** | **[T2] Baixa Latência em LAN:** Comunicação via UDP de baixa sobrecarga de dados por pacote (< 128 bytes). |
| **RNF-07** | **[T2] Tolerância a Falhas de Rede:** Desconexão segura por timeout após 5 segundos de inatividade sem congelar o Pygame. |
| **RNF-08** | **[T2] Integridade da Física:** Preservação estrita de todas as constantes gravitacionais, colisões e câmera do jogo original. |

---

## 2. Diagramas de Arquitetura (UML)

Os diagramas de arquitetura foram completamente atualizados para incorporar os pacotes de rede (`network/`), o editor de fases modular (`ui/screens/level_editor.py`), os novos menus e os padrões de projeto.

### 2.1 Diagrama de Pacotes (PlantUML)
Localizado em [docs/uml/pacotes.puml](file:///c:/projetos_disco_C/faculdade/TrabalhoTACIII-PyShooter/docs/uml/pacotes.puml):
- Ilustra o fluxo de inicialização a partir de `main.py` e `game.py` (Fachada).
- Destaca o pacote `network/` interagindo com o `game.py` e alimentando o subsistema `gameplay`.
- Demonstra a integração de `level_editor` com os arquivos em `levels/`.
- Mapeia o desacoplamento das telas em `ui/screens/`.

### 2.2 Diagrama de Classes (PlantUML)
Localizado em [docs/uml/classes.puml](file:///c:/projetos_disco_C/faculdade/TrabalhoTACIII-PyShooter/docs/uml/classes.puml):
- Detalha as classes `GameServer`, `NetworkClient` e `Protocol`.
- Exibe o relacionamento de herança entre `pygame.sprite.Sprite` e a nova entidade `RemotePlayer`.
- Identifica os novos estados de `GameState` (`MULTIPLAYER_MENU` e `EDITOR`).
- Inclui estereótipos explícitos para os padrões GoF: `<<Singleton>>`, `<<State>>`, `<<Factory Method>>`, `<<Facade>>` e `<<Proxy>>`.

---

## 3. Repositório do Projeto

O código-fonte integral, histórico de commits e documentações estão disponíveis no repositório oficial do projeto:
- **Repositório GitHub:** [https://github.com/pedromota05/TrabalhoTACIII-PyShooter.git](https://github.com/pedromota05/TrabalhoTACIII-PyShooter.git)
