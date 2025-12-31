#!/usr/bin/env python3
"""
Sanctions & PEP Screening Demo

Demonstrates screening against commercial lists:
- Dow Jones Risk & Compliance
- LSEG (Refinitiv) World-Check
- Sanctions lists (OFAC, EU, UN)
- PEP databases
- Adverse media
"""

import sys
sys.path.insert(0, '../backend')

from datetime import datetime, timedelta
from typing import List, Dict

# Import the screening service
try:
    from app.services.screening_lists import (
        ScreeningService,
        ScreeningListType,
        MatchConfidence
    )
    HAS_SERVICE = True
except ImportError:
    HAS_SERVICE = False
    print("Note: Running in demo mode. Install backend dependencies for full functionality.")


def demo_sanctions_screening():
    """Demonstrate sanctions screening."""
    
    print("=" * 60)
    print("Sanctions Screening Demo")
    print("=" * 60)
    print("""
    Screening names against sanctions lists:
    - OFAC SDN List
    - EU Consolidated List
    - UN Security Council List
    - MAS List
    """)
    
    names_to_screen = [
        {"name": "Kim Jong Un", "entity_type": "individual"},
        {"name": "Vladimir Putin", "entity_type": "individual"},
        {"name": "John Smith", "entity_type": "individual"},
        {"name": "Acme Trading Corp", "entity_type": "organization"},
        {"name": "Bank of Iran", "entity_type": "organization"},
    ]
    
    print("\nScreening names:")
    for item in names_to_screen:
        print(f"  • {item['name']} ({item['entity_type']})")
    
    print("\n" + "-" * 40)
    
    if HAS_SERVICE:
        service = ScreeningService()
        
        for item in names_to_screen:
            print(f"\nScreening: {item['name']}")
            result = service.screen(
                name=item['name'],
                entity_type=item['entity_type'],
                list_types=[ScreeningListType.SANCTIONS]
            )
            display_screening_result(result)
    else:
        demo_mode_screening(names_to_screen, "sanctions")


def demo_pep_screening():
    """Demonstrate PEP screening."""
    
    print("\n\n" + "=" * 60)
    print("PEP (Politically Exposed Person) Screening Demo")
    print("=" * 60)
    print("""
    Identifying politically exposed persons:
    - Current/former government officials
    - Senior military/judicial officers
    - Senior executives of state corporations
    - Family members and close associates
    """)
    
    names_to_screen = [
        {"name": "Minister Lee Hsien Loong", "entity_type": "individual"},
        {"name": "Senator Johnson", "entity_type": "individual"},
        {"name": "Governor Maria Santos", "entity_type": "individual"},
        {"name": "Jane Doe", "entity_type": "individual"},
    ]
    
    print("\nScreening for PEP status:")
    for item in names_to_screen:
        print(f"  • {item['name']}")
    
    print("\n" + "-" * 40)
    
    if HAS_SERVICE:
        service = ScreeningService()
        
        for item in names_to_screen:
            print(f"\nScreening: {item['name']}")
            result = service.screen(
                name=item['name'],
                entity_type=item['entity_type'],
                list_types=[ScreeningListType.PEP]
            )
            display_screening_result(result)
    else:
        demo_mode_screening(names_to_screen, "pep")


def demo_comprehensive_screening():
    """Demonstrate comprehensive screening across all lists."""
    
    print("\n\n" + "=" * 60)
    print("Comprehensive Screening Demo")
    print("=" * 60)
    print("""
    Full screening across all data sources:
    - Dow Jones Watchlist
    - Refinitiv World-Check
    - Sanctions (OFAC, EU, UN)
    - PEP databases
    - Adverse media
    - Enforcement actions
    """)
    
    # Customer to screen
    customer = {
        "name": "Vladimir Petrov",
        "entity_type": "individual",
        "data": {
            "date_of_birth": "1970-05-15",
            "nationality": "RU",
            "country_of_residence": "CH"
        }
    }
    
    print(f"\nCustomer: {customer['name']}")
    print(f"Nationality: {customer['data']['nationality']}")
    print(f"Residence: {customer['data']['country_of_residence']}")
    print("-" * 40)
    
    if HAS_SERVICE:
        service = ScreeningService()
        
        result = service.screen(
            name=customer['name'],
            entity_type=customer['entity_type'],
            additional_data=customer['data']
        )
        
        display_screening_result(result, detailed=True)
    else:
        demo_mode_comprehensive(customer)


