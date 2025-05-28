"""
Configuration and Constants for GPP Platform
"""

import os

# App Configuration
APP_CONFIG = {
    "page_title": "GPP - Global Property Platform",
    "page_icon": "🏠",
    "layout": "wide"
}

# Data Directory Configuration
DATA_DIR = "data"
PROPERTIES_FILE = os.path.join(DATA_DIR, "properties.json")
DOCUMENTS_FILE = os.path.join(DATA_DIR, "documents.json")
AGENTS_FILE = os.path.join(DATA_DIR, "agents.json")
BUYERS_FILE = os.path.join(DATA_DIR, "buyers.json")
NOTARIES_FILE = os.path.join(DATA_DIR, "notaries.json")
BUYING_FILE = os.path.join(DATA_DIR, "buying.json")
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")  # Chat storage

# NEW: Add buying transactions file
BUYING_TRANSACTIONS_FILE = os.path.join(DATA_DIR, "buying_transactions.json")

# File paths for different document types
DOCUMENT_PATHS = {
    "photos": "/photos/",
    "documents": "/documents/",
    "additional_docs": "/additional_docs/",
    "buying_documents": "/buying_documents/"  # NEW: Buying documents path
}

# Mandatory legal documents configuration
MANDATORY_DOCS = {
    "title_deed": "Title Deed / Property Ownership Document",
    "land_registry_extract": "Land Registry Extract",
    "building_permit": "Building Permit",
   # "habitation_certificate": "Habitation Certificate",
   # "mortgage_lien_certificate": "Mortgage / Lien Certificate",
   # "seller_id_document": "Seller's ID Document",
   # "marital_status_documents": "Marital Status Documents",
   # "power_of_attorney": "Power of Attorney",
   # "litigation_certificate": "Litigation Certificate"
}

# Additional document categories
ADDITIONAL_DOC_CATEGORIES = {
    "supplementary_documents": "📋 Supplementary Legal Documents",
    "corrections": "🔧 Document Corrections/Updates",
    "clarifications": "💡 Clarification Documents",
    "agent_notes": "📝 Agent Notes & Explanations",
    "updated_photos": "📸 Additional/Updated Photos",
    "floor_plans": "📐 Floor Plans & Blueprints",
    "certificates": "🏆 Additional Certificates",
    "correspondence": "✉️ Email Exchanges & Letters",
    "other": "📁 Other Documents"
}

# File upload configurations
ALLOWED_IMAGE_TYPES = ['jpg', 'jpeg', 'png']
ALLOWED_DOCUMENT_TYPES = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx']
ALLOWED_PHOTO_TYPES = ['jpg', 'jpeg', 'png']

# UI Configuration
MAX_PHOTOS_PREVIEW = 4
MAX_RECENT_ACTIVITY = 20
MAX_RECENT_NOTES = 5

# ========== BUYING SYSTEM CONSTANTS ==========

# Buying transaction document types
BUYING_DOCUMENT_TYPES = {
    "purchase_contract": "Purchase Contract",
    "payment_proof": "Payment Verification",
    "loan_approval": "Bank Loan Approval",
    "inspection_report": "Property Inspection Report",
    "insurance_policy": "Property Insurance Policy",
    "transfer_deed": "Property Transfer Deed"
}

# Meeting types for buying transactions
MEETING_TYPES = {
    "property_viewing": "Property Viewing",
    "contract_discussion": "Contract Discussion",
    "final_signing": "Final Contract Signing",
    "inspection_meeting": "Property Inspection Meeting",
    "closing_meeting": "Transaction Closing Meeting",
    "general_discussion": "General Discussion"
}

# Transaction statuses
TRANSACTION_STATUSES = {
    "pending": "🟡 Pending - Initial Interest",
    "documents_pending": "📄 Documents Pending",
    "under_review": "🔍 Under Review",
    "approved": "✅ Approved - Ready to Close",
    "completed": "🎉 Transaction Completed",
    "cancelled": "❌ Transaction Cancelled",
    "on_hold": "⏸️ On Hold"
}

# NEW: Meeting statuses
MEETING_STATUSES = {
    "scheduled": "📅 Scheduled",
    "in_progress": "🔄 In Progress",
    "completed": "✅ Completed",
    "cancelled": "❌ Cancelled",
    "rescheduled": "📅 Rescheduled"
}

# NEW: Note types for transaction communication
TRANSACTION_NOTE_TYPES = {
    "general": "💬 General Note",
    "document": "📄 Document Related",
    "meeting": "📅 Meeting Related",
    "urgent": "⚠️ Urgent",
    "system": "🤖 System Generated",
    "validation": "✅ Validation Note",
    "initial_offer": "💰 Initial Offer",
    "signature": "✍️ Document Signature",
    "signature_complete": "🎉 Signature Complete",
    "phase_complete": "🏆 Phase Complete",
    "key_handover": "🔑 Key Handover",
    "document_upload": "📤 Document Upload"
}

