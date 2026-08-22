"""Shared pytest configuration.

Three test tiers:
  * unit      — no marker, no network, always runs
  * cassette  — @pytest.mark.vcr, replays a recorded response, always runs
  * live      — @pytest.mark.live, real provider, SKIPPED unless you pass -m live

Run the free suite:      uv run pytest
Run the live suite:      uv run pytest -m live
Re-record a cassette:    uv run pytest -m live --record-mode=rewrite
"""

from __future__ import annotations

import json
import pathlib

import pytest

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def pytest_collection_modifyitems(config, items):
    """Skip every @pytest.mark.live test unless the run explicitly asked for them."""
    if "live" in (config.getoption("-m") or ""):
        return
    skip_live = pytest.mark.skip(reason="live test — run with `uv run pytest -m live`")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(scope="session")
def vcr_config():
    """How cassettes are recorded. Secrets are stripped before anything hits disk."""
    return {
        "filter_headers": [
            ("authorization", "REDACTED"),
            ("x-goog-api-key", "REDACTED"),
            ("api-key", "REDACTED"),
        ],
        "filter_query_parameters": [("key", "REDACTED")],
        "record_mode": "once",
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
    }


@pytest.fixture
def golden_tickets() -> list[dict]:
    """The ten invented tickets. Used by every phase from here to Day 90."""
    return json.loads((FIXTURES / "tickets.json").read_text(encoding="utf-8"))
