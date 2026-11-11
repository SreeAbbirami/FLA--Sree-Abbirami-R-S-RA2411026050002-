# FLA--Sree-Abbirami-R-S-RA2411026050002-

# AutomataForge

**Build, simulate, convert and analyse finite automata — in your browser or on your desktop.**

An advanced educational tool for creating, editing, converting, simulating and analysing
Deterministic (DFA) and Non-deterministic (NFA) Finite Automata, including
ε-transitions, Regular Expressions, and Language Algebra. It exists in two forms that
share the same file format and algorithms: a **modern web app** that runs entirely in
the browser, and a **Python desktop app** built with PyQt6.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

> 🌐 **Try it now — no installation:** open `web/index.html` in any modern browser.
>
> 💻 **Prefer a desktop app?** Run `python main.py` after installing the requirements (Windows, macOS, Linux).

---

## Advanced Features

**Editing & Interactive Canvas**
- Visual editor for states, alphabet and transitions, with ε-transitions
- Interactive canvas: drag states, zoom with the scroll wheel, pan
- **Double-click canvas to create a new state** at your cursor position
- Multiple auto-layout algorithms:
  - **Circular layout**: cleanly spaces states in a circle
  - **Layered (DAG) layout**: topological left-to-right layering ideal for sequential automata
  - **Force-directed / Spring layout**: organic physical simulation untangling complex graphs
- Accepting states, start state, renaming, full undo/redo history (Ctrl+Z / Ctrl+Y)
- Live validation with clear diagnostic error messages

