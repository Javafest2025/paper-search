import asyncio
import os
import time

from app.services.academic_apis.clients import UnpaywallClient


def test_unpaywall_report_if_configured(pytestconfig):
    report = pytestconfig._api_report  # type: ignore[attr-defined]
    client_name = "Unpaywall"
    email = os.getenv("UNPAYWALL_EMAIL")
    if not email:
        report["clients"][client_name] = {"skipped": True, "reason": "UNPAYWALL_EMAIL not set"}
        return

    client = UnpaywallClient(email=email)
    started = time.time()
    results = asyncio.run(client.search_papers(query="transformers", limit=10))
    duration = time.time() - started

    fetched = len(results)
    titles = sum(1 for p in results if (p or {}).get("title"))
    report["clients"][client_name] = {
        "query": "transformers",
        "duration_sec": round(duration, 2),
        "fetched_count": fetched,
        "with_title_count": titles,
        "limit": 10,
    }

    assert fetched <= 10


