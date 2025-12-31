# FTex Decision Intelligence Platform

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/docker-ready-brightgreen.svg" alt="Docker">
  <img src="https://img.shields.io/badge/spark-3.5-orange.svg" alt="Spark">
</p>

A comprehensive **FTex Decision Intelligence Platform** designed for Tier 1 Banking organisations. Built with enterprise-grade technologies for real-time entity resolution, transaction monitoring, and graph-based analytics - demonstrating the technical capabilities used in financial crime detection.

## 🎯 FTex Core Technologies

This platform implements key Decision Intelligence technologies:

### 1. Entity Resolution Engine
FTex's signature capability for creating a single view of entities from disparate data sources:
- **Blocking Strategies** - Soundex, Metaphone, N-gram blocking for efficient candidate generation
- **Multi-Algorithm Matching** - Jaro-Winkler, Levenshtein, Jaccard, Token-based, Phonetic similarity
- **Graph-Based Clustering** - Union-Find connected components for entity grouping
- **Canonical Record Generation** - Survivorship rules to select best attribute values

### 2. Network Generation Engine
Dynamic knowledge graph creation from resolved entities:
- **Relationship Extraction** - From transactions, corporate registries, KYC data
- **Relationship Inference** - Automatic discovery of hidden connections (shared address, phone, devices)
- **Multi-hop Network Expansion** - Explore connections up to N degrees of separation
- **Network Schema Management** - Standardized relationship types (OWNS, CONTROLS, TRANSACTED_WITH, etc.)

### 3. Contextual Scoring Engine
The key FTex differentiator - risk scoring based on **network context**, not just individual attributes:
- **Sanctions & PEP Screening** - With fuzzy matching support
- **Jurisdiction Risk** - FATF high-risk country assessment
- **Transaction Pattern Analysis** - Structuring, velocity, round amounts detection
- **Network Risk Propagation** - Risk flows through connections
- **Behavioral Anomaly Detection** - Unusual activity patterns

### 4. Decision Intelligence
Combining all capabilities for comprehensive investigation:
- **360° Entity View** - Resolved entity + network + transactions + alerts
- **Explainable AI** - Full transparency into risk scoring factors
- **Investigation Workflows** - Case management with SAR filing

### 5. RFP/RFI Management
Complete proposal lifecycle management for presales activities:
- **Proposal Tracking** - Track RFPs, RFIs, RFQs from receipt to outcome
- **Content Library** - Reusable response content for faster proposal creation
- **Win/Loss Analytics** - Analyze proposal outcomes by solution area, client, industry
- **Team Collaboration** - Assign sections to team members with review workflow

### Features

- **Transaction Monitoring** - Real-time AML and fraud detection with configurable rules engine
- **Case Management** - End-to-end investigation workflow with SAR filing support
- **KYC/CDD** - Customer due diligence and sanctions screening integration
- **RFP/RFI Management** - Complete proposal management for solution engineering teams

### Technical Highlights

- 🚀 **High Performance** - Distributed processing with Apache Spark for handling millions of transactions
- 🔍 **Full-Text Search** - OpenSearch integration for fast entity and transaction lookup
- 🕸️ **Graph Database** - Neo4j for relationship mapping and network visualization
- 📊 **Real-time Streaming** - Kafka integration for live transaction monitoring
- 🔐 **Enterprise Security** - JWT authentication, role-based access control
- 🐳 **Cloud Native** - Fully containerized with Docker and Kubernetes-ready

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NGINX (Reverse Proxy)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────────┐                 ┌───────────────────┐
│     Frontend      │                 │     Backend       │
│   (Next.js/React) │                 │    (FastAPI)      │
└───────────────────┘                 └─────────┬─────────┘
                                                │
        ┌───────────────┬───────────────┬───────┴───────┐
        │               │               │               │
        ▼               ▼               ▼               ▼
┌───────────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────┐
│  PostgreSQL   │ │   Redis   │ │ OpenSearch│ │     Neo4j     │
│  (Primary DB) │ │  (Cache)  │ │  (Search) │ │   (Graph)     │
└───────────────┘ └───────────┘ └───────────┘ └───────────────┘

        ┌───────────────────────────────────────────────────┐
        │                  Apache Spark Cluster              │
        │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
        │  │ Master  │  │ Worker1 │  │ Worker2 │            │
        └──┴─────────┴──┴─────────┴──┴─────────┴────────────┘

        ┌───────────────────────────────────────────────────┐
        │              Kafka (Event Streaming)               │
        └───────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Next.js 14, React 18, TailwindCSS |
| Backend API | FastAPI, Python 3.11 |
| Primary Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Search Engine | OpenSearch 2.11 |
| Graph Database | Neo4j 5.15 |
| Data Processing | Apache Spark 3.5 |
| Message Queue | Apache Kafka |
| Reverse Proxy | Nginx |
| Containerization | Docker, Docker Compose |

## 🚀 Quick Start

### Prerequisites

- Docker Desktop 4.0+
- Docker Compose v2
- 16GB RAM minimum (recommended 32GB for full stack)
- 20GB free disk space

### Installation

1. **Clone the repository**
   ```bash
   cd /path/to/your/projects
   git clone <repository-url> quantex
   cd ftex
   ```

2. **Configure environment**
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

3. **Build and start services**
   ```bash
   # Using Make
   make build
   make up
   
   # Or using Docker Compose directly
   docker-compose build
   docker-compose up -d
   ```

4. **Verify installation**
   ```bash
   # Check service health
   make health
   
   # Or manually
   curl http://localhost:8000/health
   ```

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend Dashboard | http://localhost:3000 | - |
| Backend API | http://localhost:8000 | - |
| API Documentation | http://localhost:8000/docs | - |
| Spark Master UI | http://localhost:8080 | - |
| OpenSearch Dashboard | http://localhost:5601 | - |
| Neo4j Browser | http://localhost:7474 | neo4j / ftex_secret |

