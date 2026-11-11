"""Algorithms package for finite automata."""
from .simulation import simulate, batch_simulate, generate_accepted_strings, epsilon_closure, SimulationResult
from .subset_construction import nfa_to_dfa, SubsetConstructionResult
from .minimization import minimize_dfa, MinimizationResult
from .properties import analyze, is_language_infinite, is_language_empty, PropertiesReport
from .conversions import (
    regex_to_nfa,
    automaton_to_regex,
    complement_dfa,
    intersect_dfas,
    union_dfas,
    check_equivalence,
    dfa_to_nfa,
    compute_layered_positions,
)
