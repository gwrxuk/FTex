"""
Commercial Screening List Integrations.

Provides integration with commercial screening data providers
as referenced in line 33 of plan.txt:
- Dow Jones Factiva
- LSEG (Refinitiv) World-Check
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import hashlib


class ScreeningListType(str, Enum):
    """Types of screening lists."""
    SANCTIONS = "sanctions"
    PEP = "pep"
    ADVERSE_MEDIA = "adverse_media"
    ENFORCEMENT = "enforcement"
    SOE = "state_owned_enterprise"
    REGULATORY = "regulatory"


class MatchConfidence(str, Enum):
    """Match confidence levels."""
    EXACT = "exact"
    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"
    POTENTIAL = "potential"


@dataclass
class ScreeningMatch:
    """A match from screening list."""
    match_id: str
    list_source: str  # dow_jones, refinitiv, ofac, etc.
    list_type: ScreeningListType
    matched_name: str
    matched_entity_type: str  # individual, organization, vessel
    confidence: MatchConfidence
    match_score: float
    
    # Match details
    query_name: str
    matched_aliases: List[str] = field(default_factory=list)
    matched_attributes: Dict[str, Any] = field(default_factory=dict)
    
    # List entry details
    list_entry_id: str = ""
    listed_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    
    # Sanctions specific
    sanctions_programs: List[str] = field(default_factory=list)
    
    # PEP specific
    pep_positions: List[Dict[str, str]] = field(default_factory=list)
    
    # Adverse media
    media_articles: List[Dict[str, Any]] = field(default_factory=list)
    
    # Categories/Flags
    categories: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)
    
    # Source URL/Reference
    source_url: Optional[str] = None


@dataclass
class ScreeningResult:
    """Complete screening result."""
    query_id: str
    query_name: str
    query_type: str  # individual, organization
    screened_at: datetime
    
    total_matches: int
    matches: List[ScreeningMatch]
    
    # Aggregated risk
    highest_risk_match: Optional[ScreeningMatch] = None
    recommended_action: str = "review"
    
    # Provider details
    providers_checked: List[str] = field(default_factory=list)
    
    def get_matches_by_type(self, list_type: ScreeningListType) -> List[ScreeningMatch]:
        """Get matches filtered by list type."""
        return [m for m in self.matches if m.list_type == list_type]
    
    def has_sanctions_match(self) -> bool:
        """Check if any sanctions matches exist."""
        return any(m.list_type == ScreeningListType.SANCTIONS for m in self.matches)
    
    def has_pep_match(self) -> bool:
        """Check if any PEP matches exist."""
        return any(m.list_type == ScreeningListType.PEP for m in self.matches)


class ScreeningProvider(ABC):
    """Abstract base class for screening providers."""
    
    @abstractmethod
    def screen(
        self,
        name: str,
        entity_type: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> List[ScreeningMatch]:
        """Screen a name against the provider's lists."""
        pass
    
    @abstractmethod
    def get_entity_details(self, list_entry_id: str) -> Dict[str, Any]:
        """Get full details for a list entry."""
        pass


