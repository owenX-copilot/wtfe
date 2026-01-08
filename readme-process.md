# WTFE — Why The Folder Exists

WTFE 是一个用于 **自动理解陌生代码与系统结构的分析工具链**。

它的目标不是"读懂一切代码"，而是在**最少上下文、最少人工介入、甚至不依赖 AI 的情况下**，回答一个工程中反复出现、却很少被系统性解决的问题：

> **"这段代码 / 这个文件 / 这个文件夹 / 这个进程，到底是干什么的？"**

---

## 核心架构：三管齐下的分析管道

WTFE 采用 **三条并行的自底向上分析管道**，分别从不同维度理解代码：

### Pipeline A - Capabilities（能力分析）

**从结构推断能力**

```
A1: 单文件分析 (wtfe-file)
   输入：单个源文件
   输出：FileFact（结构、信号、角色、置信度）
   
A2: 文件夹聚合 (wtfe-folder)  
   输入：目录 + 多个 FileFact
   输出：ModuleSummary（模块职责、核心文件、依赖）
   
A3: 项目能力总结 (wtfe-project)
   输入：多个 ModuleSummary
   输出：ProjectCapabilities（技术栈、架构类型、领域特征）
```

**核心问题**：  
- *这个文件能做什么？*  
- *这个模块提供什么能力？*  
- *这个项目属于什么类型？*

---

### Pipeline B - Operation（运行分析）

**从入口推断运行方式**

```
B1: 入口点检测 (wtfe-run)
   输入：项目根目录
   输出：EntryPoint[]（main、Makefile、package.json scripts、Dockerfile CMD）
   
B2: 启动命令推断
   输入：EntryPoint[] + 配置文件
   输出：RunConfig（命令、参数、环境变量、依赖服务）
   
B3: 运行时依赖分析
   输入：docker-compose、requirements.txt、package.json
   输出：RuntimeDeps（数据库、缓存、队列、外部服务）
```

**核心问题**：  
- *这个项目怎么跑起来？*  
- *需要哪些外部依赖？*  
- *是服务还是工具？*

---

### Pipeline C - Context（上下文分析）

**从元信号推断项目成熟度与环境**

```
C1: 项目元信息提取
   输入：README、LICENSE、package.json、pyproject.toml
   输出：ProjectMetadata（名称、版本、作者、描述）
   
C2: 工程质量信号检测
   输入：测试目录、CI 配置、类型标注、文档覆盖率
   输出：QualitySignals（has_tests、has_ci、has_typing、doc_coverage）
   
C3: 项目规模与成熟度评分
   输入：文件数、代码行数、Git 历史、依赖复杂度
   输出：ProjectContext（scale、maturity_score、complexity）
```

**核心问题**：  
- *这个项目处于什么阶段？*  
- *值不值得投入时间研究？*  
- *代码质量如何？*

---

### 最终汇聚：AI 增强表达层

```
三条管道输出 → 压缩事实 → AI 生成自然语言 README
```

**AI 仅用于最后一步**，而非贯穿整个分析过程。

---
## 总体架构：五层信息压缩模型

WTFE 采用 **自底向上的分层抽象** + **高权重作者意图融合** 机制：

```
                    ┌────────────────────────────┐
                    │  Author-Intent Channel      │
                    │  - project README.md        │
                    │  - module README.md         │
                    │  - folder README.md         │
                    └──────────────┬─────────────┘
                                   │（高权重融合）
┌──────────────────────────────────▼──────────────────────────────────┐
│        L4 · Project Semantic Summary Layer (给总结 AI / README AI)   │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│        L3 · Module Responsibility Layer                              │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│        L2 · File Functional Summary Layer                             │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│        L1 · File Feature Tree Layer                                   │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────┐
│        L0 · Raw Source Code                                            │
└──────────────────────────────────────────────────────────────────────┘
```

### 层级说明

