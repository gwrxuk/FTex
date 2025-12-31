"""
FTex Entity Resolution Engine

Core technology for resolving entities across multiple data sources using:
- Blocking strategies for efficient candidate generation
- Fuzzy matching with multiple similarity algorithms
- Machine learning-based scoring
- Graph-based clustering for entity grouping
"""

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
from collections import defaultdict


class MatchType(str, Enum):
    """Types of matching algorithms."""
    EXACT = "exact"
    FUZZY = "fuzzy"
    PHONETIC = "phonetic"
    SEMANTIC = "semantic"


@dataclass
class EntityRecord:
    """Represents a record from a source system."""
    id: str
    source_system: str
    entity_type: str
    attributes: Dict[str, Any]
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolvedEntity:
    """A resolved entity combining multiple source records."""
    resolved_id: str
    canonical_name: str
    entity_type: str
    source_records: List[EntityRecord]
    confidence_score: float
    attributes: Dict[str, Any]
    match_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class MatchCandidate:
    """A candidate pair for matching."""
    record_a: EntityRecord
    record_b: EntityRecord
    blocking_key: str
    similarity_scores: Dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0


class BlockingStrategy:
    """
    Blocking strategies to reduce comparison space.
    
    FTex uses sophisticated blocking to handle billions of records
    by only comparing records within the same "block".
    """
    
    @staticmethod
    def soundex(name: str) -> str:
        """Generate Soundex code for phonetic blocking."""
        if not name:
            return "0000"
        
        name = name.upper()
        # Keep first letter
        result = name[0]
        
        # Soundex mapping
        mapping = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5',
            'R': '6'
        }
        
        prev_code = mapping.get(name[0], '0')
        for char in name[1:]:
            code = mapping.get(char, '0')
            if code != '0' and code != prev_code:
                result += code
                if len(result) == 4:
                    break
            prev_code = code
        
        return (result + "0000")[:4]
    
    @staticmethod
    def metaphone(name: str) -> str:
        """Simplified Metaphone for phonetic blocking."""
        if not name:
            return ""
        
        name = name.upper()
        # Basic transformations
        name = re.sub(r'[^A-Z]', '', name)
        
        # Common phonetic replacements
        replacements = [
            (r'^KN', 'N'), (r'^GN', 'N'), (r'^PN', 'N'),
            (r'^AE', 'E'), (r'^WR', 'R'), (r'^WH', 'W'),
            (r'MB$', 'M'), (r'GH', ''), (r'PH', 'F'),
            (r'CK', 'K'), (r'SH', 'X'), (r'TH', '0'),
            (r'CH', 'X'), (r'SCH', 'SK'), (r'DG', 'J'),
        ]
        
        for pattern, replacement in replacements:
            name = re.sub(pattern, replacement, name)
        
        return name[:6]
    
    @staticmethod
    def ngram_blocking(name: str, n: int = 3) -> List[str]:
        """Generate n-gram blocking keys."""
        if not name or len(name) < n:
            return [name.lower()] if name else []
        
        name = name.lower().replace(" ", "")
        return [name[i:i+n] for i in range(len(name) - n + 1)]
    
    @staticmethod
    def first_letter_year(name: str, year: Optional[int] = None) -> str:
        """Composite blocking key: first letter + year."""
        first = name[0].upper() if name else "X"
        year_str = str(year) if year else "0000"
        return f"{first}_{year_str}"
    
    @staticmethod
    def location_blocking(country: str, city: str = None) -> str:
        """Geographic blocking key."""
        country_code = (country or "XX").upper()[:2]
        city_code = (city or "XX").upper()[:3]
        return f"{country_code}_{city_code}"


