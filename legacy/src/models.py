"""The model pins. One place, so a rotated free model is a one-line fix.

Free-tier rosters rotate WITHOUT NOTICE — especially OpenRouter's `:free` list.
Never write a model id anywhere else in this project. Import from here.

Re-checked every Friday by the freshness routine (Principle 13).

Usage
-----
    >>> from mandala.models import FAST_LOOP, PROVIDERS
    >>> PROVIDERS["groq"].base_url
    'https://api.groq.com/openai/v1'
"""

from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------
# Model pins — FILL THESE IN from the live provider consoles on Day 1.
# The test `test_model_pins_are_explicit` fails while a placeholder remains.
# --------------------------------------------------------------------------
# Read from the live rosters (GET /models) on 2026-08-20 and confirmed with one
# real completion each by days/day-01/lab/verify_keys.py. Re-checked every Friday.
WORKHORSE = "gemini-3.7-flash"  # Gemini: labs, capstone, long context
FAST_LOOP = "openai/gpt-oss-20b"  # Groq:   dev loop, tool-calling drills
JUDGE = "nvidia/nemotron-3-super-120b-a12b:free"  # OpenRouter: evals. Different family from
#                                                  # both WORKHORSE and FAST_LOOP.
OFFLINE = "<ollama-local-model>"  # Ollama: optional outage branch — NOT installed here


@dataclass(frozen=True)
class Provider:
    """One OpenAI-compatible endpoint: which key it uses and where it lives."""

    key_attr: str  # the attribute name on mandala.config.Keys
    base_url: str  # the OpenAI-compatible endpoint
    default_model: str  # the pinned model for this provider


PROVIDERS: dict[str, Provider] = {
    "gemini": Provider(
        key_attr="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        default_model=WORKHORSE,
    ),
    "groq": Provider(
        key_attr="groq",
        base_url="https://api.groq.com/openai/v1",
        default_model=FAST_LOOP,
    ),
    "openrouter": Provider(
        key_attr="openrouter",
        base_url="https://openrouter.ai/api/v1",
        default_model=JUDGE,
    ),
}
