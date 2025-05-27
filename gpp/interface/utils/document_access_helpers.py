"""
Document Access Helper Functions
Provides utilities for managing document visibility and access based on user roles and transaction status
Integrates with existing constants and file structure
"""

from typing import Dict, List, Optional, Tuple
from gpp.classes.document import Document
from gpp.classes.property import Property
from gpp.classes.buying import Buying
from gpp.interface.utils.database import get_documents, get_properties
from gpp.interface.utils.buying_database import get_user_buying_transactions
from gpp.interface.config.constants import MANDATORY_DOCS, ADDITIONAL_DOC_CATEGORIES, BUYING_DOCUMENT_TYPES


def can_user_access_property_documents(user_id: str, user_type: str, property_id: str) -> Tuple[bool, str]:
    """
    Check if a user can access property documents based on their role and transaction status

    Returns:
        Tuple[bool, str]: (can_access, reason)
    """

    if user_type == "agent":
        # Agents can access documents for their own properties
        properties = get_properties()
        property_data = properties.get(property_id)
        if property_data and property_data.agent_id == user_id:
            return True, "Agent owns this property"
        return False, "Not your property"

    elif user_type == "notary":
        # Notaries can access documents for properties they're assigned to validate
        properties = get_properties()
        property_data = properties.get(property_id)
        if property_data and (property_data.notary_attached == user_id or user_id in property_data.attached_notarys_id):
            return True, "Notary assigned to this property"
        # Also allow access if there are active buying transactions needing validation
        buying_transactions = get_user_buying_transactions(user_id, "notary")
        for transaction in buying_transactions.values():
            if transaction.property_id == property_id and transaction.status in ["documents_pending", "under_review"]:
                return True, "Active transaction requiring validation"
        return False, "Not assigned to this property"

    elif user_type == "buyer":
        # Buyers can access documents for properties they have reserved/purchased
        buying_transactions = get_user_buying_transactions(user_id, "buyer")
        for transaction in buying_transactions.values():
            if transaction.property_id == property_id:
                return True, f"Active transaction ({transaction.status})"
        return False, "No active transaction for this property"

    return False, "Invalid user type"


def get_accessible_documents_for_user(user_id: str, user_type: str, property_id: str = None) -> Dict[
    str, List[Document]]:
    """
    Get all documents accessible to a user, optionally filtered by property

    Returns:
        Dict with categories: 'mandatory_docs', 'additional_docs', 'transaction_docs'
    """
    accessible_docs = {
        'mandatory_docs': [],
        'additional_docs': [],
        'transaction_docs': []
    }

    documents = get_documents()
    properties = get_properties()

    if property_id:
        # Check access for specific property
        can_access, reason = can_user_access_property_documents(user_id, user_type, property_id)
        if not can_access:
            return accessible_docs

        property_data = properties.get(property_id)
        if not property_data:
            return accessible_docs

        # Get mandatory documents
        for doc_id in property_data.mandatory_legal_docs.values():
            if doc_id and doc_id in documents:
                accessible_docs['mandatory_docs'].append(documents[doc_id])

        # Get additional documents
        for doc_list in property_data.additional_docs.values():
            for doc_id in doc_list:
                if doc_id in documents:
                    accessible_docs['additional_docs'].append(documents[doc_id])

        # Get transaction documents if buyer
        if user_type == "buyer":
            buying_transactions = get_user_buying_transactions(user_id, "buyer")
            for transaction in buying_transactions.values():
                if transaction.property_id == property_id:
                    for doc_id in transaction.buying_documents.values():
                        if doc_id and doc_id in documents:
                            accessible_docs['transaction_docs'].append(documents[doc_id])

    else:
        # Get all accessible documents for user
        if user_type == "buyer":
            buying_transactions = get_user_buying_transactions(user_id, "buyer")
            for transaction in buying_transactions.values():
                property_data = properties.get(transaction.property_id)
                if property_data:
                    # Mandatory docs
                    for doc_id in property_data.mandatory_legal_docs.values():
                        if doc_id and doc_id in documents:
                            accessible_docs['mandatory_docs'].append(documents[doc_id])

                    # Additional docs
                    for doc_list in property_data.additional_docs.values():
                        for doc_id in doc_list:
                            if doc_id in documents:
                                accessible_docs['additional_docs'].append(documents[doc_id])

                    # Transaction docs
                    for doc_id in transaction.buying_documents.values():
                        if doc_id and doc_id in documents:
                            accessible_docs['transaction_docs'].append(documents[doc_id])

        elif user_type == "agent":
            # Agent can access all documents for their properties
            for property_id, property_data in properties.items():
                if property_data.agent_id == user_id:
                    # Mandatory docs
                    for doc_id in property_data.mandatory_legal_docs.values():
                        if doc_id and doc_id in documents:
                            accessible_docs['mandatory_docs'].append(documents[doc_id])

                    # Additional docs
                    for doc_list in property_data.additional_docs.values():
                        for doc_id in doc_list:
                            if doc_id in documents:
                                accessible_docs['additional_docs'].append(documents[doc_id])

        elif user_type == "notary":
            # Notary can access documents for assigned properties and active transactions
            buying_transactions = get_user_buying_transactions(user_id, "notary")
            accessible_property_ids = set()

            # Properties assigned to notary
            for property_id, property_data in properties.items():
                if property_data.notary_attached == user_id or user_id in property_data.attached_notarys_id:
                    accessible_property_ids.add(property_id)

            # Properties with active transactions
            for transaction in buying_transactions.values():
                accessible_property_ids.add(transaction.property_id)

            # Get documents for accessible properties
            for property_id in accessible_property_ids:
                property_data = properties.get(property_id)
                if property_data:
                    # Mandatory docs
                    for doc_id in property_data.mandatory_legal_docs.values():
                        if doc_id and doc_id in documents:
                            accessible_docs['mandatory_docs'].append(documents[doc_id])

                    # Additional docs
                    for doc_list in property_data.additional_docs.values():
                        for doc_id in doc_list:
                            if doc_id in documents:
                                accessible_docs['additional_docs'].append(documents[doc_id])

    # Remove duplicates
    accessible_docs['mandatory_docs'] = list(
        {doc.document_id: doc for doc in accessible_docs['mandatory_docs']}.values())
    accessible_docs['additional_docs'] = list(
        {doc.document_id: doc for doc in accessible_docs['additional_docs']}.values())
    accessible_docs['transaction_docs'] = list(
        {doc.document_id: doc for doc in accessible_docs['transaction_docs']}.values())

    return accessible_docs


