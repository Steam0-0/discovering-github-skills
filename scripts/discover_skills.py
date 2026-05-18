#!/usr/bin/env python3
"""Discover GitHub repos with 1000+ stars that qualify as AI skills/agents/tools,
fetch their README, and generate structured summaries."""

import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_KEYWORDS = [
    "agent", "ai", "skill", "tool", "automation", "assistant",
    "llm", "mlops", "inference", "training", "rag", "chain",
    "diffusion", "model", "neural", "deep-learning", "nlp",
    "computer-vision", "transformer", "rlhf", "fine-tuning",
]

CACHE_FILE = ".github_skills_cache.json"

GITHUB_API = "https://api.github.com"


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------

def _headers():
    token = os.environ.get("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def fetch_repos(query: str, min_stars: int, page: int = 1, per_page: int = 100) -> list:
    """Search GitHub repos, return items list."""
    url = f"{GITHUB_API}/search/repositories"
    params = {
        "q": f"{query} stars:>={min_stars}",
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
        "page": page,
    }
    r = requests.get(url, headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("items", [])


def get_readme(owner: str, repo: str) -> str:
    """Fetch README from main or master branch, return text or empty string."""
    for branch in ("main", "master"):
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            continue
    return ""


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

def is_skill_repo(repo: dict, keywords: list[str]) -> bool:
    """Return True if repo matches skill-like criteria."""
    if repo.get("fork", False):
        return False
    text = f"{repo.get('name', '')} {repo.get('description') or ''} {repo.get('topics', [])}".lower()
    return any(k.lower() in text for k in keywords)


# ---------------------------------------------------------------------------
# Summary generation (local, no LLM needed for base version)
# ---------------------------------------------------------------------------

def generate_summary(repo: dict, readme: str) -> dict:
    """Generate a structured summary dict from repo metadata + README."""
    description = repo.get("description") or ""
    topics = repo.get("topics", [])
    readme_head = readme[:2000] if readme else ""

    features = _extract_features(readme_head, description)
    tech_stack = _guess_tech_stack(readme_head, topics)

    return {
        "name": repo["name"],
        "full_name": repo["full_name"],
        "url": repo["html_url"],
        "stars": repo["stargazers_count"],
        "description": description,
        "summary": _one_sentence(description, readme_head),
        "features": features,
        "use_cases": _guess_use_cases(description, topics, readme_head),
        "category": _categorize(description, topics, readme_head),
        "is_ai_skill": True,
        "tech_stack": tech_stack,
        "topics": topics,
        "language": repo.get("language"),
        "license": _extract_license(repo),
        "updated_at": repo.get("updated_at", ""),
    }


def _one_sentence(description: str, readme_head: str) -> str:
    """Use description if available, otherwise first meaningful line from README."""
    if description:
        return description.rstrip(".")
    for line in readme_head.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("!") and len(line) > 20:
            return line.rstrip(".")
    return ""


def _extract_features(readme_head: str, description: str) -> list[str]:
    """Extract bullet-point features from README (lines starting with - or *)."""
    features = []
    for line in readme_head.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")) and 10 < len(stripped) < 120:
            feat = stripped.lstrip("-* ").strip()
            if feat and feat not in features:
                features.append(feat)
            if len(features) >= 6:
                break
    return features


def _guess_use_cases(description: str, topics: list, readme_head: str) -> list[str]:
    """Guess use cases from description and topics."""
    use_cases = []
    text = f"{description} {' '.join(topics)}".lower()

    mappings = {
        "inference": "Production model inference and serving",
        "training": "Model training and fine-tuning",
        "fine-tuning": "Fine-tuning pretrained models",
        "agent": "Autonomous AI agent workflows",
        "rag": "Retrieval-augmented generation pipelines",
        "mlops": "ML operations and experiment tracking",
        "diffusion": "Image/video generation with diffusion models",
        "nlp": "Natural language processing tasks",
        "computer-vision": "Computer vision and image analysis",
        "automation": "Workflow automation and orchestration",
        "evaluation": "Model evaluation and benchmarking",
        "safety": "AI safety and alignment",
    }
    for key, uc in mappings.items():
        if key in text and uc not in use_cases:
            use_cases.append(uc)
        if len(use_cases) >= 4:
            break

    if not use_cases:
        use_cases.append("General-purpose AI/ML development")
    return use_cases


CATEGORY_KEYWORDS = {
    "Inference & Serving": ["inference", "serving", "deploy", "api", "server", "runtime", "llm.cpp"],
    "Training & Fine-tuning": ["training", "fine-tun", "finetun", "rlhf", "grpo", "lora", "peft"],
    "Agents & Orchestration": ["agent", "orchestr", "workflow", "automation", "copilot", "assistant"],
    "RAG & Search": ["rag", "retrieval", "search", "vector", "embedding", "index"],
    "Data & Processing": ["data", "dataset", "processing", "pipeline", "etl", "curation"],
    "Evaluation & Safety": ["eval", "benchmark", "safety", "alignment", "guardrail", "red-team"],
    "Infrastructure & MLOps": ["mlops", "monitor", "logging", "tracking", "ci/cd", "infrastructure"],
    "Multimodal & Vision": ["multimodal", "vision", "image", "video", "audio", "diffusion"],
    "Optimization & Quantization": ["quantiz", "prun", "distill", "compress", "optim"],
}


def _categorize(description: str, topics: list, readme_head: str) -> str:
    text = f"{description} {' '.join(topics)} {readme_head[:500]}".lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(k in text for k in keywords):
            return cat
    return "Other"


def _guess_tech_stack(readme_head: str, topics: list) -> list[str]:
    """Guess tech stack from README imports and topics."""
    stack = []
    text = f"{readme_head} {' '.join(topics)}".lower()

    indicators = {
        "python": ["python", "pip install", "import torch", "import transformers"],
        "pytorch": ["pytorch", "torch", "cuda"],
        "tensorflow": ["tensorflow", "tf."],
        "rust": ["rust", "cargo "],
        "go": ["golang", " go "],
        "javascript": ["javascript", "npm ", "node.js"],
        "typescript": ["typescript", "ts-node"],
        "docker": ["docker", "dockerfile"],
        "kubernetes": ["kubernetes", "k8s", "helm"],
        "cuda": ["cuda", "gpu", "triton"],
        "onnx": ["onnx"],
        "react": ["react", "next.js"],
    }
    for tech, patterns in indicators.items():
        if any(p in text for p in patterns):
            stack.append(tech)
        if len(stack) >= 5:
            break
    return stack


def _extract_license(repo: dict) -> str:
    spdx = repo.get("license", {})
    if spdx and isinstance(spdx, dict):
        return spdx.get("spdx_id", "Unknown")
    return "Unknown"


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def load_cache(path: str) -> dict:
    if Path(path).exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_cache(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Star growth calculation
# ---------------------------------------------------------------------------

MAX_STARGAZER_PAGES = 400  # GitHub API limit


def _stargazers_cutoff_page(owner: str, repo: str, cutoff_date: str, total_stars: int) -> int | None:
    """Binary search stargazers API to find the first page where all stars are >= cutoff_date.

    Stargazers are ordered oldest-first (page 1 = earliest stars).
    Returns the 1-indexed page number, or None on API error.
    """
    per_page = 100
    total_pages = max(1, math.ceil(total_stars / per_page))
    hi = min(total_pages, MAX_STARGAZER_PAGES)
    lo = 1

    while lo < hi:
        mid = (lo + hi) // 2
        r = requests.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/stargazers",
            headers={**_headers(), "Accept": "application/vnd.github.star+json"},
            params={"per_page": per_page, "page": mid},
            timeout=15,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        if not data:
            hi = mid
            continue
        if data[0].get("starred_at", "") >= cutoff_date:
            hi = mid
        else:
            lo = mid + 1

    return lo


def count_stars_after_date(owner: str, repo: str, cutoff_date: str, total_stars: int) -> int | None:
    """Count stars gained after cutoff_date using binary search on the stargazers API.

    Returns None if the cutoff date is older than the accessible range
    (i.e. the repo gained more than 40k stars in the period).
    """
    per_page = 100
    page = _stargazers_cutoff_page(owner, repo, cutoff_date, total_stars)
    if page is None:
        return None

    # Check the boundary page to get exact count
    r = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/stargazers",
        headers={**_headers(), "Accept": "application/vnd.github.star+json"},
        params={"per_page": per_page, "page": page},
        timeout=15,
    )
    if r.status_code != 200:
        return None
    data = r.json()
    if not data:
        return total_stars

    # Stars before cutoff on the boundary page
    count_before = sum(1 for item in data if item.get("starred_at", "") < cutoff_date)
    if page == 1:
        stars_before_cutoff = count_before
    else:
        stars_before_cutoff = (page - 1) * per_page + count_before

    return total_stars - stars_before_cutoff


def compute_growth_for_repos(skills: list[dict], top_n: int = 100) -> list[dict]:
    """Compute 1-month and 3-month star growth for the top N repos by total stars."""
    now = datetime.now(timezone.utc)
    three_months_ago = (now - timedelta(days=90)).strftime("%Y-%m-%dT00:00:00Z")
    one_month_ago = (now - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00Z")

    candidates = sorted(skills, key=lambda x: x["stars"], reverse=True)[:top_n]

    for i, skill in enumerate(candidates):
        owner, repo = skill["full_name"].split("/", 1)
        total = skill["stars"]

        print(f"  [{i+1}/{len(candidates)}] Computing growth for {skill['full_name']} ...")

        growth_3m = count_stars_after_date(owner, repo, three_months_ago, total)
        skill["growth_3m"] = growth_3m

        growth_1m = count_stars_after_date(owner, repo, one_month_ago, total)
        skill["growth_1m"] = growth_1m

        time.sleep(0.3)

    # Propagate growth data back to the full skills list
    growth_map = {s["full_name"]: (s.get("growth_3m"), s.get("growth_1m")) for s in candidates}
    for skill in skills:
        g3, g1 = growth_map.get(skill["full_name"], (None, None))
        skill.setdefault("growth_3m", g3)
        skill.setdefault("growth_1m", g1)

    return skills


# ---------------------------------------------------------------------------
# Ranking generation
# ---------------------------------------------------------------------------

RANKINGS_DIR = "rankings"


def _make_ranking_entry(skill: dict, growth_field: str | None = None) -> dict:
    """Create a lightweight ranking entry from a skill dict."""
    entry = {
        "rank": 0,
        "name": skill["name"],
        "full_name": skill["full_name"],
        "url": skill["url"],
        "stars": skill["stars"],
        "description": skill.get("summary", skill.get("description", "")),
        "category": skill.get("category", ""),
        "language": skill.get("language"),
        "license": skill.get("license", "Unknown"),
    }
    if growth_field:
        entry[growth_field] = skill.get(growth_field)
    return entry


def generate_rankings(skills: list[dict], output_dir: str = RANKINGS_DIR) -> str:
    """Generate three ranking files (top 20 each) and a combined index.

    Rankings:
      1. by_total_stars.json  — sorted by total star count
      2. by_growth_3m.json    — sorted by star growth in last 3 months
      3. by_growth_1m.json    — sorted by star growth in last 1 month

    Returns the output directory path.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. Total stars ranking
    by_total = sorted(skills, key=lambda x: x["stars"], reverse=True)[:20]
    for i, s in enumerate(by_total, 1):
        entry = _make_ranking_entry(s)
        entry["rank"] = i
        by_total[i - 1] = entry

    # 2. 3-month growth ranking
    by_growth_3m = sorted(
        [s for s in skills if s.get("growth_3m") is not None],
        key=lambda x: x["growth_3m"],
        reverse=True,
    )[:20]
    for i, s in enumerate(by_growth_3m, 1):
        entry = _make_ranking_entry(s, "growth_3m")
        entry["rank"] = i
        by_growth_3m[i - 1] = entry

    # 3. 1-month growth ranking
    by_growth_1m = sorted(
        [s for s in skills if s.get("growth_1m") is not None],
        key=lambda x: x["growth_1m"],
        reverse=True,
    )[:20]
    for i, s in enumerate(by_growth_1m, 1):
        entry = _make_ranking_entry(s, "growth_1m")
        entry["rank"] = i
        by_growth_1m[i - 1] = entry

    # Write JSON files
    for name, data in [
        ("by_total_stars.json", by_total),
        ("by_growth_3m.json", by_growth_3m),
        ("by_growth_1m.json", by_growth_1m),
    ]:
        with open(out / name, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  -> {out / name} ({len(data)} entries)")

    # Write combined index as Markdown
    _write_rankings_md(out, by_total, by_growth_3m, by_growth_1m)

    return str(out)


def _write_rankings_md(out: Path, by_total: list, by_growth_3m: list, by_growth_1m: list):
    """Write a human-readable Markdown summary of all three rankings."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    md = out / "README.md"
    with open(md, "w") as f:
        f.write(f"# AI Skill Rankings (as of {now})\n\n")

        f.write("## Top 20 by Total Stars\n\n")
        f.write("| Rank | Name | Stars | Category | Description |\n")
        f.write("|------|------|-------|----------|-------------|\n")
        for s in by_total:
            name = f"[{s['name']}]({s['url']})"
            desc = s["description"][:60].replace("|", "\\|") if s["description"] else ""
            f.write(f"| {s['rank']} | {name} | {s['stars']:,} | {s['category']} | {desc} |\n")

        f.write("\n## Top 20 by 3-Month Star Growth\n\n")
        f.write("| Rank | Name | Growth (3m) | Total Stars | Category | Description |\n")
        f.write("|------|------|-------------|-------------|----------|-------------|\n")
        for s in by_growth_3m:
            name = f"[{s['name']}]({s['url']})"
            g = s.get("growth_3m", 0)
            desc = s["description"][:50].replace("|", "\\|") if s["description"] else ""
            f.write(f"| {s['rank']} | {name} | +{g:,} | {s['stars']:,} | {s['category']} | {desc} |\n")

        f.write("\n## Top 20 by 1-Month Star Growth\n\n")
        f.write("| Rank | Name | Growth (1m) | Total Stars | Category | Description |\n")
        f.write("|------|------|-------------|-------------|----------|-------------|\n")
        for s in by_growth_1m:
            name = f"[{s['name']}]({s['url']})"
            g = s.get("growth_1m", 0)
            desc = s["description"][:50].replace("|", "\\|") if s["description"] else ""
            f.write(f"| {s['rank']} | {name} | +{g:,} | {s['stars']:,} | {s['category']} | {desc} |\n")

    print(f"  -> {md}")


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_discover(args):
    """Main discovery pipeline: fetch -> filter -> summarize -> output."""
    keywords = [k.strip() for k in args.keywords.split(",")]
    cache = load_cache(args.cache) if args.cache else {}
    results = []
    seen = set()

    if args.query:
        query = args.query
    else:
        # Build a broad OR query from top keywords for maximum recall
        top_kw = keywords[:6]
        query = " OR ".join(top_kw)

    for page in range(1, args.pages + 1):
        print(f"Fetching page {page}/{args.pages} ...")
        try:
            repos = fetch_repos(query, args.min_stars, page=page)
        except requests.HTTPError as e:
            print(f"HTTP error on page {page}: {e}", file=sys.stderr)
            break

        if not repos:
            print("No more results from GitHub API.")
            break

        for repo in repos:
            full_name = repo["full_name"]

            if full_name in seen:
                continue
            seen.add(full_name)

            if repo["stargazers_count"] < args.min_stars:
                continue

            if args.include_forks is False and repo.get("fork", False):
                continue

            if not is_skill_repo(repo, keywords):
                continue

            # Cache check: skip if unchanged and not force-refreshing
            cached = cache.get(full_name)
            if cached and not args.force_refresh and cached.get("updated_at") == repo.get("updated_at"):
                results.append(cached)
                continue

            print(f"  Processing {full_name} ({repo['stargazers_count']} stars)")
            readme = get_readme(repo["owner"]["login"], repo["name"])
            summary = generate_summary(repo, readme)
            results.append(summary)
            cache[full_name] = summary

            # Be polite to GitHub API
            time.sleep(0.5)

        # GitHub search API: 30 requests/minute for authenticated users
        if page < args.pages:
            time.sleep(2)

    # Sort by stars descending
    results.sort(key=lambda x: x["stars"], reverse=True)

    # Compute star growth and generate rankings
    print(f"\nComputing star growth for top projects ...")
    results = compute_growth_for_repos(results, top_n=args.rank_top_n)
    print(f"\nGenerating rankings ...")
    rankings_dir = generate_rankings(results, output_dir=args.rankings_dir)
    print(f"Rankings written to {rankings_dir}/")

    # Save output
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nDiscovered {len(results)} skills -> {args.output}")

    # Save cache
    if args.cache:
        save_cache(args.cache, cache)


def cmd_summary(args):
    """Print a summary of an existing catalog."""
    with open(args.input) as f:
        skills = json.load(f)

    categories = {}
    for s in skills:
        cat = s.get("category", "Other")
        categories.setdefault(cat, []).append(s)

    print(f"Total skills: {len(skills)}\n")
    for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"## {cat} ({len(items)})")
        for item in items[:5]:
            print(f"  - {item['name']} ({item['stars']} stars): {item.get('summary', '')[:80]}")
        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")
        print()


def cmd_filter(args):
    """Filter catalog by category or keyword."""
    with open(args.input) as f:
        skills = json.load(f)

    if args.category:
        skills = [s for s in skills if args.category.lower() in s.get("category", "").lower()]

    if args.keyword:
        skills = [s for s in skills if args.keyword.lower() in json.dumps(s).lower()]

    for s in skills:
        print(f"- {s['full_name']} ({s['stars']} stars) [{s.get('category', '')}]")
        print(f"  {s.get('summary', '')[:100]}")
    print(f"\n{len(skills)} results")


def cmd_export_md(args):
    """Export catalog as a Markdown table."""
    with open(args.input) as f:
        skills = json.load(f)

    with open(args.output, "w") as f:
        f.write("# GitHub Skills Catalog\n\n")
        f.write("| Name | Stars | Category | Summary | Tech Stack |\n")
        f.write("|------|-------|----------|---------|------------|\n")
        for s in skills:
            name = f"[{s['name']}]({s['url']})"
            stars = f"{s['stars']:,}"
            cat = s.get("category", "")
            summary = s.get("summary", "").replace("|", "\\|")[:80]
            stack = ", ".join(s.get("tech_stack", [])[:4])
            f.write(f"| {name} | {stars} | {cat} | {summary} | {stack} |\n")

    print(f"Exported {len(skills)} skills -> {args.output}")


def cmd_merge(args):
    """Merge two catalogs, deduplicating by full_name."""
    with open(args.input1) as f:
        cat1 = json.load(f)
    with open(args.input2) as f:
        cat2 = json.load(f)

    seen = set()
    merged = []
    for s in cat1 + cat2:
        if s["full_name"] not in seen:
            seen.add(s["full_name"])
            merged.append(s)

    merged.sort(key=lambda x: x["stars"], reverse=True)

    with open(args.output, "w") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    print(f"Merged: {len(cat1)} + {len(cat2)} -> {len(merged)} unique skills -> {args.output}")


def cmd_rankings(args):
    """Generate three ranking files from an existing catalog."""
    with open(args.input) as f:
        skills = json.load(f)

    # Compute growth if not already present
    needs_growth = any(s.get("growth_3m") is None for s in skills[:args.top_n])
    if needs_growth:
        print(f"Computing star growth for top {args.top_n} repos ...")
        skills = compute_growth_for_repos(skills, top_n=args.top_n)
    else:
        print("Growth data already present, skipping API calls.")

    print("Generating rankings ...")
    rankings_dir = generate_rankings(skills, output_dir=args.rankings_dir)
    print(f"Rankings written to {rankings_dir}/")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Discover GitHub AI skills with 1000+ stars")
    sub = parser.add_subparsers(dest="command")

    # discover
    p = sub.add_parser("discover", help="Fetch, filter, and summarize GitHub skills")
    p.add_argument("--min-stars", type=int, default=1000)
    p.add_argument("--pages", type=int, default=3, help="Number of pages to fetch (100 per page)")
    p.add_argument("--query", type=str, default=None, help="Custom GitHub search query")
    p.add_argument("--keywords", type=str, default=",".join(DEFAULT_KEYWORDS))
    p.add_argument("--output", type=str, default="skills_catalog.json")
    p.add_argument("--cache", type=str, default=CACHE_FILE)
    p.add_argument("--force-refresh", action="store_true")
    p.add_argument("--include-forks", action="store_true")
    p.add_argument("--rank-top-n", type=int, default=100,
                    help="Number of top repos to compute star growth for (default: 100)")
    p.add_argument("--rankings-dir", type=str, default=RANKINGS_DIR,
                    help="Output directory for ranking files (default: rankings)")
    p.set_defaults(func=cmd_discover)

    # summary
    p = sub.add_parser("summary", help="Print summary of a catalog")
    p.add_argument("input", type=str)
    p.set_defaults(func=cmd_summary)

    # filter
    p = sub.add_parser("filter", help="Filter catalog by category or keyword")
    p.add_argument("input", type=str)
    p.add_argument("--category", type=str, default=None)
    p.add_argument("--keyword", type=str, default=None)
    p.set_defaults(func=cmd_filter)

    # export-md
    p = sub.add_parser("export-md", help="Export catalog as Markdown table")
    p.add_argument("input", type=str)
    p.add_argument("--output", type=str, default="SKILLS_TABLE.md")
    p.set_defaults(func=cmd_export_md)

    # merge
    p = sub.add_parser("merge", help="Merge two catalogs with dedup")
    p.add_argument("input1", type=str)
    p.add_argument("input2", type=str)
    p.add_argument("--output", type=str, default="merged_catalog.json")
    p.set_defaults(func=cmd_merge)

    # rankings
    p = sub.add_parser("rankings", help="Generate top-20 rankings from an existing catalog")
    p.add_argument("input", type=str, help="Path to skills_catalog.json")
    p.add_argument("--top-n", type=int, default=100,
                    help="Number of top repos to compute star growth for (default: 100)")
    p.add_argument("--rankings-dir", type=str, default=RANKINGS_DIR,
                    help="Output directory for ranking files (default: rankings)")
    p.set_defaults(func=cmd_rankings)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
