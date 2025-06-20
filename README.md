# Company Research Agent

A comprehensive research automation tool that collects, enriches, and formats company information from multiple high-quality APIs including CoreSignal Multi-Source API, Apollo Organization API, and Tavily Search, generating structured reports with optional Google Drive integration.

## Features

- **Multi-source API research**: CoreSignal Multi-Source, Apollo Organization, Tavily Search
- **CoreSignal integration**: Comprehensive company data, employee information, funding details, and market intelligence
- **Apollo API integration**: Organization enrichment and contact details
- **Tavily search capabilities**: Recent news, major customers, and competitor analysis
- **LLM-powered report generation**: Structured markdown reports using GPT-4
- **PDF export**: Professional PDF reports with Pandoc
- **Google Drive integration**: Automatic upload to Google Drive with sharing links
- **Email notifications**: Send reports via email with Drive links
- **Web interface**: User-friendly frontend for easy report generation
- **Background processing**: Non-blocking report generation with email delivery
- **RESTful API**: Full API access with `/api` prefix structure
- **Automatic company name extraction**: No need to manually enter company names
- **Multiple output formats**: Markdown, JSON, PDF
- **Intelligent data caching**: Cached API responses for efficiency

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- Google Cloud Project (for Drive integration)

## 🚀 Quick Start

### 1. Clone and Install Dependencies

```bash
git clone <repo-url>
cd company_research_agent
uv sync
```

### 2. Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
CORESIGNAL_API_KEY=your_coresignal_api_key
APOLLO_API_KEY=your_apollo_api_key
TAVILY_API_KEY=your_tavily_api_key
# Optional: CORESIGNAL_BASE_URL=https://api.coresignal.com
# Optional: APOLLO_BASE_URL=https://api.apollo.io/api/v1
```

### 3. Start Development Server

```bash
uv run uvicorn api.company_research_fastapi:app --reload --host 0.0.0.0 --port 8000
```

Your API will be available at:
- **API Base URL**: http://localhost:8000
- **Web Interface**: http://localhost:8000 (Frontend for generating reports)
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### 4. Test Your Setup

```bash
curl http://localhost:8000/api/health
```

## 🔧 Local Development Guide

### Available Development Commands

#### Start with auto-reload (recommended for development):
```bash
uv run uvicorn api.company_research_fastapi:app --reload
```

#### Start in production mode:
```bash
uv run uvicorn api.company_research_fastapi:app --host 0.0.0.0 --port 8000
```

#### Run with custom port:
```bash
uv run uvicorn api.company_research_fastapi:app --port 3000
```

#### Check dependencies:
```bash
uv pip list
```

#### Add new dependency:
```bash
uv add package_name
```

### 🔑 API Endpoints

#### Core Endpoints:
- `GET /` - Web interface for generating reports
- `GET /api/health` - Health check with API status
- `GET /docs` - Interactive API documentation (Swagger UI)

#### Research Endpoints:
- `POST /api/multi-source-research` - Apollo + Tavily research (returns PDF or uploads to Drive)
- `POST /api/multi-source-research-background` - Apollo + Tavily research (background processing, email notification)
- `POST /api/coresignal/generate-pdf` - CoreSignal PDF report generation
- `POST /api/coresignal/generate-pdf-background` - CoreSignal PDF report (background processing, email notification)
- `GET /api/drive-files` - List files in Google Drive folder

### 🧪 Testing the API

#### 1. Open Interactive Documentation
Visit: http://localhost:8000/docs

#### 2. Test Multi-Source Research
```bash
curl -X POST "http://localhost:8000/api/multi-source-research" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "openai.com",
    "return_data": true,
    "upload_to_drive": false
  }'
```

#### 3. Test CoreSignal PDF Generation
```bash
curl -X POST "http://localhost:8000/api/coresignal/generate-pdf" \
  -H "Content-Type: application/json" \
  -d '{
    "website": "https://example.com",
    "upload_to_drive": false
  }'
```

### 🐛 Troubleshooting

#### Common Issues:

1. **Port already in use**:
   ```bash
   # Find and kill process using port 8000
   lsof -ti:8000 | xargs kill -9
   ```

2. **Import errors**:
   ```bash
   # Ensure dependencies are synced
   uv sync
   ```

3. **API key issues**:
   ```bash
   # Check health endpoint
   curl http://localhost:8000/api/health
   ```

4. **Missing pandoc** (for PDF generation):
   ```bash
   # macOS
   brew install pandoc
   
   # Ubuntu/Debian
   sudo apt-get install pandoc
   ```

## Google Drive Setup (Optional)

For PDF upload to Google Drive functionality:

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "company-research-drive")
3. Enable Google Drive API in "APIs & Services"

### 2. Create Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill details:
   - Name: `company-research-uploader`
   - Description: `Service account for uploading company research PDFs`

### 3. Generate Service Account Key
1. Click on the created service account
2. Go to "Keys" tab → "Add Key" → "Create new key"
3. Choose "JSON" format
4. **Save as `service_account.json` in the project root**

## Usage

### Web Interface

The easiest way to generate reports is through the web interface:

1. Visit http://localhost:8000 in your browser
2. Enter the company website (e.g., "example.com" or "https://example.com")
3. Enter your email address to receive the report
4. Click "Generate Report" to start the research process

The system will:
- Automatically extract the company name from the website
- Research the company using multiple data sources
- Generate a comprehensive PDF report
- Upload the report to Google Drive (if configured)
- Send you an email with the report attached and Drive link

### Command Line Interface

Run the main research tool:

```bash
uv run main.py
```

You'll be prompted for:
- Company domain (for Apollo API, e.g., example.com)

The system will automatically extract the company name from the API data.
Results are saved to `results/{company_name}_multi_source_research_report.md`

### API Interface Examples

#### Generate PDF Report

**Without Google Drive**:
```bash
curl -X POST "http://localhost:8000/api/coresignal/generate-pdf" \
     -H "Content-Type: application/json" \
     -d '{"website": "example.com", "upload_to_drive": false}' \
     --output report.pdf
