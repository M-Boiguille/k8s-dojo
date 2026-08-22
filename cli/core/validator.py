"""Kata validation utilities."""
from cli.core.k8s_client import exec_check


REQUIRED_FIELDS = {"id", "title", "tool", "level", "category", "mode"}
VALID_TOOLS = {"k8s", "terraform", "aws", "github-actions"}
VALID_LEVELS = {"beginner", "intermediate", "advanced", "boss"}
VALID_CATEGORIES = {"pods", "services", "storage", "networking", "rbac", "git", "architecture"}
VALID_MODES = {"creation", "troubleshooting", "chaos", "git", "architecture"}
VALID_COMPARATORS = {"eq", "ne", "contains", "regex"}


def validate_kata_schema(kata: dict) -> list[str]:
    """Return a list of human-readable schema errors."""
    errors = []
    missing = REQUIRED_FIELDS - set(kata.keys())
    if missing:
        errors.append(f"Missing required fields: {', '.join(sorted(missing))}")
    if kata.get("tool") not in VALID_TOOLS:
        errors.append(f"Invalid tool '{kata.get('tool')}'")
    if kata.get("level") not in VALID_LEVELS:
        errors.append(f"Invalid level '{kata.get('level')}'")
    if kata.get("category") not in VALID_CATEGORIES:
        errors.append(f"Invalid category '{kata.get('category')}'")
    if kata.get("mode") not in VALID_MODES:
        errors.append(f"Invalid mode '{kata.get('mode')}'")
    checks = kata.get("validation", {}).get("checks", [])
    if not isinstance(checks, list) or not checks:
        errors.append("validation.checks must be a non-empty list")
    for idx, check in enumerate(checks):
        if not isinstance(check, dict):
            errors.append(f"check[{idx}] is not a dict")
            continue
        for key in ("command", "expected", "comparator"):
            if key not in check:
                errors.append(f"check[{idx}] missing '{key}'")
        if check.get("comparator") not in VALID_COMPARATORS:
            errors.append(f"check[{idx}] has invalid comparator '{check.get('comparator')}'")
    return errors


def run_dry_run_checks(kata: dict) -> tuple[bool, str]:
    """Execute checks in dry-run mode (no real cluster)."""
    log = []
    for idx, check in enumerate(kata.get("validation", {}).get("checks", [])):
        ok, output = exec_check(check, dry_run=True)
        log.append(f"[{idx + 1}] {check.get('description', 'check')}: {'OK' if ok else 'FAIL'}\n{output}")
    return True, "\n".join(log)
