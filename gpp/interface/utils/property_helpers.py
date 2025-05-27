"""
Property helper functions and utilities
"""

from typing import Dict, Any, List
from gpp.classes.property import Property, get_property_additional_docs_count, get_property_recent_activity
from gpp.classes.document import Document
from gpp.interface.utils.database import get_properties, get_documents


def get_property_validation_progress(property_id: str) -> Dict[str, Any]:
    """Get validation progress for a property"""
    properties = get_properties()
    documents = get_documents()

    if property_id not in properties:
        return {"validated": 0, "total": 0, "progress": 0.0}

    prop_data = properties[property_id]
    doc_ids = prop_data.mandatory_legal_docs

    total_docs = len([doc_id for doc_id in doc_ids.values() if doc_id])
    validated_docs = 0

    for doc_id in doc_ids.values():
        if doc_id and doc_id in documents and documents[doc_id].validation_status:
            validated_docs += 1

    progress = validated_docs / total_docs if total_docs > 0 else 0

    return {
        "validated": validated_docs,
        "total": total_docs,
        "progress": progress
    }


def get_agent_properties(agent_id: str) -> Dict[str, Property]:
    """Get all properties for a specific agent"""
    properties = get_properties()
    return {k: v for k, v in properties.items() if v.agent_id == agent_id}


def get_pending_validation_properties() -> Dict[str, Property]:
    """Get properties pending validation"""
    properties = get_properties()
    return {k: v for k, v in properties.items()
            if v.looking_for_notary and not v.notary_attached}


def get_validated_properties() -> Dict[str, Property]:
    """Get fully validated properties available to buyers"""
    properties = get_properties()
    validated_properties = {}

    for prop_id, prop_data in properties.items():
        # Check if all mandatory documents are validated
        progress = get_property_validation_progress(prop_id)
        if progress['validated'] == progress['total'] and progress['total'] > 0:
            # Also check if notary is attached (property was approved)
            if prop_data.notary_attached:
                validated_properties[prop_id] = prop_data

    return validated_properties


def get_property_photos(property_obj: Property) -> List[Document]:
    """Get all photo documents for a property"""
    documents = get_documents()
    return [doc for doc_id, doc in documents.items()
            if doc_id in property_obj.document_ids
            and doc.document_name.startswith("Property Photo")]


def format_timestamp(timestamp) -> str:
    """Format timestamp for display"""
    if isinstance(timestamp, str):
        return timestamp[:16]
    else:
        return timestamp.strftime('%Y-%m-%d %H:%M')