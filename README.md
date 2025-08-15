# ScholarAI Paper Search Service

A comprehensive academic paper search service that mirrors the Backend-AI implementation with robust PDF processing, B2 storage integration, and RabbitMQ message handling.

## 🚀 Features

- **Multi-Source Academic Search**: Search across arXiv, PubMed, OpenAlex, and more
- **AI-Powered Query Refinement**: Intelligent query expansion and refinement
- **PDF Collection & Storage**: Aggressive PDF collection with B2 cloud storage
- **Paper Deduplication**: Intelligent deduplication across sources
- **Metadata Enrichment**: Complete paper metadata with enrichment
- **RabbitMQ Integration**: Asynchronous message processing
- **REST API**: Direct HTTP API for testing and integration

## 📋 Complete Workflow

### 1. RabbitMQ Message Processing
```
Message Received → Parse & Validate → Route to Handler → Process Request
```

### 2. Multi-Source Search Orchestration
```
Query Terms → AI Refinement → Parallel Source Search → Deduplication → Enrichment
```

### 3. PDF Processing Pipeline
```
Paper Metadata → PDF Collection → B2 Upload → URL Generation → Response
```

### 4. Paper Entity Structure
Each paper follows the exact structure from Backend-AI with all fields populated.

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   RabbitMQ      │    │   WebSearch      │    │   PDF Processor │
│   Consumer      │───▶│   Agent          │───▶│   Service       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Search         │    │   B2 Storage    │
                       │   Orchestrator   │    │   Service       │
                       └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Academic       │
                       │   API Clients    │
                       └──────────────────┘
```

## 📦 Installation

1. **Clone the repository**
   ```bash
   cd AI-Agents/paper-search
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

## ⚙️ Configuration

### Required Environment Variables

```bash
# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
RABBITMQ_WEBSEARCH_QUEUE=websearch_queue
RABBITMQ_EXCHANGE_NAME=scholarai_exchange

# B2 Storage Configuration
B2_APPLICATION_KEY_ID=your_b2_key_id
B2_APPLICATION_KEY=your_b2_application_key
B2_BUCKET_NAME=scholarai-papers
B2_BUCKET_ID=your_bucket_id

# AI Configuration (Optional)
OPENAI_API_KEY=your_openai_key
AI_MODEL_NAME=gpt-3.5-turbo

# Search Configuration
PAPERS_PER_SOURCE=20
MAX_SEARCH_ROUNDS=3
ENABLE_AI_REFINEMENT=true
RECENT_YEARS_FILTER=5
```

## 🚀 Running the Service

### Option 1: Full Service (Recommended)
```bash
python -m app.main
```

This starts:
- FastAPI server on port 8000
- RabbitMQ consumer in background
- PDF processor with B2 integration

### Option 2: RabbitMQ Consumer Only
```bash
python -m app.services.rabbitmq_consumer
```

### Option 3: Direct API Testing
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Health Check
```bash
GET /health
```

### Direct Search API
```bash
POST /api/v1/search
Content-Type: application/json

{
  "projectId": "test-project",
  "queryTerms": ["machine learning", "neural networks"],
  "domain": "Computer Science",
  "batchSize": 10,
  "correlationId": "corr-123"
}
```

### Service Statistics
```bash
GET /api/v1/stats
```

## 🔄 RabbitMQ Message Format

### Request Message
```json
{
  "projectId": "string",
  "queryTerms": ["string"],
  "domain": "string",
  "batchSize": "integer",
  "correlationId": "string"
}
```

