"""Input validation helpers used by the GUI panels and dialogs."""
from __future__ import annotations

import re
from typing import Optional

from models.automaton import EPSILON, Automaton

_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")


def validate_state_name(name: str, automaton: Automaton, editing: Optional[str] = None) -> Optional[str]:
    name = name.strip()
    if not name:
        return "State name cannot be empty."
    if not _NAME_RE.match(name):
        return "State name can only contain letters, numbers, '_' and '-'."
    if name != editing and name in automaton.states:
        return f"State '{name}' already exists."
    return None


def validate_symbol(symbol: str, automaton: Automaton) -> Optional[str]:
    symbol = symbol.strip()
    if not symbol:
        return "Symbol cannot be empty."
    if symbol == EPSILON:
        return "That symbol is reserved for epsilon transitions."
    if len(symbol) != 1:
        return "Single-character symbols are recommended."
    if symbol in automaton.alphabet:
        return f"Symbol '{symbol}' is already in the alphabet."
    return None


def validate_transition(source: str, symbol: str, target: str, automaton: Automaton, allow_epsilon: bool = True) -> Optional[str]:
    if source not in automaton.states:
        return f"Source state '{source}' does not exist."
    if target not in automaton.states:
        return f"Target state '{target}' does not exist."
    if symbol == EPSILON:
        if not allow_epsilon:
            return "Epsilon transitions are not allowed in a DFA."
        return None
    if symbol not in automaton.alphabet:
        return f"Symbol '{symbol}' does not belong to the alphabet."
    return None


def validate_input_string(text: str, automaton: Automaton) -> Optional[str]:
    for ch in text:
        if ch not in automaton.alphabet:
            return f"Character '{ch}' does not belong to the automaton alphabet."
    return None
