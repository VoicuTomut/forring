"""
Complete Buying Transaction System with Enhanced Document Signing
Handles property buying transactions with document management, meeting scheduling, and digital signatures
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import hashlib


class Buying(BaseModel):
    """Enhanced Buying class - manages the transaction between agent, buyer, and property with signing workflow"""
    buying_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = Field(..., description="Agent involved in the transaction")
    buyer_id: str = Field(..., description="Buyer involved in the transaction")
    property_id: str = Field(..., description="Property being bought")

    # Enhanced Transaction Documents - supports both old and new document types
    buying_documents: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            # Original document types (for backward compatibility)
            "purchase_contract": None,
            "payment_proof": None,
            "loan_approval": None,
            "inspection_report": None,
            "insurance_policy": None,
            "transfer_deed": None,
            # Enhanced document types for signing workflow
            "reservation_agreement": None,
            "proof_of_funds": None,
            "mortgage_pre_approval": None,
            "preliminary_contract": None,
            "deposit_payment_proof": None,
            "due_diligence_documents": None,
            "final_purchase_contract": None,
            "final_payment_proof": None,
            "notary_validation_certificate": None,
        },
        description="Dictionary of buying transaction documents"
    )

    # Digital signatures tracking - NEW
    document_signatures: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Digital signatures for each document type"
    )

    # Workflow phase tracking - NEW
    current_phase: str = Field(default="reservation", description="Current workflow phase")
    phase_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of phase transitions"
    )

    # Enhanced audit trail - NEW
    audit_trail: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Complete audit trail of all actions"
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


class DigitalSignature(BaseModel):
    """Digital signature model"""
    signature_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    signer_id: str = Field(..., description="ID of person who signed")
    signer_type: str = Field(..., description="Type: agent, buyer, notary")
    document_type: str = Field(..., description="Type of document signed")
    signature_hash: str = Field(..., description="Hash of signature data")
    timestamp: datetime = Field(default_factory=datetime.now)
    ip_address: Optional[str] = Field(None, description="IP address of signer")
    signature_method: str = Field(default="digital", description="Signature method")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional signature metadata")


# ===== BACKWARD COMPATIBILITY FUNCTIONS =====

def ensure_enhanced_fields(buying_obj: Buying) -> Buying:
    """
    Ensure buying object has all enhanced fields for backward compatibility
    Call this function whenever you load a buying transaction
    """
    # Add current_phase if missing
    if not hasattr(buying_obj, 'current_phase') or not buying_obj.current_phase:
        buying_obj.current_phase = "reservation"

    # Add document_signatures if missing
    if not hasattr(buying_obj, 'document_signatures'):
        buying_obj.document_signatures = {}

    # Add phase_history if missing
    if not hasattr(buying_obj, 'phase_history'):
        buying_obj.phase_history = []

    # Add audit_trail if missing
    if not hasattr(buying_obj, 'audit_trail'):
        buying_obj.audit_trail = []

    # Ensure all enhanced document types exist
    enhanced_doc_types = [
        "reservation_agreement", "proof_of_funds", "mortgage_pre_approval",
        "preliminary_contract", "deposit_payment_proof", "due_diligence_documents",
        "final_purchase_contract", "final_payment_proof", "notary_validation_certificate"
    ]

    for doc_type in enhanced_doc_types:
        if doc_type not in buying_obj.buying_documents:
            buying_obj.buying_documents[doc_type] = None

    return buying_obj


# ===== CORE HELPER FUNCTIONS =====

def add_document_to_buying(buying_obj: Buying, doc_type: str, document_id: str) -> Buying:
    """Add document ID to buying transaction's document dictionary"""
    # Ensure enhanced fields exist
    buying_obj = ensure_enhanced_fields(buying_obj)

    # Add document to the dictionary
    buying_obj.buying_documents[doc_type] = document_id

    # Initialize validation status for this document
    buying_obj.document_validation_status[doc_type] = {
        "document_id": document_id,
        "validation_status": False,
        "uploaded_by": None,
        "upload_date": datetime.now(),
        "validated_by": None,
        "validation_date": None,
        "validation_notes": "",
        "fully_signed": False,
        "signing_completed_date": None
    }

    # Add audit trail entry
    add_audit_entry(buying_obj, "document_uploaded", {
        "document_type": doc_type,
        "document_id": document_id
    }, "system")

    buying_obj.last_updated = datetime.now()
    return buying_obj


