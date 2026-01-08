# WTFE — Why The Folder Exists

**Automatically analyze unfamiliar code projects and generate README documentation.**

Facing an unknown project and don't know what it does or how to run it? WTFE extracts project structure and capabilities through static analysis, then uses AI to generate human-friendly documentation.

## Quick Start

### Complete Workflow: Generate README

```bash
# Recommended: Use the unified entry point (Interactive API Key setup on first run)
python wtfe.py ./your-project

# Legacy method: Pipeline
# 1. Set Environment Variable
# export WTFE_API_KEY="sk-..."  # Linux/Mac
# $env:WTFE_API_KEY = "sk-..."  # Windows

# 2. Analyze and Generate
python wtfe-analyze/wtfe_analyze.py ./your-project | python wtfe-readme/wtfe_readme.py -
```

### Test Individual Modules

```bash
# Clone repository
git clone https://github.com/owenX-copilot/wtfe.git
cd wtfe

# Use unified entry point to run modules
python wtfe.py -m file example/app.py           # Single file analysis
python wtfe.py -m folder example/example_folder # Folder analysis
python wtfe.py -m run example/example_folder    # Entry point detection
python wtfe.py -m context example/example_folder # Context analysis
python wtfe.py -m analyze example/example_folder # Full analysis

# View Help
python wtfe.py --help
```

## Modules

| Module | Function | Status |
|--------|----------|--------|
| **wtfe-file** | Single file analysis, supports 11 file types (Python/JS/TS/Java, etc.) | ✅ |
| **wtfe-folder** | Recursive folder analysis, identifies core files and module responsibilities | ✅ |
| **wtfe-run** | Detects entry points (main/Makefile/Dockerfile/npm scripts) | ✅ |
| **wtfe-context** | Collects 40+ project signals (scale/maturity/tech stack) | ✅ |
| **wtfe-intent** | Extracts existing README/LICENSE/CHANGELOG (author intent) | ✅ |
| **wtfe-analyze** | Orchestrates all modules, outputs structured JSON | ✅ |
| **wtfe-readme** | AI-generated natural language README | ✅ |

## Configuration

### wtfe-readme Configuration (config.yaml)

```yaml
# API Provider (supports OpenAI-compatible format)
provider: openai
base_url: https://api.siliconflow.cn/v1  # SiliconFlow (recommended for China)
# base_url: https://api.openai.com/v1   # OpenAI official
# base_url: http://localhost:11434/v1   # Ollama local model

# API Key (read from environment variable)
api_key: ${WTFE_API_KEY}

# Model selection
model: deepseek-ai/DeepSeek-V3.2  # Default, cost-effective ($0.27/M tokens)
# model: gpt-4o-mini                # OpenAI
# model: llama3.1:8b                # Ollama local

# Generation parameters
max_tokens: 4096
temperature: 0.7
language: en  # zh-cn | en
```

### Supported AI Services

- **SiliconFlow (Recommended for CN)**: Domestic access, low cost, no VPN required
- **OpenAI Official**: GPT-4o / GPT-4o-mini / GPT-3.5-turbo
- **Local Models**: Ollama / vLLM / LM Studio

## How It Works

### Analysis Pipeline

```
┌─────────────┐
│ Source Code │
└──────┬──────┘
       │
       ├──→ wtfe-file    (file feature extraction)
       ├──→ wtfe-folder  (module structure analysis)
       ├──→ wtfe-run     (entry point detection)
       ├──→ wtfe-context (project signal collection)
       └──→ wtfe-intent  (existing docs extraction)
       │
       ↓
┌──────────────┐
│ wtfe-analyze │ Orchestrate, generate JSON
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ wtfe-readme  │ AI converts to natural language
└──────┬───────┘
       │
       ↓
  README.md
```

### Design Principles

1. **Rules First, AI Assists**: File analysis and structure extraction use rules; AI only handles final language generation
2. **Author Intent First**: If project has existing README, use it as highest-weight reference
3. **Zero-dependency Analysis**: Pure static analysis, no code execution
4. **Incremental & Cacheable**: Reuse analysis results for unchanged files

## Example Output

### Analysis Result (JSON)

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

### Generated README

Based on the above JSON, AI generates a README containing:
- Project introduction
- Features
- Tech stack
- Installation & running instructions
- Usage examples
- Testing instructions

## Project Structure

```
wtfe/
├── core/models.py           # Data structure definitions
├── wtfe-file/               # Single file analysis
├── wtfe-folder/             # Folder aggregation
├── wtfe-run/                # Entry point detection
├── wtfe-context/            # Context signals
├── wtfe-intent/             # Author intent extraction
├── wtfe-analyze/            # Orchestrator
├── wtfe-readme/             # AI generation layer
│   ├── providers/           # AI service abstraction
│   ├── templates/prompt.py  # Prompt templates
│   ├── config.yaml          # Configuration file
│   └── wtfe_readme.py       # Main program
└── example/                 # Test examples
```

## Use Cases

- Quickly understand open source projects
- Add documentation to legacy projects
- Analyze legacy codebases
- Evaluate project quality
- Assist code reviews

## Limitations

- Static analysis only, no code execution
- Does not understand business logic
- Generated README requires human review
- AI cost depends on project size (small projects < $0.01)

## License

MIT
