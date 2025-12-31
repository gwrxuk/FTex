#!/usr/bin/env python3
"""
Credit Card Fraud Detection Demo

Demonstrates detection of various credit card fraud patterns:
- Card testing/probing attacks
- Velocity spikes
- Geographic anomalies (impossible travel)
- CNP fraud indicators
- Behavioral deviations
"""

import sys
sys.path.insert(0, '../backend')

from datetime import datetime, timedelta
from typing import List, Dict

# Import the fraud detection service
try:
    from app.services.fraud_detection import (
        CreditCardFraudDetector, 
        FraudAlert,
        FraudRiskLevel
    )
    HAS_SERVICE = True
except ImportError:
    HAS_SERVICE = False
    print("Note: Running in demo mode. Install backend dependencies for full functionality.")


def create_sample_transaction(
    amount: float,
    merchant_country: str = "SG",
    merchant_city: str = "Singapore",
    is_card_present: bool = True,
    cvv_match: bool = True,
    avs_match: bool = True,
    mcc: str = "5411",
    hours_ago: int = 0
) -> Dict:
    """Create a sample credit card transaction."""
    return {
        "transaction_id": f"TXN-{datetime.now().timestamp()}",
        "cardholder_id": "CH-12345",
        "amount": amount,
        "currency": "USD",
        "merchant_country": merchant_country,
        "merchant_city": merchant_city,
        "merchant_name": "Sample Merchant",
        "mcc": mcc,
        "is_card_present": is_card_present,
        "cvv_match": cvv_match,
        "avs_match": avs_match,
        "3ds_authenticated": is_card_present,
        "timestamp": datetime.now() - timedelta(hours=hours_ago),
        "status": "pending"
    }


def create_cardholder_profile() -> Dict:
    """Create a sample cardholder profile."""
    return {
        "cardholder_id": "CH-12345",
        "avg_transaction_amount": 150.00,
        "std_transaction_amount": 75.00,
        "usual_mccs": ["5411", "5812", "5541", "5942"],  # Grocery, Restaurant, Gas, Books
        "usual_hours": list(range(8, 23)),  # 8 AM to 11 PM
        "usual_countries": ["SG", "MY", "TH"],
        "account_age_days": 730
    }


def demo_card_testing_detection():
    """Demonstrate card testing/probing detection."""
    
    print("=" * 60)
    print("Scenario 1: Card Testing Attack")
    print("=" * 60)
    print("""
    Pattern: Multiple small transactions followed by larger ones
    - Fraudsters test stolen cards with small amounts
    - If successful, they make larger purchases
    """)
    
    # Transaction history showing testing pattern
    history = [
        create_sample_transaction(0.10, hours_ago=3),
        create_sample_transaction(1.00, hours_ago=2),
        create_sample_transaction(2.00, hours_ago=1),
    ]
    # Mark some as declined
    history[0]["status"] = "declined"
    history[1]["status"] = "declined"
    history[2]["status"] = "approved"
    
    # Current transaction - larger amount after successful test
    current_txn = create_sample_transaction(500.00)
    
    analyze_transaction("Card Testing", current_txn, history)


def demo_velocity_attack():
    """Demonstrate velocity spike detection."""
    
    print("\n\n" + "=" * 60)
    print("Scenario 2: Velocity Attack")
    print("=" * 60)
    print("""
    Pattern: Unusually high number of transactions in short period
    - Normal cardholder: 2-5 transactions per day
    - This case: 20+ transactions in a few hours
    """)
    
    # Create many transactions in short period
    history = [
        create_sample_transaction(50.00, hours_ago=i * 0.1)
        for i in range(20)
    ]
    
    current_txn = create_sample_transaction(75.00)
    
    analyze_transaction("Velocity Attack", current_txn, history)


def demo_impossible_travel():
    """Demonstrate impossible travel detection."""
    
    print("\n\n" + "=" * 60)
    print("Scenario 3: Impossible Travel")
    print("=" * 60)
    print("""
    Pattern: Transactions in different countries within impossible timeframe
    - Transaction in Singapore at 10:00 AM
    - Transaction in London at 11:00 AM (same day)
    - Flight time: 13+ hours
    """)
    
    # Recent transaction in Singapore
    history = [
        create_sample_transaction(200.00, merchant_country="SG", hours_ago=1)
    ]
    
    # Current transaction in UK - only 1 hour later
    current_txn = create_sample_transaction(
        500.00, 
        merchant_country="GB", 
        merchant_city="London"
    )
    
    analyze_transaction("Impossible Travel", current_txn, history)


