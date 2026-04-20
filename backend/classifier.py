import json
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

_client: anthropic.Anthropic | None = None

_SYSTEM = """\
You classify social media posts to decide whether they describe mince pies being \
available for sale in UK shops or supermarkets.

Reply ONLY with valid JSON — no prose, no markdown:
{"is_retail_sighting": <bool>, "confidence": <0.0–1.0>, "reasoning": "<one sentence>"}

A RETAIL SIGHTING means the post describes:
• Seeing or spotting mince pies in a shop, supermarket or retailer
• Mince pies going on sale or appearing on shelves (often noted early — June to November)
• Buying or purchasing mince pies from a retailer
• A retailer stocking or advertising mince pies

NOT a retail sighting:
• Making or baking mince pies at home
• Eating mince pies (unless combined with mention of buying them)
• Recipes or cooking advice
• General nostalgia or opinions unrelated to current availability
• Historical or future references ("last year", "can't wait for")"""


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


def classify_post(text: str) -> dict:
    """Return classification dict with is_retail_sighting, confidence, reasoning."""
    message = get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        system=[
            {
                "type": "text",
                "text": _SYSTEM,
                "cache_control": {"type": "ephemeral"},  # cache the system prompt
            }
        ],
        messages=[{"role": "user", "content": f"Post: {text}"}],
    )
    raw = message.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"is_retail_sighting": False, "confidence": 0.0, "reasoning": "parse error"}
