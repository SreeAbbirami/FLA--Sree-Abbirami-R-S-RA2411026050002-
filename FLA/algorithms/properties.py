"""Structural and language property analysis for an automaton."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from models.automaton import EPSILON, Automaton


@dataclass
class PropertiesReport:
    is_deterministic: bool
    is_complete: bool
    is_connected: bool
    has_epsilon_transitions: bool
    unreachable_states: Set[str] = field(default_factory=set)
    dead_states: Set[str] = field(default_factory=set)
    missing_transitions: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    is_empty: bool = False
    is_infinite: bool = False


def is_language_empty(automaton: Automaton) -> bool:
    """Return True if the language accepted by the automaton is empty (L = ∅)."""
    if automaton.start_state is None:
        return True
    reachable = automaton.get_reachable_states()
    return len(reachable & automaton.accept_states) == 0


def is_language_infinite(automaton: Automaton) -> bool:
    """Return True if the automaton accepts infinitely many strings (has a useful cycle)."""
    if automaton.start_state is None or is_language_empty(automaton):
        return False

    alive = set(automaton.states) - automaton.get_dead_states()
    reachable = automaton.get_reachable_states()
    useful = reachable & alive

    visited: Set[str] = set()
    rec_stack: Set[str] = set()

    def has_cycle(u: str) -> bool:
        visited.add(u)
        rec_stack.add(u)
        for sym, dests in automaton.transitions.get(u, {}).items():
            for v in dests:
                if v in useful:
                    if v not in visited:
                        if has_cycle(v):
                            return True
                    elif v in rec_stack:
                        return True
        rec_stack.remove(u)
        return False

    for st in useful:
        if st not in visited:
            if has_cycle(st):
                return True

    return False


def analyze(automaton: Automaton) -> PropertiesReport:
    unreachable = automaton.get_unreachable_states()
    dead = automaton.get_dead_states()
    missing: List[str] = []
    if automaton.alphabet:
        for state in automaton.states:
            for symbol in automaton.alphabet:
                if not automaton.targets(state, symbol):
                    missing.append(f"{state} --{symbol}--> (undefined)")

    return PropertiesReport(
        is_deterministic=automaton.is_deterministic(),
        is_complete=automaton.is_complete(),
        is_connected=len(unreachable) == 0,
        has_epsilon_transitions=automaton.has_epsilon_transitions(),
        unreachable_states=unreachable,
        dead_states=dead,
        missing_transitions=missing,
        validation_errors=automaton.validate(),
        is_empty=is_language_empty(automaton),
        is_infinite=is_language_infinite(automaton),
    )


# ----------------------------------------------------------------------
# Word-length distribution
# ----------------------------------------------------------------------
def _epsilon_closure_set(automaton: Automaton, states: Set[str]) -> Set[str]:
    """Return the ε-closure of a set of states."""
    stack = list(states)
    closure = set(states)
    while stack:
        u = stack.pop()
        for v in automaton.transitions.get(u, {}).get(EPSILON, set()):
            if v not in closure:
                closure.add(v)
                stack.append(v)
    return closure


def word_length_distribution(automaton: Automaton, max_length: int = 10) -> Dict[int, int]:
    """Count accepted strings of each length 0..max_length.

    Uses dynamic programming over the active set of states (NFA-style),
    so it works for both DFAs and NFAs (including ε-transitions).
    Returns {length: number_of_accepted_strings}.
    """
    result: Dict[int, int] = {}
    if automaton.start_state is None:
        return {n: 0 for n in range(max_length + 1)}

    alphabet = [s for s in automaton.alphabet if s != EPSILON]
    if not alphabet:
        # no real symbols: only the empty string can be accepted
        start_closure = _epsilon_closure_set(automaton, {automaton.start_state})
        result[0] = 1 if (start_closure & automaton.accept_states) else 0
        for n in range(1, max_length + 1):
            result[n] = 0
        return result

    active = _epsilon_closure_set(automaton, {automaton.start_state})
    result[0] = 1 if (active & automaton.accept_states) else 0

    for length in range(1, max_length + 1):
        next_active: Set[str] = set()
        for state in active:
            for sym in alphabet:
                for dest in automaton.transitions.get(state, {}).get(sym, set()):
                    next_active.add(dest)
        active = _epsilon_closure_set(automaton, next_active)
        result[length] = 1 if (active & automaton.accept_states) else 0

    return result


def distribution_ascii_bar(automaton: Automaton, max_length: int = 10,
                           bar_width: int = 30) -> str:
    """Return a small ASCII bar chart of the word-length distribution."""
    dist = word_length_distribution(automaton, max_length)
    total = sum(dist.values())
    lines = [f"<b>Accepted strings per length</b> (0..{max_length}) — total: {total}"]
    for n in range(max_length + 1):
        count = dist[n]
        bar = "█" * count if count > 0 else ""
        lines.append(f"len {n:>2}: {count} {bar}")
    return "<br>".join(lines)