def create_buying_transaction(agent_id: str, buyer_id: str, property_id: str) -> Buying:
    """Create new buying transaction with enhanced fields"""
    transaction = Buying(
        agent_id=agent_id,
        buyer_id=buyer_id,
        property_id=property_id
    )

    # Ensure all enhanced fields are present
    return ensure_enhanced_fields(transaction)


def update_buying_status(buying_obj: Buying, new_status: str, notes: str = "") -> Buying:
    """Update buying transaction status"""
    buying_obj = ensure_enhanced_fields(buying_obj)

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

    # Add audit trail entry
    add_audit_entry(buying_obj, "status_changed", {
        "old_status": old_status,
        "new_status": new_status,
        "notes": notes
    }, "system")

    return buying_obj


def add_transaction_note(buying_obj: Buying, note: str, author_id: str, note_type: str = "general") -> Buying:
    """Add note to transaction communication log"""
    buying_obj = ensure_enhanced_fields(buying_obj)

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
    buying_obj = ensure_enhanced_fields(buying_obj)

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
    from gpp.interface.config.constants import MEETING_TYPES
    meeting_type_name = MEETING_TYPES.get(meeting['meeting_type'], meeting['meeting_type'])

    add_transaction_note(
        buying_obj,
        f"Meeting scheduled: {meeting_type_name} "
        f"on {meeting['scheduled_date'].strftime('%Y-%m-%d %H:%M')}",
        meeting_data.get("created_by", "system"),
        "meeting"
    )

    return buying_obj


def get_buying_progress(buying_obj: Buying) -> Dict[str, Any]:
    """Get progress information for buying transaction"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    total_docs = len([doc_id for doc_id in buying_obj.buying_documents.values() if doc_id])
    validated_docs = len([
        doc for doc in buying_obj.document_validation_status.values()
        if doc.get("validation_status", False)
    ])

    progress = (validated_docs / total_docs * 100) if total_docs > 0 else 0

    from gpp.interface.config.constants import TRANSACTION_STATUSES

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
        ]),
        "current_phase": buying_obj.current_phase,
        "signatures_completed": sum(1 for sigs in buying_obj.document_signatures.values() if sigs)
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
        # Ensure enhanced fields
        buying_obj = ensure_enhanced_fields(buying_obj)

        if user_type == "agent" and buying_obj.agent_id == user_id:
            relevant_transactions[buying_id] = buying_obj
        elif user_type == "buyer" and buying_obj.buyer_id == user_id:
            relevant_transactions[buying_id] = buying_obj
        elif user_type == "notary":
            # Notaries see all transactions that need validation
            if buying_obj.status in ["documents_pending", "under_review"]:
                relevant_transactions[buying_id] = buying_obj

    return relevant_transactions


# ===== ENHANCED SIGNING FUNCTIONS =====

def create_digital_signature(signer_id: str, signer_type: str, document_type: str,
                             document_content: str = "", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a digital signature"""
    # Create signature hash
    signature_data = f"{signer_id}:{signer_type}:{document_type}:{datetime.now().isoformat()}:{document_content}"
    signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()

    return {
        "signature_id": str(uuid.uuid4()),
        "signer_id": signer_id,
        "signer_type": signer_type,
        "document_type": document_type,
        "signature_hash": signature_hash,
        "timestamp": datetime.now(),
        "metadata": metadata or {}
    }


def can_user_sign_document(buying_obj: Buying, document_type: str,
                           user_id: str, user_type: str) -> tuple[bool, str]:
    """Check if user can sign a specific document"""
    # Import here to avoid circular imports
    try:
        from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES
    except ImportError:
        # Fallback if constants not available
        return False, "Document configuration not available"

    buying_obj = ensure_enhanced_fields(buying_obj)

    doc_config = ENHANCED_BUYING_DOCUMENT_TYPES.get(document_type)
    if not doc_config:
        return False, "Unknown document type"

    # Check if document exists and is uploaded
    if not buying_obj.buying_documents.get(document_type):
        return False, "Document not uploaded yet"

    # Check if document is validated (if required)
    validation_status = buying_obj.document_validation_status.get(document_type, {})
    if doc_config.get("validatable_by") and not validation_status.get("validation_status", False):
        return False, "Document not validated yet"

    # Check if user type can sign this document
    required_signers = doc_config.get("required_signers", [])
    if user_type not in required_signers:
        return False, f"User type '{user_type}' not authorized to sign this document"

    # Check if user already signed
    existing_signatures = buying_obj.document_signatures.get(document_type, [])
    if any(sig.get("signer_id") == user_id for sig in existing_signatures):
        return False, "Document already signed by this user"

    # Check signing order if specified
    signing_order = doc_config.get("signing_order", [])
    if signing_order:
        current_position = signing_order.index(user_type) if user_type in signing_order else -1
        if current_position > 0:
            # Check if previous signers have signed
            for i in range(current_position):
                previous_signer_type = signing_order[i]
                if not any(sig.get("signer_type") == previous_signer_type for sig in existing_signatures):
                    return False, f"Waiting for {previous_signer_type} to sign first"

    return True, "Can sign"


