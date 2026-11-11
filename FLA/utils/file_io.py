"""Project persistence, format export (PNG, PDF, DOT, TikZ, JFLAP) and import helpers."""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from models.automaton import EPSILON, Automaton

PROJECT_EXTENSION = ".afjson"


def save_project(path: str, automaton: Automaton) -> None:
    data = automaton.to_dict()
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_project(path: str) -> Automaton:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return Automaton.from_dict(data)


def export_scene_png(scene, path: str, padding: int = 20) -> None:
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QImage, QPainter

    rect = scene.itemsBoundingRect().adjusted(-padding, -padding, padding, padding)
    if rect.isEmpty():
        rect = QRectF(0, 0, 400, 300)
    image = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
    image.fill(0xFFFFFFFF)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    scene.render(painter, source=rect)
    painter.end()
    image.save(path)


def export_pdf(
    path: str,
    automaton: Automaton,
    image_path: Optional[str] = None,
    simulation_summary: Optional[List[Tuple[str, str]]] = None,
    properties_summary: Optional[List[str]] = None,
) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(path, pagesize=A4)
    story = []

    story.append(Paragraph(f"Automaton: {automaton.name}", styles["Title"]))
    story.append(Spacer(1, 0.4 * cm))

    kind = "DFA (Deterministic)" if automaton.is_deterministic() else "NFA (Non-deterministic)"
    story.append(Paragraph(f"Type: {kind}", styles["Normal"]))
    story.append(Paragraph(f"States: {', '.join(automaton.states) or '(none)'}", styles["Normal"]))
    story.append(Paragraph(f"Alphabet: {', '.join(automaton.alphabet) or '(empty)'}", styles["Normal"]))
    story.append(Paragraph(f"Start state: {automaton.start_state or '(undefined)'}", styles["Normal"]))
    story.append(Paragraph(
        f"Accepting states: {', '.join(sorted(automaton.accept_states)) or '(none)'}",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("Transition table", styles["Heading2"]))
    header = ["State"] + list(automaton.alphabet)
    rows = [header]
    for state in automaton.states:
        row = [state]
        for symbol in automaton.alphabet:
            targets = automaton.targets(state, symbol)
            row.append(", ".join(sorted(targets)) if targets else "-")
        rows.append(row)
    table = Table(rows, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d5f8b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5 * cm))

    if properties_summary:
        story.append(Paragraph("Properties", styles["Heading2"]))
        for line in properties_summary:
            story.append(Paragraph(f"• {line}", styles["Normal"]))
        story.append(Spacer(1, 0.5 * cm))

    if image_path and Path(image_path).exists():
        story.append(Paragraph("Diagram", styles["Heading2"]))
        story.append(Image(image_path, width=16 * cm, height=10 * cm, kind="proportional"))
        story.append(Spacer(1, 0.5 * cm))

    if simulation_summary:
        story.append(Paragraph("Simulation Result", styles["Heading2"]))
        for label, value in simulation_summary:
            story.append(Paragraph(f"<b>{label}:</b> {value}", styles["Normal"]))

    doc.build(story)


# ------------------------------------------------------------------
# Multi-format Exporters & JFLAP Import
# ------------------------------------------------------------------

def to_dot(automaton: Automaton) -> str:
    """Generate Graphviz DOT format for the automaton."""
    lines = [
        "digraph finite_state_machine {",
        '  rankdir=LR;',
        '  size="8,5";',
        '  node [fontname="Helvetica,Arial,sans-serif"];',
        '  edge [fontname="Helvetica,Arial,sans-serif"];',
    ]

    accepting = sorted(automaton.accept_states)
    if accepting:
        names = " ".join(f'"{s}"' for s in accepting)
        lines.append(f"  node [shape = doublecircle]; {names};")

    lines.append("  node [shape = circle];")

    if automaton.start_state is not None:
        lines.append('  __start [shape = none, label = "", width = 0, height = 0];')
        lines.append(f'  __start -> "{automaton.start_state}";')

    edges: Dict[Tuple[str, str], List[str]] = {}
    for src in automaton.states:
        for sym, dests in automaton.transitions.get(src, {}).items():
            sym_label = "ε" if sym == EPSILON else sym
            for dst in dests:
                edges.setdefault((src, dst), []).append(sym_label)

    for (src, dst), symbols in sorted(edges.items()):
        label = ", ".join(sorted(symbols))
        lines.append(f'  "{src}" -> "{dst}" [label = "{label}"];')

    lines.append("}")
    return "\n".join(lines)


def to_mermaid(automaton: Automaton) -> str:
    """Generate a Mermaid.js state-diagram string for the automaton.

    Mermaid renders in GitHub Markdown, Notion, Obsidian, and many wikis,
    which makes this a very practical modern export format.
    """
    lines = ["stateDiagram-v2"]
    if automaton.start_state is not None:
        lines.append(f'    [*] --> {automaton.start_state}')

    edges: Dict[Tuple[str, str], List[str]] = {}
    for src in automaton.states:
        for sym, dests in automaton.transitions.get(src, {}).items():
            sym_label = "ε" if sym == EPSILON else sym
            for dst in dests:
                edges.setdefault((src, dst), []).append(sym_label)

    for (src, dst), symbols in sorted(edges.items()):
        label = ", ".join(sorted(symbols))
        lines.append(f'    {src} --> {dst} : {label}')

    for st in sorted(automaton.accept_states):
        lines.append(f'    {st} --> [*]')

    return "\n".join(lines)


