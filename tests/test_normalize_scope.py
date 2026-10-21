from commit_scope_lint.rules import normalize_scope_case

def test_normalize_scope_case():
    assert normalize_scope_case(" CoreAPI ") == "coreapi"