def sign_document(buying_obj: Buying, document_type: str, signer_id: str,
                  signer_type: str, document_content: str = "", metadata: Dict[str, Any] = None) -> tuple[bool, str]:
    """Sign a document digitally"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    # Check if user can sign
    can_sign, reason = can_user_sign_document(buying_obj, document_type, signer_id, signer_type)
    if not can_sign:
        return False, reason

    # Create digital signature
    signature = create_digital_signature(signer_id, signer_type, document_type, document_content, metadata)

    # Add signature to document
    if document_type not in buying_obj.document_signatures:
        buying_obj.document_signatures[document_type] = []

    buying_obj.document_signatures[document_type].append(signature)

    # Add audit trail entry
    add_audit_entry(buying_obj, "document_signed", {
        "document_type": document_type,
        "signer_id": signer_id,
        "signer_type": signer_type,
        "signature_id": signature["signature_id"]
    }, signer_id)

    # Add transaction note
    try:
        from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES
        doc_name = ENHANCED_BUYING_DOCUMENT_TYPES.get(document_type, {}).get("name", document_type)
    except ImportError:
        doc_name = document_type

    add_transaction_note(
        buying_obj,
        f"Document signed: {doc_name}",
        signer_id,
        "signature"
    )

    # Check if document is fully signed
    if is_document_fully_signed(buying_obj, document_type):
        # Mark document as fully signed
        if document_type in buying_obj.document_validation_status:
            buying_obj.document_validation_status[document_type]["fully_signed"] = True
            buying_obj.document_validation_status[document_type]["signing_completed_date"] = datetime.now()

        # Add completion note
        add_transaction_note(
            buying_obj,
            f"Document fully signed: {doc_name}",
            "system",
            "signature_complete"
        )

        # Check if phase can be advanced
        check_and_advance_phase(buying_obj)

    buying_obj.last_updated = datetime.now()
    return True, "Document signed successfully"


def is_document_fully_signed(buying_obj: Buying, document_type: str) -> bool:
    """Check if document has all required signatures"""
    try:
        from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES
    except ImportError:
        return False

    buying_obj = ensure_enhanced_fields(buying_obj)

    doc_config = ENHANCED_BUYING_DOCUMENT_TYPES.get(document_type)
    if not doc_config:
        return False

    required_signers = doc_config.get("required_signers", [])
    if not required_signers:
        return True  # No signatures required

    existing_signatures = buying_obj.document_signatures.get(document_type, [])
    signed_by_types = [sig.get("signer_type") for sig in existing_signatures]

    return all(signer_type in signed_by_types for signer_type in required_signers)


def get_document_signing_status(buying_obj: Buying, document_type: str) -> Dict[str, Any]:
    """Get detailed signing status for a document"""
    try:
        from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES
    except ImportError:
        # Fallback if constants not available
        return {
            "document_type": document_type,
            "document_name": document_type,
            "required_signers": [],
            "signed_by": [],
            "missing_signers": [],
            "fully_signed": True,
            "signatures": [],
            "signing_order": [],
            "next_signer": None
        }

    buying_obj = ensure_enhanced_fields(buying_obj)

    doc_config = ENHANCED_BUYING_DOCUMENT_TYPES.get(document_type, {})
    required_signers = doc_config.get("required_signers", [])
    existing_signatures = buying_obj.document_signatures.get(document_type, [])

    signed_by = [sig.get("signer_type") for sig in existing_signatures]
    missing_signers = [signer for signer in required_signers if signer not in signed_by]

    return {
        "document_type": document_type,
        "document_name": doc_config.get("name", document_type),
        "required_signers": required_signers,
        "signed_by": signed_by,
        "missing_signers": missing_signers,
        "fully_signed": len(missing_signers) == 0,
        "signatures": existing_signatures,
        "signing_order": doc_config.get("signing_order", []),
        "next_signer": missing_signers[0] if missing_signers else None
    }


def check_and_advance_phase(buying_obj: Buying) -> bool:
    """Check if current phase is complete and advance to next phase"""
    try:
        from gpp.interface.config.constants import ENHANCED_WORKFLOW_PHASES
    except ImportError:
        return False

    buying_obj = ensure_enhanced_fields(buying_obj)

    current_phase_config = ENHANCED_WORKFLOW_PHASES.get(buying_obj.current_phase, {})
    required_docs = current_phase_config.get("required_documents", [])

    # Check if all required documents for current phase are validated
    all_validated = True
    for doc_type in required_docs:
        if not buying_obj.buying_documents.get(doc_type):
            all_validated = False
            break

        validation_status = buying_obj.document_validation_status.get(doc_type, {})
        if not validation_status.get("validation_status", False):
            all_validated = False
            break

    # If all documents are validated, check if phase can advance
    if all_validated:
        # Check if signatures are also complete (if required)
        required_signatures = current_phase_config.get("required_signatures", [])
        signatures_complete = True

        for doc_type in required_signatures:
            if not is_document_fully_signed(buying_obj, doc_type):
                signatures_complete = False
                break

        # If both documents and signatures are complete, advance phase
        if signatures_complete:
            next_phase = current_phase_config.get("next_phase")
            if next_phase:
                advance_workflow_phase(buying_obj, next_phase, "system")
                return True

    return False


def advance_workflow_phase(buying_obj: Buying, new_phase: str, advanced_by: str) -> Buying:
    """Advance transaction to next workflow phase"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    old_phase = buying_obj.current_phase
    buying_obj.current_phase = new_phase
    buying_obj.last_updated = datetime.now()

    # Add phase change to history
    phase_change = {
        "from_phase": old_phase,
        "to_phase": new_phase,
        "advanced_by": advanced_by,
        "timestamp": datetime.now(),
        "automatic": advanced_by == "system"
    }
    buying_obj.phase_history.append(phase_change)

    # Add transaction note
    try:
        from gpp.interface.config.constants import ENHANCED_WORKFLOW_PHASES
        old_phase_name = ENHANCED_WORKFLOW_PHASES.get(old_phase, {}).get("name", old_phase)
        new_phase_name = ENHANCED_WORKFLOW_PHASES.get(new_phase, {}).get("name", new_phase)
    except ImportError:
        old_phase_name = old_phase
        new_phase_name = new_phase

    add_transaction_note(
        buying_obj,
        f"Phase advanced from {old_phase_name} to {new_phase_name}",
        advanced_by,
        "phase_complete"
    )

    # Add to audit trail
    add_audit_entry(buying_obj, "phase_advanced", {
        "old_phase": old_phase,
        "new_phase": new_phase,
        "advanced_by": advanced_by
    }, advanced_by)

    return buying_obj


