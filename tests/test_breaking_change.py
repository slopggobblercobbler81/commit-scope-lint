import pytest
from commit_scope_lint.parser import parse_commit_message


def test_breaking_change_bang_syntax():
    msg = "feat(auth)!: change token format"
    parsed = parse_commit_message(msg)
    assert parsed.type == "feat"
    assert parsed.scope == "auth"
    assert parsed.is_breaking is True
    assert parsed.subject == "change token format"
