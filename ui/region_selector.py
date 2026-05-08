"""
区域截图窗口：全屏半透明 + 鼠标拖拽选择区域
"""

from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush

from ..modules.screenshot import region_capture


class RegionSelector(QWidget):
    region_selected = pyqtSignal(object, object)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.showFullScreen()

        self._start = QPoint()
        self._end = QPoint()
        self._selecting = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(0, 0, 0), 0))
        painter.setBrush(QBrush(QColor(0, 0, 0, 120)))
        painter.drawRect(self.rect())

        if self._selecting:
            rect = QRect(self._start, self._end).normalized()
            painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
            painter.setPen(QPen(QColor(0, 120, 255), 2))
            painter.drawRect(rect)

            painter.setPen(QColor(255, 255, 255))
            painter.drawText(rect.topLeft() + QPoint(5, -5),
                             f"{rect.width()}x{rect.height()}")

    def mousePressEvent(self, event):
        self._start = event.pos()
        self._end = event.pos()
        self._selecting = True
        self.update()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self._selecting = False
        rect = QRect(self._start, self._end).normalized()
        if rect.width() > 10 and rect.height() > 10:
            from PyQt6.QtGui import QGuiApplication
            screen = QGuiApplication.primaryScreen()
            pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
            from PIL import Image
            import io
            from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
            data = QByteArray()
            buf = QBuffer(data)
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buf, "PNG")
            from PIL import Image as PILImage
            import io as io2
            pil_img = PILImage.open(io2.BytesIO(data.data())).convert("RGB")
            self.region_selected.emit(pixmap, pil_img)
        else:
            self.region_selected.emit(None, None)
        self.close()