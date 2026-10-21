from commit_scope_lint.rules import count_commit_body_lines

def test_count_commit_body_lines():
    body = "Line 1\n\nLine 2\nLine 3\n"
    assert count_commit_body_lines(body) == 3
