"""Tests for multi-scope and custom delimiter support."""

import pytest
from commit_scope_lint.parser import parse_commit_message


def test_parse_comma_separated_scopes():
    msg = "feat(api,auth): add multi-scope authentication endpoint"
    parsed = parse_commit_message(msg)
    assert parsed.type == "feat"
    assert parsed.scope == "api,auth"
    assert parsed.subject == "add multi-scope authentication endpoint"


def test_parse_slash_delimited_scopes():
    msg = "fix(frontend/components): resolve button padding bug"
    parsed = parse_commit_message(msg)
    assert parsed.type == "fix"
    assert parsed.scope == "frontend/components"
    assert parsed.subject == "resolve button padding bug"


def test_parse_hyphen_delimited_scopes():
    msg = "refactor(core-engine-v2): optimize loop performance"
    parsed = parse_commit_message(msg)
    assert parsed.type == "refactor"
    assert parsed.scope == "core-engine-v2"
    assert parsed.subject == "optimize loop performance"
