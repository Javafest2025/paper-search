import asyncio
import time

from app.services.academic_apis.clients import ArxivClient


def test_arxiv_smoke_and_report(pytestconfig):
    report = pytestconfig._api_report  # type: ignore[attr-defined]
    client_name = "arXiv"
    report["clients"].setdefault(client_name, {})

    client = ArxivClient()

    started = time.time()
    results = asyncio.run(client.search_papers(query="machine learning", limit=10))
    duration = time.time() - started

    assert isinstance(results, list)
    fetched = len(results)
    titles = sum(1 for p in results if (p or {}).get("title"))

    # Try details for first result if available
    details_ok = 0
    if results:
        arxiv_id = results[0].get("arxivId")
        if arxiv_id:
            details = asyncio.run(client.get_paper_details(arxiv_id))
            if isinstance(details, dict):
                details_ok = 1

    report["clients"][client_name] = {
        "query": "machine learning",
        "duration_sec": round(duration, 2),
        "fetched_count": fetched,
        "with_title_count": titles,
        "details_success_count": details_ok,
        "limit": 10,
    }

    # Basic expectations
    assert fetched <= 10

