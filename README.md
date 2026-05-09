# Pi-hole + Unbound Container (Autonomous Fork)

This is an automated, single-container solution for Pi-hole and Unbound, forked from the `mpgirro` logic for networking stability but enhanced with a **"Set and Forget"** update engine.

## 🚀 Why this is better?

Most community images are either **stale** (manual updates) or **over-complex** (using heavy tools like Renovate/Dependabot which trigger builds immediately). This fork takes a "Reliability First" approach:

### 1. The 3-Day Stability Buffer
Unlike other repos that build the second a new Pi-hole tag is released, we wait exactly **3 days**. 
*   **Why?** Community "Day 0" releases occasionally have bugs. By waiting 3 days, we ensure your DNS infrastructure only pulls "matured" stable releases.

### 2. Auto-Updating Root Hints
We don't rely on the OS defaults for DNS recursion.
*   **Action:** Every build automatically downloads the latest `named.root` from Internic. 
*   **Result:** Your Unbound instance is always using the most current root server list for maximum recursion accuracy.

### 3. Dual-Stream Monitoring
The "Engine" monitors both Pi-hole releases AND Unbound package updates. If either is updated and stable, a new image is delivered.

## 🛠️ Usage

Update your local `docker-compose.yml` to point to this registry:

```yaml
services:
  pihole:
    image: ghcr.io/teeesss/pihole-unbound-container:latest
    # ... rest of your 100% working config ...
```

## 🤖 Automation Details
- **Update Checker**: Runs every 12 hours (`.github/workflows/update-checker.yml`).
- **Build Pipeline**: Builds and pushes to GHCR whenever the `VERSION` file is updated.
- **Multi-Arch Support**: Built for `x86_64`, `ARM64` (Pi 4/5), and `ARMv7` (Pi 3).

---
*Maintained by the teeesss autonomous pipeline.*
