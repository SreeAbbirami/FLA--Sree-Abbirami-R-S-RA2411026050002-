"""Light and dark Qt stylesheets for AutomataForge.

Design language: "Aurora Glass"
  - Coral (#fb7185) → violet (#a78bfa) gradient accent everywhere
  - Frosted-glass panels with soft borders and rounded corners
  - Fully pill-shaped (999px radius) buttons with gradient fills
  - Gradient canvas background with a faint dot overlay
  - Branded gradient header strip above the canvas
  - Amber (#f59e0b) reserved for simulation highlighting
"""

LIGHT_QSS = """
QWidget {
    background-color: #f8fafc;
    color: #1e293b;
    font-family: "Segoe UI", "Inter", "Noto Sans", sans-serif;
    font-size: 13px;
}
QMainWindow { background-color: #f1f5f9; }

/* ---------- Central area + branded header ---------- */
#centralWidget { background-color: #f1f5f9; }
#appHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #fb7185, stop:0.5 #c084fc, stop:1 #818cf8);
    border-bottom: 1px solid #e2e8f0;
}
#headerLogo {
    color: white;
    font-size: 22px;
    font-weight: bold;
}
#headerTitle {
    color: white;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
#headerSubtitle {
    color: rgba(255,255,255,0.85);
    font-size: 11px;
}
#headerBadge {
    color: white;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 600;
}

/* ---------- Menu bar ---------- */
QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 2px 8px;
}
QMenuBar::item { padding: 6px 14px; border-radius: 8px; background: transparent; }
QMenuBar::item:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fce7f3, stop:1 #ede9fe);
    color: #be185d;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 6px;
}
QMenu::item { padding: 7px 18px; border-radius: 6px; }
QMenu::item:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fce7f3, stop:1 #ede9fe);
    color: #be185d;
}
QMenu::separator { height: 1px; background: #f1f5f9; margin: 4px 8px; }

/* ---------- Toolbar ---------- */
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    spacing: 8px;
    padding: 10px 14px;
}
QToolBar QToolButton {
    background-color: #f8fafc;
    color: #475569;
    padding: 7px 16px;
    border-radius: 999px;
    border: 1px solid #e2e8f0;
    font-weight: 600;
}
QToolBar QToolButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fce7f3, stop:1 #ede9fe);
    color: #be185d;
    border-color: #f9a8d4;
}
QToolBar QToolButton:checked {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fb7185, stop:1 #a78bfa);
    color: white;
    border: none;
}
QToolBar::separator { width: 1px; background: #e2e8f0; margin: 6px 4px; }

/* ---------- Dock widgets (glass panels) ---------- */
QDockWidget { font-weight: 600; color: #1e293b; }
QDockWidget::title {
    background-color: #ffffff;
    padding: 12px 16px;
    border: 1px solid #e2e8f0;
    border-bottom: none;
    border-radius: 12px 12px 0 0;
    color: #7c3aed;
    letter-spacing: 0.4px;
    font-size: 12px;
    text-transform: uppercase;
}
QDockWidget QWidget { background-color: #ffffff; }
QDockWidget::close-button, QDockWidget::float-button {
    background: #f1f5f9; border-radius: 6px; padding: 2px;
}
QDockWidget::close-button:hover, QDockWidget::float-button:hover { background: #e2e8f0; }

/* ---------- Canvas (gradient) ---------- */
QGraphicsView {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #fdf2f8, stop:0.5 #f5f3ff, stop:1 #eff6ff);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}

/* ---------- Tables & lists ---------- */
QTableWidget, QListWidget, QTreeWidget {
    background-color: #fafafa;
    border: 1px solid #f1f5f9;
    border-radius: 10px;
    gridline-color: #f1f5f9;
    outline: none;
    padding: 4px;
}
QTableWidget::item { padding: 8px; border-bottom: 1px solid #f8fafc; }
QTableWidget::item:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fce7f3, stop:1 #ede9fe);
    color: #be185d;
}
QListWidget::item { padding: 7px; border-radius: 6px; }
QListWidget::item:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fce7f3, stop:1 #ede9fe);
    color: #be185d;
}
QHeaderView::section {
    background-color: #fafafa;
    color: #64748b;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-weight: 700;
    font-size: 12px;
}

/* ---------- Buttons ---------- */
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fb7185, stop:1 #a78bfa);
    color: white;
    border: none;
    border-radius: 999px;
    padding: 9px 20px;
    font-weight: 700;
    font-size: 13px;
}
QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #f43f5e, stop:1 #8b5cf6);
}
QPushButton:pressed {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #e11d48, stop:1 #7c3aed);
}
QPushButton:disabled { background: #cbd5e1; color: #94a3b8; }
QPushButton#secondary {
    background-color: #ffffff;
    color: #475569;
    border: 1px solid #e2e8f0;
}
QPushButton#secondary:hover {
    background-color: #fafafa;
    border-color: #c084fc;
    color: #7c3aed;
}
QPushButton#secondary:disabled { background: #f8fafc; color: #cbd5e1; }

/* ---------- Inputs ---------- */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #fafafa;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 7px 12px;
    selection-background-color: #f9a8d4;
    selection-color: #831843;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #a78bfa;
    background-color: #ffffff;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    selection-background-color: #fce7f3;
    selection-color: #be185d;
}

QCheckBox { spacing: 10px; padding: 4px; color: #475569; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 5px;
    border: 1px solid #cbd5e1; background: #ffffff;
}
QCheckBox::indicator:checked {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fb7185, stop:1 #a78bfa);
    border-color: #a78bfa;
}

/* ---------- Tabs ---------- */
QTabWidget::pane {
    border: 1px solid #f1f5f9;
    border-radius: 12px;
    background: #fafafa;
    top: -1px;
    padding: 10px;
}
QTabBar::tab {
    background: #f1f5f9;
    color: #64748b;
    padding: 9px 20px;
    margin-right: 6px;
    border-radius: 999px;
    border: 1px solid #e2e8f0;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fb7185, stop:1 #a78bfa);
    color: white;
    border: none;
}
QTabBar::tab:hover:!selected { background: #e2e8f0; color: #334155; }

/* ---------- Text edit ---------- */
QTextEdit {
    background-color: #fafafa;
    border: 1px solid #f1f5f9;
    border-radius: 10px;
    padding: 10px;
    selection-background-color: #f9a8d4;
    selection-color: #831843;
}

/* ---------- Status bar ---------- */
QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #e2e8f0;
    color: #64748b;
    padding: 2px 8px;
}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 4px; }
QScrollBar::handle:vertical {
    background: #cbd5e1; border-radius: 5px; min-height: 32px;
}
QScrollBar::handle:vertical:hover { background: #94a3b8; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 4px; }
QScrollBar::handle:horizontal {
    background: #cbd5e1; border-radius: 5px; min-width: 32px;
}
QScrollBar::handle:horizontal:hover { background: #94a3b8; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""

DARK_QSS = """
QWidget {
    background-color: #0f172a;
    color: #e2e8f0;
    font-family: "Segoe UI", "Inter", "Noto Sans", sans-serif;
    font-size: 13px;
}
QMainWindow { background-color: #0b1220; }

/* ---------- Central area + branded header ---------- */
#centralWidget { background-color: #0b1220; }
#appHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #be185d, stop:0.5 #7c3aed, stop:1 #4f46e5);
    border-bottom: 1px solid #1e293b;
}
#headerLogo { color: white; font-size: 22px; font-weight: bold; }
#headerTitle {
    color: white;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
