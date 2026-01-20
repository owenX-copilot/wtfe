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

### 使用在线服务（可选）

WTFE 提供了完整的在线API服务，支持用户认证、API密钥管理和使用限制：

```bash
# 用户注册
python wtfe.py auth register

# 用户登录
python wtfe.py auth login

# 创建API密钥（每个用户最多2个）
python wtfe.py auth api-key

# 查看用户信息
python wtfe.py auth user-info

# 重新发送验证邮件
python wtfe.py auth resend-verification

# 使用在线服务分析项目
python wtfe.py online /path/to/your-project --detail
```

**注意**：在线服务是可选的，推荐使用本地CLI自建分析环境以保护隐私和降低成本。

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
| **wtfe_online** | 在线API服务，支持用户认证和API密钥管理 | ✅ |

### 在线服务特性
- **用户认证系统**：注册、登录、邮箱验证
- **API密钥管理**：创建API密钥，每个用户最多2个密钥
- **使用限制**：每个API密钥每天最多10次调用
- **隐私保护**：所有分析数据通过HTTPS加密传输
- **免费额度**：提供有限的免费调用额度（防止滥用）
- **自动认证**：登录后自动保存认证信息，下次使用无需重新登录
- **SSL支持**：自动处理SSL证书问题，支持自签名证书
- **文件上传**：支持目录（自动压缩为tar.gz）和文件（zip/tar.gz）上传
- **详细模式**：支持 `--detail` 参数启用详细分析模式
- **优雅等待效果**：内置等待管理器，提供打字机动画效果，让长时间操作不再枯燥
- **智能README保存**：自动检测现有README文件，智能处理覆盖和备份，避免意外数据丢失

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
5. **隐私保护**: 默认只发送结构化摘要给AI，不上传源码内容

### 隐私与详细模式

**默认模式（最小暴露）**：
- WTFE 仅将项目的结构化摘要、文件列表、检测到的入口点类型发送给 AI
- 不上传任何源代码文件内容
- 适用于私有项目或隐私敏感场景

**详细模式（`--detail` 或 `-d`）**：
- 启用后，WTFE 会读取识别到的入口文件内容并随分析数据一起发送给 AI
- 使用 **Token 预算控制**：
  - 如果入口文件 < 8000 tokens：发送完整内容，AI 可生成精确的启动命令
  - 如果入口文件 > 8000 tokens：自动降级为片段抽取（前100行+后50行）并提示用户"不保证命令准确性"
- 用法：`python wtfe.py --detail ./your-project`
- 推荐用于：学习项目、示例代码、需要精确启动指令的场景

**何时使用详细模式**：
- ✅ 公开/开源项目
- ✅ 学习类代码（教程、Demo）
- ✅ 需要 AI 给出准确的启动命令和参数
- ❌ 私有/商业项目（除非已评估隐私风险）
- ❌ 包含敏感信息的代码库

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

### 通用限制
- 仅静态分析，不执行代码
- 不理解业务逻辑
- 生成的README需人工审核
- AI成本取决于项目规模（小项目 < ¥0.01）

### 在线服务限制
- **调用限制**：每个API密钥每天最多10次调用
- **文件大小**：最大上传文件2GB
- **认证要求**：需要注册并验证邮箱才能使用
- **API密钥**：每个用户最多创建2个API密钥
- **隐私考虑**：项目文件会上传到服务器进行分析
- **网络依赖**：需要稳定的网络连接

### 推荐使用场景
- **推荐使用本地CLI**：对于私有项目或需要保护隐私的场景
- **推荐使用在线服务**：对于公开项目、快速原型或不想配置AI API密钥的场景
- **混合使用**：可以先试用在线服务，熟悉后再切换到本地CLI

## 支持的编程语言

wtfe_file 模块支持分析以下 **11 种** 编程语言及格式：

| 语言 | 扩展名 | 支持内容 |
|------|--------|---------|
| Python | `.py` | 导入、函数、类、装饰器、主模块 |
| JavaScript | `.js` | 导入、导出、函数、类、变量 |
| TypeScript | `.ts` | 类型定义、接口、导入、导出 |
| Java | `.java` | 包、类、方法、导入 |
| HTML | `.html` | 标签、脚本、样式链接 |
| JSON | `.json` | 键值对、嵌套结构 |
| YAML | `.yaml`, `.yml` | 配置键、嵌套结构 |
| Dockerfile | `Dockerfile` | FROM、RUN、CMD、ENTRYPOINT 等 |
| Makefile | `Makefile` | 目标、依赖、命令 |
| Markdown | `.md` | 标题、代码块、链接 |
| Jupyter Notebook | `.ipynb` | 代码单元、Markdown单元 |

**可扩展性**：其他语言支持可通过添加新的 extractor 模块来扩展（例如 Go、Rust、PHP 等）。

## License

MIT（见 LICENSE 文件，SPDX: MIT）

本项目采用 MIT 许可证，详见仓库根目录的 `LICENSE` 文件以获取完整条款。
