#!/usr/bin/env python3
"""
Blockchain/Crypto Fraud Detection Demo

Demonstrates detection of crypto-specific fraud patterns:
- Mixer/tumbler usage
- Sanctioned wallet interactions
- Layering through multiple wallets
- Darknet market transactions
- Chain hopping
"""

import sys
sys.path.insert(0, '../backend')

from datetime import datetime, timedelta
from typing import List, Dict

# Import the fraud detection service
try:
    from app.services.fraud_detection import (
        BlockchainFraudDetector,
        FraudAlert,
        FraudRiskLevel
    )
    HAS_SERVICE = True
except ImportError:
    HAS_SERVICE = False
    print("Note: Running in demo mode. Install backend dependencies for full functionality.")


def create_sample_transaction(
    from_address: str,
    to_address: str,
    amount: float,
    currency: str = "ETH",
    hours_ago: int = 0
) -> Dict:
    """Create a sample blockchain transaction."""
    return {
        "tx_hash": f"0x{abs(hash(f'{from_address}{to_address}{amount}'))%10**64:064x}",
        "from_address": from_address,
        "to_address": to_address,
        "amount": amount,
        "currency": currency,
        "timestamp": datetime.now() - timedelta(hours=hours_ago),
        "block_number": 18500000 - hours_ago * 100,
        "gas_used": 21000,
        "status": "confirmed"
    }


def demo_mixer_detection():
    """Demonstrate mixer/tumbler detection."""
    
    print("=" * 60)
    print("Scenario 1: Mixer Usage Detection")
    print("=" * 60)
    print("""
    Mixers/Tumblers are services that obscure the source of funds
    by mixing crypto from multiple sources.
    
    Red flags:
    - Sending funds to known mixer addresses
    - Receiving funds from mixer addresses
    - Pattern of send-to-mixer, receive-from-different-address
    """)
    
    # Transaction to a mixer
    history = []
    current_txn = create_sample_transaction(
        from_address="0x742d35Cc6634C0532925a3b844Bc9e7595f1e123",
        to_address="0xTornado_Cash_Router_Address_Pattern",  # Known mixer
        amount=10.0,
        currency="ETH"
    )
    
    analyze_blockchain_transaction("Mixer Usage", current_txn, history)


def demo_sanctioned_wallet():
    """Demonstrate sanctioned wallet detection."""
    
    print("\n\n" + "=" * 60)
    print("Scenario 2: Sanctioned Wallet Interaction")
    print("=" * 60)
    print("""
    OFAC and other regulators maintain lists of sanctioned 
    cryptocurrency addresses. Any interaction is prohibited.
    
    Detection:
    - Receiving funds from sanctioned addresses
    - Sending funds to sanctioned addresses
    - Intermediate hops involving sanctioned wallets
    """)
    
    history = []
    
    # Transaction involving sanctioned address
    current_txn = create_sample_transaction(
        from_address="0x8589427373D6D84E98730D7795D8f6f8731FDA16",  # Sanctioned prefix
        to_address="0x742d35Cc6634C0532925a3b844Bc9e7595f1e456",
        amount=50.0,
        currency="ETH"
    )
    
    analyze_blockchain_transaction("Sanctioned Wallet", current_txn, history)


def demo_layering_pattern():
    """Demonstrate layering detection."""
    
    print("\n\n" + "=" * 60)
    print("Scenario 3: Layering Pattern Detection")
    print("=" * 60)
    print("""
    Layering: Moving funds through many wallets to obscure origin
    
    Indicators:
    - Rapid movement through multiple addresses
    - Many unique addresses in short timeframe
    - Amount splitting and reconsolidation
    """)
    
    # Create history showing layering pattern
    wallets = [f"0x{i:040x}" for i in range(1, 12)]
    
    history = []
    for i in range(10):
        history.append(create_sample_transaction(
            from_address=wallets[i],
            to_address=wallets[i + 1],
            amount=10.0 - (i * 0.1),  # Decreasing amounts (fees)
            hours_ago=10 - i
        ))
    
    current_txn = create_sample_transaction(
        from_address=wallets[-2],
        to_address="0xFinal_Destination_Address",
        amount=9.0
    )
    
    analyze_blockchain_transaction("Layering", current_txn, history)


