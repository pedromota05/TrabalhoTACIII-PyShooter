# Tarefa: editor — desfazer, refazer e castelo na paleta

## Objetivo
No editor de fases: (1) desfazer (Ctrl+Z e botão "Desfazer") e refazer (Ctrl+Y ou Ctrl+Shift+Z e botão "Refazer") qualquer mudança no mapa; (2) os tiles de saída (20 e 41) aparecem na paleta lateral como o castelinho, igual ao mapa.

## Já feito (não refazer)
- Tudo em `ui/screens/level_editor.py`, classe `LevelEditorScreen`. O mapa é `self.world_data[linha][coluna]` (int, -1 = vazio).
- Mudanças no mapa acontecem em `update` (passo 4): pintar (`self.world_data[r][c] = self.current_tile`, botão esquerdo segurado), apagar (botão direito segurado, `= -1`), e no Modo Mover (pegar o tile ao pressionar, soltar/trocar ao largar, `_cancel_drag` devolve). Carregar fase (`load_level_data`) troca o mapa todo.
- Teclas ficam em `handle_event` (KEYDOWN/KEYUP). Botão "Mover (M)" é desenhado à mão no painel inferior (`pygame.draw.rect` + texto) com clique por borda (`self._prev_left`); copie esse estilo.
- Notificação: `self.notification_msg` / `self.notification_timer`.
- Paleta: `_init_tile_images` monta `self.img_list` e `_init_palette_buttons` cria um `button.Button` por imagem (miniatura de até 36x36). No mapa, tiles 20/41 em fases de `CASTLE_THEMES` já são desenhados como `Castle(self.level, door)` + `FinishLine` (cache `self._castle_cache`).

## Arquivos permitidos
- `ui/screens/level_editor.py`
- Qualquer outro arquivo: NÃO tocar.

## Passos
1. Histórico:
   - `self.undo_stack = []`, `self.redo_stack = []` (listas de cópias do mapa: `[row[:] for row in self.world_data]`), limite de 100 estados (descarta o mais antigo).
   - `_snapshot()`: empilha a cópia atual em `undo_stack` e limpa `redo_stack`.
   - Agrupar por "traço": um arrasto pintando/apagando vira UM passo. Guarde `self._stroke_active = False`; no primeiro quadro em que o botão esquerdo (pintar) ou direito (apagar) vai realmente MUDAR uma célula (valor diferente do atual), chame `_snapshot()` antes da mudança e ligue `_stroke_active`; quando os dois botões estiverem soltos, desligue. Não empilhe nada se o clique não mudou nenhuma célula.
   - Modo Mover: `_snapshot()` no momento em que pega o tile (antes de tirar da origem); se o arrasto for cancelado (`_cancel_drag`), descarte esse snapshot (`undo_stack.pop()`), pois nada mudou.
   - `undo()`: se houver, cancela arrasto, empilha o estado atual em `redo_stack`, restaura o topo de `undo_stack`, limpa `self._castle_cache`, notificação "Desfeito". `redo()`: o contrário, notificação "Refeito". Sem histórico: notificação "Nada para desfazer" / "Nada para refazer".
   - Ao carregar outra fase (setas cima/baixo e botão Carregar): limpar as duas pilhas.
2. Atalhos em `handle_event` (KEYDOWN): Ctrl+Z = `undo()`; Ctrl+Y ou Ctrl+Shift+Z = `redo()` (use `event.mod & pygame.KMOD_CTRL` / `KMOD_SHIFT`). Atenção: Shift sozinho hoje acelera a rolagem; com Ctrl junto não deve atrapalhar.
3. Botões "Desfazer" e "Refazer" no painel inferior, mesmo estilo do "Mover (M)", em lugar livre (confira posições de `back_button`, `save_button`, `load_button`, botão Mover e do texto `info_x`; não sobrepor). Cinza mais escuro quando a pilha correspondente estiver vazia. Atualizar o texto de dica para incluir "Ctrl+Z/Ctrl+Y: Desfazer/Refazer" (se não couber numa linha, quebre em duas, com `self.font_small`).
4. Paleta com castelo: em `_init_tile_images`, depois de montar a lista, trocar `self.img_list[20]` pela imagem de `Castle(1, pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)).image` e `self.img_list[41]` por `Castle(3, ...).image` (importe `Castle` de `entities.castle`, já importado no arquivo). MAS o mapa e o resto do editor usam `self.img_list[20/41]` para desenhar/medir a saída em fases sem tema: guarde as imagens originais em `self._exit_tile_imgs = {20: original, 41: original}` e use essas originais em `_draw_tiles`/no cálculo da porta do castelo; só a PALETA usa o castelo. Se for mais simples, mantenha `self.img_list` intacta e troque apenas a imagem passada para o `button.Button` dos ids 20 e 41 em `_init_palette_buttons` — essa é a forma preferida.

## O que NÃO fazer
- Não mudar salvar/carregar, formato do CSV, Modo Mover (além do snapshot), nem a lógica do castelo no mapa.
- Não tocar em outros arquivos. Não rodar comandos nem fazer commit.

## Verificação (eu rodo)
- `python -m py_compile ui/screens/level_editor.py`; captura do editor.

## Critério de pronto
Ctrl+Z/Ctrl+Y e os botões desfazem/refazem pintar, apagar e mover (um arrasto = um passo); a paleta mostra o castelo nos ids 20 e 41.