def to_tikz(automaton: Automaton) -> str:
    """Generate LaTeX TikZ format using the 'automata' TikZ library."""
    lines = [
        r"% Requires: \usepackage{tikz}",
        r"% \usetikzlibrary{automata, positioning, arrows}",
        r"\begin{tikzpicture}[shorten >=1pt, node distance=2.8cm, on grid, auto, >=stealth]",
    ]

    has_pos = bool(automaton.positions)
    scale = 0.025

    for s in automaton.states:
        options = ["state"]
        if s == automaton.start_state:
            options.append("initial")
        if s in automaton.accept_states:
            options.append("accepting")

        opt_str = ", ".join(options)
        if has_pos and s in automaton.positions:
            px, py = automaton.positions[s]
            lines.append(f"  \\node[{opt_str}] ({s}) at ({round(px * scale, 2)},{round(-py * scale, 2)}) {{{s}}};")
        else:
            lines.append(f"  \\node[{opt_str}] ({s}) {{{s}}};")

    lines.append(r"  \path[->]")
    for src in automaton.states:
        for sym, dests in automaton.transitions.get(src, {}).items():
            sym_tex = r"$\varepsilon$" if sym == EPSILON else sym
            for dst in dests:
                if src == dst:
                    lines.append(f"    ({src}) edge [loop above] node {{{sym_tex}}} ({dst})")
                else:
                    lines.append(f"    ({src}) edge node {{{sym_tex}}} ({dst})")

    lines.append("  ;")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def to_jflap_xml(automaton: Automaton) -> str:
    """Generate JFLAP 7 (.jff) XML for the automaton."""
    root = ET.Element("structure")
    type_el = ET.SubElement(root, "type")
    type_el.text = "fa"
    automaton_el = ET.SubElement(root, "automaton")
    state_to_id: Dict[str, int] = {s: i for i, s in enumerate(automaton.states)}

    for s, idx in state_to_id.items():
        state_el = ET.SubElement(automaton_el, "state", id=str(idx), name=s)
        px, py = automaton.positions.get(s, (100.0 + idx * 80, 150.0))
        x_el = ET.SubElement(state_el, "x")
        x_el.text = str(round(px, 1))
        y_el = ET.SubElement(state_el, "y")
        y_el.text = str(round(py, 1))

        if s == automaton.start_state:
            ET.SubElement(state_el, "initial")
        if s in automaton.accept_states:
            ET.SubElement(state_el, "final")

    for src in automaton.states:
        src_id = str(state_to_id[src])
        for sym, dests in automaton.transitions.get(src, {}).items():
            sym_read = "" if sym == EPSILON else sym
            for dst in dests:
                dst_id = str(state_to_id[dst])
                trans_el = ET.SubElement(automaton_el, "transition")
                ET.SubElement(trans_el, "from").text = src_id
                ET.SubElement(trans_el, "to").text = dst_id
                ET.SubElement(trans_el, "read").text = sym_read

    raw = ET.tostring(root, encoding="utf-8").decode("utf-8")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<!-- Created with AutomataForge -->\n{raw}'


def from_jflap_xml(xml_content: str) -> Automaton:
    """Parse JFLAP 7 (.jff) XML format into an Automaton."""
    root = ET.fromstring(xml_content)
    automaton_el = root.find("automaton")
    if automaton_el is None:
        raise ValueError("Invalid JFLAP XML: missing <automaton> element.")

    id_to_name: Dict[str, str] = {}
    states: List[str] = []
    positions: Dict[str, Tuple[float, float]] = {}
    accept_states: Set[str] = set()
    start_state: Optional[str] = None

    for state_el in automaton_el.findall("state"):
        s_id = state_el.attrib.get("id", "")
        s_name = state_el.attrib.get("name", f"q{s_id}")
        id_to_name[s_id] = s_name
        states.append(s_name)
        x_el, y_el = state_el.find("x"), state_el.find("y")
        if x_el is not None and y_el is not None and x_el.text and y_el.text:
            try:
                positions[s_name] = (float(x_el.text), float(y_el.text))
            except ValueError:
                pass
        if state_el.find("initial") is not None:
            start_state = s_name
        if state_el.find("final") is not None:
            accept_states.add(s_name)

    alphabet_set: Set[str] = set()
    transitions: Dict[str, Dict[str, Set[str]]] = {s: {} for s in states}

    for trans_el in automaton_el.findall("transition"):
        from_el, to_el, read_el = trans_el.find("from"), trans_el.find("to"), trans_el.find("read")
        if from_el is None or to_el is None or from_el.text is None or to_el.text is None:
            continue
        src = id_to_name.get(from_el.text.strip())
        dst = id_to_name.get(to_el.text.strip())
        if not src or not dst:
            continue
        sym_text = read_el.text.strip() if (read_el is not None and read_el.text) else ""
        sym = EPSILON if sym_text in {"", "ε", "\\e"} else sym_text
        transitions.setdefault(src, {}).setdefault(sym, set()).add(dst)
        if sym != EPSILON:
            alphabet_set.add(sym)

    return Automaton(
        name="Imported JFLAP Automaton",
        states=states,
        alphabet=sorted(alphabet_set),
        start_state=start_state or (states[0] if states else None),
        accept_states=accept_states,
        transitions=transitions,
        positions=positions,
    )
