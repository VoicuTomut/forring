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
    "initial_offer": "💰 Initial Offer"
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