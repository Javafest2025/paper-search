# Paper Entity Structure for RabbitMQ Response

This document outlines the structure of the `Paper` entity JSON object that is sent as a response via RabbitMQ from the websearch service.

## Overview

The final `Paper` entity is a JSON object meticulously constructed by aggregating data from multiple academic APIs, standardizing the information, enriching it with missing metadata, and processing associated PDF documents. This process ensures a comprehensive and well-formed data structure for each paper.

### Data Flow

1.  **Initial Fetch & Parse**: The process begins with clients like `SemanticScholarClient`, which fetch data from academic APIs. This raw data is then parsed by `JSONParser` into a standardized base paper object.
2.  **Source Tagging**: The `MultiSourceSearchOrchestrator` tags each paper object with a `source` field, indicating its origin (e.g., "Semantic Scholar", "arXiv").
3.  **Metadata Enrichment**: The `PaperMetadataEnrichmentService` ensures essential fields (`doi`, `abstract`, `authors`, `publicationDate`) are present, fetching any missing information from alternative sources like Crossref.
4.  **PDF Processing**: Finally, the `PDFProcessorService` finds, downloads, and uploads the paper's PDF to B2 cloud storage. It then adds a permanent `pdfContentUrl` to the paper object. A paper is discarded if a PDF cannot be successfully processed and stored.

## Paper JSON Structure

Here is the detailed breakdown of the `Paper` entity's fields:

```json
{
  "title": "string",
  "abstract": "string | null",
  "authors": [
    {
      "name": "string",
      "authorId": "string | null",
      "orcid": "string | null",
      "affiliation": "string | null"
    }
  ],
  "publicationDate": "string",
  "doi": "string | null",
  "semanticScholarId": "string | null",
  "externalIds": {
    "DOI": "string",
    "ArXiv": "string",
    "PubMedCentral": "string",
    "CorpusId": "integer"
  },
  "source": "string",
  "pdfContentUrl": "string",
  "pdfUrl": "string | null",
  "isOpenAccess": "boolean",
  "paperUrl": "string | null",
  "venueName": "string | null",
  "publisher": "string | null",
  "publicationTypes": ["string"],
  "volume": "string | null",
  "issue": "string | null",
  "pages": "string | null",
  "citationCount": "integer | null",
  "referenceCount": "integer | null",
  "influentialCitationCount": "integer | null",
  "fieldsOfStudy": ["string"]
}
```

### Field Descriptions

| Field                        | Type             | Description                                                                                             | Service Responsible                               |
| ---------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `title`                      | `string`         | Paper title.                                                                                            | `*Client` -> `JSONParser`                         |
| `abstract`                   | `string`\|`null` | Paper abstract.                                                                                         | `*Client` -> `JSONParser`, `EnrichmentService`    |
| `authors`                    | `Array<Object>`  | List of authors with their details.                                                                     | `*Client` -> `JSONParser`, `EnrichmentService`    |
| `authors.name`               | `string`         | Full name of the author.                                                                                | `*Client` -> `JSONParser`                         |
| `authors.authorId`           | `string`\|`null` | Semantic Scholar author ID.                                                                             | `*Client` -> `JSONParser`                         |
| `authors.orcid`              | `string`\|`null` | Author's ORCID ID.                                                                                      | `*Client` -> `JSONParser`                         |
| `authors.affiliation`        | `string`\|`null` | Author's affiliation.                                                                                   | `*Client` -> `JSONParser`                         |
| `publicationDate`            | `string`         | Publication date (YYYY-MM-DD format).                                                                   | `*Client` -> `JSONParser`, `EnrichmentService`    |
| `doi`                        | `string`\|`null` | Digital Object Identifier.                                                                              | `*Client` -> `JSONParser`, `EnrichmentService`    |
| `semanticScholarId`          | `string`\|`null` | Unique ID from Semantic Scholar.                                                                        | `SemanticScholarClient` -> `JSONParser`           |
| `externalIds`                | `Object`         | A dictionary of IDs from various sources (e.g., ArXiv, PubMedCentral).                                  | `*Client` -> `JSONParser`                         |
| `source`                     | `string`         | The primary academic API source (e.g., "Semantic Scholar", "arXiv").                                    | `SearchOrchestrator`                              |
| `pdfContentUrl`              | `string`         | The permanent URL to the PDF stored in B2 storage. A paper is discarded if this cannot be generated.    | `PDFProcessorService`                             |
| `pdfUrl`                     | `string`\|`null` | The original open access PDF URL found from the source API.                                             | `*Client` -> `JSONParser`                         |
| `isOpenAccess`               | `boolean`        | Flag indicating if the paper is open access.                                                            | `*Client` -> `JSONParser`                         |
| `paperUrl`                   | `string`\|`null` | URL to the paper's landing page on the publisher's site.                                                | `*Client` -> `JSONParser`                         |
| `venueName`                  | `string`\|`null` | Name of the journal or conference venue.                                                                | `*Client` -> `JSONParser`                         |
| `publisher`                  | `string`\|`null` | The publisher of the paper.                                                                             | `*Client` -> `JSONParser`                         |
| `publicationTypes`           | `Array<string>`  | Type of publication (e.g., "JournalArticle", "Conference").                                             | `*Client` -> `JSONParser`                         |
| `volume`                     | `string`\|`null` | Journal volume.                                                                                         | `*Client` -> `JSONParser`                         |
| `issue`                      | `string`\|`null` | Journal issue.                                                                                          | `*Client` -> `JSONParser`                         |
| `pages`                      | `string`\|`null` | Page numbers.                                                                                           | `*Client` -> `JSONParser`                         |
| `citationCount`              | `integer`\|`null`| Total number of citations.                                                                              | `*Client` -> `JSONParser`                         |
| `referenceCount`             | `integer`\|`null`| Total number of references.                                                                             | `*Client` -> `JSONParser`                         |
| `influentialCitationCount`   | `integer`\|`null`| Number of influential citations.                                                                        | `*Client` -> `JSONParser`                         |
| `fieldsOfStudy`              | `Array<string>`  | List of research fields associated with the paper.                                                      | `*Client` -> `JSONParser`                         |

