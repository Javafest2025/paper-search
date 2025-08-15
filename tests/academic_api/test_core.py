import asyncio
import os
import time

from app.services.academic_apis.clients import COREClient


def test_core_report_if_configured(pytestconfig):
    report = pytestconfig._api_report  # type: ignore[attr-defined]
    client_name = "CORE"
    api_key = os.getenv("CORE_API_KEY")
    if not api_key:
        report["clients"][client_name] = {"skipped": True, "reason": "CORE_API_KEY not set"}
        return

    client = COREClient(api_key=api_key)
    started = time.time()
    # Broaden query for better recall on CORE
    results = asyncio.run(client.search_papers(query="machine learning", limit=10))
    duration = time.time() - started

    fetched = len(results)
    titles = sum(1 for p in results if (p or {}).get("title"))
    report["clients"][client_name] = {
        "query": "machine learning",
        "duration_sec": round(duration, 2),
        "fetched_count": fetched,
        "with_title_count": titles,
        "limit": 10,
    }

    assert fetched <= 10


