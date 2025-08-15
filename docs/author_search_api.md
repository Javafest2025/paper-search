# Author Search API Documentation

## Overview

The Author Search API provides comprehensive author information by searching across multiple academic databases simultaneously. It aggregates data from various sources to provide robust and validated author profiles.

## Features

- **Multi-Source Search**: Searches across 5+ academic databases
- **Cross-Validation**: Validates data across multiple sources
- **Comprehensive Data**: Returns detailed author profiles with metrics
- **Confidence Scoring**: Provides confidence scores for data quality
- **Real-time Results**: Fetches live data from academic APIs

## API Endpoints

### 1. POST /api/v1/authors/search

Search for author information using POST request with JSON body.

**Request Body:**
```json
{
  "name": "Yann LeCun",
  "institution": "Meta AI",  // Optional
  "field_of_study": "Computer Science",  // Optional
  "email": "yann.lecun@meta.com"  // Optional
}
```

**Response:**
```json
{
  "author_id": "1688882",
  "name": "Yann LeCun",
  "orcid": "0000-0002-1825-0097",
  "affiliations": [
    {
      "institution_id": "meta-ai",
      "institution_name": "Meta AI",
      "country": "USA",
      "start_date": "2013-12-01",
      "end_date": null
    }
  ],
  "homepage_url": "https://yann.lecun.com",
  "email": null,
  "h_index": 32,
  "paper_count": 161,
  "citation_count": 134465,
  "fields_of_study": ["Computer Science", "Machine Learning"],
  "profile_image_url": "https://example.com/yann-lecun.jpg",
  "last_updated": "2025-08-13T20:51:58.127352",
  "sources": ["openalex", "semantic_scholar", "pubmed", "europepmc"],
  "confidence_score": 1.0
}
```

### 2. GET /api/v1/authors/search/{name}

Search for author information using GET request with query parameters.

**URL Parameters:**
- `name` (path): Author name to search for
- `institution` (query, optional): Institution name
- `field_of_study` (query, optional): Field of study
- `email` (query, optional): Email address

**Example:**
```
GET /api/v1/authors/search/Yann%20LeCun?institution=Meta%20AI&field_of_study=Computer%20Science
```

## Data Sources

The API searches across the following academic databases:

1. **Semantic Scholar** - Comprehensive academic database with citation networks
2. **OpenAlex** - Open academic knowledge graph
3. **DBLP** - Computer science bibliography
4. **Europe PMC** - Life sciences literature
5. **PubMed** - Biomedical literature

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `author_id` | string | Unique identifier for the author |
| `name` | string | Author's full name |
| `orcid` | string | ORCID identifier (if available) |
| `affiliations` | array | List of institutional affiliations |
| `homepage_url` | string | Author's homepage URL |
| `email` | string | Email address (if available) |
| `h_index` | integer | H-index metric |
| `paper_count` | integer | Total number of papers found |
| `citation_count` | integer | Total citation count |
| `fields_of_study` | array | List of research fields |
| `profile_image_url` | string | Profile image URL |
| `last_updated` | string | Timestamp of last data update |
| `sources` | array | List of data sources used |
| `confidence_score` | float | Data quality confidence (0.0-1.0) |

## Confidence Scoring

The confidence score is calculated based on:
- Number of sources providing data (0.2 per source)
- Presence of papers (0.3 if papers found)
- Data completeness and quality

**Score Ranges:**
- 0.0-0.3: Low confidence (single source, minimal data)
- 0.4-0.7: Medium confidence (multiple sources, some data)
- 0.8-1.0: High confidence (multiple sources, comprehensive data)

## Error Handling

### 404 Not Found
```json
{
  "detail": "No author information found for 'NonExistentAuthor'"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Usage Examples

### Python Example
```python
import requests

# Search for an author
response = requests.post("http://localhost:8000/api/v1/authors/search", 
    json={"name": "Yann LeCun"})
    
if response.status_code == 200:
    author_data = response.json()
    print(f"Found {author_data['paper_count']} papers")
    print(f"Confidence: {author_data['confidence_score']}")
```

### cURL Example
```bash
curl -X POST "http://localhost:8000/api/v1/authors/search" \
     -H "Content-Type: application/json" \
     -d '{"name": "Yann LeCun"}'
```

## Performance

- **Response Time**: 5-15 seconds (depending on API availability)
- **Concurrent Searches**: All sources are queried simultaneously
- **Rate Limiting**: Respects individual API rate limits
- **Caching**: No caching implemented (real-time data)

## Best Practices

1. **Use Full Names**: Provide complete author names for better matching
2. **Include Context**: Add institution or field of study for disambiguation
3. **Handle Errors**: Always check for 404 responses for unknown authors
4. **Check Confidence**: Use confidence scores to assess data quality
5. **Multiple Sources**: The API automatically validates across sources

## Limitations

- Some APIs may have rate limits
- Not all authors will have complete profiles
- ORCID and email information may not be available
- Profile images are not currently supported
- H-index calculation may vary by source

## Future Enhancements

- [ ] Add Google Scholar integration
- [ ] Implement profile image fetching
- [ ] Add citation network analysis
- [ ] Support for co-author relationships
- [ ] Enhanced affiliation parsing
- [ ] Real-time h-index calculation
