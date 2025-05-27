"""
Complete Buying Transaction System
Handles property buying transactions with document management and meeting scheduling
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
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

    # Meeting and Communication
    scheduled_meetings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of scheduled meetings between parties"
    )

    # Additional documents can be added
    additional_docs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Possibility to add more buying documents"
    )

    # Validation tracking
    document_validation_status: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Track validation status of each document"
    )

    # Transaction timeline
    created_date: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

    # Notes and communication log
    transaction_notes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Communication log between parties"
    )


class Meeting(BaseModel):
    """Meeting scheduling for buying transactions"""
    meeting_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    buying_id: str = Field(..., description="Associated buying transaction")
    meeting_type: str = Field(..., description="Type of meeting")
    scheduled_date: datetime = Field(..., description="Scheduled meeting date")
    participants: List[str] = Field(..., description="List of participant IDs")
    location: str = Field(default="", description="Meeting location")
    agenda: str = Field(default="", description="Meeting agenda")
    status: str = Field(default="scheduled", description="Meeting status")
    meeting_notes: str = Field(default="", description="Meeting notes")
    created_by: str = Field(..., description="Who created the meeting")
    created_date: datetime = Field(default_factory=datetime.now)


# Document type configurations for buying transactions
BUYING_DOCUMENT_TYPES = {
    "purchase_contract": "Purchase Contract",
    "payment_proof": "Payment Verification",
    "loan_approval": "Bank Loan Approval",
    "inspection_report": "Property Inspection Report",
    "insurance_policy": "Property Insurance Policy",
    "transfer_deed": "Property Transfer Deed"
}

MEETING_TYPES = {
    "property_viewing": "Property Viewing",
    "contract_discussion": "Contract Discussion",
    "final_signing": "Final Contract Signing",
    "inspection_meeting": "Property Inspection Meeting",
    "closing_meeting": "Transaction Closing Meeting",
    "general_discussion": "General Discussion"
}

TRANSACTION_STATUSES = {
    "pending": "🟡 Pending - Initial Interest",
    "documents_pending": "📄 Documents Pending",
    "under_review": "🔍 Under Review",
    "approved": "✅ Approved - Ready to Close",
    "completed": "🎉 Transaction Completed",
    "cancelled": "❌ Transaction Cancelled",
    "on_hold": "⏸️ On Hold"
}


# Helper functions for buying transaction management
def add_document_to_buying(buying_obj: Buying, doc_type: str, document_id: str) -> Buying:
    """Add document ID to buying transaction's document dictionary"""
    if doc_type in buying_obj.buying_documents:
        buying_obj.buying_documents[doc_type] = document_id

        # Initialize validation status for this document
        buying_obj.document_validation_status[doc_type] = {
            "document_id": document_id,
            "validation_status": False,
            "uploaded_by": None,
            "upload_date": datetime.now(),
            "validated_by": None,
            "validation_date": None,
            "validation_notes": ""
        }

        buying_obj.last_updated = datetime.now()
    return buying_obj


def create_buying_transaction(agent_id: str, buyer_id: str, property_id: str) -> Buying:
    """Create new buying transaction"""
    return Buying(
        agent_id=agent_id,
        buyer_id=buyer_id,
        property_id=property_id
    )


def update_buying_status(buying_obj: Buying, new_status: str, notes: str = "") -> Buying:
    """Update buying transaction status"""
    old_status = buying_obj.status
    buying_obj.status = new_status
    buying_obj.last_updated = datetime.now()

    if new_status == "completed":
        buying_obj.transaction_date = datetime.now()

    # Add status change to transaction notes
    if notes or old_status != new_status:
        add_transaction_note(
            buying_obj,
            f"Status changed from {old_status} to {new_status}. {notes}".strip(),
            "system"
        )

    return buying_obj


def add_transaction_note(buying_obj: Buying, note: str, author_id: str, note_type: str = "general") -> Buying:
    """Add note to transaction communication log"""
    buying_obj.transaction_notes.append({
        "note_id": str(uuid.uuid4()),
        "note": note,
        "author_id": author_id,
        "note_type": note_type,
        "timestamp": datetime.now(),
        "visibility": "all"  # or "agent_only", "buyer_only"
    })
    buying_obj.last_updated = datetime.now()
    return buying_obj


