# FTex Platform Examples

This folder contains example scripts demonstrating the key features of the FTex Decision Intelligence Platform.

## Prerequisites

```bash
# Install Python dependencies
pip install requests httpx pandas

# Ensure the platform is running
docker-compose up -d
```

## Example Scripts

### Core Decision Intelligence

| Script | Description |
|--------|-------------|
| `entity_resolution_demo.py` | Demonstrates entity resolution with fuzzy matching |
| `network_generation_demo.py` | Shows network/graph generation from entities |
| `contextual_scoring_demo.py` | Risk scoring with network context |
| `decision_intelligence_demo.py` | Full investigation workflow |

### Fraud Detection

| Script | Description |
|--------|-------------|
| `credit_card_fraud_demo.py` | Credit card fraud detection patterns |
| `blockchain_fraud_demo.py` | Crypto/blockchain transaction monitoring |
| `lending_fraud_demo.py` | Loan application fraud detection |

### Compliance & Screening

| Script | Description |
|--------|-------------|
| `screening_demo.py` | Sanctions & PEP screening with Dow Jones/Refinitiv |
| `customer360_demo.py` | Master Data Management / Customer 360 view |
| `transaction_monitoring_demo.py` | AML transaction monitoring rules |

### Sales Engineering Tools

| Script | Description |
|--------|-------------|
| `rfp_management_demo.py` | RFP/RFI lifecycle management |
| `poc_demo_management.py` | PoC and product demo tracking |

### API Integration

| Script | Description |
|--------|-------------|
| `api_client_example.py` | Basic API client usage |
| `batch_processing_example.py` | Batch entity/transaction processing |
| `webhook_integration.py` | Webhook setup for real-time alerts |

## Running Examples

```bash
# Run individual example
python examples/entity_resolution_demo.py

# Run with API base URL override
API_URL=http://localhost:8000 python examples/api_client_example.py
```

## Sample Data

The `data/` subfolder contains sample datasets for testing:
- `sample_entities.json` - Entity records for resolution
- `sample_transactions.json` - Transaction data
- `sample_names.txt` - Names for screening tests

