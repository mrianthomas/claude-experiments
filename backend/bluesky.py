from datetime import datetime, timezone

import httpx

SEARCH_URL = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"

# Search terms — cast wide, classifier will filter
SEARCH_TERMS = ["mince pie", "mince pies", "mincepie", "mincepies"]


def _post_url(handle: str, uri: str) -> str:
    rkey = uri.split("/")[-1]
    return f"https://bsky.app/profile/{handle}/post/{rkey}"


async def search_recent_posts(since: datetime | None = None) -> list[dict]:
    """Return new BlueSky posts mentioning mince pies, optionally filtered by time."""
    seen: set[str] = set()
    results: list[dict] = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        for term in SEARCH_TERMS:
            try:
                resp = await client.get(
                    SEARCH_URL, params={"q": term, "limit": 25, "sort": "latest"}
                )
                resp.raise_for_status()
            except httpx.HTTPError:
                continue

            for post in resp.json().get("posts", []):
                uri = post.get("uri", "")
                if not uri or uri in seen:
                    continue
                seen.add(uri)

                created_at_str = post.get("record", {}).get("createdAt", "")
                if since and created_at_str:
                    try:
                        post_time = datetime.fromisoformat(
                            created_at_str.replace("Z", "+00:00")
                        )
                        if post_time <= since:
                            continue
                    except ValueError:
                        pass

                handle = post.get("author", {}).get("handle", "")
                results.append(
                    {
                        "post_id": uri,
                        "text": post.get("record", {}).get("text", ""),
                        "author_handle": handle,
                        "created_at": created_at_str,
                        "url": _post_url(handle, uri),
                        "raw": post,
                    }
                )

    return results
