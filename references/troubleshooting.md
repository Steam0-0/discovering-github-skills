# Troubleshooting

## Contents
- API rate limiting
- Authentication errors
- Empty or missing results
- README fetch failures
- Cache issues
- Encoding problems

## API rate limiting

**Symptom**: `403 API rate limit exceeded` or `422 Validation Failed`

GitHub Search API limits:
- Authenticated: 30 requests/minute
- Unauthenticated: 10 requests/minute (effectively unusable)

**Fix 1**: Set `GITHUB_TOKEN` environment variable:
```bash
export GITHUB_TOKEN="ghp_your_token_here"
python scripts/discover_skills.py discover --pages 3
```

**Fix 2**: Reduce page count and wait between runs:
```bash
python scripts/discover_skills.py discover --pages 1  # fetch fewer pages
```

**Fix 3**: The script already includes a 2-second delay between pages. Increase it by editing the sleep in `cmd_discover`:
```python
time.sleep(5)  # increase inter-page delay
```

## Authentication errors

**Symptom**: `401 Unauthorized`

- Verify your token is valid at https://github.com/settings/tokens
- Check the token hasn't expired
- No special scopes are needed for public repo access
- Ensure no extra whitespace in the environment variable:
```bash
echo "[$GITHUB_TOKEN]"  # should show [ghp_xxxxx] with no spaces
```

## Empty or missing results

**Symptom**: "Discovered 0 skills" or far fewer than expected

**Cause 1**: Keywords too restrictive
```bash
# Use broader keywords
python scripts/discover_skills.py discover --keywords "ai,llm,model,tool,framework"
```

**Cause 2**: `--min-stars` too high
```bash
# Lower threshold
python scripts/discover_skills.py discover --min-stars 500
```

**Cause 3**: GitHub search API returns different results than github.com search. The API has a 1000-result cap per search query. For exhaustive results, use targeted queries:
```bash
python scripts/discover_skills.py discover --query "topic:llm stars:>=1000"
python scripts/discover_skills.py discover --query "topic:agent stars:>=1000"
```

**Cause 4**: Fork exclusion removing valid repos. Include forks temporarily to check:
```bash
python scripts/discover_skills.py discover --include-forks
```

## README fetch failures

**Symptom**: Empty `summary` and `features` fields

**Cause**: Repo uses non-standard branch names or has no README.md.

The script tries `main` then `master`. If the repo uses a different default branch, the README fetch fails. The script falls back to the repo `description` field from the API.

**Fix**: Manually check and adjust branch names:
```python
# Add more branches to try in get_readme()
for branch in ("main", "master", "develop", "v1"):
```

## Cache issues

**Symptom**: Stale data after repo updates

**Fix**: Force refresh to ignore cache:
```bash
python scripts/discover_skills.py discover --force-refresh
```

**Fix**: Delete cache file to start fresh:
```bash
rm .github_skills_cache.json
```

**Symptom**: Cache file corrupted (JSON parse error)

```bash
rm .github_skills_cache.json
python scripts/discover_skills.py discover --pages 3
```

## Encoding problems

**Symptom**: `UnicodeDecodeError` or garbled characters in output

The script uses `ensure_ascii=False` in JSON output. If downstream tools have issues:

```bash
# Re-export with ASCII only
python -c "
import json
data = json.load(open('skills_catalog.json'))
print(json.dumps(data, indent=2, ensure_ascii=True))
" > skills_catalog_ascii.json
```

## Connection timeouts

**Symptom**: `requests.exceptions.ReadTimeout`

Default timeout is 30s for API calls, 15s for README fetches. Increase for slow connections:

```python
# In fetch_repos()
r = requests.get(url, headers=_headers(), params=params, timeout=60)

# In get_readme()
r = requests.get(url, timeout=30)
```
