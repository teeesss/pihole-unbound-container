#!/usr/bin/env python3
"""
Unit and integration tests for Upstream Security Evaluation and Adaptive Buffer.
Tests CVE identification, security severity keyword detection, threshold calculation (12h vs 24h),
and decoupled version promotion.
"""

import re
import unittest
from datetime import datetime, timezone

# ── Security Evaluation Engine ───────────────────────────────────────────────

SECURITY_PATTERN = re.compile(
    r"(?i)(CVE-[0-9]{4}-[0-9]+|"
    r"\b(critical|high)[ -]severit|"
    r"severity:\s*(critical|high)|"
    r"\brce\b|remote\s+code\s+execution|"
    r"denial\s+of\s+service|\bDoS\b|"
    r"dnssec\s+bypass|cache\s+poisoning|\bpoisoning\b|\bspoofing\b|"
    r"buffer\s+overflow|memory\s+corruption|privilege\s+escalation|arbitrary\s+code|"
    r"vulnerabilit(y|ies)|security\s+(patch|fix|update|advisory|issue)|"
    r"zero-day|0-day)"
)

CVE_PATTERN = re.compile(r"CVE-[0-9]{4}-[0-9]+", re.IGNORECASE)


def is_security_release(text: str) -> bool:
    """Return True if text contains security vulnerability indicators or CVEs."""
    if not text:
        return False
    return bool(SECURITY_PATTERN.search(text))


def extract_security_reason(text: str) -> str:
    """Extract human-readable security reason from release text."""
    if not text:
        return "Standard Release"
    cve_match = CVE_PATTERN.search(text)
    if cve_match:
        return f"CVE detected: {cve_match.group(0).upper()}"
    sec_match = SECURITY_PATTERN.search(text)
    if sec_match:
        return f"Security indicator: {sec_match.group(0)}"
    return "Standard Release"


def calculate_threshold(text: str, override_hours: int = 0, force_immediate: bool = False) -> int:
    """
    Calculate buffer threshold in seconds:
    - force_immediate -> 0s
    - override_hours > 0 -> override_hours * 3600
    - is_security_release -> 12 hours (43200s)
    - standard -> 24 hours (86400s)
    """
    if force_immediate:
        return 0
    if override_hours > 0:
        return override_hours * 3600
    if is_security_release(text):
        return 43200  # 12 hours
    return 86400  # 24 hours


