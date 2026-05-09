# Pi-hole + Unbound Container (Autonomous Fork)

This is an automated, single-container solution for Pi-hole and Unbound, forked from the `mpgirro` logic for networking stability but enhanced with a **"Set and Forget"** update engine.

> [!IMPORTANT]
> **Scope Disclaimer**: This repository exists to provide **automation** and **version parity**. It is not a support forum for general Pi-hole or Unbound troubleshooting. For functional help, see the [Reference & Support](#reference--support) section below.

## 🚀 Why this is better?

Most community images are either **stale** (manual updates) or **over-complex**. This fork takes a "Reliability First" approach:

### 1. The 3-Day Stability Buffer
We wait **3 days** after an official release before building. 
*   **Why?** To ensure your DNS infrastructure only pulls "matured" stable releases.

### 2. Auto-Updating Root Hints
Every build automatically downloads the latest `named.root` from Internic. 

### 3. Dual-Stream Monitoring
The "Engine" monitors both [Pi-hole Releases](https://github.com/pi-hole/docker-pi-hole/releases) AND Unbound package updates. 

---

## 🛠️ Configuration

### 1. Pi-hole DNS Settings
To use the integrated Unbound resolver, go to your Pi-hole Web UI:
1.  Navigate to **Settings** > **DNS**.
2.  Uncheck all boxes under "Upstream DNS Servers".
3.  In **Custom 1 (IPv4)**, enter: `127.0.0.1#5335`
4.  Click **Save**.

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

## ✅ Verification & Testing

### 1. Test Recursion
```bash
docker exec -it pihole dig @127.0.0.1 -p 5335 google.com
```
*   **Success**: Should return `status: NOERROR` and an IP address.

### 2. Test DNSSEC Validation
```bash
# This should work (Authentic Data)
docker exec -it pihole dig @127.0.0.1 -p 5335 sigok.verteiltesysteme.net

# This SHOULD FAIL (BOGUS signature)
docker exec -it pihole dig @127.0.0.1 -p 5335 sigfail.verteiltesysteme.net
```
*   **Success**: Look for the **`ad`** (Authentic Data) flag in the first result. 

---

## ⏪ How to Rollback

If a new version causes issues, use a versioned tag from the [Packages Section](https://github.com/teeesss/pihole-unbound-container/pkgs/container/pihole-unbound-container).

```bash
docker pull ghcr.io/teeesss/pihole-unbound-container:[VERSION_TAG]
```

---

## 📚 Reference & Support

If you have functional issues not related to this Docker build, please use these official resources:

*   **Pi-hole**: [Official Documentation](https://docs.pi-hole.net/) | [Support Forum](https://discourse.pi-hole.net/) | [GitHub Repo](https://github.com/pi-hole/docker-pi-hole)
*   **Unbound**: [Official Documentation](https://unbound.docs.nlnetlabs.nl/) | [Unbound GitHub](https://github.com/NLnetLabs/unbound)
*   **Base Logic**: This project's networking logic is based on the [mpgirro/docker-pihole-unbound](https://github.com/mpgirro/docker-pihole-unbound) project.

---

## 🤖 Automation Details
- **Update Checker**: Runs every 12 hours.
- **Multi-Arch Support**: Builds for `x86_64`, `ARM64`, and `ARMv7`.

---
*Maintained by the teeesss autonomous pipeline.*
