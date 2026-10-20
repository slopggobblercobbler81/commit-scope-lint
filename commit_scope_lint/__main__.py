"""Entry point for python -m commit_scope_lint."""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
