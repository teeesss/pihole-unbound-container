# Knowledge Base

## GitHub API Rate-Limiting
- **Problem**: Anonymous requests are limited to 60/hr. If the `jq` filter expects an array but gets an error object, the pipeline crashes.
- **Solution**: Always use `GITHUB_TOKEN` in CI. Add a JSON type guard: `if ! echo "$response" | jq -e 'type == "array"'`.

## Release Filtering Strategy
- **Standard**: Don't trust the `.prerelease` flag alone. Maintainers often forget it.
- **Hardened Pattern**:
  - `Blocklist`: Keywords like `rc`, `beta`, `nightly`.
  - `Allowlist`: Positive regex like `^v?\d+([.\-]\d+)*$` ensures only clean version numbers pass.
  - `Buffer`: 3-day age check allows for community testing/bug discovery before auto-adoption.

## PowerShell Pitfalls
- Use `Get-ChildItem -Filter` instead of `ls` if positional parameters are ambiguous.
- Use `;` instead of `&&` for command chaining in PowerShell.
