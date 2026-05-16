# Pi-hole + Unbound Container (Autonomous Fork)

This is an automated, single-container solution for Pi-hole and Unbound, forked from the `mpgirro` logic for networking stability but enhanced with a **"Set and Forget"** update engine.

> [!IMPORTANT]
> **Scope Disclaimer**: This repository exists to provide **automation** and **version parity**. It is not a support forum for general Pi-hole or Unbound troubleshooting. For functional help, see the [Reference & Support](#reference--support) section below.

---

## 🚀 Why this is better?

Most community images are either **stale** (manual updates) or **over-complex**. This fork takes a "Reliability First" approach:

### 1. The 3-Day Stability Buffer
We wait **3 days** after an official release before building.
- **Why?** To ensure your DNS infrastructure only pulls "matured" stable releases.

### 2. Auto-Updating Root Hints
Every build automatically downloads the latest `named.root` from Internic.

### 3. Dual-Stream Monitoring
The "Engine" monitors both [Pi-hole Releases](https://github.com/pi-hole/docker-pi-hole/releases) AND Unbound package updates.

### 4. Stable-Only Release Filter (4-Layer Guard)
The update checker enforces **4 independent layers** before any version is accepted:

| Layer | Type | What It Catches |
|---|---|---|
| `.prerelease == false` | API flag | Releases the maintainer flagged as pre-release |
| `.draft == false` | API flag | Unpublished / draft releases |
| **Tag blocklist** | Regex (deny) | `alpha`, `beta`, `rc`, `rh`, `test`, `dev`, `nightly`, `pre-*`, `snapshot`, `preview`, `unstable`, `canary`, `experimental` — case-insensitive |
| **Tag allowlist** | Regex (allow) | Tag **must** match `v1.2.3`, `1.2.3`, or `2024.06.01` — pure semver/date only, no suffixes |

A release must pass **all 4 layers**. The allowlist is the zero-trust final gate — anything that doesn't look exactly like a clean version number is rejected by default, even if the blocklist missed it.

**Examples:**

| Tag | Result |
|---|---|
| `v2024.5.0` | ✅ Accepted |
| `2026.05.0` | ✅ Accepted |
| `release-1.25.0` | ❌ Rejected (blocklist: `release` prefix not pure semver) |
| `v2.1.0-rc1` | ❌ Rejected (blocklist + allowlist) |
| `v2.1.0-hotfix` | ❌ Rejected (allowlist: unknown suffix) |
| `nightly-20240601` | ❌ Rejected (blocklist + allowlist) |

---

## 🛠️ Configuration

### 1. Pi-hole DNS Settings
To use the integrated Unbound resolver, go to your Pi-hole Web UI:
1. Navigate to **Settings** > **DNS**.
2. Uncheck all boxes under "Upstream DNS Servers".
3. In **Custom 1 (IPv4)**, enter: `127.0.0.1#5335`
4. Click **Save**.

### 2. Docker Compose Example

```yaml
services:
  pihole:
    image: ghcr.io/teeesss/pihole-unbound-container:latest
    container_name: pihole
    environment:
      TZ: 'America/Chicago'
      PIHOLE_DNS_: '127.0.0.1#5335'
      DNSSEC: 'true'
    volumes:
      - './etc-pihole:/etc/pihole'
      - './etc-dnsmasq.d:/etc/dnsmasq.d'
    restart: unless-stopped
```

---

## 💡 Pro-Level Insights (Information Only)

### ⚡ Unbound Performance (Multi-Core)
If your container has multiple CPU cores, mount a custom config to `/etc/unbound/unbound.conf.d/pro.conf`:
- **Threads**: Set `num-threads` to match your core count.
- **Slabs**: Set `msg-cache-slabs` and `rrset-cache-slabs` to a power of 2 (e.g., `4`) to reduce lock contention.

### 🔒 Security Hardening Tips
To run in a "Locked Down" state:
- **Read-Only**: Set `read_only: true` in your compose file (requires `tmpfs` mounts for `/run`, `/tmp`, and `/var/log/pihole`).
- **Cap-Drop**: Safely drop `ALL` capabilities and add back only `NET_BIND_SERVICE` and `CHOWN`.

### 🚀 Pi-hole v6 Advantage
v6 introduces a unified FTL-only engine (removing Lighttpd/PHP) — faster dashboard loads and a smaller security footprint.

---

## ✅ Verification & Testing

### 1. Test Recursion
```bash
docker exec -it pihole dig @127.0.0.1 -p 5335 google.com
```
**Success**: Returns `status: NOERROR` and an IP address.

### 2. Test DNSSEC Validation
```bash
# Should succeed (Authentic Data flag)
docker exec -it pihole dig @127.0.0.1 -p 5335 sigok.verteiltesysteme.net

# Should FAIL (BOGUS signature)
docker exec -it pihole dig @127.0.0.1 -p 5335 sigfail.verteiltesysteme.net
```
**Success**: Look for the **`ad`** (Authentic Data) flag in the first result.

---

## ⏪ How to Rollback

If a new version causes issues, pull a versioned tag from the [Packages page](https://github.com/teeesss/pihole-unbound-container/pkgs/container/pihole-unbound-container):

```bash
docker pull ghcr.io/teeesss/pihole-unbound-container:[VERSION_TAG]
```

---

## 🤖 Automation Details

| Component | Detail |
|---|---|
| **Update Checker** | Runs every 12 hours via GitHub Actions cron |
| **Rate-limit Protection** | All GitHub API calls authenticated with `GITHUB_TOKEN` (5,000 req/hr vs 60 unauthenticated) |
| **Graceful Fallback** | If API is unreachable or returns an error object, workflow emits `::warning::` and exits cleanly — no red failures |
| **Multi-Arch Builds** | `linux/amd64`, `linux/arm64`, `linux/arm/v7` |
| **Build Trigger** | Auto-fires when `VERSION` or `docker/` files change |
| **Layer Cache** | GitHub Actions GHA cache for fast multi-arch layer reuse |

---

## 📚 Reference & Support

- **Pi-hole**: [Docs](https://docs.pi-hole.net/) | [Forum](https://discourse.pi-hole.net/) | [GitHub](https://github.com/pi-hole/docker-pi-hole)
- **Unbound**: [Docs](https://unbound.docs.nlnetlabs.nl/) | [GitHub](https://github.com/NLnetLabs/unbound)
- **Base Logic**: Networking adapted from [mpgirro/docker-pihole-unbound](https://github.com/mpgirro/docker-pihole-unbound)

---
*Maintained by the teeesss autonomous pipeline.*
