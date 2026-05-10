from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
import json
import csv

from ..modules.history import HistoryManager


class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = HistoryManager()
        self.setWindowTitle("历史记录")
        self.setMinimumSize(800, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["时间", "通知文本"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self._show_detail)

        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新")
        export_json_btn = QPushButton("导出 JSON")
        export_csv_btn = QPushButton("导出 CSV")
        clear_btn = QPushButton("清空")
        close_btn = QPushButton("关闭")

        refresh_btn.clicked.connect(self._load_data)
        export_json_btn.clicked.connect(lambda: self._export("json"))
        export_csv_btn.clicked.connect(lambda: self._export("csv"))
        clear_btn.clicked.connect(self._clear)
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(export_json_btn)
        btn_layout.addWidget(export_csv_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self._load_data()

    def _load_data(self):
        records = self.manager.get_all()
        self.table.setRowCount(len(records))
        for i, rec in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(rec.get("timestamp", "")))
            text = rec.get("notification_text", "")
            self.table.setItem(i, 1, QTableWidgetItem(text[:50] + "…" if len(text) > 50 else text))

    def _show_detail(self, row, col):
        records = self.manager.get_all()
        if 0 <= row < len(records):
            rec = records[row]
            detail = (
                f"截图路径：{rec.get('screenshot_path', 'N/A')}\n\n"
                f"--- 通知文本 ---\n{rec.get('notification_text', '')}"
            )
            QMessageBox.information(self, f"详情 - {rec.get('timestamp', '')}", detail)

    def _export(self, fmt):
        records = self.manager.get_all()
        if not records:
            QMessageBox.information(self, "提示", "没有历史记录可导出")
            return

        default_name = f"history.{fmt}"
        filepath, _ = QFileDialog.getSaveFileName(self, "导出历史记录", default_name, f"{'JSON' if fmt == 'json' else 'CSV'} 文件 (*.{fmt})")
        if not filepath:
            return

        if fmt == "json":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
        else:
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["时间", "通知文本"])
                for rec in records:
                    writer.writerow([rec.get("timestamp", ""), rec.get("notification_text", "")])

        QMessageBox.information(self, "导出成功", f"已导出到 {filepath}")

    def _clear(self):
        r = QMessageBox.question(self, "确认清空", "确定要清空所有历史记录吗？",
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if r == QMessageBox.StandardButton.Yes:
            self.manager.clear()
            self._load_data()