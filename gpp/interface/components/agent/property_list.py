"""
Agent property list component
"""

import streamlit as st
from gpp.classes.agent import Agent
from gpp.classes.property import Property, get_property_additional_docs_count
from gpp.classes.document import Document
from gpp.interface.utils.database import get_properties, get_documents
from gpp.interface.utils.property_helpers import get_property_validation_progress


def show_agent_properties(current_agent: Agent):
    """Display agent's properties in a list format"""
    st.subheader("My Properties")

    properties = get_properties()
    agent_properties = {k: v for k, v in properties.items()
                        if k in current_agent.agent_active_prop_list}

    if not agent_properties:
        st.info("No properties added yet. Use the 'Add New Property' tab to get started.")
        return

    # Display properties in cards
    for prop_id, prop_data in agent_properties.items():
        _render_property_card(prop_id, prop_data)


def _render_property_card(prop_id: str, prop_data: Property):
    """Render individual property card"""
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.write(f"**{prop_data.title}**")
            st.write(f"€{prop_data.price:,.2f}")
            st.write(f"📍 {prop_data.address}, {prop_data.city}")
            if prop_data.number_of_rooms:
                st.write(f"🏠 {prop_data.number_of_rooms} rooms")

        with col2:
            st.write(f"📏 {prop_data.dimension}")

            # Status indicators
            if prop_data.looking_for_notary:
                st.warning("🔄 Pending Validation")
            elif prop_data.notary_attached:
                st.success("✅ Notary Assigned")

            # Photo count
            photo_count = _get_photo_count(prop_data)
            if photo_count > 0:
                st.write(f"📸 {photo_count} photos uploaded")

            # Additional documents count
            additional_count = sum(get_property_additional_docs_count(prop_data).values())
            if additional_count > 0:
                st.write(f"📎 {additional_count} additional documents")

        with col3:
            # Validation progress
            validation_progress = get_property_validation_progress(prop_id)
            st.write(f"**{validation_progress['validated']}/{validation_progress['total']}**")
            st.progress(validation_progress['progress'])

            # Button to manage this property's documents
            if st.button("📎 Add Docs", key=f"add_docs_{prop_id}"):
                st.session_state['manage_property_id'] = prop_id

    st.divider()


def _get_photo_count(property_obj: Property) -> int:
    """Get count of photos for a property"""
    documents = get_documents()
    return len([doc_id for doc_id in property_obj.document_ids
                if get_documents().get(doc_id, Document()).document_name.startswith("Property Photo")])