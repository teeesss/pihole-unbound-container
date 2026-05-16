# Claude Code Context - Pi-hole + Unbound

## Architecture
- **Single Container**: Pi-hole + Unbound running via `custom-entrypoint.sh`.
- **Base Image**: `pihole/pihole:latest` (Alpine based).
- **Automation**: GitHub Actions monitor upstream releases every 12 hours.

## CI/CD Guards
- **3-Day Stability Buffer**: No update is pushed unless the upstream release is 3+ days old.
- **4-Layer Stable Filter**:
  1. `.prerelease == false`
  2. `.draft == false`
  3. **Blocklist**: Excludes `rc`, `alpha`, `beta`, `test`, `dev`, `nightly`, etc.
  4. **Allowlist**: Regex `^(v?\d+([.\-]\d+)*|release-\d+(\.\d+)*)$`.

## Key Files
- `docker/Dockerfile`: Main container definition.
- `docker/unbound-pihole.conf`: Unbound config tuned for Pi-hole.
- `.github/workflows/update-checker.yml`: Version monitoring logic.
- `.github/workflows/docker-publish.yml`: Build and push logic.
- `local-deploy/install.sh`: Automated local setup tool.

## Deployment
- Registry: `ghcr.io/teeesss/pihole-unbound-container:latest`
- Custom DNS: `127.0.0.1#5335` (Unbound port).
