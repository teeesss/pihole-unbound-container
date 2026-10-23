# Test Results

## Latest Run: 2026-10-23 (All Passed - 100%)

### Summary
| Test Suite | Total Tests | Passed | Failed | Status |
| :--- | :--- | :--- | :--- | :--- |
| `environment/tests/test_container_config.py` | 23 | 23 | 0 | ✅ PASS |
| `environment/tests/test_security_eval.py` | 6 | 6 | 0 | ✅ PASS |
| `environment/tests/test_security_eval.sh` | 10 | 10 | 0 | ✅ PASS |

---

### Detailed Test Breakdown

#### 1. Python Container Configuration, Hardening & NTP Recovery (`test_container_config.py`)
- `test_serve_expired_rfc8767`: ✅ PASS (RFC 8767 serve-expired, 86400s TTL, 1800ms client timeout verified)
- `test_prefetch_and_prefetch_key`: ✅ PASS (Cache prefetch and DNSKEY prefetching enabled)
- `test_cache_and_buffer_sizing`: ✅ PASS (msg-cache 64m, rrset-cache 128m, socket buffers 4m, num-queries-per-thread 4096 verified)
- `test_dnssec_and_root_anchor`: ✅ PASS (RFC 5011 auto-trust-anchor-file, harden-dnssec-stripped verified)
- `test_privacy_and_hardening`: ✅ PASS (hide-identity, hide-version, nxdomain cut, ACLs verified)
- `test_bind_tools_installed`: ✅ PASS (bind-tools present in Dockerfile runtime stage)
- `test_libunbound_shared_library_copied`: ✅ PASS (libunbound.so* copied to runtime stage)
- `test_binary_stripping_in_builder`: ✅ PASS (strip command in builder stage verified)
- `test_safe_root_hints_download`: ✅ PASS (root.hints size assertion verified)
- `test_legacy_lighttpd_removed`: ✅ PASS (legacy lighttpd copy removed from Dockerfile)
- `test_dynamic_build_year_generated`: ✅ PASS (/etc/build_year generated dynamically in Dockerfile)
- `test_entrypoint_uses_build_year`: ✅ PASS (custom-entrypoint.sh compares against /etc/build_year floor)
- `test_entrypoint_checks_local_router_gateway`: ✅ PASS (dynamically extracts default gateway via ip route)
- `test_tier1_providers_present`: ✅ PASS (5 Tier-1 providers: Cloudflare, Google, NIST, Apple, Microsoft)
- `test_ip_format_validity`: ✅ PASS (all provider Anycast IPs strictly valid IPv4 syntax)
- `test_preflight_checkconf`: ✅ PASS (unbound-checkconf pre-flight in entrypoint verified)
- `test_root_anchor_initialization`: ✅ PASS (unbound-anchor initialization in entrypoint verified)
- `test_fail_fast_on_startup_failure`: ✅ PASS (exit 1 fail-fast active on daemon start failure)
- `test_tag_triggers`: ✅ PASS (docker-publish.yml triggers on '20*' and 'v*')
- `test_gha_cache_efficiency`: ✅ PASS (single-arch test step avoids duplicate cache export)
- `test_ntp_pass_precedes_router_http`: ✅ PASS (Anycast NTP runs before router HTTP Date)
- `test_quick_start_uses_v6_upstream_and_sys_time`: ✅ PASS (README uses FTLCONF_dns_upstreams and SYS_TIME)

#### 2. Python Security & Decoupled Resolution (`test_security_eval.py`)
- `test_cve_pattern_detection`: ✅ PASS (Detected CVE patterns and extracted identifiers)
- `test_security_keywords`: ✅ PASS (Matched RCE, DoS, memory corruption, bypass, zero-day)
- `test_standard_release_clean`: ✅ PASS (No false positives on standard feature/translation releases)
- `test_threshold_overrides`: ✅ PASS (Verified 12h, 24h, custom override, and force immediate)
- `test_real_world_unbound_1_26_2`: ✅ PASS (Verified Unbound 1.26.2 CVE-2026-35501 triggers 12h and becomes READY at 13h)
- `test_decoupled_resolution_scenarios`: ✅ PASS (Verified independent promotion of Pi-hole and Unbound)

#### 3. Bash Workflow Function Tests (`test_security_eval.sh`)
- `CVE-2026-35501 identified as security release`: ✅ PASS
- `CVE extraction formatted correctly`: ✅ PASS
- `High severity keyword identified`: ✅ PASS
- `Standard release not flagged as security`: ✅ PASS
- `Security release gets 12h (43200s)`: ✅ PASS
- `Standard release gets 24h (86400s)`: ✅ PASS
- `Manual override 6h respected (21600s)`: ✅ PASS
- `Force immediate sets threshold to 0s`: ✅ PASS
- `Unbound 1.26.2 payload recognized as security release`: ✅ PASS
- `Unbound 1.26.2 gets 12h threshold`: ✅ PASS
