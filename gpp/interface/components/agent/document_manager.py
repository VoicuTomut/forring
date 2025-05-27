"""
Document management interface for agents
"""

import streamlit as st
from datetime import datetime

from gpp.classes.agent import Agent
from gpp.classes.property import (
    Property, add_additional_document_to_property, replace_mandatory_document,
    add_agent_note_to_property, get_property_additional_docs_count, get_property_recent_activity
)
from gpp.classes.document import Document
from gpp.interface.utils.database import get_properties, save_property, get_documents, save_document
from gpp.interface.utils.property_helpers import get_property_validation_progress, format_timestamp
from gpp.interface.config.constants import ADDITIONAL_DOC_CATEGORIES, MANDATORY_DOCS, ALLOWED_DOCUMENT_TYPES, DOCUMENT_PATHS


def manage_additional_documents(current_agent: Agent):
    """Main interface for managing additional documents"""
    st.subheader("📎 Manage Additional Documents")

    properties = get_properties()
    agent_properties = {k: v for k, v in properties.items()
                        if k in current_agent.agent_active_prop_list}

    if not agent_properties:
        st.info("No properties to manage. Add a property first.")
        return

    # Property selection
    selected_property_id = _get_selected_property(agent_properties)
    if not selected_property_id:
        return

    selected_property = agent_properties[selected_property_id]
    _render_property_overview(selected_property_id, selected_property)

    # Document management tabs
    _render_document_management_tabs(selected_property, current_agent)


def _get_selected_property(agent_properties):
    """Handle property selection logic"""
    if 'manage_property_id' in st.session_state and st.session_state['manage_property_id'] in agent_properties:
        return st.session_state['manage_property_id']
    else:
        property_options = {f"{prop.title} - {prop.city}": prop_id
                            for prop_id, prop in agent_properties.items()}

        if not property_options:
            st.info("No properties available for document management.")
            return None

        selected_title = st.selectbox("Select Property:", options=list(property_options.keys()))
        return property_options[selected_title]


def _render_property_overview(property_id: str, selected_property: Property):
    """Render property overview section"""
    st.write(f"**Managing Documents for:** {selected_property.title}")

    # Show property status
    col1, col2, col3 = st.columns(3)
    with col1:
        validation_progress = get_property_validation_progress(property_id)
        st.metric("Validation Progress", f"{validation_progress['validated']}/{validation_progress['total']}")

    with col2:
        additional_count = sum(get_property_additional_docs_count(selected_property).values())
        st.metric("Additional Documents", additional_count)

    with col3:
        if selected_property.looking_for_notary:
            st.warning("🔄 In Review")
        elif selected_property.notary_attached:
            st.success("✅ Validated")
        else:
            st.info("📋 Draft")


def _render_document_management_tabs(selected_property: Property, current_agent: Agent):
    """Render document management tabs"""
    doc_tab1, doc_tab2, doc_tab3, doc_tab4 = st.tabs([
        "➕ Add Documents",
        "🔄 Replace Mandatory",
        "📝 Add Note",
        "📋 Document History"
    ])

    with doc_tab1:
        _add_additional_documents_interface(selected_property, current_agent)

    with doc_tab2:
        _replace_mandatory_documents_interface(selected_property, current_agent)

    with doc_tab3:
        _add_agent_note_interface(selected_property, current_agent)

    with doc_tab4:
        _show_document_history_interface(selected_property)


def _add_additional_documents_interface(property_obj: Property, current_agent: Agent):
    """Interface for adding additional documents"""
    st.subheader("➕ Add Additional Documents")

    with st.form("add_additional_docs"):
        # Category selection
        category = st.selectbox(
            "Document Category:",
            options=list(ADDITIONAL_DOC_CATEGORIES.keys()),
            format_func=lambda x: ADDITIONAL_DOC_CATEGORIES[x]
        )

        # File upload
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=ALLOWED_DOCUMENT_TYPES,
            accept_multiple_files=True,
            help="Upload documents related to your property"
        )

        # Agent note
        agent_note = st.text_area(
            "Note (Optional):",
            placeholder="Explain why you're adding these documents..."
        )

        submitted = st.form_submit_button("📎 Add Documents", type="primary")

        if submitted:
            if not uploaded_files:
                st.error("Please upload at least one document.")
                return

            # Save uploaded documents
            document_ids = []
            for uploaded_file in uploaded_files:
                doc = Document(
                    document_name=f"{ADDITIONAL_DOC_CATEGORIES[category]} - {uploaded_file.name}",
                    document_path=f"{DOCUMENT_PATHS['additional_docs']}{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    upload_id=current_agent.agent_id,
                    validation_status=False,
                    visibility=True
                )
                save_document(doc)
                document_ids.append(doc.document_id)

            # Add documents to property
            updated_property = property_obj
            for doc_id in document_ids:
                updated_property = add_additional_document_to_property(
                    updated_property, category, doc_id, agent_note
                )

            save_property(updated_property)

            st.success(f"✅ Added {len(document_ids)} documents to {ADDITIONAL_DOC_CATEGORIES[category]}")
            st.rerun()


