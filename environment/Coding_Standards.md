# Coding Standards

## Shell Scripting (Bash)
- Use `set -euo pipefail` in all scripts.
- Never use post-increment in arithmetic statements (e.g., `(( count++ ))` returns 1 when count is 0 under `set -e`). Use `count=$(( count + 1 ))`.
- When filtering stream output with regex, avoid `head -n 1` after `grep` under `pipefail` to prevent SIGPIPE (exit code 141). Use `sed -n '1p'`.
- Quote all variables to handle whitespace and empty values: `"$var"`.
- Use local variables inside functions: `local my_var="$1"`.

## Docker & Containerization
- Avoid implicit folder assumptions during archive extractions. Use `--strip-components=1 -C <target_dir>`.
- Use multi-stage builds to keep build dependencies out of production runtime images.
- Always provide explicit timeouts and retry counts on external network calls (`curl`, `wget`).
- Ensure entrypoint scripts forward OS signals and manage child processes cleanly.

## GitHub Actions & Workflows
- Security-first: validate API response formats before piping into `jq` (`type == "array"`).
- Reusable workflows: use relative paths without branch suffixes for internal caller workflows (`uses: ./.github/workflows/<file>.yml`).
- Git state safety: always run `git pull --rebase` before staging files with `git add` to prevent index conflicts.
- Rate-limiting protection: authenticate all GitHub API queries with `GITHUB_TOKEN`.
