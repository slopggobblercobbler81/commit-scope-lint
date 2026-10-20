"""Tests for the CommitLinter orchestration engine."""

import pytest
from commit_scope_lint.config import LintConfig
from commit_scope_lint.linter import CommitLinter
from commit_scope_lint.models import LintLevel


def test_linter_clean_commit():
    linter = CommitLinter()
    result = linter.lint_commit("feat(auth): add OAuth2 provider support")
    assert result.passed
    assert result.errors_count == 0
    assert result.warnings_count == 0


def test_linter_invalid_commit():
    linter = CommitLinter()
    result = linter.lint_commit("bad commit message without type")
    assert not result.passed
    assert result.errors_count > 0


def test_linter_ignore_patterns():
    linter = CommitLinter()
    # Merge commit
    result_merge = linter.lint_commit("Merge branch 'feature/login' into main")
    assert result_merge.is_ignored
    assert result_merge.passed

    # Release commit
    result_release = linter.lint_commit("chore(release): 1.2.0")
    assert result_release.is_ignored
    assert result_release.passed


def test_linter_strict_mode():
    config = LintConfig(strict=True)
    linter = CommitLinter(config=config)
    # A commit with warning (trailing period) should become an error under strict mode
    result = linter.lint_commit("feat(core): add retry mechanism.")
    assert not result.passed
    assert any(v.rule_id == "subject-full-stop" and v.level == LintLevel.ERROR for v in result.violations)


def test_linter_multiple_commits():
    linter = CommitLinter()
    commits = [
        ("h1", "Alice", "feat(cli): add list subcommand"),
        ("h2", "Bob", "invalid message header"),
        ("h3", "Charlie", "Merge pull request #10 from dev"),
    ]
    suite = linter.lint_commits(commits)
    assert suite.total_commits == 3
    assert suite.passed_commits == 2
    assert suite.failed_commits == 1
    assert not suite.success
