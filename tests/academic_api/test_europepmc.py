import asyncio
import os
import time

from app.services.academic_apis.clients import EuropePMCClient


def test_europepmc_report_if_configured(pytestconfig):
    report = pytestconfig._api_report  # type: ignore[attr-defined]
    client_name = "EuropePMC"
    
    # Europe PMC is free to use, no API key required
    client = EuropePMCClient()
    started = time.time()
    results = asyncio.run(client.search_papers(query="cancer", limit=10))
    duration = time.time() - started

    fetched = len(results)
    titles = sum(1 for p in results if (p or {}).get("title"))
    report["clients"][client_name] = {
        "query": "cancer",
        "duration_sec": round(duration, 2),
        "fetched_count": fetched,
        "with_title_count": titles,
        "limit": 10,
    }

    assert fetched <= 10


def test_europepmc_get_paper_details_if_available(pytestconfig):
    report = pytestconfig._api_report  # type: ignore[attr-defined]
    client_name = "EuropePMC"

    client = EuropePMCClient()
    
    # First search for a paper to get an ID
    results = asyncio.run(client.search_papers(query="cancer", limit=1))
    if not results:
        return  # Skip if no search results
    
    paper = results[0]
    paper_id = paper.get("pmid") or paper.get("pmcid") or paper.get("doi")
    if not paper_id:
        return  # Skip if no paper ID
    
    # Get detailed information
    details = asyncio.run(client.get_paper_details(paper_id))
    if details is not None:
        assert isinstance(details, dict)
        if details.get("title"):
            assert isinstance(details["title"], str)
