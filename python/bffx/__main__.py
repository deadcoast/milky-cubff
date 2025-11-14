"""
Entry point for running bffx as a module: python -m bffx
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
