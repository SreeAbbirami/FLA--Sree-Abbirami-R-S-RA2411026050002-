"""Automaton conversions: Regex ↔ NFA/DFA, state elimination, completion, complement, product and equivalence."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from algorithms.simulation import epsilon_closure
from models.automaton import EPSILON, Automaton


# ------------------------------------------------------------------
# Trivial conversions
# ------------------------------------------------------------------

def dfa_to_nfa(dfa: Automaton) -> Automaton:
    """Return an equivalent copy of the DFA flagged as an NFA."""
    nfa = dfa.clone()
    nfa.name = f"{dfa.name} (equivalent NFA)"
    return nfa


def remove_unreachable_states(automaton: Automaton) -> Automaton:
    result = automaton.clone()
    for state in result.get_unreachable_states():
        result.remove_state(state)
    return result


# ------------------------------------------------------------------
# Regular Expression -> NFA (Thompson's Construction)
# ------------------------------------------------------------------

class RegexParser:
    """Parses infix regular expressions into postfix using the Shunting-yard algorithm."""

    PRECEDENCE = {"|": 1, "·": 2, "*": 3, "+": 3, "?": 3}

    @classmethod
    def expand_shorthands(cls, regex: str) -> str:
        """Expands [a-c], [0-9], and {n} quantifiers into standard regular expressions."""
        import re
        s = regex.replace(r"\.", ".")

        def _replace_class(match):
            content = match.group(1)
            chars = []
            i = 0
            while i < len(content):
                if i + 2 < len(content) and content[i + 1] == "-":
                    start_c, end_c = content[i], content[i + 2]
                    for code in range(ord(start_c), ord(end_c) + 1):
                        chars.append(chr(code))
                    i += 3
                else:
                    chars.append(content[i])
                    i += 1
            if not chars:
                return ""
            return "(" + "|".join(chars) + ")"

        res = re.sub(r"\[([^\]]+)\]", _replace_class, s)

        def _expand_repeat(expr: str) -> str:
            m = re.search(r"\{(\d+)\}", expr)
            if not m:
                return expr
            count = int(m.group(1))
            start_idx = m.start()
            end_idx = m.end()
            if start_idx == 0:
                return expr
            if expr[start_idx - 1] == ")":
                depth = 1
                p = start_idx - 2
                while p >= 0 and depth > 0:
                    if expr[p] == ")":
                        depth += 1
                    elif expr[p] == "(":
                        depth -= 1
                    p -= 1
                token = expr[p + 1 : start_idx]
                expanded = token * count
                return _expand_repeat(expr[: p + 1] + expanded + expr[end_idx:])
            else:
                token = expr[start_idx - 1]
                expanded = token * count
                return _expand_repeat(expr[: start_idx - 1] + expanded + expr[end_idx:])

        return _expand_repeat(res)

    @classmethod
    def insert_concat(cls, regex: str) -> str:
        cleaned = [ch for ch in regex if not ch.isspace()]
        if not cleaned:
            return ""
        output = []
        postfix_ops = {"*", "+", "?"}
        for i in range(len(cleaned)):
            c1 = cleaned[i]
            output.append(c1)
            if i + 1 < len(cleaned):
                c2 = cleaned[i + 1]
                is_c1_src = (c1 not in cls.PRECEDENCE and c1 not in {"(", "|"}) or (c1 in postfix_ops) or (c1 == ")")
                is_c2_dst = (c2 not in cls.PRECEDENCE and c2 not in {")", "*", "+", "?", "|"}) or (c2 == "(")
                if is_c1_src and is_c2_dst:
                    output.append("·")
        return "".join(output)

    @classmethod
    def to_postfix(cls, regex: str) -> str:
        expanded = cls.expand_shorthands(regex)
        with_concat = cls.insert_concat(expanded)
        output, stack = [], []
        postfix_unary = {"*", "+", "?"}
        for c in with_concat:
            if c in postfix_unary:
                output.append(c)
            elif c == "|":
                while stack and stack[-1] != "(" and cls.PRECEDENCE.get(stack[-1], 0) >= cls.PRECEDENCE["|"]:
                    output.append(stack.pop())
                stack.append(c)
            elif c == "·":
                while stack and stack[-1] != "(" and cls.PRECEDENCE.get(stack[-1], 0) >= cls.PRECEDENCE["·"]:
                    output.append(stack.pop())
                stack.append(c)
            elif c == "(":
                stack.append(c)
            elif c == ")":
                while stack and stack[-1] != "(":
                    output.append(stack.pop())
                if stack and stack[-1] == "(":
                    stack.pop()
            else:
                output.append(c)
        while stack:
            output.append(stack.pop())
        return "".join(output)


class Fragment:
    def __init__(self, start: str, accept: str):
        self.start = start
        self.accept = accept


def compute_layered_positions(automaton: Automaton) -> None:
    """Assign clean left-to-right positions using topological layer ranking."""
    if not automaton.states or automaton.start_state is None:
        return
    layers: Dict[int, List[str]] = {}
    state_layer: Dict[str, int] = {automaton.start_state: 0}
    queue = [automaton.start_state]

    while queue:
        curr = queue.pop(0)
        curr_layer = state_layer[curr]
        layers.setdefault(curr_layer, []).append(curr)
        for sym, dests in automaton.transitions.get(curr, {}).items():
            for d in dests:
                if d not in state_layer:
                    state_layer[d] = curr_layer + 1
                    queue.append(d)

    max_layer = max(layers.keys()) if layers else 0
    for s in automaton.states:
        if s not in state_layer:
            max_layer += 1
            state_layer[s] = max_layer
            layers.setdefault(max_layer, []).append(s)

    x_start, x_gap, y_center, y_gap = 80, 130, 220, 100
    positions: Dict[str, Tuple[float, float]] = {}
    for layer_idx, st_list in layers.items():
        x = x_start + layer_idx * x_gap
        count = len(st_list)
        y_offset = y_center - (count - 1) * (y_gap / 2)
        for i, st in enumerate(st_list):
            y = y_offset + i * y_gap
            positions[st] = (round(x, 1), round(y, 1))
    automaton.positions = positions


def regex_to_nfa(regex_str: str, automaton_name: Optional[str] = None) -> Automaton:
    """Build an epsilon-NFA from a regular expression using Thompson's construction."""
    regex_clean = regex_str.strip()
    if not regex_clean:
        nfa = Automaton(name=automaton_name or "NFA: empty", states=["q0"], alphabet=[], start_state="q0", accept_states={"q0"}, positions={"q0": (150, 150)})
        return nfa

    postfix = RegexParser.to_postfix(regex_clean)
    state_counter = 0

    def new_state() -> str:
        nonlocal state_counter
        s = f"q{state_counter}"
        state_counter += 1
        return s

    transitions: Dict[str, Dict[str, Set[str]]] = {}
    states: List[str] = []
    alphabet_set: Set[str] = set()

    def add_st(st: str) -> None:
        if st not in states:
            states.append(st)
            transitions[st] = {}

    def add_tr(src: str, sym: str, dst: str) -> None:
        add_st(src)
        add_st(dst)
        transitions.setdefault(src, {}).setdefault(sym, set()).add(dst)
        if sym != EPSILON:
            alphabet_set.add(sym)

    stack: List[Fragment] = []

    for token in postfix:
        if token == "*":
            if not stack:
                continue
            frag = stack.pop()
            s, e = new_state(), new_state()
            add_tr(s, EPSILON, frag.start)
            add_tr(s, EPSILON, e)
            add_tr(frag.accept, EPSILON, frag.start)
            add_tr(frag.accept, EPSILON, e)
            stack.append(Fragment(s, e))
        elif token == "+":
            if not stack:
                continue
            frag = stack.pop()
            s, e = new_state(), new_state()
            add_tr(s, EPSILON, frag.start)
            add_tr(frag.accept, EPSILON, frag.start)
            add_tr(frag.accept, EPSILON, e)
            stack.append(Fragment(s, e))
        elif token == "?":
            if not stack:
                continue
            frag = stack.pop()
            s, e = new_state(), new_state()
            add_tr(s, EPSILON, frag.start)
            add_tr(s, EPSILON, e)
            add_tr(frag.accept, EPSILON, e)
            stack.append(Fragment(s, e))
        elif token == "|":
            if len(stack) < 2:
                continue
            f2, f1 = stack.pop(), stack.pop()
            s, e = new_state(), new_state()
            add_tr(s, EPSILON, f1.start)
            add_tr(s, EPSILON, f2.start)
            add_tr(f1.accept, EPSILON, e)
            add_tr(f2.accept, EPSILON, e)
            stack.append(Fragment(s, e))
        elif token == "·":
            if len(stack) < 2:
                continue
            f2, f1 = stack.pop(), stack.pop()
            add_tr(f1.accept, EPSILON, f2.start)
            stack.append(Fragment(f1.start, f2.accept))
        else:
            sym = EPSILON if token in {"ε", "e", "E", "\\e"} else token
            s, e = new_state(), new_state()
            add_tr(s, sym, e)
            stack.append(Fragment(s, e))

    if not stack:
        return Automaton(name=automaton_name or f"NFA: {regex_clean}", states=["q0"], alphabet=[], start_state="q0", accept_states={"q0"})

    final_frag = stack[-1]
    nfa = Automaton(
        name=automaton_name or f"NFA: {regex_clean}",
        alphabet=sorted(alphabet_set),
        states=list(states),
        start_state=final_frag.start,
        accept_states={final_frag.accept},
        transitions=transitions,
    )
    compute_layered_positions(nfa)
    return nfa


