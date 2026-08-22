"""kubectl subprocess wrapper."""
import os
import re
import subprocess


def run_kubectl(command: str, dry_run: bool = False) -> tuple[int, str, str]:
    """Run a kubectl command and return (returncode, stdout, stderr)."""
    if dry_run:
        return 0, "dry-run", ""
    env = os.environ.copy()
    if "KUBECONFIG" in os.environ:
        env["KUBECONFIG"] = os.environ["KUBECONFIG"]
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def compare_output(output: str, expected: str, comparator: str) -> bool:
    if comparator == "eq":
        return output == expected
    if comparator == "ne":
        return output != expected
    if comparator == "contains":
        return expected in output
    if comparator == "regex":
        return re.search(expected, output) is not None
    return output == expected


def exec_check(check: dict, dry_run: bool = False) -> tuple[bool, str]:
    command = check.get("command", "")
    expected = str(check.get("expected", ""))
    comparator = check.get("comparator", "eq")
    returncode, stdout, stderr = run_kubectl(command, dry_run=dry_run)
    output = stdout if returncode == 0 else stderr
    ok = returncode == 0 and compare_output(stdout, expected, comparator)
    return ok, output