def add_audit_entry(buying_obj: Buying, action: str, details: Dict[str, Any], user_id: str = "system") -> Buying:
    """Add entry to audit trail"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    audit_entry = {
        "audit_id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "action": action,
        "user_id": user_id,
        "details": details,
        "transaction_id": buying_obj.buying_id
    }

    buying_obj.audit_trail.append(audit_entry)
    return buying_obj


def get_current_phase_requirements(buying_obj: Buying) -> Dict[str, Any]:
    """Get requirements for current phase"""
    try:
        from gpp.interface.config.constants import ENHANCED_WORKFLOW_PHASES
    except ImportError:
        # Fallback if constants not available
        return {
            "phase_name": buying_obj.current_phase,
            "required_documents": [],
            "optional_documents": [],
            "required_signatures": [],
            "completion_trigger": "",
            "next_phase": ""
        }

    buying_obj = ensure_enhanced_fields(buying_obj)

    phase_config = ENHANCED_WORKFLOW_PHASES.get(buying_obj.current_phase, {})

    return {
        "phase_name": phase_config.get("name", buying_obj.current_phase),
        "required_documents": phase_config.get("required_documents", []),
        "optional_documents": phase_config.get("optional_documents", []),
        "required_signatures": phase_config.get("required_signatures", []),
        "completion_trigger": phase_config.get("completion_trigger", ""),
        "next_phase": phase_config.get("next_phase", "")
    }


# ===== ENHANCED VALIDATION FUNCTIONS =====

def validate_buying_document(buying_obj: Buying, doc_type: str, validator_id: str,
                             validation_status: bool, notes: str = "") -> Buying:
    """Enhanced validation function that properly updates progress"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    if doc_type in buying_obj.document_validation_status:
        # Update validation status
        buying_obj.document_validation_status[doc_type].update({
            "validation_status": validation_status,
            "validated_by": validator_id,
            "validation_date": datetime.now(),
            "validation_notes": notes
        })

        # Also update the actual document in the documents database
        try:
            from gpp.interface.utils.database import get_documents, save_document
            from gpp.classes.document import validate_document

            documents = get_documents()
            doc_id = buying_obj.buying_documents.get(doc_type)

            if doc_id and doc_id in documents:
                document = documents[doc_id]
                if validation_status:
                    # Validate the document
                    validated_doc = validate_document(document, validator_id)
                    save_document(validated_doc)
        except ImportError:
            pass  # Skip document database update if imports fail

        buying_obj.last_updated = datetime.now()

        # Add validation note
        status_text = "approved" if validation_status else "rejected"
        add_transaction_note(
            buying_obj,
            f"Document {doc_type.replace('_', ' ').title()} {status_text}. {notes}".strip(),
            validator_id,
            "validation"
        )

        # Add audit trail entry
        add_audit_entry(buying_obj, "document_validated", {
            "document_type": doc_type,
            "validation_status": validation_status,
            "validator_id": validator_id,
            "notes": notes
        }, validator_id)

        # Check if this document validation allows phase advancement
        check_and_advance_phase(buying_obj)

    return buying_obj


