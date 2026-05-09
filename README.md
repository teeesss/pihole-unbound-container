# Pi-hole + Unbound Container (Autonomous Fork)

This is an automated, single-container solution for Pi-hole and Unbound, forked from the `mpgirro` logic for networking stability but enhanced with a **"Set and Forget"** update engine.

## 🚀 Why this is better?

Most community images are either **stale** (manual updates) or **over-complex**. This fork takes a "Reliability First" approach:

### 1. The 3-Day Stability Buffer
We wait **3 days** after an official release before building. 
*   **Why?** To ensure your DNS infrastructure only pulls "matured" stable releases.

### 2. Auto-Updating Root Hints
Every build automatically downloads the latest `named.root` from Internic. 
*   **Result:** Maximum recursion accuracy for Unbound.

### 3. Dual-Stream Monitoring
The "Engine" monitors both Pi-hole releases AND Unbound package updates. 

---

## 🛠️ Configuration

You don't need to go elsewhere for documentation. Here is a baseline working configuration.

### Recommended `docker-compose.yml`

```yaml
services:
  pihole:
    image: ghcr.io/teeesss/pihole-unbound-container:latest
    container_name: pihole
    hostname: pihole
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "80:80/tcp" # Change local port if 80 is in use (e.g. 8088:80)
    environment:
      TZ: 'America/Chicago'
      PIHOLE_DNS_: '127.0.0.1#5335' # Point to internal Unbound
      DNSSEC: 'true'
    volumes:
      - './etc-pihole:/etc/pihole'
      - './etc-dnsmasq.d:/etc/dnsmasq.d'
    restart: unless-stopped
```

### Key Environment Variables
| Variable | Description | Recommended |
| :--- | :--- | :--- |
| `PIHOLE_DNS_` | Upstream DNS for Pi-hole | `127.0.0.1#5335` |
| `DNSSEC` | Enable DNSSEC validation | `true` |
| `TZ` | Your Timezone | e.g. `UTC` or `America/New_York` |

---

## ⏪ How to Rollback

If a new version causes issues, don't panic. This repository automatically creates **Versioned Tags** for every build.

1.  **Find the version**: Go to the [Packages Section](https://github.com/teeesss/pihole-unbound-container/pkgs/container/pihole-unbound-container) of this repo.
2.  **Pick a tag**: Find a previous working tag (e.g., `2026.04.1`).
3.  **Update Compose**:
    ```yaml
    image: ghcr.io/teeesss/pihole-unbound-container:2026.04.1
    ```
4.  **Pull and Restart**:
    ```bash
    docker pull ghcr.io/teeesss/pihole-unbound-container:2026.04.1
    docker-compose up -d
    ```

---

## 🤖 Automation Details
- **Update Checker**: Runs every 12 hours.
- **Multi-Arch Support**: Built for `x86_64`, `ARM64` (Pi 4/5), and `ARMv7` (Pi 3).
- **Healthchecks**: Built-in support for checking both Pi-hole and Unbound availability.

---
*Maintained by the teeesss autonomous pipeline.*
