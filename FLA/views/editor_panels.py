"""Left-side editor panels: states, alphabet, transitions."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from models.automaton import EPSILON
from utils.validators import validate_state_name, validate_symbol, validate_transition


class StatesPanel(QWidget):
    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        layout.addWidget(QLabel("States"))
        layout.addWidget(self.list_widget)

        btn_row1 = QHBoxLayout()
        self.btn_add = QPushButton("+ Add")
        self.btn_remove = QPushButton("Delete")
        self.btn_remove.setObjectName("secondary")
        btn_row1.addWidget(self.btn_add)
        btn_row1.addWidget(self.btn_remove)
        layout.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        self.btn_rename = QPushButton("Rename")
        self.btn_rename.setObjectName("secondary")
        self.btn_start = QPushButton("Set start")
        self.btn_start.setObjectName("secondary")
        btn_row2.addWidget(self.btn_rename)
        btn_row2.addWidget(self.btn_start)
        layout.addLayout(btn_row2)

        self.btn_accept = QPushButton("Toggle accepting")
        layout.addWidget(self.btn_accept)

        self.btn_add.clicked.connect(self._add_state)
        self.btn_remove.clicked.connect(self._remove_state)
        self.btn_rename.clicked.connect(self._rename_state)
        self.btn_start.clicked.connect(self._set_start)
        self.btn_accept.clicked.connect(self._toggle_accept)

        controller.model_changed.connect(self.refresh)
        self.refresh()

    def _selected_name(self):
        item = self.list_widget.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _add_state(self) -> None:
        name, ok = QInputDialog.getText(self, "New State", "State name:")
        if not ok:
            return
        name = name.strip()
        error = validate_state_name(name, self.controller.automaton)
        if error:
            QMessageBox.warning(self, "Validation error", error)
            return
        self.controller.add_state(name)

    def _remove_state(self) -> None:
        name = self._selected_name()
        if not name:
            return
        if QMessageBox.question(self, "Confirm", f"Delete state '{name}'?") == QMessageBox.StandardButton.Yes:
            self.controller.remove_state(name)

    def _rename_state(self) -> None:
        name = self._selected_name()
        if not name:
            return
        new_name, ok = QInputDialog.getText(self, "Rename State", "New name:", text=name)
        if not ok:
            return
        new_name = new_name.strip()
        error = validate_state_name(new_name, self.controller.automaton, editing=name)
        if error:
            QMessageBox.warning(self, "Validation error", error)
            return
        self.controller.rename_state(name, new_name)

    def _set_start(self) -> None:
        name = self._selected_name()
        if name:
            self.controller.set_start_state(name)

    def _toggle_accept(self) -> None:
        name = self._selected_name()
        if name:
            self.controller.toggle_accept_state(name)

    def refresh(self) -> None:
        automaton = self.controller.automaton
        self.list_widget.clear()
        for state in automaton.states:
            label = state
            if state == automaton.start_state:
                label = "→ " + label
            if state in automaton.accept_states:
                label = label + "  (accepting)"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, state)
            self.list_widget.addItem(item)


class AlphabetPanel(QWidget):
    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(QLabel("Alphabet"))
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("+ Add")
        self.btn_remove = QPushButton("Delete")
        self.btn_remove.setObjectName("secondary")
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_remove)
        layout.addLayout(btn_row)

        self.btn_add.clicked.connect(self._add_symbol)
        self.btn_remove.clicked.connect(self._remove_symbol)

        controller.model_changed.connect(self.refresh)
        self.refresh()

    def _add_symbol(self) -> None:
        symbol, ok = QInputDialog.getText(self, "New Symbol", "Alphabet symbol:")
        if not ok:
            return
        symbol = symbol.strip()
        error = validate_symbol(symbol, self.controller.automaton)
        if error:
            QMessageBox.warning(self, "Validation error", error)
            return
        self.controller.add_symbol(symbol)

    def _remove_symbol(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            return
        symbol = item.text()
        self.controller.remove_symbol(symbol)

    def refresh(self) -> None:
        self.list_widget.clear()
        self.list_widget.addItems(self.controller.automaton.alphabet)


class TransitionsPanel(QWidget):
    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Transitions"))

        form = QHBoxLayout()
        self.combo_source = QComboBox()
        self.combo_symbol = QComboBox()
        self.combo_target = QComboBox()
        form.addWidget(self.combo_source)
        form.addWidget(self.combo_symbol)
        form.addWidget(self.combo_target)
        layout.addLayout(form)

        self.btn_add = QPushButton("+ Add transition")
        layout.addWidget(self.btn_add)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["From", "Symbol", "To"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.btn_remove = QPushButton("Delete selected")
        self.btn_remove.setObjectName("secondary")
        layout.addWidget(self.btn_remove)

        self.btn_add.clicked.connect(self._add_transition)
        self.btn_remove.clicked.connect(self._remove_transition)

        controller.model_changed.connect(self.refresh)
        self.refresh()

    def _add_transition(self) -> None:
        source = self.combo_source.currentText()
        symbol = self.combo_symbol.currentText()
        target = self.combo_target.currentText()
        error = validate_transition(source, symbol, target, self.controller.automaton)
        if error:
            QMessageBox.warning(self, "Validation error", error)
            return
        self.controller.add_transition(source, symbol, target)

    def _remove_transition(self) -> None:
        row = self.table.currentRow()
        if row < 0:
            return
        source = self.table.item(row, 0).text()
        symbol = self.table.item(row, 1).text()
        target = self.table.item(row, 2).text()
        self.controller.remove_transition(source, symbol, target)

    def refresh(self) -> None:
        automaton = self.controller.automaton
        for combo in (self.combo_source, self.combo_target):
            current = combo.currentText()
            combo.clear()
            combo.addItems(automaton.states)
            idx = combo.findText(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)

        current_symbol = self.combo_symbol.currentText()
        self.combo_symbol.clear()
        self.combo_symbol.addItems(automaton.alphabet + [EPSILON])
        idx = self.combo_symbol.findText(current_symbol)
        if idx >= 0:
            self.combo_symbol.setCurrentIndex(idx)

        rows = automaton.all_transition_rows()
        self.table.setRowCount(len(rows))
        for i, (src, sym, dst) in enumerate(sorted(rows)):
            self.table.setItem(i, 0, QTableWidgetItem(src))
            self.table.setItem(i, 1, QTableWidgetItem(sym))
            self.table.setItem(i, 2, QTableWidgetItem(dst))
        self.table.resizeColumnsToContents()


class RegexPanel(QWidget):
    """Builds an optimal clean DFA or raw Thompson NFA from regular expressions."""

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Regular Expression:"))
        self.input_regex = QLineEdit()
        self.input_regex.setPlaceholderText("e.g. [0-9]{4} or (a|b)*abb")
        layout.addWidget(self.input_regex)

        self.btn_build_clean = QPushButton("Build Clean Diagram (Best)")
        layout.addWidget(self.btn_build_clean)

        self.btn_build_raw = QPushButton("Build Raw ε-NFA (Thompson)")
        self.btn_build_raw.setObjectName("secondary")
        layout.addWidget(self.btn_build_raw)

        layout.addWidget(QLabel("Verification Presets (Click to Load):"))
        btn_pin = QPushButton("ATM PIN: [0-9]{4}")
        btn_email = QPushButton("Email: [a-c]+@[a-c]+\\.[a-c]+")
        btn_pwd = QPushButton("Password: (a|1)*(a(a|1)*1|1(a|1)*a)(a|1)*")
        btn_ab = QPushButton("(a|b)*abb")

        for b in (btn_pin, btn_email, btn_pwd, btn_ab):
            b.setObjectName("secondary")
            layout.addWidget(b)

        btn_pin.clicked.connect(lambda: self._apply_preset("[0-9]{4}"))
        btn_email.clicked.connect(lambda: self._apply_preset("[a-c]+@[a-c]+\\.[a-c]+"))
        btn_pwd.clicked.connect(lambda: self._apply_preset("(a|1)*(a(a|1)*1|1(a|1)*a)(a|1)*"))
        btn_ab.clicked.connect(lambda: self._apply_preset("(a|b)*abb"))

        self.btn_build_clean.clicked.connect(self._build_clean)
        self.btn_build_raw.clicked.connect(self._build_raw)
        layout.addStretch()

    def _apply_preset(self, rx: str) -> None:
        self.input_regex.setText(rx)
        self._build_clean()

    def _build_clean(self) -> None:
        text = self.input_regex.text().strip()
        if not text:
            return
        try:
            self.controller.from_regex(text, name=f"DFA: {text}", clean=True)
        except Exception as e:
            QMessageBox.warning(self, "Regex Error", str(e))

    def _build_raw(self) -> None:
        text = self.input_regex.text().strip()
        if not text:
            return
        try:
            self.controller.from_regex(text, name=f"NFA from {text}", clean=False)
        except Exception as e:
            QMessageBox.warning(self, "Regex Error", str(e))


class EditorTabs(QTabWidget):
    """Combines the states, alphabet, transitions, and regex editors into one dock widget."""

    def __init__(self, controller, parent=None) -> None:
        super().__init__(parent)
        self.states_panel = StatesPanel(controller)
        self.alphabet_panel = AlphabetPanel(controller)
        self.transitions_panel = TransitionsPanel(controller)
        self.regex_panel = RegexPanel(controller)
        self.addTab(self.states_panel, "States")
        self.addTab(self.alphabet_panel, "Alphabet")
        self.addTab(self.transitions_panel, "Transitions")
        self.addTab(self.regex_panel, "Regex")