def regex_to_clean_dfa(regex_str: str, automaton_name: Optional[str] = None) -> Automaton:
    """Converts any regular expression into an optimal, minimal, clean DFA

    with cleanly numbered states (q0, q1, ...) and automatic layered layout.
    Avoids raw Thompson epsilon explosion and gives the clearest diagram.
    """
    from algorithms.subset_construction import nfa_to_dfa
    from algorithms.minimization import minimize_dfa

    nfa = regex_to_nfa(regex_str, automaton_name=automaton_name)
    dfa_res = nfa_to_dfa(nfa)
    min_res = minimize_dfa(dfa_res.dfa)
    raw_dfa = min_res.dfa

    # Determine topological layer ordering of states from start state
    layers: Dict[int, List[str]] = {}
    state_layer: Dict[str, int] = {}
    if raw_dfa.start_state:
        state_layer[raw_dfa.start_state] = 0
        queue = [raw_dfa.start_state]
        while queue:
            curr = queue.pop(0)
            curr_l = state_layer[curr]
            layers.setdefault(curr_l, []).append(curr)
            for sym, dests in raw_dfa.transitions.get(curr, {}).items():
                for d in dests:
                    if d not in state_layer:
                        state_layer[d] = curr_l + 1
                        queue.append(d)

    # Order states by layer so q0 is start, q1 is next, etc.
    ordered_states: List[str] = []
    for l in sorted(layers.keys()):
        for s in layers[l]:
            if s not in ordered_states:
                ordered_states.append(s)
    for s in raw_dfa.states:
        if s not in ordered_states:
            ordered_states.append(s)

    state_map = {s: f"q{i}" for i, s in enumerate(ordered_states)}

    clean_dfa = Automaton(
        name=automaton_name or f"DFA: {regex_str}",
        alphabet=list(raw_dfa.alphabet),
    )
    for s in ordered_states:
        clean_dfa.add_state(state_map[s])
    if raw_dfa.start_state:
        clean_dfa.set_start_state(state_map[raw_dfa.start_state])
    for s in raw_dfa.accept_states:
        clean_dfa.accept_states.add(state_map[s])

    for src in ordered_states:
        for sym, dests in raw_dfa.transitions.get(src, {}).items():
            for dst in dests:
                clean_dfa.add_transition(state_map[src], sym, state_map[dst])

    compute_layered_positions(clean_dfa)
    return clean_dfa


