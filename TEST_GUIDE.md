# Test Guide

## Overview
This repository uses automated unit and integration tests to validate version filtering, security severity detection, adaptive cooling buffers (12h vs 24h), and decoupled promotions.

## Test Suites

### 1. Python Security & Promotion Test Suite
Validates CVE identification, keyword scanning, threshold calculations, real-world CVE payloads (Unbound 1.26.2), and independent version promotion logic.

```bash
# Run with Python 3:
python environment/tests/test_security_eval.py
```

### 2. Bash Workflow Logic Test Suite
Validates the exact shell functions used in GitHub Actions (`.github/workflows/update-checker.yml`).

```bash
# Run with Bash:
bash environment/tests/test_security_eval.sh
```

## Adding New Tests
- Place new test scripts inside `/environment/tests/`.
- Ensure all tests exit with status code `0` on success and non-zero on failure.
- Always record results in `TEST_RESULTS.md` after running test suites.
