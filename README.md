# Pi-hole + Unbound Container

[![Build Status](https://github.com/teeesss/pihole-unbound-container/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/teeesss/pihole-unbound-container/actions/workflows/docker-publish.yml)
[![Update Checker](https://github.com/teeesss/pihole-unbound-container/actions/workflows/update-checker.yml/badge.svg)](https://github.com/teeesss/pihole-unbound-container/actions/workflows/update-checker.yml)

A **single-container**, self-updating solution pairing [Pi-hole](https://pi-hole.net/) with [Unbound](https://nlnetlabs.nl/projects/unbound/about/) for recursive, privacy-focused, ad-blocking DNS on your local network.

> [!NOTE]
> This repository provides an **automated container build pipeline**. It is not a support forum for Pi-hole or Unbound. For product help, see [Reference & Support](#-reference--support).

---

## What Is This?

This container runs two services side-by-side in a single Docker image:

- **Pi-hole** — a DNS sinkhole that blocks ads and trackers at the network level for every device on your network.
- **Unbound** — a validating, recursive DNS resolver that queries authoritative DNS servers directly instead of forwarding to a third-party provider like Google (`8.8.8.8`) or Cloudflare (`1.1.1.1`).

Together they give you **ad-blocking**, **DNSSEC validation**, and **DNS privacy** — no third-party resolver ever sees your query history.

> [!TIP]
> New to Pi-hole? Start with the official [Pi-hole documentation](https://docs.pi-hole.net/). New to Unbound? Read the [Pi-hole + Unbound guide](https://docs.pi-hole.net/guides/dns/unbound/).

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.
- A host on your local network (Raspberry Pi, VM, NAS, old laptop, etc.).
- Port **53** (DNS) and **80** (Pi-hole Web UI) available on the host.

### 1. Create a `docker-compose.yml`

```yaml
services:
  pihole:
    image: ghcr.io/teeesss/pihole-unbound-container:latest
    container_name: pihole
    hostname: pihole
    environment:
      TZ: 'America/Chicago'            # Set to your timezone
      WEBPASSWORD: 'changeme'          # Pi-hole admin dashboard password
      PIHOLE_DNS_: '127.0.0.1#5335'   # Points Pi-hole at the bundled Unbound
      DNSSEC: 'true'                   # Enable DNSSEC validation
    ports:
      - "53:53/tcp"                    # DNS (TCP)
      - "53:53/udp"                    # DNS (UDP)
      - "80:80/tcp"                    # Pi-hole web dashboard
    volumes:
      - './etc-pihole:/etc/pihole'           # Persistent Pi-hole config
      - './etc-dnsmasq.d:/etc/dnsmasq.d'     # Persistent dnsmasq config
    restart: unless-stopped
```

### 2. Start the Container

```bash
docker compose up -d
```

### 3. Access the Dashboard

Open `http://<HOST_IP>/admin` in your browser and log in with the password you set above.

### 4. Point Your Network at Pi-hole

Set your **router's DHCP DNS server** to the IP address of the host running this container. All devices on the network will then use Pi-hole for DNS.

> [!IMPORTANT]
> For router-specific instructions, see [Pi-hole's post-install guide](https://docs.pi-hole.net/main/post-install/).

---

## ✅ Verification

After starting the container, confirm everything is working:

### Test DNS Resolution (Unbound)
```bash
docker exec -it pihole dig @127.0.0.1 -p 5335 google.com
```
**Expected**: `status: NOERROR` with an IP address in the answer section.

### Test DNSSEC Validation
```bash
# Should SUCCEED — look for the 'ad' (Authentic Data) flag in the output
docker exec -it pihole dig @127.0.0.1 -p 5335 sigok.verteiltesysteme.net

# Should FAIL with SERVFAIL — the signature on this domain is intentionally broken
docker exec -it pihole dig @127.0.0.1 -p 5335 sigfail.verteiltesysteme.net
```

### Test Pi-hole Ad-blocking
```bash
# Should return 0.0.0.0 or NXDOMAIN (blocked)
docker exec -it pihole dig @127.0.0.1 ads.google.com
```

---

## ⚙️ Configuration

### Pi-hole DNS Settings

The `PIHOLE_DNS_: '127.0.0.1#5335'` environment variable tells Pi-hole to forward all DNS queries to the bundled Unbound resolver on port 5335. This is configured automatically when you use the compose file above.

To verify or change it manually:
1. Open the Pi-hole dashboard → **Settings** → **DNS**.
2. Uncheck all upstream DNS servers (Google, Cloudflare, etc.).
3. Under **Custom DNS (IPv4)**, enter `127.0.0.1#5335`.
4. Click **Save**.

> [!TIP]
> Port 5335 is internal to the container — it is not exposed to your network. Only Pi-hole can reach Unbound on this port.

### IPv6

The bundled Unbound configuration has IPv6 disabled by default (`do-ip6: no`). If your network has native IPv6 connectivity and you want Unbound to query authoritative servers over IPv6, mount a custom config (see below) and set `do-ip6: yes`.

> [!NOTE]
> For IPv6 configuration guidance, see the [Pi-hole IPv6 documentation](https://docs.pi-hole.net/) and the [Unbound configuration reference](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html).

---

## 💡 Advanced Configuration

### Custom Unbound Settings

Mount a custom config file to extend or override the defaults:

```yaml
volumes:
  - './my-unbound.conf:/etc/unbound/unbound.conf.d/custom.conf'
```

**Multi-core performance** — if your host has multiple CPU cores:

```ini
server:
    num-threads: 4               # Match your core count
    msg-cache-slabs: 4           # Power of 2, reduces lock contention
    rrset-cache-slabs: 4
    infra-cache-slabs: 4
    key-cache-slabs: 4
```

> [!NOTE]
> For the complete list of Unbound options, see the [Unbound man page](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html).

### Security Hardening

Drop all Linux capabilities and add back only the required ones:

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
> Capability requirements may change between Pi-hole versions. Always test after upgrading. See the [Pi-hole Docker repo](https://github.com/pi-hole/docker-pi-hole) for the latest guidance.

---

## ⏪ Rollback

All versioned images are published to the [GitHub Container Registry](https://github.com/teeesss/pihole-unbound-container/pkgs/container/pihole-unbound-container). Image tags mirror the upstream **Pi-hole version** (e.g., `2026.05.0`).

To pin to a specific version:

```yaml
# In your docker-compose.yml
image: ghcr.io/teeesss/pihole-unbound-container:2026.05.0
```

Then recreate the container:

```bash
docker compose up -d --force-recreate
```

---

## ❓ Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Container exits immediately | Port 53 already in use | Stop `systemd-resolved` or other DNS services: `sudo systemctl disable --now systemd-resolved` |
| `dig` returns SERVFAIL for everything | Unbound failed to start | Check logs: `docker logs pihole` and look for Unbound errors |
| No `ad` flag on DNSSEC queries | DNSSEC not enabled | Verify `DNSSEC: 'true'` is set in your environment |
| Dashboard unreachable | Port 80 conflict | Check if another service (Apache, Nginx) is using port 80 |
| Slow first query after restart | Normal Unbound behavior | Unbound has an empty cache on startup — it warms up within minutes |

> [!NOTE]
> For detailed troubleshooting, see the [Pi-hole FAQ](https://docs.pi-hole.net/) and the [Unbound troubleshooting guide](https://unbound.docs.nlnetlabs.nl/en/latest/getting-started/troubleshooting.html).

---

## 🤖 Automation Architecture

This repository is **fully autonomous** — no manual intervention needed. The pipeline checks for new stable releases every 12 hours and rebuilds the container image when versions change.

### Update Pipeline

```
GitHub Actions (every 12h)
         │
         ▼
  fetch_release() ─── GitHub API (authenticated, 5000 req/hr)
         │              └── Docker Hub API (fallback)
         ▼
  ┌─ 4-Layer Stability Filter ─────────────────────────┐
  │  Layer 1: .prerelease == false     (API flag)       │
  │  Layer 2: .draft == false          (API flag)       │
  │  Layer 3: Tag Blocklist            (alpha/beta/rc…) │
  │  Layer 4: Tag Allowlist            (semver only)    │
  └─────────────────────────────────────────────────────┘
         │
         ▼
  3-Day Stability Buffer (waits 72h for community testing)
         │
         ▼
  Downgrade Guard (sort -V rejects older versions)
         │
         ▼
  VERSION file updated → Docker build triggered → pushed to GHCR
```

### Tag Filtering Examples

| Tag | Result | Reason |
|---|---|---|
| `2026.05.0` | ✅ Accepted | Pi-hole date-based release |
| `v2.1.3` | ✅ Accepted | Standard semver |
| `release-1.25.0` | ✅ Accepted | Unbound's official tag format |
| `v2.1.0-rc1` | ❌ Rejected | Blocklist: `rc` keyword |
| `v2.1.0-hotfix` | ❌ Rejected | Allowlist: suffix not numeric |
| `nightly-20240601` | ❌ Rejected | Blocklist: `nightly` keyword |
| `vTestTag` | ❌ Rejected | Allowlist: non-numeric content |

### Infrastructure Details

| Component | Detail |
|---|---|
| **Update Frequency** | Every 12 hours via GitHub Actions cron |
| **API Authentication** | `GITHUB_TOKEN` (auto-provided by GitHub, 5,000 req/hr) |
| **API Fallback** | Docker Hub Registry API if GitHub API is unreachable |
| **Network Resilience** | 3 retries with exponential backoff on all API calls |
| **Failure Mode** | Emits `::warning::` and exits cleanly — never fails red on transient errors |
| **Multi-Arch** | `linux/amd64`, `linux/arm64`, `linux/arm/v7` |
| **Build Trigger** | Changes to `VERSION`, `docker/`, or the workflow file itself |
| **Layer Cache** | GitHub Actions cache (`type=gha`) for fast multi-arch rebuilds |

---

## 📚 Reference & Support

### Pi-hole
| Resource | Link |
|---|---|
| Documentation | [docs.pi-hole.net](https://docs.pi-hole.net/) |
| Docker Image | [github.com/pi-hole/docker-pi-hole](https://github.com/pi-hole/docker-pi-hole) |
| Pi-hole + Unbound Guide | [docs.pi-hole.net/guides/dns/unbound](https://docs.pi-hole.net/guides/dns/unbound/) |
| Community Forum | [discourse.pi-hole.net](https://discourse.pi-hole.net/) |

### Unbound
| Resource | Link |
|---|---|
| Documentation | [unbound.docs.nlnetlabs.nl](https://unbound.docs.nlnetlabs.nl/) |
| Configuration Reference | [unbound.conf man page](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html) |
| GitHub | [github.com/NLnetLabs/unbound](https://github.com/NLnetLabs/unbound) |
| Troubleshooting | [Unbound Troubleshooting Guide](https://unbound.docs.nlnetlabs.nl/en/latest/getting-started/troubleshooting.html) |

### This Repository
| Resource | Link |
|---|---|
| Container Images | [GHCR Packages](https://github.com/teeesss/pihole-unbound-container/pkgs/container/pihole-unbound-container) |
| Build Logs | [Actions Tab](https://github.com/teeesss/pihole-unbound-container/actions) |
| Original Base | [mpgirro/docker-pihole-unbound](https://github.com/mpgirro/docker-pihole-unbound) |

---

*Maintained by the teeesss autonomous pipeline. For Pi-hole or Unbound product questions, please use the official support channels linked above.*
