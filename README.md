<p align="center">
  <h1 align="center">🔍 Discovering GitHub Skills</h1>
  <p align="center">
    <em>自动发现 GitHub 上 1000+ Stars 的 AI Skill / Agent / Tool，生成结构化摘要</em>
  </p>
  <p align="center">
    <a href="#quick-start">快速开始</a> · <a href="#features">功能特性</a> · <a href="#architecture">实现架构</a> · <a href="#usage">使用指南</a> · <a href="#api-reference">API 参考</a>
  </p>
</p>

---

## 背景

AI 开源生态爆发式增长，GitHub 上每天都有新的 Agent、Tool、Framework 涌现。但发现和筛选高质量项目仍然依赖人工——在 Trending 页面翻页、在各种 Awesome 列表间跳转。

**Discovering GitHub Skills** 旨在自动化这一过程：通过 GitHub Search API 系统性地检索高星项目，用关键词引擎判断其是否属于 AI Skill/Agent/Tool，并自动生成包含一句话摘要、功能列表、适用场景、技术栈的结构化摘要。

## 功能特性

- **自动化检索** — 基于 GitHub Search API，按 star 数、关键词批量拉取仓库
- **智能过滤** — 20+ 关键词匹配引擎，自动排除 fork，精准识别 AI skill/agent/tool
- **结构化摘要** — 自动从 README 和仓库元数据中提取 features、use cases、category、tech stack
- **9 大分类** — Agents & Orchestration、Inference & Serving、Training & Fine-tuning、RAG & Search 等
- **增量更新** — 内置缓存机制，仅处理新增或更新的仓库，避免重复拉取
- **多种输出格式** — JSON 目录、Markdown 表格、按分类过滤查看
- **目录合并** — 支持多次搜索结果去重合并
- **LLM 增强就绪** — 预留 Claude API 集成点，可一键升级为高质量 LLM 摘要

## 实现架构

```
┌─────────────────────────────────────────────────────────┐
│                    Discover Pipeline                     │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌───────────────────┐  │
│  │  Fetch   │───▶│  Filter  │───▶│   Summarize       │  │
│  │          │    │          │    │                   │  │
│  │ GitHub   │    │ Keywords │    │ README Extraction │  │
│  │ Search   │    │ Fork     │    │ Feature Parsing   │  │
│  │ API      │    │ Star     │    │ Categorization    │  │
│  │ (paged)  │    │ Match    │    │ Tech Stack Guess  │  │
│  └──────────┘    └──────────┘    └───────────────────┘  │
│       │               │                   │              │
│       ▼               ▼                   ▼              │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Cache (JSON, incremental)            │   │
│  └──────────────────────────────────────────────────┘   │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐           │
│  │  JSON    │    │ Markdown │    │  Merge   │           │
│  │  Catalog │    │  Table   │    │  & Dedup │           │
│  └──────────┘    └──────────┘    └──────────┘           │
└─────────────────────────────────────────────────────────┘
```

### 三阶段 Pipeline 详解

**Stage 1: Fetch（采集层）**
- 调用 GitHub Search API，分页拉取仓库数据
- 支持 `--query` 自定义搜索语法（language、topic、pushed 等筛选）
- 内置请求限速（2s/page），避免触发 API rate limit

**Stage 2: Filter（过滤层）**
- 20+ 关键词匹配（agent、llm、inference、rag、training 等）
- 自动排除 fork 仓库
- Star 数阈值过滤（默认 ≥ 1000，可配置）

**Stage 3: Summarize（摘要层）**
- 拉取 README（自动尝试 main/master 分支）
- 提取 bullet-point features（从 README 列表项）
- 基于 9 大分类关键词匹配自动分类
- 从 README import 语句和 topics 推断技术栈
- 从描述和 topics 推断适用场景

## 项目结构

```
discovering-github-skills/
├── SKILL.md                        # Skill 主文件：frontmatter + 工作流 + 使用指南
├── README.md                       # 本文件
├── skills_catalog.json             # 示例输出：300 个已发现的 skill（按 star 降序）
├── .github_skills_cache.json       # 增量缓存（自动生成）
├── scripts/
│   └── discover_skills.py          # 核心脚本：5 个子命令
└── references/
    ├── advanced-config.md           # 进阶配置：关键词定制、LLM 集成、CI/CD、向量库
    └── troubleshooting.md           # 常见问题：限流、认证、空结果、编码等
```

### 核心脚本模块

