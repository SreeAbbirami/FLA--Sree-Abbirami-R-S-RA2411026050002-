"""Right-side analysis panels: properties, NFA->DFA, minimization, DFA->NFA."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class PropertiesPanel(QWidget):
    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        layout = QVBoxLayout(self)
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)
        controller.model_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        report = self.controller.analyze_properties()
        lines = [
            f"<b>Deterministic (DFA)?</b> {'Yes' if report.is_deterministic else 'No'}",
            f"<b>Complete?</b> {'Yes' if report.is_complete else 'No'}",
            f"<b>Connected?</b> {'Yes' if report.is_connected else 'No'}",
            f"<b>Has ε-transitions?</b> {'Yes' if report.has_epsilon_transitions else 'No'}",
            f"<b>Unreachable states:</b> {', '.join(sorted(report.unreachable_states)) or 'none'}",
            f"<b>Dead states:</b> {', '.join(sorted(report.dead_states)) or 'none'}",
        ]
        if report.missing_transitions:
            lines.append("<b>Missing transitions (not complete):</b>")
            lines.append("<br>".join(report.missing_transitions[:30]))
        if report.validation_errors:
            lines.append("<b style='color:#f43f5e;'>Validation errors:</b>")
            lines.append("<br>".join(report.validation_errors))
        self.text.setHtml("<br>".join(lines))


class ConversionPanel(QWidget):
    """NFA -> DFA via subset construction, with a step-by-step table."""

    def __init__(self, controller, main_window, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.main_window = main_window
        self._result = None
        layout = QVBoxLayout(self)

        self.btn_convert = QPushButton("Convert NFA → DFA (subset construction)")
        layout.addWidget(self.btn_convert)

        self.table = QTableWidget(0, 1)
        layout.addWidget(QLabel("Subset Construction Table"))
        layout.addWidget(self.table)

        row = QHBoxLayout()
        self.btn_apply = QPushButton("Use as current automaton")
        self.btn_apply.setEnabled(False)
        row.addWidget(self.btn_apply)
        layout.addLayout(row)

        self.btn_convert.clicked.connect(self._convert)
        self.btn_apply.clicked.connect(self._apply)

    def _convert(self) -> None:
        try:
            result = self.controller.convert_nfa_to_dfa()
        except ValueError as e:
            QMessageBox.warning(self, "Could not convert", str(e))
            return
        self._result = result
        alphabet = result.dfa.alphabet
        headers = ["DFA State", "NFA Subset"] + alphabet
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(result.steps))
        for i, step in enumerate(result.steps):
            self.table.setItem(i, 0, QTableWidgetItem(step.dfa_state))
            self.table.setItem(i, 1, QTableWidgetItem("{" + ",".join(sorted(step.source_nfa_states)) + "}"))
            for j, symbol in enumerate(alphabet):
                self.table.setItem(i, 2 + j, QTableWidgetItem(step.transitions.get(symbol, "-")))
        self.table.resizeColumnsToContents()
        self.btn_apply.setEnabled(True)
        self.main_window.show_status(
            f"DFA generated with {len(result.dfa.states)} states from {len(self.controller.automaton.states)} NFA states."
        )

    def _apply(self) -> None:
        if self._result:
            self.controller.replace_automaton(self._result.dfa)
            self.main_window.show_status("Automaton replaced by equivalent DFA.")


class MinimizationPanel(QWidget):
    def __init__(self, controller, main_window, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.main_window = main_window
        self._result = None
        layout = QVBoxLayout(self)

        self.btn_minimize = QPushButton("Minimize DFA (Moore)")
        layout.addWidget(self.btn_minimize)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(QLabel("Partitions per iteration"))
        layout.addWidget(self.text)

        self.btn_apply = QPushButton("Use as current automaton")
        self.btn_apply.setEnabled(False)
        layout.addWidget(self.btn_apply)

        self.btn_minimize.clicked.connect(self._minimize)
        self.btn_apply.clicked.connect(self._apply)

    def _minimize(self) -> None:
        try:
            result = self.controller.minimize()
        except ValueError as e:
            QMessageBox.warning(self, "Could not minimize", str(e))
            return
        self._result = result
        lines = []
        if result.removed_unreachable:
            lines.append(f"Unreachable states removed before minimizing: {', '.join(sorted(result.removed_unreachable))}")
        for step in result.steps:
            groups = " | ".join("{" + ",".join(sorted(g)) + "}" for g in step.groups)
            lines.append(f"<b>{step.description}</b><br>{groups}")
        lines.append(f"<br><b>Result:</b> {len(result.dfa.states)} states in the minimal DFA.")
        self.text.setHtml("<br><br>".join(lines))
        self.btn_apply.setEnabled(True)
        self.main_window.show_status(f"DFA minimized to {len(result.dfa.states)} states.")

    def _apply(self) -> None:
        if self._result:
            self.controller.replace_automaton(self._result.dfa)
            self.main_window.show_status("Automaton replaced by minimal DFA.")


class DfaToNfaPanel(QWidget):
    def __init__(self, controller, main_window, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.main_window = main_window
        self._result = None
        layout = QVBoxLayout(self)

        info = QLabel(
            "Every DFA is also a valid NFA. This produces an equivalent copy of the current automaton "
            "ready to extend with non-deterministic or epsilon transitions."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.btn_convert = QPushButton("Generate equivalent NFA")
        layout.addWidget(self.btn_convert)

        self.btn_apply = QPushButton("Use as current automaton")
        self.btn_apply.setEnabled(False)
        layout.addWidget(self.btn_apply)
        layout.addStretch(1)

        self.btn_convert.clicked.connect(self._convert)
        self.btn_apply.clicked.connect(self._apply)

    def _convert(self) -> None:
        self._result = self.controller.convert_dfa_to_nfa()
        self.btn_apply.setEnabled(True)
        self.main_window.show_status("Equivalent NFA generated.")

    def _apply(self) -> None:
        if self._result:
            self.controller.replace_automaton(self._result)
            self.main_window.show_status("Automaton replaced by equivalent NFA.")


class HistoryPanel(QWidget):
    """Shows the most recent simulations and conversions performed."""

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Recent simulations"))
        self.sim_text = QTextEdit()
        self.sim_text.setReadOnly(True)
        layout.addWidget(self.sim_text)
        layout.addWidget(QLabel("Recent conversions"))
        self.conv_text = QTextEdit()
        self.conv_text.setReadOnly(True)
        layout.addWidget(self.conv_text)

    def refresh(self) -> None:
        sim_lines = []
        for result in self.controller.simulation_log[:10]:
            verdict = "ACCEPTED" if result.accepted else "REJECTED"
            text = result.input_string or "(empty string)"
            sim_lines.append(f"'{text}' → {verdict}")
        self.sim_text.setPlainText("\n".join(sim_lines) or "No simulations yet.")
        self.conv_text.setPlainText("\n".join(self.controller.conversion_log[:10]) or "No conversions yet.")


class RandomGeneratorPanel(QWidget):
    """Generate a random DFA or NFA with configurable parameters."""

    def __init__(self, controller, main_window, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.main_window = main_window
        layout = QVBoxLayout(self)

        info = QLabel(
            "Generate a random finite automaton for quick experiments, "
            "testing, or classroom demos. Adjust the parameters and click Generate."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        row = QHBoxLayout()
        row.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["DFA", "NFA"])
        row.addWidget(self.type_combo)
        layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("States:"))
        self.states_spin = QSpinBox()
        self.states_spin.setRange(1, 30)
        self.states_spin.setValue(5)
        row.addWidget(self.states_spin)
        layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Alphabet size:"))
        self.alphabet_spin = QSpinBox()
        self.alphabet_spin.setRange(1, 10)
        self.alphabet_spin.setValue(2)
        row.addWidget(self.alphabet_spin)
        layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Transition density:"))
        self.density_spin = QDoubleSpinBox()
        self.density_spin.setRange(0.05, 1.0)
        self.density_spin.setSingleStep(0.05)
        self.density_spin.setValue(1.0)
        row.addWidget(self.density_spin)
        layout.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(QLabel("Accept ratio:"))
        self.accept_spin = QDoubleSpinBox()
        self.accept_spin.setRange(0.0, 1.0)
        self.accept_spin.setSingleStep(0.05)
        self.accept_spin.setValue(0.4)
        row.addWidget(self.accept_spin)
        layout.addLayout(row)

        self.epsilon_check = QCheckBox("Allow ε-transitions (NFA only)")
        self.epsilon_check.setChecked(True)
        layout.addWidget(self.epsilon_check)

        self.non_det_spin = QDoubleSpinBox()
        self.non_det_spin.setRange(0.0, 1.0)
        self.non_det_spin.setSingleStep(0.05)
        self.non_det_spin.setValue(0.3)
        row = QHBoxLayout()
        row.addWidget(QLabel("Non-determinism (NFA):"))
        row.addWidget(self.non_det_spin)
        layout.addLayout(row)

        self.btn_generate = QPushButton("Generate random automaton")
        layout.addWidget(self.btn_generate)
        layout.addStretch(1)

        self.btn_generate.clicked.connect(self._generate)

    def _generate(self) -> None:
        alphabet = [chr(ord("a") + i) for i in range(self.alphabet_spin.value())]
        try:
            if self.type_combo.currentText() == "DFA":
                self.controller.generate_random_dfa(
                    num_states=self.states_spin.value(),
                    alphabet=alphabet,
                    density=self.density_spin.value(),
                    accept_ratio=self.accept_spin.value(),
                )
            else:
                self.controller.generate_random_nfa(
                    num_states=self.states_spin.value(),
                    alphabet=alphabet,
                    density=self.density_spin.value(),
                    epsilon_prob=0.15 if self.epsilon_check.isChecked() else 0.0,
                    accept_ratio=self.accept_spin.value(),
                    nondeterminism=self.non_det_spin.value(),
                )
        except ValueError as e:
            QMessageBox.warning(self, "Could not generate", str(e))
            return
        self.main_window.show_status(
            f"Generated random {self.type_combo.currentText()} with "
            f"{self.states_spin.value()} states."
        )


class DistributionPanel(QWidget):
    """Word-length distribution: how many accepted strings exist at each length."""

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        row.addWidget(QLabel("Max length:"))
        self.max_len_spin = QSpinBox()
        self.max_len_spin.setRange(1, 30)
        self.max_len_spin.setValue(10)
        row.addWidget(self.max_len_spin)
        self.btn_refresh = QPushButton("Compute")
        row.addWidget(self.btn_refresh)
        layout.addLayout(row)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

        self.btn_refresh.clicked.connect(self.refresh)
        controller.model_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        try:
            dist = self.controller.word_length_distribution(self.max_len_spin.value())
        except Exception:
            self.text.setPlainText("Could not compute distribution.")
            return
        total = sum(dist.values())
        lines = [f"Accepted strings per length (0..{self.max_len_spin.value()}) — total: {total}", ""]
        max_count = max(dist.values()) if dist else 0
        for n in range(self.max_len_spin.value() + 1):
            count = dist[n]
            bar = "█" * count if count > 0 else ""
            lines.append(f"len {n:>2}: {count} {bar}")
        if max_count == 0:
            lines.append("")
            lines.append("(No accepted strings in this range — language may be empty.)")
        self.text.setPlainText("\n".join(lines))


class AnalysisTabs(QTabWidget):
    def __init__(self, controller, main_window, parent=None) -> None:
        super().__init__(parent)
        self.addTab(PropertiesPanel(controller), "Properties")
        self.addTab(ConversionPanel(controller, main_window), "NFA → DFA")
        self.addTab(MinimizationPanel(controller, main_window), "Minimize DFA")
        self.addTab(DfaToNfaPanel(controller, main_window), "DFA → NFA")
        self.addTab(RandomGeneratorPanel(controller, main_window), "Random Gen")
        self.addTab(DistributionPanel(controller), "Distribution")
        self.history_panel = HistoryPanel(controller)
        self.addTab(self.history_panel, "History")
