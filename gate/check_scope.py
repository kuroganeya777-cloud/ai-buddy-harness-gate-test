#!/usr/bin/env python3
"""Read-only, stdlib-only PR file-scope gate; no publishing or deployment.

Prototype scope validation, not full Harness v0.3 and not owner approval.
"""
from __future__ import annotations
import argparse
import re
import subprocess
import sys

ALLOWED_EXACT = frozenset({"README.md"})
ALLOWED_PREFIXES = ("examples/", "docs/")
SHA = re.compile(r"[0-9a-fA-F]{40,64}\Z")


def allowed_path(path: str) -> bool:
    return path in ALLOWED_EXACT or any(
        path.startswith(prefix) and len(path) > len(prefix)
        for prefix in ALLOWED_PREFIXES
    )


def evaluate(changes: list[tuple[str, str]], modes: dict[str, str]) -> list[str]:
    violations = []
    if not changes:
        return ["No changed files found"]
    for status, path in changes:
        if status not in ("A", "M"):
            violations.append(f"Disallowed change type {status!r}: {path!r}")
        if not allowed_path(path):
            violations.append(f"Path outside allowlist: {path!r}")
        if modes.get(path) != "100644":
            violations.append(
                f"Nonregular, executable, deleted, or missing file: {path!r}, mode={modes.get(path)!r}"
            )
    return violations


def run_git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if result.returncode:
        raise RuntimeError(
            f"git {args[0]} failed with exit {result.returncode}: "
            f"{result.stderr.decode('utf-8', 'replace')[:500]}"
        )
    return result.stdout


def inspect(base: str, head: str) -> list[str]:
    if not SHA.fullmatch(base) or not SHA.fullmatch(head):
        return ["Invalid commit SHA"]
    data = run_git("diff", "--name-status", "-z", "--no-renames", base, head)
    items = data.split(b"\0")
    if not items or items[-1] != b"":
        return ["Unexpected git diff format"]
    items.pop()
    if len(items) % 2:
        return ["Unexpected git diff status/path count"]
    changes = [
        (
            items[i].decode("utf-8", "surrogateescape"),
            items[i + 1].decode("utf-8", "surrogateescape"),
        )
        for i in range(0, len(items), 2)
    ]
    modes = {}
    for record in run_git("ls-tree", "-r", "-z", head).split(b"\0"):
        if not record:
            continue
        meta, sep, path = record.partition(b"\t")
        if not sep:
            return ["Unexpected git tree format"]
        mode = meta.split(b" ", 1)[0].decode("ascii", "strict")
        modes[path.decode("utf-8", "surrogateescape")] = mode
    return evaluate(changes, modes)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only PR scope check")
    parser.add_argument("base")
    parser.add_argument("head")
    args = parser.parse_args()
    try:
        violations = inspect(args.base, args.head)
    except (RuntimeError, OSError, UnicodeError, ValueError) as exc:
        print(f"SCOPE GATE: FAIL (inspection error: {exc})")
        return 2
    if violations:
        print("SCOPE GATE: FAIL")
        for violation in violations:
            print("-", violation)
        return 1
    print("SCOPE GATE: PASS (file-scope only; not owner approval or deployment authorization)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
