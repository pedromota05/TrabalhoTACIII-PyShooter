"""entities/sign.py — Placa de madeira interativa (tecla E mostra uma dica)."""
from entities.environment import Decoration


class Sign(Decoration):
    """Decoração com texto; o texto é definido em load_level pela ordem no mapa."""

    def __init__(self, img, x: int, y: int):
        super().__init__(img, x, y)
        self.text = ''
