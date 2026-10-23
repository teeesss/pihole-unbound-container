#!/usr/bin/env python3
"""
Unit and regression tests for Pi-hole + Unbound container configuration,
Dockerfile hardening, custom-entrypoint lifecycle, and CI workflow specifications.
"""

import os
import re
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCKERFILE_PATH = os.path.join(PROJECT_ROOT, "docker", "Dockerfile")
UNBOUND_CONF_PATH = os.path.join(PROJECT_ROOT, "docker", "unbound-pihole.conf")
ENTRYPOINT_PATH = os.path.join(PROJECT_ROOT, "docker", "custom-entrypoint.sh")
WORKFLOW_PUBLISH_PATH = os.path.join(PROJECT_ROOT, ".github", "workflows", "docker-publish.yml")


class TestUnboundConfiguration(unittest.TestCase):
    """Validate unbound-pihole.conf parameters and performance tuning."""

    @classmethod
    def setUpClass(cls):
        with open(UNBOUND_CONF_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_serve_expired_rfc8767(self):
        """Verify RFC 8767 serve-expired is enabled with adequate TTL and timeout."""
        self.assertRegex(self.content, r"serve-expired:\s+yes", "serve-expired must be enabled")
        self.assertRegex(self.content, r"serve-expired-ttl:\s+86400", "serve-expired-ttl must be 86400 (24h)")
        self.assertRegex(self.content, r"serve-expired-client-timeout:\s+1800", "serve-expired-client-timeout must be 1800ms")

    def test_prefetch_and_prefetch_key(self):
        """Verify both record prefetching and DNSKEY prefetching are active."""
        self.assertRegex(self.content, r"prefetch:\s+yes", "prefetch must be enabled")
        self.assertRegex(self.content, r"prefetch-key:\s+yes", "prefetch-key must be enabled")

    def test_cache_and_buffer_sizing(self):
        """Verify memory cache and socket buffer sizing."""
        self.assertRegex(self.content, r"msg-cache-size:\s+64m", "msg-cache-size must be at least 64m")
        self.assertRegex(self.content, r"rrset-cache-size:\s+128m", "rrset-cache-size must be at least 128m")
        self.assertRegex(self.content, r"so-rcvbuf:\s+4m", "so-rcvbuf must be configured")
        self.assertRegex(self.content, r"so-sndbuf:\s+4m", "so-sndbuf must be configured")
        self.assertRegex(self.content, r"num-queries-per-thread:\s+4096", "num-queries-per-thread must be 4096")

    def test_dnssec_and_root_anchor(self):
        """Verify DNSSEC hardening and root key trust anchor path."""
        self.assertRegex(self.content, r'auto-trust-anchor-file:\s*"/var/lib/unbound/root\.key"')
        self.assertRegex(self.content, r"harden-dnssec-stripped:\s+yes")
        self.assertRegex(self.content, r"harden-glue:\s+yes")

    def test_privacy_and_hardening(self):
        """Verify privacy flags and access controls."""
        self.assertRegex(self.content, r"hide-identity:\s+yes")
        self.assertRegex(self.content, r"hide-version:\s+yes")
        self.assertRegex(self.content, r"harden-below-nxdomain:\s+yes")
        self.assertRegex(self.content, r"qname-minimisation:\s+yes")
        self.assertRegex(self.content, r"access-control:\s+127\.0\.0\.1/32\s+allow")
        self.assertRegex(self.content, r"access-control:\s+0\.0\.0\.0/0\s+refuse")


class TestDockerfileHardening(unittest.TestCase):
    """Validate Dockerfile build dependencies, stripping, shared libraries, and safety checks."""

    @classmethod
    def setUpClass(cls):
        with open(DOCKERFILE_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_bind_tools_installed(self):
        """Verify bind-tools (dig) is included in runtime stage for healthchecks."""
        self.assertIn("bind-tools", self.content, "bind-tools must be present in runtime apk add")

    def test_libunbound_shared_library_copied(self):
        """Verify libunbound.so* is copied from builder stage."""
        self.assertIn(
            "COPY --from=builder /usr/lib/libunbound* /usr/lib/",
            self.content,
            "Shared libunbound libraries must be copied to runtime stage",
        )

    def test_binary_stripping_in_builder(self):
        """Verify debug symbols are stripped in builder stage."""
        self.assertRegex(
            self.content,
            r"strip\s+/usr/sbin/unbound\*",
            "strip command must be run on compiled binaries",
        )

    def test_safe_root_hints_download(self):
        """Verify root hints download asserts file existence and non-zero size."""
        self.assertIn("-s /var/lib/unbound/root.hints", self.content, "Must assert root hints size > 0")
        self.assertNotIn("wget ... | tee", self.content)

    def test_legacy_lighttpd_removed(self):
        """Verify legacy lighttpd configuration is not copied into image."""
        self.assertNotIn("lighttpd-external.conf", self.content, "Legacy lighttpd config must be removed")

    def test_edns_cap_set_through_ftl(self):
        """Pi-hole v6 applies dnsmasq lines from FTLCONF, not from a hidden dnsmasq.d file."""
        self.assertIn(
            "FTLCONF_misc_dnsmasq_lines=edns-packet-max=1232",
            self.content,
            "Image must set the EDNS cap through FTL so a bind mount cannot hide it",
        )


class TestCustomEntrypoint(unittest.TestCase):
    """Validate custom-entrypoint.sh supervision and error handling."""

    @classmethod
    def setUpClass(cls):
        with open(ENTRYPOINT_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_preflight_checkconf(self):
        """Verify entrypoint runs unbound-checkconf before daemon launch."""
        self.assertIn("unbound-checkconf", self.content)

    def test_root_anchor_initialization(self):
        """Verify entrypoint initializes DNSSEC root key if missing."""
        self.assertIn("unbound-anchor", self.content)
        self.assertIn("/var/lib/unbound/root.key", self.content)

    def test_fail_fast_on_startup_failure(self):
        """Verify entrypoint aborts container execution (exit 1) if Unbound fails."""
        self.assertRegex(self.content, r"exit 1")
        # Ensure 'exit 1' is active and not commented out
        active_exits = [line for line in self.content.splitlines() if line.strip() == "exit 1"]
        self.assertGreaterEqual(len(active_exits), 1, "At least one active exit 1 must guard startup failure")


class TestPublishWorkflow(unittest.TestCase):
    """Validate docker-publish.yml workflow triggers and cache optimization."""

    @classmethod
    def setUpClass(cls):
        with open(WORKFLOW_PUBLISH_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_tag_triggers(self):
        """Verify workflow triggers on both 20* and v* release tag patterns."""
        self.assertIn("'20*'", self.content)
        self.assertIn("'v*'", self.content)

    def test_gha_cache_efficiency(self):
        """Verify single-arch test step does not export cache-to, avoiding overwrite."""
        # Find step "Build Local Test Image"
        test_step = re.search(r"name:\s*Build Local Test Image.*?(?=\n\s*-\s*name:)", self.content, re.DOTALL)
        self.assertIsNotNone(test_step, "Build Local Test Image step must exist")
        self.assertNotIn("cache-to:", test_step.group(0), "Test build step should not export cache-to")

        # Find final "Build and Push" step
        push_step = re.search(r"name:\s*Build and Push.*", self.content, re.DOTALL)
        self.assertIsNotNone(push_step, "Build and Push step must exist")
        self.assertIn("cache-to: type=gha,mode=max", push_step.group(0), "Multi-arch push must export cache")


class TestNtpServersConfig(unittest.TestCase):
    """Validate docker/ntp-servers.conf providers and Anycast IP formatting."""

    NTP_CONF_PATH = os.path.join(PROJECT_ROOT, "docker", "ntp-servers.conf")

    @classmethod
    def setUpClass(cls):
        with open(cls.NTP_CONF_PATH, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_tier1_providers_present(self):
        """Verify 5 Tier-1 Anycast NTP providers are present."""
        providers = ["CLOUDFLARE", "GOOGLE", "NIST", "APPLE", "MICROSOFT"]
        for p in providers:
            self.assertIn(p, self.content, f"Provider {p} must be defined in ntp-servers.conf")

    def test_ip_format_validity(self):
        """Verify each provider line has valid IPv4 syntax."""
        ip_regex = re.compile(r"^[A-Z0-9_-]+\|[a-z0-9.-]+\|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        lines = [line.strip() for line in self.content.splitlines() if line.strip() and not line.startswith("#")]
        self.assertGreaterEqual(len(lines), 5, "At least 5 provider lines expected")
        for line in lines:
            self.assertTrue(ip_regex.match(line), f"Malformed NTP provider entry: {line}")


class TestClockResuscitation(unittest.TestCase):
    """Validate entrypoint time recovery and build year guards."""

    @classmethod
    def setUpClass(cls):
        with open(ENTRYPOINT_PATH, "r", encoding="utf-8") as f:
            cls.entrypoint = f.read()
        with open(DOCKERFILE_PATH, "r", encoding="utf-8") as f:
            cls.dockerfile = f.read()

    def test_dynamic_build_year_generated(self):
        """Verify Dockerfile generates /etc/build_year at image build time."""
        self.assertIn("/etc/build_year", self.dockerfile)

    def test_entrypoint_uses_build_year(self):
        """Verify custom-entrypoint.sh compares current year against /etc/build_year."""
        self.assertIn("/etc/build_year", self.entrypoint)
        self.assertIn("AUTO_TIME_SYNC", self.entrypoint)

    def test_entrypoint_checks_local_router_gateway(self):
        """Verify entrypoint attempts local default gateway router before WAN."""
        self.assertIn("ip route", self.entrypoint)
        self.assertIn("awk '/default/", self.entrypoint)

    def test_ntp_pass_precedes_router_http(self):
        """Anycast NTP runs before an HTTP Date from the router can be accepted."""
        ntp_pass = self.entrypoint.find("for ip in $custom_ips $router_ip $anycast_ips")
        http_pass = self.entrypoint.find("for ip in $custom_ips $anycast_ips $router_ip")
        self.assertGreater(ntp_pass, 0, "NTP pass must list router before anycast")
        self.assertGreater(http_pass, ntp_pass, "HTTP pass must come after NTP and list anycast before the router")


class TestPublishedQuickStart(unittest.TestCase):
    """The public README is the contract for how the two daemons are wired."""

    @classmethod
    def setUpClass(cls):
        readme = os.path.join(PROJECT_ROOT, "README.md")
        with open(readme, "r", encoding="utf-8") as f:
            cls.content = f.read()

    def test_quick_start_uses_v6_upstream_and_sys_time(self):
        self.assertIn("FTLCONF_dns_upstreams: '127.0.0.1#5335'", self.content)
        self.assertNotIn("PIHOLE_DNS_:", self.content)
        self.assertIn("SYS_TIME", self.content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
