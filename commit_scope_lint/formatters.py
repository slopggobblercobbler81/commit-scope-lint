"""Output formatters for terminal, JSON, GitHub Actions, and Markdown."""

import json
import os
import sys
from typing import Optional
from .models import LintLevel, LintResult, LintSuiteResult


def can_encode(char: str) -> bool:
    """Check if stdout can encode the character."""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        char.encode(encoding)
        return True
    except Exception:
        return False


# Encoding-safe symbols
SYM_PASS = "✔" if can_encode("✔") else "[PASS]"
SYM_FAIL = "✖" if can_encode("✖") else "[FAIL]"
SYM_WARN = "⚠" if can_encode("⚠") else "[WARN]"
SYM_INFO = "ℹ" if can_encode("ℹ") else "[INFO]"
SYM_BULLET = "•" if can_encode("•") else "*"
SYM_BULB = "💡" if can_encode("💡") else "->"


class Colors:
    """ANSI color codes with NO_COLOR detection."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"

    @classmethod
    def enabled(cls) -> bool:
        if os.environ.get("NO_COLOR") is not None:
            return False
        if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
            return os.environ.get("FORCE_COLOR") == "1"
        return True

    @classmethod
    def colorize(cls, code: str, text: str) -> str:
        if not cls.enabled():
            return text
        return f"{code}{text}{cls.RESET}"


def format_terminal(suite: LintSuiteResult, quiet: bool = False) -> str:
    """Format lint results for human-readable terminal display."""
    lines = []

    for i, res in enumerate(suite.results, 1):
        commit = res.commit
        header = commit.header or "(empty message)"
        hash_str = f" [{commit.commit_hash[:8]}]" if commit.commit_hash else ""

        if res.is_ignored:
            if not quiet:
                prefix = Colors.colorize(Colors.GRAY, f"{SYM_INFO} IGNORED")
                lines.append(f"{prefix}{hash_str}: {header}")
                if res.ignore_reason:
                    lines.append(Colors.colorize(Colors.GRAY, f"  Reason: {res.ignore_reason}"))
            continue

        if res.passed and res.warnings_count == 0:
            if not quiet:
                prefix = Colors.colorize(Colors.GREEN, f"{SYM_PASS} PASS")
                lines.append(f"{prefix}{hash_str}: {header}")
            continue

        if res.passed and res.warnings_count > 0:
            prefix = Colors.colorize(Colors.YELLOW, f"{SYM_WARN} WARN")
            lines.append(f"{prefix}{hash_str}: {header}")
        else:
            prefix = Colors.colorize(Colors.RED, f"{SYM_FAIL} FAIL")
            lines.append(f"{prefix}{hash_str}: {header}")

        for v in res.violations:
            level_str = (
                Colors.colorize(Colors.RED, "ERROR")
                if v.level == LintLevel.ERROR
                else Colors.colorize(Colors.YELLOW, "WARN")
            )
            line_info = f" (line {v.line_number})" if v.line_number else ""
            rule_badge = Colors.colorize(Colors.CYAN, f"[{v.rule_id}]")
            lines.append(f"  {SYM_BULLET} {level_str} {rule_badge}{line_info}: {v.message}")
            if v.suggestion:
                lines.append(Colors.colorize(Colors.GRAY, f"    {SYM_BULB} Suggestion: {v.suggestion}"))

    # Summary
    if suite.total_commits > 0 and (not quiet or not suite.success):
        lines.append("")
        total = suite.total_commits
        passed = suite.passed_commits
        failed = suite.failed_commits
        errors = suite.total_errors
        warnings = suite.total_warnings

        if suite.success:
            status_text = Colors.colorize(Colors.GREEN, Colors.BOLD + f"{SYM_PASS} All {total} commit(s) passed successfully!")
        else:
            status_text = Colors.colorize(Colors.RED, Colors.BOLD + f"{SYM_FAIL} {failed} of {total} commit(s) failed validation.")

        stats = f"Commits: {passed}/{total} passed | Issues: {errors} error(s), {warnings} warning(s)"
        lines.append(status_text)
        lines.append(Colors.colorize(Colors.GRAY, stats))

    return "\n".join(lines)


def format_json(suite: LintSuiteResult) -> str:
    """Format lint results as structured JSON."""
    return json.dumps(suite.to_dict(), indent=2)


def format_github(suite: LintSuiteResult) -> str:
    """Format violations as GitHub Actions workflow commands (::error / ::warning)."""
    lines = []
    for res in suite.results:
        if res.is_ignored:
            continue
        for v in res.violations:
            cmd = "error" if v.level == LintLevel.ERROR else "warning"
            params = [f"title={v.rule_id}"]
            if v.line_number:
                params.append(f"line={v.line_number}")
            param_str = ",".join(params)
            msg = v.message
            if v.suggestion:
                msg += f" (Suggestion: {v.suggestion})"
            lines.append(f"::{cmd} {param_str}::{msg}")

    # Append standard terminal summary
    lines.append(format_terminal(suite))
    return "\n".join(lines)


def format_markdown(suite: LintSuiteResult) -> str:
    """Format lint results as a GitHub Flavored Markdown comment/summary."""
    lines = ["## 🔍 Commit Scope Lint Report\n"]

    if suite.success:
        lines.append(f"> **Status:** Passed ✅ — All {suite.total_commits} commit(s) follow Conventional Commits.\n")
    else:
        lines.append(f"> **Status:** Failed ❌ — {suite.failed_commits} of {suite.total_commits} commit(s) failed validation.\n")

    lines.append("| Metric | Value |")
    lines.append("| :--- | :--- |")
    lines.append(f"| Total Commits | `{suite.total_commits}` |")
    lines.append(f"| Passed Commits | `{suite.passed_commits}` |")
    lines.append(f"| Failed Commits | `{suite.failed_commits}` |")
    lines.append(f"| Total Errors | `{suite.total_errors}` |")
    lines.append(f"| Total Warnings | `{suite.total_warnings}` |\n")

    if suite.failed_commits > 0 or suite.total_warnings > 0:
        lines.append("### Details\n")
        for res in suite.results:
            if res.is_ignored or (res.passed and res.warnings_count == 0):
                continue
            badge = "❌" if not res.passed else "⚠️"
            header = res.commit.header or "(empty)"
            hash_info = f"`{res.commit.commit_hash[:7]}` " if res.commit.commit_hash else ""
            lines.append(f"#### {badge} {hash_info}{header}\n")
            lines.append("| Level | Rule | Message | Suggestion |")
            lines.append("| :--- | :--- | :--- | :--- |")
            for v in res.violations:
                lvl = "🔴 Error" if v.level == LintLevel.ERROR else "🟡 Warning"
                sugg = v.suggestion or "-"
                lines.append(f"| {lvl} | `{v.rule_id}` | {v.message} | {sugg} |")
            lines.append("")

    return "\n".join(lines)
