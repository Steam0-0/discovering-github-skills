---
name: discovering-github-skills
description: Discovers GitHub repositories with 1000+ stars that qualify as AI skills, agents, or tools, and generates structured summaries. Use when building a skill directory, curating open-source AI tools, or generating a catalog of high-star GitHub projects.
version: 1.0.0
author: Orchestra Research
license: MIT
tags: [GitHub, Skill Discovery, AI Tools, Agent Catalog, Open Source, Data Pipeline]
dependencies: [requests>=2.28.0, PyYAML>=6.0]
---

# Discovering GitHub Skills

Discovers high-star GitHub repositories that are AI skills/agents/tools and generates structured summaries with one-sentence descriptions, feature lists, use cases, and tech stack. Automatically produces three **Top 20 rankings** — by total stars, by 3-month star growth, and by 1-month star growth — in a `rankings/` directory with JSON and Markdown output.

## Quick start

**Basic usage**:
```bash
# Set your GitHub token (required to avoid rate limits)
export GITHUB_TOKEN="your_token_here"

# Run discovery pipeline — fetches repos, filters skills, generates summaries + rankings
python scripts/discover_skills.py discover --min-stars 1000 --pages 3 --output skills_catalog.json
```

This produces:
- `skills_catalog.json` — full catalog with growth data
- `rankings/by_total_stars.json` — Top 20 by total star count
- `rankings/by_growth_3m.json` — Top 20 by 3-month star growth
- `rankings/by_growth_1m.json` — Top 20 by 1-month star growth
- `rankings/README.md` — human-readable Markdown summary of all three rankings

## Common workflows

### Workflow 1: Full discovery pipeline

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Set up GitHub token
- [ ] Step 2: Run discovery script
- [ ] Step 3: Review and filter results
- [ ] Step 4: Generate final catalog
```

**Step 1: Set up GitHub token**

Create a GitHub personal access token at https://github.com/settings/tokens (no scopes needed for public repos).

```bash
export GITHUB_TOKEN="your_token_here"
```

**Step 2: Run discovery script**

```bash
# Fetch top 300 repos (3 pages x 100), filter for AI skills, output JSON + rankings
python scripts/discover_skills.py discover \
  --min-stars 1000 \
  --pages 3 \
  --output skills_catalog.json \
  --keywords "agent,ai,skill,tool,automation,assistant,llm,mlops,inference,training"
```

**Step 3: Review rankings**

```bash
# View the Markdown rankings summary
cat rankings/README.md

# Or regenerate rankings from an existing catalog (without re-fetching)
python scripts/discover_skills.py rankings skills_catalog.json --top-n 100
```

**Step 4: Generate final catalog**

```bash
# Export as Markdown table for documentation
python scripts/discover_skills.py export-md skills_catalog.json --output SKILLS_TABLE.md
```

### Workflow 2: Targeted search by topic

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Define search query
- [ ] Step 2: Run targeted search
- [ ] Step 3: Merge with existing catalog
```

**Step 1: Define search query**

Use GitHub search syntax to narrow results:
```bash
# Example: find RL training frameworks specifically
QUERY="reinforcement learning training framework stars:>=1000"
```

**Step 2: Run targeted search**

```bash
python scripts/discover_skills.py \
  --query "reinforcement learning training framework" \
  --min-stars 1000 \
  --pages 2 \
  --output rl_skills.json
```

**Step 3: Merge with existing catalog**

```bash
python scripts/discover_skills.py --merge skills_catalog.json rl_skills.json --output merged_catalog.json
```

### Workflow 3: Incremental update with cache

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Load cached results
- [ ] Step 2: Fetch only new/updated repos
- [ ] Step 3: Re-generate summaries for changed repos
```

**Step 1: Load cached results**

The script auto-loads `.github_skills_cache.json` if present:
```bash
# Previous run creates cache automatically
ls .github_skills_cache.json
```

**Step 2: Fetch only new/updated repos**

```bash
python scripts/discover_skills.py \
  --min-stars 1000 \
  --pages 2 \
  --cache .github_skills_cache.json \
  --output skills_catalog_v2.json
```

**Step 3: Re-generate summaries for changed repos**

```bash
# --force-refresh ignores cache and re-fetches README + regenerates summaries
python scripts/discover_skills.py \
  --min-stars 1000 \
  --pages 2 \
  --force-refresh \
  --output skills_catalog_v2.json
```

## When to use vs alternatives

**Use this when:**
- Building a curated directory of AI/ML tools from GitHub
- Generating structured summaries for a skill marketplace or catalog
- Discovering trending open-source AI projects by star growth
- Creating input data for a vector DB or semantic search system
- Comparing AI projects by momentum (recent star growth) vs total popularity

**Use GitHub trending page instead when:**
- You just want a quick glance at what's popular today
- You don't need structured output or filtering

**Use `gh search repos` CLI instead when:**
- You need a one-off ad-hoc search without summaries
- You don't need the "is this a skill" filtering or LLM summarization

## Common issues

**Issue: `403 API rate limit exceeded`**

GitHub API allows 5000 requests/hour with a token, 10/hour without. Fix by setting `GITHUB_TOKEN`:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

**Issue: Too many non-skill repos in results**

Tighten keyword filtering or increase `--min-stars`:
```bash
# More strict: require 5000+ stars and specific keywords
python scripts/discover_skills.py --min-stars 5000 --keywords "agent,llm,inference,training,mlops"
```

**Issue: `README not found` for some repos**

Some repos use `master` instead of `main`, or have no README. The script tries both branches and falls back to the repo `description` field.

**Issue: Duplicate entries from forks**

The script excludes forks by default (`--exclude-forks`, on by default). To include them:
```bash
python scripts/discover_skills.py --include-forks
```

## Star growth rankings

The `discover` command and `rankings` subcommand automatically generate three Top-20 rankings in a `rankings/` directory:

| File | Sorting | Description |
|------|---------|-------------|
| `by_total_stars.json` | Total star count | All-time most popular projects |
| `by_growth_3m.json` | Stars gained in last 90 days | Projects with the most momentum over a quarter |
| `by_growth_1m.json` | Stars gained in last 30 days | Currently trending projects |

Growth is computed by binary-searching the GitHub stargazers API (with timestamps) to count how many stars were gained after each cutoff date. This requires ~9 API calls per repo per cutoff date (log₂ of accessible pages), and is only computed for the top N repos (default 100) to stay within API rate limits.

**Regenerate rankings from an existing catalog:**
```bash
python scripts/discover_skills.py rankings skills_catalog.json --top-n 50 --rankings-dir my_rankings
```

**Customize during discovery:**
```bash
python scripts/discover_skills.py discover \
  --rank-top-n 50 \
  --rankings-dir custom_rankings \
  --pages 3
```

## Advanced topics

**Custom keyword configuration**: See [references/advanced-config.md](references/advanced-config.md)
**Troubleshooting API issues**: See [references/troubleshooting.md](references/troubleshooting.md)

## Resources

- GitHub Search API: https://docs.github.com/en/rest/search/search
- GitHub token settings: https://github.com/settings/tokens