# ------------------------------------------------------------------
# Automaton -> Regular Expression (GNFA State Elimination)
# ------------------------------------------------------------------

@dataclass
class StateEliminationStep:
    index: int
    eliminated_state: str
    remaining_states: List[str]
    description: str


@dataclass
class DfaToRegexResult:
    regex: str
    steps: List[StateEliminationStep] = field(default_factory=list)


def _union_regex(r1: Optional[str], r2: Optional[str]) -> Optional[str]:
    if not r1:
        return r2
    if not r2:
        return r1
    if r1 == r2:
        return r1
    p1 = set(r1.split("|")) if not (r1.startswith("(") and r1.endswith(")")) else {r1}
    p2 = set(r2.split("|")) if not (r2.startswith("(") and r2.endswith(")")) else {r2}
    combined = sorted(p1 | p2)
    return "|".join(combined) if len(combined) > 1 else combined[0]


def _concat_regex(r1: Optional[str], r2: Optional[str]) -> Optional[str]:
    if r1 is None or r2 is None:
        return None
    if r1 == EPSILON:
        return r2
    if r2 == EPSILON:
        return r1
    p1 = f"({r1})" if ("|" in r1 and not (r1.startswith("(") and r1.endswith(")"))) else r1
    p2 = f"({r2})" if ("|" in r2 and not (r2.startswith("(") and r2.endswith(")"))) else r2
    return f"{p1}{p2}"


