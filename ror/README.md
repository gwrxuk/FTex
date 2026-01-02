# FTex Worker - Ruby on Rails + Sidekiq

Background job processing service for FTex Decision Intelligence Platform.

## Overview

This service provides asynchronous job processing for FTex's core capabilities:

- **Entity Resolution** - Batch processing of entity matching and deduplication
- **Network Analysis** - Graph-based relationship analysis
- **Risk Scoring** - Contextual risk calculation with explainability
- **Screening** - Batch sanctions/watchlist screening
- **Alert Management** - Alert creation and notification handling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FTex Platform                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐ │
│  │   Frontend  │───▶│   Backend   │───▶│   RoR Worker    │ │
│  │  (Next.js)  │    │  (FastAPI)  │    │   (Sidekiq)     │ │
│  └─────────────┘    └─────────────┘    └────────┬────────┘ │
│                            │                     │          │
│                            ▼                     ▼          │
│                     ┌─────────────┐       ┌───────────┐    │
│                     │   Redis     │◀──────│ Scheduled │    │
│                     │   Queue     │       │   Jobs    │    │
│                     └─────────────┘       └───────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Workers

| Worker | Queue | Description |
|--------|-------|-------------|
| `EntityResolutionWorker` | entity_resolution | Resolves entities across data sources |
| `EntityResolutionSyncWorker` | entity_resolution | Scheduled sync for new entities |
| `NetworkAnalysisWorker` | network_analysis | Analyzes entity networks |
| `NetworkGenerationWorker` | network_analysis | Generates knowledge graphs |
| `RiskScoringWorker` | scoring | Calculates contextual risk scores |
| `BatchScoringWorker` | scoring | Batch risk scoring operations |
| `AlertWorker` | critical | Creates and manages alerts |
| `WatchlistSyncWorker` | critical | Syncs sanctions/PEP watchlists |
| `BatchScreeningWorker` | batch | Batch entity screening |
| `TransactionAnalysisWorker` | batch | Transaction pattern analysis |
| `EnhancedDueDiligenceWorker` | default | EDD workflow processing |
| `CleanupWorker` | low | Cleanup old processing data |

## Scheduled Jobs

Configured in `config/sidekiq.yml`:

| Job | Schedule | Description |
|-----|----------|-------------|
| Entity Resolution Sync | Hourly | Sync new entities across sources |
| Network Analysis Refresh | Every 4 hours | Refresh network metrics |
| Risk Score Recalculation | Hourly at :30 | Recalculate outdated scores |
| Watchlist Sync | Daily at 2 AM | Sync sanctions/PEP lists |
| Cleanup | Weekly (Sunday 3 AM) | Clean old processing data |

## API Endpoints

The service exposes an API for triggering jobs:

```
POST /api/v1/jobs/entity-resolution
POST /api/v1/jobs/entity-resolution/batch
POST /api/v1/jobs/network-analysis
POST /api/v1/jobs/network-generation
POST /api/v1/jobs/risk-scoring
POST /api/v1/jobs/risk-scoring/batch
POST /api/v1/jobs/screening
POST /api/v1/jobs/watchlist-sync
GET  /api/v1/jobs/:job_id/status
GET  /health
```

## Running with Docker

### Start all services

```bash
docker-compose up -d ftex-sidekiq ftex-worker-api
```

### View Sidekiq Web UI

Access at: `http://localhost:3001/sidekiq`

### Check health

```bash
curl http://localhost:3001/health
```

## Development

### Prerequisites

- Ruby 3.3.0
- PostgreSQL 15+
- Redis 7+

### Setup

```bash
# Install dependencies
bundle install

# Setup database
rails db:create db:migrate

# Start Sidekiq
bundle exec sidekiq -C config/sidekiq.yml

# Start API server (separate terminal)
bundle exec puma -C config/puma.rb
```

### Running Tests

```bash
bundle exec rspec
```

## Environment Variables

See `env.example` for all configuration options.

Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | redis://redis:6379/1 |
| `FTEX_API_URL` | Backend API URL | http://backend:8000 |
| `DATABASE_HOST` | PostgreSQL host | postgres |
| `NEO4J_URI` | Neo4j connection | bolt://neo4j:7687 |

## Queue Priority

Queues are processed in priority order:

1. `critical` (6) - Urgent security/compliance events
2. `entity_resolution` (5) - Entity resolution jobs
3. `network_analysis` (4) - Network/graph generation
4. `scoring` (4) - Risk scoring calculations
5. `batch` (3) - Batch processing jobs
6. `default` (2) - Standard priority
7. `low` (1) - Background maintenance

## Monitoring

- **Sidekiq Web UI**: Real-time queue and job monitoring
- **Health Endpoint**: `/health` for container health checks
- **Prometheus Metrics**: Available via prometheus-client gem
- **Sentry Integration**: Error tracking and alerting

## License

Proprietary - FTex Decision Intelligence Platform

