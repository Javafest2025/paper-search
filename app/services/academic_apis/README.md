# Academic APIs

This module provides unified access to multiple academic databases and APIs for research paper discovery and retrieval.

## Overview

The Academic APIs module offers a standardized interface to search, retrieve, and analyze academic papers from various sources:

- **Semantic Scholar**: AI-powered semantic search and citation analysis
- **arXiv**: Physics, mathematics, computer science preprints  
- **Crossref**: DOI metadata and citation information
- **PubMed**: Biomedical and life sciences literature
- **OpenAlex**: Comprehensive open catalog of scholarly papers
- **CORE**: Open access research aggregator
- **Unpaywall**: Open access PDF finder and status checker
- **Europe PMC**: Life sciences literature with full-text access
- **DBLP**: Computer science bibliography and publications
- **bioRxiv/medRxiv**: Biology and medical preprint servers
- **DOAJ**: Directory of Open Access Journals articles
- **BASE**: European academic search engine

## Architecture

```
app/services/academic_apis/
├── __init__.py
├── clients/
│   ├── __init__.py
│   ├── semantic_scholar_client.py
│   ├── arxiv_client.py
│   ├── crossref_client.py
│   ├── pubmed_client.py
│   ├── openalex_client.py
│   ├── core_client.py
│   ├── unpaywall_client.py
│   ├── europepmc_client.py
│   ├── dblp_client.py
│   ├── biorxiv_client.py
│   ├── doaj_client.py
│   └── base_search_client.py
├── common/
│   ├── __init__.py
│   ├── base_client.py
│   ├── exceptions.py
│   └── normalizers.py
├── parsers/
│   ├── __init__.py
│   ├── json_parser.py
│   ├── xml_parser.py
│   └── feed_parser.py
└── README.md
```

## Features

### Unified Interface
All clients implement the same base interface:
- `search_papers()`: Search for papers by query
- `get_paper_details()`: Get detailed paper information
- `get_citations()`: Get papers that cite a given paper
- `get_references()`: Get papers referenced by a given paper

### Data Normalization
Papers from different sources are normalized to a consistent format:

```python
{
    "title": "Paper Title",
    "doi": "10.1000/example",
    "publicationDate": "2023-01-15",
    "authors": [{"name": "Author Name"}],
    "abstract": "Paper abstract...",
    "citationCount": 42,
    "venue": "Journal Name",
    "isOpenAccess": true,
    "source": "semantic_scholar"
}
```

### Rate Limiting & Retries
- Automatic rate limiting with exponential backoff
- Request retries with configurable attempts
- Response caching to minimize API calls

### Error Handling
- Custom exception hierarchy
- Graceful degradation on API failures
- Comprehensive logging

## Client Documentation

### Semantic Scholar
High-quality academic search with AI-powered features.

**Features:**
- Semantic search capabilities
- Citation network analysis
- Author disambiguation
- Field of study classification

**Rate Limits:** 100 requests/minute (with API key)

### arXiv
Preprint repository for physics, mathematics, computer science.

**Features:**
- Subject classification
- Version tracking
- Author search
- Date range filtering

**Rate Limits:** 3 requests/second

### Crossref
DOI registration agency with extensive metadata.

**Features:**
- DOI resolution
- Publisher metadata
- Funding information
- ORCID integration

**Rate Limits:** 50 requests/second (polite pool)

### PubMed
Biomedical literature database.

**Features:**
- MeSH term search
- Clinical trial filters
- Publication type filtering
- PMID/PMC lookup

**Rate Limits:** 10 requests/second (with API key)

### OpenAlex
Comprehensive open catalog of scholarly papers across all disciplines.

**Features:**
- Multi-disciplinary paper search
- Citation and reference networks
- Author and institution data
- Concept classification
- Open access detection

**Rate Limits:** 100 requests/second (polite pool)

**Example:**
```python
from app.services.academic_apis.clients import OpenAlexClient

async with OpenAlexClient(email="your@email.com") as client:
    papers = await client.search_papers("machine learning", limit=10)
    for paper in papers:
        print(f"{paper['title']} - {paper['citationCount']} citations")
```

### CORE
Open access research aggregator with full-text access.

**Features:**
- Open access paper discovery
- Full-text PDF access
- Repository metadata
- Multi-disciplinary coverage

**Rate Limits:** 100 requests/hour (free tier)
**Authentication:** API key required

### Unpaywall
Find open access versions of academic papers.

**Features:**
- DOI-based OA status checking
- PDF download links
- Repository version tracking
- Bulk DOI processing

**Rate Limits:** Conservative (email required)
**Authentication:** Email contact required

### Europe PMC
Life sciences literature with enhanced features.

**Features:**
- Biomedical paper search
- MeSH term integration
- Full-text XML access
- Citation networks
- Clinical trial data

**Rate Limits:** Standard web limits

### DBLP
Computer science bibliography and publications.

**Features:**
- CS author and venue search
- Publication listings
- Conference/journal metadata
- Co-authorship data

**Rate Limits:** Conservative web scraping limits

### bioRxiv/medRxiv
Biology and medical preprint servers.

**Features:**
- Preprint search and discovery
- Category filtering (biology/medicine)
- Version tracking
- Author affiliation data