# NEW: File storage directories (absolute paths)
STORAGE_DIRECTORIES = {
    "documents": os.path.join(DATA_DIR, "files", "documents"),
    "photos": os.path.join(DATA_DIR, "files", "photos"),
    "additional_docs": os.path.join(DATA_DIR, "files", "additional_docs"),
    "buying_documents": os.path.join(DATA_DIR, "files", "buying_documents")
}

# NEW: Progress tracking thresholds
PROGRESS_THRESHOLDS = {
    "property_validation": {
        "low": 30,    # 0-30% - Red
        "medium": 70, # 31-70% - Yellow
        "high": 100   # 71-100% - Green
    },
    "buying_transaction": {
        "low": 25,    # 0-25% - Red
        "medium": 75, # 26-75% - Yellow
        "high": 100   # 76-100% - Green
    }
}

# ========== ENHANCED DOCUMENT SIGNING CONSTANTS ==========

# Document signing statuses
DOCUMENT_SIGNING_STATUSES = {
    "not_uploaded": "❌ Not Uploaded",
    "uploaded": "📄 Uploaded",
    "validated": "✅ Validated",
    "ready_for_signing": "✍️ Ready for Signing",
    "partially_signed": "🔄 Partially Signed",
    "fully_signed": "🎉 Fully Signed"
}

# Signature types
DIGITAL_SIGNATURE_TYPES = {
    "agent": "🏢 Agent Signature",
    "buyer": "💰 Buyer Signature",
    "notary": "⚖️ Notary Signature"
}

# Phase completion messages
PHASE_COMPLETION_MESSAGES = {
    "reservation": "🏠 Property successfully reserved!",
    "financial_verification": "💰 Financial documents verified!",
    "preliminary_contract": "📋 Preliminary contract signed!",
    "due_diligence": "🔍 Due diligence completed!",
    "final_contract": "✍️ Final contract signed!",
    "final_payment": "💳 Final payment processed!",
    "completed": "🔑 Keys are on the way!"
}

# NEW: Workflow phase statuses for enhanced signing system
WORKFLOW_PHASE_STATUSES = {
    "not_started": "⚪ Not Started",
    "in_progress": "🔄 In Progress",
    "completed": "✅ Completed",
    "blocked": "🚫 Blocked"
}

# NEW: Document workflow phases
DOCUMENT_WORKFLOW_PHASES = {
    "reservation": {
        "name": "🏠 Property Reservation",
        "order": 1,
        "required_roles": ["agent", "buyer"],
        "description": "Initial property reservation and agreement"
    },
    "financial_verification": {
        "name": "💰 Financial Verification",
        "order": 2,
        "required_roles": ["buyer", "notary"],
        "description": "Buyer financial capability verification"
    },
    "preliminary_contract": {
        "name": "📋 Preliminary Contract",
        "order": 3,
        "required_roles": ["agent", "buyer", "notary"],
        "description": "Initial contract and deposit agreement"
    },
    "due_diligence": {
        "name": "🔍 Due Diligence",
        "order": 4,
        "required_roles": ["buyer", "notary"],
        "description": "Final property and financing checks"
    },
    "final_contract": {
        "name": "✍️ Final Contract",
        "order": 5,
        "required_roles": ["agent", "buyer", "notary"],
        "description": "Final purchase agreement execution"
    },
    "final_payment": {
        "name": "💳 Final Payment",
        "order": 6,
        "required_roles": ["buyer", "notary"],
        "description": "Final payment and legal completion"
    }
}

# NEW: Signature validation rules
SIGNATURE_VALIDATION_RULES = {
    "min_signature_time": 30,  # Minimum seconds between viewing and signing
    "require_document_view": True,  # Must view document before signing
    "allow_bulk_signing": False,  # Prevent bulk signing without individual review
    "signature_timeout": 3600,  # Seconds before signature session expires
}

# NEW: Enhanced file type validation
ENHANCED_FILE_VALIDATION = {
    "max_file_size_mb": 50,  # Maximum file size in MB
    "allowed_extensions": {
        "documents": ['.pdf', '.doc', '.docx', '.txt'],
        "images": ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
        "spreadsheets": ['.xls', '.xlsx', '.csv'],
        "presentations": ['.ppt', '.pptx']
    },
    "virus_scan_required": False,  # Enable when antivirus integration available
    "watermark_required": False   # Enable when watermarking feature available
}

