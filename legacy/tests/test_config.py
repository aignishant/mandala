"""Day-1 guardrails: keys fail loudly, and model pins are real."""

import pytest
from mandala.config import MissingKey, load_keys

from mandala import models


def test_missing_key_fails_loudly(monkeypatch):
    """A missing key must raise MissingKey naming the variable, not a bare KeyError."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(MissingKey, match="GEMINI_API_KEY"):
        load_keys()


def test_blank_key_is_treated_as_missing(monkeypatch):
    """A key line left empty in .env is the same failure as no line at all."""
    monkeypatch.setenv("GROQ_API_KEY", "   ")
    with pytest.raises(MissingKey, match="GROQ_API_KEY"):
        load_keys()


@pytest.mark.parametrize("name", ["WORKHORSE", "FAST_LOOP", "JUDGE"])
def test_model_pins_are_explicit(name):
    """Principle 4: no placeholders. Red until you visit the consoles and fill them in."""
    value = getattr(models, name)
    assert value, f"{name} is empty"
    assert "<" not in value, f"{name} is still the placeholder {value!r}"
