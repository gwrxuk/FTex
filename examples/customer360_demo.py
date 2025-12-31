#!/usr/bin/env python3
"""
Customer 360 / MDM Demo

Demonstrates Master Data Management and unified customer view:
- Data aggregation from multiple sources
- Survivorship rules for golden record
- Data quality assessment
- Complete customer profile
"""

import sys
sys.path.insert(0, '../backend')

from datetime import datetime, timedelta
from typing import Dict, List

# Import the Customer 360 service
try:
    from app.services.customer360 import Customer360Service, Customer360View
    HAS_SERVICE = True
except ImportError:
    HAS_SERVICE = False
    print("Note: Running in demo mode. Install backend dependencies for full functionality.")


def create_sample_source_records() -> List[Dict]:
    """Create sample records from different source systems."""
    
    return [
        # CRM System
        {
            "record_id": "CRM-001",
            "source_system": "crm",
            "updated_at": datetime.now() - timedelta(days=5),
            "name": "John Michael Smith",
            "email": "john.smith@email.com",
            "phones": [
                {"number": "+65 9123 4567", "type": "mobile", "primary": True}
            ],
            "addresses": [
                {
                    "line1": "123 Orchard Road",
                    "line2": "#10-01",
                    "city": "Singapore",
                    "postal_code": "238858",
                    "country": "SG",
                    "type": "residential"
                }
            ],
            "emails": [
                {"address": "john.smith@email.com", "type": "personal", "primary": True}
            ],
            "accounts": [
                {
                    "account_id": "ACC-001",
                    "account_type": "savings",
                    "balance": 50000,
                    "currency": "SGD",
                    "status": "active"
                }
            ],
            "risk_score": 0.25
        },
        
        # KYC System
        {
            "record_id": "KYC-001",
            "source_system": "kyc_system",
            "updated_at": datetime.now() - timedelta(days=30),
            "name": "SMITH, John Michael",
            "date_of_birth": "1985-03-15",
            "nationality": "US",
            "national_id": "S1234567A",
            "occupation": "Software Engineer",
            "employer": "Tech Corp Pte Ltd",
            "annual_income": 150000,
            "kyc_status": {
                "status": "verified",
                "verification_date": "2024-01-15",
                "risk_rating": "low",
                "next_review": "2025-01-15"
            },
            "is_sanctioned": False,
            "is_pep": False,
            "documents": [
                {
                    "type": "passport",
                    "number": "E12345678",
                    "issuing_country": "US",
                    "expiry_date": "2028-05-20"
                },
                {
                    "type": "work_permit",
                    "number": "WP-2024-001",
                    "issuing_country": "SG",
                    "expiry_date": "2026-12-31"
                }
            ],
            "risk_score": 0.20
        },
        
        # Core Banking System
        {
            "record_id": "CORE-001",
            "source_system": "core_banking",
            "updated_at": datetime.now() - timedelta(days=1),
            "name": "John M. Smith",
            "phones": [
                {"number": "+65 9123 4567", "type": "mobile"},
                {"number": "+65 6789 0123", "type": "work"}
            ],
            "accounts": [
                {
                    "account_id": "ACC-001",
                    "account_type": "savings",
                    "balance": 52340.50,  # More recent balance
                    "currency": "SGD",
                    "status": "active",
                    "opened_date": "2020-06-15"
                },
                {
                    "account_id": "ACC-002",
                    "account_type": "checking",
                    "balance": 15000,
                    "currency": "SGD",
                    "status": "active",
                    "opened_date": "2020-06-15"
                },
                {
                    "account_id": "ACC-003",
                    "account_type": "credit_card",
                    "balance": -2500,
                    "credit_limit": 20000,
                    "currency": "SGD",
                    "status": "active"
                }
            ],
            "products": [
                {"product_id": "SAV-PLUS", "name": "Savings Plus", "type": "deposit"},
                {"product_id": "CC-PLATINUM", "name": "Platinum Credit Card", "type": "credit"}
            ],
            "risk_score": 0.22
        },
        
        # Trade System
        {
            "record_id": "TRADE-001",
            "source_system": "trade_system",
            "updated_at": datetime.now() - timedelta(days=60),
            "name": "J. Smith",
            "accounts": [
                {
                    "account_id": "TRADE-001",
                    "account_type": "brokerage",
                    "balance": 125000,
                    "currency": "USD",
                    "status": "active"
                }
            ],
            "products": [
                {"product_id": "BROKER-STD", "name": "Standard Brokerage", "type": "investment"}
            ],
            "relationships": [
                {
                    "type": "authorized_trader",
                    "related_entity": "Smith Family Trust",
                    "since": "2022-01-01"
                }
            ]
        }
    ]


