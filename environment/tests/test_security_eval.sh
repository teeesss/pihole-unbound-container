#!/bin/bash
# Bash-level unit tests for update-checker security parsing & threshold logic
set -euo pipefail

PASS_COUNT=0
FAIL_COUNT=0

assert_eq() {
  local expected="$1"
  local actual="$2"
  local msg="$3"
  if [ "$expected" = "$actual" ]; then
    echo "  [PASS] $msg"
    PASS_COUNT=$(( PASS_COUNT + 1 ))
  else
    echo "  [FAIL] $msg (Expected '$expected', got '$actual')"
    FAIL_COUNT=$(( FAIL_COUNT + 1 ))
  fi
}

# ── Functions under test ───────────────────────────────────────────────────

is_security_release() {
  local text="$1"
  echo "$text" | grep -Eiq "CVE-[0-9]{4}-[0-9]+|\b(critical|high)[ -]severit|severity:\s*(critical|high)|\brce\b|remote[ -]code[ -]execution|denial[ -]of[ -]service|\bDoS\b|dnssec[ -]bypass|cache[ -]poisoning|\bpoisoning\b|\bspoofing\b|buffer[ -]overflow|memory[ -]corruption|privilege[ -]escalation|arbitrary[ -]code|vulnerabilit(y|ies)|security[ -](patch|fix|update|advisory|issue)|zero-day|0-day"
}

extract_security_reason() {
  local text="$1"
  local cve
  cve=$(echo "$text" | grep -Eio "CVE-[0-9]{4}-[0-9]+" || true)
  cve=$(echo "$cve" | sed -n '1p')
  if [ -n "$cve" ]; then
    echo "CVE detected: $(echo "$cve" | tr '[:lower:]' '[:upper:]')"
    return
  fi
  local kw
  kw=$(echo "$text" | grep -Eio "\b(critical|high)[ -]severit|\brce\b|remote[ -]code[ -]execution|denial[ -]of[ -]service|\bDoS\b|dnssec[ -]bypass|cache[ -]poisoning|\bpoisoning\b|\bspoofing\b|buffer[ -]overflow|memory[ -]corruption|privilege[ -]escalation|vulnerabilit[a-z]*|security[ -][a-z]+" || true)
  kw=$(echo "$kw" | sed -n '1p')
  if [ -n "$kw" ]; then
    echo "Security indicator: $kw"
    return
  fi
  echo "Security alert"
}

get_threshold_seconds() {
  local text="$1"
  local override_hours="${2:-0}"
  local force_immediate="${3:-false}"

  if [ "$force_immediate" = "true" ]; then
    echo 0
    return
  fi
  if [ "$override_hours" -gt 0 ] 2>/dev/null; then
    echo $(( override_hours * 3600 ))
    return
  fi
  if is_security_release "$text"; then
    echo 43200 # 12 hours
  else
    echo 86400 # 24 hours
  fi
}

echo "Running update-checker bash unit tests..."

# Test 1: CVE pattern detection
if is_security_release "Fix CVE-2026-35501 island trust anchor bypass"; then
  assert_eq "0" "0" "CVE-2026-35501 identified as security release"
else
  assert_eq "0" "1" "CVE-2026-35501 identified as security release"
fi

REASON=$(extract_security_reason "Fix CVE-2026-35501 island trust anchor bypass")
assert_eq "CVE detected: CVE-2026-35501" "$REASON" "CVE extraction formatted correctly"

# Test 2: High severity keywords
if is_security_release "High severity memory corruption in resolver"; then
  assert_eq "0" "0" "High severity keyword identified"
else
  assert_eq "0" "1" "High severity keyword identified"
fi

# Test 3: Standard clean release
if is_security_release "feat: add dark mode and translation updates"; then
  assert_eq "0" "1" "Standard release not flagged as security"
else
  assert_eq "0" "0" "Standard release not flagged as security"
fi

# Test 4: Threshold calculations
SEC_THRESH=$(get_threshold_seconds "Fix CVE-2026-35501" 0 false)
assert_eq "43200" "$SEC_THRESH" "Security release gets 12h (43200s)"

STD_THRESH=$(get_threshold_seconds "feat: normal update" 0 false)
assert_eq "86400" "$STD_THRESH" "Standard release gets 24h (86400s)"

OVR_THRESH=$(get_threshold_seconds "feat: normal update" 6 false)
assert_eq "21600" "$OVR_THRESH" "Manual override 6h respected (21600s)"

FORCE_THRESH=$(get_threshold_seconds "Fix CVE-2026-35501" 0 true)
assert_eq "0" "$FORCE_THRESH" "Force immediate sets threshold to 0s"

# Test 5: Real-world Unbound 1.26.2 payload
UNBOUND_PAYLOAD="- Fix CVE-2026-35501, Bypass of a configured island trust anchor underneath an insecure parent from an attacker-controlled NSEC record."
if is_security_release "$UNBOUND_PAYLOAD"; then
  assert_eq "0" "0" "Unbound 1.26.2 payload recognized as security release"
else
  assert_eq "0" "1" "Unbound 1.26.2 payload recognized as security release"
fi
UNBOUND_THRESH=$(get_threshold_seconds "$UNBOUND_PAYLOAD" 0 false)
assert_eq "43200" "$UNBOUND_THRESH" "Unbound 1.26.2 gets 12h threshold"

echo "----------------------------------------"
echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed."
[ "$FAIL_COUNT" -eq 0 ] || exit 1
