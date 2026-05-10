<div align="center">

# OCR-XDF 课程信息提取工具

截图 → AI视觉识别 → 通知生成，一站式自动化

</div>

## 项目简介

一款基于 **PyQt6** 的桌面工具，专为需要频繁记录课程安排的学生、教务人员设计。通过粘贴课程表截图，AI 自动识别并生成格式化通知文本，支持一键复制发送。

**工作流程：** 粘贴图片 → AI视觉识别 → 自动排序 → 通知生成

## 功能特性

- **图片粘贴** — 支持 Ctrl+V 粘贴图片，最多同时处理5张
- **AI识别** — 通过视觉大模型（VLM）直接从图片中提取课程信息，无需本地OCR
- **自动排序** — 课程按日期自动排序，确保通知顺序正确
- **自定义模板** — 支持自定义通知模板，AI会严格按照模板格式输出
- **多图合并** — 多张图片的课程自动合并去重
- **历史记录** — 自动保存处理记录，支持查看
- **主题切换** — 支持亮色/暗色主题

## 开始使用

### 环境要求

- Python 3.10+
- 操作系统：Windows 10/11

### 安装

```bash
# 克隆仓库
git clone https://github.com/<your-username>/OCR-XDF.git
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

1. 启动应用，点击菜单 **工具 → 设置**
2. 填入 API Key 和 API Base URL（默认为 `https://api.siliconflow.cn/v1`）
3. 选择模型（推荐 `Qwen/Qwen3-VL-32B-Instruct` 等视觉模型）

## 项目结构

```
OCR-XDF/
├── src/                          # 源代码
│   ├── __main__.py              # 入口
│   ├── main_window.py           # 主窗口
│   ├── modules/                 # 核心模块
│   │   ├── config.py            # 配置管理
│   │   ├── extractor.py         # AI信息提取
│   │   ├── screenshot.py        # 截图功能
│   │   ├── history.py           # 历史记录
│   │   └── theme.py             # 主题管理
│   ├── ui/                      # UI组件
│   │   ├── settings_dialog.py   # 设置对话框
│   │   ├── history_dialog.py    # 历史记录对话框
│   │   └── region_selector.py   # 区域选择器
│   ├── config/                  # 配置文件（自动生成）
│   ├── history/                 # 历史记录（自动生成）
│   └── screenshots/             # 截图存档（自动生成）
├── 参考图片/                     # 示例图片
├── 提示词.md                    # AI识别提示词
├── 需求.md                      # 需求文档
├── pyproject.toml               # 项目配置
├── requirements.txt             # 依赖列表
└── LICENSE                      # MIT 许可证
```

## 使用说明

1. **粘贴图片** — 按 Ctrl+V 粘贴课程表截图（可粘贴多张）
2. **开始识别** — 点击「开始识别」按钮，AI自动提取课程信息
3. **查看结果** — 课程按日期排序显示，格式化为通知文本
4. **复制发送** — 点击「复制到剪贴板」即可发送

## 通知模板自定义

在 **设置 → 通知模板** 中可自定义通知格式：

```
📚 课程通知
━━━━━━━━━━━━━━━━━━
📅 日期：X月X日 周X | 📖 科目：XXX | ⏰ 时间：HH:MM-HH:MM（上午/下午） | 📍 位置：XXX
━━━━━━━━━━━━━━━━━━
此条信息不用回复，如有特殊情况提前沟通
```

- 分隔线之间的课程行会自动按日期排序
- 分隔线之外的内容（标题、页脚）会完整保留

## 技术栈

| 模块 | 技术 |
|------|------|
| GUI 框架 | PyQt6 |
| AI 视觉识别 | OpenAI 兼容 API（视觉大模型） |
| 截图 | PIL |
| 日志 | loguru |

## 推荐模型

| 模型 | 特点 |
|------|------|
| Qwen/Qwen3-VL-32B-Instruct | 速度快，识别准确（推荐） |
| Qwen/Qwen3-Omni-30B-A3B-Instruct | 激活参数少，效率高 |
| Qwen/Qwen3.5-9B | 轻量级，速度快 |

## 开发相关

### 打包为可执行文件

```bash
pip install pyinstaller
pyinstaller --name="OCR-XDF" --windowed --onefile src/__main__.py
```

### 提示词定制

AI 识别依赖 `提示词.md` 中的结构化提示词，可根据实际课程表格式进行调整。

## 许可证

本项目基于 [MIT](./LICENSE) 许可证开源。
