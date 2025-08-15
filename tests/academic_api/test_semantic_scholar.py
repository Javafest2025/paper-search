import asyncio
import os
import time

from app.services.academic_apis.clients import SemanticScholarClient


def test_semantic_scholar_report_if_configured(pytestconfig):
    report = pytestconfig._api_report  # type: ignore[attr-defined]
    client_name = "SemanticScholar"
    api_key = os.getenv("S2_API_KEY")  # Optional - can work without it
    
    client = SemanticScholarClient(api_key=api_key)
    started = time.time()
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


def test_semantic_scholar_get_paper_details_if_available(pytestconfig):
    report = pytestconfig._api_report  # type: ignore[attr-defined]
    client_name = "SemanticScholar"
    api_key = os.getenv("S2_API_KEY")  # Optional - can work without it

    client = SemanticScholarClient(api_key=api_key)
    
    # First search for a paper to get an ID
    results = asyncio.run(client.search_papers(query="machine learning", limit=1))
    if not results:
        return  # Skip if no search results
    
    paper = results[0]
    paper_id = paper.get("semanticScholarId") or paper.get("doi")
    if not paper_id:
        return  # Skip if no paper ID
    
    # Get detailed information
    details = asyncio.run(client.get_paper_details(paper_id))
    if details is not None:
        assert isinstance(details, dict)
        if details.get("title"):
            assert isinstance(details["title"], str)