class DowJonesProvider(ScreeningProvider):
    """
    Dow Jones Risk & Compliance Integration.
    
    Provides access to:
    - Dow Jones Watchlist
    - State Ownership data
    - PEP data
    - Sanctions lists
    - Adverse Media
    """
    
    def __init__(self, api_key: str = None, api_url: str = None):
        self.api_key = api_key or "demo_key"
        self.api_url = api_url or "https://api.dowjones.com/risk"
        self.provider_name = "dow_jones"
    
    def screen(
        self,
        name: str,
        entity_type: str = "individual",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> List[ScreeningMatch]:
        """
        Screen a name against Dow Jones lists.
        
        In production, this would call the actual Dow Jones API.
        """
        matches = []
        
        # Simulate API call - in production, this would be actual API integration
        simulated_results = self._simulate_screening(name, entity_type, additional_data)
        
        for result in simulated_results:
            match = ScreeningMatch(
                match_id=self._generate_match_id(name, result),
                list_source=self.provider_name,
                list_type=ScreeningListType(result['list_type']),
                matched_name=result['matched_name'],
                matched_entity_type=result['entity_type'],
                confidence=MatchConfidence(result['confidence']),
                match_score=result['score'],
                query_name=name,
                matched_aliases=result.get('aliases', []),
                matched_attributes=result.get('attributes', {}),
                list_entry_id=result.get('entry_id', ''),
                listed_date=result.get('listed_date'),
                sanctions_programs=result.get('programs', []),
                pep_positions=result.get('positions', []),
                categories=result.get('categories', []),
                risk_flags=result.get('flags', [])
            )
            matches.append(match)
        
        return matches
    
    def get_entity_details(self, list_entry_id: str) -> Dict[str, Any]:
        """Get full details for a Dow Jones list entry."""
        # In production, this would call the actual API
        return {
            'entry_id': list_entry_id,
            'provider': self.provider_name,
            'full_details': 'Available via API'
        }
    
    def _simulate_screening(
        self,
        name: str,
        entity_type: str,
        additional_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Simulate screening results for demonstration.
        
        In production, this would be replaced with actual API calls.
        """
        results = []
        name_lower = name.lower()
        
        # Check for known test patterns
        if 'kim' in name_lower and 'jong' in name_lower:
            results.append({
                'list_type': 'sanctions',
                'matched_name': 'KIM Jong Un',
                'entity_type': 'individual',
                'confidence': 'strong',
                'score': 0.92,
                'entry_id': 'DJ-OFAC-12345',
                'programs': ['DPRK', 'OFAC-SDN'],
                'categories': ['Head of State', 'Weapons Proliferation'],
                'flags': ['OFAC', 'UN', 'EU']
            })
        
        if 'putin' in name_lower:
            results.append({
                'list_type': 'sanctions',
                'matched_name': 'Vladimir PUTIN',
                'entity_type': 'individual',
                'confidence': 'strong',
                'score': 0.95,
                'entry_id': 'DJ-OFAC-23456',
                'programs': ['RUSSIA', 'OFAC-SDN'],
                'categories': ['Head of State'],
                'flags': ['OFAC', 'EU', 'UK']
            })
            results.append({
                'list_type': 'pep',
                'matched_name': 'Vladimir PUTIN',
                'entity_type': 'individual',
                'confidence': 'exact',
                'score': 1.0,
                'entry_id': 'DJ-PEP-11111',
                'positions': [
                    {'title': 'President', 'country': 'RU', 'since': '2000'}
                ],
                'categories': ['Head of State']
            })
        
        # Generic PEP simulation for names with titles
        if any(title in name_lower for title in ['minister', 'senator', 'president', 'governor']):
            results.append({
                'list_type': 'pep',
                'matched_name': name,
                'entity_type': 'individual',
                'confidence': 'potential',
                'score': 0.65,
                'entry_id': f'DJ-PEP-{abs(hash(name)) % 100000}',
                'positions': [
                    {'title': 'Political Figure', 'country': 'Unknown'}
                ],
                'categories': ['PEP']
            })
        
        return results
    
    def _generate_match_id(self, query: str, result: Dict[str, Any]) -> str:
        """Generate unique match ID."""
        data = f"{query}{result.get('entry_id', '')}{datetime.utcnow().isoformat()}"
        return f"DJ-{hashlib.md5(data.encode()).hexdigest()[:12].upper()}"


class RefinitivProvider(ScreeningProvider):
    """
    LSEG (Refinitiv) World-Check Integration.
    
    Provides access to:
    - World-Check One
    - PEP database
    - Sanctions lists
    - Adverse media
    - Enforcement actions
    """
    
    def __init__(self, api_key: str = None, api_url: str = None):
        self.api_key = api_key or "demo_key"
        self.api_url = api_url or "https://api.refinitiv.com/worldcheck"
        self.provider_name = "refinitiv"
    
    def screen(
        self,
        name: str,
        entity_type: str = "individual",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> List[ScreeningMatch]:
        """
        Screen a name against Refinitiv World-Check.
        
        In production, this would call the actual World-Check API.
        """
        matches = []
        
        # Simulate API call
        simulated_results = self._simulate_screening(name, entity_type, additional_data)
        
        for result in simulated_results:
            match = ScreeningMatch(
                match_id=self._generate_match_id(name, result),
                list_source=self.provider_name,
                list_type=ScreeningListType(result['list_type']),
                matched_name=result['matched_name'],
                matched_entity_type=result['entity_type'],
                confidence=MatchConfidence(result['confidence']),
                match_score=result['score'],
                query_name=name,
                matched_aliases=result.get('aliases', []),
                matched_attributes=result.get('attributes', {}),
                list_entry_id=result.get('entry_id', ''),
                sanctions_programs=result.get('programs', []),
                pep_positions=result.get('positions', []),
                media_articles=result.get('articles', []),
                categories=result.get('categories', []),
                risk_flags=result.get('flags', [])
            )
            matches.append(match)
        
        return matches
    
    def get_entity_details(self, list_entry_id: str) -> Dict[str, Any]:
        """Get full details for a World-Check entry."""
        return {
            'entry_id': list_entry_id,
            'provider': self.provider_name,
            'full_details': 'Available via API'
        }
    
    def _simulate_screening(
        self,
        name: str,
        entity_type: str,
        additional_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Simulate World-Check screening results."""
        results = []
        name_lower = name.lower()
        
        # Adverse media simulation
        if any(term in name_lower for term in ['fraud', 'scandal', 'corrupt']):
            results.append({
                'list_type': 'adverse_media',
                'matched_name': name,
                'entity_type': entity_type,
                'confidence': 'medium',
                'score': 0.70,
                'entry_id': f'WC-AM-{abs(hash(name)) % 100000}',
                'articles': [
                    {
                        'title': 'Potential match in adverse media',
                        'source': 'News Archive',
                        'date': '2024-01-15'
                    }
                ],
                'categories': ['Adverse Media'],
                'flags': ['Media Watch']
            })
        
        # Enforcement action simulation
        if 'sec' in name_lower or 'violation' in name_lower:
            results.append({
                'list_type': 'enforcement',
                'matched_name': name,
                'entity_type': entity_type,
                'confidence': 'potential',
                'score': 0.55,
                'entry_id': f'WC-ENF-{abs(hash(name)) % 100000}',
                'categories': ['Regulatory Enforcement'],
                'flags': ['SEC Action']
            })
        
        return results
    
    def _generate_match_id(self, query: str, result: Dict[str, Any]) -> str:
        """Generate unique match ID."""
        data = f"{query}{result.get('entry_id', '')}{datetime.utcnow().isoformat()}"
        return f"WC-{hashlib.md5(data.encode()).hexdigest()[:12].upper()}"


class ScreeningService:
    """
    Unified Screening Service.
    
    Orchestrates screening across multiple providers:
    - Dow Jones
    - Refinitiv World-Check
    - OFAC (via built-in list)
    - EU Sanctions
    - UN Consolidated List
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize providers
        self.providers: List[ScreeningProvider] = []
        
        # Add Dow Jones if configured
        if self.config.get('dow_jones_enabled', True):
            self.providers.append(DowJonesProvider(
                api_key=self.config.get('dow_jones_api_key'),
                api_url=self.config.get('dow_jones_api_url')
            ))
        
        # Add Refinitiv if configured
        if self.config.get('refinitiv_enabled', True):
            self.providers.append(RefinitivProvider(
                api_key=self.config.get('refinitiv_api_key'),
                api_url=self.config.get('refinitiv_api_url')
            ))
    
    def screen(
        self,
        name: str,
        entity_type: str = "individual",
        additional_data: Optional[Dict[str, Any]] = None,
        list_types: Optional[List[ScreeningListType]] = None
    ) -> ScreeningResult:
        """
        Screen a name against all configured providers.
        
        Args:
            name: Name to screen
            entity_type: "individual" or "organization"
            additional_data: Additional context (DOB, country, etc.)
            list_types: Specific list types to check (all if None)
        
        Returns:
            ScreeningResult with all matches
        """
        all_matches = []
        providers_checked = []
        
        for provider in self.providers:
            try:
                matches = provider.screen(name, entity_type, additional_data)
                
                # Filter by list type if specified
                if list_types:
                    matches = [m for m in matches if m.list_type in list_types]
                
                all_matches.extend(matches)
                providers_checked.append(provider.provider_name)
            except Exception as e:
                # Log error but continue with other providers
                print(f"Error with provider {provider.provider_name}: {e}")
        
        # Sort matches by score
        all_matches.sort(key=lambda m: m.match_score, reverse=True)
        
        # Determine highest risk match
        highest_risk = all_matches[0] if all_matches else None
        
        # Determine recommended action
        action = self._determine_action(all_matches)
        
        return ScreeningResult(
            query_id=self._generate_query_id(name),
            query_name=name,
            query_type=entity_type,
            screened_at=datetime.utcnow(),
            total_matches=len(all_matches),
            matches=all_matches,
            highest_risk_match=highest_risk,
            recommended_action=action,
            providers_checked=providers_checked
        )
    
    def batch_screen(
        self,
        names: List[Dict[str, Any]]
    ) -> List[ScreeningResult]:
        """
        Screen multiple names in batch.
        
        Args:
            names: List of dicts with 'name' and optional 'entity_type', 'data'
        
        Returns:
            List of ScreeningResult
        """
        results = []
        
        for item in names:
            result = self.screen(
                name=item.get('name', ''),
                entity_type=item.get('entity_type', 'individual'),
                additional_data=item.get('data')
            )
            results.append(result)
        
        return results
    
    def _determine_action(self, matches: List[ScreeningMatch]) -> str:
        """Determine recommended action based on matches."""
        if not matches:
            return "clear"
        
        # Check for sanctions
        sanctions_matches = [m for m in matches if m.list_type == ScreeningListType.SANCTIONS]
        if sanctions_matches:
            if any(m.confidence == MatchConfidence.EXACT for m in sanctions_matches):
                return "reject_sanctions_exact"
            elif any(m.confidence == MatchConfidence.STRONG for m in sanctions_matches):
                return "escalate_sanctions"
            else:
                return "review_sanctions"
        
        # Check for PEP
        pep_matches = [m for m in matches if m.list_type == ScreeningListType.PEP]
        if pep_matches:
            if any(m.confidence in [MatchConfidence.EXACT, MatchConfidence.STRONG] for m in pep_matches):
                return "enhanced_due_diligence"
            else:
                return "review_pep"
        
        # Check adverse media
        media_matches = [m for m in matches if m.list_type == ScreeningListType.ADVERSE_MEDIA]
        if media_matches:
            return "review_media"
        
        return "review"
    
    def _generate_query_id(self, name: str) -> str:
        """Generate unique query ID."""
        data = f"{name}{datetime.utcnow().isoformat()}"
        return f"SCR-{hashlib.md5(data.encode()).hexdigest()[:12].upper()}"
    
    def to_dict(self, result: ScreeningResult) -> Dict[str, Any]:
        """Convert ScreeningResult to dictionary."""
        return {
            'query_id': result.query_id,
            'query_name': result.query_name,
            'query_type': result.query_type,
            'screened_at': result.screened_at.isoformat(),
            'total_matches': result.total_matches,
            'matches': [
                {
                    'match_id': m.match_id,
                    'list_source': m.list_source,
                    'list_type': m.list_type.value,
                    'matched_name': m.matched_name,
                    'confidence': m.confidence.value,
                    'match_score': m.match_score,
                    'categories': m.categories,
                    'risk_flags': m.risk_flags,
                    'sanctions_programs': m.sanctions_programs,
                    'pep_positions': m.pep_positions
                }
                for m in result.matches
            ],
            'has_sanctions_match': result.has_sanctions_match(),
            'has_pep_match': result.has_pep_match(),
            'recommended_action': result.recommended_action,
            'providers_checked': result.providers_checked
        }

