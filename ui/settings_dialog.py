import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QTabWidget,
                                QWidget, QFormLayout, QDoubleSpinBox, QGroupBox,
                                QFileDialog, QTextEdit, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ..modules.config import DEFAULT_LLM_PROMPT, DEFAULT_NOTIFICATION_TEMPLATES, PROMPT_FILE
from ..modules.extractor import test_api_connectivity


class ApiTestWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        ok, msg = test_api_connectivity(self.config)
        self.finished.emit(ok, msg)


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("设置")
        self.setMinimumWidth(650)
        self.setMinimumHeight(600)
        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # AI 设置
        ai_tab = QWidget()
        form = QFormLayout(ai_tab)

        ai_group = QGroupBox("AI 接口设置")
        ai_layout = QFormLayout(ai_group)
        self.llm_api_key = QLineEdit()
        self.llm_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        ai_layout.addRow("API Key：", self.llm_api_key)
        self.llm_api_base = QLineEdit()
        ai_layout.addRow("API Base：", self.llm_api_base)
        self.llm_model = QLineEdit()
        ai_layout.addRow("模型：", self.llm_model)
        self.llm_temp = QDoubleSpinBox()
        self.llm_temp.setRange(0, 2)
        self.llm_temp.setSingleStep(0.1)
        self.llm_temp.setValue(0.1)
        ai_layout.addRow("Temperature：", self.llm_temp)
        self.api_test_btn = QPushButton("测试连接")
        self.api_test_result = QLabel("")
        self.api_test_result.setStyleSheet("font-size: 11px;")
        self.api_test_btn.clicked.connect(self._test_api)
        test_row = QHBoxLayout()
        test_row.addWidget(self.api_test_btn)
        test_row.addWidget(self.api_test_result, 1)
        ai_layout.addRow("", test_row)
        form.addRow(ai_group)

        prompt_group = QGroupBox("提示词（发送给 AI 的指令）")
        prompt_layout = QVBoxLayout(prompt_group)
        prompt_tip = QLabel(f"提示词来自项目根目录的「提示词.md」文件，请在外部编辑该文件后重新加载。")
        prompt_tip.setStyleSheet("color: #888; font-size: 11px;")
        prompt_tip.setWordWrap(True)
        prompt_layout.addWidget(prompt_tip)
        self.llm_prompt = QTextEdit()
        self.llm_prompt.setMinimumHeight(180)
        self.llm_prompt.setReadOnly(True)
        prompt_layout.addWidget(self.llm_prompt)
        prompt_btn_row = QHBoxLayout()
        prompt_btn_row.addStretch()
        reload_prompt_btn = QPushButton("重新加载")
        reload_prompt_btn.clicked.connect(self._reload_prompt)
        prompt_btn_row.addWidget(reload_prompt_btn)
        prompt_layout.addLayout(prompt_btn_row)
        form.addRow(prompt_group)

        tabs.addTab(ai_tab, "AI 设置")

        # 通知模板设置
        template_tab = QWidget()
        template_layout = QVBoxLayout(template_tab)
        tip = QLabel(
            "在模板中用「date」「course_name」「start_time」「end_time」"
            "「period」「location」「notes」作为占位符，程序会自动替换为实际内容。\n"
            "设置好保存后，每次识别都会按此模板生成通知。"
        )
        tip.setStyleSheet("color: #888; font-size: 11px;")
        tip.setWordWrap(True)
        template_layout.addWidget(tip)

        self.template_edit = QTextEdit()
        self.template_edit.setMinimumHeight(200)
        template_layout.addWidget(self.template_edit, 1)

        tabs.addTab(template_tab, "通知模板")

        # 界面设置
        ui_tab = QWidget()
        form3 = QFormLayout(ui_tab)
        self.theme = QComboBox()
        self.theme.addItems(["light", "dark"])
        form3.addRow("主题：", self.theme)

        tabs.addTab(ui_tab, "界面设置")

        layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        cancel_btn = QPushButton("取消")
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _test_api(self):
        test_config = {
            "llm_api_key": self.llm_api_key.text().strip(),
            "llm_api_base": self.llm_api_base.text().strip(),
            "llm_model": self.llm_model.text().strip(),
        }
        self.api_test_btn.setEnabled(False)
        self.api_test_result.setText("测试中…")
        self.api_test_result.setStyleSheet("color: #888; font-size: 11px;")
        self.worker = ApiTestWorker(test_config)
        self.worker.finished.connect(self._on_api_test_done)
        self.worker.start()

    def _on_api_test_done(self, ok, msg):
        self.api_test_btn.setEnabled(True)
        self.api_test_result.setText(msg)
        self.api_test_result.setStyleSheet("color: green; font-size: 11px;" if ok else "color: red; font-size: 11px;")

    def _reload_prompt(self):
        try:
            with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                self.llm_prompt.setPlainText(f.read())
        except Exception:
            self.llm_prompt.setPlainText(DEFAULT_LLM_PROMPT)

    def _load_config(self):
        self.llm_api_key.setText(self.config.get("llm_api_key", ""))
        self.llm_api_base.setText(self.config.get("llm_api_base", "https://api.siliconflow.cn/v1"))
        self.llm_model.setText(self.config.get("llm_model", "Qwen/Qwen3.6-27B"))
        self.llm_temp.setValue(self.config.get("llm_temperature", 0.1))
        self._reload_prompt()
        self.theme.setCurrentText(self.config.get("theme", "light"))
        templates = self.config.get("notification_templates", DEFAULT_NOTIFICATION_TEMPLATES)
        current = self.config.get("last_template", "wechat")
        self.template_edit.setPlainText(templates.get(current, ""))

    def _save(self):
        self.config["llm_api_key"] = self.llm_api_key.text()
        self.config["llm_api_base"] = self.llm_api_base.text()
        self.config["llm_model"] = self.llm_model.text()
        self.config["llm_temperature"] = self.llm_temp.value()
        self.config["theme"] = self.theme.currentText()
        self.config["notification_template"] = self.template_edit.toPlainText()
        self.accept()