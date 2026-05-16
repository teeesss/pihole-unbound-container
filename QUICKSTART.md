# Quickstart Guide

## 1. Local Deployment
Run the automated installer on your Linux VM:
```bash
cd local-deploy
sudo ./install.sh
```

## 2. Docker Compose Setup
Create a `docker-compose.yml`:
```yaml
services:
  pihole:
    image: ghcr.io/teeesss/pihole-unbound-container:latest
    container_name: pihole
    environment:
      TZ: 'America/Chicago'
      PIHOLE_DNS_: '127.0.0.1#5335'
    volumes:
      - './etc-pihole:/etc/pihole'
      - './etc-dnsmasq.d:/etc/dnsmasq.d'
    restart: unless-stopped
```

## 3. Verify Operation
Check if DNS recursion is working:
```bash
docker exec -it pihole dig @127.0.0.1 -p 5335 google.com
```

Check if DNSSEC is validating:
```bash
docker exec -it pihole dig @127.0.0.1 -p 5335 sigok.verteiltesysteme.net
```
Look for the `ad` (Authentic Data) flag.
