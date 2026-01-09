# wtfe_context

**Pipeline C - 项目上下文与成熟度信号采集**

## 功能

wtfe_context 负责收集项目级的**原始信号**，而不做最终结论。

它扫描项目根目录，检测40+种文件存在性信号、统计项目规模、提取依赖列表，将这些**事实性证据**交给后续的AI层进行综合判断。

## 设计原则

### ❌ 不做的事情
- **不预判项目类型**（不输出"这是Django项目"这样的结论）
- **不推断框架**（不基于规则硬编码"有app.py就是Flask"）
- **不评分**（不输出"成熟度8/10"这样的主观评价）

### ✅ 只做的事情
- **检测文件存在性**（has_main_py, has_dockerfile等40+布尔值）
- **统计客观数据**（文件数、代码行数、语言分布）
- **提取依赖列表**（从requirements.txt、package.json中提取前20个依赖）

## 检测的信号类别

### 项目结构文件（7种）
```
has_setup_py, has_pyproject_toml, has_package_json, 
has_cargo_toml, has_go_mod, has_pom_xml, has_requirements_txt
```

### 入口文件（7种）
```
has_main_py, has_app_py, has_manage_py, has_wsgi_py,
has_index_js, has_server_js, has_main_go
```

### 框架配置（4种）
```
has_next_config, has_vite_config, has_webpack_config, has_tsconfig
```

### 构建/部署（3种）
```
has_dockerfile, has_docker_compose, has_makefile
```

### 文档（4种）
```
has_readme, has_license, has_docs_dir, has_changelog
```

### 测试（5种）
```
has_tests, has_test_dir, has_pytest_ini, 
has_jest_config, has_coverage_config
```

### CI/CD（5种）
```
has_ci, has_github_actions, has_gitlab_ci, 
has_travis, has_jenkins
```

### 代码质量（5种）
```
has_typing, has_eslint, has_prettier, 
has_mypy_ini, has_black_config
```

### 版本控制（2种）
```
has_git, has_gitignore
```

### 依赖（原始列表）
```
dependencies: {
  python: ["flask", "requests", ...],  // 前20个
  nodejs: ["react", "express", ...]    // 前20个
}
```

## 使用示例

### 分析项目上下文

```bash
python wtfe_context/wtfe_context.py .
```

**输出示例**：
```json
{
  "root_path": "D:\\project6\\wtfe",
  "project_name": "wtfe",
  "scale": {
    "file_count": 28,
    "line_count": 2832,
    "languages": ["Python", "JavaScript", "Markdown"]
  },
  "maturity": {
    "has_tests": false,
    "has_ci": false,
    "has_typing": true
  },
  "signals": {
    "has_setup_py": false,
    "has_package_json": false,
    "has_main_py": true,
    "has_app_py": false,
    "has_dockerfile": false,
    "has_readme": true,
    "has_tests": false,
    "has_ci": false,
    "has_typing": true,
    "has_git": true,
    "dependencies": {
      "python": ["flask", "requests"]
    }
  }
}
```

## 为什么这样设计？

### 问题：规则无法涵盖所有项目类型

如果我们用规则判断：
```python
if has_app_py:
    return "Flask项目"
```

会遇到问题：
- app.py可能是任意Web框架（FastAPI、Bottle、自定义）
- app.py可能只是普通模块名，不是入口
- 非标准项目结构无法识别

### 解决方案：信号 → AI

我们提供**所有可观测信号**：
```json
{
  "has_main_py": true,
  "has_app_py": true,
  "has_wsgi_py": false,
  "has_dockerfile": true,
  "has_requirements_txt": true,
  "dependencies": {
    "python": ["flask", "gunicorn", "sqlalchemy"]
  }
}
```

AI可以综合推断：
> "有main.py和app.py，依赖flask和gunicorn，有Dockerfile但没有wsgi.py，可能是一个容器化部署的Flask应用"

### 优势

1. **扩展性强**：新项目类型不需要修改代码，AI自适应
2. **无误判风险**：不做硬编码判断，避免"有manage.py不一定是Django"的尴尬
3. **信息完整**：40+信号提供全面视角，比单一规则准确
4. **可解释**：AI的判断基于哪些信号一目了然

## 与其他模块的关系

```
wtfe_context (收集信号)
    ↓
wtfe_readme (AI综合判断)
    ↓
最终README (自然语言描述)
```

wtfe_context不负责"理解"项目，只负责"观测"项目。

## 输出数据结构

### scale（规模）
- `file_count`: 代码文件总数
- `line_count`: 代码总行数
- `languages`: 语言分布列表

### maturity（成熟度-仅3个核心指标）
- `has_tests`: 是否有测试
- `has_ci`: 是否有CI配置
- `has_typing`: 是否使用类型标注

### signals（原始信号-40+个布尔值）
所有文件存在性检测结果 + 依赖列表

## 局限性

- **不递归扫描依赖内容**：只看顶层package文件
- **不解析代码逻辑**：只检查文件存在性，不读取内部实现
- **采样限制**：类型检测仅采样前10个Python文件

这些都是有意为之，保持模块轻量、快速、确定性。
