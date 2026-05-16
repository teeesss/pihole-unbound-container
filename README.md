# Pi-hole + Unbound Container

[![Build Status](https://github.com/teeesss/pihole-unbound-container/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/teeesss/pihole-unbound-container/actions/workflows/docker-publish.yml)
[![Update Checker](https://github.com/teeesss/pihole-unbound-container/actions/workflows/update-checker.yml/badge.svg)](https://github.com/teeesss/pihole-unbound-container/actions/workflows/update-checker.yml)

A **single-container**, self-updating solution pairing [Pi-hole](https://pi-hole.net/) with [Unbound](https://nlnetlabs.nl/projects/unbound/about/) for recursive, encrypted, ad-blocking DNS on your local network.

> [!NOTE]
> **What this is**: An automated container build and update pipeline. It is **not** a support forum for general Pi-hole or Unbound configuration. For product support, see [Reference & Support](#-reference--support) below.

---

## What Is This?

This container runs **Pi-hole** (DNS sinkhole / ad-blocker) and **Unbound** (recursive DNS resolver) side-by-side in a single Docker image.

- **Pi-hole** intercepts DNS queries, blocking ad and tracker domains at the network level for all devices on your network.
- **Unbound** resolves DNS queries directly against the root DNS servers — no upstream provider like Google (8.8.8.8) or Cloudflare (1.1.1.1). Your DNS queries never leave your network.

Together, they give you **privacy**, **speed**, and **ad-blocking** with full **DNSSEC validation**.

> [!TIP]
> New to Pi-hole? Start with the official [Pi-hole documentation](https://docs.pi-hole.net/) before deploying. New to Unbound? Read the [official Unbound guide on Pi-hole's docs](https://docs.pi-hole.net/guides/dns/unbound/).

---

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed on your host.
- A host on your local network (a Raspberry Pi, VM, NAS, etc.)
- Port `53` (DNS) and `80`/`443` (Pi-hole Web UI) available on the host.

### 1. Create a `docker-compose.yml`

```yaml
services:
  pihole:
    image: ghcr.io/teeesss/pihole-unbound-container:latest
    container_name: pihole
    environment:
      TZ: 'America/Chicago'            # Your timezone
      WEBPASSWORD: 'your-password'     # Pi-hole admin dashboard password
      PIHOLE_DNS_: '127.0.0.1#5335'   # Use the bundled Unbound resolver
      DNSSEC: 'true'                   # Enable DNSSEC validation
    ports:
      - "53:53/tcp"                    # DNS
      - "53:53/udp"
      - "80:80/tcp"                    # Pi-hole web UI
    volumes:
      - './etc-pihole:/etc/pihole'
      - './etc-dnsmasq.d:/etc/dnsmasq.d'
    restart: unless-stopped
```

### 2. Start the Container

```bash
docker compose up -d
```

### 3. Point Your Network at Pi-hole

Set your **router's DHCP DNS server** (or individual device DNS) to the IP address of the machine running this container. Pi-hole will handle all DNS queries for your network.

> [!IMPORTANT]
> For step-by-step router configuration, see [Pi-hole's documentation on router setup](https://docs.pi-hole.net/main/post-install/).

---

## ⚙️ Pi-hole DNS Configuration

Because Unbound is bundled inside the container, Pi-hole must be told to use it instead of an external DNS provider.

If you set `PIHOLE_DNS_: '127.0.0.1#5335'` in your environment variables (as shown above), this is handled automatically.

To verify or change it manually in the Pi-hole Web UI:
1. Open the Pi-hole dashboard → **Settings** → **DNS**.
2. Uncheck all upstream DNS servers.
3. Under **Custom DNS (IPv4)**, enter `127.0.0.1#5335`.
4. Click **Save**.

> [!TIP]
> Port `5335` is the port Unbound listens on inside the container. It is not exposed externally — it is only reachable by Pi-hole internally.

---

## ✅ Verification

### Test DNS Resolution
```bash
docker exec -it pihole dig @127.0.0.1 -p 5335 google.com
```
**Expected**: Returns `status: NOERROR` and an IP address.

### Test DNSSEC Validation
```bash
# This should SUCCEED (look for the 'ad' Authentic Data flag)
docker exec -it pihole dig @127.0.0.1 -p 5335 sigok.verteiltesysteme.net

# This should FAIL with SERVFAIL (signature is intentionally broken)
docker exec -it pihole dig @127.0.0.1 -p 5335 sigfail.verteiltesysteme.net
```
The `ad` flag in the first result confirms DNSSEC is working correctly.

---

## ⏪ Rollback to a Previous Version

All versioned images are published to the GitHub Container Registry. If an update causes issues, pin to a specific version:

```bash
# See available versions
# https://github.com/teeesss/pihole-unbound-container/pkgs/container/pihole-unbound-container

docker pull ghcr.io/teeesss/pihole-unbound-container:2026.05.0
```

Then update your `docker-compose.yml` to pin the image tag:
```yaml
image: ghcr.io/teeesss/pihole-unbound-container:2026.05.0
```

---

## 💡 Advanced Configuration

### Custom Unbound Configuration
Mount a custom config file to extend or override Unbound settings:
```yaml
volumes:
  - './my-unbound.conf:/etc/unbound/unbound.conf.d/custom.conf'
```

**Multi-core performance** — if your host has multiple CPU cores, add this to your custom config:
```ini
server:
    num-threads: 4               # Match your core count
    msg-cache-slabs: 4           # Must be a power of 2
    rrset-cache-slabs: 4
    infra-cache-slabs: 4
    key-cache-slabs: 4
```

> [!NOTE]
> For all Unbound configuration options, see the [Unbound man page](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html).

### Security Hardening
Run the container in a locked-down state by dropping Linux capabilities:
```yaml
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE
  - CHOWN
  - SETUID
  - SETGID
```

> [!CAUTION]
> Capability requirements may change between Pi-hole versions. Always test after a version update. See [Pi-hole's Docker documentation](https://github.com/pi-hole/docker-pi-hole#docker-compose-examples) for the latest guidance.

---

## 🤖 Automation Architecture

This repository is designed to be **fully autonomous** — it self-updates to the latest stable versions of both Pi-hole and Unbound without manual intervention.

### The Update Pipeline

```
GitHub Actions (every 12h)
         │
         ▼
  fetch_release() Helper
  ├── GitHub API (authenticated, 5000 req/hr)
  └── Docker Hub API (fallback if GitHub unavailable)
         │
         ▼
  4-Layer Stability Filter
  ├── Layer 1: .prerelease == false  (API flag)
  ├── Layer 2: .draft == false       (API flag)
  ├── Layer 3: Tag Blocklist         (alpha/beta/rc/rh/dev/nightly/...)
  └── Layer 4: Tag Allowlist         (must be clean semver or release-X.Y.Z)
         │
         ▼
  3-Day Stability Buffer
  (waits 72h after release before accepting)
         │
         ▼
  Downgrade Guard
  (sort -V prevents rolling back to an older version)
         │
         ▼
  Update VERSION file → triggers Docker build → pushes to GHCR
```

### Accepted vs. Rejected Tags

| Tag | Accepted? | Reason |
|---|---|---|
| `2026.05.0` | ✅ | Pi-hole date-based release |
| `v2.1.3` | ✅ | Standard semver |
| `release-1.25.0` | ✅ | Unbound's confirmed tag format |
| `v2.1.0-rc1` | ❌ | Blocklist: `rc` keyword |
| `v2.1.0-hotfix` | ❌ | Allowlist: unknown suffix |
| `nightly-20240601` | ❌ | Blocklist: `nightly` keyword |
| `vTestTag` | ❌ | Allowlist: non-numeric suffix |

### Build Details

| Component | Detail |
|---|---|
| **Update Checker** | Runs every 12 hours via GitHub Actions cron |
| **API Auth** | `GITHUB_TOKEN` auto-injected by GitHub (5,000 req/hr) |
| **API Fallback** | Docker Hub Registry API if GitHub is unreachable |
| **Network Resilience** | 3-retry with backoff on all API calls |
| **Graceful Failure** | Emits `::warning::` and exits cleanly instead of failing red |
| **Multi-Arch Builds** | `linux/amd64`, `linux/arm64`, `linux/arm/v7` |
| **Build Trigger** | Auto-fires when `VERSION` or `docker/` files change |

---

## 📚 Reference & Support

### Official Documentation
- **Pi-hole Docs**: [docs.pi-hole.net](https://docs.pi-hole.net/)
- **Pi-hole Docker**: [github.com/pi-hole/docker-pi-hole](https://github.com/pi-hole/docker-pi-hole)
- **Pi-hole + Unbound Guide**: [docs.pi-hole.net/guides/dns/unbound](https://docs.pi-hole.net/guides/dns/unbound/)
- **Pi-hole Community Forum**: [discourse.pi-hole.net](https://discourse.pi-hole.net/)

### Unbound
- **Unbound Docs**: [unbound.docs.nlnetlabs.nl](https://unbound.docs.nlnetlabs.nl/)
- **Unbound GitHub**: [github.com/NLnetLabs/unbound](https://github.com/NLnetLabs/unbound)

### This Repository
- **Container Packages**: [GHCR Packages](https://github.com/teeesss/pihole-unbound-container/pkgs/container/pihole-unbound-container)
- **Build Logs**: [Actions Tab](https://github.com/teeesss/pihole-unbound-container/actions)
- **Base Logic**: Networking adapted from [mpgirro/docker-pihole-unbound](https://github.com/mpgirro/docker-pihole-unbound)

---

*Maintained by the teeesss autonomous pipeline. For Pi-hole or Unbound product issues, please use their official support channels above.*