def _replace_mandatory_documents_interface(property_obj: Property, current_agent: Agent):
    """Interface for replacing mandatory documents"""
    st.subheader("🔄 Replace Mandatory Documents")

    # Show current mandatory documents
    documents = get_documents()

    with st.form("replace_mandatory_doc"):
        # Document type selection
        doc_type = st.selectbox(
            "Select Document to Replace:",
            options=list(MANDATORY_DOCS.keys()),
            format_func=lambda x: MANDATORY_DOCS[x]
        )

        # Show current document info
        current_doc_id = property_obj.mandatory_legal_docs.get(doc_type)
        if current_doc_id and current_doc_id in documents:
            current_doc = documents[current_doc_id]
            st.info(f"Current document: {current_doc.document_name}")
            if current_doc.validation_status:
                st.warning("⚠️ This document is already validated. Replacing it will require re-validation.")
        else:
            st.warning("No document currently uploaded for this type.")

        # New file upload
        new_file = st.file_uploader(
            "Upload Replacement Document",
            type=ALLOWED_DOCUMENT_TYPES,
            help="Upload the corrected/updated version"
        )

        # Reason for replacement
        reason = st.text_area(
            "Reason for Replacement*:",
            placeholder="Explain why you're replacing this document (e.g., 'Updated version with correct dates', 'Higher quality scan')"
        )

        submitted = st.form_submit_button("🔄 Replace Document", type="primary")

        if submitted:
            if not new_file:
                st.error("Please upload a replacement document.")
                return

            if not reason.strip():
                st.error("Please provide a reason for the replacement.")
                return

            # Save new document
            new_doc = Document(
                document_name=f"{MANDATORY_DOCS[doc_type]} (Replacement)",
                document_path=f"{DOCUMENT_PATHS['documents']}{new_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                upload_id=current_agent.agent_id,
                validation_status=False,  # Needs re-validation
                visibility=True
            )
            save_document(new_doc)

            # Replace document in property
            updated_property = replace_mandatory_document(
                property_obj, doc_type, new_doc.document_id, reason
            )
            save_property(updated_property)

            st.success(f"✅ Replaced {MANDATORY_DOCS[doc_type]} successfully!")
            st.info("The new document will need to be validated by a notary.")
            st.rerun()


def _add_agent_note_interface(property_obj: Property, current_agent: Agent):
    """Interface for adding agent notes"""
    st.subheader("📝 Add Agent Note")

    with st.form("add_agent_note"):
        note_context = st.selectbox(
            "Note Context:",
            options=["general", "document_clarification", "property_update", "notary_communication", "buyer_inquiry"],
            format_func=lambda x: x.replace("_", " ").title()
        )

        note_text = st.text_area(
            "Note*:",
            placeholder="Add any important information, clarifications, or updates about this property...",
            height=100
        )

        submitted = st.form_submit_button("📝 Add Note", type="primary")

        if submitted:
            if not note_text.strip():
                st.error("Please enter a note.")
                return

            updated_property = add_agent_note_to_property(property_obj, note_text.strip(), note_context)
            save_property(updated_property)

            st.success("✅ Note added successfully!")
            st.rerun()


def _show_document_history_interface(property_obj: Property):
    """Show document history and recent activity"""
    st.subheader("📋 Document History & Activity")

    # Recent activity
    recent_activity = get_property_recent_activity(property_obj, limit=20)

    if not recent_activity:
        st.info("No activity recorded yet.")
        return

    # Show activity timeline
    for activity in recent_activity:
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                if activity["type"] == "document_activity":
                    st.write(f"📄 **{activity['description']}**")
                    details = activity["details"]
                    if "note" in details and details["note"]:
                        st.write(f"   💬 {details['note']}")
                else:  # agent_note
                    st.write(f"📝 **Agent Note:** {activity['details']['note']}")
                    st.write(f"   🏷️ Context: {activity['details']['context'].replace('_', ' ').title()}")

            with col2:
                timestamp = activity["timestamp"]
                st.write(f"🕒 {format_timestamp(timestamp)}")

        st.divider()

    # Show additional documents summary
    st.subheader("📊 Additional Documents Summary")
    additional_counts = get_property_additional_docs_count(property_obj)

    if any(count > 0 for count in additional_counts.values()):
        for category, count in additional_counts.items():
            if count > 0:
                st.write(f"• **{ADDITIONAL_DOC_CATEGORIES[category]}**: {count} documents")
    else:
        st.info("No additional documents uploaded yet.")