def get_enhanced_buying_progress(buying_obj: Buying) -> Dict[str, Any]:
    """Enhanced progress calculation with proper phase tracking"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    try:
        from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES, ENHANCED_WORKFLOW_PHASES

        # Calculate document progress
        total_docs = 0
        uploaded_docs = 0
        validated_docs = 0
        signed_docs = 0

        for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
            # Only count documents that are relevant to current phase or earlier
            doc_phase = doc_config.get("phase", "unknown")
            current_phase_order = ENHANCED_WORKFLOW_PHASES.get(buying_obj.current_phase, {}).get("order", 1)
            doc_phase_order = ENHANCED_WORKFLOW_PHASES.get(doc_phase, {}).get("order", 999)

            # Only count documents from current phase and earlier phases
            if doc_phase_order <= current_phase_order:
                total_docs += 1

                # Check if uploaded
                if buying_obj.buying_documents.get(doc_type):
                    uploaded_docs += 1

                    # Check if validated
                    validation_status = buying_obj.document_validation_status.get(doc_type, {})
                    if validation_status.get("validation_status", False):
                        validated_docs += 1

                    # Check if signed (if signatures required)
                    if doc_config.get("required_signers"):
                        if is_document_fully_signed(buying_obj, doc_type):
                            signed_docs += 1

        # Calculate phase progress
        phases = list(ENHANCED_WORKFLOW_PHASES.keys())
        current_phase_index = phases.index(buying_obj.current_phase) if buying_obj.current_phase in phases else 0
        phase_progress = (current_phase_index / len(phases)) * 100

        # Calculate overall progress
        if total_docs > 0:
            upload_progress = (uploaded_docs / total_docs) * 100
            validation_progress = (validated_docs / total_docs) * 100
            overall_progress = (validation_progress + phase_progress) / 2
        else:
            upload_progress = 0
            validation_progress = 0
            overall_progress = phase_progress

        return {
            "total_documents": total_docs,
            "uploaded_documents": uploaded_docs,
            "validated_documents": validated_docs,
            "signed_documents": signed_docs,
            "upload_progress": upload_progress,
            "validation_progress": validation_progress,
            "signing_progress": (signed_docs / max(1, total_docs)) * 100,
            "phase_progress": phase_progress,
            "overall_progress": overall_progress,
            "status": buying_obj.status,
            "current_phase": buying_obj.current_phase,
            "current_phase_name": ENHANCED_WORKFLOW_PHASES.get(buying_obj.current_phase, {}).get("name", buying_obj.current_phase),
            "last_updated": buying_obj.last_updated,
            "can_advance_phase": _can_current_phase_advance(buying_obj)
        }

    except ImportError:
        # Fallback to original progress calculation if constants not available
        return get_buying_progress(buying_obj)


def _can_current_phase_advance(buying_obj: Buying) -> bool:
    """Check if current phase can advance"""
    try:
        from gpp.interface.config.constants import ENHANCED_WORKFLOW_PHASES

        current_phase_config = ENHANCED_WORKFLOW_PHASES.get(buying_obj.current_phase, {})

        # Check required documents
        required_docs = current_phase_config.get("required_documents", [])
        for doc_type in required_docs:
            if not buying_obj.buying_documents.get(doc_type):
                return False

            validation_status = buying_obj.document_validation_status.get(doc_type, {})
            if not validation_status.get("validation_status", False):
                return False

        # Check required signatures
        required_signatures = current_phase_config.get("required_signatures", [])
        for doc_type in required_signatures:
            if not is_document_fully_signed(buying_obj, doc_type):
                return False

        return True

    except ImportError:
        return False


def bulk_validate_documents(buying_obj: Buying, doc_types: List[str], validator_id: str,
                           validation_status: bool, notes: str = "") -> Buying:
    """Validate multiple documents at once (useful for notaries)"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    validated_docs = []

    for doc_type in doc_types:
        if doc_type in buying_obj.document_validation_status:
            buying_obj = validate_buying_document(buying_obj, doc_type, validator_id, validation_status, notes)
            validated_docs.append(doc_type)

    # Add bulk validation note
    if validated_docs:
        status_text = "approved" if validation_status else "rejected"
        doc_names = [doc_type.replace('_', ' ').title() for doc_type in validated_docs]
        add_transaction_note(
            buying_obj,
            f"Bulk validation - {status_text}: {', '.join(doc_names)}. {notes}".strip(),
            validator_id,
            "validation"
        )

    return buying_obj


