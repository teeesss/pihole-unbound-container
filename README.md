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
- **Unbound** — a validating, recursive DNS resolver. Compiled dynamically from source in a multi-stage Docker build to match the exact pinned version, rather than relying on stale distribution packages. It queries authoritative DNS servers directly instead of forwarding to a third-party provider like Google (`8.8.8.8`) or Cloudflare (`1.1.1.1`).

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
      TZ: 'America/Chicago'                          # Set to your timezone
      FTLCONF_webserver_api_password: 'changeme'     # Pi-hole v6 admin password
      PIHOLE_DNS_: '127.0.0.1#5335'                  # Points Pi-hole at the bundled Unbound
      FTLCONF_dns_dnssec: 'true'                     # Enable DNSSEC validation
    ports:
      - "53:53/tcp"                    # DNS (TCP)
      - "53:53/udp"                    # DNS (UDP)
      - "80:80/tcp"                    # Pi-hole web dashboard
    volumes:
      - './etc-pihole:/etc/pihole'           # Persistent Pi-hole config
      - './etc-dnsmasq.d:/etc/dnsmasq.d'     # Persistent dnsmasq config
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "dig @127.0.0.1 -p 5335 google.com +short && dig @127.0.0.1 google.com +short || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
```

> [!WARNING]
> Pi-hole v6 replaced the `WEBPASSWORD` environment variable with `FTLCONF_webserver_api_password`. If you are coming from an older guide, update your compose file accordingly. See the [Pi-hole v6 Docker documentation](https://github.com/pi-hole/docker-pi-hole) for all available `FTLCONF_` variables.

### 2. Start the Container

```bash
docker compose up -d
```

### 3. Access the Dashboard

Open `http://<HOST_IP>/admin` in your browser and log in with the password you set above.