def _star_regex(r: Optional[str]) -> Optional[str]:
    if not r or r == EPSILON:
        return EPSILON
    if r.endswith("*"):
        return r
    if len(r) == 1:
        return f"{r}*"
    if r.startswith("(") and r.endswith(")") and r.count("(") == 1:
        return f"{r}*"
    return f"({r})*"


def automaton_to_regex(automaton: Automaton) -> DfaToRegexResult:
    """Convert any finite automaton to an equivalent regular expression using state elimination."""
    if automaton.start_state is None or not automaton.accept_states:
        return DfaToRegexResult(regex="∅", steps=[])

    states = list(automaton.states)
    q_init, q_final = "__init__", "__final__"
    while q_init in states:
        q_init = "_" + q_init
    while q_final in states:
        q_final = "_" + q_final

    all_gnfa_states = [q_init] + states + [q_final]
    R: Dict[str, Dict[str, Optional[str]]] = {u: {v: None for v in all_gnfa_states} for u in all_gnfa_states}
    R[q_init][automaton.start_state] = EPSILON
    for acc in automaton.accept_states:
        if acc in states:
            R[acc][q_final] = EPSILON

    for src in states:
        for sym, dests in automaton.transitions.get(src, {}).items():
            sym_label = EPSILON if sym == EPSILON else sym
            for dst in dests:
                if dst in states:
                    R[src][dst] = _union_regex(R[src][dst], sym_label)

    steps: List[StateEliminationStep] = []
    remaining = list(states)
    step_idx = 1

    for q_rip in states:
        remaining.remove(q_rip)
        r_loop = R[q_rip][q_rip]
        r_loop_star = _star_regex(r_loop)
        active = [q_init] + remaining + [q_final]

        for p in active:
            if p == q_final or R[p][q_rip] is None:
                continue
            r_p_rip = R[p][q_rip]
            for s in active:
                if s == q_init or R[q_rip][s] is None:
                    continue
                r_rip_s = R[q_rip][s]
                bypass = _concat_regex(_concat_regex(r_p_rip, r_loop_star), r_rip_s)
                R[p][s] = _union_regex(R[p][s], bypass)

        steps.append(StateEliminationStep(
            index=step_idx, eliminated_state=q_rip, remaining_states=list(remaining),
            description=f"Eliminated state '{q_rip}'. {len(remaining)} intermediate states remaining.",
        ))
        step_idx += 1

    return DfaToRegexResult(regex=R[q_init][q_final] or "∅", steps=steps)


# ------------------------------------------------------------------
# Language Algebra: Completion, Complement, Product & Equivalence
# ------------------------------------------------------------------

def complete_dfa(automaton: Automaton) -> Automaton:
    """Ensure every state in the DFA has an explicit transition for every alphabet symbol."""
    if not automaton.is_deterministic():
        raise ValueError("Only deterministic automata (DFA) can be completed.")
    if automaton.is_complete():
        return automaton.clone()

    comp = automaton.clone()
    comp.name = f"{automaton.name} (completed)"
    alphabet = list(comp.alphabet)

    trap_state = "trap"
    counter = 1
    while trap_state in comp.states:
        trap_state = f"trap_{counter}"
        counter += 1

    trap_needed = any(not comp.targets(s, sym) for s in comp.states for sym in alphabet)
    if not trap_needed:
        return comp

    comp.add_state(trap_state, (300, 350))
    for sym in alphabet:
        comp.add_transition(trap_state, sym, trap_state)
    for s in list(comp.states):
        for sym in alphabet:
            if not comp.targets(s, sym):
                comp.add_transition(s, sym, trap_state)
    return comp


def complement_dfa(automaton: Automaton) -> Automaton:
    """Compute the complement language DFA (L') by completing and inverting accept states."""
    if not automaton.is_deterministic():
        raise ValueError("Only deterministic automata (DFA) can be complemented.")
    if automaton.start_state is None:
        raise ValueError("The automaton has no start state.")
    comp = complete_dfa(automaton)
    comp.name = f"{automaton.name} (complement)"
    comp.accept_states = set(comp.states) - set(comp.accept_states)
    return comp