def force_phase_advancement(buying_obj: Buying, target_phase: str, advanced_by: str,
                           reason: str = "Manual advancement") -> Buying:
    """Force phase advancement (for admin/notary override)"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    # Add note about forced advancement
    add_transaction_note(
        buying_obj,
        f"Phase manually advanced to {target_phase}. Reason: {reason}",
        advanced_by,
        "phase_complete"
    )

    # Advance phase
    buying_obj = advance_workflow_phase(buying_obj, target_phase, advanced_by)

    return buying_obj


def get_user_dashboard_summary(buying_obj: Buying, user_id: str, user_type: str) -> Dict[str, Any]:
    """Get dashboard summary for specific user type"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    progress = get_enhanced_buying_progress(buying_obj)
    action_items = get_user_action_items(buying_obj, user_id, user_type)

    # Get recent activity
    recent_notes = buying_obj.transaction_notes[-5:] if buying_obj.transaction_notes else []

    # Get next actions
    next_actions = [item for item in action_items if item["priority"] == "high"][:3]

    return {
        "transaction_id": buying_obj.buying_id,
        "current_phase": buying_obj.current_phase,
        "current_phase_name": progress["current_phase_name"],
        "overall_progress": progress["overall_progress"],
        "validation_progress": progress["validation_progress"],
        "signing_progress": progress["signing_progress"],
        "status": buying_obj.status,
        "last_updated": buying_obj.last_updated,
        "action_items_count": len(action_items),
        "high_priority_actions": len(next_actions),
        "next_actions": next_actions,
        "recent_activity": recent_notes,
        "can_advance_phase": progress["can_advance_phase"]
    }