**Regular Expressions & Finite Automata**
- **Regex ➔ NFA (Thompson's Construction)**: Build an equivalent ε-NFA directly from any regular expression (`[0-9]{4}`, `(a|b)*abb`, `(0|1)*00`, `a+b?`, etc.) with automatic layered DAG layout.
- **Automaton ➔ Regular Expression (State Elimination GNFA)**: Convert any finite automaton into its equivalent regular expression step-by-step. Inspect each intermediate state elimination and copy the resulting closed-form regex with one click.
- **Real-World Verification Presets**:
  - **ATM PIN Verification**: Validates strict 4-digit bank credentials using regex `[0-9]{4}` and minimal 5-state DFA.
  - **Email Validation**: Validates `user@domain.ext` format over alphanumeric and symbol sets using regex `[a-c]+@[a-c]+\.[a-c]+`.
  - **Password Verification**: Validates complexity policies requiring at least one letter and at least one digit via `(a|1)*(a(a|1)*1|1(a|1)*a)(a|1)*`.

**Automata Operations & Algebra of Regular Languages**
- **DFA Completion**: Auto-complete missing transitions into a trap/dead state.
- **DFA Complementation ($L'$)**: Inverts accept states of a complete DFA to recognize the complement language $\Sigma^* \setminus L$.
- **Intersection ($L_1 \cap L_2$)**: Product automaton construction for the intersection of two DFAs.
- **Union ($L_1 \cup L_2$)**: Cross-product or Thompson union for two automata.
- **Equivalence & Inclusion Checker**: Test if $L(M_1) == L(M_2)$ or $L(M_1) \subseteq L(M_2)$. If automata are not equivalent, automatically finds and displays the **shortest counterexample string**!

**Language Analysis & Batch Testing**
- **Language Properties**: Detects whether the language is empty ($L = \emptyset$), finite, or infinite ($L = \infty$).
- **Shortlex Accepted Word Generator**: Generates the shortest accepted strings in lexicographical order.
- **Word-Length Distribution**: Dynamic-programming analysis showing which string lengths the language accepts.
- **Random Automaton Generator**: Instantly create a random DFA or NFA with configurable states, alphabet size, transition density and accept ratio (NFAs may include ε-transitions).
- **Batch Test Suite**: Run multiple test strings at once with instant PASS/FAIL status indicators and active final states.

**Simulation**
- Step-by-step simulation of any automaton (DFA or NFA alike) by tracking the set of active states
- Active states and the edges just taken are highlighted on the diagram in real time
- Walk forward and backward through the run, jump to first/last, or auto-play with adjustable speed
- Input tape showing exactly which symbol is being consumed

**Interoperability & Export**
- **JSON (.afjson)**: Save and open projects — compatible across both web and desktop apps.
- **JFLAP 7 (.jff) XML**: Full export and import compatibility with the widely used academic tool JFLAP.
- **Graphviz DOT (.dot)**: Export clean Graphviz digraph source code.
- **Mermaid (.mmd)**: Export a `stateDiagram-v2` that renders in GitHub, Notion, Obsidian and most wikis.
- **LaTeX TikZ (.tex)**: Export publication-ready TikZ code for papers, homework, and slides.
- **Vector SVG & High-res PNG**: Direct diagram download.
- **Printable PDF report**: Includes diagram, structural properties, and full transition table.

---

## Project Structure

```
automata-studio/
├── main.py                     # Desktop entry point
├── requirements.txt
├── models/automaton.py         # Automaton data model (DFA and NFA unified class)
├── algorithms/                 # Clean, consolidated algorithms package
│   ├── conversions.py          # Regex ↔ NFA/DFA, GNFA, complement, product, equivalence
│   ├── minimization.py         # Moore partition refinement algorithm
│   ├── properties.py           # Structural analysis, finiteness, emptiness, word-length distribution
│   ├── random_gen.py           # Random DFA / NFA generator
│   ├── simulation.py           # Active-state set simulation, shortlex generator, batch testing
│   └── subset_construction.py  # NFA to DFA subset construction
├── controllers/                # Mediator between model, algorithms, and views
├── views/                      # Main window, editor panels, canvas
├── utils/                      # File I/O (JSON, JFLAP, DOT, TikZ, Mermaid), validators, history
├── resources/                  # Preloaded examples and app icon
├── tests/                      # Python unit test suite
├── examples/                   # Clean sample .afjson automata (ATM PIN, Email, Password, etc.)
└── web/                        # The web version (fully static)
    ├── index.html
    ├── css/styles.css
    ├── js/
    │   ├── automaton.js        # Data model + JSON serialization
    │   ├── algorithms.js       # Complete port of algorithms/
    │   ├── examples.js         # Bundled examples
    │   ├── graph.js            # SVG renderer: spring, circular & DAG layouts
    │   └── app.js              # UI wiring, batch tests, equivalence, exporters
    └── tests/                  # Node test suite mirroring Python test suite
```

---

## Running Locally

### Web App

Static site — runs in any modern browser without installation or build step:

```bash
cd web
python -m http.server 8000
# open http://localhost:8000
```

Opening `web/index.html` directly from your file system (`file://`) also works.

### Desktop App

Requires Python 3.10+ and PyQt6:

```bash
pip install -r requirements.txt
python main.py
```

---

## Tests

Both the Python backend and JavaScript browser engine have synchronized unit test suites:

```bash
node web/tests/run-tests.js      # JavaScript port (136 checks, 0 failures)
python tests/test_algorithms.py  # Python algorithm test suite
```

Both test suites verify:
1. NFA simulation & step tracing
2. NFA ➔ DFA subset construction
3. ε-NFA handling
4. DFA minimization by partition refinement
5. Properties analysis & reachability
6. Regex ➔ NFA (Thompson's construction)
7. Automaton ➔ Regex (GNFA state elimination)
8. Complementation, product intersection, product union
9. Equivalence checking & counterexample generation
10. Shortlex accepted string generation & batch testing
11. Multi-format exporters (Graphviz DOT, Mermaid, LaTeX TikZ, JFLAP XML) & JFLAP round-trip import
12. Real-world verification patterns (ATM PIN [0-9]{4}, Email validation, Password verification)
13. Random DFA / NFA generation (deterministic when seeded)
14. Word-length distribution over DFAs, NFAs and ε-NFAs

---

## License

[MIT](LICENSE) — free to use, modify, and share for educational and professional purposes.

[MIT](LICENSE) — free to use, modify, and share for educational and professional purposes.
