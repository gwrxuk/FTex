"""
Specialized Fraud Detection Service.

Implements fraud detection for specific domains as referenced in line 33 of plan.txt:
- Lending fraud
- Payments fraud (domestic/international/blockchain)
- Credit card fraud
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib


class FraudType(str, Enum):
    """Types of fraud detected."""
    CREDIT_CARD = "credit_card"
    LENDING = "lending"
    PAYMENT_DOMESTIC = "payment_domestic"
    PAYMENT_INTERNATIONAL = "payment_international"
    BLOCKCHAIN = "blockchain"
    IDENTITY = "identity"
    APPLICATION = "application"
    ACCOUNT_TAKEOVER = "account_takeover"


class FraudRiskLevel(str, Enum):
    """Fraud risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FraudAlert:
    """Fraud detection alert."""
    alert_id: str
    fraud_type: FraudType
    risk_level: FraudRiskLevel
    risk_score: float
    entity_id: str
    transaction_id: Optional[str]
    detected_at: datetime
    indicators: List[str]
    evidence: Dict[str, Any]
    recommended_action: str
    is_confirmed: bool = False


class CreditCardFraudDetector:
    """
    Credit Card Fraud Detection.
    
    Detects various credit card fraud patterns:
    - Card-not-present (CNP) fraud
    - Card testing/probing
    - Velocity attacks
    - Geographic anomalies
    - Merchant category code anomalies
    """
    
    # High-risk MCCs (Merchant Category Codes)
    HIGH_RISK_MCCS = {
        '5967': 'Direct Marketing',
        '5966': 'Direct Marketing-Outbound Telemarketing',
        '7995': 'Gambling',
        '5912': 'Drug Stores',
        '5999': 'Miscellaneous Retail',
        '4829': 'Money Transfer',
        '6051': 'Non-FI Money Orders',
        '6211': 'Securities Dealers',
    }
    
    # Test amount thresholds
    TEST_AMOUNTS = [0.01, 0.10, 1.00, 2.00]
    
    def __init__(self):
        self.velocity_window_hours = 24
        self.max_transactions_per_hour = 10
        self.max_decline_rate = 0.3
    
    def detect_fraud(
        self,
        transaction: Dict[str, Any],
        transaction_history: List[Dict[str, Any]],
        card_profile: Optional[Dict[str, Any]] = None
    ) -> Optional[FraudAlert]:
        """
        Analyze a credit card transaction for fraud.
        """
        indicators = []
        risk_score = 0.0
        evidence = {}
        
        # Check for card testing
        is_test, test_evidence = self._detect_card_testing(transaction, transaction_history)
        if is_test:
            indicators.append("card_testing_pattern")
            risk_score += 0.4
            evidence['card_testing'] = test_evidence
        
        # Check velocity
        velocity_risk, velocity_evidence = self._check_velocity(transaction, transaction_history)
        if velocity_risk > 0:
            indicators.append("high_velocity")
            risk_score += velocity_risk
            evidence['velocity'] = velocity_evidence
        
        # Check geographic anomaly
        geo_risk, geo_evidence = self._check_geographic_anomaly(transaction, transaction_history)
        if geo_risk > 0:
            indicators.append("geographic_anomaly")
            risk_score += geo_risk
            evidence['geographic'] = geo_evidence
        
        # Check MCC risk
        mcc = transaction.get('mcc')
        if mcc in self.HIGH_RISK_MCCS:
            indicators.append(f"high_risk_mcc_{mcc}")
            risk_score += 0.2
            evidence['mcc'] = {'code': mcc, 'category': self.HIGH_RISK_MCCS[mcc]}
        
        # Check CNP indicators
        if transaction.get('is_card_present') == False:
            if not transaction.get('cvv_match'):
                indicators.append("cvv_mismatch")
                risk_score += 0.25
            if not transaction.get('avs_match'):
                indicators.append("avs_mismatch")
                risk_score += 0.2
            if not transaction.get('3ds_authenticated'):
                indicators.append("no_3ds")
                risk_score += 0.15
        
        # Check behavioral deviation
        if card_profile:
            behavior_risk, behavior_evidence = self._check_behavioral_deviation(
                transaction, card_profile
            )
            if behavior_risk > 0:
                indicators.append("behavioral_deviation")
                risk_score += behavior_risk
                evidence['behavioral'] = behavior_evidence
        
        if not indicators:
            return None
        
        risk_score = min(1.0, risk_score)
        risk_level = self._score_to_level(risk_score)
        
        return FraudAlert(
            alert_id=self._generate_alert_id(transaction),
            fraud_type=FraudType.CREDIT_CARD,
            risk_level=risk_level,
            risk_score=risk_score,
            entity_id=transaction.get('cardholder_id', ''),
            transaction_id=transaction.get('transaction_id'),
            detected_at=datetime.utcnow(),
            indicators=indicators,
            evidence=evidence,
            recommended_action=self._get_recommended_action(risk_level, indicators)
        )
    
    def _detect_card_testing(
        self,
        transaction: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> tuple:
        """Detect card testing/probing patterns."""
        amount = transaction.get('amount', 0)
        
        # Small test amount
        if amount in self.TEST_AMOUNTS or amount < 5:
            # Check for subsequent larger transactions
            recent = [t for t in history if t.get('amount', 0) > amount]
            if len(recent) > 0:
                return True, {
                    'test_amount': amount,
                    'subsequent_transactions': len(recent)
                }
        
        # Multiple declines followed by approval
        recent_declines = [
            t for t in history[-10:]
            if t.get('status') == 'declined'
        ]
        if len(recent_declines) >= 3:
            return True, {
                'decline_count': len(recent_declines),
                'pattern': 'multiple_declines'
            }
        
        return False, {}
    
    def _check_velocity(
        self,
        transaction: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> tuple:
        """Check transaction velocity."""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=self.velocity_window_hours)
        
        recent = [
            t for t in history
            if t.get('timestamp', datetime.min) >= cutoff
        ]
        
        count = len(recent)
        if count > self.max_transactions_per_hour:
            return 0.3, {
                'transaction_count': count,
                'window_hours': self.velocity_window_hours,
                'threshold': self.max_transactions_per_hour
            }
        
        return 0, {}
    
    def _check_geographic_anomaly(
        self,
        transaction: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> tuple:
        """Check for impossible travel or geographic anomalies."""
        current_country = transaction.get('merchant_country')
        current_city = transaction.get('merchant_city')
        
        if not current_country:
            return 0, {}
        
        # Get last known location
        for t in reversed(history):
            prev_country = t.get('merchant_country')
            prev_time = t.get('timestamp')
            
            if prev_country and prev_country != current_country:
                # Check time difference
                current_time = transaction.get('timestamp', datetime.utcnow())
                if isinstance(prev_time, datetime):
                    hours_diff = (current_time - prev_time).total_seconds() / 3600
                    
                    # Impossible travel (less than 3 hours between countries)
                    if hours_diff < 3:
                        return 0.5, {
                            'current_country': current_country,
                            'previous_country': prev_country,
                            'hours_between': hours_diff,
                            'pattern': 'impossible_travel'
                        }
                break
        
        return 0, {}
    
    def _check_behavioral_deviation(
        self,
        transaction: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> tuple:
        """Check if transaction deviates from cardholder's normal behavior."""
        risk = 0.0
        evidence = {}
        
        # Amount deviation
        avg_amount = profile.get('avg_transaction_amount', 0)
        std_amount = profile.get('std_transaction_amount', 0)
        current_amount = transaction.get('amount', 0)
        
        if avg_amount > 0 and std_amount > 0:
            z_score = (current_amount - avg_amount) / std_amount
            if z_score > 3:
                risk += 0.2
                evidence['amount_z_score'] = z_score
        
        # Unusual merchant category
        usual_mccs = profile.get('usual_mccs', [])
        current_mcc = transaction.get('mcc')
        if usual_mccs and current_mcc and current_mcc not in usual_mccs:
            risk += 0.1
            evidence['unusual_mcc'] = current_mcc
        
        # Unusual time
        usual_hours = profile.get('usual_hours', list(range(8, 22)))
        current_hour = transaction.get('timestamp', datetime.utcnow()).hour
        if current_hour not in usual_hours:
            risk += 0.1
            evidence['unusual_hour'] = current_hour
        
        return risk, evidence
    
    def _score_to_level(self, score: float) -> FraudRiskLevel:
        """Convert score to risk level."""
        if score >= 0.8:
            return FraudRiskLevel.CRITICAL
        elif score >= 0.6:
            return FraudRiskLevel.HIGH
        elif score >= 0.3:
            return FraudRiskLevel.MEDIUM
        else:
            return FraudRiskLevel.LOW
    
    def _generate_alert_id(self, transaction: Dict[str, Any]) -> str:
        """Generate unique alert ID."""
        data = f"{transaction.get('transaction_id', '')}{datetime.utcnow().isoformat()}"
        return f"CC-{hashlib.md5(data.encode()).hexdigest()[:12].upper()}"
    
    def _get_recommended_action(self, level: FraudRiskLevel, indicators: List[str]) -> str:
        """Get recommended action based on risk level."""
        if level == FraudRiskLevel.CRITICAL:
            return "Block transaction and contact cardholder immediately"
        elif level == FraudRiskLevel.HIGH:
            return "Hold transaction pending cardholder verification"
        elif level == FraudRiskLevel.MEDIUM:
            return "Flag for review and monitor subsequent transactions"
        else:
            return "Monitor transaction pattern"


class BlockchainFraudDetector:
    """
    Blockchain/Crypto Transaction Fraud Detection.
    
    Detects:
    - Mixer/tumbler usage
    - Darknet market transactions
    - Sanctioned wallet interactions
    - High-risk exchange patterns
    - Layering through multiple wallets
    """
    
    # Known high-risk address patterns (simplified)
    HIGH_RISK_PATTERNS = {
        'mixer': ['tornado', 'wasabi', 'samurai'],
        'darknet': ['hydra', 'silk'],
        'gambling': ['stake', 'cloudbet']
    }
    
    # Sanctioned wallet prefixes (examples)
    SANCTIONED_PREFIXES = ['0x8589', '0x098B', '0xd90e']
    
    def __init__(self):
        self.max_hops = 3  # Max hops to trace
    
    def detect_fraud(
        self,
        transaction: Dict[str, Any],
        wallet_history: List[Dict[str, Any]],
        blockchain_data: Optional[Dict[str, Any]] = None
    ) -> Optional[FraudAlert]:
        """
        Analyze a blockchain transaction for fraud/money laundering.
        """
        indicators = []
        risk_score = 0.0
        evidence = {}
        
        from_address = transaction.get('from_address', '')
        to_address = transaction.get('to_address', '')
        
        # Check for mixer usage
        if self._is_mixer_address(to_address):
            indicators.append("mixer_usage")
            risk_score += 0.7
            evidence['mixer'] = {'address': to_address, 'type': 'outgoing'}
        
        if self._is_mixer_address(from_address):
            indicators.append("mixer_source")
            risk_score += 0.6
            evidence['mixer'] = {'address': from_address, 'type': 'incoming'}
        
        # Check for sanctioned addresses
        sanctioned = self._check_sanctioned_addresses(from_address, to_address)
        if sanctioned:
            indicators.append("sanctioned_address")
            risk_score += 1.0  # Automatic critical
            evidence['sanctioned'] = sanctioned
        
        # Check for layering patterns
        layering = self._detect_layering(transaction, wallet_history)
        if layering:
            indicators.append("layering_pattern")
            risk_score += 0.5
            evidence['layering'] = layering
        
        # Check transaction timing patterns
        timing_risk = self._check_timing_patterns(transaction, wallet_history)
        if timing_risk > 0:
            indicators.append("suspicious_timing")
            risk_score += timing_risk
            evidence['timing'] = {'risk': timing_risk}
        
        # Check for high-risk exchange patterns
        exchange_risk = self._check_exchange_patterns(transaction, wallet_history)
        if exchange_risk:
            indicators.append("high_risk_exchange")
            risk_score += 0.3
            evidence['exchange'] = exchange_risk
        
        # Check for dusting attacks
        if self._is_dust_transaction(transaction):
            indicators.append("potential_dust_attack")
            risk_score += 0.2
            evidence['dust'] = {'amount': transaction.get('amount')}
        
        if not indicators:
            return None
        
        risk_score = min(1.0, risk_score)
        risk_level = self._score_to_level(risk_score)
        
        return FraudAlert(
            alert_id=self._generate_alert_id(transaction),
            fraud_type=FraudType.BLOCKCHAIN,
            risk_level=risk_level,
            risk_score=risk_score,
            entity_id=transaction.get('wallet_id', from_address),
            transaction_id=transaction.get('tx_hash'),
            detected_at=datetime.utcnow(),
            indicators=indicators,
            evidence=evidence,
            recommended_action=self._get_recommended_action(risk_level, indicators)
        )
    
    def _is_mixer_address(self, address: str) -> bool:
        """Check if address is associated with a mixer."""
        address_lower = address.lower()
        for patterns in self.HIGH_RISK_PATTERNS.values():
            for pattern in patterns:
                if pattern in address_lower:
                    return True
        return False
    
    def _check_sanctioned_addresses(
        self,
        from_addr: str,
        to_addr: str
    ) -> Optional[Dict[str, Any]]:
        """Check if addresses are sanctioned."""
        for prefix in self.SANCTIONED_PREFIXES:
            if from_addr.lower().startswith(prefix.lower()):
                return {'address': from_addr, 'direction': 'from', 'list': 'OFAC'}
            if to_addr.lower().startswith(prefix.lower()):
                return {'address': to_addr, 'direction': 'to', 'list': 'OFAC'}
        return None
    
    def _detect_layering(
        self,
        transaction: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Detect potential layering through multiple wallets."""
        if len(history) < 5:
            return None
        
        # Look for rapid movement pattern
        recent = history[-10:]
        
        # Check for many unique addresses in short time
        unique_addresses = set()
        for tx in recent:
            unique_addresses.add(tx.get('from_address', ''))
            unique_addresses.add(tx.get('to_address', ''))
        
        if len(unique_addresses) > 8:
            return {
                'unique_addresses': len(unique_addresses),
                'transaction_count': len(recent),
                'pattern': 'multiple_wallet_hops'
            }
        
        return None
    
    def _check_timing_patterns(
        self,
        transaction: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> float:
        """Check for suspicious timing patterns."""
        if len(history) < 3:
            return 0.0
        
        # Check for very rapid transactions
        timestamps = [
            tx.get('timestamp') for tx in history
            if tx.get('timestamp')
        ]
        
        if len(timestamps) >= 2:
            # Sort timestamps
            timestamps.sort()
            
            # Check intervals
            rapid_count = 0
            for i in range(1, len(timestamps)):
                if isinstance(timestamps[i], datetime) and isinstance(timestamps[i-1], datetime):
                    interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                    if interval < 60:  # Less than 1 minute apart
                        rapid_count += 1
            
            if rapid_count >= 3:
                return 0.3
        
        return 0.0
    
    def _check_exchange_patterns(
        self,
        transaction: Dict[str, Any],
        history: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Check for high-risk exchange usage patterns."""
        # Look for patterns of converting between multiple currencies
        currencies = set()
        for tx in history[-20:]:
            currencies.add(tx.get('currency', ''))
        
        if len(currencies) > 5:
            return {
                'currencies_involved': list(currencies),
                'pattern': 'chain_hopping'
            }
        
        return None
    
    def _is_dust_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Check if transaction is a potential dusting attack."""
        amount = transaction.get('amount', 0)
        currency = transaction.get('currency', 'ETH')
        
        # Very small amounts that could be dusting
        dust_thresholds = {
            'BTC': 0.00001,
            'ETH': 0.0001,
            'USDT': 0.01
        }
        
        threshold = dust_thresholds.get(currency, 0.0001)
        return amount > 0 and amount < threshold
    
    def _score_to_level(self, score: float) -> FraudRiskLevel:
        """Convert score to risk level."""
        if score >= 0.8:
            return FraudRiskLevel.CRITICAL
        elif score >= 0.6:
            return FraudRiskLevel.HIGH
        elif score >= 0.3:
            return FraudRiskLevel.MEDIUM
        else:
            return FraudRiskLevel.LOW
    
    def _generate_alert_id(self, transaction: Dict[str, Any]) -> str:
        """Generate unique alert ID."""
        data = f"{transaction.get('tx_hash', '')}{datetime.utcnow().isoformat()}"
        return f"BC-{hashlib.md5(data.encode()).hexdigest()[:12].upper()}"
    
    def _get_recommended_action(self, level: FraudRiskLevel, indicators: List[str]) -> str:
        """Get recommended action."""
        if 'sanctioned_address' in indicators:
            return "Block transaction immediately - OFAC/sanctions violation"
        elif level == FraudRiskLevel.CRITICAL:
            return "Freeze wallet and file SAR"
        elif level == FraudRiskLevel.HIGH:
            return "Enhanced due diligence and transaction review"
        else:
            return "Monitor wallet activity"


class LendingFraudDetector:
    """
    Lending/Loan Fraud Detection.
    
    Detects:
    - Application fraud
    - Income fabrication
    - Identity fraud
    - Collusion patterns
    - First-party fraud
    """
    
    def __init__(self):
        self.income_deviation_threshold = 2.0
    
    def detect_fraud(
        self,
        application: Dict[str, Any],
        applicant_history: Optional[Dict[str, Any]] = None,
        bureau_data: Optional[Dict[str, Any]] = None
    ) -> Optional[FraudAlert]:
        """
        Analyze a loan application for fraud.
        """
        indicators = []
        risk_score = 0.0
        evidence = {}
        
        # Check income consistency
        income_check = self._verify_income(application, bureau_data)
        if income_check['risk'] > 0:
            indicators.append("income_discrepancy")
            risk_score += income_check['risk']
            evidence['income'] = income_check
        
        # Check employment verification
        employment_check = self._verify_employment(application)
        if employment_check['risk'] > 0:
            indicators.append("employment_concern")
            risk_score += employment_check['risk']
            evidence['employment'] = employment_check
        
        # Check for velocity abuse
        velocity_check = self._check_application_velocity(application, applicant_history)
        if velocity_check['risk'] > 0:
            indicators.append("application_velocity")
            risk_score += velocity_check['risk']
            evidence['velocity'] = velocity_check
        
        # Check address/identity consistency
        identity_check = self._verify_identity_consistency(application, bureau_data)
        if identity_check['risk'] > 0:
            indicators.append("identity_inconsistency")
            risk_score += identity_check['risk']
            evidence['identity'] = identity_check
        
        # Check for synthetic identity
        synthetic_check = self._detect_synthetic_identity(application, bureau_data)
        if synthetic_check['risk'] > 0:
            indicators.append("potential_synthetic_identity")
            risk_score += synthetic_check['risk']
            evidence['synthetic'] = synthetic_check
        
        # Check device/session anomalies
        device_check = self._check_device_anomalies(application)
        if device_check['risk'] > 0:
            indicators.append("device_anomaly")
            risk_score += device_check['risk']
            evidence['device'] = device_check
        
        if not indicators:
            return None
        
        risk_score = min(1.0, risk_score)
        risk_level = self._score_to_level(risk_score)
        
        return FraudAlert(
            alert_id=self._generate_alert_id(application),
            fraud_type=FraudType.LENDING,
            risk_level=risk_level,
            risk_score=risk_score,
            entity_id=application.get('applicant_id', ''),
            transaction_id=application.get('application_id'),
            detected_at=datetime.utcnow(),
            indicators=indicators,
            evidence=evidence,
            recommended_action=self._get_recommended_action(risk_level, indicators)
        )
    
    def _verify_income(
        self,
        application: Dict[str, Any],
        bureau_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Verify stated income against available data."""
        stated_income = application.get('annual_income', 0)
        
        if not bureau_data:
            return {'risk': 0, 'verified': False}
        
        bureau_income = bureau_data.get('estimated_income', 0)
        
        if stated_income > 0 and bureau_income > 0:
            ratio = stated_income / bureau_income
            if ratio > self.income_deviation_threshold:
                return {
                    'risk': 0.4,
                    'stated': stated_income,
                    'estimated': bureau_income,
                    'ratio': ratio,
                    'issue': 'income_inflated'
                }
        
        return {'risk': 0, 'verified': True}
    
    def _verify_employment(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """Check employment information."""
        employer = application.get('employer', '')
        employment_length = application.get('employment_length_months', 0)
        
        risk = 0.0
        issues = []
        
        # Very short employment with high income
        if employment_length < 6 and application.get('annual_income', 0) > 200000:
            risk += 0.2
            issues.append('short_tenure_high_income')
        
        # Self-employed with no business verification
        if application.get('employment_type') == 'self_employed':
            if not application.get('business_verified'):
                risk += 0.15
                issues.append('unverified_self_employment')
        
        return {'risk': risk, 'issues': issues}
    
    def _check_application_velocity(
        self,
        application: Dict[str, Any],
        history: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check for multiple applications in short period."""
        if not history:
            return {'risk': 0}
        
        recent_apps = history.get('applications_last_30_days', 0)
        
        if recent_apps > 5:
            return {
                'risk': 0.4,
                'recent_applications': recent_apps,
                'issue': 'high_application_velocity'
            }
        elif recent_apps > 3:
            return {
                'risk': 0.2,
                'recent_applications': recent_apps,
                'issue': 'moderate_application_velocity'
            }
        
        return {'risk': 0}
    
    def _verify_identity_consistency(
        self,
        application: Dict[str, Any],
        bureau_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check identity data consistency."""
        if not bureau_data:
            return {'risk': 0}
        
        issues = []
        risk = 0.0
        
        # Name mismatch
        app_name = application.get('name', '').lower()
        bureau_name = bureau_data.get('name', '').lower()
        if app_name and bureau_name and app_name != bureau_name:
            risk += 0.2
            issues.append('name_mismatch')
        
        # DOB mismatch
        app_dob = application.get('date_of_birth')
        bureau_dob = bureau_data.get('date_of_birth')
        if app_dob and bureau_dob and app_dob != bureau_dob:
            risk += 0.3
            issues.append('dob_mismatch')
        
        # SSN/ID issues
        if bureau_data.get('ssn_issues'):
            risk += 0.4
            issues.append('ssn_concerns')
        
        return {'risk': risk, 'issues': issues}
    
    def _detect_synthetic_identity(
        self,
        application: Dict[str, Any],
        bureau_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detect potential synthetic identity."""
        if not bureau_data:
            return {'risk': 0}
        
        indicators = []
        risk = 0.0
        
        # Thin credit file with recent accounts
        if bureau_data.get('credit_file_age_months', 0) < 12:
            if bureau_data.get('account_count', 0) >= 5:
                risk += 0.3
                indicators.append('new_file_many_accounts')
        
        # No historical address
        if not bureau_data.get('historical_addresses'):
            risk += 0.2
            indicators.append('no_address_history')
        
        # Authorized user abuse
        if bureau_data.get('authorized_user_accounts', 0) > 3:
            risk += 0.2
            indicators.append('high_au_accounts')
        
        return {'risk': risk, 'indicators': indicators} if indicators else {'risk': 0}
    
    def _check_device_anomalies(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """Check for device/session anomalies."""
        risk = 0.0
        issues = []
        
        device_info = application.get('device_info', {})
        
        # VPN/Proxy usage
        if device_info.get('is_vpn') or device_info.get('is_proxy'):
            risk += 0.2
            issues.append('vpn_proxy_detected')
        
        # Device fingerprint seen with other identities
        if device_info.get('other_identities_count', 0) > 1:
            risk += 0.3
            issues.append('device_shared_identity')
        
        # Geolocation mismatch
        if device_info.get('geo_mismatch'):
            risk += 0.2
            issues.append('geolocation_mismatch')
        
        return {'risk': risk, 'issues': issues}
    
    def _score_to_level(self, score: float) -> FraudRiskLevel:
        """Convert score to risk level."""
        if score >= 0.7:
            return FraudRiskLevel.CRITICAL
        elif score >= 0.5:
            return FraudRiskLevel.HIGH
        elif score >= 0.3:
            return FraudRiskLevel.MEDIUM
        else:
            return FraudRiskLevel.LOW
    
    def _generate_alert_id(self, application: Dict[str, Any]) -> str:
        """Generate unique alert ID."""
        data = f"{application.get('application_id', '')}{datetime.utcnow().isoformat()}"
        return f"LF-{hashlib.md5(data.encode()).hexdigest()[:12].upper()}"
    
    def _get_recommended_action(self, level: FraudRiskLevel, indicators: List[str]) -> str:
        """Get recommended action."""
        if 'potential_synthetic_identity' in indicators:
            return "Decline application and flag for fraud investigation"
        elif level == FraudRiskLevel.CRITICAL:
            return "Decline application"
        elif level == FraudRiskLevel.HIGH:
            return "Request additional documentation and verification"
        elif level == FraudRiskLevel.MEDIUM:
            return "Enhanced manual review required"
        else:
            return "Proceed with standard underwriting"


class FraudDetectionService:
    """
    Unified Fraud Detection Service.
    
    Orchestrates all fraud detection capabilities.
    """
    
    def __init__(self):
        self.credit_card_detector = CreditCardFraudDetector()
        self.blockchain_detector = BlockchainFraudDetector()
        self.lending_detector = LendingFraudDetector()
    
    def detect_credit_card_fraud(
        self,
        transaction: Dict[str, Any],
        history: List[Dict[str, Any]],
        profile: Optional[Dict[str, Any]] = None
    ) -> Optional[FraudAlert]:
        """Detect credit card fraud."""
        return self.credit_card_detector.detect_fraud(transaction, history, profile)
    
    def detect_blockchain_fraud(
        self,
        transaction: Dict[str, Any],
        wallet_history: List[Dict[str, Any]],
        blockchain_data: Optional[Dict[str, Any]] = None
    ) -> Optional[FraudAlert]:
        """Detect blockchain/crypto fraud."""
        return self.blockchain_detector.detect_fraud(transaction, wallet_history, blockchain_data)
    
    def detect_lending_fraud(
        self,
        application: Dict[str, Any],
        applicant_history: Optional[Dict[str, Any]] = None,
        bureau_data: Optional[Dict[str, Any]] = None
    ) -> Optional[FraudAlert]:
        """Detect lending fraud."""
        return self.lending_detector.detect_fraud(application, applicant_history, bureau_data)