| 层级 | 名称 | 实现模块 | 输出 |
|------|------|----------|------|
| **L0** | 原始源代码 | - | `.py`, `.js`, `.ts`, `.java` 等文件 |
| **L1** | 文件特征树 | `wtfe-file` | FileFact（结构、信号、角色、置信度） |
| **L2** | 文件功能摘要 | `wtfe-file` | 角色推断 + 能力标签 |
| **L3** | 模块职责层 | `wtfe-folder` | ModuleSummary（核心文件、主要职责、依赖关系） |
| **L4** | 项目语义总结 | `wtfe-readme` (AI) | 自然语言 README / 架构说明 |

### Author-Intent Channel（作者意图通道）

**特殊设计**：已有的 README/文档在生成时具有 **更高权重**：

- 如果项目已有 README.md → 作为"真实意图锚点"参与 L4 融合
- 如果模块有文档 → 优先信任作者的描述
- 信号冲突时 → 作者意图覆盖自动推断

**示例**：
```python
# 推断：这是个 Web 框架（因为检测到 Flask + routes）
# 作者 README：这是个"博客系统演示项目"
# 最终输出：博客系统（Web 框架特征被用作证据，但不是主要定位）
```

### 为什么这样设计？

1. **信息有损压缩**：每层丢弃细节，保留本质
2. **可增量计算**：L1 缓存后，文件不变则无需重算
3. **AI 仅在 L4**：避免 AI 参与底层事实提取（成本高、不稳定）
4. **作者意图优先**：机器推断永远是辅助，人类文档是权威

---
## 项目结构（实际目录）

```
wtfe/
├── core/                  # 核心数据模型
│   └── models.py         # FileFact, ModuleSummary, EntryPoint, RunConfig, ProjectContext, AuthorIntent
│
├── wtfe-file/            # Pipeline A1：单文件分析
│   ├── wtfe_file.py      # ✅ 已完成：支持 11 种文件类型
│   └── readme.md         # 模块文档
│
├── wtfe-folder/          # Pipeline A2：文件夹聚合
│   ├── wtfe_folder.py    # ✅ 已完成：递归分析、角色聚类、核心文件识别
│   └── readme.md         # 模块文档
│
├── wtfe-run/             # Pipeline B1：入口点检测
│   ├── wtfe_run.py       # ✅ 已完成：识别 main、Makefile、Docker、npm scripts
│   └── readme.md         # 模块文档
│
├── wtfe-context/         # Pipeline C：上下文分析
│   ├── wtfe_context.py   # ✅ 已完成：收集40+原始信号，不做预判
│   └── readme.md         # 模块文档
│
├── wtfe-intent/          # Author-Intent Channel：作者意图提取
│   ├── wtfe_intent.py    # ✅ 已完成：提取README/CHANGELOG/LICENSE/package元数据
│   └── readme.md         # 模块文档
│
├── wtfe-analyze/         # 统一编排器
│   ├── wtfe_analyze.py   # ✅ 已完成：整合所有管道，输出统一JSON
│   └── readme.md         # 模块文档
│
├── wtfe-readme/          # AI 生成层
│   ├── providers/        # AI服务提供商抽象
│   │   ├── base.py      # Provider基类
│   │   └── openai.py    # ✅ OpenAI兼容API实现
│   ├── templates/
│   │   └── prompt.py    # ✅ Prompt构建逻辑
│   ├── wtfe_readme.py   # ✅ 主生成器
│   ├── config.yaml      # ✅ 配置文件（支持环境变量）
│   └── readme.md        # 模块文档
│
│
├── example/              # 测试示例
│   ├── example_folder/   # 真实Flask项目示例（8文件，含utils/和tests/子目录）
│   └── ...              # 16个不同类型的测试文件
│
├── scripts/              # 批量测试脚本
│   └── test_examples.py  # ✅ 全部测试通过
│
├── readme.md             # 本文件
└── readme_en.md          # 英文版说明
```

---

## 当前进展

### ✅ 已完成

