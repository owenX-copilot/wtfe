# wtfe-readme

**AI生成层 - 将项目分析转换为自然语言README**

## 功能

wtfe-readme 是WTFE框架的**最终输出层**，负责将wtfe-analyze的结构化JSON数据转换为人类友好的README.md文档。

它通过AI模型理解项目特征，生成：
- 项目简介和功能特性
- 安装和使用说明
- 技术栈和架构说明
- 贡献指南和许可证信息

## 使用方法

### 方式1：从JSON文件生成

```bash
# 1. 先运行分析
python wtfe-analyze/wtfe_analyze.py ./example/example_folder > analysis.json

# 2. 基于分析结果生成README
python wtfe-readme/wtfe_readme.py analysis.json
```

### 方式2：管道模式

```bash
python wtfe-analyze/wtfe_analyze.py ./example/example_folder | python wtfe-readme/wtfe_readme.py -
```

### 方式3：输出到stdout

```bash
python wtfe-readme/wtfe_readme.py analysis.json --stdout > README_new.md
```

## 配置说明

### 环境变量设置（推荐）

```bash
# Windows PowerShell
$env:WTFE_API_KEY = "sk-your-api-key-here"

# Windows CMD
set WTFE_API_KEY=sk-your-api-key-here

# Linux/Mac
export WTFE_API_KEY=sk-your-api-key-here
```

### config.yaml 配置

```yaml
# API配置
provider: openai
base_url: https://api.siliconflow.cn/v1  # 硅基流动（默认）
api_key: ${WTFE_API_KEY}                 # 从环境变量读取
model: deepseek-ai/DeepSeek-V3.2         # 推荐模型

# 生成参数
max_tokens: 4096
temperature: 0.7
top_p: 0.9

# 输出配置
output_file: README.md
overwrite: false       # false会生成README_generated.md
backup_existing: true  # 覆盖前备份为README.md.bak

# Prompt配置
language: zh-cn        # zh-cn | en
style: technical       # technical | casual | formal
include_badges: true
include_toc: true
include_architecture: true
```

### 支持的AI服务

#### 硅基流动（SiliconFlow）- 推荐

**为什么推荐**：
- ✅ 极低价格（DeepSeek-V3.2: ¥1/百万tokens输入）
- ✅ 无需科学上网
- ✅ 支持国内支付
- ✅ API稳定快速

**配置**：
```yaml
base_url: https://api.siliconflow.cn/v1
model: deepseek-ai/DeepSeek-V3.2
```

**可选模型**：
- `deepseek-ai/DeepSeek-V3.2` - 性价比最高
- `deepseek-ai/DeepSeek-V3.2-Exp` - 实验版，更新更快
- `Qwen/Qwen2.5-72B-Instruct` - 阿里通义千问
- `Pro/deepseek-ai/DeepSeek-V3.2-Exp` - Pro版本

#### OpenAI官方

```yaml
base_url: https://api.openai.com/v1
model: gpt-4o-mini  # 或 gpt-4o, gpt-3.5-turbo
```

#### 本地模型（Ollama）

```yaml
base_url: http://localhost:11434/v1
model: llama3.1:8b
api_key: dummy  # 本地不需要但保持接口一致
```

**注意**：需先启动Ollama服务：
```bash
ollama serve
ollama pull llama3.1:8b
```

#### vLLM本地推理

```yaml
base_url: http://localhost:8000/v1
model: meta-llama/Llama-3.1-8B-Instruct
api_key: dummy
```

## Prompt设计

### 核心原则

1. **作者意图优先**
   - 如果项目已有README，其内容具有最高权重
   - AI应融合现有描述，而非完全重写

2. **基于事实**
   - 所有内容必须基于wtfe-analyze的数据
   - 不编造功能或夸大能力

3. **结构化输出**
   - 按固定章节顺序生成
   - 确保可操作性（如安装步骤必须具体）

### Prompt结构

```
1. 任务说明 + 生成要求
2. 作者意图（如有README，高权重）
3. 项目摘要（summary）
4. 文件夹分析（能力、核心文件、依赖）
5. 入口点信息（如何运行）
6. 上下文信号（规模、成熟度）
7. 其他文档（LICENSE, CHANGELOG）
8. 最终生成指令
```

详见 [templates/prompt.py](templates/prompt.py)

## 输出示例

