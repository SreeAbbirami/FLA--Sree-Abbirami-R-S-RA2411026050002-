"""Random finite-automaton generator.

A genuinely unique feature: generates a random DFA or NFA with a
configurable number of states, alphabet size, and transition density.
Useful for quick experimentation, testing, and classroom demos.
"""
from __future__ import annotations

import math
import random
from typing import List, Optional

from models.automaton import EPSILON, Automaton


def _state_name(index: int) -> str:
    """Name states q0, q1, ... for readability."""
    return f"q{index}"


def _circular_positions(n: int, cx: float = 400.0, cy: float = 250.0,
                        radius: float = 180.0) -> dict:
    """Place states evenly on a circle so the canvas looks clean."""
    positions = {}
    for i in range(n):
        angle = 2 * math.pi * i / n - math.pi / 2
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        positions[_state_name(i)] = (round(x, 1), round(y, 1))
    return positions


def generate_random_dfa(
    num_states: int = 5,
    alphabet: Optional[List[str]] = None,
    density: float = 1.0,
    accept_ratio: float = 0.4,
    seed: Optional[int] = None,
) -> Automaton:
    """Generate a random *complete* DFA.

    density in (0, 1]: probability that a (state, symbol) transition
    targets a *different* state than the current one. With density=1
    every transition is randomised; with lower density transitions
    tend to self-loop, keeping the automaton sparse.
    """
    if num_states < 1:
        raise ValueError("num_states must be >= 1")
    if not 0 < density <= 1:
        raise ValueError("density must be in (0, 1]")
    if not 0 <= accept_ratio <= 1:
        raise ValueError("accept_ratio must be in [0, 1]")

    alphabet = alphabet or ["a", "b"]
    rng = random.Random(seed)

    aut = Automaton(name=f"Random DFA ({num_states} states)")
    states = [_state_name(i) for i in range(num_states)]
    for s in states:
        aut.add_state(s, position=_circular_positions(num_states)[s])
    aut.start_state = states[0]

    # accept states: a random subset of the requested size
    num_accept = max(1, int(round(num_states * accept_ratio)))
    for s in rng.sample(states, k=min(num_accept, num_states)):
        aut.toggle_accept_state(s)

    for src in states:
        aut.transitions[src] = {}
        for sym in alphabet:
            if sym not in aut.alphabet:
                aut.alphabet.append(sym)
            if rng.random() < density and num_states > 1:
                target = rng.choice([s for s in states if s != src])
            else:
                target = src
            aut.transitions[src][sym] = {target}

    return aut


def generate_random_nfa(
    num_states: int = 5,
    alphabet: Optional[List[str]] = None,
    density: float = 0.6,
    epsilon_prob: float = 0.15,
    accept_ratio: float = 0.4,
    nondeterminism: float = 0.3,
    seed: Optional[int] = None,
) -> Automaton:
    """Generate a random NFA (possibly with ε-transitions).

    nondeterminism: probability that a transition fans out to 2+ targets.
    epsilon_prob: probability per state of having at least one ε-transition.
    """
    if num_states < 1:
        raise ValueError("num_states must be >= 1")
    if not 0 < density <= 1:
        raise ValueError("density must be in (0, 1]")
    if not 0 <= epsilon_prob <= 1:
        raise ValueError("epsilon_prob must be in [0, 1]")
    if not 0 <= nondeterminism <= 1:
        raise ValueError("nondeterminism must be in [0, 1]")

    alphabet = alphabet or ["a", "b"]
    rng = random.Random(seed)

    aut = Automaton(name=f"Random NFA ({num_states} states)")
    states = [_state_name(i) for i in range(num_states)]
    positions = _circular_positions(num_states)
    for s in states:
        aut.add_state(s, position=positions[s])
    aut.start_state = states[0]

    num_accept = max(1, int(round(num_states * accept_ratio)))
    for s in rng.sample(states, k=min(num_accept, num_states)):
        aut.toggle_accept_state(s)

    for sym in alphabet:
        if sym not in aut.alphabet:
            aut.alphabet.append(sym)

    for src in states:
        aut.transitions[src] = {}
        for sym in alphabet:
            if rng.random() < density:
                targets = {rng.choice(states)}
                while rng.random() < nondeterminism and len(targets) < num_states:
                    targets.add(rng.choice(states))
                aut.transitions[src][sym] = targets
        # optional epsilon transitions
        if rng.random() < epsilon_prob:
            targets = {rng.choice(states)}
            while rng.random() < nondeterminism / 2 and len(targets) < num_states:
                targets.add(rng.choice(states))
            aut.transitions[src][EPSILON] = targets
            if EPSILON not in aut.alphabet:
                aut.alphabet.append(EPSILON)

    return aut
