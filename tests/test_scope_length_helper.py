from commit_scope_lint.rules import is_valid_scope_length

def test_is_valid_scope_length():
    assert is_valid_scope_length("core") is True
    assert is_valid_scope_length("") is False
    assert is_valid_scope_length("x" * 51) is False