**Rate Limits:** Conservative API limits

### DOAJ
Directory of Open Access Journals articles.

**Features:**
- Open access journal articles
- Subject classification
- Publisher metadata
- Journal indexing information

**Rate Limits:** 60 requests/minute

### BASE
European academic search engine and OAI-PMH aggregator.

**Features:**
- European repository search
- OAI-PMH aggregated content
- Multi-disciplinary coverage
- Repository metadata

**Rate Limits:** 100 requests/minute

## Usage Examples

### Basic Search
```python
import asyncio
from app.services.academic_apis.clients import SemanticScholarClient

async def search_papers():
    async with SemanticScholarClient() as client:
        papers = await client.search_papers(
            query="deep learning",
            limit=20,
            filters={"year_range": (2020, 2023)}
        )
        
        for paper in papers:
            print(f"Title: {paper['title']}")
            print(f"Authors: {', '.join(a['name'] for a in paper['authors'])}")
            print(f"Citations: {paper['citationCount']}")
            print("-" * 50)

asyncio.run(search_papers())
```

### Multi-Source Search
```python
from app.services.academic_apis.clients import (
    SemanticScholarClient, OpenAlexClient, ArxivClient, PubMedClient
)

async def multi_source_search(query: str):
    clients = [
        SemanticScholarClient(),
        OpenAlexClient(),
        ArxivClient(), 
        PubMedClient()
    ]
    
    all_papers = []
    for client in clients:
        async with client:
            papers = await client.search_papers(query, limit=10)
            all_papers.extend(papers)
    
    # Remove duplicates by DOI
    unique_papers = {}
    for paper in all_papers:
        if paper['doi'] and paper['doi'] not in unique_papers:
            unique_papers[paper['doi']] = paper
    
    return list(unique_papers.values())
```

### Open Access Discovery
```python
from app.services.academic_apis.clients import (
    DOAJClient, COREClient, UnpaywallClient
)

async def find_open_access_papers(query: str):
    # Search DOAJ for open access journal articles
    async with DOAJClient() as doaj:
        doaj_papers = await doaj.search_papers(query, limit=10)
    
    # Search CORE for open access repository papers
    async with COREClient(api_key="your_key") as core:
        core_papers = await core.search_papers(query, limit=10)
    
    # Check papers for OA status with Unpaywall
    async with UnpaywallClient(email="your@email.com") as unpaywall:
        # Example: check a specific DOI
        oa_status = await unpaywall.get_paper_details("10.1000/example")
    
    return doaj_papers + core_papers
```

### Citation Analysis
```python
async def analyze_citations(paper_id: str):
    async with SemanticScholarClient() as client:
        # Get paper details
        paper = await client.get_paper_details(paper_id)
        print(f"Analyzing: {paper['title']}")
        
        # Get citing papers
        citations = await client.get_citations(paper_id, limit=50)
        print(f"Found {len(citations)} citing papers")
        
        # Get referenced papers
        references = await client.get_references(paper_id, limit=50)
        print(f"Found {len(references)} referenced papers")
        
        return {
            'paper': paper,
            'citations': citations,
            'references': references
        }
```

## Configuration

### API Keys
Set API keys as environment variables:

```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export PUBMED_API_KEY="your_email@example.com"
export CORE_API_KEY="your_core_key"
export UNPAYWALL_EMAIL="your_email@example.com"
```

### Rate Limiting
Configure rate limits in client initialization:

```python
client = SemanticScholarClient(
    rate_limit_calls=50,  # requests per period
    rate_limit_period=60,  # period in seconds
    max_retries=3
)
```

## Error Handling

The module provides specific exceptions for different error types:

```python
from app.services.academic_apis.common import APIError, RateLimitError

try:
    papers = await client.search_papers("query")
except RateLimitError:
    print("Rate limit exceeded, waiting...")
    await asyncio.sleep(60)
except APIError as e:
    print(f"API error: {e}")
```

## Best Practices

1. **Use async context managers** to ensure proper cleanup
2. **Implement exponential backoff** for rate limit handling
3. **Cache responses** when making repeated requests
4. **Respect API rate limits** and terms of service
5. **Normalize data** before storing or processing
6. **Handle errors gracefully** with fallback strategies
7. **Use appropriate APIs** for specific use cases:
   - **Semantic Scholar/OpenAlex**: General academic search
   - **PubMed/Europe PMC**: Biomedical research
   - **arXiv/bioRxiv**: Preprints and early research
   - **CORE/DOAJ**: Open access focused search
   - **Unpaywall**: OA status checking
   - **DBLP**: Computer science publications
   - **BASE**: European repository content

## Testing

Run the test suite:

```bash
pytest tests/academic_apis/ -v
```

For integration tests with real APIs:

```bash
pytest tests/academic_apis/ -v --integration
```

## Contributing

When adding new academic sources:

1. Create a new client class extending `BaseAcademicClient`
2. Implement all required abstract methods
3. Add source-specific parsing in `JSONParser` or `XMLParser`
4. Add source recognition in `BaseAcademicClient._get_source_name()`
5. Update the client imports in `__init__.py`
6. Create comprehensive tests
7. Update documentation

See existing clients for implementation patterns and best practices. 