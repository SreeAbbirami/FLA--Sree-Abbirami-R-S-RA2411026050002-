"""Main application window: menu, toolbar, docks and central graph canvas."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QActionGroup, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QStyle,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from controllers.automaton_controller import AutomatonController
from models.automaton import Automaton
from resources.examples import EXAMPLES
from utils import file_io, theme
from views.editor_panels import EditorTabs
from views.graph_view import AutomatonGraphView
from views.info_panels import AnalysisTabs
from views.simulation_panel import SimulationPanel

HELP_TEXT = """
<h2>AutomataForge — Quick Guide</h2>
<p><b>1. Create an automaton:</b> Use the left panel (States tab) to add states,
the Alphabet tab to define symbols, and the Transitions tab to connect states.</p>
<p><b>2. Mark states:</b> Select a state and use "Set start" or "Toggle accepting".</p>
<p><b>3. Visual canvas:</b> The center panel draws the automaton automatically. Drag
states with the mouse to rearrange, and use the scroll wheel to zoom.</p>
<p><b>4. Simulate strings:</b> Type a string in the bottom panel and click "Simulate". Use
First / Prev / Next / Auto controls to step through symbol-by-symbol with active states highlighted in red.</p>
<p><b>5. Convert and minimize:</b> Use the right panel to convert NFA → DFA (subset construction),
DFA → NFA, or minimize a DFA (Moore). Each operation displays the step-by-step process before applying.</p>
<p><b>6. Analyze properties:</b> The Properties tab displays determinism, completeness, connectedness,
and flags unreachable or dead states.</p>
<p><b>7. Save and export:</b> Use the File menu to save projects (.afjson), or export the
diagram as a PNG image or comprehensive PDF report.</p>
<p><b>8. Examples:</b> The Examples menu includes preloaded DFA and NFA automata to practice with.</p>
"""


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AutomataForge — Finite Automata Editor")
        self.resize(1400, 900)

        self.controller = AutomatonController()
        self.current_file_path: Optional[str] = None
        self.dark_mode = False

        # Branded header strip that sits above the canvas
        self.header = self._build_header()

        self.graph_view = AutomatonGraphView(self.controller)

        central = QWidget()
        central.setObjectName("centralWidget")
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.header)
        central_layout.addWidget(self.graph_view, 1)
        self.setCentralWidget(central)

        self.editor_tabs = EditorTabs(self.controller)
        self.left_dock = QDockWidget("Automaton Editor", self)
        self.left_dock.setWidget(self.editor_tabs)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.left_dock)

        self.analysis_tabs = AnalysisTabs(self.controller, self)
        self.right_dock = QDockWidget("Analysis & Conversions", self)
        self.right_dock.setWidget(self.analysis_tabs)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.right_dock)

        self.simulation_panel = SimulationPanel(self.controller, self.graph_view, self)
        self.bottom_dock = QDockWidget("Step-by-step Simulation", self)
        self.bottom_dock.setWidget(self.simulation_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_dock)

        self._build_actions()
        self._build_menu()
        self._build_toolbar()
        self.statusBar().showMessage("Ready.")

        self.controller.model_changed.connect(self._on_model_changed)
        self.controller.history_changed.connect(self._update_undo_redo_actions)
        self._update_undo_redo_actions()
        self._update_window_title()

    # ------------------------------------------------------------------
    def show_status(self, message: str, timeout: int = 5000) -> None:
        self.statusBar().showMessage(message, timeout)

    def refresh_history_panel(self) -> None:
        self.analysis_tabs.history_panel.refresh()

    def _on_model_changed(self) -> None:
        self._update_window_title()

    def _update_window_title(self) -> None:
        name = self.controller.automaton.name
        path = f" — {Path(self.current_file_path).name}" if self.current_file_path else ""
        self.setWindowTitle(f"AutomataForge — {name}{path}")
        # Mirror the automaton name into the header subtitle
        if hasattr(self, "header_subtitle"):
            self.header_subtitle.setText(name)

    # ------------------------------------------------------------------
    def _build_header(self) -> QWidget:
        """Branded gradient header shown above the canvas."""
        header = QFrame()
        header.setObjectName("appHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(12)

        logo = QLabel("◆")
        logo.setObjectName("headerLogo")
        layout.addWidget(logo)

        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        title = QLabel("AutomataForge")
        title.setObjectName("headerTitle")
        self.header_subtitle = QLabel("Untitled automaton")
        self.header_subtitle.setObjectName("headerSubtitle")
        text_col.addWidget(title)
        text_col.addWidget(self.header_subtitle)
        layout.addLayout(text_col)
        layout.addStretch(1)

        badge = QLabel("Finite Automata Studio")
        badge.setObjectName("headerBadge")
        layout.addWidget(badge)

        return header

    # ------------------------------------------------------------------
    def _build_actions(self) -> None:
        style = self.style()

        self.act_new = QAction(style.standardIcon(QStyle.StandardPixmap.SP_FileIcon), "New", self)
        self.act_new.setShortcut(QKeySequence.StandardKey.New)
        self.act_new.triggered.connect(self._new_project)

        self.act_open = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "Open...", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self._open_project)

        self.act_save = QAction(style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Save", self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.triggered.connect(self._save_project)

        self.act_save_as = QAction("Save As...", self)
        self.act_save_as.triggered.connect(self._save_project_as)

        self.act_export_png = QAction("Export PNG Image...", self)
        self.act_export_png.triggered.connect(self._export_png)

        self.act_export_pdf = QAction("Export PDF Report...", self)
        self.act_export_pdf.triggered.connect(self._export_pdf)

        self.act_export_mermaid = QAction("Export Mermaid (.mmd)...", self)
        self.act_export_mermaid.triggered.connect(self._export_mermaid)

        self.act_exit = QAction("Exit", self)
        self.act_exit.triggered.connect(self.close)

        self.act_undo = QAction(style.standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Undo", self)
        self.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.act_undo.triggered.connect(self._undo)

        self.act_redo = QAction(style.standardIcon(QStyle.StandardPixmap.SP_ArrowForward), "Redo", self)
        self.act_redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.act_redo.triggered.connect(self._redo)

        self.act_validate = QAction("Validate Automaton", self)
        self.act_validate.triggered.connect(self._validate)

        self.act_auto_layout = QAction("Auto-layout States", self)
        self.act_auto_layout.triggered.connect(self.graph_view.auto_layout)

        self.act_zoom_in = QAction(style.standardIcon(QStyle.StandardPixmap.SP_ArrowUp), "Zoom In", self)
        self.act_zoom_in.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.act_zoom_in.triggered.connect(self.graph_view.zoom_in)

        self.act_zoom_out = QAction(style.standardIcon(QStyle.StandardPixmap.SP_ArrowDown), "Zoom Out", self)
        self.act_zoom_out.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.act_zoom_out.triggered.connect(self.graph_view.zoom_out)

        self.act_zoom_reset = QAction("Reset Zoom", self)
        self.act_zoom_reset.triggered.connect(self.graph_view.zoom_reset)

        self.act_fit_view = QAction("Fit to View", self)
        self.act_fit_view.triggered.connect(self.graph_view.fit_view)

        self.act_dark_mode = QAction("Dark Mode", self, checkable=True)
        self.act_dark_mode.toggled.connect(self._toggle_dark_mode)

        self.act_help = QAction("Help", self)
        self.act_help.triggered.connect(self._show_help)

        self.act_about = QAction("About", self)
        self.act_about.triggered.connect(self._show_about)

    def _build_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self.act_new)
        file_menu.addAction(self.act_open)
        file_menu.addAction(self.act_save)
        file_menu.addAction(self.act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.act_export_png)
        file_menu.addAction(self.act_export_pdf)
        file_menu.addAction(self.act_export_mermaid)
        file_menu.addSeparator()
        file_menu.addAction(self.act_exit)

        edit_menu = menubar.addMenu("&Edit")
        edit_menu.addAction(self.act_undo)
        edit_menu.addAction(self.act_redo)

        automaton_menu = menubar.addMenu("&Automaton")
        automaton_menu.addAction(self.act_validate)
        automaton_menu.addAction(self.act_auto_layout)

        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.act_zoom_in)
        view_menu.addAction(self.act_zoom_out)
        view_menu.addAction(self.act_zoom_reset)
        view_menu.addAction(self.act_fit_view)
        view_menu.addSeparator()
        view_menu.addAction(self.left_dock.toggleViewAction())
        view_menu.addAction(self.right_dock.toggleViewAction())
        view_menu.addAction(self.bottom_dock.toggleViewAction())
        view_menu.addSeparator()
        view_menu.addAction(self.act_dark_mode)

        examples_menu = menubar.addMenu("E&xamples")
        for key in EXAMPLES:
            action = QAction(key, self)
            action.triggered.connect(lambda checked=False, k=key: self._load_example(k))
            examples_menu.addAction(action)

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self.act_help)
        help_menu.addAction(self.act_about)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(toolbar.iconSize())
        self.addToolBar(toolbar)
        for action in (self.act_new, self.act_open, self.act_save):
            toolbar.addAction(action)
        toolbar.addSeparator()
        for action in (self.act_undo, self.act_redo):
            toolbar.addAction(action)
        toolbar.addSeparator()
        for action in (self.act_zoom_in, self.act_zoom_out):
            toolbar.addAction(action)
        toolbar.addSeparator()
        toolbar.addAction(self.act_auto_layout)
        toolbar.addAction(self.act_validate)
        toolbar.addSeparator()
        toolbar.addAction(self.act_dark_mode)

    # ------------------------------------------------------------------
    def _update_undo_redo_actions(self) -> None:
        self.act_undo.setEnabled(self.controller.history.can_undo())
        self.act_redo.setEnabled(self.controller.history.can_redo())

    def _undo(self) -> None:
        self.controller.undo()

    def _redo(self) -> None:
        self.controller.redo()

    # ------------------------------------------------------------------
    def _new_project(self) -> None:
        self.controller.new_automaton()
        self.current_file_path = None
        self.simulation_panel.clear()
        self._update_window_title()

    def _open_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open project", "", "AutomataForge Projects (*.afjson);;All Files (*)")
        if not path:
            return
        try:
            automaton = file_io.load_project(path)
        except Exception as e:
            QMessageBox.critical(self, "Open Error", f"Could not open file:\n{e}")
            return
        self.controller.replace_automaton(automaton)
        self.current_file_path = path
        self.simulation_panel.clear()
        self._update_window_title()
        self.show_status(f"Project loaded from {path}")

    def _save_project(self) -> None:
        if not self.current_file_path:
            self._save_project_as()
            return
        self._write_project(self.current_file_path)

    def _save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save project as", f"{self.controller.automaton.name}.afjson", "AutomataForge Projects (*.afjson)")
        if not path:
            return
        if not path.endswith(".afjson"):
            path += ".afjson"
        self.current_file_path = path
        self._write_project(path)

    def _write_project(self, path: str) -> None:
        try:
            file_io.save_project(path, self.controller.automaton)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save file:\n{e}")
            return
        self._update_window_title()
        self.show_status(f"Project saved to {path}")

    def _export_png(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export PNG Image", f"{self.controller.automaton.name}.png", "PNG Image (*.png)")
        if not path:
            return
        if not path.endswith(".png"):
            path += ".png"
        self.graph_view.clear_highlights()
        file_io.export_scene_png(self.graph_view.scene_, path)
        self.show_status(f"Image exported to {path}")

    def _export_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF Report", f"{self.controller.automaton.name}.pdf", "PDF Document (*.pdf)")
        if not path:
            return
        if not path.endswith(".pdf"):
            path += ".pdf"

        self.graph_view.clear_highlights()
        with tempfile.TemporaryDirectory() as tmp_dir:
            image_path = str(Path(tmp_dir) / "diagram.png")
            file_io.export_scene_png(self.graph_view.scene_, image_path)

            report = self.controller.analyze_properties()
            properties_summary = [
                f"Deterministic: {'Yes' if report.is_deterministic else 'No'}",
                f"Complete: {'Yes' if report.is_complete else 'No'}",
                f"Connected: {'Yes' if report.is_connected else 'No'}",
                f"Unreachable states: {', '.join(sorted(report.unreachable_states)) or 'none'}",
                f"Dead states: {', '.join(sorted(report.dead_states)) or 'none'}",
            ]
            simulation_summary = None
            if self.controller.simulation_log:
                last = self.controller.simulation_log[0]
                simulation_summary = [
                    ("String", last.input_string or "(empty)"),
                    ("Result", "Accepted" if last.accepted else "Rejected"),
                ]
            try:
                file_io.export_pdf(path, self.controller.automaton, image_path, simulation_summary, properties_summary)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not generate PDF:\n{e}")
                return
        self.show_status(f"PDF report exported to {path}")

    def _export_mermaid(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Mermaid diagram",
            f"{self.controller.automaton.name}.mmd",
            "Mermaid diagram (*.mmd *.mermaid);;All Files (*)",
        )
        if not path:
            return
        if not (path.endswith(".mmd") or path.endswith(".mermaid")):
            path += ".mmd"
        try:
            mermaid = file_io.to_mermaid(self.controller.automaton)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(mermaid)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Could not write Mermaid:\n{e}")
            return
        self.show_status(f"Mermaid diagram exported to {path}")

    # ------------------------------------------------------------------
    def _validate(self) -> None:
        errors = self.controller.automaton.validate()
        if errors:
            QMessageBox.warning(self, "Validation", "Problems found:\n\n" + "\n".join(f"• {e}" for e in errors))
        else:
            QMessageBox.information(self, "Validation", "The automaton is valid.")

    def _load_example(self, key: str) -> None:
        data = EXAMPLES[key]
        automaton = Automaton.from_dict(data)
        self.controller.replace_automaton(automaton)
        self.current_file_path = None
        self.simulation_panel.clear()
        self.graph_view.fit_view()
        self._update_window_title()
        self.show_status(f"Loaded example: {key}")

    def _toggle_dark_mode(self, checked: bool) -> None:
        self.dark_mode = checked
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.stylesheet(checked))
        self.graph_view.set_dark_mode(checked)

    def _show_help(self) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Help")
        dialog.setTextFormat(Qt.TextFormat.RichText)
        dialog.setText(HELP_TEXT)
        dialog.exec()

    def _show_about(self) -> None:
        QMessageBox.about(
            self, "About AutomataForge",
            "AutomataForge\n\n"
            "An educational tool for creating, editing, converting, simulating and analysing "
            "Deterministic (DFA) and Non-deterministic (NFA) Finite Automata.\n\n"
            "Built with Python and PyQt6.",
        )
