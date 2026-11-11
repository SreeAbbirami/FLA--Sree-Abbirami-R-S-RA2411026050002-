"""Lightweight smoke tests for the automata algorithms (run with plain python)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.automaton import Automaton, EPSILON
from algorithms.simulation import simulate, batch_simulate, generate_accepted_strings
from algorithms.subset_construction import nfa_to_dfa
from algorithms.minimization import minimize_dfa
from algorithms.properties import analyze, is_language_infinite, is_language_empty
from algorithms.conversions import (
    regex_to_nfa,
    regex_to_clean_dfa,
    automaton_to_regex,
    complement_dfa,
    intersect_dfas,
    union_dfas,
    check_equivalence,
)
from utils.file_io import to_dot, to_tikz, to_jflap_xml, from_jflap_xml


def build_nfa_ends_with_ab() -> Automaton:
    # NFA over {a,b} accepting strings that end with "ab"
    nfa = Automaton(name="Termina en ab")
    for s in ["q0", "q1", "q2"]:
        nfa.add_state(s)
    nfa.alphabet = ["a", "b"]
    nfa.set_start_state("q0")
    nfa.accept_states = {"q2"}
    nfa.add_transition("q0", "a", "q0")
    nfa.add_transition("q0", "b", "q0")
    nfa.add_transition("q0", "a", "q1")
    nfa.add_transition("q1", "b", "q2")
    return nfa


def test_simulation():
    nfa = build_nfa_ends_with_ab()
    assert simulate(nfa, "ab").accepted
    assert simulate(nfa, "aab").accepted
    assert simulate(nfa, "aba").accepted is False
    assert simulate(nfa, "").accepted is False
    print("OK simulate NFA")


def test_subset_construction():
    nfa = build_nfa_ends_with_ab()
    result = nfa_to_dfa(nfa)
    dfa = result.dfa
    assert dfa.is_deterministic()
    for s in ["ab", "aab", "bbab", "aababab"]:
        nfa_r = simulate(nfa, s).accepted
        dfa_r = simulate(dfa, s).accepted
        assert nfa_r == dfa_r, f"mismatch on {s}: nfa={nfa_r} dfa={dfa_r}"
    for s in ["", "a", "ba", "aba", "bb"]:
        nfa_r = simulate(nfa, s).accepted
        dfa_r = simulate(dfa, s).accepted
        assert nfa_r == dfa_r, f"mismatch on {s}: nfa={nfa_r} dfa={dfa_r}"
    print("OK subset construction, steps:", len(result.steps))


def test_epsilon_nfa():
    nfa = Automaton(name="epsilon test")
    for s in ["q0", "q1", "q2"]:
        nfa.add_state(s)
    nfa.alphabet = ["a"]
    nfa.set_start_state("q0")
    nfa.accept_states = {"q2"}
    nfa.add_transition("q0", EPSILON, "q1")
    nfa.add_transition("q1", "a", "q2")
    assert simulate(nfa, "a").accepted
    assert simulate(nfa, "").accepted is False
    dfa = nfa_to_dfa(nfa).dfa
    assert dfa.is_deterministic()
    assert simulate(dfa, "a").accepted
    print("OK epsilon-NFA handling")


def test_minimization():
    # Classic textbook example: DFA over {0,1} with equivalent states to merge.
    dfa = Automaton(name="min test")
    for s in ["A", "B", "C", "D", "E", "F"]:
        dfa.add_state(s)
    dfa.alphabet = ["0", "1"]
    dfa.set_start_state("A")
    dfa.accept_states = {"C", "D", "E"}
    trans = {
        ("A", "0"): "B", ("A", "1"): "C",
        ("B", "0"): "A", ("B", "1"): "D",
        ("C", "0"): "E", ("C", "1"): "F",
        ("D", "0"): "E", ("D", "1"): "F",
        ("E", "0"): "E", ("E", "1"): "F",
        ("F", "0"): "F", ("F", "1"): "F",
    }
    for (src, sym), dst in trans.items():
        dfa.add_transition(src, sym, dst)

    result = minimize_dfa(dfa)
    min_dfa = result.dfa
    assert len(min_dfa.states) == 3, f"expected 3 states, got {len(min_dfa.states)}: {min_dfa.states}"
    for s in ["", "0", "1", "01", "10", "0011", "111", "000"]:
        orig = simulate(dfa, s).accepted
        mini = simulate(min_dfa, s).accepted
        assert orig == mini, f"mismatch on {s}: orig={orig} min={mini}"
    print("OK minimization, groups:", len(min_dfa.states))


def test_properties():
    dfa = Automaton(name="props test")
    dfa.add_state("q0")
    dfa.add_state("q1")
    dfa.add_state("unreachable")
    dfa.alphabet = ["a"]
    dfa.set_start_state("q0")
    dfa.accept_states = {"q1"}
    dfa.add_transition("q0", "a", "q1")
    dfa.add_transition("q1", "a", "q1")
    report = analyze(dfa)
    assert report.is_deterministic
    assert not report.is_connected
    assert "unreachable" in report.unreachable_states
    print("OK properties analysis")


def test_regex_to_nfa():
    nfa = regex_to_nfa("(a|b)*abb")
    assert len(nfa.states) > 0
    assert simulate(nfa, "abb").accepted
    assert simulate(nfa, "aabb").accepted
    assert simulate(nfa, "babb").accepted
    assert simulate(nfa, "abba").accepted is False
    assert simulate(nfa, "ab").accepted is False
    print("OK regex to NFA")


def test_automaton_to_regex():
    nfa = build_nfa_ends_with_ab()
    dfa = nfa_to_dfa(nfa).dfa
    res = automaton_to_regex(dfa)
    assert isinstance(res.regex, str) and len(res.regex) > 0
    assert len(res.steps) == len(dfa.states)
    print("OK automaton to regex (GNFA)")


def test_operations():
    nfa = build_nfa_ends_with_ab()
    dfa = nfa_to_dfa(nfa).dfa
    comp = complement_dfa(dfa)
    assert comp.is_deterministic()
    assert simulate(comp, "ab").accepted is False
    assert simulate(comp, "aba").accepted is True

    self_eq = check_equivalence(dfa, dfa)
    assert self_eq["equivalent"]

    comp_eq = check_equivalence(dfa, comp)
    assert comp_eq["equivalent"] is False
    assert comp_eq["counterexample_1_not_2"] is not None

    inter = intersect_dfas(dfa, comp)
    assert is_language_empty(inter)

    uni = union_dfas(dfa, comp)
    assert simulate(uni, "ab").accepted and simulate(uni, "aba").accepted
    print("OK automata operations (complement, intersection, union, equivalence)")


def test_word_generator_and_batch():
    nfa = build_nfa_ends_with_ab()
    dfa = nfa_to_dfa(nfa).dfa
    words = generate_accepted_strings(dfa, limit=5)
    assert len(words) == 5
    assert all(w.endswith("ab") for w in words)
    assert is_language_infinite(dfa)

    batch = batch_simulate(dfa, ["ab", "aba", "aab", "b"])
    assert [b["accepted"] for b in batch] == [True, False, True, False]
    print("OK string generation and batch testing")


def test_exporters():
    nfa = build_nfa_ends_with_ab()
    dfa = nfa_to_dfa(nfa).dfa
    dot = to_dot(dfa)
    assert "digraph" in dot and "doublecircle" in dot

    tikz = to_tikz(dfa)
    assert "tikzpicture" in tikz and r"\node" in tikz

    xml = to_jflap_xml(dfa)
    assert "<structure>" in xml and "<automaton>" in xml

    imported = from_jflap_xml(xml)
    assert len(imported.states) == len(dfa.states)
    assert simulate(imported, "ab").accepted
    assert simulate(imported, "aba").accepted is False
    print("OK exporters (DOT, TikZ, JFLAP)")


def test_atm_pin_verification():
    # ATM PIN requires exactly 4 digits: [0-9]{4}
    nfa = regex_to_nfa("[0-9]{4}", automaton_name="ATM PIN Verification")
    assert simulate(nfa, "1234").accepted
    assert simulate(nfa, "0000").accepted
    assert simulate(nfa, "9876").accepted
    assert simulate(nfa, "123").accepted is False
    assert simulate(nfa, "12345").accepted is False
    assert simulate(nfa, "").accepted is False
    print("OK ATM PIN verification (regex [0-9]{4} -> NFA)")


def test_email_validation():
    # Email pattern: user@domain.ext
    nfa = regex_to_nfa("[a-c]+@[a-c]+\\.[a-c]+", automaton_name="Email Validation")
    assert simulate(nfa, "a@b.c").accepted
    assert simulate(nfa, "ab@ba.cb").accepted
    assert simulate(nfa, "c@a.b").accepted
    assert simulate(nfa, "@b.c").accepted is False
    assert simulate(nfa, "a@.c").accepted is False
    assert simulate(nfa, "a@b.").accepted is False
    assert simulate(nfa, "a@b").accepted is False
    assert simulate(nfa, "").accepted is False
    print("OK Email validation (regex [a-c]+@[a-c]+\\.[a-c]+ -> NFA)")


def test_password_verification():
    # Password requirement: at least one letter and at least one digit
    pwd_regex = "(a|1)*(a(a|1)*1|1(a|1)*a)(a|1)*"
    nfa = regex_to_nfa(pwd_regex, automaton_name="Password Verification")
    assert simulate(nfa, "a1").accepted
    assert simulate(nfa, "1a").accepted
    assert simulate(nfa, "aaa1").accepted
    assert simulate(nfa, "111a11").accepted
    assert simulate(nfa, "aaaa").accepted is False
    assert simulate(nfa, "1111").accepted is False
    assert simulate(nfa, "").accepted is False
    print("OK Password verification (regex (a|1)*(a(a|1)*1|1(a|1)*a)(a|1)* -> NFA)")


def test_clean_dfa_generation():
    # Verify regex -> clean minimal DFA eliminates state explosion:
    # ATM PIN [0-9]{4}: 152 raw NFA states -> exactly 5 clean DFA states!
    pin = regex_to_clean_dfa("[0-9]{4}", "ATM PIN (Clean)")
    assert len(pin.states) == 5, f"Expected 5 states, got {len(pin.states)}"
    assert pin.is_deterministic()
    assert simulate(pin, "1234").accepted
    assert simulate(pin, "123").accepted is False

    # Email [a-c]+@[a-c]+\.[a-c]+: 40 raw NFA states -> exactly 6 clean DFA states!
    email = regex_to_clean_dfa("[a-c]+@[a-c]+\\.[a-c]+", "Email (Clean)")
    assert len(email.states) == 6, f"Expected 6 states, got {len(email.states)}"
    assert simulate(email, "a@b.c").accepted
    assert simulate(email, "a@b").accepted is False

    # Password: 42 raw NFA states -> exactly 4 clean DFA states!
    pwd = regex_to_clean_dfa("(a|1)*(a(a|1)*1|1(a|1)*a)(a|1)*", "Password (Clean)")
    assert len(pwd.states) == 4, f"Expected 4 states, got {len(pwd.states)}"
    assert simulate(pwd, "a1").accepted
    assert simulate(pwd, "aaaa").accepted is False

    # Textbook (a|b)*abb: 14 raw states -> exactly 4 clean DFA states!
    abb = regex_to_clean_dfa("(a|b)*abb", "abb (Clean)")
    assert len(abb.states) == 4, f"Expected 4 states, got {len(abb.states)}"
    assert simulate(abb, "abb").accepted
    assert simulate(abb, "ab").accepted is False
    print("OK clean minimal DFA generation (no state explosion)")


if __name__ == "__main__":
    test_simulation()
    test_subset_construction()
    test_epsilon_nfa()
    test_minimization()
    test_properties()
    test_regex_to_nfa()
    test_automaton_to_regex()
    test_operations()
    test_word_generator_and_batch()
    test_exporters()
    test_atm_pin_verification()
    test_email_validation()
    test_password_verification()
    test_clean_dfa_generation()
    print("\nAll algorithm smoke tests passed.")