def get_property_document_summary(property_id: str, viewer_user_id: str, viewer_user_type: str) -> Dict[str, any]:
    """
    Get a summary of all documents for a property from a user's perspective
    """
    can_access, reason = can_user_access_property_documents(viewer_user_id, viewer_user_type, property_id)

    if not can_access:
        return {"accessible": False, "reason": reason}

    properties = get_properties()
    property_data = properties.get(property_id)

    if not property_data:
        return {"accessible": False, "reason": "Property not found"}

    documents = get_documents()
    summary = {
        "accessible": True,
        "property_title": property_data.title,
        "mandatory_documents": {},
        "additional_documents": {},
        "transaction_documents": {},
        "totals": {
            "mandatory_total": len(MANDATORY_DOCS),
            "mandatory_uploaded": 0,
            "mandatory_validated": 0,
            "additional_total": 0,
            "additional_uploaded": 0,
            "transaction_total": 0,
            "transaction_uploaded": 0,
            "transaction_validated": 0
        }
    }

    # Analyze mandatory documents
    for doc_type, doc_name in MANDATORY_DOCS.items():
        doc_id = property_data.mandatory_legal_docs.get(doc_type)
        doc_info = {
            "name": doc_name,
            "uploaded": False,
            "validated": False,
            "document_id": None,
            "upload_date": None,
            "validation_date": None
        }

        if doc_id and doc_id in documents:
            document = documents[doc_id]
            doc_info.update({
                "uploaded": True,
                "validated": document.validation_status,
                "document_id": doc_id,
                "upload_date": document.upload_date,
                "validation_date": document.validation_date
            })
            summary["totals"]["mandatory_uploaded"] += 1
            if document.validation_status:
                summary["totals"]["mandatory_validated"] += 1

        summary["mandatory_documents"][doc_type] = doc_info

    # Analyze additional documents
    for category, doc_ids in property_data.additional_docs.items():
        if category in ADDITIONAL_DOC_CATEGORIES and doc_ids:
            category_docs = []
            for doc_id in doc_ids:
                if doc_id in documents:
                    document = documents[doc_id]
                    category_docs.append({
                        "document_id": doc_id,
                        "name": document.document_name,
                        "upload_date": document.upload_date,
                        "validated": document.validation_status,
                        "validation_date": document.validation_date
                    })
                    summary["totals"]["additional_uploaded"] += 1

            if category_docs:
                summary["additional_documents"][category] = {
                    "category_name": ADDITIONAL_DOC_CATEGORIES[category],
                    "documents": category_docs
                }

    summary["totals"]["additional_total"] = summary["totals"]["additional_uploaded"]

    # Analyze transaction documents if buyer
    if viewer_user_type == "buyer":
        buying_transactions = get_user_buying_transactions(viewer_user_id, "buyer")
        for transaction in buying_transactions.values():
            if transaction.property_id == property_id:
                summary["totals"]["transaction_total"] = len(BUYING_DOCUMENT_TYPES)

                for doc_type, doc_name in BUYING_DOCUMENT_TYPES.items():
                    doc_id = transaction.buying_documents.get(doc_type)
                    doc_info = {
                        "name": doc_name,
                        "uploaded": False,
                        "validated": False,
                        "document_id": None,
                        "upload_date": None,
                        "validation_date": None,
                        "validation_notes": ""
                    }

                    if doc_id and doc_id in documents:
                        document = documents[doc_id]
                        validation_info = transaction.document_validation_status.get(doc_type, {})

                        doc_info.update({
                            "uploaded": True,
                            "validated": validation_info.get("validation_status", False),
                            "document_id": doc_id,
                            "upload_date": document.upload_date,
                            "validation_date": validation_info.get("validation_date"),
                            "validation_notes": validation_info.get("validation_notes", "")
                        })
                        summary["totals"]["transaction_uploaded"] += 1
                        if validation_info.get("validation_status", False):
                            summary["totals"]["transaction_validated"] += 1

                    summary["transaction_documents"][doc_type] = doc_info
                break

    return summary