**输入**：example_folder的分析JSON（Flask Blog API）

**输出**：完整的README.md，包含：
- 项目标题和简介
- 功能特性列表
- 技术栈（Flask, SQLAlchemy等）
- 项目结构
- 安装步骤
- 运行方法（`python main.py`）
- API使用示例
- 测试说明
- 许可证信息

## 设计架构

### Provider抽象

```python
class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass
```

当前实现：
- `OpenAIProvider`: 支持所有OpenAI兼容API

未来可扩展：
- `AnthropicProvider`: Claude专用格式
- `LocalProvider`: 本地模型优化

### 错误处理

- **API失败自动重试**：默认3次，指数退避（1s, 2s, 4s）
- **超时保护**：默认60秒
- **友好错误提示**：区分网络错误、API错误、配置错误

### 配置灵活性

- 环境变量支持（安全）
- YAML配置文件（方便）
- 命令行覆盖（灵活）

## 性能和成本

### 典型项目成本估算

| 项目规模 | Input Tokens | Output Tokens | DeepSeek-V3.2成本 | GPT-4o成本 |
|---------|-------------|--------------|------------------|-----------|
| 小型 (10文件) | ~3,000 | ~1,500 | ¥0.002 | $0.02 |
| 中型 (50文件) | ~8,000 | ~2,500 | ¥0.005 | $0.05 |
| 大型 (200文件) | ~20,000 | ~4,000 | ¥0.01 | $0.10 |

**结论**：使用硅基流动+DeepSeek模型，每次生成成本**不到1分钱**。

### 生成时间

- 小型项目：5-10秒
- 中型项目：10-20秒
- 大型项目：20-40秒

（取决于网络和模型响应速度）

## 限制和注意事项

### 当前限制

1. **不支持流式输出**：目前一次性返回完整内容
2. **单次生成**：不支持多轮交互优化
3. **无缓存**：每次都重新生成（config中cache_enabled暂未实现）

### 使用建议

1. **API Key安全**：
   - 不要把key硬编码在config.yaml
   - 使用环境变量：`export WTFE_API_KEY=xxx`
   - 或使用`.env`文件（不要提交到Git）

2. **生成后人工审查**：
   - AI生成的内容可能需要微调
   - 检查技术细节准确性
   - 补充特定于项目的说明

3. **迭代优化**：
   - 首次生成后，可将AI输出作为project_readme
   - 再次运行wtfe-analyze+wtfe-readme
   - AI会基于上次内容改进

## 与其他模块的关系

```
wtfe-analyze (统一编排器)
    ↓ 输出JSON
wtfe-readme (本模块)
    ↓ 调用AI
OpenAI兼容API (硅基流动/OpenAI/本地模型)
    ↓ 返回Markdown
README.md (最终输出)
```

wtfe-readme是WTFE框架的最后一环，将机器理解转换为人类阅读。

## 故障排查

### 错误：Environment variable WTFE_API_KEY not set

**解决**：
```bash
export WTFE_API_KEY=your-api-key-here
```

### 错误：API Error (HTTP 401): Unauthorized

**原因**：API Key无效或过期

**解决**：检查config.yaml中的api_key或环境变量

### 错误：Connection error

**原因**：网络问题或base_url配置错误

**解决**：
1. 检查网络连接
2. 确认base_url正确（如`https://api.siliconflow.cn/v1`）
3. 如果用本地模型，确认服务已启动

### 错误：Request timeout

**原因**：模型响应慢或网络不稳定

**解决**：增加timeout配置（默认60秒）：
```yaml
timeout: 120  # 增加到120秒
```

## 未来计划

### Phase 2
- [ ] 流式输出（实时显示生成进度）
- [ ] 多轮优化（用户反馈后迭代）
- [ ] 缓存机制（相同项目避免重复调用）

### Phase 3
- [ ] 支持function calling（结构化输出）
- [ ] 多语言同时生成（README.md + README_en.md）
- [ ] 自定义模板（用户定制Prompt）

### Phase 4
- [ ] Web UI（图形化配置和生成）
- [ ] 批量生成（monorepo多项目）
- [ ] 质量评分（评估生成的README质量）

## 贡献

欢迎提交Issue和PR改进：
- Prompt优化建议
- 新Provider实现
- 错误处理改进
- 文档补充

## 许可证

与WTFE主项目相同。
