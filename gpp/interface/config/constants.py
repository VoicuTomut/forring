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
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")  # NEW: Chat storage

# File paths for different document types
DOCUMENT_PATHS = {
    "photos": "/photos/",
    "documents": "/documents/",
    "additional_docs": "/additional_docs/"
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