# NEW: User role permissions for document operations
DOCUMENT_OPERATION_PERMISSIONS = {
    "agent": {
        "can_upload": ["reservation_agreement", "purchase_contract", "property_disclosure"],
        "can_sign": ["reservation_agreement", "preliminary_contract", "final_purchase_contract"],
        "can_validate": [],
        "can_view_all": True
    },
    "buyer": {
        "can_upload": ["proof_of_funds", "deposit_payment_proof", "due_diligence_documents", "final_payment_proof"],
        "can_sign": ["reservation_agreement", "preliminary_contract", "final_purchase_contract"],
        "can_validate": [],
        "can_view_all": False  # Only own transaction documents
    },
    "notary": {
        "can_upload": ["preliminary_contract", "final_purchase_contract", "notary_validation_certificate"],
        "can_sign": ["preliminary_contract", "final_purchase_contract", "notary_validation_certificate"],
        "can_validate": "all",  # Can validate any document
        "can_view_all": True
    }
}

# NEW: Notification triggers for enhanced system
NOTIFICATION_TRIGGERS = {
    "document_uploaded": {
        "notify_roles": ["notary"],
        "message_template": "New document uploaded for validation: {document_name}"
    },
    "document_validated": {
        "notify_roles": ["agent", "buyer"],
        "message_template": "Document validated: {document_name}"
    },
    "signature_required": {
        "notify_roles": ["signer"],
        "message_template": "Your signature required on: {document_name}"
    },
    "phase_completed": {
        "notify_roles": ["agent", "buyer", "notary"],
        "message_template": "Phase completed: {phase_name}"
    },
    "transaction_completed": {
        "notify_roles": ["agent", "buyer"],
        "message_template": "🔑 Transaction completed! Keys are on the way!"
    }
}

# NEW: Audit trail configuration
AUDIT_TRAIL_CONFIG = {
    "track_document_views": True,
    "track_signature_attempts": True,
    "track_upload_attempts": True,
    "retention_days": 2555,  # 7 years for legal compliance
    "export_formats": ["json", "csv", "pdf"],
    "required_fields": [
        "timestamp", "user_id", "user_type", "action",
        "document_id", "transaction_id", "ip_address"
    ]
}

# NEW: Integration endpoints (for future API integrations)
INTEGRATION_ENDPOINTS = {
    "notary_services": {
        "enabled": False,
        "base_url": "",
        "api_key": "",
        "supported_operations": ["document_validation", "digital_notarization"]
    },
    "payment_gateways": {
        "enabled": False,
        "providers": ["stripe", "paypal", "bank_transfer"],
        "webhook_endpoints": {
            "payment_success": "/webhooks/payment/success",
            "payment_failed": "/webhooks/payment/failed"
        }
    },
    "document_storage": {
        "enabled": False,
        "provider": "local",  # Options: "local", "aws_s3", "azure_blob"
        "encryption_enabled": True,
        "backup_enabled": True
    }

}

# ===== ADD THESE TO YOUR EXISTING constants.py FILE =====

# Enhanced document types with complete signing workflow
ENHANCED_BUYING_DOCUMENT_TYPES = {
    # Phase 1: Reservation (Auto-generated after payment)
    "reservation_agreement": {
        "name": "🏠 Reservation Agreement",
        "phase": "reservation",
        "required_signers": ["buyer", "agent"],
        "signing_order": ["buyer", "agent"],
        "auto_generated": True,
        "uploadable_by": [],
        "validatable_by": ["notary"]
    },

    # Phase 2: Financial Verification
    "proof_of_funds": {
        "name": "💰 Proof of Funds",
        "phase": "financial_verification",
        "required_signers": [],
        "uploadable_by": ["buyer"],
        "validatable_by": ["notary"],
        "mandatory": True
    },
    "mortgage_pre_approval": {
        "name": "🏦 Mortgage Pre-Approval",
        "phase": "financial_verification",
        "required_signers": [],
        "uploadable_by": ["buyer"],
        "validatable_by": ["notary"],
        "mandatory": False
    },

    # Phase 3: Preliminary Contract
    "preliminary_contract": {
        "name": "📋 Preliminary Contract",
        "phase": "preliminary_contract",
        "required_signers": ["notary", "buyer", "agent"],
        "signing_order": ["notary", "buyer", "agent"],
        "auto_generated": True,
        "generated_by": "notary",
        "uploadable_by": ["notary"],
        "validatable_by": ["notary"]
    },
    "deposit_payment_proof": {
        "name": "💳 Deposit Payment Proof",
        "phase": "preliminary_contract",
        "required_signers": [],
        "uploadable_by": ["buyer"],
        "validatable_by": ["notary"],
        "mandatory": True
    },

    # Phase 4: Due Diligence
    "due_diligence_documents": {
        "name": "🔍 Due Diligence Documents",
        "phase": "due_diligence",
        "required_signers": [],
        "uploadable_by": ["buyer"],
        "validatable_by": ["notary"],
        "mandatory": True
    },

    # Phase 5: Final Contract
    "final_purchase_contract": {
        "name": "✍️ Final Purchase Contract",
        "phase": "final_contract",
        "required_signers": ["notary", "buyer", "agent"],
        "signing_order": ["notary", "buyer", "agent"],
        "auto_generated": True,
        "generated_by": "notary",
        "uploadable_by": ["notary"],
        "validatable_by": ["notary"]
    },

    # Phase 6: Final Payment
    "final_payment_proof": {
        "name": "💸 Final Payment Proof",
        "phase": "final_payment",
        "required_signers": [],
        "uploadable_by": ["buyer"],
        "validatable_by": ["notary"],
        "mandatory": True
    },
    "notary_validation_certificate": {
        "name": "⚖️ Notary Validation Certificate",
        "phase": "final_payment",
        "required_signers": ["notary"],
        "signing_order": ["notary"],
        "auto_generated": True,
        "generated_by": "notary",
        "uploadable_by": ["notary"],
        "validatable_by": ["notary"]
    }
}

