# Author Search API Documentation

This document describes the Author Search API endpoints that provide access to Semantic Scholar's author data through our service.

## Overview

The Author Search API allows you to search for academic authors by name using the Semantic Scholar API. It provides multiple endpoints for different use cases and includes proper error handling and rate limiting.

## Base URL

```
http://localhost:8001/api/v1/authors
```

## Endpoints

### 1. Search Authors (POST)

**Endpoint:** `POST /api/v1/authors/search`

**Description:** Search for authors by name with full control over parameters.

**Request Body:**
```json
{
  "query": "Oren Etzioni",
  "limit": 100,
  "offset": 0,
  "fields": "name,affiliations,url,homepage,paperCount,citationCount,hIndex"
}
```

**Parameters:**
- `query` (string, required): Author name to search for
- `limit` (integer, optional): Number of results to return (1-1000, default: 100)
- `offset` (integer, optional): Starting position for pagination (default: 0)
- `fields` (string, optional): Comma-separated list of fields to return
- `exact_match` (boolean, optional): Filter results to exact name matches only (default: true)

**Response:**
```json
{
  "total": 15117,
  "offset": 0,
  "next": 100,
  "data": [
    {
      "authorId": "1741101",
      "name": "Oren Etzioni",
      "url": "https://www.semanticscholar.org/author/1741101",
      "affiliations": ["Allen Institute for AI"],
      "homepage": "https://allenai.org/",
      "paperCount": 10,
      "citationCount": 50,
      "hIndex": 5,
      "externalIds": {
        "DBLP": [123]
      },
      "papers": [
        {
          "paperId": "5c5751d45e298cea054f32b392c12c61027d2fe7",
          "corpusId": 215416146,
          "title": "Construction of the Literature Graph in Semantic Scholar",
          "year": 2020,
          "citationCount": 453,
          "venue": "Annual Meeting of the Association for Computational Linguistics"
        }
      ]
    }
  ]
}
```

### 2. Search Authors by Name (GET)

**Endpoint:** `GET /api/v1/authors/search/{name}`

**Description:** Convenience GET endpoint that takes the author name as a path parameter.

**URL Parameters:**
- `name` (path parameter): Author name to search for
- `limit` (query parameter, optional): Number of results (1-1000, default: 100)
- `offset` (query parameter, optional): Starting position (default: 0)
- `fields` (query parameter, optional): Comma-separated fields list
- `exact_match` (query parameter, optional): Filter results to exact name matches only (default: true)

**Example:**
```
GET /api/v1/authors/search/Oren%20Etzioni?limit=5&fields=name,affiliations
```

### 3. Basic Author Search (GET)

**Endpoint:** `GET /api/v1/authors/search/{name}/basic`

**Description:** Fast author search with minimal fields for quick lookups.

**URL Parameters:**
- `name` (path parameter): Author name to search for

**Response:**
```json
{
  "total": 15117,
  "offset": 0,
  "next": 10,
  "data": [
    {
      "authorId": "1741101",
      "name": "Oren Etzioni",
      "paperCount": 10,
      "citationCount": 50,
      "hIndex": 5,
      "externalIds": {
        "DBLP": [123]
      }
    }
  ]
}
```

### 4. Health Check (GET)

**Endpoint:** `GET /api/v1/authors/health`

**Description:** Check the health status of the author search service.

**Response:**
```json
{
  "status": "healthy",
  "service": "author-search",
  "semantic_scholar_api": "connected",
  "test_query": "successful"
}
```

## Available Fields

The following fields can be requested in the `fields` parameter:

### Author Fields:
- `name`: Author's full name (always included)
- `authorId`: Semantic Scholar's unique ID for the author (always included)
- `url`: Author's Semantic Scholar profile URL
- `affiliations`: Array of organizational affiliations for the author
- `homepage`: Author's personal homepage
- `paperCount`: Author's total publications count (as integer)
- `citationCount`: Author's total citations count (as integer)
- `hIndex`: Author's h-index (as integer)
- `externalIds`: Object containing ORCID/DBLP IDs for the author

### Paper Fields (when requesting `papers`):
- `paperId`: Semantic Scholar's primary unique identifier for a paper
- `corpusId`: Semantic Scholar's secondary unique identifier for a paper
- `externalIds`: Object containing paper's unique identifiers in external sources (ArXiv, MAG, ACL, PubMed, Medline, PubMedCentral, DBLP, DOI)
- `url`: URL of the paper on the Semantic Scholar website
- `title`: Title of the paper
- `abstract`: The paper's abstract
- `venue`: The name of the paper's publication venue
- `publicationVenue`: Object containing venue information (id, name, type, alternate_names, url)
- `year`: The year the paper was published
- `referenceCount`: Total number of papers this paper references
- `citationCount`: Total number of papers that reference this paper
- `influentialCitationCount`: Subset of citation count with significant impact
- `isOpenAccess`: Whether the paper is open access
- `openAccessPdf`: Object containing PDF URL, status, license, and disclaimer
- `fieldsOfStudy`: Array of high-level academic categories
- `s2FieldsOfStudy`: Array of field classifications with source information
- `publicationTypes`: Array of publication types
- `publicationDate`: Publication date in YYYY-MM-DD format
- `journal`: Object containing journal name, volume, and pages
- `citationStyles`: BibTex bibliographical citation
- `authors`: Array of author information for the paper

### Subfield Selection:
You can request specific subfields using dot notation:
- `papers.title`: Only paper titles
- `papers.year`: Only publication years
- `papers.authors`: Only author information for papers
- `papers.abstract`: Only paper abstracts

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request parameters
- `429`: Rate limit exceeded
- `500`: Internal server error
- `504`: Request timeout