def demo_cnp_fraud():
    """Demonstrate Card-Not-Present fraud detection."""
    
    print("\n\n" + "=" * 60)
    print("Scenario 4: Card-Not-Present Fraud")
    print("=" * 60)
    print("""
    Pattern: Online transaction with multiple risk indicators
    - CVV mismatch
    - AVS (Address Verification) mismatch
    - No 3D Secure authentication
    - High-risk merchant category
    """)
    
    history = []
    
    # CNP transaction with fraud indicators
    current_txn = create_sample_transaction(
        1500.00,
        is_card_present=False,
        cvv_match=False,
        avs_match=False,
        mcc="5967"  # Direct Marketing - high risk
    )
    current_txn["3ds_authenticated"] = False
    
    analyze_transaction("CNP Fraud Indicators", current_txn, history)


def demo_behavioral_deviation():
    """Demonstrate behavioral deviation detection."""
    
    print("\n\n" + "=" * 60)
    print("Scenario 5: Behavioral Deviation")
    print("=" * 60)
    print("""
    Pattern: Transaction deviates from cardholder's normal behavior
    - Unusual transaction amount (10x normal)
    - Unusual merchant category
    - Unusual time (3 AM)
    """)
    
    history = [
        create_sample_transaction(50.00, mcc="5411", hours_ago=24),
        create_sample_transaction(35.00, mcc="5812", hours_ago=48),
        create_sample_transaction(75.00, mcc="5541", hours_ago=72),
    ]
    
    # Unusual transaction
    current_txn = create_sample_transaction(
        2500.00,  # Much higher than usual
        mcc="7995"  # Gambling - unusual category
    )
    current_txn["timestamp"] = datetime.now().replace(hour=3)  # 3 AM
    
    profile = create_cardholder_profile()
    
    analyze_transaction("Behavioral Deviation", current_txn, history, profile)


def analyze_transaction(
    scenario: str, 
    transaction: Dict, 
    history: List[Dict],
    profile: Dict = None
):
    """Analyze a transaction for fraud."""
    
    print(f"\nAnalyzing transaction: ${transaction['amount']:.2f} at {transaction['merchant_country']}")
    print("-" * 40)
    
    if HAS_SERVICE:
        detector = CreditCardFraudDetector()
        alert = detector.detect_fraud(transaction, history, profile)
        
        if alert:
            display_alert(alert)
        else:
            print("✅ No fraud detected - Transaction appears legitimate")
    else:
        # Demo mode output
        print(f"[Demo Mode] Would analyze for: {scenario}")
        print("  Indicators checked:")
        print("    • Card testing patterns")
        print("    • Transaction velocity")
        print("    • Geographic anomalies")
        print("    • CNP fraud indicators")
        print("    • Behavioral deviations")


def display_alert(alert: FraudAlert):
    """Display fraud alert details."""
    
    risk_icons = {
        FraudRiskLevel.LOW: "🟡",
        FraudRiskLevel.MEDIUM: "🟠",
        FraudRiskLevel.HIGH: "🔴",
        FraudRiskLevel.CRITICAL: "⛔"
    }
    
    icon = risk_icons.get(alert.risk_level, "⚪")
    
    print(f"\n{icon} FRAUD ALERT GENERATED")
    print("=" * 40)
    print(f"Alert ID: {alert.alert_id}")
    print(f"Risk Level: {alert.risk_level.value.upper()}")
    print(f"Risk Score: {alert.risk_score:.2f}")
    print(f"Fraud Type: {alert.fraud_type.value}")
    
    print(f"\nIndicators Detected:")
    for indicator in alert.indicators:
        print(f"  ⚠️  {indicator}")
    
    print(f"\nEvidence:")
    for key, value in alert.evidence.items():
        print(f"  {key}: {value}")
    
    print(f"\n📋 Recommended Action:")
    print(f"  {alert.recommended_action}")


def demo_summary():
    """Show summary of fraud detection capabilities."""
    
    print("\n\n" + "=" * 60)
    print("Credit Card Fraud Detection Summary")
    print("=" * 60)
    print("""
    FTex Credit Card Fraud Detection covers:
    
    1. CARD TESTING
       - Small test transactions
       - Multiple declines followed by approval
       - Rapid succession of attempts
    
    2. VELOCITY ABUSE
       - Unusual transaction frequency
       - Rapid spending patterns
       - Statistical anomaly detection
    
    3. GEOGRAPHIC ANOMALIES
       - Impossible travel detection
       - Unusual location for cardholder
       - Cross-border pattern analysis
    
    4. CNP FRAUD INDICATORS
       - CVV/CVC mismatch
       - Address verification failures
       - Missing 3D Secure
       - High-risk merchant categories
    
    5. BEHAVIORAL DEVIATION
       - Amount anomalies
       - Category anomalies
       - Time-of-day anomalies
       - Device/location changes
    
    All detections generate:
    - Scored risk alerts
    - Detailed evidence
    - Recommended actions
    """)


if __name__ == "__main__":
    demo_card_testing_detection()
    demo_velocity_attack()
    demo_impossible_travel()
    demo_cnp_fraud()
    demo_behavioral_deviation()
    demo_summary()

