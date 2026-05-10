import os
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QTextEdit,
                               QSplitter, QFrame, QProgressBar,
                               QFileDialog, QMessageBox, QStatusBar, QMenuBar,
                               QMenu, QSizePolicy, QApplication, QScrollArea,
                               QGridLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QEvent
from PyQt6.QtGui import QAction, QPixmap

from .modules.config import load_config, save_config
from .modules.screenshot import paste_from_clipboard
from .modules.extractor import extract_with_vlm, extract_with_vlm_multi
from .modules.history import HistoryManager
from .modules.theme import update_theme
from .ui.settings_dialog import SettingsDialog
from .ui.history_dialog import HistoryDialog

from loguru import logger


class VlmWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, pil_images, config):
        super().__init__()
        self.pil_images = pil_images
        self.config = config

    def run(self):
        try:
            if len(self.pil_images) > 1:
                result = extract_with_vlm_multi(self.pil_images, self.config)
            else:
                result = extract_with_vlm(self.pil_images[0], self.config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.images = []
        self.pixmap_list = []
        self.current_screenshot_path = ""
        self.history_manager = HistoryManager()

        self._setup_ui()
        self._connect_signals()
        self._setup_autosave()
        logger.info("主窗口初始化完成")

    def _setup_ui(self):
        self.setWindowTitle("课程信息提取工具")
        self.setMinimumSize(1100, 750)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        toolbar = QHBoxLayout()
        self.btn_paste = QPushButton("粘贴图片 (Ctrl+V)")
        self.btn_paste.setToolTip("从剪贴板粘贴图片，最多支持5张")
        self.btn_clear = QPushButton("清空")
        self.btn_clear.setToolTip("清空所有已粘贴的图片")
        self.image_count_label = QLabel("图片：0/5")
        self.image_count_label.setStyleSheet("color: #666; font-size: 13px; padding: 4px;")
        toolbar.addWidget(self.btn_paste)
        toolbar.addWidget(self.btn_clear)
        toolbar.addWidget(self.image_count_label, 1)
        left_layout.addLayout(toolbar)

        # 图片预览区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(300)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: 2px dashed #aaa;
                border-radius: 8px;
                background: #f5f5f5;
            }
        """)
        self.scroll_content = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder = QLabel("按 Ctrl+V 粘贴图片\n（最多5张图片）")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #888; font-size: 14px;")
        self.scroll_layout.addWidget(placeholder, 0, 0)
        self.scroll_area.setWidget(self.scroll_content)
        left_layout.addWidget(self.scroll_area, 1)

        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.step_label = QLabel("粘贴图片 → 点击「开始识别」→ AI 自动提取并生成通知")
        self.step_label.setStyleSheet("color: #666; font-size: 12px; padding: 4px; background: #eef; border-radius: 4px;")
        self.step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.step_label)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setMaximumHeight(6)
        right_layout.addWidget(self.progress)

        btn_bar = QHBoxLayout()
        self.btn_process = QPushButton("开始识别")
        btn_bar.addWidget(self.btn_process)
        btn_bar.addStretch()
        right_layout.addLayout(btn_bar)

        self.notif_edit = QTextEdit()
        self.notif_edit.setPlaceholderText("AI 生成的通知文本将显示在这里…")
        self.notif_edit.setMaximumHeight(250)
        right_layout.addWidget(self.notif_edit)

        action_bar = QHBoxLayout()
        self.btn_copy = QPushButton("复制到剪贴板")
        self.btn_save = QPushButton("保存到文件")
        action_bar.addWidget(self.btn_copy)
        action_bar.addWidget(self.btn_save)
        action_bar.addStretch()
        right_layout.addLayout(action_bar)

        preview_frame = QFrame()
        preview_frame.setStyleSheet("QFrame { border: 1px solid #ddd; border-radius: 4px; padding: 6px; }")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setSpacing(2)
        preview_layout.addWidget(QLabel("提取信息"))
        self.preview_info = QLabel("等待识别…")
        self.preview_info.setStyleSheet("color: #666; font-size: 12px;")
        self.preview_info.setWordWrap(True)
        preview_layout.addWidget(self.preview_info)
        right_layout.addWidget(preview_frame)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

        # 菜单
        menubar = self.menuBar()
        tool_menu = menubar.addMenu("工具")
        settings_act = QAction("设置", self)
        settings_act.triggered.connect(self._on_settings)
        tool_menu.addAction(settings_act)
        history_act = QAction("历史记录", self)
        history_act.triggered.connect(self._on_history)
        tool_menu.addAction(history_act)

        help_menu = menubar.addMenu("帮助")
        about_act = QAction("关于", self)
        about_act.triggered.connect(lambda: QMessageBox.about(self, "关于", "课程信息提取工具 v3.0\n截图 → AI 视觉识别 → 通知生成"))
        help_menu.addAction(about_act)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 按 Ctrl+V 从剪贴板粘贴图片")

    def _connect_signals(self):
        self.btn_paste.clicked.connect(self._on_paste)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_process.clicked.connect(self._on_process)
        self.btn_copy.clicked.connect(self._on_copy)
        self.btn_save.clicked.connect(self._on_save)

    def _setup_autosave(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self._autosave)
        self.autosave_timer.start(60000)

    def _autosave(self):
        notif = self.notif_edit.toPlainText().strip()
        if notif:
            record = {
                "screenshot_path": self.current_screenshot_path,
                "notification_text": notif,
            }
            self.history_manager.add_record(record)

    def eventFilter(self, obj, event):
        """拦截所有控件的 Ctrl+V，改为粘贴图片到左侧"""
        if event.type() == QEvent.Type.KeyPress:
            if hasattr(event, 'key'):
                key = event.key()
                mods = event.modifiers()
                is_ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier) or bool(mods & Qt.KeyboardModifier.MetaModifier)
                if is_ctrl and key == Qt.Key.Key_V:
                    self._on_paste()
                    return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """窗口级别的按键事件也拦截 Ctrl+V"""
        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._on_paste()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _on_paste(self):
        if len(self.images) >= 5:
            self.status_bar.showMessage("已达最大图片数量（5张）")
            return

        qpixmap, pil_img = paste_from_clipboard()
        if not qpixmap or not pil_img:
            self.status_bar.showMessage("剪贴板中没有图片，请先复制一张图片")
            return

        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        self.images.append(pil_img)
        self.pixmap_list.append(qpixmap)
        self._refresh_preview()
        img_count = len(self.images)
        if img_count == 1:
            self.step_label.setText("已粘贴图片 → 点击「开始识别」")
        self.status_bar.showMessage(f"已粘贴第 {img_count} 张图片（Ctrl+V 可继续粘贴，最多5张）")
        self.notif_edit.clear()
        self.preview_info.setText("等待识别…")

    def _on_clear(self):
        self.images.clear()
        self.pixmap_list.clear()
        self.current_screenshot_path = ""
        self._refresh_preview()
        self.notif_edit.clear()
        self.preview_info.setText("等待识别…")
        self.step_label.setText("粘贴图片 → 点击「开始识别」→ AI 自动提取并生成通知")
        self.status_bar.showMessage("已清空所有图片")

    def _refresh_preview(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.images:
            label = QLabel("按 Ctrl+V 粘贴图片\n（最多5张图片）")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #888; font-size: 14px;")
            self.scroll_layout.addWidget(label, 0, 0)
            self.image_count_label.setText("图片：0/5")
        else:
            max_display = 5
            for i in range(min(len(self.pixmap_list), max_display)):
                thumbnail = self.pixmap_list[i].scaled(
                    200, 150,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                thumb_lbl = QLabel()
                thumb_lbl.setPixmap(thumbnail)
                thumb_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumb_lbl.setStyleSheet("border: 2px solid #ccc; border-radius: 6px; background: #fff;")
                col = i % 2
                row = i // 2
                self.scroll_layout.addWidget(thumb_lbl, row, col)

            if len(self.pixmap_list) > max_display:
                more_label = QLabel(f"还有 {len(self.pixmap_list) - max_display} 张未显示")
                more_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                more_label.setStyleSheet("color: #888;")
                self.scroll_layout.addWidget(more_label, max_display // 2 + 1, 0, 1, 2)

            self.image_count_label.setText(f"图片：{len(self.images)}/5")

    def _on_process(self):
        if not self.images:
            QMessageBox.warning(self, "提示", "请先粘贴图片（Ctrl+V）")
            return

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.btn_process.setEnabled(False)
        self.status_bar.showMessage(f"正在识别 {len(self.images)} 张图片，请稍候…")
        self.notif_edit.clear()
        self.preview_info.setText("识别中…")
        logger.info(f"开始 AI 视觉识别（共 {len(self.images)} 张图片）")

        self.vlm_worker = VlmWorker(self.images[:], self.config)
        self.vlm_worker.finished.connect(self._on_vlm_finished)
        self.vlm_worker.error.connect(self._on_vlm_error)
        self.vlm_worker.start()

    def _on_vlm_finished(self, notification_text):
        self.progress.setVisible(False)
        self.btn_process.setEnabled(True)
        self.notif_edit.setText(notification_text)

        preview_lines = []
        for label in ["日期", "科目", "时间", "位置", "备注"]:
            for line in notification_text.split("\n"):
                if label in line:
                    preview_lines.append(line.strip())
                    break
        if preview_lines:
            self.preview_info.setText("\n".join(preview_lines))
        else:
            self.preview_info.setText(notification_text[:100] + "…")

        self.status_bar.showMessage("识别完成")
        self.step_label.setText("全部完成！可复制或保存通知文本")
        logger.info(f"AI 识别完成: {notification_text[:100]}")
        self._save_to_history()

    def _on_vlm_error(self, err):
        self.progress.setVisible(False)
        self.btn_process.setEnabled(True)
        logger.error(f"AI 识别失败: {err}")
        QMessageBox.critical(self, "识别错误", f"识别失败：{err}")
        self.status_bar.showMessage("识别失败")
        self.preview_info.setText("识别失败")

    def _on_copy(self):
        text = self.notif_edit.toPlainText()
        if text.strip():
            QApplication.clipboard().setText(text)
            self.status_bar.showMessage("已复制到剪贴板")
        else:
            QMessageBox.warning(self, "提示", "没有可复制的内容")

    def _on_save(self):
        text = self.notif_edit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "提示", "没有可保存的内容")
            return
        filepath, _ = QFileDialog.getSaveFileName(self, "保存通知文本", "课程通知.txt", "文本文件 (*.txt)")
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            self.status_bar.showMessage(f"已保存到 {os.path.basename(filepath)}")

    def _on_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            save_config(self.config)
            app = QApplication.instance()
            update_theme(app, self.config)
            self.status_bar.showMessage("设置已保存")

    def _on_history(self):
        dialog = HistoryDialog(self)
        dialog.exec()

    def _save_to_history(self):
        if not self.config.get("save_history", True):
            return
        record = {
            "screenshot_path": self.current_screenshot_path,
            "notification_text": self.notif_edit.toPlainText(),
        }
        self.history_manager.add_record(record)
