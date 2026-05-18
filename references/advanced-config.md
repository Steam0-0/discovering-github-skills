# Advanced Configuration

## Contents
- Custom keyword sets
- Category customization
- GitHub search query syntax
- LLM-powered summary generation
- Pipeline integration

## Custom keyword sets

The default keywords are tuned for AI/ML skill discovery. Override with `--keywords`:

```bash
# Focus on infrastructure and serving tools
python scripts/discover_skills.py --keywords "inference,serving,deployment,kubernetes,docker,api,runtime"

# Focus on agent and automation tools
python scripts/discover_skills.py --keywords "agent,automation,workflow,copilot,assistant,orchestration"
```

### Keyword file

For large keyword sets, create a text file (one keyword per line) and pass via stdin:

```bash
# keywords.txt
cat keywords.txt | tr '\n' ',' | xargs -I {} python scripts/discover_skills.py --keywords "{}"
```

## Category customization

Categories are defined in `discover_skills.py` as `CATEGORY_KEYWORDS`. To customize:

1. Edit the `CATEGORY_KEYWORDS` dict in `scripts/discover_skills.py`
2. Add new categories or modify keyword mappings:

```python
CATEGORY_KEYWORDS = {
    "Inference & Serving": ["inference", "serving", "deploy", "api", "server", "runtime"],
    "Your Custom Category": ["keyword1", "keyword2", "keyword3"],
    # ...
}
```

## GitHub search query syntax

The `--query` flag supports full GitHub search syntax:

| Query | Result |
|-------|--------|
| `stars:>=1000 language:python` | Python repos with 1000+ stars |
| `topic:llm topic:inference` | Repos with both LLM and inference topics |
| `agent stars:>=5000 pushed:>2024-01-01` | Agent repos updated since 2024 |
| `fork:false stars:>=1000 topic:ai` | Non-fork AI repos |

Combine with `--min-stars` for additional filtering:

```bash
python scripts/discover_skills.py \
  --query "language:python topic:llm fork:false" \
  --min-stars 2000 \
  --pages 5
```

## LLM-powered summary generation

The base script generates summaries from repo metadata and README content using heuristic rules. For higher quality summaries, integrate an LLM:

### Using Claude API

```python
import anthropic

def llm_summarize(repo: dict, readme: str) -> dict:
    client = anthropic.Anthropic()
    prompt = f"""Analyze this GitHub project and generate a structured summary.

Project: {repo['full_name']}
Stars: {repo['stargazers_count']}
Description: {repo.get('description', '')}
README (first 3000 chars):
{readme[:3000]}

Output JSON with keys: summary (one sentence), features (3-6 items), use_cases (2-4 items), category (one of: {', '.join(CATEGORY_KEYWORDS.keys())}), tech_stack (list)"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(response.content[0].text)
```

### Integration point

Replace the `generate_summary()` call in the discover loop:

```python
# In cmd_discover, replace:
summary = generate_summary(repo, readme)
# With:
summary = llm_summarize(repo, readme)
```

## Pipeline integration

### GitHub Actions daily cron

```yaml
# .github/workflows/discover-skills.yml
name: Discover Skills
on:
  schedule:
    - cron: '0 2 * * *'  # 2am UTC daily
  workflow_dispatch:

jobs:
  discover:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests pyyaml
      - run: python scripts/discover_skills.py discover --min-stars 1000 --pages 5 --output catalog.json --cache .github_skills_cache.json
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      - uses: actions/upload-artifact@v4
        with:
          name: skills-catalog
          path: catalog.json
```

### Vector DB ingestion

Output JSON can be ingested into vector databases for semantic search:

```python
# Example: load into FAISS
from sentence_transformers import SentenceTransformer
import faiss, json

skills = json.load(open("skills_catalog.json"))
model = SentenceTransformer("all-MiniLM-L6-v2")
texts = [f"{s['name']}: {s['summary']} {' '.join(s['features'])}" for s in skills]
embeddings = model.encode(texts)
index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)
```
