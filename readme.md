# WTFE — Why The Folder Exists

**自动分析陌生代码项目，生成README文档。**

面对一个未知项目，不知道它是干什么的、怎么运行？WTFE通过静态分析提取项目结构和能力，结合AI生成人类友好的说明文档。

> 🌐 **Language**: [English](readme_en.md) | **中文**

## 快速开始

### 完整流程：生成README

**前置条件**：
1. 安装依赖：`pip install -r requirements.txt`
2. 设置环境变量 `WTFE_API_KEY` 或修改配置文件 `wtfe_readme/config.yaml`（二选一）。
   *注：如果未配置，程序将在首次运行时自动启动交互式配置向导。*

```bash
# 推荐：使用统一入口
python wtfe.py ./your-project

# 传统方式：管道组合
# 1. 设置环境变量
# $env:WTFE_API_KEY = "sk-..."  # Windows
# export WTFE_API_KEY="sk-..."  # Linux/Mac

# 2. 执行分析与生成
python wtfe_analyze/wtfe_analyze.py ./your-project | python wtfe_readme/wtfe_readme.py -
```

### 测试单个模块

```bash
# 克隆仓库
git clone https://github.com/owenX-copilot/wtfe.git
cd wtfe

# 使用统一入口调用各模块
python wtfe.py -m file example/app.py           # 单文件分析
python wtfe.py -m folder example/example_folder # 文件夹分析
python wtfe.py -m run example/example_folder    # 入口点检测
python wtfe.py -m context example/example_folder # 上下文分析
python wtfe.py -m analyze example/example_folder # 完整分析

# 查看帮助
python wtfe.py --help
```

## 功能模块

| 模块 | 功能 | 状态 |
|------|------|------|
| **wtfe_file** | 单文件分析，支持11种文件类型（Python/JS/TS/Java等） | ✅ |
| **wtfe_folder** | 文件夹递归分析，识别核心文件和模块职责 | ✅ |
| **wtfe_run** | 检测项目入口点（main/Makefile/Dockerfile/npm scripts） | ✅ |
| **wtfe_context** | 收集40+项目信号（规模/成熟度/技术栈） | ✅ |
| **wtfe_intent** | 提取现有README/LICENSE/CHANGELOG（作者意图） | ✅ |
| **wtfe_analyze** | 统一编排所有模块，输出结构化JSON | ✅ |
| **wtfe_readme** | AI生成自然语言README文档 | ✅ |

## 配置说明

### wtfe_readme配置（config.yaml）

```yaml
# API服务商（支持OpenAI兼容格式）
provider: openai
base_url: https://api.siliconflow.cn/v1  # 硅基流动（国内推荐）
# base_url: https://api.openai.com/v1   # OpenAI官方
# base_url: http://localhost:11434/v1   # Ollama本地模型

# API密钥（从环境变量读取）
api_key: ${WTFE_API_KEY}

# 模型选择
model: deepseek-ai/DeepSeek-V3.2  # 默认，性价比高（¥1/百万tokens）
# model: gpt-4o-mini                # OpenAI
# model: llama3.1:8b                # Ollama本地

# 生成参数
max_tokens: 4096
temperature: 0.7
language: zh-cn  # zh-cn | en
```

### 支持的AI服务

- **硅基流动（推荐）**: 国内可用，价格低，无需科学上网
- **OpenAI官方**: GPT-4o / GPT-4o-mini / GPT-3.5-turbo
- **本地模型**: Ollama / vLLM / LM Studio

## 工作原理

### 分析流程

```
┌─────────────┐
│ 源代码项目  │
└──────┬──────┘
       │
       ├──→ wtfe_file    (单文件特征提取)
       ├──→ wtfe_folder  (模块结构分析)
       ├──→ wtfe_run     (入口点检测)
       ├──→ wtfe_context (项目信号收集)
       └──→ wtfe_intent  (现有文档提取)
       │
       ↓
┌──────────────┐
│ wtfe_analyze │ 统一编排，生成JSON
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ wtfe_readme  │ AI转换为自然语言
└──────┬───────┘
       │
       ↓
  README.md
```

### 设计原则

1. **规则优先，AI辅助**: 文件分析、结构提取用规则完成，AI只负责最后的语言生成
2. **作者意图优先**: 如果项目已有README，作为最高权重参考
3. **零依赖分析**: 不运行代码，纯静态分析
4. **增量可缓存**: 文件未修改时可复用分析结果

## 输出示例

### 分析结果（JSON）

```json
{
  "metadata": {
    "project_name": "example_folder",
    "analysis_timestamp": "2026-01-08T20:40:24"
  },
  "folder_analysis": {
    "files": ["main.py", "app.py", "models.py", ...],
    "core_files": ["main.py"],
    "primary_role": "entry_point",
    "capabilities": ["has_network", "has_database", "has_tests"]
  },
  "entry_points": [
    {"file": "main.py", "type": "main", "command": "python main.py"}
  ],
  "context_signals": {
    "scale": {"file_count": 9, "line_count": 369},
    "maturity": {"has_tests": true, "has_ci": false}
  },
  "author_intent": {
    "project_readme": "# Flask Blog API\n\n..."
  }
}
```

### 生成的README

基于上述JSON，AI生成包含以下内容的README：
- 项目简介
- 功能特性
- 技术栈
- 安装运行方法
- 使用示例
- 测试说明

## 项目结构

```
wtfe/
├── core/models.py           # 数据结构定义
├── wtfe_file/               # 单文件分析
├── wtfe_folder/             # 文件夹聚合
├── wtfe_run/                # 入口点检测
├── wtfe_context/            # 上下文信号
├── wtfe_intent/             # 作者意图提取
├── wtfe_analyze/            # 统一编排器
├── wtfe_readme/             # AI生成层
│   ├── providers/           # AI服务抽象
│   ├── templates/prompt.py  # Prompt模板
│   ├── config.yaml          # 配置文件
│   └── wtfe_readme.py       # 主程序
└── example/                 # 测试示例
```

## 使用场景

- 快速理解开源项目
- 为旧项目补充文档
- 分析遗留代码库
- 评估项目质量
- 辅助代码审查

## 限制

- 仅静态分析，不执行代码
- 不理解业务逻辑
- 生成的README需人工审核
- AI成本取决于项目规模（小项目 < ¥0.01）

## License

MIT
