"""Tests for the commit message parser."""

import pytest
from commit_scope_lint.parser import clean_git_comments, parse_commit_message


def test_parse_simple_commit():
    msg = "feat: add user login endpoint"
    parsed = parse_commit_message(msg)
    assert parsed.type == "feat"
    assert parsed.scope is None
    assert not parsed.is_breaking
    assert parsed.subject == "add user login endpoint"
    assert parsed.body is None
    assert parsed.footers == []


def test_parse_scoped_commit():
    msg = "fix(auth-service): correct jwt expiration timestamp"
    parsed = parse_commit_message(msg)
    assert parsed.type == "fix"
    assert parsed.scope == "auth-service"
    assert not parsed.is_breaking
    assert parsed.subject == "correct jwt expiration timestamp"


def test_parse_breaking_change_bang():
    msg = "refactor(api)!: migrate to rest v2 schema"
    parsed = parse_commit_message(msg)
    assert parsed.type == "refactor"
    assert parsed.scope == "api"
    assert parsed.is_breaking
    assert parsed.subject == "migrate to rest v2 schema"


def test_parse_commit_with_body_and_footer():
    raw = (
        "chore(deps): bump urllib3 from 2.0 to 2.1\n"
        "\n"
        "Upgrades the security patch for urllib3 to address CVE-2024-xxxx.\n"
        "Backward compatibility is preserved.\n"
        "\n"
        "Signed-off-by: Dev Bot <bot@example.com>\n"
        "Refs: #1234\n"
    )
    parsed = parse_commit_message(raw)
    assert parsed.type == "chore"
    assert parsed.scope == "deps"
    assert parsed.subject == "bump urllib3 from 2.0 to 2.1"
    assert parsed.body is not None
    assert "Upgrades the security patch" in parsed.body
    assert len(parsed.footers) == 2
    assert parsed.footers[0] == ("Signed-off-by", "Dev Bot <bot@example.com>")
    assert parsed.footers[1] == ("Refs", "#1234")


def test_parse_commit_with_breaking_change_footer():
    raw = (
        "feat(database): introduce async connection pool\n"
        "\n"
        "BREAKING CHANGE: Sync engine removed in favor of AsyncEngine.\n"
    )
    parsed = parse_commit_message(raw)
    assert parsed.type == "feat"
    assert parsed.scope == "database"
    assert parsed.is_breaking
    assert len(parsed.footers) == 1
    assert parsed.footers[0][0] == "BREAKING CHANGE"
    assert "Sync engine removed" in parsed.footers[0][1]


def test_parse_empty_message():
    parsed = parse_commit_message("")
    assert parsed.header == ""
    assert parsed.type is None
    assert parsed.subject is None


def test_clean_git_comments():
    raw = (
        "fix(ui): adjust navbar padding\n"
        "# Please enter the commit message for your changes.\n"
        "# Lines starting with '#' will be ignored.\n"
    )
    cleaned = clean_git_comments(raw)
    assert cleaned == "fix(ui): adjust navbar padding"
    parsed = parse_commit_message(raw, strip_comments=True)
    assert parsed.type == "fix"
    assert parsed.scope == "ui"


def test_parse_windows_crlf():
    raw = "fix(cli): handle crlf gracefully\r\n\r\nDetailed explanation line 1.\r\nDetailed explanation line 2."
    parsed = parse_commit_message(raw)
    assert parsed.type == "fix"
    assert parsed.scope == "cli"
    assert parsed.subject == "handle crlf gracefully"
    assert parsed.body == "Detailed explanation line 1.\nDetailed explanation line 2."