def _product_construction(dfa1: Automaton, dfa2: Automaton, mode: str = "intersection") -> Automaton:
    if not dfa1.is_deterministic() or not dfa2.is_deterministic():
        raise ValueError("Both automata must be deterministic (DFA) for product construction.")
    if dfa1.start_state is None or dfa2.start_state is None:
        raise ValueError("Both automata must have a defined start state.")

    common_alphabet = sorted(set(dfa1.alphabet) | set(dfa2.alphabet))
    c1, c2 = complete_dfa(dfa1), complete_dfa(dfa2)
    for sym in common_alphabet:
        if sym not in c1.alphabet:
            c1.add_symbol(sym)
            c1 = complete_dfa(c1)
        if sym not in c2.alphabet:
            c2.add_symbol(sym)
            c2 = complete_dfa(c2)

    start_pair = (c1.start_state, c2.start_state)
    start_name = f"({start_pair[0]},{start_pair[1]})"
    prod_name = f"{dfa1.name} ∩ {dfa2.name}" if mode == "intersection" else f"{dfa1.name} ∪ {dfa2.name}"

    product = Automaton(name=prod_name, alphabet=common_alphabet)
    product.add_state(start_name)
    product.set_start_state(start_name)

    pair_to_name = {start_pair: start_name}
    queue = [start_pair]
    visited = {start_pair}

    while queue:
        p1, p2 = queue.pop(0)
        curr_name = pair_to_name[(p1, p2)]
        is_acc1 = p1 in c1.accept_states
        is_acc2 = p2 in c2.accept_states
        if mode == "intersection" and (is_acc1 and is_acc2):
            product.accept_states.add(curr_name)
        elif mode == "union" and (is_acc1 or is_acc2):
            product.accept_states.add(curr_name)
        elif mode == "diff1" and (is_acc1 and not is_acc2):
            product.accept_states.add(curr_name)

        for sym in common_alphabet:
            t1 = next(iter(c1.targets(p1, sym)), None)
            t2 = next(iter(c2.targets(p2, sym)), None)
            if t1 is None or t2 is None:
                continue
            target_pair = (t1, t2)
            if target_pair not in pair_to_name:
                t_name = f"({t1},{t2})"
                pair_to_name[target_pair] = t_name
                product.add_state(t_name)
            if target_pair not in visited:
                visited.add(target_pair)
                queue.append(target_pair)
            product.add_transition(curr_name, sym, pair_to_name[target_pair])

    n = len(product.states)
    cx, cy, r = 260, 220, max(120, n * 24)
    for i, s in enumerate(product.states):
        angle = (2 * math.pi * i) / max(1, n) - (math.pi / 2)
        product.positions[s] = (round(cx + r * math.cos(angle), 1), round(cy + r * math.sin(angle), 1))
    return product


def intersect_dfas(dfa1: Automaton, dfa2: Automaton) -> Automaton:
    return _product_construction(dfa1, dfa2, mode="intersection")


def union_dfas(dfa1: Automaton, dfa2: Automaton) -> Automaton:
    return _product_construction(dfa1, dfa2, mode="union")


def _find_shortest_accepted_string(automaton: Automaton) -> Optional[str]:
    if automaton.start_state is None:
        return None
    if automaton.start_state in automaton.accept_states:
        return ""
    queue: List[Tuple[str, str]] = [(automaton.start_state, "")]
    visited: Set[str] = {automaton.start_state}
    while queue:
        curr, word = queue.pop(0)
        for sym in sorted(automaton.alphabet):
            for dest in automaton.targets(curr, sym):
                if dest in automaton.accept_states:
                    return word + sym
                if dest not in visited:
                    visited.add(dest)
                    queue.append((dest, word + sym))
    return None


def check_equivalence(dfa1: Automaton, dfa2: Automaton) -> dict:
    """Test if two DFAs recognize the exact same language or find a counterexample."""
    if not dfa1.is_deterministic() or not dfa2.is_deterministic():
        raise ValueError("Both automata must be deterministic (DFA) to test equivalence.")

    diff1 = _product_construction(dfa1, dfa2, mode="diff1")
    ce1 = _find_shortest_accepted_string(diff1)
    diff2 = _product_construction(dfa2, dfa1, mode="diff1")
    ce2 = _find_shortest_accepted_string(diff2)

    sub1, sub2 = ce1 is None, ce2 is None
    equiv = sub1 and sub2

    if equiv:
        msg = "The two automata are equivalent! They accept the exact same language."
    elif sub1:
        msg = f"L(M1) ⊂ L(M2). M2 accepts '{ce2}' which M1 rejects."
    elif sub2:
        msg = f"L(M2) ⊂ L(M1). M1 accepts '{ce1}' which M2 rejects."
    else:
        msg = f"Not equivalent. E.g. '{ce1}' ∈ L1\\L2, '{ce2}' ∈ L2\\L1."

    return {
        "equivalent": equiv,
        "subset_1_in_2": sub1,
        "subset_2_in_1": sub2,
        "counterexample_1_not_2": ce1,
        "counterexample_2_not_1": ce2,
        "message": msg,
    }