```

**With Google Drive Upload**:
```bash
curl -X POST "http://localhost:8000/api/coresignal/generate-pdf" \
     -H "Content-Type: application/json" \
     -d '{"website": "example.com", "upload_to_drive": true}'
```

**Background Processing with Email**:
```bash
curl -X POST "http://localhost:8000/api/multi-source-research-background" \
     -H "Content-Type: application/json" \
     -d '{"website": "example.com", "email": "your-email@example.com"}'
```

Response includes Google Drive file ID and shareable link:
```json
{
    "message": "PDF generated and uploaded to Google Drive successfully",
    "pdf_filename": "Example_Company_report_20241216_143022.pdf",
    "google_drive": {
        "file_id": "1ABCDEFGHijklmnopQRSTUVWXYZ",
        "view_link": "https://drive.google.com/file/d/1ABCDEFGHijklmnopQRSTUVWXYZ/view",
        "size": "245760"
    }
}
```

#### List Google Drive Files

```bash
curl -X GET "http://localhost:8000/api/drive-files" \
     -H "Content-Type: application/json"
```

## 🚀 Production Deployment

For production deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md) which covers:
- Railway (Recommended)
- Render
- Fly.io  
- Docker deployment
- Environment variable setup
- Troubleshooting

## Project Structure

```
company_research_agent/
├── api/                          # FastAPI application
│   ├── company_research_fastapi.py  # Main API server
│   └── drive_uploader_complete.py   # Google Drive integration
├── researchers/                  # Research modules
│   ├── multi_source_researcher.py   # Apollo + Tavily researcher
│   └── browser_use_research/        # Browser automation research
├── third_party_api/             # API integrations
│   ├── apollo_organization_api.py   # Apollo API client
│   └── coresignal_multisource_api.py # CoreSignal API client
├── search_engines/              # Search functionality
│   ├── tavily_search.py             # Tavily search integration
│   └── langgraph_tavily.py          # LangGraph Tavily integration
├── results/                     # Generated reports
├── pyproject.toml              # UV dependencies
├── requirements.txt            # Docker dependencies  
├── Dockerfile                  # Container build
├── docker-compose.yml          # Container orchestration
└── DEPLOYMENT.md              # Production deployment guide
```

## Data Sources

### Primary APIs

1. **CoreSignal Multi-Source API**: 
   - Comprehensive company profiles and employee data
   - Funding information and investment history
   - Company updates and news
   - Geographic employee distribution
   - Executive profiles and leadership changes
   - Competitor intelligence

2. **Apollo Organization API**: 
   - Company information and contact details
   - Employee data and organizational structure
   - Industry classification
   - Revenue and size information

3. **Tavily Search API**: 
   - Recent news and press coverage
   - Major customers and partnerships
   - Competitive intelligence
   - Market insights

### Data Quality & Coverage

- **Employee Information**: Current count, geographic distribution, department breakdown
- **Financial Data**: Funding rounds, revenue ranges, investment history
- **Leadership**: Executive profiles, recent changes, contact information
- **Market Position**: Competitors, customers, industry classification
- **Company Updates**: Recent news, announcements, social media activity

## Output Formats

- **Markdown**: Human-readable structured reports with sections for:
  - Company overview and industry classification
  - Contact details and leadership profiles
  - Employee count and geographic distribution
  - Funding and financial information
  - Recent news and market updates
  - Enterprise customers and partnerships
  - Competitive landscape analysis

- **JSON**: Machine-readable data format with structured fields
- **PDF**: Professional reports with formatting for sharing and presentations

## Dependencies

Key dependencies managed via `pyproject.toml`:
- `langchain-openai`: LLM integration for report generation
- `fastapi`: Web API framework
- `tavily-python`: Search API client
- `weasyprint`: PDF generation
- `google-api-python-client`: Google Drive integration
- `requests`: HTTP client for API calls
- `python-dotenv`: Environment variable management

## Security Notes

- Never commit `service_account.json` to version control
- Keep all API keys secure in `.env` file
- Regularly rotate service account keys
- Monitor API usage in respective consoles
- CoreSignal and Apollo APIs may have rate limits and usage quotas

## API Rate Limits & Best Practices

- **CoreSignal**: Implements intelligent caching to avoid redundant API calls
- **Apollo**: Respects rate limits with proper error handling
- **Tavily**: Optimized search queries to minimize API usage
- **OpenAI**: Efficient prompt engineering to reduce token consumption

---

For issues or contributions, please open a GitHub issue or pull request.
