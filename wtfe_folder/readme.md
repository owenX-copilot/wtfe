# wtfe_folder

**Pipeline A2 - 文件夹级聚合分析**

## 功能

wtfe_folder 负责分析一个文件夹，聚合其中所有文件的 FileFact，推断模块的主要职责。

它会：
1. 扫描目录下所有支持的文件（调用wtfe_file）
2. 按角色聚类（SERVICE, CLI, TEST, UTILITY等）
3. 识别核心文件 vs 辅助文件
4. 提取模块能力（网络、IO、框架等）
5. 分析外部依赖
6. **递归处理子文件夹**

## 使用示例

### 分析单个文件夹

```bash
python wtfe_folder/wtfe_folder.py example/example_folder
```

**输出示例**：
```json
{
  "path": "D:\\project6\\wtfe\\example\\example_folder",
  "name": "example_folder",
  "files": [
    "app.py",
    "config.py",
    "main.py",
    "models.py",
    "routes.py"
  ],
  "core_files": [
    "main.py"
  ],
  "primary_role": "entry_point",
  "capabilities": [
    "languages",
    "has_network",
    "has_io",
    "has_tests",
    "frameworks",
    "total_structures"
  ],
  "external_deps": [
    "flask",
    "app",
    "config",
    "models",
    "routes"
  ],
  "subfolders": 2,
  "subfolder_details": [
    {
      "name": "tests",
      "path": "...",
      "files_count": 1,
      "primary_role": "test"
    },
    {
      "name": "utils",
      "path": "...",
      "files_count": 2,
      "primary_role": "unknown"
    }
  ]
}
```

## 核心逻辑

### 1. 角色聚类

根据 FileFact 的 roles 字段分组：
- ENTRY_POINT: 入口文件
- SERVICE: 服务/后端逻辑
- CLI: 命令行工具
- TEST: 测试文件
- CONFIG: 配置文件
- UTILITY: 工具函数

### 2. 核心文件识别

优先级权重：
```
ENTRY_POINT (10) > SERVICE (8) > CLI (7) > LIBRARY (5) > UTILITY (4)
```

结合置信度评分，选出Top 5核心文件。

### 3. 主要角色推断

按角色权重 × 文件数量 × 平均置信度，计算加权分数，确定模块主要职责。

### 4. 能力提取

聚合所有文件的 signals：
- `has_network`: 任一文件有网络信号
- `has_io`: 任一文件有IO信号
- `has_tests`: 包含TEST角色文件
- `frameworks`: 检测到的框架（React, Express等）
- `total_structures`: 类和函数总数

### 5. 依赖分析

从所有文件的 imports 中提取外部依赖，过滤标准库，返回Top 20。

### 6. 递归扫描

如果子目录存在且不在忽略列表中（`__pycache__`, `node_modules`等），递归调用 FolderAnalyzer。

## 支持的文件类型

与 wtfe_file 一致：
- Python (.py)
- JavaScript (.js/.jsx)
- TypeScript (.ts/.tsx)
- HTML (.html)
- Java (.java)
- JSON (.json)
- YAML (.yml/.yaml)
- Dockerfile
- Makefile
- Markdown (.md)
- Jupyter Notebook (.ipynb)

## 输出数据结构

### ModuleSummary
- `path`: 模块路径
- `name`: 模块名称
- `files`: 所有分析的文件列表
- `core_files`: 核心文件列表（Top 5）
- `primary_role`: 主要角色（entry_point/service/cli等）
- `capabilities`: 能力列表
- `external_deps`: 外部依赖列表（Top 20）
- `subfolders`: 子文件夹数量
- `subfolder_details`: 子文件夹摘要

## 设计考虑

### 为什么需要递归？

真实项目往往有这样的结构：
```
project/
├── main.py         (entry point)
├── app.py          (app logic)
├── utils/          (utilities)
│   ├── helper.py
│   └── logger.py
└── tests/          (tests)
    └── test_app.py
```

wtfe_folder 需要：
1. 分析顶层文件（main.py, app.py）
2. 递归分析 utils/（识别为utility模块）
3. 递归分析 tests/（识别为test模块）

最终输出包含完整的层次结构信息。

### 忽略目录

以下目录会被跳过：
```python
ignore_dirs = {
    '__pycache__', '.git', 'node_modules', 
    '.venv', 'venv', 'dist', 'build'
}
```

这些是构建产物或依赖目录，不包含项目源码。

## 与其他模块的关系

```
wtfe_file (单文件分析)
    ↓
wtfe_folder (文件夹聚合) ← 当前模块
    ↓
wtfe_project (项目级总结，未实现)
```

wtfe_folder 消费 wtfe_file 的输出（FileFact），产出 ModuleSummary。
