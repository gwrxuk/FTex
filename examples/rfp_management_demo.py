#!/usr/bin/env python3
"""
RFP/RFI Management Demo

Demonstrates proposal lifecycle management:
- Creating and tracking RFPs/RFIs
- Managing proposal sections
- Content library usage
- Win/loss analytics
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List

API_BASE_URL = "http://localhost:8000/api"


def demo_create_proposal():
    """Demonstrate creating a new RFP."""
    
    print("=" * 60)
    print("RFP/RFI Management Demo")
    print("=" * 60)
    print("""
    Managing the proposal lifecycle:
    - RFP (Request for Proposal)
    - RFI (Request for Information)
    - RFQ (Request for Quotation)
    """)
    
    # Create a new RFP
    print("\n--- Creating New RFP ---")
    
    rfp_data = {
        "proposal_type": "rfp",
        "client_name": "DBS Bank",
        "client_industry": "Banking",
        "client_country": "Singapore",
        "title": "Enterprise AML Transaction Monitoring Platform",
        "description": "End-to-end AML solution with entity resolution, transaction monitoring, and case management capabilities for retail and corporate banking.",
        "solution_areas": ["AML", "Transaction Monitoring", "Entity Resolution", "Case Management"],
        "use_cases": [
            "Real-time transaction screening",
            "Customer risk scoring",
            "Suspicious activity detection",
            "SAR generation"
        ],
        "priority": "high",
        "due_date": (datetime.now() + timedelta(days=45)).isoformat(),
        "estimated_deal_value": 2500000,
        "currency": "USD",
        "lead_owner": "solution_engineer_1",
        "team_members": ["architect_1", "product_specialist_1"]
    }
    
    print(f"\nProposal: {rfp_data['title']}")
    print(f"Client: {rfp_data['client_name']}")
    print(f"Value: ${rfp_data['estimated_deal_value']:,}")
    print(f"Due: {rfp_data['due_date'][:10]}")
    
    try:
        response = requests.post(f"{API_BASE_URL}/rfp/", json=rfp_data)
        response.raise_for_status()
        proposal = response.json()
        
        print(f"\n✅ Proposal created: {proposal.get('proposal_number')}")
        return proposal
        
    except requests.exceptions.ConnectionError:
        print("\n[Demo Mode - API not available]")
        return {"id": "DEMO-001", "proposal_number": "RFP-202501-0001"}
    except Exception as e:
        print(f"\nError: {e}")
        return None


def demo_add_sections(proposal_id: str):
    """Demonstrate adding proposal sections."""
    
    print("\n\n--- Adding Proposal Sections ---")
    
    sections = [
        {
            "section_number": "1.0",
            "title": "Company Overview",
            "question": "Please provide an overview of your company, including history, size, and financial stability.",
            "category": "company",
            "is_mandatory": True,
            "assigned_to": "solution_engineer_1"
        },
        {
            "section_number": "2.0",
            "title": "Technical Architecture",
            "question": "Describe the technical architecture of your proposed solution, including deployment options.",
            "category": "technical",
            "is_mandatory": True,
            "max_score": 20,
            "weight": 2.0,
            "assigned_to": "architect_1"
        },
        {
            "section_number": "3.0",
            "title": "Entity Resolution Capabilities",
            "question": "Describe your entity resolution approach including matching algorithms and accuracy metrics.",
            "category": "technical",
            "is_mandatory": True,
            "max_score": 25,
            "weight": 2.5,
            "assigned_to": "product_specialist_1"
        },
        {
            "section_number": "4.0",
            "title": "Implementation Methodology",
            "question": "Describe your implementation approach, timeline, and resource requirements.",
            "category": "project",
            "is_mandatory": True,
            "max_score": 15,
            "assigned_to": "solution_engineer_1"
        },
        {
            "section_number": "5.0",
            "title": "Security and Compliance",
            "question": "Describe security controls, certifications, and regulatory compliance capabilities.",
            "category": "compliance",
            "is_mandatory": True,
            "max_score": 20,
            "weight": 2.0,
            "assigned_to": "architect_1"
        }
    ]
    
    print(f"Adding {len(sections)} sections to proposal...")
    
    for section in sections:
        print(f"  • [{section['section_number']}] {section['title']}")
        print(f"    Category: {section['category']}, Assigned: {section['assigned_to']}")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/rfp/{proposal_id}/sections",
                json=section
            )
            response.raise_for_status()
        except:
            pass  # Continue demo even if API unavailable


def demo_content_library():
    """Demonstrate content library usage."""
    
    print("\n\n--- Content Library ---")
    print("Reusable content for faster proposal creation:")
    
    content_items = [
        {
            "title": "Entity Resolution Overview",
            "category": "technical",
            "solution_area": "Entity Resolution",
            "usage_count": 15,
            "snippet": "Our entity resolution engine uses advanced fuzzy matching..."
        },
        {
            "title": "Network Analytics Description",
            "category": "technical", 
            "solution_area": "Network Analytics",
            "usage_count": 12,
            "snippet": "The network analytics module provides graph-based analysis..."
        },
        {
            "title": "AML Compliance Statement",
            "category": "compliance",
            "solution_area": "AML",
            "usage_count": 23,
            "snippet": "Our solution fully supports compliance with MAS Notice 626..."
        },
        {
            "title": "Implementation Methodology",
            "category": "project",
            "solution_area": "Implementation",
            "usage_count": 18,
            "snippet": "We follow an agile implementation methodology..."
        },
        {
            "title": "Security and Data Protection",
            "category": "security",
            "solution_area": "Security",
            "usage_count": 28,
            "snippet": "The platform implements enterprise-grade security..."
        }
    ]
    
    try:
        response = requests.get(f"{API_BASE_URL}/rfp/library/content")
        response.raise_for_status()
        content_items = response.json().get('items', content_items)
    except:
        pass
    
    print("\nTop Content Items by Usage:")
    for item in sorted(content_items, key=lambda x: x.get('usage_count', 0), reverse=True)[:5]:
        print(f"  📄 {item['title']}")
        print(f"     Category: {item['category']} | Used: {item.get('usage_count', 0)} times")
        if 'snippet' in item:
            print(f"     Preview: {item['snippet'][:60]}...")


def demo_dashboard():
    """Demonstrate RFP dashboard."""
    
    print("\n\n--- RFP Dashboard ---")
    
    try:
        response = requests.get(f"{API_BASE_URL}/rfp/dashboard")
        response.raise_for_status()
        dashboard = response.json()
    except:
        # Demo data
        dashboard = {
            "active_proposals": 5,
            "due_this_week": 2,
            "win_rate": 62.5,
            "total_won_value": 8500000,
            "by_status": {
                "draft": 1,
                "in_progress": 2,
                "review": 2,
                "submitted": 1,
                "won": 5,
                "lost": 3
            },
            "by_type": {
                "rfp": 10,
                "rfi": 4,
                "rfq": 2
            }
        }
    
    print("\n┌─────────────────────────────────────────┐")
    print("│           RFP PIPELINE DASHBOARD        │")
    print("├─────────────────────────────────────────┤")
    print(f"│  Active Proposals:     {dashboard['active_proposals']:>3}              │")
    print(f"│  Due This Week:        {dashboard['due_this_week']:>3}              │")
    print(f"│  Win Rate:           {dashboard['win_rate']:>5.1f}%            │")
    print(f"│  Total Won Value:  ${dashboard['total_won_value']/1000000:>4.1f}M            │")
    print("└─────────────────────────────────────────┘")
    
    print("\nBy Status:")
    status_bar = lambda count, total: "█" * (count * 20 // max(total, 1))
    total = sum(dashboard['by_status'].values())
    for status, count in dashboard['by_status'].items():
        if count > 0:
            bar = status_bar(count, total)
            print(f"  {status:12s} [{bar:20s}] {count}")
    
    print("\nBy Type:")
    for ptype, count in dashboard['by_type'].items():
        print(f"  {ptype.upper():4s}: {count}")


def demo_proposal_workflow():
    """Demonstrate full proposal workflow."""
    
    print("\n\n--- Proposal Workflow Demo ---")
    print("""
    Typical proposal lifecycle:
    
    1. 📥 RECEIVED
       └─> RFP received from client
       
    2. 📝 DRAFT
       └─> Initial proposal setup
       └─> Team assignment
       └─> Section breakdown
       
    3. ✏️  IN PROGRESS
       └─> Team working on responses
       └─> Content library usage
       └─> Internal collaboration
       
    4. 🔍 REVIEW
       └─> Technical review
       └─> Commercial review
       └─> Final polish
       
    5. 📤 SUBMITTED
       └─> Proposal sent to client
       └─> Presentation scheduled
       
    6. 🏆 OUTCOME
       └─> WON: Celebrate! Record win factors
       └─> LOST: Learn. Record loss reasons
    """)
    
    # Show sample timeline
    print("\nSample Proposal Timeline:")
    print("-" * 40)
    
    timeline = [
        ("Jan 15", "RFP received from DBS Bank"),
        ("Jan 16", "Team kickoff meeting"),
        ("Jan 17", "Solution architecture drafted"),
        ("Jan 20", "Technical sections completed"),
        ("Jan 25", "Internal review #1"),
        ("Jan 28", "Pricing approved"),
        ("Feb 01", "Final review complete"),
        ("Feb 03", "Proposal submitted"),
        ("Feb 15", "Client presentation"),
        ("Feb 28", "Won! Contract negotiation begins"),
    ]
    
    for date, event in timeline:
        print(f"  {date:8s} │ {event}")


def demo_win_loss_analytics():
    """Demonstrate win/loss analytics."""
    
    print("\n\n--- Win/Loss Analytics ---")
    
    try:
        response = requests.get(f"{API_BASE_URL}/rfp/analytics/win-loss")
        response.raise_for_status()
        analytics = response.json()
    except:
        analytics = {
            "period_months": 12,
            "total_proposals": 16,
            "won": 10,
            "lost": 6,
            "total_won_value": 12500000,
            "by_solution_area": {
                "AML": {"won": 5, "lost": 2},
                "Fraud": {"won": 3, "lost": 2},
                "KYC": {"won": 2, "lost": 2}
            },
            "by_client_industry": {
                "Banking": {"won": 8, "lost": 4},
                "Insurance": {"won": 2, "lost": 2}
            }
        }
    
    print(f"\nLast {analytics['period_months']} Months Summary:")
    print("-" * 40)
    print(f"Total Proposals: {analytics['total_proposals']}")
    print(f"Won: {analytics['won']} | Lost: {analytics['lost']}")
    
    win_rate = analytics['won'] / analytics['total_proposals'] * 100 if analytics['total_proposals'] > 0 else 0
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Total Won Value: ${analytics['total_won_value']:,}")
    
    print("\nBy Solution Area:")
    for area, stats in analytics['by_solution_area'].items():
        total = stats['won'] + stats['lost']
        rate = stats['won'] / total * 100 if total > 0 else 0
        bar = "🟢" * stats['won'] + "🔴" * stats['lost']
        print(f"  {area:15s} {bar} ({rate:.0f}%)")
    
    print("\nBy Industry:")
    for industry, stats in analytics['by_client_industry'].items():
        total = stats['won'] + stats['lost']
        rate = stats['won'] / total * 100 if total > 0 else 0
        print(f"  {industry:15s} Won: {stats['won']}, Lost: {stats['lost']} ({rate:.0f}%)")


if __name__ == "__main__":
    proposal = demo_create_proposal()
    if proposal:
        demo_add_sections(proposal.get('id', 'DEMO'))
    demo_content_library()
    demo_dashboard()
    demo_proposal_workflow()
    demo_win_loss_analytics()

