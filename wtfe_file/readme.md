# WTFE_file — 管线 A1：文件级事实提取

WTFE_file 是 WTFE 分析框架的**第一层**，负责单文件级别的结构化事实提取。

它是整个分析管线的基础，为上层聚合与推断提供高质量、可缓存的结构化数据。

## 核心职责

> **将单个源文件转换为机器可读的"文件事实描述（FileFact）"**

不依赖项目上下文、不假设命名规范、不调用 AI。

---

## 核心目标

WTFE 的设计目标是降低理解陌生代码（尤其是非规范代码）的心理与分析成本，适用于：

- 由 AI 自动生成、命名极端但逻辑成立的代码
- 缺乏文档、注释极少的遗留文件
- 单文件功能模块（并发、工具类、实验性代码等）
- 在阅读源码之前进行“方向判断”

---

## 分析维度

WTFE 当前关注 **“结构信号”而非“语义解释”**，主要包括：

### 1. 基础属性
- 语言类型（基于文件后缀与解析能力）
- 文件名

### 2. 结构抽取
- 定义的类（classes）
- 定义的函数 / 方法（functions）
- 可见的全局符号（globals）

> 注意：globals 可能包含局部变量噪声，其目的是**反映复杂度与风格极端程度**，而非严格语义分类。

### 3. 行为信号（Signals）
- imports：使用到的标准库 / 第三方库
- network：是否存在网络相关调用（如 socket / requests）
- io：是否存在文件或标准 IO 行为

这些信号用于**推断文件职责边界**，而不是做安全或性能审计。

---

## 设计原则

1. **独立性** — 每个文件都是独立分析单元，不依赖项目上下文
2. **容错性** — 即使文件命名混乱、代码风格极端也能提取事实
3. **确定性** — 同一文件多次分析结果完全一致（可缓存）
4. **可扩展** — 新语言支持通过添加 Extractor 实现
5. **零 AI** — 纯规则/AST/正则提取，无任何 AI 调用

---

## 输出示例（简化）

```json
{
  "language": "python",
  "file": "example.py",
  "structures": {
    "classes": ["ExampleClass"],
    "functions": ["main", "helper"],
    "globals": ["x", "y"]
  },
  "signals": {
    "imports": ["threading", "time"],
    "network": [],
    "io": []
  }
}

```

## 当前支持的文件类型

| 类型 | 扩展名/文件名 | Extractor | 提取内容 |
|------|---------------|-----------|----------|
| Python | `.py` | `PythonExtractor` | AST: classes/functions/imports, network/io 检测 |
| JavaScript | `.js`, `.jsx` | `JsExtractor` | imports/require, functions/classes, CommonJS/ESM, Express/React 标记 |
| TypeScript | `.ts`, `.tsx` | `TsExtractor` | imports, types/interfaces, JSX 标记 |
| HTML | `.html` | `HtmlExtractor` | tags, script blocks, forms |
| Java | `.java` | `JavaExtractor` | classes, methods, imports, main 检测 |
| JSON | `.json` | `JsonExtractor` | top_keys, is_package_json 判断 |
| YAML | `.yml`, `.yaml` | `YamlExtractor` | top_keys, K8s/Compose 判断 |
| Dockerfile | `Dockerfile` | `DockerfileExtractor` | FROM, EXPOSE, ENTRYPOINT/CMD |
| Makefile | `Makefile` | `MakefileExtractor` | targets, has_default_target |
| Markdown | `.md` | `MarkdownExtractor` | headings, code_blocks, install_steps 标记 |
| Jupyter Notebook | `.ipynb` | `NotebookExtractor` | code_cells/md_cells, imports |

**扩展方式：** 继承 `BaseExtractor`，实现 `extract()` 方法，在 `get_extractor()` 中注册。

---

## 使用方式

```bash
# 分析单个文件
python wtfe_file/wtfe_file.py example/example.py

# 批量测试
python scripts/test_examples.py
```

---

## 输出到上层

WTFE_file 的输出会被：
- **wtfe_folder** 聚合为模块职责
- **wtfe_run** 用于识别入口点与启动方式
- **wtfe_context** 用于判断项目成熟度
- 最终由 **wtfe_readme** 转换为自然语言文档

---

## 下一步

- [ ] 统一数据模型（`core/models/FileFact`）
- [ ] 增加置信度与证据字段
- [ ] 支持更多语言（Go, Rust, C/C++）
- [ ] 导出 `spec/file_types.yaml` 配置
