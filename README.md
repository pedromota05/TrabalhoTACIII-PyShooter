# PyShooter

Jogo de plataforma e ação 2D desenvolvido em Python com Pygame. Controle o personagem, enfrente inimigos e chefes, colete recursos e avance pelas fases.

## Requisitos

- Python 3
- Pygame
- Pillow — usado para carregar a animação da tela de game over

## Instalação

No terminal, na pasta raiz do projeto, instale as dependências:

```bash
python -m pip install pygame pillow
```

## Como executar

Execute o comando a partir da raiz do repositório. Isso é importante porque imagens, áudios e fases são carregados por caminhos relativos.

```bash
python main.py
```

## Controles

| Ação | Teclas |
| --- | --- |
| Mover para a esquerda | `A` ou seta para a esquerda |
| Mover para a direita | `D` ou seta para a direita |
| Pular | `W` ou seta para cima |
| Atirar | `Espaço` |
| Lançar granada | `Q` ou `G` |
| Pausar, voltar ou sair de uma tela | `Esc` |

Use o mouse para navegar pelo menu, escolher uma fase, pausar o jogo e ajustar o volume.

## Fases

As fases jogáveis ficam em [`levels/`](levels/) e seguem o padrão `level<N>_data.csv`. Atualmente, a progressão utiliza as fases 1 a 4, conforme `MAX_LEVELS` em [`config.py`](config.py).

## Organização do projeto

```text
main.py             Ponto de entrada do jogo.
game.py             Coordena a sessão, as telas e o loop principal.
core/               Serviços de gameplay, entrada, renderização e carregamento de fases.
entities/           Jogador, inimigos, projéteis, itens e elementos de cenário.
ui/                 Telas, HUD e transições visuais.
world/              Construção do mundo a partir da matriz de tiles.
levels/             Arquivos CSV das fases.
img/ e audio/       Recursos visuais e sonoros.
config.py           Constantes de tela, física, fases e interface.
```

## Edição de fases

O projeto inclui o script `level-editor.py` para edição manual das matrizes de tiles. Os mapas utilizados pelo jogo devem ser salvos em `levels/` com o nome esperado pela fase, por exemplo `level1_data.csv`.

## Créditos dos assets

- [Pixel Platformer](https://erayzesen.itch.io/pixel-platformer)
- [Team Wars Platformer Battle](https://secrethideout.itch.io/team-wars-platformer-battle)
- [Soundimage](https://soundimage.org/fantasywonder)
- [Grenades 16x16](https://mtk.itch.io/grenades-16x16)