| 模块 | 状态 | 功能 |
|------|------|------|
| **core/models.py** | ✅ 完成 | 定义了所有数据结构（FileFact, ModuleSummary, EntryPoint, RunConfig, ProjectContext, AuthorIntent, Evidence, FileRole） |
| **wtfe-file** | ✅ 完成 | 支持 11 种文件类型，输出符合 FileFact 规范，包含角色推断和置信度评分 |
| **wtfe-folder** | ✅ 完成 | 递归文件夹分析，角色聚类，核心文件识别，能力聚合，支持子文件夹 |
| **wtfe-run** | ✅ 完成 | 入口点检测（Python main、Makefile targets、npm scripts、Dockerfile CMD、运行时依赖推断） |
| **wtfe-context** | ✅ 完成 | 收集40+项目信号（不预判类型），统计规模，提取依赖，检测成熟度指标 |
| **wtfe-intent** | ✅ 完成 | 提取作者意图文档（README/CHANGELOG/LICENSE），package元数据，高权重信号源 |
| **wtfe-analyze** | ✅ 完成 | 统一编排器，整合所有管道输出，生成结构化JSON，准备AI输入 |
| **wtfe-readme** | ✅ 完成 | AI生成层，支持OpenAI兼容API，默认DeepSeek-V3.2模型，环境变量配置 |
| **测试框架** | ✅ 完成 | 17个示例文件 + example_folder真实项目 + 批量测试脚本，所有测试通过 |

**wtfe-file 支持的文件类型**：
- Python (.py) - AST 解析
- JavaScript (.js/.jsx) - 正则提取，检测 CommonJS/ESM/React
- TypeScript (.ts/.tsx) - 类型和 JSX 检测
- HTML (.html) - 标签、表单、脚本块分析
- Java (.java) - 类、方法、main 入口检测
- JSON (.json) - 键提取，识别 package.json
- YAML (.yml/.yaml) - K8s/Compose 检测
- Dockerfile - FROM/EXPOSE/CMD 提取
- Makefile - target 提取
- Markdown (.md) - 标题和代码块统计
- Jupyter Notebook (.ipynb) - cell 类型统计

---� 下一步

| 优先级 | 模块 | 描述 |
|--------|------|------|
| 1 | **CLI 入口** | 统一命令行工具 `wtfe analyze <path>` 调用所有模块，输出完整分析结果 |
| 2 | **wtfe-readme** | AI 生成层：将压缩事实（FileFact + ModuleSummary + RunConfig + ProjectContext）项目成熟度分析（检测 tests、CI、typing、文档） |
| 4 | **CLI 入口** | 统一命令行工具 `wtfe analyze <path>` 调用所有模块 |
| 5 | **wtfe-readme** | AI 生成层：将压缩事实转为自然语言 README |

---

## 设计原则

### 1️⃣ 事实优先（Fact-first）

所有推断必须基于可验证的事实：
- 代码结构（AST、正则提取）
- 语言特征（类型标注、并发模型）
- 导入的库（requests → 网络，pytest → 测试）
- 文件名模式（test_*.py、config.json）

### 2️⃣ 规则优于 AI

**能不用 AI 的地方坚决不用**：
- 单文件分析：规则 + AST 足够
- 入口点检测：模式匹配即可
- 角色推断：基于信号的决策树

**AI 仅用于最后一步**：将结构化事实转为人类友好的语言。

### 3️⃣ 自底向上聚合

```
File Facts → Module Summary → Project Capabilities → AI-Generated README
```

每一层都是独立、可复用、可单独运行的。

### 4️⃣ 增量与缓存

- FileFact 可缓存，文件未修改时直接复用
- 模块分析可并行
- 支持仅分析变更部分

---

## 使用示例

### 分析单个文件

```bash
python wtfe-file/wtfe_file.py example/8bit_marshmallow.py
```