def get_buyer_document_access_summary(buyer_id: str) -> Dict[str, any]:
    """
    Get a comprehensive summary of all documents accessible to a buyer
    """
    buying_transactions = get_user_buying_transactions(buyer_id, "buyer")

    if not buying_transactions:
        return {
            "has_access": False,
            "reason": "No active transactions",
            "transaction_count": 0,
            "properties": []
        }

    properties = get_properties()
    documents = get_documents()

    summary = {
        "has_access": True,
        "transaction_count": len(buying_transactions),
        "properties": [],
        "totals": {
            "total_documents": 0,
            "validated_documents": 0,
            "pending_documents": 0
        }
    }

    for transaction_id, transaction in buying_transactions.items():
        property_data = properties.get(transaction.property_id)
        if not property_data:
            continue

        property_summary = get_property_document_summary(
            transaction.property_id, buyer_id, "buyer"
        )

        if property_summary["accessible"]:
            property_info = {
                "transaction_id": transaction_id,
                "property_id": transaction.property_id,
                "property_title": property_data.title,
                "transaction_status": transaction.status,
                "last_updated": transaction.last_updated,
                "document_summary": property_summary
            }

            # Add to totals
            totals = property_summary["totals"]
            summary["totals"]["total_documents"] += (
                    totals["mandatory_uploaded"] +
                    totals["additional_uploaded"] +
                    totals["transaction_uploaded"]
            )
            summary["totals"]["validated_documents"] += (
                    totals["mandatory_validated"] +
                    totals["transaction_validated"]
            )

            summary["properties"].append(property_info)

    summary["totals"]["pending_documents"] = (
            summary["totals"]["total_documents"] -
            summary["totals"]["validated_documents"]
    )

    return summary


def format_document_access_status(user_id: str, user_type: str, property_id: str) -> str:
    """
    Get a formatted string describing document access status for display
    """
    can_access, reason = can_user_access_property_documents(user_id, user_type, property_id)

    if not can_access:
        return f"❌ No Access: {reason}"

    # Get document summary
    accessible_docs = get_accessible_documents_for_user(user_id, user_type, property_id)

    mandatory_count = len(accessible_docs['mandatory_docs'])
    additional_count = len(accessible_docs['additional_docs'])
    transaction_count = len(accessible_docs['transaction_docs'])

    total_docs = mandatory_count + additional_count + transaction_count

    if total_docs == 0:
        return "⚠️ Access Granted - No Documents Available"

    # Count validated documents
    validated_count = sum(1 for doc in accessible_docs['mandatory_docs'] if doc.validation_status)
    validated_count += sum(1 for doc in accessible_docs['additional_docs'] if doc.validation_status)
    validated_count += sum(1 for doc in accessible_docs['transaction_docs'] if doc.validation_status)

    if validated_count == total_docs:
        return f"✅ Full Access - {total_docs} Documents (All Validated)"
    elif validated_count > 0:
        return f"🟡 Partial Access - {total_docs} Documents ({validated_count} Validated)"
    else:
        return f"⏳ Access Granted - {total_docs} Documents (Validation Pending)"