#headerSubtitle { color: rgba(255,255,255,0.85); font-size: 11px; }
#headerBadge {
    color: white;
    background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 11px;
    font-weight: 600;
}

/* ---------- Menu bar ---------- */
QMenuBar {
    background-color: #1e293b;
    border-bottom: 1px solid #334155;
    padding: 2px 8px;
}
QMenuBar::item { padding: 6px 14px; border-radius: 8px; background: transparent; }
QMenuBar::item:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #831843, stop:1 #5b21b6);
    color: #f9a8d4;
}
QMenu {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 6px;
}
QMenu::item { padding: 7px 18px; border-radius: 6px; }
QMenu::item:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #831843, stop:1 #5b21b6);
    color: #f9a8d4;
}
QMenu::separator { height: 1px; background: #334155; margin: 4px 8px; }

/* ---------- Toolbar ---------- */
QToolBar {
    background-color: #1e293b;
    border-bottom: 1px solid #334155;
    spacing: 8px;
    padding: 10px 14px;
}
QToolBar QToolButton {
    background-color: #334155;
    color: #cbd5e1;
    padding: 7px 16px;
    border-radius: 999px;
    border: 1px solid #475569;
    font-weight: 600;
}
QToolBar QToolButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #831843, stop:1 #5b21b6);
    color: #f9a8d4;
    border-color: #be185d;
}
QToolBar QToolButton:checked {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fb7185, stop:1 #a78bfa);
    color: white;
    border: none;
}
QToolBar::separator { width: 1px; background: #334155; margin: 6px 4px; }

/* ---------- Dock widgets ---------- */
QDockWidget { font-weight: 600; color: #e2e8f0; }
QDockWidget::title {
    background-color: #1e293b;
    padding: 12px 16px;
    border: 1px solid #334155;
    border-bottom: none;
    border-radius: 12px 12px 0 0;
    color: #c4b5fd;
    letter-spacing: 0.4px;
    font-size: 12px;
}
QDockWidget QWidget { background-color: #1e293b; }
QDockWidget::close-button, QDockWidget::float-button {
    background: #334155; border-radius: 6px; padding: 2px;
}
QDockWidget::close-button:hover, QDockWidget::float-button:hover { background: #475569; }

/* ---------- Canvas ---------- */
QGraphicsView {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #1e1b4b, stop:0.5 #312e81, stop:1 #1e293b);
    border: 1px solid #334155;
    border-radius: 12px;
}

/* ---------- Tables & lists ---------- */
QTableWidget, QListWidget, QTreeWidget {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    gridline-color: #334155;
    outline: none;
    padding: 4px;
}
QTableWidget::item { padding: 8px; border-bottom: 1px solid #1e293b; }
QTableWidget::item:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #831843, stop:1 #5b21b6);
    color: #f9a8d4;
}
QListWidget::item { padding: 7px; border-radius: 6px; }
QListWidget::item:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #831843, stop:1 #5b21b6);
    color: #f9a8d4;
}
QHeaderView::section {
    background-color: #334155;
    color: #cbd5e1;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #475569;
    font-weight: 700;
    font-size: 12px;
}

/* ---------- Buttons ---------- */
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fb7185, stop:1 #a78bfa);
    color: white;
    border: none;
    border-radius: 999px;
    padding: 9px 20px;
    font-weight: 700;
    font-size: 13px;
}
QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #f43f5e, stop:1 #8b5cf6);
}
QPushButton:pressed {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #e11d48, stop:1 #7c3aed);
}
QPushButton:disabled { background: #334155; color: #64748b; }
QPushButton#secondary {
    background-color: #1e293b;
    color: #cbd5e1;
    border: 1px solid #475569;
}
QPushButton#secondary:hover {
    background-color: #334155;
    border-color: #a78bfa;
    color: #c4b5fd;
}
QPushButton#secondary:disabled { background: #1e293b; color: #475569; }

