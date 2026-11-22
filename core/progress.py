"""
core/progress.py — Progresso salvo do jogador (fases concluídas, campanha e recorde).

Grava em save/progresso.json. Toda leitura e gravação é protegida: se o
arquivo não existir, estiver corrompido ou não puder ser gravado, o jogo
continua com o progresso vazio em vez de travar.

A variável de ambiente PYSHOOTER_SAVE troca o caminho do arquivo (usada
pelo bot de testes para não mexer no progresso real).
"""

import json
import os

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_PATH = os.environ.get('PYSHOOTER_SAVE', os.path.join(_RAIZ, 'save', 'progresso.json'))

_cache = {'mtime': None, 'dados': None}


def _vazio() -> dict:
    return {'fases_concluidas': [], 'campanha_zerada': False, 'recorde_desafio': None, 'cor_jogador': 0}


def carregar() -> dict:
    """Devolve o progresso salvo. Relê o arquivo só quando ele muda no disco."""
    try:
        mtime = os.path.getmtime(SAVE_PATH)
    except OSError:
        return _vazio()
    if _cache['mtime'] == mtime and _cache['dados'] is not None:
        return dict(_cache['dados'])
    try:
        with open(SAVE_PATH, encoding='utf-8') as f:
            lido = json.load(f)
        dados = _vazio()
        dados['fases_concluidas'] = sorted({int(n) for n in lido.get('fases_concluidas', [])})
        dados['campanha_zerada'] = bool(lido.get('campanha_zerada', False))
        recorde = lido.get('recorde_desafio')
        dados['recorde_desafio'] = float(recorde) if recorde is not None else None
        dados['cor_jogador'] = int(lido.get('cor_jogador', 0))
    except (OSError, ValueError, TypeError, AttributeError):
        dados = _vazio()
    _cache['mtime'], _cache['dados'] = mtime, dados
    return dict(dados)


def _salvar(dados: dict) -> None:
    try:
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        with open(SAVE_PATH, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=1)
    except OSError:
        pass  # sem permissão de gravação: o jogo segue sem salvar
    _cache['mtime'] = None


def marcar_fase(numero: int) -> None:
    """Registra a fase como concluída."""
    dados = carregar()
    if numero not in dados['fases_concluidas']:
        dados['fases_concluidas'] = sorted(dados['fases_concluidas'] + [numero])
        _salvar(dados)


def marcar_campanha_zerada() -> None:
    """Registra que a campanha foi concluída (libera o Modo Desafio)."""
    dados = carregar()
    if not dados['campanha_zerada']:
        dados['campanha_zerada'] = True
        _salvar(dados)


def salvar_cor(indice: int) -> None:
    """Registra a cor do soldado escolhida pelo jogador."""
    dados = carregar()
    dados['cor_jogador'] = int(indice)
    _salvar(dados)


def registrar_tempo_desafio(segundos: float) -> bool:
    """Guarda o tempo se for o melhor. Devolve True quando é um novo recorde."""
    dados = carregar()
    recorde = dados['recorde_desafio']
    if recorde is not None and segundos >= recorde:
        return False
    dados['recorde_desafio'] = round(segundos, 1)
    _salvar(dados)
    return True