def get_user_action_items(buying_obj: Buying, user_id: str, user_type: str) -> List[Dict[str, Any]]:
    """Get list of action items for a specific user"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    try:
        from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES

        action_items = []

        for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
            # Check if user can upload this document
            if user_type in doc_config.get("uploadable_by", []):
                if not buying_obj.buying_documents.get(doc_type):
                    action_items.append({
                        "type": "upload",
                        "priority": "high" if doc_config.get("mandatory", False) else "medium",
                        "action": f"Upload {doc_config.get('name', doc_type)}",
                        "document_type": doc_type,
                        "description": f"Upload required document: {doc_config.get('name', doc_type)}"
                    })

            # Check if user can sign this document
            if user_type in doc_config.get("required_signers", []):
                if buying_obj.buying_documents.get(doc_type):
                    can_sign, reason = can_user_sign_document(buying_obj, doc_type, user_id, user_type)
                    if can_sign:
                        action_items.append({
                            "type": "sign",
                            "priority": "high",
                            "action": f"Sign {doc_config.get('name', doc_type)}",
                            "document_type": doc_type,
                            "description": f"Digital signature required for: {doc_config.get('name', doc_type)}"
                        })

            # Check if user can validate this document (notaries)
            if user_type in doc_config.get("validatable_by", []):
                if buying_obj.buying_documents.get(doc_type):
                    validation_status = buying_obj.document_validation_status.get(doc_type, {})
                    if not validation_status.get("validation_status", False):
                        action_items.append({
                            "type": "validate",
                            "priority": "high",
                            "action": f"Validate {doc_config.get('name', doc_type)}",
                            "document_type": doc_type,
                            "description": f"Review and validate: {doc_config.get('name', doc_type)}"
                        })

        # Sort by priority (high first)
        priority_order = {"high": 1, "medium": 2, "low": 3}
        action_items.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return action_items

    except ImportError:
        return []


def get_signing_progress_summary(buying_obj: Buying) -> Dict[str, Any]:
    """Get summary of signing progress across all documents"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    try:
        from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES

        total_signable = 0
        fully_signed = 0
        pending_by_user_type = {"buyer": 0, "agent": 0, "notary": 0}

        for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
            required_signers = doc_config.get("required_signers", [])

            if required_signers and buying_obj.buying_documents.get(doc_type):
                total_signable += 1

                if is_document_fully_signed(buying_obj, doc_type):
                    fully_signed += 1
                else:
                    # Count pending signatures by user type
                    existing_signatures = buying_obj.document_signatures.get(doc_type, [])
                    signed_by_types = [sig.get("signer_type") for sig in existing_signatures]

                    for signer_type in required_signers:
                        if signer_type not in signed_by_types:
                            pending_by_user_type[signer_type] += 1

        overall_progress = (fully_signed / total_signable * 100) if total_signable > 0 else 0

        return {
            "total_signable_documents": total_signable,
            "fully_signed_documents": fully_signed,
            "pending_signatures": sum(pending_by_user_type.values()),
            "user_pending_signatures": pending_by_user_type,
            "overall_progress": overall_progress
        }

    except ImportError:
        return {
            "total_signable_documents": 0,
            "fully_signed_documents": 0,
            "pending_signatures": 0,
            "user_pending_signatures": {},
            "overall_progress": 0
        }


def generate_transaction_summary(buying_obj: Buying) -> Dict[str, Any]:
    """Generate comprehensive transaction summary"""
    buying_obj = ensure_enhanced_fields(buying_obj)

    # Basic transaction info
    progress_info = get_buying_progress(buying_obj)
    signing_info = get_signing_progress_summary(buying_obj)

    # Phase information
    try:
        from gpp.interface.config.constants import ENHANCED_WORKFLOW_PHASES
        phase_info = ENHANCED_WORKFLOW_PHASES.get(buying_obj.current_phase, {})
        current_phase_name = phase_info.get("name", buying_obj.current_phase)
    except ImportError:
        current_phase_name = buying_obj.current_phase

    # Timeline info
    timeline_events = []
    timeline_events.extend([
        {
            "timestamp": note.get("timestamp", datetime.now()),
            "event": note.get("note", ""),
            "type": note.get("note_type", "general"),
            "author": note.get("author_id", "unknown")
        }
        for note in buying_obj.transaction_notes[-5:]  # Last 5 events
    ])

    # Recent signatures
    recent_signatures = []
    for doc_type, signatures in buying_obj.document_signatures.items():
        for sig in signatures[-3:]:  # Last 3 signatures per document
            recent_signatures.append({
                "document_type": doc_type,
                "signer_type": sig.get("signer_type"),
                "timestamp": sig.get("timestamp"),
                "signature_id": sig.get("signature_id")
            })

    # Sort recent signatures by timestamp
    recent_signatures.sort(key=lambda x: x.get("timestamp", datetime.now()), reverse=True)

    return {
        "transaction_id": buying_obj.buying_id,
        "property_id": buying_obj.property_id,
        "agent_id": buying_obj.agent_id,
        "buyer_id": buying_obj.buyer_id,
        "current_phase": buying_obj.current_phase,
        "current_phase_name": current_phase_name,
        "status": buying_obj.status,
        "created_date": buying_obj.created_date,
        "last_updated": buying_obj.last_updated,
        "final_price": buying_obj.final_price,
        "progress": progress_info,
        "signing_progress": signing_info,
        "recent_timeline": timeline_events,
        "recent_signatures": recent_signatures[:5],  # Last 5 signatures
        "total_notes": len(buying_obj.transaction_notes),
        "total_meetings": len(buying_obj.scheduled_meetings),
        "total_audit_entries": len(buying_obj.audit_trail)
    }


# ===== UTILITY FUNCTIONS FOR MIGRATION =====

