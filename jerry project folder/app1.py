import os
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------
# BACKEND CORE: CONFIDENCE-BASED PROPERTY CONSOLIDATOR
# ---------------------------------------------------

class ConfidenceLevel(Enum):
    VERY_HIGH = 95
    HIGH = 85
    MEDIUM = 70
    LOW = 50


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
    value: Any
    confidence: int
    source_document: str
    source_type: DocumentType
    extraction_date: str
    notes: str = ""


@dataclass
class PropertyObject:
    property_id: str
    address: Optional[PropertyValue] = None
    sale_amount: Optional[PropertyValue] = None
    building_type: Optional[PropertyValue] = None
    total_units: Optional[PropertyValue] = None
    heating_system: Optional[PropertyValue] = None
    foundation_type: Optional[PropertyValue] = None
    plumbing_type: Optional[PropertyValue] = None
    water_tank_age: Optional[PropertyValue] = None
    created_date: str = ""
    last_updated: str = ""
    source_documents: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.created_date:
            self.created_date = datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()


class PropertyConsolidator:
    def __init__(self, data_dir="extraction_results"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.properties: Dict[str, PropertyObject] = {}
        self.load_properties()

    # -----------------------
    # Unique ID per property
    # -----------------------
    def generate_property_id(self, address: str) -> str:
        addr = str(address).lower().strip().replace(",", "")
        return "PROP_" + hashlib.md5(addr.encode()).hexdigest()[:8].upper()

    # -----------------------
    # Document classification
    # -----------------------
    def classify_document_type(self, data: Dict) -> DocumentType:
        doc = str(data.get("Document Type", "")).lower()
        if "appraisal" in doc:
            return DocumentType.APPRAISAL
        if "insurance" in doc:
            return DocumentType.INSURANCE
        if "tax" in doc or "municipal" in doc:
            return DocumentType.TAX_ASSESSMENT
        if "declaration" in doc or "vendeur" in doc:
            return DocumentType.SELLER_DECLARATION
        return DocumentType.INSURANCE

    # -----------------------
    # Create a new PropertyValue
    # -----------------------
    def create_value(self, value, src, doc_type) -> PropertyValue:
        return PropertyValue(
            value=value,
            confidence=doc_type.confidence.value,
            source_document=src,
            source_type=doc_type,
            extraction_date=datetime.now().isoformat()
        )

    # -----------------------
    # Update or add property
    # -----------------------
    def update_property_from_extraction(self, data: Dict):
        # Smart address detection (any key containing 'address')
        address = None
        for key in data.keys():
            if "address" in key.lower():
                address = data[key]
                break

        if not address or str(address).strip() in ["", "/", "null", "none"]:
            address = f"Unknown_{hashlib.md5(json.dumps(data).encode()).hexdigest()[:6]}"

        prop_id = self.generate_property_id(address)
        doc_type = self.classify_document_type(data)
        src = data.get("source_file", "upload")

        # retrieve existing property if any
        prop = self.properties.get(prop_id, PropertyObject(property_id=prop_id))
        if src not in prop.source_documents:
            prop.source_documents.append(src)

        field_map = {
            "address": address,
            "sale_amount": data.get("Sale Amount"),
            "building_type": data.get("Building Type"),
            "total_units": data.get("Total Units"),
            "heating_system": data.get("Heating System"),
            "foundation_type": data.get("Foundation Type"),
            "plumbing_type": data.get("Plumbing Type"),
            "water_tank_age": data.get("Water Tank Age"),
        }

        for field, val in field_map.items():
            if val and str(val).strip() not in ["", "null", "/"]:
                setattr(prop, field, self.create_value(val, src, doc_type))

        prop.last_updated = datetime.now().isoformat()
        self.properties[prop_id] = prop
        self.save_properties()
        return prop_id

    # -----------------------
    # Property summary
    # -----------------------
    def get_property_summary(self, prop_id: str):
        prop = self.properties.get(prop_id)
        if not prop:
            return None
        summary = {
            "property_id": prop_id,
            "fields": {},
            "source_documents": prop.source_documents
        }
        for name, value in prop.__dict__.items():
            if isinstance(value, PropertyValue):
                summary["fields"][name] = {
                    "value": value.value,
                    "confidence": value.confidence,
                    "source_document": value.source_document,
                    "source_type": value.source_type.doc_name
                }
        return summary

    # -----------------------
    # List all properties
    # -----------------------
    def list_all_properties(self):
        return list(self.properties.values())

    # -----------------------
    # Save all properties to disk
    # -----------------------
    def save_properties(self):
        for pid, prop in self.properties.items():
            with open(os.path.join(self.data_dir, f"{pid}_consolidated.json"), "w", encoding="utf-8") as f:
                json.dump({"property": self.serialize_property(prop)}, f, indent=2, default=str)

        # ✅ Add summary exporter call
        try:
            self.export_summary()
        except Exception as e:
            print(f"⚠️ Warning: Failed to export summary - {e}")

    # helper for JSON safe dump
    def serialize_property(self, prop: PropertyObject) -> Dict:
        data = prop.__dict__.copy()
        for key, val in data.items():
            if isinstance(val, PropertyValue):
                data[key] = {
                    "value": val.value,
                    "confidence": val.confidence,
                    "source_document": val.source_document,
                    "source_type": val.source_type.doc_name,
                    "extraction_date": val.extraction_date,
                }
        return data

    # -----------------------
    # Export combined summary (for Jerry)
    # -----------------------
    def export_summary(self):
        try:
            summary = []
            for pid, prop in self.properties.items():
                total_fields = len([v for v in prop.__dict__.values() if isinstance(v, PropertyValue)])
                avg_conf = round(sum(
                    v.confidence for v in prop.__dict__.values()
                    if isinstance(v, PropertyValue)
                ) / max(total_fields, 1), 1)
                summary.append({
                    "Property ID": pid,
                    "Source Count": len(prop.source_documents),
                    "Average Confidence": f"{avg_conf}%",
                    "Last Updated": prop.last_updated.split("T")[0],
                    "Total Fields": total_fields
                })

            with open(os.path.join(self.data_dir, "master_summary.json"), "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            print(f"✅ Summary exported successfully ({len(summary)} properties).")

        except Exception as e:
            print(f"⚠️ Warning: Failed to export summary - {e}")

    # -----------------------
    # Load all saved properties
    # -----------------------
    def load_properties(self):
        for f in os.listdir(self.data_dir):
            if f.endswith("_consolidated.json"):
                try:
                    data = json.load(open(os.path.join(self.data_dir, f), "r", encoding="utf-8"))
                    prop_data = data.get("property", {})
                    pid = prop_data.get("property_id")
                    if not pid:
                        continue

                    prop_obj = PropertyObject(
                        property_id=pid,
                        created_date=prop_data.get("created_date", ""),
                        last_updated=prop_data.get("last_updated", ""),
                        source_documents=prop_data.get("source_documents", [])
                    )

                    # restore all PropertyValue fields
                    for field_name, field_val in prop_data.items():
                        if isinstance(field_val, dict) and "value" in field_val:
                            setattr(prop_obj, field_name, PropertyValue(
                                value=field_val.get("value"),
                                confidence=field_val.get("confidence", 85),
                                source_document=field_val.get("source_document", ""),
                                source_type=DocumentType.INSURANCE,
                                extraction_date=field_val.get("extraction_date", "")
                            ))

                    self.properties[pid] = prop_obj

                except json.JSONDecodeError:
                    print(f"⚠️ Skipped corrupt file: {f}")