> [!TIP]
> If port 80 is occupied by another service, Pi-hole's embedded web server (FTL) will automatically fall back to port **8080**. Try `http://<HOST_IP>:8080/admin` if the default doesn't respond.

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
> For IPv6 guidance, see the [Pi-hole documentation](https://docs.pi-hole.net/) and the [Unbound configuration reference](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html).

### ⏱️ Cold-Boot DNSSEC & Time Recovery (Raspberry Pi & SBCs)

#### The Problem: The "Chicken-and-Egg" Deadlock
Single-board computers like the **Raspberry Pi lack a hardware battery-backed Real-Time Clock (RTC)**. When power is lost or the device is cold-booted:
1. The host system clock resets to 1970 (or the last saved timestamp).
2. Unbound starts up with DNSSEC validation enforced (`harden-dnssec-stripped: yes`).
3. DNSSEC compares the digital signatures (`RRSIG`) of upstream domains against the local system clock. Because the system clock is in 1970, all signatures are evaluated as expired or not yet valid, causing Unbound to return `SERVFAIL` on **every single DNS query**.
4. The host OS's NTP daemon attempts to sync the clock by resolving `pool.ntp.org` via Pi-hole (`127.0.0.1`).
5. Because DNS is dead, NTP cannot resolve the time servers. Because time cannot sync, DNS remains permanently dead.

#### The Autonomous Solution
To eliminate this deadlock without forcing users to rely on commercial DNS forwarders (1.1.1.1, 8.8.8.8), the container includes an autonomous, guarded clock-recovery mechanism in its entrypoint:

1. **Guarded Execution**: The recovery script checks if the system clock year is behind the image build year (`/etc/build_year`). **If your system time is already current (normal boot), this function exits in milliseconds with zero network requests.**
2. **Local Router First**: The container dynamically checks your local router's default gateway IP (queried from the kernel routing table, whether `192.168.1.1`, `10.0.0.1`, or `172.16.0.1`). If your router runs an NTP service, time syncs directly on your local LAN with **zero external Internet queries**.
3. **Multi-Vendor Anycast Fallback**: If the local router does not serve NTP, the container queries 5 globally distributed, multi-vendor Tier-1 Anycast time servers via raw IP (DNS-free):
   - **Cloudflare**: `162.159.200.1` (`time.cloudflare.com`)
   - **Google**: `216.239.35.0` (`time.google.com`)
   - **NIST (US Gov Atomic Clock)**: `129.6.15.28` (`time.nist.gov`)
   - **Apple**: `17.253.34.253` (`time.apple.com`)
   - **Microsoft**: `40.119.6.228` (`time.windows.com`)
4. **Dual-Protocol**: Attempts standard NTP over UDP port 123. If blocked by an outbound firewall, it falls back to HTTP `Date:` header extraction over standard TCP port 80.
5. **Automated CI Maintenance**: Our GitHub Actions pipeline continuously resolves upstream time hostnames and auto-updates the IP list if providers ever migrate subnets.

#### Privacy & Opt-Out Controls
If you operate in an air-gapped environment or prefer to manage system time exclusively through host tools:

- **Disable entirely**: Set `AUTO_TIME_SYNC=false` in your `docker-compose.yml` or `.env`:
  ```yaml
  environment:
    - AUTO_TIME_SYNC=false
  ```
- **Use internal corporate/homelab NTP**: Specify your own private NTP server IPs:
  ```yaml
  environment:
    - CUSTOM_NTP_IPS=192.168.1.1 10.0.0.5
  ```

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
> For the complete list of Unbound options, see the [unbound.conf man page](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html). For performance tuning tips, see the [Unbound Performance Tuning guide](https://unbound.docs.nlnetlabs.nl/en/latest/topics/core/performance.html).

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

## ⏪ Rollback & Version Pinning

All versioned images are published to the [GitHub Container Registry](https://github.com/teeesss/pihole-unbound-container/pkgs/container/pihole-unbound-container). 

> [!NOTE]
> Pi-hole versions follow the date-based tags of the official [pi-hole/docker-pi-hole releases](https://github.com/pi-hole/docker-pi-hole/releases) (e.g., `2026.05.0`), not the core Pi-hole application version (e.g., `v6.4.2`). Unbound versions follow the official [NLnetLabs/unbound tags](https://github.com/NLnetLabs/unbound/tags) (e.g. `1.25.1`).

Following container best practices, images are tagged with both upstream versions combined (`[PIHOLE_VERSION]-[UNBOUND_VERSION]`) to guarantee immutable, reproducible deployments.

To pin to a specific version:

```yaml
# In your docker-compose.yml
image: ghcr.io/teeesss/pihole-unbound-container:2026.10.0-1.26.2
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
| No `ad` flag on DNSSEC queries | DNSSEC not enabled | Verify `FTLCONF_dns_dnssec: 'true'` is set in your environment |
| Dashboard unreachable on port 80 | Port 80 conflict | Try port 8080 (`http://<IP>:8080/admin`) — FTL auto-fallback |
| Slow first query after restart | Normal Unbound behavior | Unbound has an empty cache on startup — it warms up within minutes |
| Password not working after upgrade | Pi-hole v6 env var change | Replace `WEBPASSWORD` with `FTLCONF_webserver_api_password` |

> [!NOTE]
> For detailed help, see the [Pi-hole FAQ](https://docs.pi-hole.net/) and the [Unbound documentation](https://unbound.docs.nlnetlabs.nl/en/latest/).

---

## 🤖 Automation Architecture

This repository is **fully autonomous** and handles dependencies robustly. The pipeline checks for new stable upstream releases of **either** Pi-hole or Unbound hourly. If a new version of either package is detected, an adaptive security evaluation classifies the release and applies an appropriate cooling buffer before automated promotion.

### Release Timelines & Buffers

| Tier | Window | Trigger Criteria | Target Scenario |
|---|---|---|---|
| 🚨 **Security Fast-Track** | **12 Hours** | Upstream release notes or git commit messages contain CVE IDs (`CVE-\d{4}-\d+`) or critical keywords: `critical`, `security vulnerability`, `remote code execution`, `rce`, `denial of service`, `dos`, `dnssec bypass`, `cache poisoning`, `buffer overflow`, `memory corruption`, `zero-day` | Active vulnerability patches (e.g. Unbound `1.26.2` fixing `CVE-2026-35501`) |
| ⏱️ **Standard Baseline** | **24 Hours** | Normal feature, maintenance, or non-critical bugfix releases without security flags | Routine upstream updates; allows 24h for upstream community bug detection |
| ⚡ **Emergency Bypass** | **0 Hours** | Manual workflow dispatch (`force_immediate: true`) or custom `override_buffer_hours` | Zero-day immediate deployment without waiting for cooling buffers |

> [!TIP]
> **Decoupled Promotion**: Pi-hole and Unbound version lifecycles are evaluated independently. If one component is currently cooling, the other is never blocked and promotes immediately when its own cooling window clears.

### Update Pipeline

```
GitHub Actions (hourly cron: 0 * * * *)
         │
         ▼
  fetch_release() ─── GitHub Releases API (Pi-hole)
         │        ─── GitHub Tags + Commit API (Unbound)
         │              └── Docker Hub Registry API (fallback)
         ▼
  ┌─ Adaptive Security & Decoupled Buffer ────────────────┐
  │  Independent evaluation per component:               │
  │  - Critical CVE / High Severity: 12-Hour Fast-Track   │
  │  - Routine Features / Bugfixes: 24-Hour Baseline      │
  │  - Manual Zero-Day Override: 0-Hour Immediate         │
  └───────────────────────────────────────────────────────┘
         │
         ▼
  Downgrade Guard (sort -V rejects older versions)
         │
         ▼
  VERSION file updated → Git Tag & GitHub Release created → Triggers reusable build workflow
         │
         ▼
  ┌─ Compatibility & Integration Testing Guard ──────────┐
  │  1. Spin up built container image locally in runner  │
  │  2. Run unbound-checkconf to verify configurations    │
  │  3. Verify compiled Unbound version matches target   │
  │  4. Query Unbound directly (port 5335) for recursion  │
  │  5. Query Pi-hole (port 53) to verify end-to-end     │
  │     recursive resolution via Unbound                 │
  └──────────────────────────────────────────────────────┘
         │
         ▼
  Multi-Arch Image published to GHCR (linux/amd64, linux/arm64)
```

### Tag Filtering Examples

| Tag | Result | Reason |
|---|---|---|
| `2026.10.0` | ✅ Accepted | Pi-hole date-based release (`YYYY.MM.N`) |
| `v2.1.3` | ✅ Accepted | Standard semver |
| `release-1.26.2` | ✅ Accepted | Unbound's official tag format (`release-X.Y.Z`) |
| `v2.1.0-rc1` | ❌ Rejected | Blocklist: `rc` keyword |
| `v2.1.0-hotfix` | ❌ Rejected | Allowlist: suffix not numeric |
| `nightly-20240601` | ❌ Rejected | Blocklist: `nightly` keyword |
| `vTestTag` | ❌ Rejected | Allowlist: non-numeric content |

> [!NOTE]
> **Complete Blocklist (Case-Insensitive)**:
> `alpha`, `beta`, `canary`, `debug`, `dev`, `devel`, `development`, `edge`, `experimental`, `insiders`, `next`, `nightly`, `pre-`, `pre.`, `preview`, `rc`, `rh`, `snapshot`, `temp`, `test`, `tmp`, `unstable`

### Infrastructure & Resilience

| Component | Detail |
|---|---|
| **Update Frequency** | Hourly via GitHub Actions cron (`0 * * * *`) |
| **API Authentication** | `GITHUB_TOKEN` (authenticated, 5,000 req/hr) |
| **Multi-Source Resolution** | GitHub Releases (Pi-hole), GitHub Tags + Commit API (Unbound), Docker Hub Registry fallback |
| **Upstream Scraper** | NLnetLabs publishes Git tags without Release objects; checker parses `/commits/{ref}` for accurate commit dates and CVE changelog extraction |
| **Testing Harness** | Unit test suites in `environment/tests/` (Python + Bash) validate CVE regex parsing, security classification, and threshold calculation |
| **Network Resilience** | 3 retries with exponential backoff on all API calls |
| **Failure Mode** | Emits `::warning::` and exits cleanly — never fails red on transient errors |
| **Multi-Arch** | `linux/amd64`, `linux/arm64` compiled from source |
| **Build Trigger** | Pushes to Git Tags matching `20*` or `v*`, manual dispatch, or reusable workflow call from `update-checker` |
| **Layer Cache** | GitHub Actions cache (`type=gha`) for fast multi-arch rebuilds |

---

## 🛠️ Local Deployment & Maintenance

For Linux hosts, Raspberry Pis, or home server environments, an automated interactive setup and maintenance tool is provided in `local-deploy/install.sh`:

- **Interactive Management**: 17 built-in operations (fresh install, container updates, diagnostics, password changes, adlist/domain imports, DNSSEC tests, log streaming).
- **Dual-Daemon Health Verification**: Verifies both internal Unbound recursive resolution (`127.0.0.1#5335`) and the Pi-hole DNS sinkhole (`127.0.0.1#53`).
- **Automated Stale Image Pruning**: Automatically runs `docker image prune -f` after updates to reclaim storage on flash storage devices (SD cards, eMMC).
- **Host Port 53 Stub Handler**: Automatically frees port 53 by managing the host `systemd-resolved` stub listener safely.

---

## 📚 Reference & Support

### Pi-hole
| Resource | Link |
|---|---|
| Documentation | [docs.pi-hole.net](https://docs.pi-hole.net/) |
| Docker Image & v6 Env Vars | [github.com/pi-hole/docker-pi-hole](https://github.com/pi-hole/docker-pi-hole) |
| Pi-hole + Unbound Guide | [docs.pi-hole.net/guides/dns/unbound](https://docs.pi-hole.net/guides/dns/unbound/) |
| Community Forum | [discourse.pi-hole.net](https://discourse.pi-hole.net/) |

### Unbound
| Resource | Link |
|---|---|
| Documentation | [unbound.docs.nlnetlabs.nl](https://unbound.docs.nlnetlabs.nl/) |
| Configuration Reference | [unbound.conf man page](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html) |
| Performance Tuning | [Performance Tuning Guide](https://unbound.docs.nlnetlabs.nl/en/latest/topics/core/performance.html) |
| GitHub | [github.com/NLnetLabs/unbound](https://github.com/NLnetLabs/unbound) |

### This Repository
| Resource | Link |
|---|---|
| Container Images | [GHCR Packages](https://github.com/teeesss/pihole-unbound-container/pkgs/container/pihole-unbound-container) |
| Build Logs | [Actions Tab](https://github.com/teeesss/pihole-unbound-container/actions) |
| Original Base | [mpgirro/docker-pihole-unbound](https://github.com/mpgirro/docker-pihole-unbound) |

---

*Maintained by the teeesss autonomous pipeline. For Pi-hole or Unbound product questions, please use the official support channels linked above.*
