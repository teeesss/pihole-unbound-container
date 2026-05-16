# Tasks

## Active
- [ ] Implement health check for Unbound recursion in `install.sh`
- [ ] Add automated cleanup for stale container images in local-deploy

## Completed
- [x] Harden `update-checker.yml` against GitHub API rate-limits
- [x] Implement 4-layer stable release filter (API flags, Blocklist, Allowlist)
- [x] Fix jq "Cannot index string with string 'prerelease'" error
- [x] Extend allowlist to support Unbound `release-X.Y.Z` tag format
- [x] Update README with detailed automation and filter documentation

## Issues
- [x] CI crash on anonymous API rate-limit -> FIXED (Added GITHUB_TOKEN auth)
- [x] CI accepting non-stable releases -> FIXED (Added blocklist + semver allowlist)
