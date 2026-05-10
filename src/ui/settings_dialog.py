import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QTabWidget,
                                QWidget, QFormLayout, QDoubleSpinBox, QGroupBox,
                                QFileDialog, QTextEdit, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from ..modules.config import DEFAULT_LLM_PROMPT, PROMPT_FILE, update_prompt_template
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
        self.setMinimumWidth(700)
        self.setMinimumHeight(650)
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
        prompt_tip = QLabel("提示词定义了 AI 的角色和任务，通知模板部分会自动同步。")
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
            "在此编辑通知模板，保存后会自动同步到提示词中。\n"
            "AI 将直接按照此格式输出课程通知。\n\n"
            "格式说明：\n"
            "- 每行一门课程，用 | 分隔字段\n"
            "- 支持的字段：日期、科目、时间、位置\n"
            "- 如果有多门课程，每门课程占一行\n"
            "- 最后一个分隔线之后的文字会被识别为页脚（如\"此条信息不用回复\"）"
        )
        tip.setStyleSheet("color: #888; font-size: 11px;")
        tip.setWordWrap(True)
        template_layout.addWidget(tip)

        self.template_edit = QTextEdit()
        self.template_edit.setMinimumHeight(250)
        template_layout.addWidget(self.template_edit, 1)

        template_btn_row = QHBoxLayout()
        template_btn_row.addStretch()
        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._reset_template)
        template_btn_row.addWidget(reset_btn)
        template_layout.addLayout(template_btn_row)

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

    def _reset_template(self):
        default_template = """📚 课程通知
━━━━━━━━━━━━━━━━━━
📅 日期：5月4日 周一 | 📖 科目：数学 | ⏰ 时间：08:00-10:00（上午） | 📍 位置：VIP202
📅 日期：5月4日 周一 | 📖 科目：英语 | ⏰ 时间：10:00-12:00（上午） | 📍 位置：VIP301
📅 日期：5月5日 周二 | 📖 科目：物理 | ⏰ 时间：14:00-16:00（下午） | 📍 位置：VIP105
━━━━━━━━━━━━━━━━━━
此条信息不用回复，如有特殊情况提前沟通"""
        self.template_edit.setPlainText(default_template)

    def _load_config(self):
        self.llm_api_key.setText(self.config.get("llm_api_key", ""))
        self.llm_api_base.setText(self.config.get("llm_api_base", "https://api.siliconflow.cn/v1"))
        self.llm_model.setText(self.config.get("llm_model", "Qwen/Qwen3.6-27B"))
        self.llm_temp.setValue(self.config.get("llm_temperature", 0.1))
        self._reload_prompt()
        self.theme.setCurrentText(self.config.get("theme", "light"))
        
        # 加载通知模板
        template = self.config.get("notification_template", "")
        if not template:
            self._reset_template()
        else:
            self.template_edit.setPlainText(template)

    def _save(self):
        self.config["llm_api_key"] = self.llm_api_key.text()
        self.config["llm_api_base"] = self.llm_api_base.text()
        self.config["llm_model"] = self.llm_model.text()
        self.config["llm_temperature"] = self.llm_temp.value()
        self.config["theme"] = self.theme.currentText()
        
        # 保存通知模板并同步到提示词
        template = self.template_edit.toPlainText()
        self.config["notification_template"] = template
        
        # 更新提示词文件中的模板部分
        try:
            update_prompt_template(template)
        except Exception as e:
            from loguru import logger
            logger.error(f"更新提示词模板失败: {e}")
        
        self.accept()
