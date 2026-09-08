# Fórmulas e Mecânicas Matemáticas do PyShooter

Este documento detalha as principais fórmulas matemáticas e físicas aplicadas no código-fonte do jogo. Estas equações regem a movimentação, inteligência artificial e renderização da interface do usuário, e devem servir como referência técnica para o **Game Design Document (GDD)**.

## 1. Física de Movimentação e Gravidade
Aplicada às entidades que sofrem a ação da gravidade (Jogador, Inimigos e Granadas). O motor do jogo calcula a queda baseando-se no incremento constante da aceleração sobre a velocidade vertical.

* **Fórmula da Gravidade (por frame):**
  `Velocidade_Y = Velocidade_Y + Gravidade`

* **Fórmula do Pulo:**
  `Velocidade_Y = -Força_do_Pulo`

## 2. Visão da Inteligência Artificial (Cálculo de Distância)
Para que os inimigos tomem decisões baseadas na posição do jogador (como atirar ou seguir), o jogo mede a distância absoluta em pixels entre os dois centros de massa utilizando o **Teorema de Pitágoras** (através da função `math.hypot`).

* **Fórmula de Distância Euclidiana:**
  $$Dist\hat{a}ncia = \sqrt{(X_{jogador} - X_{inimigo})^2 + (Y_{jogador} - Y_{inimigo})^2}$$

## 3. Mira e Tiros Teleguiados (Trigonometria)
Diferente dos tiros de armamentos padrão (que viajam horizontalmente), projéteis que miram diretamente no jogador (como as flechas atiradas pelos Esqueletos) utilizam trigonometria para calcular a trajetória de interceptação.

* **Cálculo do Ângulo de Tiro:**
  $$\theta = \text{atan2}(Y_{jogador} - Y_{origem}, X_{jogador} - X_{origem})$$

* **Decomposição da Velocidade nos Eixos:**
  $$Velocidade\_X (dx) = \cos(\theta) \times \text{Velocidade\_Base}$$
  $$Velocidade\_Y (dy) = \sin(\theta) \times \text{Velocidade\_Base}$$

## 4. Proporção da Interface de Usuário (Barra de Vida)
O preenchimento verde da barra de vida do HUD (Heads-Up Display) varia dinamicamente conforme o jogador sofre dano ou coleta itens médicos. O cálculo é feito utilizando uma razão geométrica.

* **Razão de Vida:**
  $$Raz\tilde{a}o = \frac{\text{Vida\_Atual}}{\text{Vida\_M\acute{a}xima}}$$

* **Fórmula de Renderização:**
  $$\text{Largura\_Exibida} = Raz\tilde{a}o \times \text{Largura\_Total\_da\_Barra}$$

## 5. Física Parabólica e Reflexão (Granada)
A granada não descreve uma reta, mas sim um arco parabólico durante seu tempo de fusão, combinando movimento linear e aceleração da gravidade, e é o único projétil no jogo com física de rebatimento horizontal.

* **Movimento do Arco Parabólico:** 
  A granada viaja simultaneamente através de um deslocamento fixo no eixo horizontal e um deslocamento acelerado no eixo vertical.
  `dx = Direção * Velocidade`
  `dy = Velocidade_Y` (acumulando a força da gravidade a cada tick)

* **Reflexão Horizontal (Quique em Paredes):** 
  Quando o deslocamento previsto em X colide com o _bounding box_ lateral de um obstáculo (parede), a granada reflete conservando sua força horizontal no sentido oposto.
  `Direção = Direção * -1`
