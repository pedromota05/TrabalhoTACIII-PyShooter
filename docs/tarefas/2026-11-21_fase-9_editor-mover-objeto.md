# Tarefa: editor de fases — mover a posição de um objeto

## Objetivo
No editor de fases, poder pegar um objeto (qualquer tile já colocado: inimigo, item, saída, placa, bloco...) e arrastá-lo para outra célula, sem precisar apagar e pintar de novo. Um "Modo Mover" liga e desliga pela tecla M (e por um botão de texto no painel inferior).

## Já feito (não refazer)
- Tudo fica em `ui/screens/level_editor.py`, classe `LevelEditorScreen`.
- `self.world_data[linha][coluna]` guarda o id do tile (-1 = vazio). `self.img_list[id]` é a imagem. Constantes: `TILE_SIZE`, `ROWS`, `COLS`, `EDITOR_VIEWPORT_WIDTH`, `SCREEN_HEIGHT`, `EDITOR_TOTAL_WIDTH`.
- `handle_event(event, game)` trata teclas (KEYDOWN/KEYUP: setas, Shift, ESC).
- `update(screen, game)`: passo "4. Modificação da grade pelo mouse" pinta com o botão esquerdo (`self.current_tile`) e apaga com o direito, usando `pygame.mouse.get_pressed()` e `self._mouse_held_from_enter`. A célula sob o mouse é `tile_col = (mouse_pos[0] + self.scroll) // TILE_SIZE`, `tile_row = mouse_pos[1] // TILE_SIZE`.
- `_draw_tiles(screen)` desenha os tiles: `px = c*TILE_SIZE - self.scroll`, `py = r*TILE_SIZE + (TILE_SIZE - img.get_height())`.
- Painel inferior: texto `hint_text` ("Setas Cima/Baixo: Mudar Fase | Shift: Scroll Rápido") em `(info_x, SCREEN_HEIGHT + 48)` e notificação temporária com `self.notification_msg` / `self.notification_timer`.

## Arquivos permitidos
- `ui/screens/level_editor.py`
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. No `__init__`: `self.move_mode = False`, `self.dragging = None` (quando arrastando: tupla `(tile_id, linha_origem, coluna_origem)`), `self._prev_left = False`.
2. `handle_event`, KEYDOWN: tecla `pygame.K_m` alterna `self.move_mode`, cancela arrasto em andamento (`self._cancel_drag()`), e mostra notificação "Modo Mover: LIGADO" / "Modo Mover: DESLIGADO" (mesmo esquema de `notification_msg`/`notification_timer` já usado no arquivo; use o mesmo tempo que o salvar usa). Tecla ESC durante um arrasto: só cancela o arrasto (não sai do editor).
3. `_cancel_drag()`: se `self.dragging`, devolve o tile para a célula de origem e zera `self.dragging`.
4. No passo 4 de `update`, se `self.move_mode` for verdadeiro, usar esta lógica NO LUGAR de pintar/apagar (o modo normal continua igual quando `move_mode` é falso):
   - Detectar borda de clique: `left = mouse_buttons[0] == 1`; `pressed = left and not self._prev_left`; `released = (not left) and self._prev_left`; no fim do passo `self._prev_left = left`. Respeitar `self._mouse_held_from_enter` como hoje.
   - `pressed` sobre célula válida com tile != -1 e sem arrasto: `self.dragging = (id, linha, coluna)` e a célula de origem vira -1.
   - `released` com arrasto: se o mouse está numa célula válida da área do mapa, colocar o tile ali (se a célula de destino tinha outro tile, ele vai para a célula de origem: troca de lugar) e mostrar notificação "Objeto movido para (linha, coluna)"; se soltou fora do mapa (painel lateral ou inferior), `_cancel_drag()`.
   - Botão direito durante o arrasto: `_cancel_drag()`.
5. Desenho (depois de `_draw_tiles` e antes da paleta lateral):
   - Em modo mover, contorno amarelo `(255, 220, 60)` de 2 px na célula sob o mouse (se dentro do mapa).
   - Durante o arrasto: retângulo vermelho tracejado ou simples (2 px) na célula de origem, e a imagem do tile arrastado desenhada semi-transparente (`img.copy()` + `set_alpha(170)`) alinhada à célula sob o mouse (mesmo cálculo de `px/py` de `_draw_tiles`).
6. Painel inferior: botão de texto "Mover (M)" ao lado dos botões Salvar/Carregar existentes — desenhe com `pygame.draw.rect` + `self.font` (fundo verde `(60, 140, 70)` quando ligado, cinza `(70, 75, 80)` quando desligado) e alterne `move_mode` ao clicar (borda de clique, como no passo 4). Ajuste o `hint_text` para "Setas Cima/Baixo: Mudar Fase | Shift: Scroll Rápido | M: Mover objeto".
   - Coloque o botão num lugar livre do painel (confira as posições de `self.save_button`, `self.load_button` e `self.back_button` em `_init_buttons` para não sobrepor).
7. Ao sair do editor (`on_exit`) e ao trocar de fase (setas cima/baixo) e no botão Carregar: chamar `_cancel_drag()` antes.

## O que NÃO fazer
- Não mudar formato do CSV, salvar/carregar, paleta, scroll nem o modo normal de pintar/apagar.
- Não tocar em outros arquivos. Não rodar comandos nem fazer commit.

## Verificação (eu rodo)
- `python -m py_compile ui/screens/level_editor.py`.
- Abrir o editor, ligar M, arrastar um inimigo para outra célula, salvar e carregar de novo.

## Critério de pronto
Com M ligado, clicar e arrastar um objeto o leva para a célula onde o botão é solto (trocando de lugar se havia outro), com prévia transparente; ESC/botão direito cancelam; M desligado mantém o editor como era.
