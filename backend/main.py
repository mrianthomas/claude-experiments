import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from bluesky import search_recent_posts
from database import get_sightings, insert_sighting
from geocoder import extract_postcode, extract_retailer, geocode_postcode
from processor import process_posts

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))  # default 5 min

_last_poll: datetime | None = None


async def _poll_loop():
    global _last_poll
    while True:
        try:
            log.info("Polling BlueSky for mince pie sightings…")
            posts = await search_recent_posts(since=_last_poll)
            log.info(f"  {len(posts)} candidate posts found")
            if posts:
                stored = await process_posts(posts)
                log.info(f"  {len(stored)} new sightings stored")
            _last_poll = datetime.now(timezone.utc)
        except Exception as exc:
            log.error(f"Poll error: {exc}")
        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_poll_loop())
    yield
    task.cancel()


app = FastAPI(title="Mince Pie Monitor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/sightings")
async def list_sightings():
    return get_sightings(limit=500)


@app.post("/api/sightings")
async def submit_manual_sighting(body: dict):
    """Accept a manually submitted sighting from the web form."""
    text: str = body.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    postcode = extract_postcode(text) or body.get("postcode", "").strip() or None
    retailer = extract_retailer(text) or body.get("retailer", "").strip() or None

    lat = lng = None
    if postcode:
        coords = await geocode_postcode(postcode)
        if coords:
            lat, lng = coords

    sighting = {
        "post_text": text,
        "platform": "manual",
        "postcode": postcode,
        "retailer": retailer,
        "lat": lat,
        "lng": lng,
        "is_retail_sighting": True,
        "confidence": 1.0,
    }
    return insert_sighting(sighting)


# Serve the frontend in production (when ../frontend exists)
_frontend = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend):
    app.mount("/", StaticFiles(directory=_frontend, html=True), name="static")
