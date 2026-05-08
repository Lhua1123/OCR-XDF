<div align="center">

# OCR-XDF 课程信息提取工具

📸 截图 → OCR识别 → AI提取 → 通知生成，一站式自动化

</div>

## 项目简介

一款基于 **PyQt6** 的桌面工具，专为需要频繁记录课程安排的学生、教务人员设计。通过截图即可自动完成课程信息提取，并生成格式化通知文本。

**工作流程：** 屏幕截图/导入图片 → OCR文字识别 → AI结构化提取 → 通知文本生成

## 功能特性

- **截图** — 全屏截图、区域截图，支持导入本地图片
- **OCR识别** — 集成 PaddleOCR 本地识别，中英文混排支持
- **AI提取** — 通过视觉大模型（VLM）从 OCR 文本中提取结构化课程信息（课程名、时间、地点、教师等）
- **双模式** — 支持本地脚本提取（离线可用）和 AI/LLM 提取，AI 失败时自动回退
- **通知模板** — 内置微信、钉钉、短信等多种通知模板，一键复制或保存
- **历史记录** — 自动保存处理记录，支持查看和导出（JSON/CSV）
- **主题切换** — 支持亮色/暗色主题切换
- **跨平台** — 支持 Windows、macOS、Linux

## 开始使用

### 环境要求

- Python 3.10+
- 操作系统：Windows 10/11（推荐）、macOS、Linux

### 安装

```bash
# 克隆仓库
git clone https://github.com/Lhua1123/OCR-XDF.git
cd OCR-XDF

# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
python -m src
```

### 配置 API

首次使用需配置视觉大模型 API：

1. 启动应用，点击 **设置**
2. 填入 API Key 和 API Base URL（如 `https://api.siliconflow.cn/v1`）
3. 选择模型（推荐 `Qwen/Qwen2.5-VL-72B` 等视觉模型）

## 项目结构

```
OCR-XDF/
├── src/                      # 源代码
│   ├── __main__.py          # 入口
│   ├── main_window.py       # 主窗口
│   ├── modules/             # 核心模块
│   │   ├── config.py        # 配置管理
│   │   ├── extractor.py     # 信息提取
│   │   ├── screenshot.py    # 截图功能
│   │   ├── history.py       # 历史记录
│   │   └── theme.py         # 主题管理
│   ├── ui/                  # UI 组件
│   │   ├── settings_dialog.py
│   │   ├── history_dialog.py
│   │   └── region_selector.py
│   ├── config/              # 配置文件
│   ├── history/             # 历史记录
│   └── screenshots/         # 截图存档
├── 参考图片/                 # 示例图片
├── 提示词.md                # AI 提取提示词
├── pyproject.toml           # 项目配置
├── requirements.txt         # 依赖列表
└── LICENSE                  # MIT 许可证
```

## 技术栈

| 模块 | 技术 |
|------|------|
| GUI 框架 | PyQt6 |
| OCR 引擎 | PaddleOCR |
| AI 提取 | OpenAI 兼容 API（视觉大模型） |
| 截图 | mss / PIL |
| 日志 | loguru |

## 开发相关

### 打包为可执行文件

```bash
pip install pyinstaller
pyinstaller --name="OCR-XDF" --windowed --onefile --add-data="src;src" src/__main__.py
```

### 提示词定制

AI 提取依赖 `提示词.md` 中的结构化提示词，可根据实际课程表格式进行调整优化。

## 许可证

本项目基于 [MIT](./LICENSE) 许可证开源。
