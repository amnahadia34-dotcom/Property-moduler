"""
Property Consolidation System with Confidence-Based Updates
Implements property objects with automatic document consolidation
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

class ConfidenceLevel(Enum):
    VERY_HIGH = 95  # Professional appraisals
    HIGH = 85       # Insurance documents, seller declarations
    MEDIUM = 70     # Tax assessments, municipal records
    LOW = 50        # Estimates, derived values

class DocumentType(Enum):
    APPRAISAL = ("Appraisal Report", ConfidenceLevel.VERY_HIGH)
    INSURANCE = ("Insurance Policy", ConfidenceLevel.HIGH)
    SELLER_DECLARATION = ("Seller Declaration", ConfidenceLevel.HIGH)
    TAX_ASSESSMENT = ("Tax Assessment", ConfidenceLevel.MEDIUM)
    LEASE = ("Lease Document", ConfidenceLevel.MEDIUM)
    
    def __init__(self, doc_name: str, confidence: ConfidenceLevel):
        self.doc_name = doc_name
        self.confidence = confidence

@dataclass
class PropertyValue:
    """Property value with confidence tracking"""
    value: Any
    confidence: int
    source_document: str
    source_type: DocumentType
    extraction_date: str
    notes: str = ""

@dataclass
class PropertyObject:
    """Core property object with confidence-based field updates"""
    # Unique identifier
    property_id: str
    
    # Address (highest confidence wins)
    address: Optional[PropertyValue] = None
    owner_address: Optional[PropertyValue] = None
    
    # Building details
    total_units: Optional[PropertyValue] = None
    unit_sizes: Optional[PropertyValue] = None
    building_age: Optional[PropertyValue] = None
    construction_date: Optional[PropertyValue] = None
    number_of_stories: Optional[PropertyValue] = None
    building_size: Optional[PropertyValue] = None
    land_size: Optional[PropertyValue] = None
    
    # Building systems
    heating_system: Optional[PropertyValue] = None
    exterior_material: Optional[PropertyValue] = None
    foundation_type: Optional[PropertyValue] = None
    windows_material: Optional[PropertyValue] = None
    windows_age: Optional[PropertyValue] = None
    plumbing_type: Optional[PropertyValue] = None
    plumbing_age: Optional[PropertyValue] = None
    electrical: Optional[PropertyValue] = None
    roofing_material: Optional[PropertyValue] = None
    roofing_type: Optional[PropertyValue] = None
    roofing_age: Optional[PropertyValue] = None
    water_tank_age: Optional[PropertyValue] = None
    
    # Services
    sewer_service: Optional[PropertyValue] = None
    sewer_source: Optional[PropertyValue] = None
    
    # Financial (Value Confidence Hierarchy Rule #10)
    sale_amount: Optional[PropertyValue] = None
    municipal_evaluation: Optional[PropertyValue] = None
    current_market_value: Optional[PropertyValue] = None  # From appraisals only
    
    # Property classification
    property_type: Optional[PropertyValue] = None
    building_type: Optional[PropertyValue] = None
    
    # Incidents (specialized damage extractor)
    fire_incidents: Optional[PropertyValue] = None
    water_incidents: Optional[PropertyValue] = None
    
    # Metadata
    created_date: str = ""
    last_updated: str = ""
    source_documents: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()

class PropertyConsolidator:
    """Manages property objects with confidence-based updates"""
    
    def __init__(self, data_dir: str = "extraction_results"):
        self.data_dir = data_dir
        self.properties: Dict[str, PropertyObject] = {}
        self.load_properties()
    
    def generate_property_id(self, address: str) -> str:
        """Generate unique property ID from normalized address for consistency"""
        # Import address normalization to ensure consistent IDs across variations
        import sys
        sys.path.insert(0, 'shared')
        try:
            from utils.address_normalization import normalize_address
            normalized = normalize_address(address)
        except ImportError:
            # Fallback if import fails
            normalized = address.lower().strip().replace(",", "").replace("  ", " ")
        
        hash_obj = hashlib.md5(normalized.encode())
        return f"PROP_{hash_obj.hexdigest()[:8].upper()}"
    
    def classify_document_type(self, doc_info: Dict) -> DocumentType:
        """Classify document type for confidence assignment"""
        doc_type = doc_info.get("Document Type", "")
        
        # Handle nested structure {value, confidence, source}
        if isinstance(doc_type, dict) and 'value' in doc_type:
            doc_type = doc_type['value']
        
        doc_type = str(doc_type).lower()
        
        if "appraisal" in doc_type or "évaluation" in doc_type:
            return DocumentType.APPRAISAL
        elif "insurance" in doc_type or "assurance" in doc_type:
            return DocumentType.INSURANCE
        elif "declaration" in doc_type or "seller" in doc_type:
            return DocumentType.SELLER_DECLARATION
        elif "tax" in doc_type or "municipal" in doc_type:
            return DocumentType.TAX_ASSESSMENT
        elif "lease" in doc_type or "bail" in doc_type:
            return DocumentType.LEASE
        else:
            return DocumentType.INSURANCE  # Default fallback
    
    def should_update_field(self, current_value: Optional[PropertyValue], 
                          new_confidence: int, new_source_type: DocumentType) -> bool:
        """Determine if field should be updated based on confidence"""
        if current_value is None:
            return True
        
        # Value Confidence Hierarchy (Rule #10)
        if new_source_type == DocumentType.APPRAISAL:
            return True  # Appraisals always override
        
        # Higher confidence always wins
        if new_confidence > current_value.confidence:
            return True
        
        # Same confidence from newer document
        if new_confidence == current_value.confidence:
            return True  # Keep most recent
        
        return False
    
    def create_property_value(self, value: Any, source_doc: str, 
                            source_type: DocumentType, notes: str = "") -> PropertyValue:
        """Create PropertyValue with confidence tracking"""
        return PropertyValue(
            value=value,
            confidence=source_type.confidence.value,
            source_document=source_doc,
            source_type=source_type,
            extraction_date=datetime.now().isoformat(),
            notes=notes
        )
    
    def save_extraction_document(self, property_id: str, doc_type: str, extraction_data: Dict) -> str:
        """
        Save individual extraction document as propertyID_doctype.json
        
        Args:
            property_id: Property ID (e.g., PROP_A1B2C3D4)
            doc_type: Document type (e.g., 'appraisal', 'insurance', 'tax')
            extraction_data: Raw extraction data
            
        Returns:
            Path to saved file
        """
        doc_file = os.path.join(self.data_dir, f"{property_id}_{doc_type}.json")
        
        data = {
            "property_id": property_id,
            "document_type": doc_type,
            "extraction_date": datetime.now().isoformat(),
            "extraction_data": extraction_data
        }
        
        with open(doc_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return doc_file
    
    def update_property_from_extraction(self, extraction_data: Dict, save_doc: bool = True, override_property_id: str = None) -> str:
        """Update property object from document extraction results
        
        Args:
            extraction_data: Extracted property data
            save_doc: Whether to save individual document JSON
            override_property_id: Use this property ID instead of generating from address (from livedata matching)
        """
        # Get property address and generate/use ID
        address = extraction_data.get("Property Address", "")
        
        # Handle nested {value, confidence, source} structure
        if isinstance(address, dict) and 'value' in address:
            address = address['value']
        
        if not address or address in ["/", "", "null"]:
            raise ValueError("Cannot create property without valid address")
        
        # Use override ID if provided (from livedata matching), otherwise generate
        if override_property_id:
            property_id = override_property_id
        else:
            property_id = self.generate_property_id(address)
        source_file = extraction_data.get("source_file", "unknown")
        doc_type = self.classify_document_type(extraction_data)
        
        # Get or create property object
        if property_id not in self.properties:
            self.properties[property_id] = PropertyObject(property_id=property_id)
        
        prop = self.properties[property_id]
        
        # CRITICAL: If override_property_id was provided, ensure PropertyObject has correct property_id
        # This handles cases where old extraction data had different ID
        if override_property_id and prop.property_id != override_property_id:
            prop.property_id = override_property_id
        
        # Add source document to tracking
        if source_file not in prop.source_documents:
            prop.source_documents.append(source_file)
        
        # Update fields based on confidence levels
        # Handle both capitalization variations (e.g., "Windows material" vs "Windows Material")
        field_mappings = {
            "address": ["Property Address"],
            "owner_address": ["Owner Address"], 
            "total_units": ["Total Units"],
            "unit_sizes": ["Unit Sizes"],
            "building_age": ["Building Age"],
            "construction_date": ["Construction Date", "Year Built"],
            "number_of_stories": ["Number of Stories"],
            "building_size": ["Building Size", "Floor Area"],
            "land_size": ["Land Size", "Lot Size"],
            "heating_system": ["Heating System"],
            "exterior_material": ["Exterior Material"],
            "foundation_type": ["Foundation Type", "Foundation"],
            "windows_material": ["Windows Material", "Windows material"],
            "windows_age": ["Windows Age"],
            "plumbing_type": ["Plumbing Type", "Plumbing type", "Plumbing System"], 
            "plumbing_age": ["Plumbing Age"],
            "electrical": ["Electrical", "Electrical System"],
            "roofing_material": ["Roofing Material", "Roofing material"],
            "roofing_type": ["Roofing Type", "Roofing type"],
            "roofing_age": ["Roofing Age", "Roofing age"],
            "water_tank_age": ["Water Tank Age"],
            "sewer_service": ["Sewer Service"],
            "sewer_source": ["Sewer Source"],
            "sale_amount": ["Sale Amount"],
            "municipal_evaluation": ["Municipal Evaluation"],
            "property_type": ["Property Type"],
            "building_type": ["Building Type"],
            "fire_incidents": ["Fire Incidents"]
        }
        
        # Update each field with confidence checking
        for prop_field, extract_field_variants in field_mappings.items():
            extracted_value = None
            
            # Try all field name variations
            for extract_field in extract_field_variants:
                if extract_field in extraction_data:
                    extracted_value = extraction_data.get(extract_field)
                    break
            
            # Handle nested {value, confidence, source} structure
            if isinstance(extracted_value, dict) and 'value' in extracted_value:
                extracted_value = extracted_value['value']
            
            if extracted_value is not None and extracted_value not in ["", "/", "null"]:
                current_value = getattr(prop, prop_field)
                
                if self.should_update_field(current_value, doc_type.confidence.value, doc_type):
                    new_value = self.create_property_value(
                        value=extracted_value,
                        source_doc=source_file,
                        source_type=doc_type,
                        notes=extraction_data.get("extraction_notes", "")
                    )
                    setattr(prop, prop_field, new_value)
        
        # Special handling for market value (Rule #10A)
        if doc_type == DocumentType.APPRAISAL and extraction_data.get("Sale Amount"):
            # Appraisal values become current market value
            market_value = self.create_property_value(
                value=extraction_data["Sale Amount"],
                source_doc=source_file,
                source_type=doc_type,
                notes="Market value from professional appraisal"
            )
            prop.current_market_value = market_value
        
        prop.last_updated = datetime.now().isoformat()
        
        # Save individual extraction document as propertyID_doctype.json
        if save_doc:
            doc_type_name = doc_type.name.lower()
            self.save_extraction_document(property_id, doc_type_name, extraction_data)
        
        # Save consolidated property file as propertyID_consolidated.json
        self.save_properties()
        
        return property_id
    
    def get_property(self, property_id: str) -> Optional[PropertyObject]:
        """Get property object by ID"""
        return self.properties.get(property_id)
    
    def get_property_by_address(self, address: str) -> Optional[PropertyObject]:
        """Get property object by address"""
        property_id = self.generate_property_id(address)
        return self.get_property(property_id)
    
    def list_all_properties(self) -> List[PropertyObject]:
        """Get all property objects"""
        return list(self.properties.values())
    
    def get_property_summary(self, property_id: str) -> Optional[Dict]:
        """Get property summary with confidence levels"""
        prop = self.get_property(property_id)
        if not prop:
            return None
        
        summary = {
            "property_id": prop.property_id,
            "source_documents": prop.source_documents,
            "created_date": prop.created_date,
            "last_updated": prop.last_updated,
            "fields": {}
        }
        
        # Add all fields with confidence info
        for field_name in prop.__dataclass_fields__:
            if field_name in ["property_id", "created_date", "last_updated", "source_documents"]:
                continue
            
            field_value = getattr(prop, field_name)
            if field_value:
                summary["fields"][field_name] = {
                    "value": field_value.value,
                    "confidence": field_value.confidence,
                    "source": field_value.source_document,
                    "source_type": field_value.source_type.doc_name,
                    "date": field_value.extraction_date
                }
        
        return summary
    
    def save_properties(self):
        """Save each property to individual propertyID_consolidated.json file"""
        os.makedirs(self.data_dir, exist_ok=True)
        
        for prop_id, prop in self.properties.items():
            # Convert property object to dictionary
            prop_dict = {}
            for field_name in prop.__dataclass_fields__:
                field_value = getattr(prop, field_name)
                if isinstance(field_value, PropertyValue):
                    prop_dict[field_name] = {
                        "value": field_value.value,
                        "confidence": field_value.confidence,
                        "source_document": field_value.source_document,
                        "source_type": field_value.source_type.name,
                        "extraction_date": field_value.extraction_date,
                        "notes": field_value.notes
                    }
                else:
                    prop_dict[field_name] = field_value
            
            # Save to individual file: propertyID_consolidated.json
            consolidated_file = os.path.join(self.data_dir, f"{prop_id}_consolidated.json")
            
            data = {
                "system_version": "PROPERTY_CONSOLIDATOR_v1.0",
                "last_updated": datetime.now().isoformat(),
                "property": prop_dict
            }
            
            with open(consolidated_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_properties(self):
        """Load all properties from individual propertyID_consolidated.json files"""
        if not os.path.exists(self.data_dir):
            return
        
        try:
            # Find all consolidated files matching pattern: *_consolidated.json
            import glob
            consolidated_files = glob.glob(os.path.join(self.data_dir, "*_consolidated.json"))
            
            for consolidated_file in consolidated_files:
                with open(consolidated_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                prop_dict = data.get("property", {})
                if not prop_dict:
                    continue
                
                prop_id = prop_dict.get("property_id")
                if not prop_id:
                    continue
                
                prop = PropertyObject(property_id=prop_id)
                
                for field_name, field_data in prop_dict.items():
                    if field_name in ["property_id", "created_date", "last_updated", "source_documents"]:
                        setattr(prop, field_name, field_data)
                    elif isinstance(field_data, dict) and "value" in field_data:
                        source_type = DocumentType[field_data["source_type"]]
                        prop_value = PropertyValue(
                            value=field_data["value"],
                            confidence=field_data["confidence"],
                            source_document=field_data["source_document"],
                            source_type=source_type,
                            extraction_date=field_data["extraction_date"],
                            notes=field_data.get("notes", "")
                        )
                        setattr(prop, field_name, prop_value)
                
                self.properties[prop_id] = prop
                
        except Exception as e:
            print(f"Error loading properties: {e}")

# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python property_consolidator.py <extraction_json_file>")
        sys.exit(1)
    
    # Load extraction results
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        extraction_data = json.load(f)
    
    # Initialize consolidator
    consolidator = PropertyConsolidator()
    
    # Process extraction
    property_id = consolidator.update_property_from_extraction(extraction_data)
    
    # Show results
    summary = consolidator.get_property_summary(property_id)
    print(json.dumps(summary, indent=2, ensure_ascii=False))