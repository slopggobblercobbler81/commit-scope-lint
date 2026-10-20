import time
import pytest
from commit_scope_lint.parser import parse_commit_message

def test_throughput_commit_parsing():
    """Test that parsing 1,000 commit messages takes less than 100ms."""
    messages = [
        f"feat(auth-{i}): add login endpoint support for feature #{i}"
        for i in range(1000)
    ]
    
    start_time = time.perf_counter()
    for msg in messages:
        parse_commit_message(msg)
    end_time = time.perf_counter()
    
    duration_ms = (end_time - start_time) * 1000.0
    print(f"\nParsed 1,000 commit messages in {duration_ms:.2f}ms")
    assert duration_ms < 100.0, f"Benchmark failed: took {duration_ms:.2f}ms (expected <100ms)"