def migrate_old_buying_transaction(old_buying_dict: Dict[str, Any]) -> Buying:
    """
    Migrate old buying transaction format to new enhanced format
    Use this when loading old transactions from database
    """
    # Create buying object from old data
    buying_obj = Buying(**old_buying_dict)

    # Ensure all enhanced fields are present
    buying_obj = ensure_enhanced_fields(buying_obj)

    return buying_obj


def get_workflow_phase_from_status(status: str) -> str:
    """
    Map old status to new workflow phase for migration
    """
    status_to_phase_mapping = {
        "pending": "reservation",
        "documents_pending": "financial_verification",
        "under_review": "preliminary_contract",
        "approved": "final_contract",
        "completed": "completed",
        "cancelled": "cancelled",
        "on_hold": "on_hold"
    }

    return status_to_phase_mapping.get(status, "reservation")


# ===== BACKWARD COMPATIBILITY WRAPPER FUNCTIONS =====

def ensure_buying_compatibility(func):
    """Decorator to ensure buying objects have enhanced fields"""

    def wrapper(*args, **kwargs):
        # Find Buying objects in arguments and ensure they have enhanced fields
        new_args = []
        for arg in args:
            if isinstance(arg, Buying):
                arg = ensure_enhanced_fields(arg)
            new_args.append(arg)

        new_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, Buying):
                value = ensure_enhanced_fields(value)
            new_kwargs[key] = value

        return func(*new_args, **new_kwargs)

    return wrapper


# Apply compatibility wrapper to key functions
add_document_to_buying = ensure_buying_compatibility(add_document_to_buying)
update_buying_status = ensure_buying_compatibility(update_buying_status)
add_transaction_note = ensure_buying_compatibility(add_transaction_note)
schedule_meeting = ensure_buying_compatibility(schedule_meeting)
validate_buying_document = ensure_buying_compatibility(validate_buying_document)
get_buying_progress = ensure_buying_compatibility(get_buying_progress)


# ===== DATABASE OPERATIONS =====

def save_buying_transaction(buying_obj: Buying):
    """Save buying transaction to database"""
    # Ensure enhanced fields before saving
    buying_obj = ensure_enhanced_fields(buying_obj)

    # Import here to avoid circular imports
    try:
        from gpp.interface.utils.database import load_data, save_data
        from gpp.interface.config.constants import BUYING_TRANSACTIONS_FILE

        transactions = load_data(BUYING_TRANSACTIONS_FILE)
        transactions[buying_obj.buying_id] = buying_obj.dict()
        save_data(BUYING_TRANSACTIONS_FILE, transactions)
    except ImportError:
        pass  # Skip database save if imports fail


def load_buying_transaction(buying_id: str) -> Optional[Buying]:
    """Load buying transaction from database"""
    try:
        from gpp.interface.utils.database import load_data
        from gpp.interface.config.constants import BUYING_TRANSACTIONS_FILE

        transactions = load_data(BUYING_TRANSACTIONS_FILE)
        if buying_id in transactions:
            buying_obj = Buying(**transactions[buying_id])
            return ensure_enhanced_fields(buying_obj)
    except ImportError:
        pass  # Skip database load if imports fail

    return None


def get_all_buying_transactions() -> Dict[str, Buying]:
    """Get all buying transactions from database"""
    try:
        from gpp.interface.utils.database import load_data
        from gpp.interface.config.constants import BUYING_TRANSACTIONS_FILE

        transactions_data = load_data(BUYING_TRANSACTIONS_FILE)
        transactions = {}

        for buying_id, buying_data in transactions_data.items():
            try:
                buying_obj = Buying(**buying_data)
                transactions[buying_id] = ensure_enhanced_fields(buying_obj)
            except Exception as e:
                # Log error but continue with other transactions
                print(f"Error loading transaction {buying_id}: {e}")

        return transactions
    except ImportError:
        return {}


# ===== INITIALIZATION FUNCTION =====

def initialize_enhanced_buying_system():
    """Initialize the enhanced buying system - call this once at startup"""
    print("Enhanced Buying System with Digital Signatures initialized")
    print("Features:")
    print("- Digital document signing workflow")
    print("- Multi-phase transaction management")
    print("- Comprehensive audit trail")
    print("- Backward compatibility with existing transactions")


if __name__ == "__main__":
    # For testing purposes
    initialize_enhanced_buying_system()

    # Create a test transaction
    test_transaction = create_buying_transaction("agent123", "buyer456", "property789")
    print(f"Created test transaction: {test_transaction.buying_id}")
    print(f"Current phase: {test_transaction.current_phase}")
    print(f"Enhanced fields present: {hasattr(test_transaction, 'document_signatures')}")