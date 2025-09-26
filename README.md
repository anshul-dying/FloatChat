# FloatChat - AI-Powered ARGO Ocean Data Assistant

[![SIH 2025](https://img.shields.io/badge/SIH-2025-blue)](https://www.sih.gov.in/)
[![Problem Statement](https://img.shields.io/badge/Problem%20Statement-25040-green)](https://www.sih.gov.in/)
[![Ministry of Earth Sciences](https://img.shields.io/badge/MoES-INCOIS-orange)](https://www.incois.gov.in/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://python.org/)
[![React](https://img.shields.io/badge/React-18+-61dafb)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688)](https://fastapi.tiangolo.com/)

## Project Overview

**FloatChat** is an innovative AI-powered conversational system designed for SIH 2025 Problem Statement 25040, enabling users to query, explore, and visualize ARGO float oceanographic data using natural language. The system bridges the gap between complex oceanographic datasets and intuitive user interactions through advanced AI technologies.

### Problem Statement 25040
**Organization**: Ministry of Earth Sciences (MoES) - INCOIS  
**Challenge**: Develop an AI-powered system for natural language querying of ARGO float oceanographic data with interactive visualizations and data export capabilities.

## Key Features

### AI-Powered Query Processing
- **Natural Language Interface**: Ask questions in plain English
- **RAG (Retrieval-Augmented Generation)**: Advanced AI for context-aware responses
- **MCP (Model Context Protocol)**: Structured tool-based interactions
- **Multi-LLM Support**: OpenAI, Anthropic, OpenRouter, and local models

### ARGO Data Integration
- **Real-time Data Access**: Direct integration with ARGO data centers
- **NetCDF Processing**: Automated conversion to structured formats
- **Metadata Extraction**: Intelligent processing of oceanographic parameters
- **Geographic Coverage**: Global ARGO float network support

### Interactive Visualizations
- **Interactive Maps**: Real-time ARGO float locations with Leaflet
- **Depth Profiles**: Oceanographic parameter visualization with Plotly
- **Time Series**: Temporal data analysis and comparison
- **Export Capabilities**: CSV, Parquet, and NetCDF format support

### Technical Architecture
- **Microservices Design**: Scalable, containerized architecture
- **Vector Database**: ChromaDB for semantic search
- **Relational Database**: PostgreSQL for structured data
- **Modern Frontend**: React + Vite with responsive design

## System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[React Frontend] --> B[Vite Dev Server]
        A --> C[Interactive Maps]
        A --> D[Data Visualizations]
    end
    
    subgraph "API Layer"
        E[FastAPI Backend] --> F[Chat Routes]
        E --> G[Data Routes]
        E --> H[Auth Routes]
    end
    
    subgraph "AI Processing Layer"
        I[RAG Pipeline] --> J[LangChain]
        I --> K[Vector Search]
        I --> L[LLM Integration]
        M[MCP Server] --> N[Tool Registry]
        M --> O[Context Management]
    end
    
    subgraph "Data Layer"
        P[PostgreSQL] --> Q[Structured Data]
        R[ChromaDB] --> S[Vector Embeddings]
        T[File Storage] --> U[Parquet/NetCDF]
    end
    
    subgraph "External Services"
        V[Argopy API] --> W[ARGO Data]
        X[OpenRouter] --> Y[LLM Services]
    end
    
    A --> E
    E --> I
    E --> M
    I --> P
    I --> R
    M --> P
    E --> V
    I --> X
```

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+

### Installation

1. **Clone the Repository**
```bash
git clone https://github.com/your-org/floatchat.git
cd floatchat
```

2. **Backend Setup**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp config/config.yaml.example config/config.yaml
# Edit config.yaml with your API keys
```

3. **Database Setup**
```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Run database migrations
python scripts/setup_db.bat
```

4. **Data Ingestion**
```bash
# Download and process ARGO data
python scripts/download_argo_data.bat
python scripts/load_argo_csv.bat
```

5. **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

6. **Start the Application**
```bash
# Start backend API
python scripts/start_api.bat

# Start frontend (in another terminal)
cd frontend
npm run dev
```

### Docker Deployment
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Project Structure

```
floatchat/
├── src/                             # Source code
│   ├── api/                         # FastAPI backend
│   │   ├── main.py                  # API entry point
│   │   └── routes/                  # API routes
│   ├── data_ingestion/              # Data processing
│   │   ├── ingest_argo.py           # ARGO data ingestion
│   │   └── nc_to_parquet.py         # NetCDF conversion
│   ├── database/                    # Database layer
│   │   ├── relational_db.py         # PostgreSQL operations
│   │   └── vector_db.py             # ChromaDB operations
│   ├── llm/                         # AI/ML components
│   │   ├── rag_pipeline.py          # RAG implementation
│   │   └── models.py                # LLM integration
│   └── utils/                       # Utilities
├── frontend/                        # React frontend
│   ├── src/
│   │   ├── components/              # React components
│   │   ├── hooks/                   # Custom hooks
│   │   └── utils/                   # Frontend utilities
│   └── package.json
├── data/                            # Data storage
│   ├── raw/                         # Raw NetCDF files
│   └── processed/                   # Processed data
├── docs/                            # Documentation
├── scripts/                         # Automation scripts
├── tests/                           # Test suite
├── docker-compose.yml               # Docker configuration
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_URL=postgresql://floatchat:floatchat123@localhost:5432/floatchat

# LLM Configuration
LLM_TYPE=openrouter  # Options: mock, openai, anthropic, openrouter
OPENROUTER_API_KEY=your_api_key_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ChromaDB Configuration
CHROMADB_PATH=./chroma_db
```

### LLM Provider Setup

#### OpenRouter (Recommended)
```yaml
# config/config.yaml
llm:
  type: openrouter
  api_key: "your_openrouter_api_key"
  model: "deepseek/deepseek-chat-v3.1:free"
  base_url: "https://openrouter.ai/api/v1"
```

#### OpenAI
```yaml
llm:
  type: openai
  api_key: "your_openai_api_key"
  model: "gpt-3.5-turbo"
```

#### Anthropic
```yaml
llm:
  type: anthropic
  api_key: "your_anthropic_api_key"
  model: "claude-3-haiku-20240307"
```

## Data Sources

### ARGO Float Data
- **Source**: Global ARGO network via Argopy
- **Coverage**: Global oceans with 4000+ active floats
- **Parameters**: Temperature, Salinity, Pressure, BGC parameters
- **Update Frequency**: Real-time data from ARGO data centers

### Data Processing Pipeline
1. **Raw Data**: NetCDF files from ARGO data centers
2. **Ingestion**: Argopy library for data access
3. **Processing**: Pandas/Xarray for data manipulation
4. **Storage**: PostgreSQL for structured data, ChromaDB for embeddings
5. **Querying**: Natural language to SQL translation

## Usage Examples

### Natural Language Queries
```
"Show me salinity profiles near the equator in March 2023"
"Compare temperature data between Arabian Sea and Bay of Bengal"
"What are the nearest ARGO floats to coordinates 20°N, 70°E?"
"Export all BGC data from the last 6 months"
```

### API Endpoints

#### Chat Interface
```bash
POST /api/chat
Content-Type: application/json

{
  "text": "Show me salinity profiles near the equator"
}
```

#### Data Access
```bash
GET /api/data?query=SELECT * FROM argo_floats LIMIT 10
GET /api/visualization?type=map&region=indian_ocean
```

## Testing

### Run Test Suite
```bash
# Backend tests
python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
python tests/test_api.py
```

### Test Coverage
```bash
# Generate coverage report
python -m pytest --cov=src tests/
```

## Performance Metrics

### System Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 8GB+ for full dataset
- **Storage**: 50GB+ for ARGO data
- **Network**: Stable internet for LLM API calls

### Performance Benchmarks
- **Query Response**: < 3 seconds average
- **Data Ingestion**: ~1000 profiles/minute
- **Concurrent Users**: 100+ supported
- **Uptime**: 99.5% target

## Security Features

### Authentication & Authorization
- API key-based authentication
- Role-based access control
- Rate limiting and request validation
- Secure data transmission (TLS 1.3)

### Data Privacy
- Encrypted data storage
- Audit logging for all operations
- GDPR compliance for user data
- Secure API key management

## Deployment

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Monitor services
docker-compose logs -f
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n floatchat
```

## CI/CD Pipeline

### GitHub Actions
- Automated testing on pull requests
- Docker image building and pushing
- Security scanning with Snyk
- Deployment to staging/production

### Quality Gates
- Code coverage > 80%
- Security scan passes
- Performance tests pass
- Documentation updated

## Documentation

### Technical Documentation
- [High-Level Design (HLD)](docs/HLD.md)
- [Low-Level Design (LLD)](docs/LLD.md)
- [System Architecture](docs/architecture.md)
- [API Documentation](docs/api_docs.md)

### User Guides
- [User Guide](docs/user_guide.md)
- [Developer Guide](docs/developer_guide.md)
- [Deployment Guide](docs/deployment_guide.md)

## Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Code Standards
- Follow PEP 8 for Python code
- Use ESLint for JavaScript/React
- Write comprehensive tests
- Update documentation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

### SIH 2025 Sponsors
- **Ministry of Earth Sciences (MoES)**
- **Indian National Centre for Ocean Information Services (INCOIS)**
- **Smart India Hackathon 2025**

### Open Source Libraries
- [Argopy](https://github.com/euroargodev/argopy) - ARGO data access
- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [ChromaDB](https://github.com/chroma-core/chroma) - Vector database
- [FastAPI](https://github.com/tiangolo/fastapi) - Web framework
- [React](https://github.com/facebook/react) - Frontend framework

### Data Sources
- **ARGO Program** - Global ocean observation network
- **INCOIS** - Indian Ocean data and services
- **OpenStreetMap** - Map tiles and geospatial data

---
