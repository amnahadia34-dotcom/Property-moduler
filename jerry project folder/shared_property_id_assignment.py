"""
Property ID Assignment Service

Handles property ID assignment during document extraction by matching
extracted addresses to livedata properties. This ensures all extraction
results are indexed by propertyID for efficient UI lookup.

Critical Design:
- Runs during document upload/extraction (NOT at UI runtime)
- Matches ALL addresses in extraction document to livedata
- Handles property aliases (multiple addresses for same property)
- Returns canonical propertyID for data storage
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from shared.utils.address_normalization import normalize_address, get_address_variants


class PropertyIDAssignmentService:
    """Service for assigning property IDs based on address matching"""
    
    def __init__(self, livedata_path="livedata/properties.json", aliases_path="livedata/property_aliases.json"):
        self.livedata_path = Path(livedata_path)
        self.aliases_path = Path(aliases_path)
        self.properties = []
        self.property_index = {}  # address -> property_id mapping
        self.aliases = {}  # property_id -> list of known aliases
        self._load_data()
    
    def _load_data(self):
        """Load livedata properties and assign IDs if missing"""
        if not self.livedata_path.exists():
            print(f"Warning: Livedata not found at {self.livedata_path}")
            return
        
        with open(self.livedata_path, 'r', encoding='utf-8') as f:
            self.properties = json.load(f)
        
        # Ensure all properties have property_id
        needs_save = False
        for prop in self.properties:
            if 'property_id' not in prop:
                # Generate property_id from address
                prop['property_id'] = self._generate_property_id(prop.get('address', ''))
                needs_save = True
            
            # Build index: normalized address -> property_id
            address = prop.get('address', '')
            if address:
                normalized = normalize_address(address)
                self.property_index[normalized] = prop['property_id']
        
        # Save if we added property_ids
        if needs_save:
            self._save_livedata()
        
        # Load aliases
        self._load_aliases()
    
    def _generate_property_id(self, address: str) -> str:
        """Generate unique property ID from address"""
        if not address:
            return f"PROP_{hashlib.md5(str(hash(address)).encode()).hexdigest()[:8].upper()}"
        
        # Use first 8 chars of MD5 hash of normalized address
        normalized = normalize_address(address)
        return f"PROP_{hashlib.md5(normalized.encode()).hexdigest()[:8].upper()}"
    
    def _save_livedata(self):
        """Save updated livedata with property IDs"""
        with open(self.livedata_path, 'w', encoding='utf-8') as f:
            json.dump(self.properties, f, indent=2, ensure_ascii=False)
    
    def _load_aliases(self):
        """Load known property aliases"""
        if self.aliases_path.exists():
            with open(self.aliases_path, 'r', encoding='utf-8') as f:
                self.aliases = json.load(f)
        else:
            self.aliases = {}
    
    def _save_aliases(self):
        """Save property aliases"""
        self.aliases_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.aliases_path, 'w', encoding='utf-8') as f:
            json.dump(self.aliases, f, indent=2, ensure_ascii=False)
    
    def match_addresses_to_property(self, extracted_addresses: List[str]) -> Tuple[Optional[str], List[str], float]:
        """
        Match extracted addresses to livedata property
        
        Args:
            extracted_addresses: List of all addresses found in document
            
        Returns:
            Tuple of (property_id, matched_addresses, confidence)
            - property_id: The matching livedata property ID or None
            - matched_addresses: Which addresses matched
            - confidence: Match confidence (0.0-1.0)
        """
        if not extracted_addresses:
            return None, [], 0.0
        
        # Normalize all extracted addresses
        normalized_extracted = [normalize_address(addr) for addr in extracted_addresses if addr]
        
        # Track matches
        matches = {}  # property_id -> (count, addresses)
        
        # Try exact matches first
        for i, norm_addr in enumerate(normalized_extracted):
            if not norm_addr:
                continue
                
            # Check against property index
            if norm_addr in self.property_index:
                prop_id = self.property_index[norm_addr]
                if prop_id not in matches:
                    matches[prop_id] = (0, [])
                count, addrs = matches[prop_id]
                matches[prop_id] = (count + 1, addrs + [extracted_addresses[i]])
            
            # Check against known aliases
            for prop_id, alias_list in self.aliases.items():
                for alias in alias_list:
                    if normalize_address(alias) == norm_addr:
                        if prop_id not in matches:
                            matches[prop_id] = (0, [])
                        count, addrs = matches[prop_id]
                        matches[prop_id] = (count + 1, addrs + [extracted_addresses[i]])
        
        if not matches:
            # Try fuzzy matching with variants
            for i, addr in enumerate(extracted_addresses):
                if not addr:
                    continue
                    
                variants = get_address_variants(addr)
                for variant in variants:
                    for livedata_addr, prop_id in self.property_index.items():
                        # Token-based similarity for hyphenated streets
                        if self._addresses_similar(variant, livedata_addr):
                            if prop_id not in matches:
                                matches[prop_id] = (0, [])
                            count, addrs = matches[prop_id]
                            matches[prop_id] = (count + 1, addrs + [extracted_addresses[i]])
                            break
        
        if not matches:
            return None, [], 0.0
        
        # Find best match (most addresses matched)
        best_prop_id = max(matches.keys(), key=lambda k: matches[k][0])
        match_count, matched_addrs = matches[best_prop_id]
        
        # Calculate confidence based on proportion of addresses matched
        confidence = match_count / len(extracted_addresses)
        
        return best_prop_id, matched_addrs, confidence
    
    def _addresses_similar(self, addr1: str, addr2: str, threshold: float = 0.6) -> bool:
        """Check if two normalized addresses are similar using token matching"""
        if not addr1 or not addr2:
            return False
        
        # Tokenize addresses
        tokens1 = set(addr1.split())
        tokens2 = set(addr2.split())
        
        if not tokens1 or not tokens2:
            return False
        
        # Separate numeric and text tokens
        numeric1 = {t for t in tokens1 if t.isdigit()}
        numeric2 = {t for t in tokens2 if t.isdigit()}
        text1 = {t for t in tokens1 if not t.isdigit()}
        text2 = {t for t in tokens2 if not t.isdigit()}
        
        # Both must have at least one matching number
        if numeric1 and numeric2 and not numeric1.intersection(numeric2):
            return False
        
        # Calculate text token similarity
        if text1 and text2:
            text_overlap = len(text1.intersection(text2))
            text_similarity = text_overlap / max(len(text1), len(text2))
            return text_similarity >= threshold
        
        return False
    
    def assign_property_id(self, extraction_data: Dict) -> Tuple[Optional[str], Dict]:
        """
        Main entry point: Assign property ID to extraction data
        
        Args:
            extraction_data: Raw extraction result containing property addresses
            
        Returns:
            Tuple of (property_id, metadata)
            - property_id: Assigned property ID or None
            - metadata: Assignment metadata (confidence, matched_addresses, etc.)
        """
        # Extract all addresses from the extraction data
        addresses = []
        
        # Check property section
        if 'property' in extraction_data:
            prop_data = extraction_data['property']
            
            # Main address
            addr = prop_data.get('address') or prop_data.get('property_address')
            if addr:
                if isinstance(addr, dict) and 'value' in addr:
                    addr = addr['value']
                if addr:
                    addresses.append(addr)
            
            # Owner address might be another alias
            owner_addr = prop_data.get('owner_address')
            if owner_addr:
                if isinstance(owner_addr, dict) and 'value' in owner_addr:
                    owner_addr = owner_addr['value']
                if owner_addr:
                    addresses.append(owner_addr)
        
        # Check for addresses in other sections
        if 'addresses' in extraction_data:
            for addr in extraction_data['addresses']:
                if addr and addr not in addresses:
                    addresses.append(addr)
        
        if not addresses:
            return None, {
                'status': 'no_addresses',
                'message': 'No addresses found in extraction data'
            }
        
        # Match to property
        property_id, matched_addrs, confidence = self.match_addresses_to_property(addresses)
        
        if property_id:
            # Update aliases if we found new ones
            if property_id not in self.aliases:
                self.aliases[property_id] = []
            
            for addr in matched_addrs:
                if addr not in self.aliases[property_id]:
                    self.aliases[property_id].append(addr)
            
            self._save_aliases()
            
            return property_id, {
                'status': 'matched',
                'confidence': confidence,
                'matched_addresses': matched_addrs,
                'all_addresses': addresses,
                'property_id': property_id
            }
        else:
            return None, {
                'status': 'no_match',
                'message': 'No matching property found in livedata',
                'addresses_tried': addresses
            }


# Global singleton instance
_service_instance = None

def get_property_id_service():
    """Get singleton instance of PropertyIDAssignmentService"""
    global _service_instance
    if _service_instance is None:
        _service_instance = PropertyIDAssignmentService()
    return _service_instance
