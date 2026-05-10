import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
logger.remove()
logger.add(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.log"),
    rotation="10 MB",
    retention=3,
    level="DEBUG",
    encoding="utf-8",
    format="{time:HH:mm:ss} | {level:<5} | {name}:{line} | {message}",
)
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<5} | {message}")

import traceback

def global_excepthook(exc_type, exc_value, exc_traceback):
    logger.critical("未捕获异常: %s", "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

sys.excepthook = global_excepthook

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.modules.config import ensure_dirs, load_config
from src.modules.theme import update_theme
from src.main_window import MainWindow


def main():
    ensure_dirs()

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("课程信息提取工具")
    app.setApplicationDisplayName("课程信息提取工具")

    config = load_config()
    update_theme(app, config)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        logger.critical("程序崩溃: %s", traceback.format_exc())
        raise