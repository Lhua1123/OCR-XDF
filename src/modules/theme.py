"""
主题管理模块
"""

DARK_STYLESHEET = """
    QMainWindow, QDialog {
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        font-size: 13px;
    }
    QMainWindow, QWidget {
        background-color: #2b2b2b;
        color: #e0e0e0;
    }
    QPushButton {
        padding: 6px 16px;
        border-radius: 4px;
        border: 1px solid #555;
        background: #3c3c3c;
        color: #e0e0e0;
    }
    QPushButton:hover {
        background: #505050;
        border-color: #777;
    }
    QPushButton:pressed {
        background: #606060;
    }
    QPushButton:disabled {
        color: #666;
        background: #333;
    }
    QLineEdit, QTextEdit {
        border: 1px solid #555;
        border-radius: 4px;
        padding: 4px;
        background: #1e1e1e;
        color: #e0e0e0;
    }
    QLineEdit:focus, QTextEdit:focus {
        border-color: #4a9eff;
    }
    QComboBox {
        padding: 4px 8px;
        border: 1px solid #555;
        border-radius: 4px;
        background: #3c3c3c;
        color: #e0e0e0;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox QAbstractItemView {
        background: #3c3c3c;
        color: #e0e0e0;
        selection-background-color: #4a9eff;
    }
    QStatusBar {
        background: #333;
        border-top: 1px solid #555;
        color: #aaa;
    }
    QProgressBar {
        border: none;
        background: #444;
        text-align: center;
    }
    QProgressBar::chunk {
        background: #4a9eff;
    }
    QTableWidget {
        border: 1px solid #555;
        gridline-color: #444;
        background: #1e1e1e;
        color: #e0e0e0;
    }
    QHeaderView::section {
        background: #333;
        border: 1px solid #555;
        padding: 4px;
        color: #e0e0e0;
    }
    QTabWidget::pane {
        border: 1px solid #555;
        background: #2b2b2b;
    }
    QTabBar::tab {
        background: #3c3c3c;
        color: #aaa;
        padding: 6px 12px;
        border: 1px solid #555;
    }
    QTabBar::tab:selected {
        background: #2b2b2b;
        color: #e0e0e0;
        border-bottom-color: #2b2b2b;
    }
    QGroupBox {
        border: 1px solid #555;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 16px;
        color: #e0e0e0;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
    }
    QMenuBar {
        background: #333;
        color: #e0e0e0;
    }
    QMenuBar::item:selected {
        background: #505050;
    }
    QMenu {
        background: #3c3c3c;
        color: #e0e0e0;
        border: 1px solid #555;
    }
    QMenu::item:selected {
        background: #4a9eff;
    }
    QSplitter::handle {
        background: #555;
    }
"""

LIGHT_STYLESHEET = """
    QMainWindow, QDialog {
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        font-size: 13px;
    }
    QPushButton {
        padding: 6px 16px;
        border-radius: 4px;
        border: 1px solid #ccc;
        background: #f8f8f8;
    }
    QPushButton:hover {
        background: #e8e8e8;
        border-color: #aaa;
    }
    QPushButton:pressed {
        background: #d8d8d8;
    }
    QPushButton:disabled {
        color: #aaa;
        background: #f0f0f0;
    }
    QLineEdit, QTextEdit {
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 4px;
    }
    QLineEdit:focus, QTextEdit:focus {
        border-color: #4a9eff;
    }
    QComboBox {
        padding: 4px 8px;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
    QStatusBar {
        background: #f0f0f0;
        border-top: 1px solid #ddd;
    }
    QProgressBar {
        border: none;
        background: #e0e0e0;
        text-align: center;
    }
    QProgressBar::chunk {
        background: #4a9eff;
    }
    QTableWidget {
        border: 1px solid #ddd;
        gridline-color: #eee;
    }
    QHeaderView::section {
        background: #f5f5f5;
        border: 1px solid #ddd;
        padding: 4px;
    }
    QGroupBox {
        border: 1px solid #ddd;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 16px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
    }
"""


def update_theme(app, config):
    theme = config.get("theme", "light")
    if theme == "dark":
        app.setStyleSheet(DARK_STYLESHEET)
    else:
        app.setStyleSheet(LIGHT_STYLESHEET)