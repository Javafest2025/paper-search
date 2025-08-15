import asyncio
import time

from app.services.academic_apis.clients import OpenAlexClient


def test_openalex_smoke_and_report(pytestconfig):
    report = pytestconfig._api_report  # type: ignore[attr-defined]
    client_name = "OpenAlex"
    report["clients"].setdefault(client_name, {})

    client = OpenAlexClient()
    started = time.time()
    results = asyncio.run(client.search_papers(query="artificial intelligence", limit=10))
    duration = time.time() - started

    assert isinstance(results, list)
    fetched = len(results)
    titles = sum(1 for p in results if (p or {}).get("title"))

    report["clients"][client_name] = {
        "query": "artificial intelligence",
        "duration_sec": round(duration, 2),
        "fetched_count": fetched,
        "with_title_count": titles,
        "limit": 10,
    }

    assert fetched <= 10