/* ---------- Inputs ---------- */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 10px;
    padding: 7px 12px;
    color: #e2e8f0;
    selection-background-color: #be185d;
    selection-color: white;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #a78bfa;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #475569;
    border-radius: 10px;
    selection-background-color: #831843;
    selection-color: #f9a8d4;
}

QCheckBox { spacing: 10px; padding: 4px; color: #cbd5e1; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 5px;
    border: 1px solid #475569; background: #1e293b;
}
QCheckBox::indicator:checked {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fb7185, stop:1 #a78bfa);
    border-color: #a78bfa;
}

/* ---------- Tabs ---------- */
QTabWidget::pane {
    border: 1px solid #334155;
    border-radius: 12px;
    background: #1e293b;
    top: -1px;
    padding: 10px;
}
QTabBar::tab {
    background: #334155;
    color: #94a3b8;
    padding: 9px 20px;
    margin-right: 6px;
    border-radius: 999px;
    border: 1px solid #475569;
    font-weight: 600;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #fb7185, stop:1 #a78bfa);
    color: white;
    border: none;
}
QTabBar::tab:hover:!selected { background: #475569; color: #e2e8f0; }

/* ---------- Text edit ---------- */
QTextEdit {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 10px;
    color: #e2e8f0;
    selection-background-color: #be185d;
    selection-color: white;
}

/* ---------- Status bar ---------- */
QStatusBar {
    background-color: #1e293b;
    border-top: 1px solid #334155;
    color: #94a3b8;
    padding: 2px 8px;
}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 4px; }
QScrollBar::handle:vertical { background: #475569; border-radius: 5px; min-height: 32px; }
QScrollBar::handle:vertical:hover { background: #64748b; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 4px; }
QScrollBar::handle:horizontal { background: #475569; border-radius: 5px; min-width: 32px; }
QScrollBar::handle:horizontal:hover { background: #64748b; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""


def stylesheet(dark: bool) -> str:
    return DARK_QSS if dark else LIGHT_QSS