### Response Message
```json
{
  "projectId": "string",
  "correlationId": "string",
  "papers": [
    {
      "title": "string",
      "abstract": "string",
      "authors": [...],
      "publicationDate": "string",
      "doi": "string",
      "source": "string",
      "pdfContentUrl": "string",
      "pdfUrl": "string",
      "isOpenAccess": "boolean",
      "paperUrl": "string",
      "venueName": "string",
      "publisher": "string",
      "publicationTypes": ["string"],
      "volume": "string",
      "issue": "string",
      "pages": "string",
      "citationCount": "integer",
      "referenceCount": "integer",
      "influentialCitationCount": "integer",
      "fieldsOfStudy": ["string"],
      "externalIds": {...}
    }
  ],
  "batchSize": "integer",
  "queryTerms": ["string"],
  "domain": "string",
  "status": "COMPLETED",
  "searchStrategy": "multi_source_modular",
  "totalSourcesUsed": "integer",
  "aiEnhanced": "boolean",
  "searchRounds": "integer",
  "deduplicationStats": {...}
}
```

## 📄 Paper Entity Structure

The service produces papers with the exact structure from Backend-AI:

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Paper title |
| `abstract` | string \| null | Paper abstract |
| `authors` | Array<Object> | List of authors with details |
| `publicationDate` | string | Publication date (YYYY-MM-DD) |
| `doi` | string \| null | Digital Object Identifier |
| `source` | string | Academic API source |
| `pdfContentUrl` | string | Permanent B2 storage URL |
| `pdfUrl` | string \| null | Original PDF URL |
| `isOpenAccess` | boolean | Open access flag |
| `paperUrl` | string \| null | Publisher landing page |
| `venueName` | string \| null | Journal/conference name |
| `publisher` | string \| null | Publisher name |
| `publicationTypes` | Array<string> | Publication types |
| `volume` | string \| null | Journal volume |
| `issue` | string \| null | Journal issue |
| `pages` | string \| null | Page numbers |
| `citationCount` | integer \| null | Total citations |
| `referenceCount` | integer \| null | Total references |
| `influentialCitationCount` | integer \| null | Influential citations |
| `fieldsOfStudy` | Array<string> | Research fields |

## 🔧 PDF Processing Strategy

1. **Direct PDF URLs**: Use PDF URLs from academic APIs
2. **DOI Resolution**: Resolve PDFs via Crossref API
3. **ArXiv Extraction**: Direct ArXiv PDF download
4. **Unpaywall Integration**: Open access PDF discovery
5. **Publisher Scraping**: Website PDF link extraction
6. **B2 Storage**: Upload to Backblaze B2 for permanent access

## 🧪 Testing

### Unit Tests
```bash
pytest tests/
```

### Integration Tests
```bash
pytest tests/integration/
```

### Manual Testing
```bash
# Test direct API
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "test",
    "queryTerms": ["machine learning"],
    "domain": "Computer Science",
    "batchSize": 5
  }'

# Test health check
curl "http://localhost:8000/health"
```

## 📊 Monitoring

### Health Check
- Service status
- RabbitMQ connection
- WebSearch agent status
- PDF processor status

### Statistics
- Search performance metrics
- Source usage statistics
- Deduplication statistics
- AI refinement usage

## 🐛 Troubleshooting

### Common Issues

1. **RabbitMQ Connection Failed**
   - Check RabbitMQ service is running
   - Verify connection credentials
   - Check network connectivity

2. **B2 Storage Issues**
   - Verify B2 credentials
   - Check bucket permissions
   - Ensure bucket exists

3. **PDF Processing Failures**
   - Check internet connectivity
   - Verify academic API access
   - Review B2 storage configuration

### Logs
```bash
# View service logs
tail -f logs/paper-search.log

# Debug mode
LOG_LEVEL=DEBUG python -m app.main
```

## 🔄 Development

### Adding New Academic Sources
1. Create client in `app/services/academic_apis/clients/`
2. Add to `MultiSourceSearchOrchestrator`
3. Update configuration

### Extending PDF Collection
1. Add new strategies to `PDFCollectorService`
2. Update collection logic
3. Test with various paper types

### Customizing Paper Structure
1. Modify enrichment service
2. Update paper entity structure
3. Ensure backward compatibility

## 📚 Documentation

- [Paper Entity Structure](docs/paper_entity_structure.md)
- [API Documentation](http://localhost:8000/docs)
- [Configuration Guide](docs/configuration.md)

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure backward compatibility

## 📄 License

This project is part of the ScholarAI system and follows the same licensing terms.
