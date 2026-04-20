import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _client


def insert_sighting(data: dict) -> dict:
    result = get_client().table("sightings").insert(data).execute()
    return result.data[0] if result.data else {}


def sighting_exists(post_id: str) -> bool:
    result = (
        get_client()
        .table("sightings")
        .select("id")
        .eq("post_id", post_id)
        .execute()
    )
    return len(result.data) > 0


def get_sightings(limit: int = 500) -> list[dict]:
    result = (
        get_client()
        .table("sightings")
        .select(
            "id,created_at,post_url,post_text,author_handle,"
            "postcode,retailer,lat,lng,platform,confidence"
        )
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data
