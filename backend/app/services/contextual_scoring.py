"""
FTex Contextual Scoring Engine

Provides context-aware risk scoring using:
- Entity attributes
- Network relationships
- Transaction patterns
- External data (sanctions, PEP, adverse media)

The key FTex differentiator: scoring based on network CONTEXT,
not just individual attributes.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import math


class RiskCategory(str, Enum):
    """Risk categories for scoring."""
    SANCTIONS = "sanctions"
    PEP = "pep"
    ADVERSE_MEDIA = "adverse_media"
    JURISDICTION = "jurisdiction"
    TRANSACTION_PATTERN = "transaction_pattern"
    NETWORK = "network"
    BEHAVIORAL = "behavioral"
    KYC = "kyc"
    FRAUD = "fraud"


@dataclass
class RiskFactor:
    """A single risk factor contributing to overall score."""
    category: RiskCategory
    name: str
    score: float  # 0.0 to 1.0
    weight: float  # Importance weight
    evidence: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class RiskScore:
    """Comprehensive risk score for an entity."""
    entity_id: str
    overall_score: float
    risk_level: str  # low, medium, high, critical
    factors: List[RiskFactor]
    network_context: Dict[str, Any] = field(default_factory=dict)
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def calculate_level(cls, score: float) -> str:
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"


class ScoringRule:
    """Base class for scoring rules."""
    
    def __init__(
        self, 
        category: RiskCategory, 
        name: str,
        weight: float = 1.0
    ):
        self.category = category
        self.name = name
        self.weight = weight
    
    def evaluate(self, entity: Dict[str, Any], context: Dict[str, Any]) -> Optional[RiskFactor]:
        """Evaluate the rule and return a risk factor if applicable."""
        raise NotImplementedError


class SanctionsRule(ScoringRule):
    """Check if entity matches sanctions lists."""
    
    def __init__(self, weight: float = 1.0):
        super().__init__(RiskCategory.SANCTIONS, "sanctions_match", weight)
        self.sanctions_lists = ["OFAC", "EU", "UN", "MAS"]
    
    def evaluate(self, entity: Dict[str, Any], context: Dict[str, Any]) -> Optional[RiskFactor]:
        is_sanctioned = entity.get('is_sanctioned', False)
        matched_lists = entity.get('matched_sanctions_lists', [])
        
        if is_sanctioned or matched_lists:
            return RiskFactor(
                category=self.category,
                name=self.name,
                score=1.0,  # Sanctions are always highest risk
                weight=self.weight,
                evidence={
                    'matched_lists': matched_lists or ['Unknown'],
                    'match_type': entity.get('sanctions_match_type', 'exact')
                },
                description="Entity appears on sanctions list"
            )
        return None


class PEPRule(ScoringRule):
    """Check if entity is a Politically Exposed Person."""
    
    def __init__(self, weight: float = 0.8):
        super().__init__(RiskCategory.PEP, "pep_status", weight)
    
    def evaluate(self, entity: Dict[str, Any], context: Dict[str, Any]) -> Optional[RiskFactor]:
        is_pep = entity.get('is_pep', False)
        pep_level = entity.get('pep_level', 'unknown')  # domestic, foreign, international_org
        
        if is_pep:
            # Score based on PEP level
            score_map = {
                'head_of_state': 1.0,
                'senior_government': 0.9,
                'international_org': 0.85,
                'domestic': 0.7,
                'foreign': 0.8,
                'family_associate': 0.6,
                'unknown': 0.75
            }
            score = score_map.get(pep_level, 0.75)
            
            return RiskFactor(
                category=self.category,
                name=self.name,
                score=score,
                weight=self.weight,
                evidence={
                    'pep_level': pep_level,
                    'position': entity.get('pep_position'),
                    'country': entity.get('pep_country')
                },
                description=f"Politically Exposed Person ({pep_level})"
            )
        return None


class JurisdictionRule(ScoringRule):
    """Assess risk based on geographic jurisdiction."""
    
    HIGH_RISK_JURISDICTIONS = {
        # FATF high-risk
        'KP': 1.0, 'IR': 1.0, 'MM': 0.95, 'SY': 0.95, 'YE': 0.9,
        # Increased monitoring
        'AF': 0.8, 'PK': 0.7, 'VE': 0.7, 'ZW': 0.7,
        # Tax havens
        'KY': 0.5, 'VG': 0.5, 'PA': 0.5, 'BZ': 0.5
    }
    
    def __init__(self, weight: float = 0.6):
        super().__init__(RiskCategory.JURISDICTION, "jurisdiction_risk", weight)
    
    def evaluate(self, entity: Dict[str, Any], context: Dict[str, Any]) -> Optional[RiskFactor]:
        country = entity.get('country') or entity.get('jurisdiction')
        
        if country and country.upper() in self.HIGH_RISK_JURISDICTIONS:
            score = self.HIGH_RISK_JURISDICTIONS[country.upper()]
            return RiskFactor(
                category=self.category,
                name=self.name,
                score=score,
                weight=self.weight,
                evidence={
                    'country': country,
                    'risk_classification': 'FATF high-risk' if score >= 0.9 else 'elevated'
                },
                description=f"High-risk jurisdiction: {country}"
            )
        return None


class TransactionPatternRule(ScoringRule):
    """Analyze transaction patterns for suspicious activity."""
    
    def __init__(self, weight: float = 0.7):
        super().__init__(RiskCategory.TRANSACTION_PATTERN, "transaction_pattern", weight)
    
    def evaluate(self, entity: Dict[str, Any], context: Dict[str, Any]) -> Optional[RiskFactor]:
        tx_stats = context.get('transaction_stats', {})
        
        risk_indicators = []
        score = 0.0
        
        # High volume
        if tx_stats.get('total_volume', 0) > 1000000:
            risk_indicators.append('high_volume')
            score += 0.2
        
        # Structuring pattern (many transactions just under threshold)
        if tx_stats.get('structuring_indicator', 0) > 0.7:
            risk_indicators.append('potential_structuring')
            score += 0.4
        
        # Rapid movement (quick in-and-out)
        if tx_stats.get('passthrough_ratio', 0) > 0.9:
            risk_indicators.append('rapid_passthrough')
            score += 0.3
        
        # Round amounts
        if tx_stats.get('round_amount_ratio', 0) > 0.5:
            risk_indicators.append('round_amounts')
            score += 0.1
        
        # Cross-border concentration
        if tx_stats.get('cross_border_ratio', 0) > 0.7:
            risk_indicators.append('high_cross_border')
            score += 0.2
        
        # Cash intensity
        if tx_stats.get('cash_ratio', 0) > 0.4:
            risk_indicators.append('cash_intensive')
            score += 0.2
        
        if risk_indicators:
            return RiskFactor(
                category=self.category,
                name=self.name,
                score=min(1.0, score),
                weight=self.weight,
                evidence={
                    'indicators': risk_indicators,
                    'stats': tx_stats
                },
                description=f"Transaction pattern risks: {', '.join(risk_indicators)}"
            )
        return None


class NetworkContextRule(ScoringRule):
    """
    The key FTex differentiator: scoring based on network context.
    
    Evaluates risk based on:
    - Connected entity risk scores
    - Relationship types
    - Network structure (centrality, clustering)
    """
    
    def __init__(self, weight: float = 0.8):
        super().__init__(RiskCategory.NETWORK, "network_context", weight)
    
    def evaluate(self, entity: Dict[str, Any], context: Dict[str, Any]) -> Optional[RiskFactor]:
        network_context = context.get('network', {})
        
        if not network_context:
            return None
        
        risk_indicators = []
        score = 0.0
        
        # Connected to high-risk entities
        high_risk_connections = network_context.get('high_risk_connections', 0)
        if high_risk_connections > 0:
            risk_indicators.append(f'{high_risk_connections} high-risk connections')
            score += min(0.4, high_risk_connections * 0.1)
        
        # Connected to sanctioned entity
        sanctioned_connections = network_context.get('sanctioned_connections', 0)
        if sanctioned_connections > 0:
            risk_indicators.append(f'{sanctioned_connections} sanctioned connections')
            score += min(0.5, sanctioned_connections * 0.2)
        
        # Network density (highly connected = potential shell network)
        if network_context.get('clustering_coefficient', 0) > 0.7:
            risk_indicators.append('dense_network_cluster')
            score += 0.15
        
        # High centrality (key player in network)
        if network_context.get('centrality_score', 0) > 0.8:
            risk_indicators.append('high_network_centrality')
            score += 0.1
        
        # Part of circular flow
        if network_context.get('in_circular_flow', False):
            risk_indicators.append('circular_transaction_flow')
            score += 0.3
        
        # Risk propagation from network
        propagated_risk = network_context.get('propagated_risk', 0)
        if propagated_risk > 0.3:
            risk_indicators.append(f'network_risk_exposure')
            score += propagated_risk * 0.5
        
        if risk_indicators:
            return RiskFactor(
                category=self.category,
                name=self.name,
                score=min(1.0, score),
                weight=self.weight,
                evidence={
                    'indicators': risk_indicators,
                    'network_metrics': network_context
                },
                description=f"Network context risks: {', '.join(risk_indicators)}"
            )
        return None


class BehavioralRule(ScoringRule):
    """Assess behavioral anomalies."""
    
    def __init__(self, weight: float = 0.6):
        super().__init__(RiskCategory.BEHAVIORAL, "behavioral_anomaly", weight)
    
    def evaluate(self, entity: Dict[str, Any], context: Dict[str, Any]) -> Optional[RiskFactor]:
        behavioral = context.get('behavioral', {})
        
        risk_indicators = []
        score = 0.0
        
        # Unusual activity hours
        if behavioral.get('off_hours_ratio', 0) > 0.3:
            risk_indicators.append('unusual_hours')
            score += 0.15
        
        # Sudden activity spike
        if behavioral.get('activity_spike', 0) > 3.0:  # 3x normal
            risk_indicators.append('activity_spike')
            score += 0.25
        
        # Changed patterns
        if behavioral.get('pattern_change_score', 0) > 0.7:
            risk_indicators.append('pattern_deviation')
            score += 0.2
        
        # Dormant account reactivation
        if behavioral.get('dormant_reactivation', False):
            risk_indicators.append('dormant_reactivation')
            score += 0.3
        
        if risk_indicators:
            return RiskFactor(
                category=self.category,
                name=self.name,
                score=min(1.0, score),
                weight=self.weight,
                evidence={
                    'indicators': risk_indicators,
                    'behavioral_data': behavioral
                },
                description=f"Behavioral anomalies: {', '.join(risk_indicators)}"
            )
        return None


class ContextualScoringEngine:
    """
    FTex Contextual Scoring Engine.
    
    Combines multiple risk factors with network context
    to produce holistic risk scores.
    """
    
    def __init__(self):
        self.rules: List[ScoringRule] = []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Configure default scoring rules."""
        self.rules = [
            SanctionsRule(weight=1.0),
            PEPRule(weight=0.8),
            JurisdictionRule(weight=0.6),
            TransactionPatternRule(weight=0.7),
            NetworkContextRule(weight=0.8),
            BehavioralRule(weight=0.6),
        ]
    
    def add_rule(self, rule: ScoringRule):
        """Add a custom scoring rule."""
        self.rules.append(rule)
    
    def calculate_score(
        self,
        entity: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> RiskScore:
        """
        Calculate comprehensive risk score for an entity.
        
        Args:
            entity: Entity attributes
            context: Additional context (network, transactions, behavioral)
        
        Returns:
            RiskScore with overall score and contributing factors
        """
        context = context or {}
        factors = []
        
        # Evaluate all rules
        for rule in self.rules:
            factor = rule.evaluate(entity, context)
            if factor:
                factors.append(factor)
        
        # Calculate weighted average
        if factors:
            total_weight = sum(f.weight for f in factors)
            weighted_sum = sum(f.weighted_score for f in factors)
            overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        else:
            overall_score = 0.0
        
        # Ensure score is in valid range
        overall_score = max(0.0, min(1.0, overall_score))
        
        return RiskScore(
            entity_id=entity.get('id', 'unknown'),
            overall_score=overall_score,
            risk_level=RiskScore.calculate_level(overall_score),
            factors=factors,
            network_context=context.get('network', {})
        )
    
    def explain_score(self, risk_score: RiskScore) -> Dict[str, Any]:
        """
        Generate human-readable explanation of risk score.
        """
        explanation = {
            'entity_id': risk_score.entity_id,
            'overall_score': round(risk_score.overall_score, 3),
            'risk_level': risk_score.risk_level,
            'summary': f"Entity has {risk_score.risk_level} risk based on {len(risk_score.factors)} factors",
            'factors': []
        }
        
        # Sort factors by contribution
        sorted_factors = sorted(
            risk_score.factors,
            key=lambda f: f.weighted_score,
            reverse=True
        )
        
        for factor in sorted_factors:
            explanation['factors'].append({
                'category': factor.category.value,
                'name': factor.name,
                'description': factor.description,
                'score': round(factor.score, 3),
                'weight': factor.weight,
                'contribution': round(factor.weighted_score, 3),
                'evidence': factor.evidence
            })
        
        # Add recommendations
        recommendations = []
        for factor in sorted_factors:
            if factor.score >= 0.8:
                if factor.category == RiskCategory.SANCTIONS:
                    recommendations.append("Immediate escalation required - sanctions match")
                elif factor.category == RiskCategory.NETWORK:
                    recommendations.append("Review network connections for risk exposure")
                elif factor.category == RiskCategory.TRANSACTION_PATTERN:
                    recommendations.append("Detailed transaction analysis recommended")
        
        explanation['recommendations'] = recommendations
        
        return explanation
    
    def batch_score(
        self,
        entities: List[Dict[str, Any]],
        context_provider: Callable[[str], Dict[str, Any]] = None
    ) -> List[RiskScore]:
        """
        Score multiple entities efficiently.
        
        Args:
            entities: List of entity dictionaries
            context_provider: Function to get context for each entity
        """
        results = []
        
        for entity in entities:
            entity_id = entity.get('id')
            context = context_provider(entity_id) if context_provider else {}
            score = self.calculate_score(entity, context)
            results.append(score)
        
        return results


# Demo
def demo_contextual_scoring():
    """Demonstrate contextual scoring capabilities."""
    
    engine = ContextualScoringEngine()
    
    # Test entity with various risk factors
    entity = {
        'id': 'E001',
        'name': 'John Smith',
        'is_sanctioned': False,
        'is_pep': True,
        'pep_level': 'senior_government',
        'pep_position': 'Minister of Finance',
        'pep_country': 'SG',
        'country': 'SG'
    }
    
    # Context from network and transactions
    context = {
        'network': {
            'high_risk_connections': 3,
            'sanctioned_connections': 1,
            'clustering_coefficient': 0.65,
            'centrality_score': 0.72,
            'in_circular_flow': False,
            'propagated_risk': 0.25
        },
        'transaction_stats': {
            'total_volume': 2500000,
            'structuring_indicator': 0.3,
            'passthrough_ratio': 0.4,
            'round_amount_ratio': 0.2,
            'cross_border_ratio': 0.6,
            'cash_ratio': 0.1
        },
        'behavioral': {
            'off_hours_ratio': 0.1,
            'activity_spike': 1.5,
            'pattern_change_score': 0.3,
            'dormant_reactivation': False
        }
    }
    
    # Calculate score
    score = engine.calculate_score(entity, context)
    
    print(f"Entity: {entity['name']}")
    print(f"Overall Score: {score.overall_score:.3f}")
    print(f"Risk Level: {score.risk_level}")
    print(f"\nContributing Factors:")
    
    for factor in score.factors:
        print(f"  - {factor.name}: {factor.score:.2f} (weight: {factor.weight})")
        print(f"    {factor.description}")
    
    # Get explanation
    explanation = engine.explain_score(score)
    print(f"\nRecommendations:")
    for rec in explanation['recommendations']:
        print(f"  - {rec}")


if __name__ == "__main__":
    demo_contextual_scoring()

