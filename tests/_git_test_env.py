"""Environment helpers for disposable Git repositories in tests."""

from __future__ import annotations

import os
from contextlib import contextmanager


def isolated_git_environment() -> dict[str, str]:
    """Keep ARCANA's real-repository object-store overrides out of temp repos."""
    env = os.environ.copy()
    env.pop("GIT_OBJECT_DIRECTORY", None)
    env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    return env


@contextmanager
def isolate_git_object_overrides():
    """Temporarily isolate nested Git calls that operate on a disposable repo."""
    names = ("GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES")
    previous = {name: os.environ.get(name) for name in names}
    try:
        for name in names:
            os.environ.pop(name, None)
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