def demo_customer_360():
    """Demonstrate Customer 360 view creation."""
    
    print("=" * 60)
    print("Customer 360 / MDM Demo")
    print("=" * 60)
    print("""
    Creating a unified customer view from multiple source systems:
    - CRM (Customer contacts, preferences)
    - KYC (Identity, verification, risk)
    - Core Banking (Accounts, balances)
    - Trade System (Investments)
    """)
    
    source_records = create_sample_source_records()
    
    print("\n--- Source Records ---")
    for record in source_records:
        print(f"  [{record['source_system']:12s}] {record['name']}")
    
    print("\n" + "-" * 40)
    
    if HAS_SERVICE:
        service = Customer360Service()
        
        # Build Customer 360 view
        customer_360 = service.build_customer_360(
            customer_id="C-12345",
            source_records=source_records
        )
        
        display_customer_360(service, customer_360)
    else:
        demo_mode_customer_360(source_records)


def display_customer_360(service: 'Customer360Service', customer_360: 'Customer360View'):
    """Display the Customer 360 view."""
    
    print("\n" + "=" * 60)
    print("CUSTOMER 360 VIEW")
    print("=" * 60)
    
    # Golden Record
    print("\n📋 GOLDEN RECORD (Canonical Data)")
    print("-" * 40)
    for key, value in customer_360.golden_record.items():
        print(f"  {key}: {value}")
    
    # Identity
    print("\n🆔 IDENTITY DOCUMENTS")
    print("-" * 40)
    for doc in customer_360.documents:
        print(f"  • {doc.get('type', 'Unknown')}: {doc.get('number', 'N/A')}")
        print(f"    Expires: {doc.get('expiry_date', 'N/A')}")
    
    # Contact Information
    print("\n📞 CONTACT INFORMATION")
    print("-" * 40)
    print("  Phones:")
    for phone in customer_360.phones:
        primary = "★" if phone.get('primary') else " "
        print(f"    {primary} {phone.get('number')} ({phone.get('type', 'unknown')})")
    print("  Emails:")
    for email in customer_360.emails:
        primary = "★" if email.get('primary') else " "
        print(f"    {primary} {email.get('address')}")
    print("  Addresses:")
    for addr in customer_360.addresses:
        print(f"    • {addr.get('line1')}, {addr.get('city')} {addr.get('postal_code')}")
    
    # Financial Summary
    print("\n💰 FINANCIAL SUMMARY")
    print("-" * 40)
    summary = customer_360.financial_summary
    print(f"  Total Accounts: {summary.get('total_accounts', 0)}")
    print(f"  Total Balance: ${summary.get('total_balance', 0):,.2f}")
    print(f"  Account Types: {', '.join(summary.get('account_types', []))}")
    
    print("\n  Accounts:")
    for account in customer_360.accounts:
        status_icon = "✅" if account.get('status') == 'active' else "⏸️"
        print(f"    {status_icon} {account.get('account_id')}: {account.get('account_type')}")
        print(f"       Balance: {account.get('currency', 'SGD')} {account.get('balance', 0):,.2f}")
    
    print("\n  Products:")
    for product in customer_360.products:
        print(f"    • {product.get('name')} ({product.get('type')})")
    
    # Risk Profile
    print("\n⚠️  RISK PROFILE")
    print("-" * 40)
    risk = customer_360.risk_profile
    level_icons = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}
    icon = level_icons.get(risk.get('risk_level', 'unknown'), '⚪')
    print(f"  Risk Level: {icon} {risk.get('risk_level', 'unknown').upper()}")
    print(f"  Current Score: {risk.get('current_risk_score', 0):.3f}")
    if risk.get('risk_factors'):
        print(f"  Risk Factors: {', '.join(risk.get('risk_factors', []))}")
    
    # Compliance Status
    print("\n✓ COMPLIANCE STATUS")
    print("-" * 40)
    kyc = customer_360.kyc_status
    sanctions = customer_360.sanctions_status
    pep = customer_360.pep_status
    
    kyc_icon = "✅" if kyc.get('status') == 'verified' else "⚠️"
    print(f"  KYC Status: {kyc_icon} {kyc.get('status', 'unknown')}")
    
    sanctions_icon = "🔴" if sanctions.get('is_sanctioned') else "✅"
    print(f"  Sanctions: {sanctions_icon} {'MATCH' if sanctions.get('is_sanctioned') else 'Clear'}")
    
    pep_icon = "⚠️" if pep.get('is_pep') else "✅"
    print(f"  PEP Status: {pep_icon} {'PEP' if pep.get('is_pep') else 'Not PEP'}")
    
    # Data Quality
    print("\n📊 DATA QUALITY")
    print("-" * 40)
    if customer_360.data_quality:
        dq = customer_360.data_quality
        print(f"  Overall Score: {dq.overall_score:.1%}")
        
        quality_bar = lambda score: "█" * int(score * 10) + "░" * (10 - int(score * 10))
        print(f"  Completeness: [{quality_bar(dq.completeness)}] {dq.completeness:.1%}")
        print(f"  Accuracy:     [{quality_bar(dq.accuracy)}] {dq.accuracy:.1%}")
        print(f"  Consistency:  [{quality_bar(dq.consistency)}] {dq.consistency:.1%}")
        print(f"  Timeliness:   [{quality_bar(dq.timeliness)}] {dq.timeliness:.1%}")
        
        if dq.issues:
            print(f"\n  ⚠️  Data Issues: {len(dq.issues)}")
            for issue in dq.issues[:3]:
                print(f"      • {issue.get('issue')}")
    
    # Source Systems
    print("\n🔗 SOURCE SYSTEMS")
    print("-" * 40)
    for source in customer_360.source_systems:
        print(f"  ✓ {source}")
    
    print(f"\n  Last Updated: {customer_360.last_updated}")


