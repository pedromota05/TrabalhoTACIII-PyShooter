"""
core/music.py — Música de fundo por tela/fase e vinhetas curtas.

Arquivos em audio/musicas/ (CC0, MintoDog; créditos em audio/CREDITOS.md).
O Game chama MusicPlayer.update(game) a cada quadro: ele descobre qual
música combina com o estado e a fase atuais e só troca quando muda, com
fade. O volume vem de game.music_vol (0 a 12), ajustado em Opções.
Cada computador toca a sua música localmente (nada vai pela rede).
"""

import os

import pygame

from game_state import GameState

_PASTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'audio', 'musicas')


def _arq(nome: str) -> str:
    return os.path.join(_PASTA, nome)


MENU = _arq('menu_titulo.ogg')
FASES = {
    1: _arq('fase1_floresta.ogg'),
    2: _arq('fase2_pantano.ogg'),
    3: _arq('fase3_neve.ogg'),
    4: _arq('fase4_chefe.ogg'),
    5: _arq('fase5_desafio_hordas.ogg'),
}
CHEFE_CLIMAX = _arq('fase4_chefe_climax.ogg')
GAME_OVER_VINHETA = _arq('gameover_vinheta.ogg')
GAME_OVER_LOOP = _arq('gameover_loop.ogg')
VITORIA = _arq('vitoria_final.ogg')
VINHETA_PERDEU_VIDA = _arq('vinheta_perdeu_vida.ogg')
VINHETA_FASE_CONCLUIDA = _arq('vinheta_fase_concluida_curta.ogg')

# Telas de menu: todas tocam a música do título (sem reiniciar ao trocar entre elas).
_ESTADOS_MENU = {
    GameState.MENU, GameState.INSTRUCTIONS, GameState.LEVEL_SELECT,
    GameState.MULTIPLAYER_MENU, GameState.EDITOR,
}
FADE_MS = 800


class MusicPlayer:
    """Escolhe e toca a música de fundo; toca vinhetas como efeito sonoro."""

    def __init__(self):
        self.atual = None          # caminho da música carregada em mixer.music
        self.vinheta_go = False    # tocando a vinheta do game over (depois vem o loop)
        self._vinhetas = {}
        self._estado_ant = None
        self._vida_ant = 0
        for chave, caminho in (('perdeu_vida', VINHETA_PERDEU_VIDA),
                               ('fase_concluida', VINHETA_FASE_CONCLUIDA)):
            try:
                self._vinhetas[chave] = pygame.mixer.Sound(caminho)
            except (pygame.error, FileNotFoundError):
                pass  # sem mixer ou sem arquivo: segue sem a vinheta

    # ------------------------------------------------------------------
    def _volume(self, game) -> float:
        return max(0, min(getattr(game, 'music_vol', 12), 12)) / 12.0

    def tocar(self, caminho: str, game, loops: int = -1, fade_ms: int = FADE_MS) -> None:
        """Toca `caminho` em loop com fade. Não reinicia se já é a música atual."""
        if caminho == self.atual:
            return
        self.atual = caminho
        try:
            pygame.mixer.music.load(caminho)
            pygame.mixer.music.set_volume(self._volume(game))
            pygame.mixer.music.play(loops, 0.0, fade_ms)
        except pygame.error:
            pass  # mixer indisponível (ex.: sem placa de som): jogo segue mudo

    def vinheta(self, chave: str, game) -> None:
        som = self._vinhetas.get(chave)
        if som is None:
            return
        som.set_volume(self._volume(game))
        som.play()

    # ------------------------------------------------------------------
    def musica_da_fase(self, game) -> str:
        fase = getattr(game, 'level', 1)
        if getattr(game, 'challenge_mode', False) and fase == 5:
            return FASES[5]
        if fase == 4 and getattr(game, 'boss_stage', 1) >= 2:
            return CHEFE_CLIMAX
        return FASES.get(fase, FASES[1])

    def desejada(self, game):
        """Música que combina com o estado atual (None = manter a que está)."""
        estado = game.state
        if estado in _ESTADOS_MENU:
            return MENU
        if estado == GameState.OPTIONS:
            # Opções abertas pela pausa mantêm a música da fase.
            return None if game.previous_state == GameState.PAUSE else MENU
        if estado in (GameState.PLAYING, GameState.LEVEL_TRANSITION):
            return self.musica_da_fase(game)
        if estado == GameState.VICTORY:
            return VITORIA
        return None  # PAUSE, GAME_OVER (tratado à parte)

    def update(self, game) -> None:
        """Chamado a cada quadro pelo game loop."""
        estado = game.state
        mudou = estado != self._estado_ant

        # Vinhetas: fase concluída (PLAYING -> LEVEL_TRANSITION) e vida perdida.
        if mudou and estado == GameState.LEVEL_TRANSITION and self._estado_ant == GameState.PLAYING:
            self.vinheta('fase_concluida', game)
        vida = getattr(game, 'life_lost_frames', 0)
        if vida > self._vida_ant and estado == GameState.PLAYING:
            self.vinheta('perdeu_vida', game)
        self._vida_ant = vida
        self._estado_ant = estado

        if estado == GameState.GAME_OVER:
            if mudou:
                self.vinheta_go = False
                if self.atual not in (GAME_OVER_VINHETA, GAME_OVER_LOOP):
                    self.tocar(GAME_OVER_VINHETA, game, loops=0, fade_ms=0)
                    self.vinheta_go = True
            elif self.vinheta_go and not pygame.mixer.music.get_busy():
                self.vinheta_go = False
                self.tocar(GAME_OVER_LOOP, game)
            return

        caminho = self.desejada(game)
        if caminho is not None:
            self.vinheta_go = False
            self.tocar(caminho, game)
