"""
level-editor.py — Launcher executável do Editor de Fases do PyShooter.

Refatorado para utilizar a classe modular LevelEditorScreen de ui/screens/level_editor.py,
mantendo 100% de compatibilidade para execução direta via linha de comando.
"""

import sys
import pygame
from asset_manager import AssetManager
from ui.screens.level_editor import LevelEditorScreen, EDITOR_TOTAL_WIDTH, EDITOR_TOTAL_HEIGHT


class EditorStandaloneRunner:
    """Ambiente de execução autônomo para o LevelEditorScreen."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.state = "editor"
        self.running = True


def main() -> None:
    """Ponto de entrada para execução avulsa do editor de fases."""
    pygame.init()
    screen = pygame.display.set_mode((EDITOR_TOTAL_WIDTH, EDITOR_TOTAL_HEIGHT))
    pygame.display.set_caption('PyShooter - Level Editor')
    clock = pygame.time.Clock()

    assets = AssetManager()
    assets.load_all()

    editor = LevelEditorScreen(assets)
    runner = EditorStandaloneRunner(screen)
    editor.on_enter(runner)

    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            editor.handle_event(event, runner)

        if runner.state != "editor":
            running = False

        editor.update(runner.screen, runner)
        import button
        button.Button.update_cursor()
        pygame.display.update()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
