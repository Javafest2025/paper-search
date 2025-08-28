# arXiv API Test Endpoint

This document describes the new arXiv API test endpoint that allows testing the arXiv academic API with the full workflow (excluding PDF processing and storage).

## Overview

The arXiv API endpoint provides a way to test the arXiv academic paper search functionality in isolation, running the complete workflow including:

- ✅ Paper search via arXiv API
- ✅ Data normalization and enrichment
- ✅ Deduplication
- ✅ Filtering by domain and recency
- ✅ Relevance ranking
- ❌ PDF processing and storage (excluded for testing)

## API Endpoints

### 1. Test arXiv Search
**POST** `/api/v1/arxiv/test`

Test the arXiv API with full workflow.

#### Request Body
```json
{
    "queryTerms": ["machine learning", "optimization"],
    "domain": "Computer Science",
    "batchSize": 10,
    "correlationId": "optional-tracking-id"
}
```

#### Request Fields
- `queryTerms` (required): Array of search terms
- `domain` (optional): Research domain (default: "Computer Science")
- `batchSize` (optional): Target number of papers (default: 10)
- `correlationId` (optional): Tracking ID for the request

#### Response
```json
{
    "projectId": null,
    "correlationId": "optional-tracking-id",
    "papers": [
        {
            "title": "Paper Title",
            "doi": "10.1234/example.doi",
            "publicationDate": "2024-01-15",
            "venueName": "Conference Name",
            "publisher": "Publisher Name",
            "peerReviewed": true,
            "authors": [
                {"name": "Author Name", "affiliation": "Institution"}
            ],
            "citationCount": 42,
            "referenceCount": 15,
            "influentialCitationCount": 5,
            "isOpenAccess": true,
            "abstract": "Paper abstract...",
            "paperUrl": "https://arxiv.org/abs/1234.5678",
            "pdfUrl": "https://arxiv.org/pdf/1234.5678",
            "pdfContentUrl": null,
            "source": "arXiv"
        }
    ],
    "batchSize": 10,
    "queryTerms": ["machine learning", "optimization"],
    "domain": "Computer Science",
    "status": "COMPLETED",
    "searchStrategy": "arxiv_only",
    "totalSourcesUsed": 1,
    "aiEnhanced": false,
    "searchRounds": 1,
    "deduplicationStats": {
        "unique_papers": 10,
        "total_identifiers": 10,
        "duplicates_removed": 0
    }
}
```

### 2. Health Check
**GET** `/api/v1/arxiv/health`

Check the health of the arXiv API service.

#### Response
```json
{
    "status": "healthy",
    "service": "arxiv-test",
    "connectivity": "ok",
    "test_query_results": 1
}
```

### 3. Service Statistics
**GET** `/api/v1/arxiv/stats`

Get statistics about the arXiv test service.

#### Response
```json
{
    "service": "arxiv-test",
    "ai_available": false,
    "ai_ready": false,
    "config": {
        "recent_years_filter": 5,
        "ai_model": null
    }
}
```

## Usage Examples

### Using curl

```bash
# Test arXiv search
curl -X POST "http://localhost:8001/api/v1/arxiv/test" \
  -H "Content-Type: application/json" \
  -d '{
    "queryTerms": ["deep learning", "neural networks"],
    "domain": "Computer Science",
    "batchSize": 5
  }'

# Health check
curl "http://localhost:8001/api/v1/arxiv/health"

# Get stats
curl "http://localhost:8001/api/v1/arxiv/stats"
```

### Using Python

```python
import httpx
import asyncio

async def test_arxiv():
    async with httpx.AsyncClient() as client:
        # Test search
        response = await client.post(
            "http://localhost:8001/api/v1/arxiv/test",
            json={
                "queryTerms": ["machine learning", "optimization"],
                "domain": "Computer Science",
                "batchSize": 5
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Found {result['batchSize']} papers")
            for paper in result['papers']:
                print(f"- {paper['title']}")

# Run the test
asyncio.run(test_arxiv())
```

## Running the Test Script

A test script is provided to verify the endpoint works correctly:

```bash
# Make sure the service is running first
cd AI-Agents/paper-search
python test_arxiv_endpoint.py
```

## Configuration

The arXiv API endpoint uses the following configuration:

- **Recent Years Filter**: 5 years (configurable)
- **Search Strategy**: `arxiv_only` (single source)
- **AI Enhancement**: Disabled for single source testing
- **Deduplication**: Enabled
- **Metadata Enrichment**: Enabled
- **Relevance Ranking**: Enabled

## Differences from RabbitMQ Workflow

This endpoint is designed for testing and differs from the full RabbitMQ workflow in several ways:

1. **Single Source**: Only uses arXiv (no multi-source search)
2. **No PDF Processing**: Skips PDF downloading and B2 storage
3. **No AI Refinement**: Single round search only
4. **No Project ID**: Simplified request structure
5. **Direct Response**: Returns results directly instead of publishing to RabbitMQ

## Error Handling

The endpoint includes comprehensive error handling:

- **API Errors**: Returns 500 with error details
- **Invalid Requests**: Returns 422 for validation errors
- **Timeout**: 60-second timeout for search requests
- **Fallback**: Continues with partial results if enrichment fails

## Monitoring

The endpoint provides detailed logging:

- Search start/completion times
- Number of papers found
- Deduplication statistics
- Error details for debugging

## Next Steps

After testing arXiv, you can create similar endpoints for other academic APIs:

1. PubMed API endpoint
2. OpenAlex API endpoint
3. CORE API endpoint
4. Europe PMC API endpoint

Each endpoint will follow the same pattern but use different API clients and filters.
