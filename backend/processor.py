import asyncio

from classifier import classify_post
from database import insert_sighting, sighting_exists
from geocoder import extract_postcode, extract_retailer, geocode_postcode

CONFIDENCE_THRESHOLD = 0.65


async def process_post(post: dict) -> dict | None:
    """Classify and store a single post. Returns the stored sighting or None."""
    if sighting_exists(post["post_id"]):
        return None

    result = classify_post(post["text"])
    if not result.get("is_retail_sighting") or result.get("confidence", 0) < CONFIDENCE_THRESHOLD:
        return None

    postcode = extract_postcode(post["text"])
    retailer = extract_retailer(post["text"])

    lat = lng = None
    if postcode:
        coords = await geocode_postcode(postcode)
        if coords:
            lat, lng = coords

    sighting: dict = {
        "post_id": post["post_id"],
        "post_url": post["url"],
        "post_text": post["text"],
        "platform": "bluesky",
        "author_handle": post["author_handle"],
        "postcode": postcode,
        "retailer": retailer,
        "lat": lat,
        "lng": lng,
        "is_retail_sighting": True,
        "confidence": result.get("confidence"),
        "raw_data": post["raw"],
    }

    return insert_sighting(sighting)


async def process_posts(posts: list[dict]) -> list[dict]:
    """Process a batch concurrently; ignore errors in individual posts."""
    tasks = [process_post(p) for p in posts]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)
    return [o for o in outcomes if isinstance(o, dict)]
