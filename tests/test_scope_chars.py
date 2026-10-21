from commit_scope_lint.rules import is_alphanumeric_scope

def test_is_alphanumeric_scope():
    assert is_alphanumeric_scope("auth-service") is True
    assert is_alphanumeric_scope("api_v2") is True
    assert is_alphanumeric_scope("invalid scope with spaces") is False
    assert is_alphanumeric_scope("auth$#") is False
