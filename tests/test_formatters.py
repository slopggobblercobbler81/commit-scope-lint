"""Tests for output formatters."""

import json
from commit_scope_lint.formatters import (
    format_github,
    format_json,
    format_markdown,
    format_terminal,
)
from commit_scope_lint.linter import CommitLinter


def test_formatters_output():
    linter = CommitLinter()
    commits = [
        ("abc1234", "Dev", "feat(cli): add interactive hook prompt"),
        ("def5678", "Dev", "invalid commit message"),
    ]
    suite = linter.lint_commits(commits)

    # Terminal formatter
    term = format_terminal(suite)
    assert "add interactive hook prompt" in term
    assert "invalid commit message" in term
    assert "FAIL" in term

    # JSON formatter
    raw_json = format_json(suite)
    parsed = json.loads(raw_json)
    assert parsed["success"] is False
    assert parsed["summary"]["total_commits"] == 2
    assert parsed["summary"]["passed_commits"] == 1
    assert parsed["summary"]["failed_commits"] == 1

    # GitHub Actions formatter
    gh = format_github(suite)
    assert "::error" in gh
    assert "title=header-format" in gh

    # Markdown formatter
    md = format_markdown(suite)
    assert "## 🔍 Commit Scope Lint Report" in md
    assert "Total Commits" in md
    assert "Failed ❌" in md


def test_markdown_formatter_all_passed():
    linter = CommitLinter()
    suite = linter.lint_commits(["feat: perfect commit message"])
    md = format_markdown(suite)
    assert "Passed ✅" in md
