"""One request per provider. Confirms the key works, the model id is real,
and shows the live rate-limit headers.

Run:
    uv run python days/day-01/lab/verify_keys.py

Budget: exactly 3 requests. Do not put this in a loop.
"""

from openai import OpenAI

from mandala.config import load_keys
from mandala.models import PROVIDERS

KEYS = load_keys()

for name, provider in PROVIDERS.items():
    api_key = getattr(KEYS, provider.key_attr)
    client = OpenAI(api_key=api_key, base_url=provider.base_url)

    try:
        raw = client.chat.completions.with_raw_response.create(
            model=provider.default_model,
            messages=[{"role": "user", "content": "reply with the single word: ok"}],
            max_tokens=5,
        )
    except Exception as exc:  # noqa: BLE001 - we want every failure shown
        print(f"{name:<12} FAILED  {type(exc).__name__}: {exc}")
        continue

    reply = raw.parse().choices[0].message.content
    remaining = raw.headers.get("x-ratelimit-remaining-requests", "(not reported)")
    reset = raw.headers.get("x-ratelimit-reset-requests", "(not reported)")
    print(f"{name:<12} ok  reply={reply!r}  requests_left={remaining}  resets_in={reset}")
