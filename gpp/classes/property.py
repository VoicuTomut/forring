from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


class Property(BaseModel):
    """Property class with all details and mandatory legal documents"""
    property_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = Field(..., description="Agent managing this property")
    attached_notarys_id: List[str] = Field(default_factory=list, description="List of notary IDs attached")

    # Basic Property Information
    title: str = Field(..., description="Property title")
    description: str = Field(..., description="Property description")
    dimension: str = Field(..., description="Property dimensions/size")
    price: Decimal = Field(..., gt=0, description="Property price")

    # Location Information
    address: str = Field(default="", description="Property address")
    city: str = Field(default="", description="Property city")
    postal_code: str = Field(default="", description="Postal code")
    country: str = Field(default="", description="Country")

    # Property Details
    number_of_rooms: Optional[int] = Field(None, description="Number of rooms")
    finishes: Optional[str] = Field(None, description="Property finishes")
    renovations: Optional[str] = Field(None, description="Renovation details")
    neighborhood_description: Optional[str] = Field(None, description="Neighborhood info")

    # Management Fields
    post_date: datetime = Field(default_factory=datetime.now)
    validation_date: Optional[datetime] = Field(None, description="When property was validated")
    reserved: bool = Field(default=False, description="Is property reserved")
    looking_for_notary: bool = Field(default=False, description="Is property looking for notary")
    notary_attached: Optional[str] = Field(None, description="Property notary attached")
    status: str = Field(default="active", description="Property status")

    # Document References - needed for photo tracking
    document_ids: List[str] = Field(
        default_factory=list,
        description="List of all document IDs (including photos)"
    )

    # Mandatory Legal Documents Dictionary
    mandatory_legal_docs: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            "title_deed": None,  # Title Deed / Property Ownership Document
            "land_registry_extract": None,  # Land Registry Extract
            "building_permit": None,  # Building Permit
            "habitation_certificate": None,  # Habitation Certificate (Certificate of Occupancy)
            "mortgage_lien_certificate": None,  # Mortgage / Lien Certificate
            "seller_id_document": None,  # Seller's ID Document
            "marital_status_documents": None,  # Marital Status Documents
            "power_of_attorney": None,  # Power of Attorney
            "litigation_certificate": None,  # Litigation Certificate or Statement
        },
        description="Dictionary of mandatory legal documents with document IDs"
    )

    # NEW: Additional documents that can be added after submission
    additional_docs: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "supplementary_documents": [],  # Additional legal documents
            "corrections": [],  # Document corrections/updates
            "clarifications": [],  # Clarification documents
            "agent_notes": [],  # Agent notes and explanations
            "updated_photos": [],  # Additional/updated photos
            "floor_plans": [],  # Floor plans and blueprints
            "certificates": [],  # Additional certificates
            "correspondence": [],  # Email exchanges, letters
            "other": []  # Other miscellaneous documents
        },
        description="Dictionary of additional document categories with document ID lists"
    )

    # NEW: Track document addition history
    document_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of document additions with timestamps"
    )

    # NEW: Allow agents to add notes when uploading additional documents
    agent_notes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Agent notes with timestamps when adding documents"
    )


# Helper functions for property management
def add_document_to_property_mandatory(property_obj: Property, doc_type: str, document_id: str) -> Property:
    """Add document ID to property's mandatory legal documents"""
    if doc_type in property_obj.mandatory_legal_docs:
        property_obj.mandatory_legal_docs[doc_type] = document_id

        # Add to document history
        property_obj.document_history.append({
            "action": "mandatory_document_added",
            "document_type": doc_type,
            "document_id": document_id,
            "timestamp": datetime.now(),
            "added_by": property_obj.agent_id
        })
    return property_obj


def add_additional_document_to_property(property_obj: Property, category: str, document_id: str,
                                        agent_note: str = "") -> Property:
    """Add additional document to property after submission"""
    if category in property_obj.additional_docs:
        property_obj.additional_docs[category].append(document_id)

        # Add to main document list
        if document_id not in property_obj.document_ids:
            property_obj.document_ids.append(document_id)

        # Add to document history
        property_obj.document_history.append({
            "action": "additional_document_added",
            "category": category,
            "document_id": document_id,
            "timestamp": datetime.now(),
            "added_by": property_obj.agent_id,
            "note": agent_note
        })

        # Add agent note if provided
        if agent_note:
            property_obj.agent_notes.append({
                "note": agent_note,
                "timestamp": datetime.now(),
                "agent_id": property_obj.agent_id,
                "context": f"Added document to {category}"
            })

    return property_obj


def replace_mandatory_document(property_obj: Property, doc_type: str, new_document_id: str,
                               reason: str = "") -> Property:
    """Replace a mandatory document (useful for corrections)"""
    if doc_type in property_obj.mandatory_legal_docs:
        old_document_id = property_obj.mandatory_legal_docs[doc_type]
        property_obj.mandatory_legal_docs[doc_type] = new_document_id

        # Update document list
        if old_document_id in property_obj.document_ids:
            property_obj.document_ids.remove(old_document_id)
        if new_document_id not in property_obj.document_ids:
            property_obj.document_ids.append(new_document_id)

        # Add to document history
        property_obj.document_history.append({
            "action": "mandatory_document_replaced",
            "document_type": doc_type,
            "old_document_id": old_document_id,
            "new_document_id": new_document_id,
            "timestamp": datetime.now(),
            "added_by": property_obj.agent_id,
            "reason": reason
        })

        # Add agent note
        if reason:
            property_obj.agent_notes.append({
                "note": f"Replaced {doc_type}: {reason}",
                "timestamp": datetime.now(),
                "agent_id": property_obj.agent_id,
                "context": "document_replacement"
            })

    return property_obj


def add_agent_note_to_property(property_obj: Property, note: str, context: str = "general") -> Property:
    """Add a note from agent to property"""
    property_obj.agent_notes.append({
        "note": note,
        "timestamp": datetime.now(),
        "agent_id": property_obj.agent_id,
        "context": context
    })
    return property_obj


def get_property_additional_docs_count(property_obj: Property) -> Dict[str, int]:
    """Get count of additional documents by category"""
    return {category: len(doc_list) for category, doc_list in property_obj.additional_docs.items()}


def get_property_recent_activity(property_obj: Property, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent activity on property (document additions, notes)"""
    all_activity = []

    # Add document history
    for entry in property_obj.document_history:
        all_activity.append({
            "type": "document_activity",
            "timestamp": entry["timestamp"],
            "description": f"{entry['action'].replace('_', ' ').title()}",
            "details": entry
        })

    # Add agent notes
    for note in property_obj.agent_notes:
        all_activity.append({
            "type": "agent_note",
            "timestamp": note["timestamp"],
            "description": f"Agent Note: {note['note'][:50]}...",
            "details": note
        })

    # Sort by timestamp (most recent first) and limit
    all_activity.sort(key=lambda x: x["timestamp"], reverse=True)
    return all_activity[:limit]


def assign_notary_to_property(property_obj: Property, notary_id: str) -> Property:
    """Assign notary to property"""
    # Add to the list if not already there
    if notary_id not in property_obj.attached_notarys_id:
        property_obj.attached_notarys_id.append(notary_id)

    # Set the main notary attachment field
    property_obj.notary_attached = notary_id

    return property_obj


def reserve_property(property_obj: Property, buyer_id: str) -> Property:
    """Reserve property for buyer"""
    property_obj.reserved = True
    return property_obj