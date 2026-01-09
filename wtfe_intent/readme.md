# wtfe_intent

**Author-Intent Channel - 作者意图通道**

## 功能

wtfe_intent 负责提取项目中**作者的显式文档和意图信号**，作为高权重证据参与最终AI生成。

它扫描并读取：
- README文件（项目级和模块级）
- CHANGELOG / CONTRIBUTING / LICENSE
- Package元数据（package.json, setup.py, pyproject.toml等）

## 设计原则

### 作者意图优先

在WTFE的五层架构中，作者意图通道具有**最高权重**：

```
Author-Intent Channel (高权重)
    ↓（融合）
L4: Project Semantic Summary (AI生成)
```

**为什么？**
- 机器推断永远是辅助，人类文档是权威
- README是"真实意图锚点"，当推断与文档冲突时，优先采信文档
- 作者知道项目真正的用途，机器只能观测表象

## 使用示例

### 提取项目意图信号

```bash
python wtfe_intent/wtfe_intent.py .
```

**输出示例**：
```json
{
  "project_readme": "# My Project\n\n...",
  "module_readmes": {
    "utils/readme.md": "# Utilities\n\n...",
    "tests/readme.md": "# Tests\n\n..."
  },
  "changelog": "# Changelog\n\n## [1.0.0] - 2024-01-01\n...",
  "license_text": "MIT License\n\n...",
  "package_metadata": {
    "package_json": {
      "name": "my-project",
      "version": "1.0.0",
      "description": "A great project",
      "author": "John Doe"
    }
  }
}
```

## 检测的内容

### README文件
- 项目根目录：`README.md`, `readme.txt`, `README.rst`, `readme`
- 模块目录：递归查找所有子目录的README（忽略node_modules等）

### 其他文档
- CHANGELOG: `CHANGELOG.md`, `HISTORY.md`, `CHANGES.md`
- CONTRIBUTING: `CONTRIBUTING.md`, `CONTRIBUTING.rst`
- LICENSE: `LICENSE`, `LICENSE.md`, `COPYING`

### Package元数据
- JavaScript: `package.json` (name, version, description, author, scripts等)
- Python: `setup.py`, `pyproject.toml`, `setup.cfg`
- Rust: `Cargo.toml`
- Go: `go.mod`
- Ruby: `Gemfile`, `*.gemspec`
- Java: `pom.xml`, `build.gradle`

## 安全限制

### 文件大小
- 默认最大500KB，超过则返回`[File too large: X bytes]`
- 防止读取巨大的生成文件

### 编码处理
- 优先UTF-8
- 失败则回退Latin-1
- 完全失败返回None

### 忽略目录
自动跳过：
```python
__pycache__, node_modules, .git, .svn,
venv, env, .venv, build, dist, target,
.pytest_cache, .mypy_cache, .idea, .vscode
```

## 输出数据结构

### AuthorIntent (core/models.py)
```python
@dataclass
class AuthorIntent:
    project_readme: Optional[str]           # 根README内容
    module_readmes: Dict[str, str]          # 路径 -> README内容
    changelog: Optional[str]                # CHANGELOG内容
    contributing: Optional[str]             # CONTRIBUTING内容
    license_text: Optional[str]             # LICENSE内容
    package_metadata: Dict[str, Any]        # Package文件提取的元数据
```

## 与其他模块的关系

```
wtfe_file, wtfe_folder, wtfe_run, wtfe_context (机器推断)
    +
wtfe_intent (作者意图，高权重)
    ↓
wtfe_readme (AI综合生成)
```

wtfe_intent提供的内容会在AI生成README时作为**最可信的参考**。

## 示例场景

### 场景1：推断与文档一致
```
机器推断：has_app_py=true, has_flask=true → Flask应用
作者README：这是一个Flask博客API
AI输出：基于Flask的博客API（两者一致，高置信度）
```

### 场景2：推断与文档冲突
```
机器推断：有main.py, app.py, routes.py → 完整的Web应用
作者README：这是一个Flask框架的演示项目
AI输出：Flask演示项目（采信作者意图，不是生产应用）
```

### 场景3：无文档但有推断
```
机器推断：有app.py, requirements.txt (flask)
作者README：无
AI输出：可能是Flask应用（基于推断，但标注为低置信度）
```

## 局限性

- **不解析代码**：只读文档文件，不分析Python/JS源码中的docstring
- **不验证真实性**：README写"这是React应用"但实际是Flask，不会检测矛盾
- **不提取所有元数据**：package.json只提取关键字段，不是完整解析

这些是有意为之，保持模块职责清晰：wtfe_intent只负责"读取作者说了什么"，不负责"判断作者说得对不对"。

## 下一步

该模块输出直接传递给wtfe_analyze统一编排，最终由wtfe_readme的AI层综合处理。