def evaluate_component(
    component_name: str,
    candidate_ver: str,
    current_ver: str,
    release_date_iso: str,
    release_text: str,
    now_epoch: int,
    override_hours: int = 0,
    force_immediate: bool = False,
) -> dict:
    """Evaluate whether candidate version is stable/ready for promotion."""
    if candidate_ver == current_ver:
        return {
            "component": component_name,
            "version": current_ver,
            "ready": True,
            "is_new": False,
            "threshold_hours": 0,
            "age_hours": 0,
            "reason": "Current version up to date",
        }

    dt = datetime.fromisoformat(release_date_iso.replace("Z", "+00:00"))
    release_epoch = int(dt.timestamp())
    age_seconds = max(0, now_epoch - release_epoch)
    age_hours = age_seconds // 3600

    threshold_seconds = calculate_threshold(release_text, override_hours, force_immediate)
    threshold_hours = threshold_seconds // 3600

    ready = age_seconds >= threshold_seconds
    is_sec = is_security_release(release_text)
    reason = extract_security_reason(release_text) if is_sec else "Standard release"

    return {
        "component": component_name,
        "candidate": candidate_ver,
        "current": current_ver,
        "ready": ready,
        "is_new": True,
        "is_security": is_sec,
        "threshold_hours": threshold_hours,
        "age_hours": age_hours,
        "remaining_hours": max(0, (threshold_seconds - age_seconds) // 3600) if not ready else 0,
        "reason": f"⚡ Security Fast-Track (12h): {reason}" if is_sec else "Standard Release (24h)",
    }


def resolve_versions(pi_eval: dict, unbound_eval: dict) -> dict:
    """Decoupled promotion resolver."""
    target_pi = pi_eval.get("candidate") if pi_eval.get("is_new") and pi_eval.get("ready") else pi_eval.get("current")
    target_unbound = unbound_eval.get("candidate") if unbound_eval.get("is_new") and unbound_eval.get("ready") else unbound_eval.get("current")

    has_promotions = (target_pi != pi_eval.get("current")) or (target_unbound != unbound_eval.get("current"))
    has_pending = (pi_eval.get("is_new") and not pi_eval.get("ready")) or (
        unbound_eval.get("is_new") and not unbound_eval.get("ready")
    )

    return {
        "target_pi": target_pi,
        "target_unbound": target_unbound,
        "promote": has_promotions,
        "pending": has_pending,
    }


# ── Test Suite ───────────────────────────────────────────────────────────────

class TestSecurityEvaluation(unittest.TestCase):

    def test_cve_pattern_detection(self):
        """Verify CVE detection catches various CVE formats."""
        self.assertTrue(is_security_release("Fix CVE-2026-35501 in trust anchor validator"))
        self.assertTrue(is_security_release("Addresses cve-2024-99999"))
        self.assertTrue(is_security_release("[SECURITY] Multiple fixes including CVE-2025-1001"))
        self.assertEqual(extract_security_reason("Fix CVE-2026-35501"), "CVE detected: CVE-2026-35501")

    def test_security_keywords(self):
        """Verify high severity keywords trigger security release classification."""
        cases = [
            "Fixed remote code execution in DNS parser",
            "High severity vulnerability in query handling",
            "Mitigate denial of service attack vectors",
            "Fix DNSSEC bypass under insecure parent delegation",
            "Prevent DNS cache poisoning vulnerability",
            "Remediates buffer overflow in FTL logging",
            "Critical security update for DNSSEC validator",
            "Zero-day advisory patch for root recursion",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertTrue(is_security_release(case), f"Failed for: {case}")
                self.assertEqual(calculate_threshold(case), 43200)

    def test_standard_release_clean(self):
        """Verify normal feature/bugfix releases are classified as standard (24h)."""
        cases = [
            "feat: Add dark mode toggle in admin settings",
            "chore: Update German and Spanish translations",
            "fix: Typo in install prompt and help command",
            "bump: Update Alpine base image from 3.20 to 3.21",
            "perf: Cache recent client stats in memory",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertFalse(is_security_release(case), f"False positive for: {case}")
                self.assertEqual(calculate_threshold(case), 86400)

    def test_threshold_overrides(self):
        """Verify manual override and force immediate parameters."""
        text = "feat: some normal release"
        self.assertEqual(calculate_threshold(text, force_immediate=True), 0)
        self.assertEqual(calculate_threshold(text, override_hours=6), 21600)

        sec_text = "Fix CVE-2026-35501"
        self.assertEqual(calculate_threshold(sec_text, force_immediate=True), 0)
        self.assertEqual(calculate_threshold(sec_text, override_hours=4), 14400)

    def test_real_world_unbound_1_26_2(self):
        """Verify exact NLnetLabs Unbound 1.26.2 commit payload."""
        payload = (
            "- Fix CVE-2026-35501, Bypass of a configured island trust anchor\n"
            "  underneath an insecure parent from an attacker-controlled NSEC\n"
            "  record. Thanks to Qifan Zhang from Palo Alto Networks for the\n"
            "  report."
        )
        self.assertTrue(is_security_release(payload))
        self.assertEqual(calculate_threshold(payload), 43200)
        self.assertIn("CVE-2026-35501", extract_security_reason(payload))

        # Test at 13.5 hours old (current age)
        now = 1761100000
        rel_time_13h_ago = datetime.fromtimestamp(now - 13 * 3600, tz=timezone.utc).isoformat()
        res = evaluate_component(
            component_name="Unbound",
            candidate_ver="release-1.26.2",
            current_ver="release-1.26.1",
            release_date_iso=rel_time_13h_ago,
            release_text=payload,
            now_epoch=now,
        )
        self.assertTrue(res["ready"], "Unbound 1.26.2 should be READY at 13h under 12h security threshold")
        self.assertTrue(res["is_security"])
        self.assertEqual(res["threshold_hours"], 12)

    def test_decoupled_resolution_scenarios(self):
        """Verify Pi-hole and Unbound promotions operate independently."""
        # Scenario 1: Pi-hole ready (standard, 25h), Unbound pending (security, 6h)
        pi_eval = {
            "component": "Pi-hole",
            "candidate": "2026.11.0",
            "current": "2026.10.0",
            "is_new": True,
            "ready": True,
        }
        unbound_eval = {
            "component": "Unbound",
            "candidate": "release-1.26.3",
            "current": "release-1.26.2",
            "is_new": True,
            "ready": False,
        }
        res = resolve_versions(pi_eval, unbound_eval)
        self.assertTrue(res["promote"])
        self.assertEqual(res["target_pi"], "2026.11.0")
        self.assertEqual(res["target_unbound"], "release-1.26.2")  # Kept current!
        self.assertTrue(res["pending"])  # Unbound still in pending file

        # Scenario 2: Pi-hole unchanged, Unbound ready (security, 13h)
        pi_eval_unchanged = {
            "component": "Pi-hole",
            "candidate": "2026.10.0",
            "current": "2026.10.0",
            "is_new": False,
            "ready": True,
        }
        unbound_eval_ready = {
            "component": "Unbound",
            "candidate": "release-1.26.2",
            "current": "release-1.26.1",
            "is_new": True,
            "ready": True,
        }
        res2 = resolve_versions(pi_eval_unchanged, unbound_eval_ready)
        self.assertTrue(res2["promote"])
        self.assertEqual(res2["target_pi"], "2026.10.0")
        self.assertEqual(res2["target_unbound"], "release-1.26.2")
        self.assertFalse(res2["pending"])  # Nothing pending

        # Scenario 3: Both pending -> No promotion
        pi_pending = {
            "component": "Pi-hole",
            "candidate": "2026.11.0",
            "current": "2026.10.0",
            "is_new": True,
            "ready": False,
        }
        unbound_pending = {
            "component": "Unbound",
            "candidate": "release-1.26.3",
            "current": "release-1.26.2",
            "is_new": True,
            "ready": False,
        }
        res3 = resolve_versions(pi_pending, unbound_pending)
        self.assertFalse(res3["promote"])
        self.assertEqual(res3["target_pi"], "2026.10.0")
        self.assertEqual(res3["target_unbound"], "release-1.26.2")
        self.assertTrue(res3["pending"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
