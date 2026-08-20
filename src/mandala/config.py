"""Loads the three free-tier API keys, and fails loudly when one is missing.

Why this file exists
--------------------
A missing key otherwise surfaces as an HTTP 401 four layers deep inside a
framework, at 11pm, and costs you forty minutes. Failing early with a message
that says exactly what to do costs you four seconds.

Usage
-----
    >>> from mandala.config import load_keys
    >>> keys = load_keys()
    >>> keys.groq[:6]
    'gsk_ab'

    >>> import os; os.environ.pop("GROQ_API_KEY", None)
    >>> load_keys()
    Traceback (most recent call last):
    mandala.config.MissingKey: GROQ_API_KEY is not set. ...
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


class MissingKey(RuntimeError):
    """Raised when a required provider key is absent from the environment."""


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise MissingKey(
            f"{name} is not set. Copy .env.example to .env and fill it in. "
            f"See docs/RATE_BUDGET.md for where to get the key."
        )
    return value


@dataclass(frozen=True)
class Keys:
    """The three free-tier keys. Frozen so nothing can reassign one mid-run."""

    gemini: str
    groq: str
    openrouter: str


def load_keys() -> Keys:
    """Read all three keys from the environment. Raises MissingKey on the first absent one."""
    return Keys(
        gemini=_require("GEMINI_API_KEY"),
        groq=_require("GROQ_API_KEY"),
        openrouter=_require("OPENROUTER_API_KEY"),
    )