def demo_rapid_transactions():
    """Demonstrate rapid transaction pattern detection."""
    
    print("\n\n" + "=" * 60)
    print("Scenario 4: Rapid Transaction Pattern")
    print("=" * 60)
    print("""
    Suspiciously rapid transactions may indicate:
    - Bot/automated activity
    - Wash trading
    - Market manipulation
    - Layering attempts
    """)
    
    # Create many transactions in very short time
    history = []
    for i in range(15):
        history.append(create_sample_transaction(
            from_address="0xSameSourceWallet",
            to_address=f"0x{i:040x}",
            amount=1.0,
            hours_ago=0  # All within same hour
        ))
        # Override timestamp to be within seconds of each other
        history[-1]["timestamp"] = datetime.now() - timedelta(seconds=i * 30)
    
    current_txn = create_sample_transaction(
        from_address="0xSameSourceWallet",
        to_address="0xAnotherAddress",
        amount=1.0
    )
    
    analyze_blockchain_transaction("Rapid Transactions", current_txn, history)


def demo_chain_hopping():
    """Demonstrate chain hopping detection."""
    
    print("\n\n" + "=" * 60)
    print("Scenario 5: Chain Hopping Detection")
    print("=" * 60)
    print("""
    Chain hopping: Moving between different blockchains to obscure trail
    
    Pattern:
    - ETH -> Bridge -> BSC -> Bridge -> Polygon -> etc.
    - Multiple different tokens/chains in short period
    - Cross-chain bridges to privacy chains
    """)
    
    # History showing multiple currencies
    history = [
        create_sample_transaction("0xAddr1", "0xBridge", 10, "ETH", hours_ago=5),
        create_sample_transaction("0xBridge", "0xAddr2", 9.9, "BSC", hours_ago=4),
        create_sample_transaction("0xAddr2", "0xBridge2", 9.8, "MATIC", hours_ago=3),
        create_sample_transaction("0xBridge2", "0xAddr3", 9.7, "AVAX", hours_ago=2),
        create_sample_transaction("0xAddr3", "0xBridge3", 9.6, "FTM", hours_ago=1),
    ]
    
    current_txn = create_sample_transaction(
        from_address="0xBridge3",
        to_address="0xFinalAddress",
        amount=9.5,
        currency="USDT"
    )
    
    analyze_blockchain_transaction("Chain Hopping", current_txn, history)


def demo_dusting_attack():
    """Demonstrate dust transaction detection."""
    
    print("\n\n" + "=" * 60)
    print("Scenario 6: Dusting Attack Detection")
    print("=" * 60)
    print("""
    Dusting attacks: Sending tiny amounts to track wallet activity
    
    Purpose:
    - De-anonymization attempts
    - Tracking high-value wallets
    - Phishing preparation
    """)
    
    history = []
    
    # Dust transaction (very small amount)
    current_txn = create_sample_transaction(
        from_address="0xUnknownSender",
        to_address="0xTargetWallet",
        amount=0.00001,  # Very small amount
        currency="ETH"
    )
    
    analyze_blockchain_transaction("Dusting Attack", current_txn, history)


def analyze_blockchain_transaction(
    scenario: str,
    transaction: Dict,
    history: List[Dict]
):
    """Analyze a blockchain transaction for fraud."""
    
    print(f"\nAnalyzing: {transaction['amount']} {transaction['currency']}")
    print(f"From: {transaction['from_address'][:20]}...")
    print(f"To: {transaction['to_address'][:20]}...")
    print("-" * 40)
    
    if HAS_SERVICE:
        detector = BlockchainFraudDetector()
        alert = detector.detect_fraud(transaction, history)
        
        if alert:
            display_alert(alert)
        else:
            print("✅ No suspicious patterns detected")
    else:
        demo_mode_output(scenario, transaction)