## Example Paper Object

```json
{
  "title": "Attention Is All You Need",
  "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder...",
  "authors": [
    {
      "name": "Ashish Vaswani",
      "authorId": "123456",
      "orcid": "0000-0001-2345-6789",
      "affiliation": "Google Research"
    },
    {
      "name": "Noam Shazeer",
      "authorId": "789012",
      "orcid": null,
      "affiliation": "Google Research"
    }
  ],
  "publicationDate": "2017-06-12",
  "doi": "10.48550/arXiv.1706.03762",
  "semanticScholarId": "649def34f8be52c8b66281af98ae884c09aef38b",
  "externalIds": {
    "DOI": "10.48550/arXiv.1706.03762",
    "ArXiv": "1706.03762",
    "PubMedCentral": null,
    "CorpusId": 215351783
  },
  "source": "arXiv",
  "pdfContentUrl": "https://f004.backblazeb2.com/file/scholarai-papers/papers/10.48550_arXiv.1706.03762.pdf",
  "pdfUrl": "https://arxiv.org/pdf/1706.03762.pdf",
  "isOpenAccess": true,
  "paperUrl": "https://arxiv.org/abs/1706.03762",
  "venueName": "Advances in Neural Information Processing Systems",
  "publisher": "Neural Information Processing Systems Foundation",
  "publicationTypes": ["Conference"],
  "volume": "30",
  "issue": null,
  "pages": "5998-6008",
  "citationCount": 45678,
  "referenceCount": 62,
  "influentialCitationCount": 1234,
  "fieldsOfStudy": ["Computer Science", "Machine Learning", "Natural Language Processing"]
}
```

## Implementation Notes

### PDF Processing Strategy

The `pdfContentUrl` field is critical and follows this process:

1. **PDF Collection**: The `PDFCollectorService` attempts to collect PDFs using multiple strategies:
   - Direct PDF URLs from academic APIs
   - DOI-based PDF resolution via Crossref
   - ArXiv PDF extraction
   - Unpaywall integration
   - Publisher website scraping

2. **B2 Storage**: Collected PDFs are uploaded to Backblaze B2 cloud storage for permanent access.

3. **URL Generation**: A permanent, public URL is generated for each stored PDF.

4. **Fallback Handling**: If PDF processing fails, the paper is still returned but without `pdfContentUrl`.

### Data Enrichment Process

The `PaperMetadataEnrichmentService` ensures data completeness by:

1. **Missing DOI Resolution**: Using Crossref API to find DOIs for papers that don't have them.
2. **Abstract Enhancement**: Fetching abstracts from alternative sources when missing.
3. **Author Information**: Enriching author details with ORCID and affiliation data.
4. **Publication Date Standardization**: Converting various date formats to YYYY-MM-DD.

### Source Attribution

Each paper is tagged with its primary source in the `source` field, which helps with:
- Data provenance tracking
- Source-specific filtering
- Quality assessment
- Debugging and monitoring

### Error Handling

The system is designed to be resilient:
- Papers without PDFs are still returned (not discarded)
- Missing optional fields are set to `null`
- API failures don't stop the entire process
- Graceful degradation when services are unavailable
