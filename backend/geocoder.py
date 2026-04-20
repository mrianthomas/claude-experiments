import re
import httpx

# Full UK postcode pattern (covers all valid formats)
POSTCODE_RE = re.compile(
    r'\b([A-PR-UWYZ][A-HK-Y]?\d[ABEHMNPRVWXY\d]?\s*\d[ABD-HJLNP-UW-Z]{2})\b',
    re.IGNORECASE,
)

RETAILERS = [
    ("marks & spencer", "M&S"),
    ("marks and spencer", "M&S"),
    ("m&s", "M&S"),
    ("sainsbury's", "Sainsbury's"),
    ("sainsburys", "Sainsbury's"),
    ("tesco", "Tesco"),
    ("asda", "Asda"),
    ("morrisons", "Morrisons"),
    ("waitrose", "Waitrose"),
    ("lidl", "Lidl"),
    ("aldi", "Aldi"),
    ("co-op", "Co-op"),
    ("coop", "Co-op"),
    ("the co-op", "Co-op"),
    ("cooperative", "Co-op"),
    ("iceland", "Iceland"),
    ("boots", "Boots"),
    ("greggs", "Greggs"),
    ("spar", "Spar"),
    ("costco", "Costco"),
    ("poundland", "Poundland"),
    ("home bargains", "Home Bargains"),
    ("b&m", "B&M"),
]


def extract_postcode(text: str) -> str | None:
    match = POSTCODE_RE.search(text)
    if match:
        # Normalise: uppercase, single space before inward code
        raw = match.group(1).upper().replace(" ", "")
        return raw[:-3] + " " + raw[-3:]
    return None


def extract_retailer(text: str) -> str | None:
    lower = text.lower()
    for needle, canonical in RETAILERS:
        if needle in lower:
            return canonical
    return None


async def geocode_postcode(postcode: str) -> tuple[float, float] | None:
    """Return (lat, lng) for a UK postcode via postcodes.io, or None."""
    clean = postcode.replace(" ", "").upper()
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"https://api.postcodes.io/postcodes/{clean}")
            if resp.status_code == 200:
                r = resp.json().get("result", {})
                lat, lng = r.get("latitude"), r.get("longitude")
                if lat and lng:
                    return float(lat), float(lng)
        except httpx.RequestError:
            pass
    return None
