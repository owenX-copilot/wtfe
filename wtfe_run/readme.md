# WTFE-run — 管线 B：启动与运行分析

WTFE-run 负责回答 **"这个项目怎么跑起来"** 的问题。

## 核心职责

- 识别项目入口点（main.py, server.js, etc.）
- 提取启动命令（Makefile, package.json, Dockerfile）
- 推断运行时依赖（DB, Cache, Queue）

---

## 检测内容

### 1. 入口点识别（Entry Points）
- 常见入口文件：`main.py`, `app.py`, `server.js`, `index.js`, `main.go`, `Main.java`, `main.rs`
- Python `if __name__ == '__main__'` 自动检测
- 置信度评分（0.0-1.0）

### 2. 启动方式扫描
- **Makefile**: 提取所有 targets（build, run, test）
- **package.json**: 提取 scripts（start, dev, build）
- **Dockerfile**: 提取 CMD/ENTRYPOINT

### 3. 运行依赖推断
基于以下信号：
- 目录名（db/, migrations/, cache/）
- docker-compose.yml 内容（postgres, redis, rabbitmq）
- 配置文件（database.yml, redis.conf）

输出：
- `requires_db`
- `requires_cache`
- `requires_queue`

---

## 使用方式

```bash
# 分析当前项目
python wtfe_run/wtfe_run.py .

# 分析指定项目
python wtfe_run/wtfe_run.py /path/to/project
```

---

## 输出示例

```json
{
  "entry_points": [
    {
      "file": "main.py",
      "type": "main",
      "command": "python main.py",
      "confidence": 0.8
    }
  ],
  "makefile_targets": ["build", "run", "test"],
  "package_scripts": {"start": "node index.js"},
  "dockerfile_cmds": ["CMD [\"python\", \"app.py\"]"],
  "runtime_deps": {
    "requires_db": true,
    "requires_cache": false,
    "requires_queue": false
  }
}
```

---

## 下一步

- [ ] 解析 requirements.txt / Pipfile / pyproject.toml 获取依赖
- [ ] 识别环境变量需求（.env.example, config files）
- [ ] 支持多环境识别（dev/staging/prod）
- [ ] 与 wtfe_file 集成，从代码导入推断依赖
