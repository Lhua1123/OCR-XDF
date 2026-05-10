"""
截图模块：图片导入、剪贴板图片
"""

import io
import os
import uuid
import ctypes
from PIL import Image

from PyQt6.QtGui import QPixmap, QImage, QGuiApplication

from .config import SCREENSHOTS_DIR


def import_image(filepath):
    """从本地导入图片，返回 (QPixmap, PIL Image)"""
    img = Image.open(filepath).convert("RGB")
    return _pil_to_qpixmap(img), img


def paste_from_clipboard():
    """从剪贴板获取图片，返回 (QPixmap, PIL Image) 或 (None, None)"""
    # 方式1: 使用 PyQt 的 clipboard image
    app = QGuiApplication.instance()
    if app:
        clipboard = app.clipboard()
        qimage = clipboard.image()
        if qimage and not qimage.isNull():
            qpixmap = QPixmap.fromImage(qimage)
            pil_img = _qimage_to_pil(qimage)
            if pil_img:
                return qpixmap, pil_img

    return None, None


def _qimage_to_pil(qimage):
    """QImage 转 PIL Image"""
    from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
    buffer = QByteArray()
    qbuffer = QBuffer(buffer)
    qbuffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap = QPixmap.fromImage(qimage)
    pixmap.save(qbuffer, "PNG")
    qbuffer.close()
    return Image.open(io.BytesIO(buffer.data())).convert("RGB")


def _pil_to_qpixmap(pil_image):
    """PIL Image 转 QPixmap"""
    pil_rgba = pil_image.convert("RGBA")
    raw = pil_rgba.tobytes("raw", "RGBA")
    qimage = QImage(raw, pil_rgba.width, pil_rgba.height, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimage)


def save_screenshot(pil_image):
    """保存图片到 screenshots 目录，返回保存路径"""
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    filename = f"screenshot_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    pil_image.save(filepath, "PNG")
    return filepath