| 模块 | 函数 | 职责 |
|------|------|------|
| GitHub API | `fetch_repos()` | 分页搜索仓库 |
| GitHub API | `get_readme()` | 拉取 README（main/master 分支） |
| 过滤 | `is_skill_repo()` | 关键词 + fork 过滤 |
| 摘要 | `generate_summary()` | 生成结构化摘要 |
| 摘要 | `_extract_features()` | 从 README 提取功能列表 |
| 摘要 | `_categorize()` | 9 大分类自动归类 |
| 摘要 | `_guess_tech_stack()` | 从 README/topics 推断技术栈 |
| 缓存 | `load_cache()` / `save_cache()` | JSON 缓存读写 |

## 快速开始

### 环境要求

- Python 3.10+
- `requests` 库（`pip install requests`）
- GitHub Personal Access Token（免费，无需特殊权限）

### 安装

```bash
git clone <this-repo>
cd discovering-github-skills
pip install requests
```

### 设置 GitHub Token

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

> 在 [GitHub Settings → Tokens](https://github.com/settings/tokens) 创建，无需勾选任何 scope。

### 运行

```bash
# 默认：拉取 star≥1000 的仓库，3 页（约 300 个），输出 JSON
python scripts/discover_skills.py discover \
  --min-stars 1000 \
  --pages 3 \
  --output skills_catalog.json
```

## 使用指南

### 子命令总览

```
discover    核心流程：抓取 → 过滤 → 摘要 → 输出
summary     查看已有目录的分类概览
filter      按分类或关键词过滤
export-md   导出 Markdown 表格
merge       合并两个目录（自动去重）
```

### 1. discover — 全量发现

```bash
# 基本用法
python scripts/discover_skills.py discover \
  --min-stars 1000 \
  --pages 5 \
  --output skills_catalog.json

# 自定义关键词
python scripts/discover_skills.py discover \
  --min-stars 2000 \
  --keywords "agent,llm,inference,training,rag" \
  --pages 3

# 自定义 GitHub 搜索查询
python scripts/discover_skills.py discover \
  --query "language:python topic:llm fork:false" \
  --min-stars 500 \
  --pages 5

# 强制刷新（忽略缓存）
python scripts/discover_skills.py discover \
  --force-refresh \
  --pages 3
```

### 2. summary — 查看概览

```bash
python scripts/discover_skills.py summary skills_catalog.json
```

输出示例：
```
Total skills: 300

## Agents & Orchestration (113)
  - openclaw (372703 stars): Your own personal AI assistant...
  - AutoGPT (184379 stars): AutoGPT is the vision of accessible AI...
  ... and 108 more

## Inference & Serving (99)
  - n8n (188398 stars): Fair-code workflow automation...
  ...
```

### 3. filter — 过滤查看

```bash
# 按分类
python scripts/discover_skills.py filter skills_catalog.json --category "Training"

# 按关键词
python scripts/discover_skills.py filter skills_catalog.json --keyword "pytorch"
```

### 4. export-md — 导出 Markdown

```bash
python scripts/discover_skills.py export-md skills_catalog.json --output SKILLS_TABLE.md
```

输出表格示例：

| Name | Stars | Category | Summary | Tech Stack |
|------|-------|----------|---------|------------|
| [openclaw](https://github.com/openclaw/openclaw) | 372,703 | Agents & Orchestration | Your own personal AI assistant... | python, docker |
| [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | 184,379 | Inference & Serving | AutoGPT is the vision of accessible AI... | python, docker |

### 5. merge — 合并目录

```bash
# 两次搜索结果合并
python scripts/discover_skills.py discover --query "topic:llm" --pages 2 --output llm_skills.json
python scripts/discover_skills.py discover --query "topic:agent" --pages 2 --output agent_skills.json

# 合并去重
python scripts/discover_skills.py merge llm_skills.json agent_skills.json --output merged.json
```

## 输出格式

每个 skill 的 JSON 结构：

```json
{
  "name": "AutoGPT",
  "full_name": "Significant-Gravitas/AutoGPT",
  "url": "https://github.com/Significant-Gravitas/AutoGPT",
  "stars": 184379,
  "description": "AutoGPT is the vision of accessible AI for everyone...",
  "summary": "AutoGPT is the vision of accessible AI for everyone, to use and to build on",
  "features": [
    "AI-powered automation",
    "Plugin ecosystem",
    "Multi-agent orchestration"
  ],
  "use_cases": [
    "Autonomous AI agent workflows",
    "Production model inference and serving"
  ],
  "category": "Agents & Orchestration",
  "is_ai_skill": true,
  "tech_stack": ["python", "docker"],
  "topics": ["ai", "agent", "automation"],
  "language": "Python",
  "license": "MIT",
  "updated_at": "2025-05-18T12:00:00Z"
}
```

## 9 大分类

| 分类 | 关键词匹配 | 示例项目 |
|------|-----------|----------|
| **Agents & Orchestration** | agent, orchestr, workflow, copilot, assistant | AutoGPT, OpenHands, CrewAI |
| **Inference & Serving** | inference, serving, deploy, api, runtime | vLLM, n8n, LiteLLM |
| **Training & Fine-tuning** | training, fine-tun, rlhf, lora, peft | LlamaFactory, Unsloth |
| **RAG & Search** | rag, retrieval, vector, embedding, index | RAGFlow, Anything-LLM |
| **Data & Processing** | data, dataset, pipeline, etl | ClickHouse, Docling |
| **Evaluation & Safety** | eval, benchmark, safety, alignment | — |
| **Infrastructure & MLOps** | mlops, monitor, tracking | Uptime Kuma, Sniffnet |
| **Multimodal & Vision** | multimodal, vision, diffusion, audio | Stable Diffusion, ComfyUI |
| **Optimization & Quantization** | quantiz, prun, distill, compress | — |

## 增量更新与缓存

脚本自动维护 `.github_skills_cache.json` 缓存文件：

- **首次运行**：全量拉取，缓存所有结果
- **后续运行**：对比 `updated_at`，仅处理有变更的仓库
- **强制刷新**：`--force-refresh` 忽略缓存，重新拉取 README 并生成摘要

```bash
# 日常增量更新
python scripts/discover_skills.py discover --pages 3 --output catalog_v2.json

# 强制全量刷新
python scripts/discover_skills.py discover --force-refresh --pages 3 --output catalog_v2.json
```

## 进阶用法

### LLM 增强摘要

默认使用启发式规则生成摘要。可在 `discover_skills.py` 中集成 Claude API 获得更高质量的摘要：

```python
# 替换 generate_summary() 调用为 llm_summarize()
import anthropic

def llm_summarize(repo, readme):
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": f"Analyze this GitHub project: {repo['full_name']}..."}],
    )
    return json.loads(response.content[0].text)
```

详见 [references/advanced-config.md](references/advanced-config.md)。

### GitHub Actions 定时任务

```yaml
# 每天凌晨 2 点自动运行
on:
  schedule:
    - cron: '0 2 * * *'
jobs:
  discover:
    runs-on: ubuntu-latest
    steps:
      - run: pip install requests
      - run: python scripts/discover_skills.py discover --min-stars 1000 --pages 5 --output catalog.json
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 向量库集成

输出 JSON 可直接导入 FAISS / Milvus / Qdrant 等向量数据库，实现语义搜索：

```python
from sentence_transformers import SentenceTransformer
import faiss, json

skills = json.load(open("skills_catalog.json"))
model = SentenceTransformer("all-MiniLM-L6-v2")
texts = [f"{s['name']}: {s['summary']} {' '.join(s['features'])}" for s in skills]
embeddings = model.encode(texts)
index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)
```

## 常见问题

<details>
<summary><b>403 API rate limit exceeded</b></summary>

GitHub Search API 限制：认证用户 30 次/分钟，未认证 10 次/分钟。设置 `GITHUB_TOKEN` 即可解决：

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

脚本内置 2 秒/页的限速，通常不会触发限制。
</details>

<details>
<summary><b>结果太少或为空</b></summary>

可能原因及修复：
- 关键词太严格 → 放宽 `--keywords` 或降低 `--min-stars`
- GitHub API 单次搜索最多返回 1000 条 → 用 `--query` 做分类搜索后 merge
- 默认排除 fork → 加 `--include-forks` 查看
</details>

<details>
<summary><b>某些仓库摘要为空</b></summary>

仓库可能使用非 main/master 分支或没有 README.md。脚本会自动 fallback 到仓库 description 字段。
</details>

<details>
<summary><b>缓存数据过期</b></summary>

```bash
# 删除缓存重新拉取
rm .github_skills_cache.json

# 或强制刷新
python scripts/discover_skills.py discover --force-refresh --pages 3
```
</details>

更多问题详见 [references/troubleshooting.md](references/troubleshooting.md)。

## 技术栈

- **语言**：Python 3.10+
- **依赖**：requests（HTTP）、PyYAML（可选）
- **数据源**：GitHub Search REST API v3
- **缓存**：JSON 文件（本地）
- **输出**：JSON / Markdown

## License

MIT
