"""Tratamento dos eventos de entrada da sessão."""

import pygame

from game_state import GameState


def handle_events(game) -> None:
    """Atualiza o estado de entrada e as transições acionadas por teclado."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game.running = False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_a, pygame.K_LEFT):
                game.moving_left = True
            if event.key in (pygame.K_d, pygame.K_RIGHT):
                game.moving_right = True
            if event.key == pygame.K_SPACE:
                game.shoot = True
            if event.key in (pygame.K_q, pygame.K_g):
                game.grenade_input = True
            if event.key in (pygame.K_w, pygame.K_UP) and game.player and game.player.alive:
                game.player.jump = True
                game.assets.get_sound('jump').play()
            if event.key == pygame.K_ESCAPE:
                if game.state in (GameState.INSTRUCTIONS, GameState.LEVEL_SELECT):
                    game.state = GameState.MENU
                elif game.state == GameState.OPTIONS:
                    game.state = game.previous_state if game.previous_state else GameState.MENU
                elif game.state == GameState.PLAYING:
                    game.state = GameState.PAUSE
                elif game.state == GameState.PAUSE:
                    game.state = GameState.PLAYING
                else:
                    game.running = False

        if event.type == pygame.KEYUP:
            if event.key in (pygame.K_a, pygame.K_LEFT):
                game.moving_left = False
            if event.key in (pygame.K_d, pygame.K_RIGHT):
                game.moving_right = False
            if event.key == pygame.K_SPACE:
                game.shoot = False
            if event.key in (pygame.K_q, pygame.K_g):
                game.grenade_input = False
                game.grenade_thrown = False
