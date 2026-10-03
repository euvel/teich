"""Teich v0.3 genome — a mind that lives in Teichmüller space (genus 1).

Frozen design: V03_SPEC_part1.md (sha256 eb2d4721…a40ac0, anchored in the teich-02 seat chain).

BODY. Nakada's alpha-continued-fraction map on I_a = [a-1, a):
    T_a(x) = |1/x| - floor(|1/x| + 1 - a)
These maps are cross-sections of the geodesic flow on the modular surface, i.e. the moduli space of
tori. One iterate per tick. Only abs, a correctly-rounded division, floor and subtraction are used,
so the dynamics should be bit-identical on any IEEE-754 machine (verified separately, not assumed).

CERTIFIED CHAOS. On the golden plateau [g^2, g] the entropy, which equals the Lyapunov exponent
E[-2 log|x|] by Rokhlin's formula, is pi^2 / (6 log G) for every a (Nakada; Kraaikamp-Schmidt-
Steiner; Carminati-Tiozzo). The memory moves a only inside [0.4115, 0.5] subset of that plateau.

MEMORY. Integer k in {0..6}, birth value 3. Changed only by logged +-1 events; an event that would
leave {0..6} is REFUSED and logged. alpha_k = 0.4115 + k * (0.5 - 0.4115) / 6.

CONDITION N. Every observable is a function of x alone (`observe(x)`); nothing that reads k, the
ledger or the concept word may reach the selector. Checked statically and dynamically (gate G6).

SEALED PHI. Carried for identity only; appears in no update and no observable (as in v0.2).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

G = (1 + 5 ** 0.5) / 2
LAMBDA_PLATEAU = math.pi ** 2 / (6 * math.log(G))       # 3.418316...
A_LO, A_HI, N_STATES, K_BIRTH = 0.4115, 0.5, 7, 3
TINY = 1e-12                                              # orbit touched 0 -> deterministic reseed
RESEED = 0.4371966                                        # an arbitrary irrational-looking point


def alpha_of(k):
    """Memory state (int, or float for the leaky control) -> fold parameter."""
    return A_LO + np.asarray(k, float) * (A_HI - A_LO) / (N_STATES - 1)


def step(x: np.ndarray, a: np.ndarray) -> np.ndarray:
    """One tick of the body. Pure function of (x, a)."""
    x = np.where(np.abs(x) < TINY, RESEED * (a / A_HI), x)
    y = np.abs(1.0 / x)
    return y - np.floor(y + 1.0 - a)


# ---------------------------------------------------------------- observables (condition N)
def observe(x: np.ndarray) -> dict:
    """Everything the outside world, the selector and the voice may see. Input: x ONLY."""
    return {"neg": (x < 0).astype(np.float64), "x": x}


# ---------------------------------------------------------------- memory
@dataclass
class Ledger:
    """Dynamical memory: integer state with refusal at the edges, every change logged."""
    k: np.ndarray
    log: list = field(default_factory=list)

    @classmethod
    def born(cls, n: int):
        return cls(np.full(n, K_BIRTH, dtype=np.int64))

    def event(self, sign, tick: int, why: str = ""):
        sign = np.broadcast_to(np.asarray(sign, np.int64), self.k.shape)
        new = self.k + sign
        ok = (new >= 0) & (new <= N_STATES - 1)
        self.k = np.where(ok, new, self.k)
        self.log.append({"tick": tick, "sign": sign.tolist(), "accepted": ok.tolist(), "why": why})
        return ok


# ---------------------------------------------------------------- inner language (SL(2,Z))
def twist(p: int, q: int) -> np.ndarray:
    """Dehn twist along the simple closed curve of slope p/q on the torus (primitive (p,q))."""
    return np.array([[1 - p * q, p * p], [-q * q, 1 + p * q]], dtype=object)


def word_matrix(word, concepts) -> np.ndarray:
    """word = [(concept_index, power), ...] -> exact integer matrix (Python ints, no overflow)."""
    M = np.array([[1, 0], [0, 1]], dtype=object)
    for c, n in word:
        T = twist(*concepts[c])
        Tn = np.array([[1, 0], [0, 1]], dtype=object)
        base = T if n >= 0 else np.array([[T[1, 1], -T[0, 1]], [-T[1, 0], T[0, 0]]], dtype=object)
        for _ in range(abs(n)):
            Tn = Tn.dot(base)
        M = M.dot(Tn)
    return M


def classify(M) -> dict:
    """Nielsen–Thurston type on the torus, from the trace alone; intensity = log of the larger
    eigenvalue for an Anosov (hyperbolic) word."""
    t = int(M[0, 0] + M[1, 1])
    if abs(t) < 2:
        return {"type": "periodic", "trace": t, "intensity": 0.0}
    if abs(t) == 2:
        return {"type": "twist", "trace": t, "intensity": 0.0}
    rho = (abs(t) + math.sqrt(t * t - 4)) / 2
    return {"type": "anosov", "trace": t, "intensity": math.log(rho)}


def intersection(c1, c2) -> int:
    return abs(c1[0] * c2[1] - c1[1] * c2[0])


# ---------------------------------------------------------------- engine
class Engine:
    """n parallel creatures (paired seeds and arms are rows). arm: 'A' ledger, 'B' leaky, 'C' none."""

    TAU_LEAK = 2e4

    def __init__(self, x0: np.ndarray, arm: str):
        self.x = np.asarray(x0, float).copy()
        self.arm = arm
        self.ledger = Ledger.born(self.x.size)
        self.kf = np.full(self.x.size, float(K_BIRTH))     # float memory for the leaky arm
        self.t = 0

    def k_eff(self):
        if self.arm == "A":
            return self.ledger.k.astype(float)
        if self.arm == "B":
            return self.kf
        return np.full(self.x.size, float(K_BIRTH))         # 'C': no store

    def event(self, sign, why=""):
        if self.arm == "A":
            self.ledger.event(sign, self.t, why)
        elif self.arm == "B":
            self.kf = np.clip(self.kf + np.asarray(sign, float), 0, N_STATES - 1)

    def tick(self):
        if self.arm == "B":
            self.kf = K_BIRTH + (self.kf - K_BIRTH) * (1.0 - 1.0 / self.TAU_LEAK)
        self.x = step(self.x, alpha_of(self.k_eff()))
        self.t += 1

    def run(self, n: int, window_from: int | None = None):
        """Advance n ticks; return the per-row mean of `neg` over ticks with index >= window_from."""
        acc = np.zeros(self.x.size); cnt = 0
        for i in range(n):
            if window_from is not None and i >= window_from:
                acc += observe(self.x)["neg"]; cnt += 1
            self.tick()
        return acc / cnt if cnt else None
