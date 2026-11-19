"""
tools/bot_fases.py — Bot headless que joga as fases do PyShooter para teste.

O bot planeja o caminho até a saída com A*, usando a MESMA colisão do Player
(Character._check_tile_collisions), e joga o loop real do jogo
(update_playing), atirando nos inimigos que estiverem à frente.

Uso (na raiz do projeto):
    python tools/bot_fases.py 1               # joga a fase 1 uma vez
    python tools/bot_fases.py 1 2 3 4         # várias fases
    python tools/bot_fases.py todas --humano 30
        # 30 tentativas por fase com ruído no controle (simula uma pessoa):
        # mostra taxa de sucesso e o mapa de mortes por trecho da fase.
    Opções: --god (invencível), --max-seg N, --seed N, --checkpoint
        (--checkpoint: ao morrer, renasce no checkpoint e continua)
"""

import heapq
import itertools
import json
import os
import random
import sys
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.chdir(RAIZ)
sys.path.insert(0, RAIZ)

import pygame  # noqa: E402

# Relógio determinístico: 1 quadro = 1/60 s, independente da velocidade da CPU.
FRAME = [0]
pygame.time.get_ticks = lambda: int(FRAME[0] * 1000 / 60)

from config import (  # noqa: E402
    GRAVITY, TERMINAL_VELOCITY, JUMP_VELOCITY, SCREEN_HEIGHT, TILE_SIZE,
)
from entities.player import Player  # noqa: E402
from game_state import GameState  # noqa: E402

MACRO = 6
ACOES = [(l, r, j) for j in (False, True)
         for (l, r) in ((False, True), (True, False), (False, False))]
PARADO = (False, False, False)


