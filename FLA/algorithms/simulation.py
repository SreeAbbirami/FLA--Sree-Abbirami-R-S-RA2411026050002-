"""Step-by-step simulation, batch testing, and accepted word generation for DFAs and NFAs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from models.automaton import EPSILON, Automaton


@dataclass
class SimulationStep:
    index: int
    symbol: Optional[str]
    from_states: Set[str]
    to_states: Set[str]
    description: str


@dataclass
class SimulationResult:
    input_string: str
    accepted: bool
    steps: List[SimulationStep] = field(default_factory=list)
    final_states: Set[str] = field(default_factory=set)
    error: Optional[str] = None


def epsilon_closure(automaton: Automaton, states: Set[str]) -> Set[str]:
    closure = set(states)
    stack = list(states)
    while stack:
        state = stack.pop()
        for target in automaton.targets(state, EPSILON):
            if target not in closure:
                closure.add(target)
                stack.append(target)
    return closure


def simulate(automaton: Automaton, input_string: str) -> SimulationResult:
    """Simulate any automaton (DFA or NFA) by tracking the set of active states."""
    if automaton.start_state is None:
        return SimulationResult(input_string, False, error="The automaton has no start state.")

    steps: List[SimulationStep] = []
    current = epsilon_closure(automaton, {automaton.start_state})
    steps.append(SimulationStep(
        index=0, symbol=None, from_states=set(), to_states=set(current),
        description=f"Start state (ε-closure): {{{', '.join(sorted(current))}}}",
    ))

    for i, symbol in enumerate(input_string, start=1):
        if symbol not in automaton.alphabet:
            return SimulationResult(
                input_string, False, steps,
                error=f"Symbol '{symbol}' is not in the alphabet.",
            )
        next_states: Set[str] = set()
        for state in current:
            next_states |= automaton.targets(state, symbol)
        next_states = epsilon_closure(automaton, next_states)
        steps.append(SimulationStep(
            index=i, symbol=symbol, from_states=set(current), to_states=set(next_states),
            description=(
                f"On '{symbol}': {{{', '.join(sorted(current)) or '∅'}}} -> "
                f"{{{', '.join(sorted(next_states)) or '∅'}}}"
            ),
        ))
        current = next_states
        if not current:
            break

    accepted = bool(current & automaton.accept_states)
    return SimulationResult(input_string, accepted, steps, final_states=current)


def batch_simulate(automaton: Automaton, strings: List[str]) -> List[dict]:
    """Simulate a batch of input strings against the automaton and return summary items."""
    results = []
    for s in strings:
        res = simulate(automaton, s)
        results.append({
            "string": s,
            "accepted": res.accepted,
            "steps_count": len(res.steps),
            "final_states": sorted(res.final_states),
            "error": res.error,
        })
    return results


def generate_accepted_strings(
    automaton: Automaton, limit: int = 15, max_length: int = 12
) -> List[str]:
    """Generate the first `limit` strings accepted by the automaton in shortlex order."""
    if automaton.start_state is None:
        return []

    alphabet = sorted([s for s in automaton.alphabet if s != EPSILON])
    if not alphabet:
        start_closure = epsilon_closure(automaton, {automaton.start_state})
        return [""] if (start_closure & automaton.accept_states) else []

    results: List[str] = []
    start_set = epsilon_closure(automaton, {automaton.start_state})
    if start_set & automaton.accept_states:
        results.append("")
        if len(results) >= limit:
            return results

    queue: List[Tuple[Set[str], str]] = [(start_set, "")]

    while queue and len(results) < limit:
        curr_states, word = queue.pop(0)
        if len(word) >= max_length:
            continue

        for sym in alphabet:
            next_states: Set[str] = set()
            for s in curr_states:
                next_states |= automaton.targets(s, sym)
            next_states = epsilon_closure(automaton, next_states)

            if not next_states:
                continue

            new_word = word + sym
            if next_states & automaton.accept_states:
                results.append(new_word)
                if len(results) >= limit:
                    break

            queue.append((next_states, new_word))

    return results