# Enhanced workflow phases with detailed requirements
ENHANCED_WORKFLOW_PHASES = {
    "reservation": {
        "name": "🏠 Property Reservation",
        "order": 1,
        "required_documents": ["reservation_agreement"],
        "required_signatures": ["reservation_agreement"],
        "completion_trigger": "all_signatures_complete",
        "next_phase": "financial_verification",
        "completion_message": "🏠 Property successfully reserved!"
    },
    "financial_verification": {
        "name": "💰 Financial Verification",
        "order": 2,
        "required_documents": ["proof_of_funds"],
        "optional_documents": ["mortgage_pre_approval"],
        "completion_trigger": "all_documents_validated",
        "next_phase": "preliminary_contract",
        "completion_message": "💰 Financial documents verified!"
    },
    "preliminary_contract": {
        "name": "📋 Preliminary Contract",
        "order": 3,
        "required_documents": ["preliminary_contract", "deposit_payment_proof"],
        "required_signatures": ["preliminary_contract"],
        "completion_trigger": "all_signatures_and_validation_complete",
        "next_phase": "due_diligence",
        "completion_message": "📋 Preliminary contract signed!"
    },
    "due_diligence": {
        "name": "🔍 Due Diligence",
        "order": 4,
        "required_documents": ["due_diligence_documents"],
        "completion_trigger": "all_documents_validated",
        "next_phase": "final_contract",
        "completion_message": "🔍 Due diligence completed!"
    },
    "final_contract": {
        "name": "✍️ Final Contract",
        "order": 5,
        "required_documents": ["final_purchase_contract"],
        "required_signatures": ["final_purchase_contract"],
        "completion_trigger": "all_signatures_complete",
        "next_phase": "final_payment",
        "completion_message": "✍️ Final contract signed!"
    },
    "final_payment": {
        "name": "💳 Final Payment",
        "order": 6,
        "required_documents": ["final_payment_proof", "notary_validation_certificate"],
        "required_signatures": ["notary_validation_certificate"],
        "completion_trigger": "all_documents_validated_and_signed",
        "next_phase": "completed",
        "completion_message": "💳 Final payment processed!"
    },
    "completed": {
        "name": "🔑 Key Handover",
        "order": 7,
        "completion_message": "🔑 Transaction completed! Keys are on the way!"
    }
}

# Signature button styles and messages
SIGNATURE_BUTTON_STYLES = {
    "ready_to_sign": {
        "style": "primary",
        "icon": "✍️",
        "text": "Sign Document",
        "color": "green"
    },
    "waiting_for_others": {
        "style": "secondary",
        "icon": "⏳",
        "text": "Waiting for Others",
        "color": "orange"
    },
    "already_signed": {
        "style": "secondary",
        "icon": "✅",
        "text": "Already Signed",
        "color": "gray"
    },
    "cannot_sign": {
        "style": "secondary",
        "icon": "🚫",
        "text": "Cannot Sign",
        "color": "red"
    }
}

# Phase progression messages
PHASE_PROGRESSION_MESSAGES = {
    "reservation_complete": "🏠 Property reserved! Next: Upload financial documents",
    "financial_verification_complete": "💰 Finances verified! Next: Preliminary contract",
    "preliminary_contract_complete": "📋 Preliminary contract signed! Next: Due diligence",
    "due_diligence_complete": "🔍 Due diligence complete! Next: Final contract",
    "final_contract_complete": "✍️ Final contract signed! Next: Final payment",
    "final_payment_complete": "💳 Payment complete! Next: Key handover",
    "transaction_complete": "🔑 Transaction complete! Welcome to your new property!"
}