## 📁 Project Structure

```
ftex/
├── backend/                    # FastAPI backend service
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   └── endpoints/     # Entity, Transaction, Alert, Case APIs
│   │   ├── core/              # Configuration, security, database
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic services
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js app router pages
│   │   ├── components/        # React components
│   │   ├── lib/               # Utilities
│   │   └── hooks/             # Custom React hooks
│   ├── Dockerfile
│   └── package.json
│
├── spark/                      # Spark processing jobs
│   ├── jobs/
│   │   ├── entity_resolution.py
│   │   ├── transaction_monitoring.py
│   │   └── network_analysis.py
│   └── Dockerfile
│
├── nginx/                      # Reverse proxy configuration
│   └── nginx.conf
│
├── scripts/                    # Database and utility scripts
│   └── init-db.sql
│
├── docker-compose.yml          # Container orchestration
├── Makefile                    # Common operations
└── README.md
```

## 🔧 Configuration

### Environment Variables

Key configuration options (see `env.example` for full list):

```bash
# Database
DATABASE_URL=postgresql://ftex:password@postgres:5432/ftex_db

# Search
OPENSEARCH_URL=http://opensearch:9200

# Graph
NEO4J_URI=bolt://neo4j:7687
NEO4J_PASSWORD=your_password

# Security
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📊 API Reference

### Entities API

```bash
# List entities with filtering
GET /api/entities?entity_type=individual&risk_score_min=0.5

# Get entity details
GET /api/entities/{entity_id}

# Entity relationships (graph)
GET /api/entities/{entity_id}/relationships?depth=2

# Entity resolution
POST /api/entities/resolve
```

### Transactions API

```bash
# List transactions
GET /api/transactions?is_flagged=true&min_amount=10000

# Transaction statistics
GET /api/transactions/stats?days=30

# Flag transaction
POST /api/transactions/{id}/flag
```

### Alerts API

```bash
# List alerts
GET /api/alerts?status=new&severity=critical

# Alert dashboard
GET /api/alerts/dashboard

# Assign/Resolve alerts
POST /api/alerts/{id}/assign
POST /api/alerts/{id}/resolve
```

### Graph Analytics API

```bash
# Entity network visualization
GET /api/graph/entity/{id}/network?depth=2

# Shortest path between entities
GET /api/graph/shortest-path?source_id=...&target_id=...

# Community detection
GET /api/graph/community-detection

# Centrality analysis
GET /api/graph/centrality?algorithm=pagerank
```

### Search API

```bash
# Global search
GET /api/search/global?q=query

# Sanctions screening
POST /api/search/screening
```

### RFP/RFI Management API

```bash
# List proposals with filtering
GET /api/rfp?status=in_progress&proposal_type=rfp

# Get proposal dashboard stats
GET /api/rfp/dashboard

# Get proposal details
GET /api/rfp/{proposal_id}

# Create new proposal
POST /api/rfp
{
  "proposal_type": "rfp",
  "client_name": "DBS Bank",
  "title": "AML Solution RFP",
  "solution_areas": ["AML", "Transaction Monitoring"]
}

# Submit proposal
POST /api/rfp/{proposal_id}/submit

# Record outcome
POST /api/rfp/{proposal_id}/outcome?outcome=won&reason=Best%20technical%20fit

# Manage proposal sections
GET /api/rfp/{proposal_id}/sections
POST /api/rfp/{proposal_id}/sections
PUT /api/rfp/{proposal_id}/sections/{section_id}

# Content library
GET /api/rfp/library/content?category=technical&solution_area=AML
POST /api/rfp/library/content

# Win/loss analytics
GET /api/rfp/analytics/win-loss?months=12
```

## 🔄 Spark Jobs

### Entity Resolution

```bash
make spark-submit JOB=entity_resolution.py \
  --input /data/entities \
  --output /data/resolved \
  --threshold 0.8
```

### Transaction Monitoring

```bash
make spark-submit JOB=transaction_monitoring.py \
  --input /data/transactions \
  --output /data/alerts \
  --rules structuring velocity round_amounts
```

### Network Analysis

```bash
make spark-submit JOB=network_analysis.py \
  --transactions /data/transactions \
  --entities /data/entities \
  --output /data/network_analysis
```

## 🧪 Development

### Local Development Setup

```bash
# Start infrastructure services only
make dev

# Run backend locally
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Run frontend locally
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
make test

# Or directly
docker-compose exec backend pytest -v
```

## 📈 Monitoring

### Health Checks

```bash
# All services health
make health

# Individual service logs
make logs-backend
make logs-frontend
make logs-spark-master
```

### Scaling

```bash
# Scale Spark workers
make scale-spark N=4

# Manual scaling
docker-compose up -d --scale spark-worker-1=4
```

## 🔐 Security

- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Rate limiting on API endpoints
- SQL injection protection via parameterized queries
- XSS protection headers
- CORS configuration

## 📋 Compliance

Designed to support compliance with:

- **MAS (Monetary Authority of Singapore)** - Technology Risk Management Guidelines
- **FATF Recommendations** - AML/CFT standards
- **GDPR** - Data protection (configurable data retention)
- **PCI DSS** - Payment card data security

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with technologies from the Apache Foundation, Neo4j, OpenSearch, and the Python/JavaScript communities
- Inspired by best practices from leading financial institutions in the APAC region

---

<p align="center">
  <strong>FTex Decision Intelligence Platform</strong><br>
  <em>Enabling smarter, faster, and more confident decision-making through connected, trusted data.</em>
</p>

