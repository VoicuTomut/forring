from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


class Buying(BaseModel):
    """Buying class - manages the transaction between agent, buyer, and property"""
    buying_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = Field(..., description="Agent involved in the transaction")
    buyer_id: str = Field(..., description="Buyer involved in the transaction")
    property_id: str = Field(..., description="Property being bought")

    # Transaction Documents
    buying_documents: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            "purchase_contract": None,  # Purchase contract
            "payment_proof": None,  # Payment verification
            "loan_approval": None,  # Bank loan approval
            "inspection_report": None,  # Property inspection
            "insurance_policy": None,  # Property insurance
            "transfer_deed": None,  # Property transfer deed
        },
        description="Dictionary of buying transaction documents"
    )

    # Transaction Details
    transaction_date: Optional[datetime] = Field(None, description="Date of transaction")
    final_price: Optional[Decimal] = Field(None, description="Final agreed price")
    status: str = Field(default="pending", description="Transaction status")

    # Additional documents can be added
    additional_docs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Possibility to add more buying documents"
    )


# Helper functions for buying transaction management
def add_document_to_buying(buying_obj: Buying, doc_type: str, document_id: str) -> Buying:
    """Add document ID to buying transaction's document dictionary"""
    if doc_type in buying_obj.buying_documents:
        buying_obj.buying_documents[doc_type] = document_id
    return buying_obj


def create_buying_transaction(agent_id: str, buyer_id: str, property_id: str) -> Buying:
    """Create new buying transaction"""
    return Buying(
        agent_id=agent_id,
        buyer_id=buyer_id,
        property_id=property_id
    )


def update_buying_status(buying_obj: Buying, new_status: str) -> Buying:
    """Update buying transaction status"""
    buying_obj.status = new_status
    if new_status == "completed":
        buying_obj.transaction_date = datetime.now()
    return buying_obj