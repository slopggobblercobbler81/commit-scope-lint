"""Tests for lowercase/uppercase scope enforcement rules."""

import pytest
from commit_scope_lint.config import LintConfig
from commit_scope_lint.rules import RuleScope, check_scope_case
from commit_scope_lint.parser import parse_commit_message

def test_check_scope_case_uppercase():
    assert check_scope_case("MY_SCOPE", "uppercase")
    assert check_scope_case("CORE", "uppercase")
    assert not check_scope_case("my_scope", "uppercase")
    assert not check_scope_case("MyScope", "uppercase")
    assert not check_scope_case("my-scope", "uppercase")

def test_rule_scope_uppercase_enforcement():
    rule = RuleScope()
    config = LintConfig(scope_case="uppercase")

    # Valid uppercase scope
    commit_valid = parse_commit_message("feat(CORE): add uppercase scope support")
    violations = rule.validate(commit_valid, config)
    assert len(violations) == 0

    # Invalid lowercase/mixed scope under uppercase rule
    commit_invalid = parse_commit_message("feat(core): add lowercase scope")
    violations_invalid = rule.validate(commit_invalid, config)
    assert len(violations_invalid) == 1
    assert violations_invalid[0].rule_id == "scope-case"
