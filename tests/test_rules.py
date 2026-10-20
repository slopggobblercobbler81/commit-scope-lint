"""Tests for commit linting rules."""

import pytest
from commit_scope_lint.config import LintConfig
from commit_scope_lint.models import LintLevel
from commit_scope_lint.parser import parse_commit_message
from commit_scope_lint.rules import (
    RuleBody,
    RuleHeaderFormat,
    RuleHeaderLength,
    RuleScope,
    RuleSubject,
    RuleTicket,
    RuleType,
    check_scope_case,
    is_camel_case,
    is_kebab_case,
    is_snake_case,
)


def test_casing_helpers():
    assert is_kebab_case("auth-provider")
    assert is_kebab_case("v2")
    assert not is_kebab_case("Auth-Provider")
    assert not is_kebab_case("auth_provider")

    assert is_snake_case("auth_provider")
    assert not is_snake_case("auth-provider")

    assert is_camel_case("authProvider")
    assert is_camel_case("authProviderV2")
    assert not is_camel_case("AuthProvider")


def test_check_scope_case_all_styles():
    assert check_scope_case("my-scope", "kebab-case")
    assert not check_scope_case("myScope", "kebab-case")

    assert check_scope_case("myscope", "lowercase")
    assert not check_scope_case("myScope", "lowercase")

    assert check_scope_case("my_scope", "snake_case")
    assert not check_scope_case("my-scope", "snake_case")

    assert check_scope_case("myScope", "camelCase")
    assert not check_scope_case("my-scope", "camelCase")

    assert check_scope_case("MY_SCOPE", "uppercase")
    assert not check_scope_case("my_scope", "uppercase")

    assert check_scope_case("Any_Scope-123", "any")


def test_rule_header_format():
    rule = RuleHeaderFormat()
    config = LintConfig()

    # Valid
    commit = parse_commit_message("feat(cli): add new command")
    assert len(rule.validate(commit, config)) == 0

    # Empty
    empty = parse_commit_message("")
    v = rule.validate(empty, config)
    assert len(v) == 1
    assert v[0].rule_id == "header-empty"

    # Malformed (no colon)
    bad = parse_commit_message("just updated some files")
    v = rule.validate(bad, config)
    assert len(v) == 1
    assert v[0].rule_id == "header-format"


def test_rule_type():
    rule = RuleType()
    config = LintConfig(types=["feat", "fix"])

    # Valid
    commit = parse_commit_message("feat: implement caching")
    assert len(rule.validate(commit, config)) == 0

    # Invalid type
    commit_bad = parse_commit_message("unknown: implement caching")
    v = rule.validate(commit_bad, config)
    assert len(v) == 1
    assert v[0].rule_id == "type-enum"

    # Uppercase type
    commit_upper = parse_commit_message("FEAT: implement caching")
    v = rule.validate(commit_upper, config)
    assert any(violation.rule_id == "type-case" for violation in v)


def test_rule_scope():
    rule = RuleScope()
    
    # Scope required
    cfg_req = LintConfig(scope_required=True)
    c_no_scope = parse_commit_message("feat: no scope provided")
    v = rule.validate(c_no_scope, cfg_req)
    assert len(v) == 1
    assert v[0].rule_id == "scope-required"

    # Scope enum
    cfg_enum = LintConfig(scopes=["core", "ui", "auth"])
    c_bad_scope = parse_commit_message("feat(billing): add stripe")
    v = rule.validate(c_bad_scope, cfg_enum)
    assert len(v) == 1
    assert v[0].rule_id == "scope-enum"

    # Scope case
    cfg_case = LintConfig(scope_case="kebab-case")
    c_bad_case = parse_commit_message("feat(AuthService): add login")
    v = rule.validate(c_bad_case, cfg_case)
    assert len(v) == 1
    assert v[0].rule_id == "scope-case"


def test_rule_header_length():
    rule = RuleHeaderLength()
    config = LintConfig(min_header_length=15, max_header_length=30)

    # Too short
    short = parse_commit_message("feat: hi")
    v = rule.validate(short, config)
    assert any(violation.rule_id == "header-min-length" for violation in v)

    # Too long
    long_msg = "feat: this commit message header is deliberately way way way too long to pass"
    v = rule.validate(parse_commit_message(long_msg), config)
    assert any(violation.rule_id == "header-max-length" for violation in v)


def test_rule_subject():
    rule = RuleSubject()
    config = LintConfig(subject_case="lowercase", subject_no_trailing_period=True)

    # Trailing period
    c_period = parse_commit_message("fix: resolved race condition.")
    v = rule.validate(c_period, config)
    assert any(violation.rule_id == "subject-full-stop" for violation in v)

    # Uppercase start with lowercase rule
    c_upper = parse_commit_message("fix: Resolved race condition")
    v = rule.validate(c_upper, config)
    assert any(violation.rule_id == "subject-case" for violation in v)

    # Sentence case rule
    config_sentence = LintConfig(subject_case="sentence-case")
    c_lower = parse_commit_message("fix: resolved race condition")
    v_sentence = rule.validate(c_lower, config_sentence)
    assert any(violation.rule_id == "subject-case" for violation in v_sentence)

    # Empty subject
    c_empty_subj = parse_commit_message("feat:")
    v_empty = rule.validate(c_empty_subj, config)
    assert any(violation.rule_id == "subject-empty" for violation in v_empty)

    # Valid
    c_ok = parse_commit_message("fix: resolved race condition")
    assert len(rule.validate(c_ok, config)) == 0


def test_rule_body():
    rule = RuleBody()
    config = LintConfig(body_blank_line_required=True, max_body_line_length=40)

    # Missing blank line between header and body
    raw_no_blank = "fix(auth): fix token\nMissing blank line here."
    c1 = parse_commit_message(raw_no_blank)
    v1 = rule.validate(c1, config)
    assert any(v.rule_id == "body-leading-blank" for v in v1)

    # Long line in body
    raw_long_body = "fix(auth): fix token\n\nThis line in the body exceeds the forty character maximum line limit configured."
    c2 = parse_commit_message(raw_long_body)
    v2 = rule.validate(c2, config)
    assert any(v.rule_id == "body-max-line-length" for v in v2)

    # URL exemption in body
    raw_url = "fix(auth): fix token\n\nSee issue details at https://github.com/org/repo/issues/12345678901234567890."
    c3 = parse_commit_message(raw_url)
    v3 = rule.validate(c3, config)
    assert not any(v.rule_id == "body-max-line-length" for v in v3)


def test_rule_ticket():
    rule = RuleTicket()
    config = LintConfig(ticket_required=True, ticket_pattern=r"JIRA-\d+", ticket_in="any")

    # Ticket in scope
    c_scope = parse_commit_message("feat(JIRA-100): implement user profile")
    assert len(rule.validate(c_scope, config)) == 0

    # Ticket in subject
    c_subj = parse_commit_message("feat: JIRA-100 implement user profile")
    assert len(rule.validate(c_subj, config)) == 0

    # Ticket in footer
    c_footer = parse_commit_message("feat: implement user profile\n\nTicket: JIRA-100")
    assert len(rule.validate(c_footer, config)) == 0

    # Ticket missing
    c_missing = parse_commit_message("feat: implement user profile")
    v = rule.validate(c_missing, config)
    assert len(v) == 1
    assert v[0].rule_id == "ticket-required"