**Error Response Format:**
```json
{
  "detail": "Error message description"
}
```

## Rate Limiting

The service respects Semantic Scholar's rate limits. If you encounter a 429 error, wait before making additional requests.

## Examples

### Example 1: Basic Search (Exact Match)
```bash
curl -X POST "http://localhost:8001/api/v1/authors/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Jun Wu", "limit": 5, "exact_match": true}'
```

### Example 2: Search with All Matches (No Filtering)
```bash
curl -X POST "http://localhost:8001/api/v1/authors/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Jun Wu", "limit": 5, "exact_match": false}'
```

### Example 3: Search with Specific Fields
```bash
curl -X GET "http://localhost:8001/api/v1/authors/search/Jun%20Wu?fields=name,affiliations,paperCount&limit=3&exact_match=true"
```

### Example 4: Search with Papers and Subfields
```bash
curl -X GET "http://localhost:8001/api/v1/authors/search/Jun%20Wu?fields=name,affiliations,papers.title,papers.year,papers.citationCount&limit=5&exact_match=true"
```

### Example 5: Search with All Paper Information
```bash
curl -X POST "http://localhost:8001/api/v1/authors/search" \
     -H "Content-Type: application/json" \
  -d '{"query": "Jun Wu", "limit": 3, "fields": "name,affiliations,papers", "exact_match": true}'
```

### Example 6: Basic Search (Always Exact Match)
```bash
curl -X GET "http://localhost:8001/api/v1/authors/search/Jun%20Wu/basic"
```

### Example 7: Health Check
```bash
curl -X GET "http://localhost:8001/api/v1/authors/health"
```

## Pagination

Use the `offset` and `limit` parameters for pagination:

1. First page: `offset=0, limit=100`
2. Second page: `offset=100, limit=100`
3. Continue using the `next` value from the response

## Complete Example Response

Here's a complete example showing all available fields:

```json
{
  "total": 15117,
  "offset": 0,
  "next": 100,
  "data": [
    {
      "authorId": "1741101",
      "name": "Oren Etzioni",
      "url": "https://www.semanticscholar.org/author/1741101",
      "affiliations": ["Allen Institute for AI"],
      "homepage": "https://allenai.org/",
      "paperCount": 10,
      "citationCount": 50,
      "hIndex": 5,
      "externalIds": {
        "DBLP": [123],
        "ORCID": ["0000-0001-1234-5678"]
      },
      "papers": [
        {
          "paperId": "5c5751d45e298cea054f32b392c12c61027d2fe7",
          "corpusId": 215416146,
          "externalIds": {
            "MAG": "3015453090",
            "DBLP": "conf/acl/LoWNKW20",
            "ACL": "2020.acl-main.447",
            "DOI": "10.18653/V1/2020.ACL-MAIN.447"
          },
          "url": "https://www.semanticscholar.org/paper/5c5751d45e298cea054f32b392c12c61027d2fe7",
          "title": "Construction of the Literature Graph in Semantic Scholar",
          "abstract": "We describe a deployed scalable system for organizing published scientific literature into a heterogeneous graph to facilitate algorithmic manipulation and discovery.",
          "venue": "Annual Meeting of the Association for Computational Linguistics",
          "publicationVenue": {
            "id": "1e33b3be-b2ab-46e9-96e8-d4eb4bad6e44",
            "name": "Annual Meeting of the Association for Computational Linguistics",
            "type": "conference",
            "alternate_names": ["ACL", "Annu Meet Assoc Comput Linguistics"],
            "url": "https://www.aclweb.org/anthology/venues/acl/"
          },
          "year": 2020,
          "referenceCount": 59,
          "citationCount": 453,
          "influentialCitationCount": 90,
          "isOpenAccess": true,
          "openAccessPdf": {
            "url": "https://www.aclweb.org/anthology/2020.acl-main.447.pdf",
            "status": "HYBRID",
            "license": "CCBY",
            "disclaimer": "Notice: This snippet is extracted from the open access paper..."
          },
          "fieldsOfStudy": ["Computer Science"],
          "s2FieldsOfStudy": [
            {
              "category": "Computer Science",
              "source": "external"
            }
          ],
          "publicationTypes": ["Journal Article", "Review"],
          "publicationDate": "2020-07-05",
          "journal": {
            "volume": "40",
            "pages": "116 - 135",
            "name": "IETE Technical Review"
          },
          "citationStyles": {
            "bibtex": "@inproceedings{Ammar2018ConstructionOT,\n  author = {Oren Etzioni},\n  title = {Construction of the Literature Graph in Semantic Scholar},\n  booktitle = {ACL},\n  year = {2020}\n}"
          },
          "authors": [
            {
              "authorId": "1741101",
              "name": "Oren Etzioni"
            }
          ]
        }
      ]
    }
  ]
}
```

## Notes

- The `total` field is approximate and may not be exact
- Hyphenated names should be replaced with spaces for better matching
- The service automatically validates and caps parameters (e.g., limit ≤ 1000)
- All responses are in JSON format
- The service includes proper logging for debugging and monitoring
- When requesting `papers`, the response may be larger and slower
- Use subfield selection (e.g., `papers.title`) to reduce response size
- **Exact Match Filtering**: By default, the API filters results to only include authors whose names exactly match the search query (case-insensitive). Set `exact_match=false` to get all matches including variations like "J. Wu" when searching for "Jun Wu"