输出：
```json
{
  "path": "example/8bit_marshmallow.py",
  "filename": "8bit_marshmallow.py",
  "language": "python",
  "structures": {
    "classes": ["WatermelonPig", "SonnetServer"],
    "functions": ["bake_kernel", "compute_os_poem_hash", ...]
  },
  "signals": {
    "imports": ["random", "datetime", "typing"],
    "entry_point": true
  },
  "roles": ["entry_point"],
  "confidence": 1.0
}
```

### 检测项目入口点

```bash
python wtfe-run/wtfe_run.py .
```

输出：
```json
{
  "entry_points": [
    {
      "file": "wtfe-file/wtfe_file.py",
      "type": "main",
      "command": "python wtfe-file/wtfe_file.py",
      "confidence": 0.8
    }
  ],
  "makefile_targets": ["all", "build", "run"],
  "requires_db": false,
  "requires_cache": false
}
```

### 批量测试所有示例

```bash
python scripts/test_examples.py
```

输出：
```
8bit_marshmallow.py => OK
clockwork_chrysalis.py => OK
...
Wrote results to example/example_results.json
```

---

## 与 AI 的关系

WTFE **不依赖 AI 存在**，但**天然适合与 AI 配合**：

| 阶段 | WTFE 负责 | AI 负责 |
|------|-----------|---------|
| **单文件** | 提取结构、信号、角色 | ❌ 不参与 |
| **模块级** | 聚合事实、建立依赖关系 | ❌ 不参与 |
| **项目级** | 压缩成结构化摘要 | ✅ 将事实转为自然语言 |

**成本对比**：
- **不用 AI**：500 文件 × 规则分析 = 几秒（可缓存）
- **全程 AI**：500 文件 × API 调用 = $$$ + 不确定性

**WTFE 哲学**：
> 把 AI 从"苦力"变成"作家"——它不负责理解代码，只负责把已经理解好的事实写得更人性化。

---

## 非目标（刻意不做）

- ❌ 不保证业务语义完全正确
- ❌ 不替代人工代码审查
- ❌ 不进行安全漏洞扫描
- ❌ 不尝试"读懂作者想法"

WTFE 关注的是 **"工程现实"而非"作者意图"**。

---

## 适用人群

- 面对大量陌生代码的开发者
- 运维 / SRE / 系统工程师
- 研究 AI 生成代码可解释性的开发者
- 需要快速判断"值不值得读下去"的人

---

## 一句话总结

> **WTFE 是一套把"代码存在的理由"从混沌中提炼出来的工程化方法。**

它不保证你立刻理解系统，  
但它保证你不会再面对一堆文件，却完全不知道从哪开始。

---

## 下一步计划

按优先级执行：

1. ✅ ~~重构 wtfe-file 输出为 FileFact 对象~~
2. ✅ ~~实现 wtfe-folder（Pipeline A2）~~
3. ✅ ~~实现 wtfe-context（Pipeline C）~~
4. ✅ ~~实现 wtfe-intent（Author-Intent Channel）~~
5. ✅ ~~实现 wtfe-analyze（统一编排器）~~
6. ✅ ~~实现 wtfe-readme（AI 生成层）~~
7. 📋 **测试和优化**

**当前状态**：🎉 **所有核心模块已完成！** 可运行完整流程：

```bash
# 设置API Key
$env:WTFE_API_KEY = "sk-your-api-key"  # Windows
# export WTFE_API_KEY="sk-xxx"  # Linux/Mac

# 一键生成README
python wtfe-analyze/wtfe_analyze.py ./your-project | python wtfe-readme/wtfe_readme.py -
```

1. ✅ ~~重构 wtfe-file 输出为 FileFact 对象~~
2. ✅ ~~实现 wtfe-folder（Pipeline A2）~~
3. ✅ ~~实现 wtfe-context（Pipeline C）~~
4. ✅ ~~实现 wtfe-intent（Author-Intent Channel）~~
5. ✅ ~~实现 wtfe-analyze（统一编排器）~~
6. ✅ ~~实现 wtfe-readme（AI 生成层）~~
7. 📋 **测试和优化**

**当前状态**：🎉 **所有核心模块已完成！** 可运行完整流程生成README。