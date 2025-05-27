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

    # Optional: Additional documents can be added
    additional_docs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary for additional documents that can be added"
    )


# Helper functions for property management
def add_document_to_property_mandatory(property_obj: Property, doc_type: str, document_id: str) -> Property:
    """Add document ID to property's mandatory legal documents"""
    if doc_type in property_obj.mandatory_legal_docs:
        property_obj.mandatory_legal_docs[doc_type] = document_id
    return property_obj


def assign_notary_to_property(property_obj: Property, notary_id: str) -> Property:
    """Assign notary to property"""
    if notary_id not in property_obj.attached_notarys_id:
        property_obj.attached_notarys_id.append(notary_id)
    return property_obj


def reserve_property(property_obj: Property, buyer_id: str) -> Property:
    """Reserve property for buyer"""
    property_obj.reserved = True
    return property_obj