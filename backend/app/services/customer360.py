"""
Customer 360 / MDM (Master Data Management) Service.

Provides unified customer view by aggregating data from multiple sources
as referenced in line 36 of plan.txt: "Financial Crime, MDM, Customer 360, Risk".
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class DataDomain(str, Enum):
    """Data domains for MDM."""
    CUSTOMER = "customer"
    PRODUCT = "product"
    ACCOUNT = "account"
    TRANSACTION = "transaction"
    PARTY = "party"
    LOCATION = "location"
    ORGANIZATION = "organization"


class DataQualityDimension(str, Enum):
    """Data quality dimensions."""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    UNIQUENESS = "uniqueness"
    VALIDITY = "validity"


@dataclass
class DataQualityScore:
    """Data quality assessment for an entity."""
    entity_id: str
    domain: DataDomain
    completeness: float  # % of required fields populated
    accuracy: float  # % of fields matching reference data
    consistency: float  # Cross-system consistency
    timeliness: float  # How recent the data is
    uniqueness: float  # No duplicates
    validity: float  # Conforms to business rules
    overall_score: float = 0.0
    issues: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        # Calculate weighted overall score
        self.overall_score = (
            self.completeness * 0.2 +
            self.accuracy * 0.25 +
            self.consistency * 0.2 +
            self.timeliness * 0.1 +
            self.uniqueness * 0.15 +
            self.validity * 0.1
        )


@dataclass
class Customer360View:
    """
    Unified 360-degree view of a customer.
    
    Aggregates data from all source systems to provide
    a single, comprehensive customer profile.
    """
    customer_id: str
    golden_record: Dict[str, Any]  # Master/canonical data
    
    # Identity
    identities: List[Dict[str, Any]] = field(default_factory=list)
    documents: List[Dict[str, Any]] = field(default_factory=list)
    
    # Demographics
    demographics: Dict[str, Any] = field(default_factory=dict)
    
    # Contact
    addresses: List[Dict[str, Any]] = field(default_factory=list)
    phones: List[Dict[str, Any]] = field(default_factory=list)
    emails: List[Dict[str, Any]] = field(default_factory=list)
    
    # Relationships
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    household: Optional[Dict[str, Any]] = None
    
    # Products & Accounts
    accounts: List[Dict[str, Any]] = field(default_factory=list)
    products: List[Dict[str, Any]] = field(default_factory=list)
    
    # Financial Summary
    financial_summary: Dict[str, Any] = field(default_factory=dict)
    
    # Risk Profile
    risk_profile: Dict[str, Any] = field(default_factory=dict)
    
    # Interactions
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Compliance
    kyc_status: Dict[str, Any] = field(default_factory=dict)
    sanctions_status: Dict[str, Any] = field(default_factory=dict)
    pep_status: Dict[str, Any] = field(default_factory=dict)
    
    # Data Quality
    data_quality: Optional[DataQualityScore] = None
    
    # Source Tracking
    source_systems: List[str] = field(default_factory=list)
    last_updated: Optional[datetime] = None


class Customer360Service:
    """
    Service for building and managing Customer 360 views.
    """
    
    # Required fields for completeness scoring
    REQUIRED_FIELDS = {
        "name": 1.0,
        "date_of_birth": 0.8,
        "nationality": 0.6,
        "address": 0.7,
        "phone": 0.5,
        "email": 0.5,
        "identification": 0.9,
        "occupation": 0.4,
        "employer": 0.3,
    }
    
    # Source system priority for survivorship
    SOURCE_PRIORITY = {
        "kyc_system": 1,
        "core_banking": 2,
        "crm": 3,
        "trade_system": 4,
        "external_data": 5
    }
    
    def __init__(self):
        self.cache = {}
    
    def build_customer_360(
        self,
        customer_id: str,
        source_records: List[Dict[str, Any]]
    ) -> Customer360View:
        """
        Build a Customer 360 view from multiple source records.
        
        Applies MDM survivorship rules to create golden record.
        """
        # Create golden record using survivorship rules
        golden_record = self._apply_survivorship_rules(source_records)
        
        # Aggregate contact information
        addresses = self._aggregate_addresses(source_records)
        phones = self._aggregate_phones(source_records)
        emails = self._aggregate_emails(source_records)
        
        # Build identity composite
        identities = self._aggregate_identities(source_records)
        documents = self._aggregate_documents(source_records)
        
        # Aggregate financial data
        accounts = self._aggregate_accounts(source_records)
        products = self._aggregate_products(source_records)
        financial_summary = self._calculate_financial_summary(accounts)
        
        # Build risk profile
        risk_profile = self._build_risk_profile(source_records)
        
        # KYC/Compliance status
        kyc_status = self._get_kyc_status(source_records)
        sanctions_status = self._get_sanctions_status(source_records)
        pep_status = self._get_pep_status(source_records)
        
        # Assess data quality
        data_quality = self._assess_data_quality(customer_id, golden_record, source_records)
        
        # Get source systems
        source_systems = list(set(
            r.get('source_system', 'unknown') for r in source_records
        ))
        
        return Customer360View(
            customer_id=customer_id,
            golden_record=golden_record,
            identities=identities,
            documents=documents,
            demographics=golden_record.get('demographics', {}),
            addresses=addresses,
            phones=phones,
            emails=emails,
            relationships=self._get_relationships(source_records),
            accounts=accounts,
            products=products,
            financial_summary=financial_summary,
            risk_profile=risk_profile,
            kyc_status=kyc_status,
            sanctions_status=sanctions_status,
            pep_status=pep_status,
            data_quality=data_quality,
            source_systems=source_systems,
            last_updated=datetime.utcnow()
        )
    
    def _apply_survivorship_rules(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply survivorship rules to create golden record.
        
        Rules:
        1. Most recent value wins (for temporal data)
        2. Source system priority (for conflicting values)
        3. Most complete record preference
        4. Specific attribute rules (e.g., highest confidence)
        """
        golden = {}
        
        # Sort records by source priority
        sorted_records = sorted(
            records,
            key=lambda r: self.SOURCE_PRIORITY.get(r.get('source_system', 'unknown'), 99)
        )
        
        # Collect all unique attribute keys
        all_keys = set()
        for record in records:
            all_keys.update(record.keys())
        
        for key in all_keys:
            if key in ['source_system', 'record_id', 'created_at', 'updated_at']:
                continue
            
            # Get all values for this attribute
            values = []
            for record in sorted_records:
                if key in record and record[key] is not None:
                    values.append({
                        'value': record[key],
                        'source': record.get('source_system'),
                        'updated_at': record.get('updated_at'),
                        'confidence': record.get(f'{key}_confidence', 1.0)
                    })
            
            if not values:
                continue
            
            # Apply survivorship rules
            if key in ['name', 'date_of_birth', 'nationality', 'gender']:
                # Source priority for identity attributes
                golden[key] = values[0]['value']
            elif key in ['address', 'phone', 'email']:
                # Most recent for contact attributes
                sorted_by_date = sorted(
                    values,
                    key=lambda v: v.get('updated_at') or datetime.min,
                    reverse=True
                )
                golden[key] = sorted_by_date[0]['value']
            else:
                # Highest confidence or first by priority
                sorted_by_conf = sorted(
                    values,
                    key=lambda v: v.get('confidence', 0),
                    reverse=True
                )
                golden[key] = sorted_by_conf[0]['value']
        
        return golden
    
    def _aggregate_addresses(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate all addresses with deduplication."""
        addresses = []
        seen = set()
        
        for record in records:
            for addr in record.get('addresses', []):
                # Create key for deduplication
                key = f"{addr.get('line1', '')}-{addr.get('postal_code', '')}"
                if key not in seen:
                    seen.add(key)
                    addresses.append({
                        **addr,
                        'source': record.get('source_system')
                    })
        
        return addresses
    
    def _aggregate_phones(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate all phone numbers with deduplication."""
        phones = []
        seen = set()
        
        for record in records:
            for phone in record.get('phones', []):
                number = phone.get('number', '')
                if number and number not in seen:
                    seen.add(number)
                    phones.append({
                        **phone,
                        'source': record.get('source_system')
                    })
        
        return phones
    
    def _aggregate_emails(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate all email addresses with deduplication."""
        emails = []
        seen = set()
        
        for record in records:
            for email in record.get('emails', []):
                addr = email.get('address', '').lower()
                if addr and addr not in seen:
                    seen.add(addr)
                    emails.append({
                        **email,
                        'source': record.get('source_system')
                    })
        
        return emails
    
    def _aggregate_identities(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate identity information."""
        identities = []
        
        for record in records:
            for identity in record.get('identities', []):
                identities.append({
                    **identity,
                    'source': record.get('source_system')
                })
        
        return identities
    
    def _aggregate_documents(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate identification documents."""
        documents = []
        seen = set()
        
        for record in records:
            for doc in record.get('documents', []):
                key = f"{doc.get('type')}-{doc.get('number')}"
                if key not in seen:
                    seen.add(key)
                    documents.append({
                        **doc,
                        'source': record.get('source_system')
                    })
        
        return documents
    
    def _aggregate_accounts(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate all accounts."""
        accounts = []
        seen = set()
        
        for record in records:
            for account in record.get('accounts', []):
                acc_id = account.get('account_id')
                if acc_id and acc_id not in seen:
                    seen.add(acc_id)
                    accounts.append(account)
        
        return accounts
    
    def _aggregate_products(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aggregate all products held."""
        products = []
        
        for record in records:
            for product in record.get('products', []):
                products.append(product)
        
        return products
    
    def _calculate_financial_summary(self, accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate financial summary from accounts."""
        total_balance = sum(a.get('balance', 0) for a in accounts)
        total_credit_limit = sum(a.get('credit_limit', 0) for a in accounts)
        
        return {
            'total_accounts': len(accounts),
            'total_balance': total_balance,
            'total_credit_limit': total_credit_limit,
            'account_types': list(set(a.get('account_type') for a in accounts if a.get('account_type'))),
            'currencies': list(set(a.get('currency') for a in accounts if a.get('currency')))
        }
    
    def _build_risk_profile(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build aggregated risk profile."""
        risk_scores = [r.get('risk_score', 0) for r in records if r.get('risk_score')]
        
        return {
            'current_risk_score': max(risk_scores) if risk_scores else 0,
            'average_risk_score': sum(risk_scores) / len(risk_scores) if risk_scores else 0,
            'risk_level': self._calculate_risk_level(max(risk_scores) if risk_scores else 0),
            'risk_factors': self._aggregate_risk_factors(records)
        }
    
    def _calculate_risk_level(self, score: float) -> str:
        """Convert risk score to level."""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _aggregate_risk_factors(self, records: List[Dict[str, Any]]) -> List[str]:
        """Aggregate all risk factors."""
        factors = set()
        for record in records:
            for factor in record.get('risk_factors', []):
                factors.add(factor)
        return list(factors)
    
    def _get_relationships(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get all relationships."""
        relationships = []
        for record in records:
            for rel in record.get('relationships', []):
                relationships.append(rel)
        return relationships
    
    def _get_kyc_status(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get KYC status - most recent wins."""
        kyc_records = [r for r in records if 'kyc_status' in r]
        if not kyc_records:
            return {'status': 'unknown'}
        
        # Sort by date, most recent first
        sorted_kyc = sorted(
            kyc_records,
            key=lambda r: r.get('kyc_date') or datetime.min,
            reverse=True
        )
        
        return sorted_kyc[0].get('kyc_status', {})
    
    def _get_sanctions_status(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get sanctions screening status."""
        for record in records:
            if record.get('is_sanctioned'):
                return {
                    'is_sanctioned': True,
                    'matched_lists': record.get('matched_sanctions_lists', []),
                    'last_screened': record.get('sanctions_screening_date')
                }
        
        return {'is_sanctioned': False}
    
    def _get_pep_status(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get PEP status."""
        for record in records:
            if record.get('is_pep'):
                return {
                    'is_pep': True,
                    'pep_level': record.get('pep_level'),
                    'pep_position': record.get('pep_position'),
                    'pep_country': record.get('pep_country')
                }
        
        return {'is_pep': False}
    
    def _assess_data_quality(
        self,
        entity_id: str,
        golden_record: Dict[str, Any],
        source_records: List[Dict[str, Any]]
    ) -> DataQualityScore:
        """
        Assess data quality for the customer record.
        """
        issues = []
        
        # Completeness - check required fields
        present_weight = 0.0
        total_weight = sum(self.REQUIRED_FIELDS.values())
        
        for field, weight in self.REQUIRED_FIELDS.items():
            if golden_record.get(field):
                present_weight += weight
            else:
                issues.append({
                    'dimension': 'completeness',
                    'field': field,
                    'issue': f'Missing required field: {field}'
                })
        
        completeness = present_weight / total_weight if total_weight > 0 else 0
        
        # Accuracy - check format validity
        accuracy_checks = 0
        accuracy_passed = 0
        
        if golden_record.get('email'):
            accuracy_checks += 1
            if '@' in golden_record['email']:
                accuracy_passed += 1
            else:
                issues.append({
                    'dimension': 'accuracy',
                    'field': 'email',
                    'issue': 'Invalid email format'
                })
        
        if golden_record.get('date_of_birth'):
            accuracy_checks += 1
            try:
                dob = golden_record['date_of_birth']
                if isinstance(dob, str):
                    datetime.fromisoformat(dob.replace('Z', '+00:00'))
                accuracy_passed += 1
            except:
                issues.append({
                    'dimension': 'accuracy',
                    'field': 'date_of_birth',
                    'issue': 'Invalid date format'
                })
        
        accuracy = accuracy_passed / accuracy_checks if accuracy_checks > 0 else 1.0
        
        # Consistency - check cross-system agreement
        consistency_score = self._check_consistency(source_records)
        
        # Timeliness - check data freshness
        timeliness = self._check_timeliness(source_records)
        
        # Uniqueness - already handled by entity resolution
        uniqueness = 1.0 if len(source_records) <= 1 else 0.8
        
        # Validity - check against business rules
        validity = 1.0  # Placeholder
        
        return DataQualityScore(
            entity_id=entity_id,
            domain=DataDomain.CUSTOMER,
            completeness=completeness,
            accuracy=accuracy,
            consistency=consistency_score,
            timeliness=timeliness,
            uniqueness=uniqueness,
            validity=validity,
            issues=issues
        )
    
    def _check_consistency(self, records: List[Dict[str, Any]]) -> float:
        """Check consistency across source systems."""
        if len(records) <= 1:
            return 1.0
        
        # Check key fields for consistency
        key_fields = ['name', 'date_of_birth', 'nationality']
        consistent_count = 0
        total_comparisons = 0
        
        for field in key_fields:
            values = [r.get(field) for r in records if r.get(field)]
            if len(values) > 1:
                total_comparisons += 1
                if len(set(values)) == 1:
                    consistent_count += 1
        
        return consistent_count / total_comparisons if total_comparisons > 0 else 1.0
    
    def _check_timeliness(self, records: List[Dict[str, Any]]) -> float:
        """Check data timeliness."""
        now = datetime.utcnow()
        max_age_days = 365  # Consider data older than 1 year as stale
        
        ages = []
        for record in records:
            updated = record.get('updated_at')
            if updated:
                if isinstance(updated, str):
                    updated = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                age_days = (now - updated).days
                ages.append(age_days)
        
        if not ages:
            return 0.5  # Unknown timeliness
        
        avg_age = sum(ages) / len(ages)
        timeliness = max(0, 1 - (avg_age / max_age_days))
        
        return timeliness
    
    def get_customer_timeline(
        self,
        customer_360: Customer360View,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get customer activity timeline.
        """
        timeline = []
        
        # Add interactions
        for interaction in customer_360.interactions:
            timeline.append({
                'type': 'interaction',
                'timestamp': interaction.get('timestamp'),
                'description': interaction.get('description'),
                'channel': interaction.get('channel')
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.get('timestamp') or '', reverse=True)
        
        return timeline
    
    def to_dict(self, customer_360: Customer360View) -> Dict[str, Any]:
        """Convert Customer360View to dictionary."""
        return {
            'customer_id': customer_360.customer_id,
            'golden_record': customer_360.golden_record,
            'identities': customer_360.identities,
            'documents': customer_360.documents,
            'demographics': customer_360.demographics,
            'contact': {
                'addresses': customer_360.addresses,
                'phones': customer_360.phones,
                'emails': customer_360.emails
            },
            'relationships': customer_360.relationships,
            'household': customer_360.household,
            'financial': {
                'accounts': customer_360.accounts,
                'products': customer_360.products,
                'summary': customer_360.financial_summary
            },
            'risk_profile': customer_360.risk_profile,
            'compliance': {
                'kyc': customer_360.kyc_status,
                'sanctions': customer_360.sanctions_status,
                'pep': customer_360.pep_status
            },
            'data_quality': {
                'overall_score': customer_360.data_quality.overall_score if customer_360.data_quality else None,
                'completeness': customer_360.data_quality.completeness if customer_360.data_quality else None,
                'accuracy': customer_360.data_quality.accuracy if customer_360.data_quality else None,
                'issues_count': len(customer_360.data_quality.issues) if customer_360.data_quality else 0
            } if customer_360.data_quality else None,
            'source_systems': customer_360.source_systems,
            'last_updated': customer_360.last_updated.isoformat() if customer_360.last_updated else None
        }