class Mapa:
    """Geometria da fase em coordenadas de mundo + simulação da física do Player."""

    def __init__(self, game):
        off = game.bg_scroll
        self.obst = [(None, t[1].move(off, 0)) for t in game.world.obstacle_list]
        self.ramps = [(None, t[1].move(off, 0)) for t in game.world.ramp_list]
        self.aguas = [w.rect.move(off, 0) for w in game.water_group]
        self.saidas = [e.rect.move(off, 0) for e in game.exit_group]
        self.por_coluna = {}
        for t in self.obst:
            for k in range(t[1].left // TILE_SIZE, t[1].right // TILE_SIZE + 1):
                self.por_coluna.setdefault(k, []).append(t)
        self.sim = Player(0, 0)
        self.largura = self.sim.rect.width

    def passo(self, s, left, right):
        """Replica Player.move. s = (x, y, vel_y, in_air, jump, speed)."""
        x, y, vy, in_air, jump, speed = s
        sim = self.sim
        sim.rect.x, sim.rect.y = x, y
        sim.vel_y, sim.in_air = vy, in_air
        dx = (-speed if left else 0) + (speed if right else 0)
        if sim.in_air:
            dx = int(dx * 0.7)
        if jump and not sim.in_air:
            sim.vel_y = JUMP_VELOCITY
            jump = False
            sim.in_air = True
        sim.vel_y = min(sim.vel_y + GRAVITY, TERMINAL_VELOCITY)
        c = x // TILE_SIZE
        perto = [t for k in range(c - 2, c + 5) for t in self.por_coluna.get(k, ())]
        dx, dy = sim._check_tile_collisions(dx, sim.vel_y, perto, self.ramps)
        morto = sim.rect.bottom > SCREEN_HEIGHT or any(
            w.colliderect(sim.rect) and sim.rect.centery > w.top for w in self.aguas)
        venceu = any(e.colliderect(sim.rect) for e in self.saidas)
        if sim.rect.left + dx < 0:
            dx = 0
        sim.rect.x += dx
        sim.rect.y += dy
        return (sim.rect.x, sim.rect.y, sim.vel_y, sim.in_air, jump, speed), morto, venceu

    def planejar(self, s0, alvo_x, max_nos=250000, alcance=None):
        """A* sobre macro-ações. Sem `alcance`, o objetivo é tocar a saída."""
        cont = itertools.count()
        h = lambda s: abs(alvo_x - (s[0] + self.largura / 2)) / 5
        aberta = [(h(s0), 0, next(cont), s0, None)]
        vistos, pais, nos = {}, {}, 0
        while aberta and nos < max_nos:
            _, custo, _, s, pid = heapq.heappop(aberta)
            nos += 1
            for a in ACOES:
                l, r, j = a
                st = (s[0], s[1], s[2], s[3], s[4] or j, s[5])
                morto = venceu = False
                for _ in range(MACRO):
                    st, morto, venceu = self.passo(st, l, r)
                    if morto or venceu:
                        break
                if morto:
                    continue
                nid = next(cont)
                pais[nid] = (pid, a)
                if alcance is not None:
                    venceu = (abs(st[0] + self.largura / 2 - alvo_x) <= alcance
                              and not st[3] and st[2] == 0)
                if venceu:
                    caminho, k = [], nid
                    while k is not None:
                        k, a2 = pais[k]
                        caminho.append(a2)
                    return caminho[::-1], nos
                chave = (st[0] // 4, st[1] // 4, round(st[2]), st[3], st[4])
                ng = custo + 1 + (0.2 if j else 0)
                if vistos.get(chave, 1e9) <= ng:
                    continue
                vistos[chave] = ng
                heapq.heappush(aberta, (ng + h(st), ng, nid, st, nid))
        return None, nos


class Bot:
    """Decide as entradas (game.moving_left/right, jump, shoot, granada) a cada quadro."""

    def __init__(self, game, humano=False, rng=None):
        self.g = game
        self.humano = humano
        self.rng = rng or random.Random(0)
        self.mapa = None
        self.mundo = None
        self.caminho = []
        self.esperado = None
        self.tempo_luta = 0
        self.atual = PARADO
        self.pulo_em = None      # quadro em que o pulo (atrasado) será apertado
        self.hesitar = 0

    # ---------------- utilidades ----------------
    def estado(self):
        p = self.g.player
        return (p.rect.x + self.g.bg_scroll, p.rect.y, p.vel_y, p.in_air, p.jump, p.speed)

    def _inimigo_a_frente(self, alcance=550):
        p = self.g.player
        for grp in (self.g.enemy_group, self.g.boss_group):
            for e in grp:
                if not e.alive:
                    continue
                dx = (e.rect.centerx - p.rect.centerx) * p.direction
                if 0 < dx < alcance and abs(e.rect.centery - p.rect.centery) < 60:
                    return e
        return None

    def _chefes_vivos(self):
        return [b for b in self.g.boss_group if b.alive]

    # ---------------- decisão ----------------
    def tick(self):
        """Chamar uma vez por quadro, ANTES de game._update_playing()."""
        g = self.g
        if g.world is not self.mundo:          # nova fase / renascimento
            self.mundo = g.world
            self.mapa = Mapa(g)
            self.caminho, self.esperado = [], None
        f = FRAME[0]
        s = self.estado()
        saida_x = self.mapa.saidas[0].centerx if self.mapa.saidas else None

        if self.pulo_em is not None and f >= self.pulo_em:
            g.player.jump = True
            self.pulo_em = None

        if f % MACRO != 1 and self.caminho:
            return
        alvo = self._inimigo_a_frente()
        no_chao = (not g.player.in_air) and g.player.vel_y == 0
        if (alvo is not None and no_chao and g.player.ammo > 0
                and self.tempo_luta < 240 and saida_x is not None):
            self.atual = PARADO
            self.tempo_luta += MACRO
            g.shoot = True
            self.caminho = []
        else:
            if alvo is None:
                self.tempo_luta = 0
            g.shoot = alvo is not None and g.player.ammo > 0
            if self.esperado is not None and (abs(s[0] - self.esperado[0]) > 2
                                              or abs(s[1] - self.esperado[1]) > 2):
                self.caminho = []
            if saida_x is None and f % 30 == 1:
                self.caminho = []
            if not self.caminho:
                if saida_x is not None:
                    caminho, _ = self.mapa.planejar(s, saida_x)
                else:
                    caminho = self._caminho_chefe(s, no_chao)
                self.caminho = caminho or [PARADO]
            self.atual = self.caminho.pop(0)
            st = (s[0], s[1], s[2], s[3], s[4] or self.atual[2], s[5])
            for _ in range(MACRO):
                st, _, _ = self.mapa.passo(st, self.atual[0], self.atual[1])
            self.esperado = st

        l, r, j = self.atual
        if self.humano:
            # Hesitação ocasional e pulo com atraso de 0 a 6 quadros.
            if self.rng.random() < 0.08:
                l = r = False
            if j:
                self.pulo_em = f + self.rng.randint(0, 6)
                j = False
        g.moving_left, g.moving_right = l, r
        if j:
            g.player.jump = True

        chefes = self._chefes_vivos()
        perto = any(abs(b.rect.centerx - g.player.rect.centerx) < 280 for b in chefes)
        if chefes and g.player.grenades > 0 and perto:
            g.grenade_input, g.grenade_thrown = True, False
        else:
            g.grenade_input = False
        if saida_x is None and chefes:
            b = min(chefes, key=lambda b: abs(b.rect.centerx - g.player.rect.centerx))
            g.player.direction = 1 if b.rect.centerx > g.player.rect.centerx else -1
            g.player.flip = g.player.direction == -1
            mira = 15 if self.humano else 5
            g.shoot = (g.player.ammo > 0
                       and b.rect.top < g.player.rect.centery - mira < b.rect.bottom)

    def _caminho_chefe(self, s, no_chao):
        chefes = self._chefes_vivos()
        if not chefes:
            return [PARADO]
        b = min(chefes, key=lambda b: abs(b.rect.centerx - self.g.player.rect.centerx))
        bx = b.rect.centerx + self.g.bg_scroll
        px = s[0] + self.mapa.largura / 2
        alvo = bx + (-1 if px < bx else 1) * 230
        if abs(px - alvo) < 40 and no_chao:
            return [PARADO]
        caminho, _ = self.mapa.planejar(s, alvo, max_nos=4000, alcance=30)
        return caminho[:4] if caminho else [PARADO]


def causa_morte(game):
    p = game.player
    if p.rect.bottom > SCREEN_HEIGHT - 5:
        return 'queda'
    if any(w.rect.colliderect(p.rect) for w in game.water_group):
        return 'agua'
    vivos = [e for grp in (game.enemy_group, game.boss_group) for e in grp if e.alive]
    if vivos:
        e = min(vivos, key=lambda e: abs(e.rect.centerx - p.rect.centerx))
        return type(e).__name__
    return 'outro'


def novo_jogo():
    from game import Game
    return Game()


def jogar_fase(game, fase, humano=False, seed=0, god=False, max_seg=240,
               checkpoint=False):
    """Joga uma fase do início. Retorna dict com resultado e eventos."""
    random.seed(seed)  # IA dos inimigos usa `random`: semente torna o teste reproduzível
    game.level = fase
    game.bg_scroll = 0
    game.start_intro = False
    if hasattr(game, 'reset_run_state'):
        game.reset_run_state()
    game._load_level(fase)
    game.state = GameState.PLAYING
    bot = Bot(game, humano=humano, rng=random.Random(seed))
    inicio = FRAME[0]
    mortes = []
    resultado = 'tempo_esgotado'
    while FRAME[0] - inicio < max_seg * 60:
        FRAME[0] += 1
        if god:
            game.player.health = 100
        bot.tick()
        game._update_playing()
        pygame.event.pump()
        if game.state == GameState.GAME_OVER:
            x = game.player.rect.centerx + game.bg_scroll
            mortes.append((x, causa_morte(game)))
            if checkpoint and getattr(game, 'checkpoint', None):
                from core.level_loader import respawn
                respawn(game)
                game.state = GameState.PLAYING
                continue
            resultado = 'morreu'
            break
        if game.state.name in ('LEVEL_TRANSITION', 'VICTORY'):
            resultado = 'passou'
            break
    return {
        'fase': fase, 'resultado': resultado,
        'segundos': round((FRAME[0] - inicio) / 60, 1),
        'vida': game.player.health, 'municao': game.player.ammo,
        'mortes': mortes, 'estado_final': game.state.name,
    }


def main(argv):
    fases = []
    for i, a in enumerate(argv):
        if a == 'todas':
            fases = [1, 2, 3, 4]
        elif a.isdigit() and not fases_opcao(argv, i):
            fases.append(int(a))
    opt = lambda nome, pad: (type(pad)(argv[argv.index(nome) + 1])
                             if nome in argv else pad)
    humano_n = opt('--humano', 0)
    seed = opt('--seed', 0)
    max_seg = opt('--max-seg', 240)
    god = '--god' in argv
    cp = '--checkpoint' in argv
    game = novo_jogo()
    saida = []
    for fase in fases or [1]:
        if humano_n:
            res = [jogar_fase(game, fase, True, seed + i, god, max_seg, cp)
                   for i in range(humano_n)]
            ok = sum(r['resultado'] == 'passou' for r in res)
            mortes = [m for r in res for m in r['mortes']]
            trechos = Counter((x // 400 * 400, c) for x, c in mortes)
            saida.append({
                'fase': fase, 'tentativas': humano_n,
                'sucesso_%': round(100 * ok / humano_n),
                'mortes_por_trecho': {f'x{k[0]}-{k[0] + 399} {k[1]}': v
                                      for k, v in trechos.most_common()},
                'tempo_medio_s': round(sum(r['segundos'] for r in res
                                           if r['resultado'] == 'passou') / max(ok, 1), 1),
            })
        else:
            saida.append(jogar_fase(game, fase, False, seed, god, max_seg, cp))
    print(json.dumps(saida, ensure_ascii=False, indent=1))


def fases_opcao(argv, i):
    """True se argv[i] é o valor de uma opção (ex.: o '30' de '--humano 30')."""
    return i > 0 and argv[i - 1] in ('--humano', '--seed', '--max-seg')


if __name__ == '__main__':
    main(sys.argv[1:])
