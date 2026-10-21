from commit_scope_lint.rules import is_kebab_or_snake

def test_is_kebab_or_snake():
    assert is_kebab_or_snake("user-auth") is True
    assert is_kebab_or_snake("user_auth") is True
    assert is_kebab_or_snake("userAuth") is False
