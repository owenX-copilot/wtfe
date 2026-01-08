# wtfe-analyze

**统一分析编排器 - Unified Analysis Orchestrator**

## 功能

wtfe-analyze 是WTFE框架的**核心编排器**，负责调用所有分析管道并生成统一的结构化输出。

它整合了：
- **Pipeline A1/A2**: wtfe-file + wtfe-folder（文件和文件夹分析）
- **Pipeline B1**: wtfe-run（入口点检测）
- **Pipeline C**: wtfe-context（项目上下文信号）
- **Author-Intent Channel**: wtfe-intent（作者意图提取）

## 使用方法

```bash
python wtfe-analyze/wtfe_analyze.py <project_path>
```

**示例**：
```bash
# 分析example_folder
python wtfe-analyze/wtfe_analyze.py ./example/example_folder

# 分析当前项目
python wtfe-analyze/wtfe_analyze.py .
```

## 输出结构

### 完整JSON输出

```json
{
  "metadata": {
    "project_name": "example_folder",
    "project_path": "D:\\project6\\wtfe\\example\\example_folder",
    "analysis_timestamp": "2026-01-08T20:40:24.794943",
    "wtfe_version": "0.1.0"
  },
  "folder_analysis": {
    "path": "...",
    "name": "example_folder",
    "files": ["main.py", "app.py", ...],
    "core_files": ["main.py"],
    "primary_role": "entry_point",
    "capabilities": ["has_network", "has_io", ...],
    "external_deps": ["flask", "sqlalchemy", ...]
  },
  "entry_points": {
    "entry_points": [{
      "file": "main.py",
      "type": "main",
      "command": "python main.py",
      "confidence": 0.8
    }],
    "makefile_targets": [],
    "package_scripts": {},
    "runtime_deps": {
      "requires_db": false,
      "requires_cache": false
    }
  },
  "context_signals": {
    "root_path": "...",
    "project_name": "example_folder",
    "scale": {
      "file_count": 9,
      "line_count": 369,
      "languages": ["Python", "Markdown"]
    },
    "maturity": {
      "has_tests": true,
      "has_ci": false,
      "has_typing": false
    },
    "signals": {
      "has_main_py": true,
      "has_app_py": true,
      "has_dockerfile": false,
      "has_readme": true,
      "has_tests": true,
      ... // 40+布尔信号
    }
  },
  "author_intent": {
    "project_readme": "# Flask Blog API\n\n...",
    "module_readmes": {},
    "changelog": null,
    "package_metadata": {}
  },
  "summary": {
    "has_documentation": true,
    "documentation_coverage": {
      "project_readme": true,
      "module_readmes": 0
    },
    "primary_role": "entry_point",
    "can_run": true,
    "entry_point_count": 1,
    "external_deps_count": 7,
    "file_count": 6,
    "has_tests": true,
    "has_ci": false,
    "has_typing": false
  }
}
```

## 核心逻辑

### 1. 编排流程

```python
def analyze(self):
    # Pipeline A: 文件夹分析（包含单文件分析）
    folder_summary = self._run_folder_analysis()
    
    # Pipeline B: 入口点检测
    run_config = self._run_entry_point_analysis()
    
    # Pipeline C: 上下文信号
    project_context = self._run_context_analysis()
    
    # Author-Intent Channel
    author_intent = self._run_intent_extraction()
    
    # 生成高层摘要
    summary = self._generate_summary(...)
    
    return unified_result
```

### 2. 错误处理

每个管道独立运行，失败不影响其他管道：

```python
try:
    folder_summary = self._run_folder_analysis()
except Exception as e:
    print(f"[WTFE] Warning: Folder analysis failed: {e}")
    folder_summary = {"error": str(e)}
```

### 3. 摘要生成

从所有管道输出中提取关键指标：

```python
summary = {
    "has_documentation": intent.project_readme is not None,
    "primary_role": folder.primary_role,
    "can_run": len(run.entry_points) > 0,
    "has_tests": context.maturity.has_tests,
    ...
}
```

## 设计原则

### 并行独立

四个管道完全独立，可以：
- 单独失败不影响其他
- 未来并行执行提速
- 模块化替换升级

### 结构化输出