def demo_batch_screening():
    """Demonstrate batch screening."""
    
    print("\n\n" + "=" * 60)
    print("Batch Screening Demo")
    print("=" * 60)
    print("""
    Screening multiple names efficiently in batch.
    Common use cases:
    - Daily customer file screening
    - Periodic re-screening
    - Onboarding batch processing
    """)
    
    names = [
        {"name": "Alice Johnson", "entity_type": "individual"},
        {"name": "Bob Smith", "entity_type": "individual"},
        {"name": "Global Trading Ltd", "entity_type": "organization"},
        {"name": "Import Export Co", "entity_type": "organization"},
        {"name": "Charlie Brown", "entity_type": "individual"},
        {"name": "Diana Ross", "entity_type": "individual"},
        {"name": "Eastern Bank", "entity_type": "organization"},
        {"name": "Frank Miller", "entity_type": "individual"},
    ]
    
    print(f"\nBatch screening {len(names)} names...")
    print("-" * 40)
    
    if HAS_SERVICE:
        service = ScreeningService()
        results = service.batch_screen(names)
        
        # Summary
        total_matches = sum(r.total_matches for r in results)
        sanctions_hits = sum(1 for r in results if r.has_sanctions_match())
        pep_hits = sum(1 for r in results if r.has_pep_match())
        
        print(f"\nBatch Summary:")
        print(f"  Names screened: {len(names)}")
        print(f"  Total matches: {total_matches}")
        print(f"  Sanctions hits: {sanctions_hits}")
        print(f"  PEP hits: {pep_hits}")
        
        # Show any hits
        for result in results:
            if result.total_matches > 0:
                print(f"\n⚠️  {result.query_name}: {result.total_matches} match(es)")
                print(f"    Action: {result.recommended_action}")
    else:
        print(f"[Demo Mode] Would screen {len(names)} names")
        print("  Providers: Dow Jones, Refinitiv")
        print("  Lists: Sanctions, PEP, Adverse Media")


def display_screening_result(result, detailed=False):
    """Display screening result."""
    
    action_icons = {
        "clear": "✅",
        "review": "🔍",
        "review_sanctions": "⚠️",
        "review_pep": "👤",
        "review_media": "📰",
        "escalate_sanctions": "🔴",
        "reject_sanctions_exact": "⛔",
        "enhanced_due_diligence": "📋"
    }
    
    if result.total_matches == 0:
        print("  ✅ No matches found - CLEAR")
        return
    
    icon = action_icons.get(result.recommended_action, "⚠️")
    print(f"  {icon} {result.total_matches} match(es) found")
    print(f"  Recommended Action: {result.recommended_action}")
    
    if detailed and result.matches:
        print(f"\n  Matches:")
        for match in result.matches[:5]:
            conf_icon = "🔴" if match.confidence.value in ["exact", "strong"] else "🟡"
            print(f"    {conf_icon} {match.matched_name}")
            print(f"       List: {match.list_source} - {match.list_type.value}")
            print(f"       Confidence: {match.confidence.value} ({match.match_score:.0%})")
            if match.sanctions_programs:
                print(f"       Programs: {', '.join(match.sanctions_programs)}")
            if match.categories:
                print(f"       Categories: {', '.join(match.categories)}")


def demo_mode_screening(names: List[Dict], list_type: str):
    """Demo mode screening output."""
    
    print("\n[Demo Mode - Simulated Screening Results]")
    
    for item in names:
        name = item['name'].lower()
        
        # Simulate matches for known sanctioned names
        if 'kim' in name or 'putin' in name or 'iran' in name:
            print(f"\n  ⚠️  {item['name']}")
            print(f"     MATCH FOUND - {list_type.upper()}")
            print(f"     Action: Escalate for review")
        else:
            print(f"\n  ✅ {item['name']}")
            print(f"     No matches - CLEAR")


def demo_mode_comprehensive(customer: Dict):
    """Demo mode comprehensive screening."""
    
    print("\n[Demo Mode - Comprehensive Screening]")
    print("\nProviders checked:")
    print("  ✓ Dow Jones Risk & Compliance")
    print("  ✓ Refinitiv World-Check")
    print("\nLists checked:")
    print("  ✓ OFAC SDN")
    print("  ✓ EU Consolidated")
    print("  ✓ UN Security Council")
    print("  ✓ PEP databases")
    print("  ✓ Adverse Media")
    print("\nResult: See actual output when service is running")


def screening_summary():
    """Show screening capabilities summary."""
    
    print("\n\n" + "=" * 60)
    print("Screening Capabilities Summary")
    print("=" * 60)
    print("""
    FTex integrates with commercial screening providers:
    
    📊 DOW JONES RISK & COMPLIANCE
       - Watchlist screening
       - PEP identification
       - Sanctions coverage
       - State ownership data
       - Adverse media monitoring
    
    📊 LSEG REFINITIV WORLD-CHECK
       - World-Check One database
       - PEP and RCA data
       - Sanctions lists
       - Adverse media
       - Enforcement actions
    
    📋 SANCTIONS LISTS
       - OFAC SDN & Non-SDN
       - EU Consolidated List
       - UN Security Council
       - MAS List (Singapore)
       - HM Treasury (UK)
    
    Features:
       ✓ Fuzzy name matching
       ✓ Transliteration support
       ✓ Alias matching
       ✓ Configurable thresholds
       ✓ Batch processing
       ✓ Audit trail
       ✓ Recommended actions
    """)


if __name__ == "__main__":
    demo_sanctions_screening()
    demo_pep_screening()
    demo_comprehensive_screening()
    demo_batch_screening()
    screening_summary()

