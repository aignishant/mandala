"""Deliberately hit a rate limit once, and look at what it actually is.

Budget: up to ~25 tiny requests on Groq, which has the most generous daily
allowance of the three. Do NOT point this at Gemini.

Run:
    uv run python days/day-02/lab/trigger_429.py
"""

from mandala.config import load_keys
from mandala.models import PROVIDERS
from openai import OpenAI, RateLimitError

provider = PROVIDERS["groq"]
client = OpenAI(api_key=load_keys().groq, base_url=provider.base_url)

for attempt in range(1, 26):
    try:
        client.chat.completions.create(
            model=provider.default_model,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1,
        )
        print(f"{attempt:>3}  ok")
    except RateLimitError as exc:
        print(f"{attempt:>3}  RATE LIMITED")
        print(f"     type      : {type(exc).__name__}")
        print(f"     status    : {exc.status_code}")
        print(f"     retry-after: {exc.response.headers.get('retry-after')}")
        print(f"     body      : {exc.message[:200]}")
        break
else:
    print("no 429 in 25 requests — your limits are generous today; note that in RATE_BUDGET.md")