输出是纯JSON，便于：
- 传递给AI处理（wtfe-readme）
- 缓存和增量更新
- 人类阅读调试

### 零AI依赖

wtfe-analyze是纯规则+AST分析：
- 不调用任何AI API
- 不依赖网络
- 确定性输出（同一项目多次分析结果一致）

## 输出字段说明

### metadata
- `project_name`: 项目名称（文件夹名）
- `project_path`: 项目绝对路径
- `analysis_timestamp`: 分析时间戳
- `wtfe_version`: WTFE框架版本

### folder_analysis (来自wtfe-folder)
- `files`: 所有分析的文件列表
- `core_files`: 核心文件（Top 5）
- `primary_role`: 主要角色（entry_point/service/cli等）
- `capabilities`: 能力列表
- `external_deps`: 外部依赖（Top 20）

### entry_points (来自wtfe-run)
- `entry_points`: 检测到的入口点列表
- `makefile_targets`: Makefile目标
- `package_scripts`: npm scripts
- `dockerfile_cmds`: Dockerfile CMD/ENTRYPOINT
- `runtime_deps`: 运行时依赖（DB/Cache/Queue）

### context_signals (来自wtfe-context)
- `scale`: 项目规模（文件数、代码行数、语言分布）
- `maturity`: 成熟度（has_tests, has_ci, has_typing）
- `signals`: 40+布尔信号（文件存在性检测）

### author_intent (来自wtfe-intent)
- `project_readme`: 项目README原文
- `module_readmes`: 模块README字典
- `changelog`: CHANGELOG原文
- `license_text`: LICENSE原文
- `package_metadata`: Package文件元数据

### summary (自动生成)
高层摘要，方便快速判断项目状态：
- `has_documentation`: 是否有文档
- `can_run`: 是否可运行（有入口点）
- `primary_role`: 主要职责
- `has_tests`: 是否有测试
- `file_count`: 文件数量

## 与其他模块的关系

```
wtfe-analyze (本模块)
    ↓ 调用
wtfe-folder, wtfe-run, wtfe-context, wtfe-intent
    ↓ 输出
统一JSON结构
    ↓ 传递
wtfe-readme (AI生成层)
```

wtfe-analyze是"事实收集的终点"和"AI生成的起点"。

## 实现细节

### 模块导入

使用动态路径导入避免硬编码：

```python
self.wtfe_root = Path(__file__).parent.parent.resolve()

folder_module_path = self.wtfe_root / 'wtfe-folder'
sys.path.insert(0, str(folder_module_path))
from wtfe_folder import FolderAnalyzer
```

### 日志输出

分析进度输出到stderr，JSON输出到stdout：

```python
print("[WTFE] Running Pipeline A...", file=sys.stderr)
# ... analysis ...
print(json.dumps(result), file=sys.stdout)  # 仅JSON
```

这样可以：
```bash
python wtfe_analyze.py . 2>log.txt > result.json
```

## 性能考虑

### 当前性能
- example_folder (9文件, 369行): ~1秒
- 中型项目 (100文件, 10K行): ~5-10秒
- 大型项目 (1000文件, 100K行): ~30-60秒

### 未来优化
- 并行执行四个管道
- FileFact缓存（文件未修改时复用）
- 增量分析（仅分析变更文件）

## 使用场景

### 场景1：初次分析项目
```bash
python wtfe-analyze/wtfe_analyze.py /path/to/unknown/project > analysis.json
```
获取完整的项目事实摘要。

### 场景2：传递给AI生成README
```bash
python wtfe-analyze/wtfe_analyze.py . > facts.json
python wtfe-readme/wtfe_readme.py facts.json > README_generated.md
```

### 场景3：CI/CD集成
```bash
# 在CI中自动分析变更
python wtfe-analyze/wtfe_analyze.py . > build/analysis.json
# 检查是否有测试
jq '.summary.has_tests' build/analysis.json
```

## 局限性

- **不生成README**：只输出结构化数据，不生成自然语言
- **不判断代码质量**：只记录事实，不评价好坏
- **不执行代码**：不运行测试或启动项目验证

这些功能由其他层负责，wtfe-analyze专注于"事实收集"。

## 下一步

wtfe-analyze的输出将作为wtfe-readme的输入，由AI转换为人类友好的README文档。