# Utility functions for UI components
def get_document_type_icon(doc_type: str, category: str = None) -> str:
    """Get appropriate icon for document type"""

    # Mandatory document icons
    mandatory_icons = {
        "title_deed": "📜",
        "land_registry_extract": "🏛️",
        "building_permit": "🏗️",
        "habitation_certificate": "🏠",
        "mortgage_lien_certificate": "💰",
        "seller_id_document": "🆔",
        "marital_status_documents": "💑",
        "power_of_attorney": "⚖️",
        "litigation_certificate": "📋"
    }

    # Transaction document icons
    transaction_icons = {
        "purchase_contract": "📋",
        "payment_proof": "💳",
        "loan_approval": "🏦",
        "inspection_report": "🔍",
        "insurance_policy": "🛡️",
        "transfer_deed": "📜"
    }

    # Additional document category icons
    additional_icons = {
        "supplementary_documents": "📋",
        "corrections": "✏️",
        "clarifications": "💡",
        "agent_notes": "📝",
        "updated_photos": "📸",
        "floor_plans": "🗺️",
        "certificates": "🏆",
        "correspondence": "📧",
        "other": "📎"
    }

    if doc_type in mandatory_icons:
        return mandatory_icons[doc_type]
    elif doc_type in transaction_icons:
        return transaction_icons[doc_type]
    elif category and category in additional_icons:
        return additional_icons[category]
    else:
        return "📄"


def get_validation_status_display(document: Document, validation_info: Dict = None) -> Dict[str, str]:
    """Get validation status display information"""

    if validation_info:
        # For transaction documents with detailed validation info
        is_validated = validation_info.get("validation_status", False)
        validation_notes = validation_info.get("validation_notes", "")
        validation_date = validation_info.get("validation_date")

        if is_validated:
            status = {
                "icon": "✅",
                "text": "Validated",
                "color": "success",
                "details": f"Validated on {validation_date.strftime('%Y-%m-%d %H:%M')}" if validation_date else "Validated"
            }
            if validation_notes:
                status["details"] += f" - {validation_notes}"
        else:
            status = {
                "icon": "⏳",
                "text": "Pending Validation",
                "color": "warning",
                "details": "Awaiting notary validation"
            }
            if validation_notes:
                status["details"] += f" - {validation_notes}"
    else:
        # For regular documents
        if document.validation_status:
            status = {
                "icon": "✅",
                "text": "Validated",
                "color": "success",
                "details": f"Validated on {document.validation_date.strftime('%Y-%m-%d %H:%M')}" if document.validation_date else "Validated"
            }
        else:
            status = {
                "icon": "⏳",
                "text": "Pending Validation",
                "color": "warning",
                "details": "Awaiting notary validation"
            }

    return status


def check_document_upload_permissions(user_id: str, user_type: str, property_id: str = None,
                                      transaction_id: str = None) -> Dict[str, bool]:
    """
    Check what types of documents a user can upload
    """
    permissions = {
        "can_upload_mandatory": False,
        "can_upload_additional": False,
        "can_upload_transaction": False,
        "can_replace_documents": False
    }

    if user_type == "agent":
        # Agents can upload all property-related documents for their properties
        if property_id:
            properties = get_properties()
            property_data = properties.get(property_id)
            if property_data and property_data.agent_id == user_id:
                permissions["can_upload_mandatory"] = True
                permissions["can_upload_additional"] = True
                permissions["can_replace_documents"] = True

    elif user_type == "buyer":
        # Buyers can upload transaction documents for their active transactions
        if transaction_id:
            buying_transactions = get_user_buying_transactions(user_id, "buyer")
            if transaction_id in buying_transactions:
                transaction = buying_transactions[transaction_id]
                if transaction.status in ["pending", "documents_pending", "under_review"]:
                    permissions["can_upload_transaction"] = True

    elif user_type == "notary":
        # Notaries generally don't upload documents, but can validate them
        # This could be extended if notaries need to upload validation reports
        pass

    return permissions


# Export the main functions
__all__ = [
    'can_user_access_property_documents',
    'get_accessible_documents_for_user',
    'get_property_document_summary',
    'get_buyer_document_access_summary',
    'format_document_access_status',
    'get_document_type_icon',
    'get_validation_status_display',
    'check_document_upload_permissions'
]