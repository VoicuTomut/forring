from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid


class Buyer(BaseModel):
    """Buyer class - similar to agent with financial documents"""
    buyer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Financial Information
    bank_account: Optional[str] = Field(None, description="Bank account information")
    income_segment: Optional[str] = Field(None, description="Income bracket/segment")

    # Property Interest Lists
    interested_properties: List[str] = Field(
        default_factory=list,
        description="List of property IDs buyer is interested in"
    )
    reserved_properties: List[str] = Field(
        default_factory=list,
        description="List of property IDs buyer has reserved"
    )

    # Buyer Documents
    documents: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            "id_document": None,  # ID/Passport
            "income_proof": None,  # Income verification
            "bank_statements": None,  # Bank statements
            "credit_report": None,  # Credit report
        },
        description="Dictionary of buyer documents with document IDs"
    )

    # Additional documents can be added
    additional_docs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Possibility to add more documents"
    )


# Helper functions for buyer management
def add_document_to_buyer(buyer_obj: Buyer, doc_type: str, document_id: str) -> Buyer:
    """Add document ID to buyer's document dictionary"""
    if doc_type in buyer_obj.documents:
        buyer_obj.documents[doc_type] = document_id
    return buyer_obj


def add_interest_to_buyer(buyer_obj: Buyer, property_id: str, interest_type: str = "interested") -> Buyer:
    """Add property to buyer's interest lists"""
    if interest_type == "interested":
        if property_id not in buyer_obj.interested_properties:
            buyer_obj.interested_properties.append(property_id)
    elif interest_type == "reserved":
        if property_id not in buyer_obj.reserved_properties:
            buyer_obj.reserved_properties.append(property_id)
    return buyer_obj