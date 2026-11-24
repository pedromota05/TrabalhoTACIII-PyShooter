# Tarefa: escolher a cor do boneco também no single player e sem cor repetida no multiplayer

## Objetivo
O seletor de cor (hoje só no menu Multiplayer) também aparece na tela de seleção de fases (single player). No multiplayer os dois jogadores nunca ficam com a mesma cor: o Host mantém a dele e o Cliente troca automaticamente para a próxima cor livre.

## Já feito (não refazer)
- `config.py`: `PLAYER_COLORS = [('VERDE', None), ('AZUL', 215), ('VERMELHO', 0), ('AMARELO', 50), ('ROXO', 285)]`.
- `core/progress.py`: `carregar()['cor_jogador']` e `salvar_cor(indice)`.
- `ui/screens/multiplayer_menu.py`: seletor com `self.color`, `self.color_left`/`self.color_right` (setas `<` `>` em ~linha 74-91, clique no `handle_event`) e desenho em ~linha 190-206 (prévia `AssetManager().load_character_animations('player', PLAYER_SCALE * 1.5, self.color)[0][0]`, setas e nome da cor com `draw_text_with_shadow`).
- `ui/screens/level_select.py`: `LevelSelectScreen.update(screen, game)` desenha a grade de fases; não tem `handle_event` (usa botões por `pygame.mouse`).
- `entities/player.py`: no `__init__`, `self.color = progress.carregar().get('cor_jogador', 0)` e, se `self.color`, recarrega `self.animation_list` com `AssetManager().load_character_animations('player', scale, self.color)`.
- `core/gameplay.py` (~linha 495-506): para cada jogador remoto chama `set_color(net_client.get_remote_color(p_id))`; o envio da própria cor é `game.network_client.send_color(getattr(game.player, 'color', 0))` a cada 60 quadros. `network/client.py`: `self.remote_colors` (dict p_id -> cor) e `get_remote_color(p_id)` devolve 0 quando ainda não chegou nada.

## Arquivos permitidos
- `ui/screens/common.py`
- `ui/screens/multiplayer_menu.py`
- `ui/screens/level_select.py`
- `entities/player.py`
- `network/client.py`
- `core/gameplay.py` (só o trecho dos jogadores remotos, ~linha 495-510)
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. `ui/screens/common.py`: nova classe `ColorPicker(center, font_bold)` reaproveitando exatamente o visual atual do menu multiplayer (prévia do boneco, setas `<` `>` 40x40 a ±65 px do centro, nome da cor 70 px abaixo). Métodos:
   - `self.color` iniciado de `progress.carregar().get('cor_jogador', 0) % len(PLAYER_COLORS)`.
   - `handle_click(pos) -> bool`: seta esquerda/direita trocam a cor (com volta), chamam `progress.salvar_cor(self.color)` e devolvem `True` se mudou.
   - `draw(screen)`: desenha tudo. Guardar as prévias em cache por índice (não chamar `load_character_animations` a cada quadro).
   - `reload()`: relê a cor salva (para quando outra tela mudou).
2. `ui/screens/multiplayer_menu.py`: trocar o seletor próprio pelo `ColorPicker` no mesmo lugar e com o mesmo visual; `self.color` continua existindo (como propriedade ou cópia de `picker.color`) se outro código usa.
3. `ui/screens/level_select.py`: criar um `ColorPicker` num canto livre da tela (abaixo/ao lado da grade de fases, sem cobrir botões nem textos; confira as posições usadas no `update`) com o título "SEU BONECO" acima. Como a tela não tem `handle_event`, detectar o clique por borda (`pygame.mouse.get_pressed()[0]` agora e no quadro anterior) dentro do `update` e chamar `handle_click(pygame.mouse.get_pos())`. Ao entrar na tela, chamar `reload()` para mostrar a cor atual. Mostrar o seletor também quando `game.mp_host_pick` for verdadeiro.
4. `entities/player.py`: novo método `set_color(self, color: int)`: se mudou, guarda `self.color`, recarrega `self.animation_list` (`AssetManager().load_character_animations('player', self.scale_used, color)` se `color` != 0, ou `AssetManager().load_character_animations('player', self.scale_used)` / a mesma chamada que a classe base usa para o verde) e atualiza `self.image` com `frame_index`/`action` atuais (cuidado com índice fora do tamanho: use `min`). Guarde a escala recebida no `__init__` em `self.scale_used`. O `__init__` passa a usar `set_color`.
5. `network/client.py`: método `has_remote_color(self, player_id) -> bool` (com o mesmo lock que `get_remote_color` usa) dizendo se a cor daquele jogador já chegou.
6. `core/gameplay.py`, no laço dos jogadores remotos (só no CLIENTE: `not game.is_host`): se `net_client.has_remote_color(p_id)` e a cor do remoto for igual a `game.player.color`, escolher a próxima cor em `PLAYER_COLORS` (índice +1, com volta) diferente da do remoto, chamar `game.player.set_color(nova)`, `net_client.send_color(nova)` na hora, e guardar o aviso em `game.color_msg = "Cor trocada para <NOME>: o parceiro já usa essa"` e `game.color_msg_frames = 120` (o desenho do aviso no HUD eu faço; aqui só decremente `game.color_msg_frames` a cada quadro quando > 0). NÃO salvar essa troca no progresso (é só para esta partida). Importar `PLAYER_COLORS` de config.

## O que NÃO fazer
- Não mudar o protocolo de rede nem o `send_color`.
- Não mudar `core/renderer.py`, `level_loader.py`, `config.py`.
- Não rodar comandos nem fazer commit.

## Verificação (eu rodo)
- `python -m py_compile` nos arquivos; `python tools/teste_multiplayer.py --porta 5601`; abrir a seleção de fases e trocar a cor.

## Critério de pronto
Seletor de cor na seleção de fases e no menu multiplayer (mesmo visual, mesma cor salva); no multiplayer, Cliente com a mesma cor do Host troca sozinho para outra cor e avisa.