def display_alert(alert: FraudAlert):
    """Display fraud alert details."""
    
    risk_icons = {
        FraudRiskLevel.LOW: "🟡",
        FraudRiskLevel.MEDIUM: "🟠",
        FraudRiskLevel.HIGH: "🔴",
        FraudRiskLevel.CRITICAL: "⛔"
    }
    
    icon = risk_icons.get(alert.risk_level, "⚪")
    
    print(f"\n{icon} BLOCKCHAIN FRAUD ALERT")
    print("=" * 40)
    print(f"Alert ID: {alert.alert_id}")
    print(f"Risk Level: {alert.risk_level.value.upper()}")
    print(f"Risk Score: {alert.risk_score:.2f}")
    print(f"Fraud Type: {alert.fraud_type.value}")
    
    print(f"\nIndicators Detected:")
    for indicator in alert.indicators:
        print(f"  ⚠️  {indicator}")
    
    if alert.evidence:
        print(f"\nEvidence:")
        for key, value in alert.evidence.items():
            print(f"  {key}: {value}")
    
    print(f"\n📋 Recommended Action:")
    print(f"  {alert.recommended_action}")


def demo_mode_output(scenario: str, transaction: Dict):
    """Demo mode output."""
    
    outputs = {
        "Mixer Usage": {
            "risk": "CRITICAL",
            "indicators": ["mixer_usage"],
            "action": "Block transaction and file SAR"
        },
        "Sanctioned Wallet": {
            "risk": "CRITICAL",
            "indicators": ["sanctioned_address"],
            "action": "Block transaction immediately - OFAC violation"
        },
        "Layering": {
            "risk": "HIGH",
            "indicators": ["layering_pattern"],
            "action": "Enhanced due diligence and transaction review"
        },
        "Rapid Transactions": {
            "risk": "MEDIUM",
            "indicators": ["suspicious_timing"],
            "action": "Monitor wallet activity"
        },
        "Chain Hopping": {
            "risk": "HIGH",
            "indicators": ["high_risk_exchange"],
            "action": "Enhanced due diligence"
        },
        "Dusting Attack": {
            "risk": "LOW",
            "indicators": ["potential_dust_attack"],
            "action": "Monitor wallet activity"
        }
    }
    
    output = outputs.get(scenario, {"risk": "UNKNOWN", "indicators": [], "action": "Review"})
    
    risk_icons = {"LOW": "🟡", "MEDIUM": "🟠", "HIGH": "🔴", "CRITICAL": "⛔"}
    icon = risk_icons.get(output["risk"], "⚪")
    
    print(f"\n[Demo Mode]")
    print(f"{icon} Risk Level: {output['risk']}")
    print(f"Indicators: {', '.join(output['indicators'])}")
    print(f"Action: {output['action']}")


def demo_summary():
    """Show blockchain fraud detection summary."""
    
    print("\n\n" + "=" * 60)
    print("Blockchain Fraud Detection Summary")
    print("=" * 60)
    print("""
    FTex Blockchain Fraud Detection covers:
    
    1. MIXER/TUMBLER DETECTION
       - Known mixer address database
       - Pattern recognition for mixer usage
       - Tornado Cash, Wasabi, Samurai detection
    
    2. SANCTIONS COMPLIANCE
       - OFAC sanctioned address list
       - Real-time screening
       - Hop analysis for sanctioned exposure
    
    3. LAYERING DETECTION
       - Multi-hop wallet analysis
       - Rapid movement patterns
       - Amount splitting detection
    
    4. TIMING ANALYSIS
       - Rapid transaction detection
       - Bot activity patterns
       - Wash trading indicators
    
    5. CHAIN HOPPING
       - Cross-chain movement tracking
       - Bridge usage analysis
       - Multi-currency patterns
    
    6. DUSTING ATTACKS
       - Small amount detection
       - De-anonymization attempt identification
    
    Integration points:
       - Exchange KYT (Know Your Transaction)
       - DeFi protocol monitoring
       - NFT marketplace screening
    """)


if __name__ == "__main__":
    demo_mixer_detection()
    demo_sanctioned_wallet()
    demo_layering_pattern()
    demo_rapid_transactions()
    demo_chain_hopping()
    demo_dusting_attack()
    demo_summary()

