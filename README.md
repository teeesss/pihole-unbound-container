# Pi-hole + Unbound Container (Autonomous Fork)

This is an automated, single-container solution for Pi-hole and Unbound, forked from the `mpgirro` logic for networking stability but enhanced with a **"Set and Forget"** update engine.

## 🚀 Why this exists?
Standard community images often fall behind official Pi-hole releases. This repo solves that by:
1.  **3-Day Stability Buffer**: Automatically checks for Pi-hole updates but waits 3 days before building to ensure the release is stable.
2.  **Dual-Stream Updates**: Triggers a build if either Pi-hole or the underlying Unbound packages are updated.
3.  **Multi-Arch Support**: Built for `x86_64`, `ARM64` (Pi 4/5), and `ARMv7` (Pi 3).

## 🛠️ Usage

Update your `docker-compose.yml` to point to this registry:

```yaml
services:
  pihole:
    image: ghcr.io/teeesss/pihole-unbound-container:latest
    # ... rest of your 100% working config ...
```

## 🤖 Automation Details
- **Update Checker**: Runs every 12 hours (`.github/workflows/update-checker.yml`).
- **Build Pipeline**: Builds and pushes to GHCR whenever the `VERSION` file is updated.
- **Root Hints**: Automatically downloads the latest `named.root` during every build to keep recursion healthy.

---
*Maintained by the teeesss autonomous pipeline.*