class SimilarityScorer:
    """
    Similarity scoring algorithms for entity matching.
    
    Implements multiple similarity measures used in FTex's
    entity resolution pipeline.
    """
    
    @staticmethod
    def levenshtein_distance(s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance."""
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return len(s1)
        
        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        
        return prev_row[-1]
    
    @staticmethod
    def levenshtein_similarity(s1: str, s2: str) -> float:
        """Normalized Levenshtein similarity (0-1)."""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        distance = SimilarityScorer.levenshtein_distance(s1.lower(), s2.lower())
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len)
    
    @staticmethod
    def jaro_similarity(s1: str, s2: str) -> float:
        """Jaro similarity score."""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        s1, s2 = s1.lower(), s2.lower()
        
        match_distance = max(len(s1), len(s2)) // 2 - 1
        if match_distance < 0:
            match_distance = 0
        
        s1_matches = [False] * len(s1)
        s2_matches = [False] * len(s2)
        
        matches = 0
        transpositions = 0
        
        for i, c1 in enumerate(s1):
            start = max(0, i - match_distance)
            end = min(i + match_distance + 1, len(s2))
            
            for j in range(start, end):
                if s2_matches[j] or c1 != s2[j]:
                    continue
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break
        
        if matches == 0:
            return 0.0
        
        k = 0
        for i, c1 in enumerate(s1):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if c1 != s2[k]:
                transpositions += 1
            k += 1
        
        jaro = (matches / len(s1) + matches / len(s2) + 
                (matches - transpositions / 2) / matches) / 3
        
        return jaro
    
    @staticmethod
    def jaro_winkler_similarity(s1: str, s2: str, p: float = 0.1) -> float:
        """Jaro-Winkler similarity (gives higher scores to strings with common prefix)."""
        jaro = SimilarityScorer.jaro_similarity(s1, s2)
        
        # Find common prefix length (max 4)
        prefix_len = 0
        s1_lower, s2_lower = s1.lower(), s2.lower()
        for i in range(min(len(s1), len(s2), 4)):
            if s1_lower[i] == s2_lower[i]:
                prefix_len += 1
            else:
                break
        
        return jaro + prefix_len * p * (1 - jaro)
    
    @staticmethod
    def jaccard_similarity(s1: str, s2: str, ngram: int = 2) -> float:
        """Jaccard similarity using character n-grams."""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        def get_ngrams(s: str) -> set:
            s = s.lower().replace(" ", "")
            if len(s) < ngram:
                return {s}
            return {s[i:i+ngram] for i in range(len(s) - ngram + 1)}
        
        set1 = get_ngrams(s1)
        set2 = get_ngrams(s2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def token_based_similarity(s1: str, s2: str) -> float:
        """Token-based similarity (good for reordered names)."""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
        
        tokens1 = set(s1.lower().split())
        tokens2 = set(s2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        return len(intersection) / len(union)
    
    @staticmethod
    def phonetic_similarity(s1: str, s2: str) -> float:
        """Phonetic similarity using Soundex."""
        soundex1 = BlockingStrategy.soundex(s1)
        soundex2 = BlockingStrategy.soundex(s2)
        
        if soundex1 == soundex2:
            return 1.0
        
        # Partial match scoring
        matches = sum(c1 == c2 for c1, c2 in zip(soundex1, soundex2))
        return matches / 4.0
    
    @staticmethod
    def composite_name_score(name1: str, name2: str) -> float:
        """
        Composite scoring for names using multiple algorithms.
        Weighted combination of different similarity measures.
        """
        scores = {
            'jaro_winkler': SimilarityScorer.jaro_winkler_similarity(name1, name2),
            'levenshtein': SimilarityScorer.levenshtein_similarity(name1, name2),
            'jaccard': SimilarityScorer.jaccard_similarity(name1, name2),
            'token': SimilarityScorer.token_based_similarity(name1, name2),
            'phonetic': SimilarityScorer.phonetic_similarity(name1, name2),
        }
        
        # Weighted average (FTex typically uses ML to learn these weights)
        weights = {
            'jaro_winkler': 0.30,
            'levenshtein': 0.25,
            'jaccard': 0.15,
            'token': 0.20,
            'phonetic': 0.10,
        }
        
        weighted_score = sum(scores[k] * weights[k] for k in scores)
        return weighted_score


class EntityResolutionEngine:
    """
    FTex Entity Resolution Engine.
    
    Implements the core entity resolution pipeline:
    1. Data Standardization
    2. Blocking (candidate generation)
    3. Pairwise Comparison
    4. Scoring & Classification
    5. Clustering (connected components)
    6. Canonical Record Generation
    """
    
    def __init__(
        self,
        match_threshold: float = 0.75,
        blocking_strategies: List[str] = None
    ):
        self.match_threshold = match_threshold
        self.blocking_strategies = blocking_strategies or ['soundex', 'ngram']
        self.scorer = SimilarityScorer()
        self.blocker = BlockingStrategy()
    
    def standardize_record(self, record: EntityRecord) -> EntityRecord:
        """
        Standardize a record for matching.
        Applies normalization rules to improve match quality.
        """
        attrs = record.attributes.copy()
        
        # Name standardization
        if 'name' in attrs:
            name = attrs['name']
            # Remove titles
            name = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof|Jr|Sr|III|II|IV)\b\.?', '', name, flags=re.IGNORECASE)
            # Remove special characters
            name = re.sub(r'[^\w\s]', '', name)
            # Normalize whitespace
            name = ' '.join(name.split())
            attrs['name_standardized'] = name.strip()
        
        # Date standardization
        if 'date_of_birth' in attrs:
            dob = attrs['date_of_birth']
            # Try to parse various date formats
            # (simplified - real implementation would use dateutil)
            attrs['dob_standardized'] = str(dob)
        
        # Address standardization
        if 'address' in attrs:
            addr = attrs['address']
            # Common abbreviations
            addr = re.sub(r'\bStreet\b', 'St', addr, flags=re.IGNORECASE)
            addr = re.sub(r'\bRoad\b', 'Rd', addr, flags=re.IGNORECASE)
            addr = re.sub(r'\bAvenue\b', 'Ave', addr, flags=re.IGNORECASE)
            attrs['address_standardized'] = addr
        
        return EntityRecord(
            id=record.id,
            source_system=record.source_system,
            entity_type=record.entity_type,
            attributes=attrs,
            raw_data=record.raw_data
        )
    
    def generate_blocking_keys(self, record: EntityRecord) -> List[str]:
        """Generate blocking keys for a record using multiple strategies."""
        keys = []
        name = record.attributes.get('name_standardized') or record.attributes.get('name', '')
        
        if 'soundex' in self.blocking_strategies:
            keys.append(f"soundex_{self.blocker.soundex(name)}")
        
        if 'metaphone' in self.blocking_strategies:
            keys.append(f"metaphone_{self.blocker.metaphone(name)}")
        
        if 'ngram' in self.blocking_strategies:
            ngrams = self.blocker.ngram_blocking(name)
            keys.extend([f"ngram_{ng}" for ng in ngrams[:3]])  # Top 3 n-grams
        
        if 'first_letter' in self.blocking_strategies:
            year = record.attributes.get('year_of_birth')
            keys.append(f"fl_{self.blocker.first_letter_year(name, year)}")
        
        return keys
    
    def score_candidate_pair(
        self, 
        record_a: EntityRecord, 
        record_b: EntityRecord
    ) -> MatchCandidate:
        """
        Score a candidate pair using multiple attributes.
        """
        scores = {}
        
        # Name matching
        name_a = record_a.attributes.get('name_standardized') or record_a.attributes.get('name', '')
        name_b = record_b.attributes.get('name_standardized') or record_b.attributes.get('name', '')
        
        if name_a and name_b:
            scores['name'] = self.scorer.composite_name_score(name_a, name_b)
        
        # Date of birth matching
        dob_a = record_a.attributes.get('date_of_birth')
        dob_b = record_b.attributes.get('date_of_birth')
        
        if dob_a and dob_b:
            scores['dob'] = 1.0 if str(dob_a) == str(dob_b) else 0.0
        
        # Address matching
        addr_a = record_a.attributes.get('address_standardized') or record_a.attributes.get('address', '')
        addr_b = record_b.attributes.get('address_standardized') or record_b.attributes.get('address', '')
        
        if addr_a and addr_b:
            scores['address'] = self.scorer.jaro_winkler_similarity(addr_a, addr_b)
        
        # ID matching (exact match if same ID type)
        for id_type in ['national_id', 'passport', 'tax_id', 'company_reg']:
            id_a = record_a.attributes.get(id_type)
            id_b = record_b.attributes.get(id_type)
            if id_a and id_b:
                scores[id_type] = 1.0 if id_a == id_b else 0.0
        
        # Calculate overall score with attribute weights
        weights = {
            'name': 0.35,
            'dob': 0.20,
            'address': 0.15,
            'national_id': 0.15,
            'passport': 0.10,
            'tax_id': 0.05,
            'company_reg': 0.05,
        }
        
        total_weight = sum(weights.get(k, 0.1) for k in scores)
        if total_weight > 0:
            overall = sum(scores[k] * weights.get(k, 0.1) for k in scores) / total_weight
        else:
            overall = 0.0
        
        return MatchCandidate(
            record_a=record_a,
            record_b=record_b,
            blocking_key="",
            similarity_scores=scores,
            overall_score=overall
        )
    
    def cluster_matches(
        self, 
        matches: List[MatchCandidate]
    ) -> List[List[EntityRecord]]:
        """
        Cluster matched records using Union-Find algorithm.
        Creates connected components of matched entities.
        """
        # Build adjacency from matches
        parent = {}
        rank = {}
        
        def find(x):
            if x not in parent:
                parent[x] = x
                rank[x] = 0
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px == py:
                return
            if rank[px] < rank[py]:
                px, py = py, px
            parent[py] = px
            if rank[px] == rank[py]:
                rank[px] += 1
        
        # Union matched pairs
        all_records = {}
        for match in matches:
            if match.overall_score >= self.match_threshold:
                id_a = match.record_a.id
                id_b = match.record_b.id
                union(id_a, id_b)
                all_records[id_a] = match.record_a
                all_records[id_b] = match.record_b
        
        # Group by cluster
        clusters = defaultdict(list)
        for record_id, record in all_records.items():
            root = find(record_id)
            clusters[root].append(record)
        
        return list(clusters.values())
    
    def create_canonical_record(
        self, 
        cluster: List[EntityRecord]
    ) -> ResolvedEntity:
        """
        Create a canonical (golden) record from a cluster of matched records.
        Uses survivorship rules to select best attribute values.
        """
        if not cluster:
            raise ValueError("Empty cluster")
        
        # Generate resolved ID
        sorted_ids = sorted(r.id for r in cluster)
        resolved_id = hashlib.md5("_".join(sorted_ids).encode()).hexdigest()[:16]
        
        # Survivorship: prefer most complete/recent records
        # Count non-null attributes per record
        completeness = []
        for record in cluster:
            non_null = sum(1 for v in record.attributes.values() if v)
            completeness.append((non_null, record))
        
        # Sort by completeness (descending)
        completeness.sort(key=lambda x: x[0], reverse=True)
        
        # Build canonical attributes
        canonical_attrs = {}
        for _, record in completeness:
            for key, value in record.attributes.items():
                if key not in canonical_attrs and value:
                    canonical_attrs[key] = value
        
        # Calculate confidence based on number of sources and agreement
        num_sources = len(set(r.source_system for r in cluster))
        confidence = min(1.0, 0.5 + num_sources * 0.1 + len(cluster) * 0.05)
        
        # Get canonical name
        canonical_name = canonical_attrs.get('name_standardized') or canonical_attrs.get('name', 'Unknown')
        
        return ResolvedEntity(
            resolved_id=resolved_id,
            canonical_name=canonical_name,
            entity_type=cluster[0].entity_type,
            source_records=cluster,
            confidence_score=confidence,
            attributes=canonical_attrs
        )
    
    def resolve(self, records: List[EntityRecord]) -> List[ResolvedEntity]:
        """
        Main entity resolution pipeline.
        
        1. Standardize all records
        2. Generate blocking keys
        3. Create candidate pairs within blocks
        4. Score all candidate pairs
        5. Cluster high-scoring matches
        6. Create canonical records
        """
        # Step 1: Standardize
        standardized = [self.standardize_record(r) for r in records]
        
        # Step 2: Generate blocking keys and index
        block_index = defaultdict(list)
        for record in standardized:
            keys = self.generate_blocking_keys(record)
            for key in keys:
                block_index[key].append(record)
        
        # Step 3 & 4: Generate and score candidates
        scored_pairs = []
        seen_pairs = set()
        
        for block_key, block_records in block_index.items():
            # Compare all pairs within block
            for i, record_a in enumerate(block_records):
                for record_b in block_records[i+1:]:
                    pair_key = tuple(sorted([record_a.id, record_b.id]))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)
                    
                    candidate = self.score_candidate_pair(record_a, record_b)
                    candidate.blocking_key = block_key
                    scored_pairs.append(candidate)
        
        # Step 5: Cluster matches
        clusters = self.cluster_matches(scored_pairs)
        
        # Add unmatched records as singletons
        matched_ids = {r.id for cluster in clusters for r in cluster}
        for record in standardized:
            if record.id not in matched_ids:
                clusters.append([record])
        
        # Step 6: Create canonical records
        resolved = [self.create_canonical_record(c) for c in clusters]
        
        return resolved


# Example usage and testing
def demo_entity_resolution():
    """Demonstrate entity resolution capabilities."""
    
    # Sample records from different source systems
    records = [
        EntityRecord(
            id="CRM_001",
            source_system="crm",
            entity_type="individual",
            attributes={
                "name": "John William Smith Jr.",
                "date_of_birth": "1985-03-15",
                "address": "123 Main Street, Singapore 123456",
                "national_id": "S1234567A"
            },
            raw_data={}
        ),
        EntityRecord(
            id="KYC_001",
            source_system="kyc_system",
            entity_type="individual",
            attributes={
                "name": "SMITH, JOHN W",
                "date_of_birth": "1985-03-15",
                "address": "123 Main St, Singapore",
                "passport": "E12345678"
            },
            raw_data={}
        ),
        EntityRecord(
            id="TXN_001",
            source_system="transaction_system",
            entity_type="individual",
            attributes={
                "name": "John Smith",
                "national_id": "S1234567A"
            },
            raw_data={}
        ),
        EntityRecord(
            id="CRM_002",
            source_system="crm",
            entity_type="individual",
            attributes={
                "name": "Jane Mary Doe",
                "date_of_birth": "1990-07-22",
                "address": "456 Oak Avenue, Singapore 654321"
            },
            raw_data={}
        ),
    ]
    
    # Run entity resolution
    engine = EntityResolutionEngine(match_threshold=0.7)
    resolved = engine.resolve(records)
    
    print(f"Input records: {len(records)}")
    print(f"Resolved entities: {len(resolved)}")
    
    for entity in resolved:
        print(f"\nResolved Entity: {entity.resolved_id}")
        print(f"  Canonical Name: {entity.canonical_name}")
        print(f"  Confidence: {entity.confidence_score:.2f}")
        print(f"  Source Records: {[r.id for r in entity.source_records]}")
        print(f"  Attributes: {entity.attributes}")


if __name__ == "__main__":
    demo_entity_resolution()

