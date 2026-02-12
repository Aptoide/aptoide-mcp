import os
import re

import httpx
from mcp.server.fastmcp import FastMCP

APTOIDE_BASE = "https://ws75.aptoide.com/api/7"

port = int(os.environ.get("PORT", "8000"))
mcp = FastMCP(
    "aptoide",
    instructions=(
        "Search and lookup Android apps on the Aptoide app store. "
        "IMPORTANT: The search API matches keywords against app names and descriptions — "
        "it does NOT support category-based queries. Searches like 'social media', "
        "'battle royale', or 'productivity' will return poor results. "
        "Instead, use your knowledge of popular apps to search by specific app names "
        "(e.g. search 'instagram' instead of 'social media', 'fortnite' instead of "
        "'battle royale'). For category-style requests, run multiple searches for "
        "well-known apps in that category by name. "
        "ALWAYS prominently display the Aptoide URL for each app in your response — "
        "this is the most important link for users to visit the app page."
    ),
    host="0.0.0.0",
    port=port,
)

client = httpx.AsyncClient(
    timeout=httpx.Timeout(10.0),
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
)


def _format_size(size_bytes):
    if size_bytes is None:
        return None
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _build_url(uname):
    if not uname:
        return None
    if not re.match(r'^[a-zA-Z0-9._-]+$', uname):
        return None
    return f"https://{uname}.en.aptoide.com/app"


def _extract_app_detail(data):
    file_data = data.get("file") or {}
    malware = file_data.get("malware") or {}
    developer = data.get("developer") or {}
    store = data.get("store") or {}
    media = data.get("media") or {}
    stats = data.get("stats") or {}
    rating = stats.get("rating") or {}
    age = data.get("age") or {}

    return {
        "name": data.get("name"),
        "package_name": data.get("package"),
        "version": file_data.get("vername"),
        "developer": developer.get("name"),
        "store": store.get("name"),
        "description": media.get("description"),
        "size": _format_size(file_data.get("filesize")),
        "downloads": stats.get("downloads"),
        "rating_avg": rating.get("avg"),
        "rating_votes": rating.get("total"),
        "icon_url": data.get("icon"),
        "graphic_url": data.get("graphic"),
        "age_rating": age.get("name"),
        "malware_rank": malware.get("rank"),
        "updated": data.get("updated"),
        "url": _build_url(data.get("uname")),
    }


def _extract_app_summary(item):
    file_data = item.get("file") or {}
    malware = file_data.get("malware") or {}
    developer = item.get("developer") or {}
    stats = item.get("stats") or {}
    rating = stats.get("rating") or {}

    return {
        "name": item.get("name"),
        "package_name": item.get("package"),
        "version": file_data.get("vername"),
        "developer": developer.get("name"),
        "downloads": stats.get("downloads"),
        "rating_avg": rating.get("avg"),
        "size": _format_size(item.get("size")),
        "icon_url": item.get("icon"),
        "malware_rank": malware.get("rank"),
        "url": _build_url(item.get("uname")),
    }


@mcp.tool()
async def get_app(package_name: str) -> dict:
    """Get detailed information about an Android app from the Aptoide app store.

    Args:
        package_name: The Android package name, e.g. "com.whatsapp" or "com.android.chrome"

    Example: get_app(package_name="com.whatsapp")

    Always show the 'url' field prominently — it links to the app page on Aptoide.
    """
    if len(package_name) > 200:
        return {"error": "Package name too long (max 200 characters)."}

    try:
        resp = await client.get(f"{APTOIDE_BASE}/app/get/package_name={package_name}/aab=1")
    except httpx.TimeoutException:
        return {"error": "Failed to reach Aptoide API: request timed out."}
    except httpx.HTTPError:
        return {"error": "Failed to reach Aptoide API."}

    if resp.status_code == 404:
        return {
            "error": f"App not found for package '{package_name}'. "
            "Try using search_apps to find the correct package name.",
        }
    if resp.status_code != 200:
        return {"error": "Aptoide API error", "status_code": resp.status_code}

    body = resp.json()
    info = body.get("info") or {}

    if info.get("status") != "OK":
        return {
            "error": f"App not found for package '{package_name}'. "
            "Try using search_apps to find the correct package name.",
        }

    nodes = body.get("nodes") or {}
    meta = nodes.get("meta") or {}
    data = meta.get("data") or {}

    if not data:
        return {
            "error": f"App not found for package '{package_name}'. "
            "Try using search_apps to find the correct package name.",
        }

    return _extract_app_detail(data)


@mcp.tool()
async def search_apps(query: str, limit: int = 10) -> dict:
    """Search for Android apps on the Aptoide app store.

    The search matches keywords against app names and descriptions. It works best
    with specific app names (e.g. "whatsapp", "instagram", "fortnite") rather than
    generic categories (e.g. "social media", "battle royale").

    For category-based requests, search for well-known apps by name individually
    instead of using a generic category term.

    Args:
        query: Search term, 2-100 characters. Use specific app names for best results.
        limit: Maximum number of results to return (1-50, default 10)

    Always show the 'url' field prominently for each app — it links to the app page on Aptoide.

    Examples:
        search_apps(query="whatsapp", limit=5)
        search_apps(query="instagram", limit=3)
    """
    if not query or len(query) < 2:
        return {"error": "Query must be at least 2 characters."}
    if len(query) > 200:
        return {"error": "Query too long (max 200 characters)."}

    limit = max(1, min(50, limit))

    try:
        resp = await client.get(f"{APTOIDE_BASE}/apps/search/query={query}/limit={limit}/aab=1")
        resp.raise_for_status()
    except httpx.TimeoutException:
        return {"error": "Failed to reach Aptoide API: request timed out."}
    except httpx.HTTPStatusError as e:
        return {"error": "Aptoide API error", "status_code": e.response.status_code}
    except httpx.HTTPError:
        return {"error": "Failed to reach Aptoide API."}

    body = resp.json()
    datalist = body.get("datalist") or {}
    items = datalist.get("list") or []

    apps = [_extract_app_summary(item) for item in items]

    return {
        "query": query,
        "total_results": datalist.get("total", 0),
        "apps": apps,
    }


@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
