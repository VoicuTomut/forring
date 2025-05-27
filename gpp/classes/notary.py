from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid


class Notary(BaseModel):
    """Notary class - validates properties and buyers"""
    notary_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Work Management Lists
    checked_prop_list: List[str] = Field(
        default_factory=list,
        description="List of property IDs that have been checked/validated"
    )
    properties_to_check: List[str] = Field(
        default_factory=list,
        description="List of property IDs that need to be checked"
    )
    buyers_to_check: List[str] = Field(
        default_factory=list,
        description="List of buyer IDs that need to be checked"
    )

    # Notary Documents
    documents: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            "professional_license": None,  # Notary license
            "certification": None,  # Professional certification
            "id_document": None,  # ID/Passport
            "chamber_registration": None,  # Notary chamber registration
        },
        description="Dictionary of notary documents with document IDs"
    )

    # Additional documents can be added
    additional_docs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Possibility to add more documents"
    )


# Helper functions for notary management
def add_document_to_notary(notary_obj: Notary, doc_type: str, document_id: str) -> Notary:
    """Add document ID to notary's document dictionary"""
    if doc_type in notary_obj.documents:
        notary_obj.documents[doc_type] = document_id
    return notary_obj


def add_work_to_notary(notary_obj: Notary, item_id: str, work_type: str) -> Notary:
    """Add property or buyer to notary's work lists"""
    if work_type == "property_to_check":
        if item_id not in notary_obj.properties_to_check:
            notary_obj.properties_to_check.append(item_id)
    elif work_type == "property_checked":
        if item_id not in notary_obj.checked_prop_list:
            notary_obj.checked_prop_list.append(item_id)
        # Remove from to_check list if it exists
        if item_id in notary_obj.properties_to_check:
            notary_obj.properties_to_check.remove(item_id)
    elif work_type == "buyer_to_check":
        if item_id not in notary_obj.buyers_to_check:
            notary_obj.buyers_to_check.append(item_id)
    return notary_obj