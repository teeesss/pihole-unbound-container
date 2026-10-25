#!/bin/ash
set -e

# Ensure Unbound state, run, and log directories exist with correct ownership
mkdir -p /var/log/unbound /var/run/unbound /var/lib/unbound
chown -R unbound:unbound /var/log/unbound /var/run/unbound /var/lib/unbound

# ── Cold-Boot Time Resuscitation (Prevents Raspberry Pi DNSSEC Deadlock) ──
sync_clock_if_skewed() {
    # Check if user opted out
    if [ "${AUTO_TIME_SYNC:-true}" = "false" ] || [ "${AUTO_TIME_SYNC:-true}" = "0" ]; then
        echo "  [i] AUTO_TIME_SYNC is disabled by user; skipping clock check."
        return 0
    fi

    local current_year
    current_year=$(date -u +%Y 2>/dev/null || echo "1970")

    local build_year
    build_year=$(cat /etc/build_year 2>/dev/null || echo "2026")

    # If clock is at or ahead of image build year (and not corrupted past 2038), time is valid; do nothing
    if [ "$current_year" -ge "$build_year" ] && [ "$current_year" -le 2038 ] 2>/dev/null; then
        return 0
    fi

    echo "  [!] WARNING: System clock ($current_year) is behind image build year ($build_year). DNSSEC validation will fail."
    echo "  [i] Initiating cold-boot clock resuscitation via raw IP (DNS-free)..."

    local custom_ips="" router_ip="" anycast_ips=""

    # 1. Custom user-supplied IPs take highest priority
    if [ -n "${CUSTOM_NTP_IPS:-}" ]; then
        custom_ips="$CUSTOM_NTP_IPS"
    fi

    # 2. Local default gateway. Used for NTP before anycast, and for HTTP only after anycast.
    router_ip=$(ip route 2>/dev/null | awk '/default/ {print $3}' | head -n1 || true)

    # 3. Built-in Tier-1 Anycast IPs from config file
    if [ -f /etc/unbound/ntp-servers.conf ]; then
        anycast_ips=$(grep -v '^#' /etc/unbound/ntp-servers.conf | cut -d'|' -f3 | tr '\n' ' ' || true)
    fi

    # Fallback hardcoded defaults if nothing else is available
    if [ -z "$custom_ips" ] && [ -z "$router_ip" ] && [ -z "$anycast_ips" ]; then
        anycast_ips="162.159.200.1 162.159.200.123 216.239.35.0 216.239.35.4 129.6.15.28 132.163.96.1 17.253.34.253 17.253.2.43 40.119.6.228 168.61.215.74"
    fi

    clock_year_ok() {
        local new_year
        new_year=$(date -u +%Y 2>/dev/null || echo "1970")
        if [ "$new_year" -ge 2025 ] && [ "$new_year" -le 2038 ]; then
            return 0
        fi
        return 1
    }

    try_ntp() {
        echo -n "  [➔] Attempting NTP via $1... "
        if busybox ntpd -q -n -p "$1" 2>/dev/null && clock_year_ok; then
            echo "SUCCESS (NTP UDP:123)"
            return 0
        fi
        echo "FAILED"
        return 1
    }

    try_http_date() {
        local http_date
        echo -n "  [➔] Attempting HTTP Date via $1... "
        http_date=$(wget -S --spider --timeout=3 "http://$1" 2>&1 | grep -i '^[[:space:]]*Date:' | head -n1 | sed -e 's/^[[:space:]]*[Dd]ate:[[:space:]]*//' || true)
        if [ -n "$http_date" ] && date -u -s "$http_date" >/dev/null 2>&1 && clock_year_ok; then
            echo "SUCCESS (HTTP Date:80)"
            return 0
        fi
        echo "FAILED"
        return 1
    }

    local synced=false
    local ip

    # Pass 1 is NTP only. Router NTP stays ahead of anycast NTP.
    # A router web page must not answer before the Tier-1 NTP servers are tried.
    for ip in $custom_ips $router_ip $anycast_ips; do
        [ -z "$ip" ] && continue
        if try_ntp "$ip"; then
            synced=true
            break
        fi
    done

    # Pass 2 is HTTP Date, and only after every NTP attempt. Anycast before the router.
    if [ "$synced" != "true" ]; then
        for ip in $custom_ips $anycast_ips $router_ip; do
            [ -z "$ip" ] && continue
            if try_http_date "$ip"; then
                synced=true
                break
            fi
        done
    fi

    if [ "$synced" = "true" ]; then
        echo "  [✓] System clock recovered successfully: $(date -u)"
    else
        echo "  [!] WARNING: Unable to synchronize clock. If DNS fails, verify WAN connection or set clock manually."
    fi
}

# Run cold-boot clock recovery before initializing DNSSEC
sync_clock_if_skewed

# Initialize or refresh DNSSEC root trust anchor (RFC 5011)
if [ ! -s /var/lib/unbound/root.key ]; then
    echo "  [i] Initializing DNSSEC root trust anchor..."
    /usr/sbin/unbound-anchor -a /var/lib/unbound/root.key || true
    chown unbound:unbound /var/lib/unbound/root.key 2>/dev/null || true
fi

# Fallback: Download root hints if missing or empty
if [ ! -s /var/lib/unbound/root.hints ]; then
    echo "  [i] Downloading root hints..."
    wget --timeout=15 --tries=3 -O /var/lib/unbound/root.hints https://www.internic.net/domain/named.root || true
    chown unbound:unbound /var/lib/unbound/root.hints 2>/dev/null || true
fi

# Pre-flight Unbound configuration check
echo "  [i] Validating Unbound configuration..."
if ! /usr/sbin/unbound-checkconf /etc/unbound/unbound.conf; then
    echo "  [!] ERROR: Unbound configuration validation failed!" >&2
    exit 1
fi

# Start Unbound daemon in background
echo "  [i] Starting Unbound daemon"
/usr/sbin/unbound -d -c /etc/unbound/unbound.conf &
UNBOUND_PID=$!

# Verify Unbound is running
sleep 1
if ps -p "$UNBOUND_PID" > /dev/null 2>&1; then
    echo "  [i] Unbound started successfully with PID $UNBOUND_PID"
else
    echo "  [!] ERROR: Unbound failed to start. Review container output above for details." >&2
    exit 1
fi

# Hand over to original Pi-hole entrypoint
exec /usr/bin/start.sh
