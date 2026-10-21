# Test Results

## Latest Run: 2026-10-21 (All Passed - 100%)

### Summary
| Test Suite | Total Tests | Passed | Failed | Status |
| :--- | :--- | :--- | :--- | :--- |
| `environment/tests/test_security_eval.py` | 6 | 6 | 0 | ✅ PASS |
| `environment/tests/test_security_eval.sh` | 10 | 10 | 0 | ✅ PASS |
| `local-deploy/install.sh (bash -n syntax)` | 1 | 1 | 0 | ✅ PASS |

---

### Detailed Test Breakdown

#### 1. Python Security & Decoupled Resolution (`test_security_eval.py`)
- `test_cve_pattern_detection`: ✅ PASS (Detected CVE patterns and extracted identifiers)
- `test_security_keywords`: ✅ PASS (Matched RCE, DoS, memory corruption, bypass, zero-day)
- `test_standard_release_clean`: ✅ PASS (No false positives on standard feature/translation releases)
- `test_threshold_overrides`: ✅ PASS (Verified 12h, 24h, custom override, and force immediate)
- `test_real_world_unbound_1_26_2`: ✅ PASS (Verified Unbound 1.26.2 CVE-2026-35501 triggers 12h and becomes READY at 13h)
- `test_decoupled_resolution_scenarios`: ✅ PASS (Verified independent promotion of Pi-hole and Unbound)

#### 2. Bash Workflow Function Tests (`test_security_eval.sh`)
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
