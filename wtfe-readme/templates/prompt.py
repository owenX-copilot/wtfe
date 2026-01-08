"""
Prompt templates for README generation.
"""
import json
from typing import Dict, Any


def build_readme_prompt(analysis_result: Dict[str, Any], config: Dict[str, Any]) -> str:
    """
    构建README生成的Prompt
    
    Args:
        analysis_result: wtfe-analyze输出的完整JSON
        config: 配置字典（从config.yaml读取）
    
    Returns:
        完整的Prompt字符串
    """
    language = config.get('language', 'zh-cn')
    style = config.get('style', 'technical')
    include_badges = config.get('include_badges', True)
    include_toc = config.get('include_toc', True)
    include_architecture = config.get('include_architecture', True)
    
    # 提取关键信息
    project_name = analysis_result.get('metadata', {}).get('project_name', 'Unknown Project')
    folder_analysis = analysis_result.get('folder_analysis', {})
    entry_points = analysis_result.get('entry_points', {})
    context = analysis_result.get('context_signals', {})
    author_intent = analysis_result.get('author_intent', {})
    summary = analysis_result.get('summary', {})
    
    # 构建Prompt
    prompt_parts = []
    
    # 基础指令
    if language == 'zh-cn':
        prompt_parts.append(f"""# 任务：生成项目README文档

你是一个专业的技术文档撰写专家。基于以下项目分析数据，生成一份清晰、专业的README.md文档。

## 项目名称
{project_name}

## 生成要求

### 文档风格
- 语言：简体中文
- 风格：{'技术专业' if style == 'technical' else '通俗易懂' if style == 'casual' else '正式规范'}
- 包含目录：{'是' if include_toc else '否'}
- 包含徽章：{'是（技术栈、License等）' if include_badges else '否'}
- 包含架构说明：{'是' if include_architecture else '否'}

### 内容结构（必须按此顺序）
1. **项目标题和徽章**（如果enable_badges=true）
2. **简介**（1-2段，说明项目是什么、解决什么问题）
3. **目录**（如果include_toc=true）
4. **功能特性**（列出主要功能点）
5. **技术栈**（从分析数据中提取）
6. **项目结构**（展示核心文件/目录）
7. **快速开始**
   - 环境要求
   - 安装步骤
   - 运行方法（基于检测到的入口点）
   - 使用示例
8. **配置说明**（如果有配置文件）
9. **测试**（如果has_tests=true）
10. **架构说明**（如果include_architecture=true且项目足够复杂）
11. **贡献指南**（如果有CONTRIBUTING）
12. **许可证**（如果有LICENSE）
13. **联系方式/致谢**（可选）

### 关键规则
- **优先采信作者意图**：如果author_intent中有project_readme，其内容具有最高权重，应融合其描述
- **基于事实**：所有内容必须基于分析数据，不要编造功能
- **简洁明确**：避免冗长描述，每个部分直奔主题
- **可操作**：安装和运行步骤必须具体可执行
- **Markdown格式**：使用规范的Markdown语法

---
""")
    else:  # English
        prompt_parts.append(f"""# Task: Generate Project README

You are an expert technical writer. Based on the following project analysis data, generate a clear, professional README.md document.

## Project Name
{project_name}

## Generation Requirements

### Document Style
- Language: English
- Style: {'Technical' if style == 'technical' else 'Casual' if style == 'casual' else 'Formal'}
- Include ToC: {'Yes' if include_toc else 'No'}
- Include Badges: {'Yes (tech stack, license, etc.)' if include_badges else 'No'}
- Include Architecture: {'Yes' if include_architecture else 'No'}

### Content Structure (Must follow this order)
1. **Title and Badges** (if enabled)
2. **Introduction** (1-2 paragraphs explaining what this project does)
3. **Table of Contents** (if enabled)
4. **Features** (list main capabilities)
5. **Tech Stack** (extract from analysis data)
6. **Project Structure** (show core files/directories)
7. **Getting Started**
   - Prerequisites
   - Installation
   - Running (based on detected entry points)
   - Usage Examples
8. **Configuration** (if config files exist)
9. **Testing** (if has_tests=true)
10. **Architecture** (if enabled and project is complex enough)
11. **Contributing** (if CONTRIBUTING exists)
12. **License** (if LICENSE exists)
13. **Contact/Acknowledgments** (optional)

### Key Rules
- **Prioritize Author Intent**: If project_readme exists in author_intent, it has the highest weight
- **Fact-Based**: All content must be based on analysis data, don't fabricate features
- **Concise**: Avoid verbosity, get to the point in each section
- **Actionable**: Installation and running steps must be concrete and executable
- **Markdown Format**: Use proper Markdown syntax

---
""")
    
    # 添加作者意图（高权重）
    if author_intent.get('project_readme'):
        prompt_parts.append(f"""## 作者意图（最高权重参考）

项目已有README内容如下，请融合其描述和结构：

```markdown
{author_intent['project_readme'][:2000]}  # 截取前2000字符避免过长
```

**重要**：如果现有README的描述与推断结果冲突，优先采信现有README。
""")
    
    # 添加项目摘要
    prompt_parts.append(f"""## 项目摘要

{json.dumps(summary, indent=2, ensure_ascii=False)}

**解读**：
- 主要角色：{summary.get('primary_role', 'unknown')}
- 是否可运行：{'是' if summary.get('can_run') else '否'}
- 是否有文档：{'是' if summary.get('has_documentation') else '否'}
- 是否有测试：{'是' if summary.get('has_tests') else '否'}
- 文件数量：{summary.get('file_count', 0)}
- 外部依赖数：{summary.get('external_deps_count', 0)}
""")
    
    # 添加文件夹分析
    prompt_parts.append(f"""## 文件夹分析（能力和职责）

{json.dumps(folder_analysis, indent=2, ensure_ascii=False)}

**核心文件**：
{', '.join(folder_analysis.get('core_files', []))}

**能力列表**：
{', '.join(folder_analysis.get('capabilities', []))}

**外部依赖（Top 10）**：
{', '.join(list(folder_analysis.get('external_deps', []))[:10])}
""")
    
    # 添加入口点信息
    if entry_points.get('entry_points'):
        prompt_parts.append(f"""## 运行入口点

{json.dumps(entry_points, indent=2, ensure_ascii=False)}

**如何运行**：基于检测到的入口点，生成明确的运行命令。
""")
    
    # 添加上下文信号
    scale = context.get('scale', {})
    maturity = context.get('maturity', {})
    signals = context.get('signals', {})
    
    prompt_parts.append(f"""## 项目上下文

### 规模
- 文件数：{scale.get('file_count', 0)}
- 代码行数：{scale.get('line_count', 0)}
- 语言分布：{', '.join(scale.get('languages', []))}

### 成熟度
- 有测试：{'是' if maturity.get('has_tests') else '否'}
- 有CI/CD：{'是' if maturity.get('has_ci') else '否'}
- 有类型标注：{'是' if maturity.get('has_typing') else '否'}

### 关键信号（从40+信号中提取的重要信息）
{json.dumps({k: v for k, v in signals.items() if v is True and k.startswith('has_')}, indent=2, ensure_ascii=False)}
""")
    
    # 添加其他文档
    if author_intent.get('changelog'):
        prompt_parts.append(f"""## 变更日志存在
项目有CHANGELOG文件，在README中提及：详见 CHANGELOG.md
""")
    
    if author_intent.get('license_text'):
        license_content = author_intent['license_text'][:200]
        prompt_parts.append(f"""## 许可证存在
{license_content}...
在README中添加License说明。
""")
    
    # 最终指令
    if language == 'zh-cn':
        prompt_parts.append("""
---

## 生成指令

现在，基于以上所有信息，生成一份完整的README.md。

**输出格式**：
- 直接输出Markdown内容，不要包含任何解释或额外文本
- 不要使用代码块包裹（即不要```markdown...```）
- 确保所有内容基于实际分析数据
- 融合作者意图中的描述
- 使用清晰的Markdown格式

开始生成：
""")
    else:
        prompt_parts.append("""
---

## Generation Instruction

Now, based on all the information above, generate a complete README.md.

**Output Format**:
- Output Markdown content directly, no explanation or extra text
- Do NOT wrap in code blocks (no ```markdown...```)
- Ensure all content is based on actual analysis data
- Integrate author intent descriptions
- Use clear Markdown formatting

Generate now:
""")
    
    return '\n'.join(prompt_parts)


def build_minimal_prompt(project_name: str, primary_role: str, files: list) -> str:
    """
    构建最小化Prompt（当分析数据不完整时的fallback）
    
    Args:
        project_name: 项目名称
        primary_role: 主要角色
        files: 文件列表
    
    Returns:
        简化的Prompt
    """
    return f"""Generate a basic README.md for a project named "{project_name}".

Project Type: {primary_role}
Files: {', '.join(files[:10])}

Include:
1. Project title
2. Brief description
3. File structure
4. Basic usage

Output in Markdown format only, no extra text.
"""