def demo_mode_customer_360(records: List[Dict]):
    """Demo mode output for Customer 360."""
    
    print("\n[Demo Mode - Simulated Customer 360]")
    print("\n" + "=" * 60)
    print("CUSTOMER 360 VIEW")
    print("=" * 60)
    
    print("""
    📋 GOLDEN RECORD
    -----------------------------------------
    name: John Michael Smith
    date_of_birth: 1985-03-15
    nationality: US
    occupation: Software Engineer
    employer: Tech Corp Pte Ltd
    
    💰 FINANCIAL SUMMARY
    -----------------------------------------
    Total Accounts: 4
    Total Balance: $192,340.50
    Account Types: savings, checking, credit_card, brokerage
    
    ⚠️  RISK PROFILE
    -----------------------------------------
    Risk Level: 🟢 LOW
    Current Score: 0.250
    
    ✓ COMPLIANCE STATUS
    -----------------------------------------
    KYC Status: ✅ verified
    Sanctions: ✅ Clear
    PEP Status: ✅ Not PEP
    
    📊 DATA QUALITY
    -----------------------------------------
    Overall Score: 87.5%
    Completeness: [████████░░] 80%
    Accuracy:     [█████████░] 90%
    Consistency:  [████████░░] 85%
    Timeliness:   [█████████░] 95%
    
    🔗 SOURCE SYSTEMS
    -----------------------------------------
    ✓ crm
    ✓ kyc_system
    ✓ core_banking
    ✓ trade_system
    """)


def demo_data_quality():
    """Demonstrate data quality assessment."""
    
    print("\n\n" + "=" * 60)
    print("Data Quality Assessment Demo")
    print("=" * 60)
    print("""
    FTex MDM assesses data quality across dimensions:
    
    ✓ COMPLETENESS - Required fields populated
    ✓ ACCURACY - Data matches reference sources
    ✓ CONSISTENCY - Agreement across systems
    ✓ TIMELINESS - Data freshness
    ✓ UNIQUENESS - No duplicate records
    ✓ VALIDITY - Conforms to business rules
    """)
    
    # Show sample quality issues
    print("\nSample Data Quality Issues:")
    print("-" * 40)
    
    issues = [
        {"dimension": "completeness", "field": "phone", "issue": "Missing mobile phone number"},
        {"dimension": "consistency", "field": "name", "issue": "Name format differs across systems"},
        {"dimension": "timeliness", "field": "address", "issue": "Address not updated in 2+ years"},
        {"dimension": "accuracy", "field": "email", "issue": "Email format invalid"},
    ]
    
    for issue in issues:
        print(f"  ⚠️  [{issue['dimension'].upper()}] {issue['issue']}")
        print(f"      Field: {issue['field']}")


if __name__ == "__main__":
    demo_customer_360()
    demo_data_quality()

