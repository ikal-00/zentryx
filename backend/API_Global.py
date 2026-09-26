"""Backward-compatible API entrypoint.

New code should import ``backend.app``. This module remains temporarily so old
local commands or integrations do not fail after the repository reorganization.
"""

from .app import create_app, main

__all__ = ["create_app", "main"]


if __name__ == "__main__":
    main()
