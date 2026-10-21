from commit_scope_lint.rules import is_allowed_ticket_prefix

def test_is_allowed_ticket_prefix():
    assert is_allowed_ticket_prefix("JIRA-123", ["JIRA", "BUG"]) is True
    assert is_allowed_ticket_prefix("XYZ-123", ["JIRA", "BUG"]) is False
