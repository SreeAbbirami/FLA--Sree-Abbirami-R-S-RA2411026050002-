"""Preloaded example automata for learning and quick testing."""
from __future__ import annotations

from typing import Dict

from models.automaton import EPSILON

EXAMPLES: Dict[str, dict] = {
    "DFA: ends with 1": {
        "name": "DFA: binary strings ending in 1",
        "states": ["q0", "q1"],
        "alphabet": ["0", "1"],
        "start_state": "q0",
        "accept_states": ["q1"],
        "transitions": {
            "q0": {"0": ["q0"], "1": ["q1"]},
            "q1": {"0": ["q0"], "1": ["q1"]},
        },
        "positions": {"q0": [100, 150], "q1": [320, 150]},
    },
    "DFA: divisible by 3": {
        "name": "DFA: binary number divisible by 3",
        "states": ["r0", "r1", "r2"],
        "alphabet": ["0", "1"],
        "start_state": "r0",
        "accept_states": ["r0"],
        "transitions": {
            "r0": {"0": ["r0"], "1": ["r1"]},
            "r1": {"0": ["r2"], "1": ["r0"]},
            "r2": {"0": ["r1"], "1": ["r2"]},
        },
        "positions": {"r0": [220, 80], "r1": [80, 260], "r2": [360, 260]},
    },
    "NFA: contains 'ab'": {
        "name": "NFA: contains the substring 'ab'",
        "states": ["s0", "s1", "s2"],
        "alphabet": ["a", "b"],
        "start_state": "s0",
        "accept_states": ["s2"],
        "transitions": {
            "s0": {"a": ["s0", "s1"], "b": ["s0"]},
            "s1": {"b": ["s2"]},
            "s2": {"a": ["s2"], "b": ["s2"]},
        },
        "positions": {"s0": [80, 150], "s1": [280, 60], "s2": [480, 150]},
    },
    "ε-NFA: a*b* ∪ b*a*": {
        "name": "NFA with epsilon: a*b* union b*a*",
        "states": ["p0", "p1", "p2", "p3", "p4"],
        "alphabet": ["a", "b"],
        "start_state": "p0",
        "accept_states": ["p2", "p4"],
        "transitions": {
            "p0": {EPSILON: ["p1", "p3"]},
            "p1": {"a": ["p1"], "b": ["p2"]},
            "p2": {"b": ["p2"]},
            "p3": {"b": ["p3"], "a": ["p4"]},
            "p4": {"a": ["p4"]},
        },
        "positions": {
            "p0": [60, 200], "p1": [220, 80], "p2": [400, 80],
            "p3": [220, 320], "p4": [400, 320],
        },
    },
    "DFA: with dead and unreachable states": {
        "name": "Example DFA with dead and unreachable states",
        "states": ["A", "B", "C", "D", "E"],
        "alphabet": ["0", "1"],
        "start_state": "A",
        "accept_states": ["B"],
        "transitions": {
            "A": {"0": ["A"], "1": ["B"]},
            "B": {"0": ["B"], "1": ["B"]},
            "C": {"0": ["D"], "1": ["D"]},
            "D": {"0": ["D"], "1": ["D"]},
            "E": {"0": ["A"], "1": ["A"]},
        },
        "positions": {
            "A": [80, 200], "B": [300, 200], "C": [500, 80],
            "D": [500, 320], "E": [80, 380],
        },
    },
    "NFA: regex (a|b)*abb": {
        "name": "NFA from regex (a|b)*abb",
        "states": ["q0", "q1", "q2", "q3"],
        "alphabet": ["a", "b"],
        "start_state": "q0",
        "accept_states": ["q3"],
        "transitions": {
            "q0": {"a": ["q0", "q1"], "b": ["q0"]},
            "q1": {"b": ["q2"]},
            "q2": {"b": ["q3"]},
            "q3": {},
        },
        "positions": {"q0": [90, 180], "q1": [250, 180], "q2": [410, 180], "q3": [570, 180]},
    },
    "DFA: even 0s and even 1s": {
        "name": "DFA: strings with even number of 0s and 1s",
        "states": ["ee", "oe", "eo", "oo"],
        "alphabet": ["0", "1"],
        "start_state": "ee",
        "accept_states": ["ee"],
        "transitions": {
            "ee": {"0": ["oe"], "1": ["eo"]},
            "oe": {"0": ["ee"], "1": ["oo"]},
            "eo": {"0": ["oo"], "1": ["ee"]},
            "oo": {"0": ["eo"], "1": ["oe"]},
        },
        "positions": {"ee": [120, 120], "oe": [360, 120], "eo": [120, 320], "oo": [360, 320]},
    },
    "DFA: ATM PIN verification (4 digits)": {
        "name": "ATM PIN Verification (4 digits)",
        "states": ["q0", "q1", "q2", "q3", "q4"],
        "alphabet": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "start_state": "q0",
        "accept_states": ["q4"],
        "transitions": {
            "q0": {d: ["q1"] for d in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]},
            "q1": {d: ["q2"] for d in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]},
            "q2": {d: ["q3"] for d in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]},
            "q3": {d: ["q4"] for d in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]},
            "q4": {},
        },
        "positions": {
            "q0": [80, 200],
            "q1": [230, 200],
            "q2": [380, 200],
            "q3": [530, 200],
            "q4": [680, 200],
        },
    },
    "DFA: Email validation": {
        "name": "Email Validation",
        "states": ["q0", "q_user", "q_at", "q_domain", "q_dot", "q_ext"],
        "alphabet": ["a", "b", "@", "."],
        "start_state": "q0",
        "accept_states": ["q_ext"],
        "transitions": {
            "q0": {"a": ["q_user"], "b": ["q_user"]},
            "q_user": {"a": ["q_user"], "b": ["q_user"], "@": ["q_at"]},
            "q_at": {"a": ["q_domain"], "b": ["q_domain"]},
            "q_domain": {"a": ["q_domain"], "b": ["q_domain"], ".": ["q_dot"]},
            "q_dot": {"a": ["q_ext"], "b": ["q_ext"]},
            "q_ext": {"a": ["q_ext"], "b": ["q_ext"]},
        },
        "positions": {
            "q0": [70, 200],
            "q_user": [210, 200],
            "q_at": [350, 200],
            "q_domain": [490, 200],
            "q_dot": [630, 200],
            "q_ext": [770, 200],
        },
    },
    "DFA: Password verification (letter + digit)": {
        "name": "Password Verification (letter + digit)",
        "states": ["q0", "q_letter", "q_digit", "q_valid"],
        "alphabet": ["a", "1"],
        "start_state": "q0",
        "accept_states": ["q_valid"],
        "transitions": {
            "q0": {"a": ["q_letter"], "1": ["q_digit"]},
            "q_letter": {"a": ["q_letter"], "1": ["q_valid"]},
            "q_digit": {"1": ["q_digit"], "a": ["q_valid"]},
            "q_valid": {"a": ["q_valid"], "1": ["q_valid"]},
        },
        "positions": {
            "q0": [90, 200],
            "q_letter": [270, 90],
            "q_digit": [270, 310],
            "q_valid": [450, 200],
        },
    },
}

# Backward compatibility aliases
EXAMPLES["AFD: termina en 1"] = EXAMPLES["DFA: ends with 1"]
EXAMPLES["AFD: divisible entre 3"] = EXAMPLES["DFA: divisible by 3"]
EXAMPLES["AFND: contiene 'ab'"] = EXAMPLES["NFA: contains 'ab'"]
EXAMPLES["AFND-ε: a*b* ∪ b*a*"] = EXAMPLES["ε-NFA: a*b* ∪ b*a*"]
EXAMPLES["AFD: con estados muertos e inaccesibles"] = EXAMPLES["DFA: with dead and unreachable states"]