def schedule_meeting(buying_obj: Buying, meeting_data: Dict[str, Any]) -> Buying:
    """Schedule a meeting for the buying transaction"""
    meeting = {
        "meeting_id": str(uuid.uuid4()),
        "meeting_type": meeting_data.get("meeting_type", "general_discussion"),
        "scheduled_date": meeting_data.get("scheduled_date"),
        "participants": meeting_data.get("participants", []),
        "location": meeting_data.get("location", ""),
        "agenda": meeting_data.get("agenda", ""),
        "status": "scheduled",
        "created_by": meeting_data.get("created_by"),
        "created_date": datetime.now(),
        "meeting_notes": ""
    }

    buying_obj.scheduled_meetings.append(meeting)
    buying_obj.last_updated = datetime.now()

    # Add note about meeting scheduling
    add_transaction_note(
        buying_obj,
        f"Meeting scheduled: {MEETING_TYPES.get(meeting['meeting_type'], meeting['meeting_type'])} "
        f"on {meeting['scheduled_date'].strftime('%Y-%m-%d %H:%M')}",
        meeting_data.get("created_by", "system"),
        "meeting"
    )

    return buying_obj


def validate_buying_document(buying_obj: Buying, doc_type: str, validator_id: str,
                           validation_status: bool, notes: str = "") -> Buying:
    """Validate a document in the buying transaction"""
    if doc_type in buying_obj.document_validation_status:
        buying_obj.document_validation_status[doc_type].update({
            "validation_status": validation_status,
            "validated_by": validator_id,
            "validation_date": datetime.now(),
            "validation_notes": notes
        })

        buying_obj.last_updated = datetime.now()

        # Add validation note
        status_text = "approved" if validation_status else "rejected"
        add_transaction_note(
            buying_obj,
            f"Document {BUYING_DOCUMENT_TYPES.get(doc_type, doc_type)} {status_text}. {notes}".strip(),
            validator_id,
            "validation"
        )

        # Check if all documents are validated and update status accordingly
        all_docs_validated = all(
            doc_info.get("validation_status", False)
            for doc_info in buying_obj.document_validation_status.values()
            if buying_obj.buying_documents.get(doc_type) is not None
        )

        if all_docs_validated and buying_obj.status == "documents_pending":
            update_buying_status(buying_obj, "under_review", "All documents validated")

    return buying_obj


def get_buying_progress(buying_obj: Buying) -> Dict[str, Any]:
    """Get progress information for buying transaction"""
    total_docs = len([doc_id for doc_id in buying_obj.buying_documents.values() if doc_id])
    validated_docs = len([
        doc for doc in buying_obj.document_validation_status.values()
        if doc.get("validation_status", False)
    ])

    progress = (validated_docs / total_docs * 100) if total_docs > 0 else 0

    return {
        "total_documents": total_docs,
        "validated_documents": validated_docs,
        "progress_percentage": progress,
        "status": buying_obj.status,
        "status_display": TRANSACTION_STATUSES.get(buying_obj.status, buying_obj.status),
        "last_updated": buying_obj.last_updated,
        "scheduled_meetings": len(buying_obj.scheduled_meetings),
        "active_meetings": len([
            m for m in buying_obj.scheduled_meetings
            if m.get("status") == "scheduled" and m.get("scheduled_date", datetime.now()) > datetime.now()
        ])
    }


def get_next_meeting(buying_obj: Buying) -> Optional[Dict[str, Any]]:
    """Get the next scheduled meeting for this transaction"""
    upcoming_meetings = [
        meeting for meeting in buying_obj.scheduled_meetings
        if meeting.get("status") == "scheduled" and
           meeting.get("scheduled_date", datetime.now()) > datetime.now()
    ]

    if upcoming_meetings:
        return min(upcoming_meetings, key=lambda x: x.get("scheduled_date", datetime.now()))

    return None


def can_user_edit_transaction(buying_obj: Buying, user_id: str, user_type: str) -> bool:
    """Check if user can edit this buying transaction"""
    if user_type == "notary":
        return True  # Notaries can edit all transactions
    elif user_type == "agent":
        return buying_obj.agent_id == user_id
    elif user_type == "buyer":
        return buying_obj.buyer_id == user_id

    return False


def get_user_buying_transactions(user_id: str, user_type: str, all_transactions: Dict[str, Buying]) -> Dict[str, Buying]:
    """Get buying transactions relevant to a specific user"""
    relevant_transactions = {}

    for buying_id, buying_obj in all_transactions.items():
        if user_type == "agent" and buying_obj.agent_id == user_id:
            relevant_transactions[buying_id] = buying_obj
        elif user_type == "buyer" and buying_obj.buyer_id == user_id:
            relevant_transactions[buying_id] = buying_obj
        elif user_type == "notary":
            # Notaries see all transactions that need validation
            if buying_obj.status in ["documents_pending", "under_review"]:
                relevant_transactions[buying_id] = buying_obj

    return relevant_transactions


# Database operations (to be implemented with your database system)
def save_buying_transaction(buying_obj: Buying):
    """Save buying transaction to database"""
    # Implement with your database system
    pass


def load_buying_transaction(buying_id: str) -> Optional[Buying]:
    """Load buying transaction from database"""
    # Implement with your database system
    pass


def get_all_buying_transactions() -> Dict[str, Buying]:
    """Get all buying transactions from database"""
    # Implement with your database system
    pass