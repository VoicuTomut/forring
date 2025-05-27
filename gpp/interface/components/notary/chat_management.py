"""
Notary chat management component
"""

import streamlit as st
from gpp.classes.notary import Notary
from gpp.interface.utils.database import get_properties
from gpp.interface.utils.chat_database import get_property_chat, save_property_chat, init_chat_storage
from gpp.classes.chat import assign_notary_to_chat, add_system_message
from gpp.interface.components.shared.chat_interface import render_agent_notary_chat, render_chat_sidebar_summary


def notary_chat_dashboard(current_notary: Notary):
    """Main chat dashboard for notaries"""
    st.subheader("💬 Property Communications")

    # Initialize chat storage
    init_chat_storage()

    # Get properties assigned to this notary or in validation queue
    properties = get_properties()
    notary_properties = {}

    for prop_id, prop in properties.items():
        # Include if notary is attached or property is looking for notary
        if (prop.notary_attached == current_notary.notary_id or
            (prop.looking_for_notary and not prop.notary_attached)):
            notary_properties[prop_id] = prop

    if not notary_properties:
        st.info("No properties assigned for validation yet.")
        return

    # Property selection
    selected_property_id = _select_property_for_chat(notary_properties)
    if not selected_property_id:
        return

    selected_property = notary_properties[selected_property_id]

    # Get chat for this property
    chat = get_property_chat(selected_property_id)

    if not chat:
        st.info("No chat available for this property yet. Chat will be created when agent starts communication.")
        return

    # Assign notary to chat if not already assigned
    if not chat.notary_id:
        chat = assign_notary_to_chat(chat, current_notary.notary_id)
        # Add system message
        chat = add_system_message(chat, f"Notary {current_notary.notary_id[:8]} joined the chat")
        save_property_chat(chat)

    # Show chat summary in sidebar
    render_chat_sidebar_summary(chat, current_notary.notary_id, "notary", selected_property)

    # Chat interface
    render_agent_notary_chat(
        chat, current_notary.notary_id, "notary",
        f"Notary {current_notary.notary_id[:8]}", selected_property
    )

    # Show property info for context
    with st.expander("📋 Property Context", expanded=False):
        st.write(f"**Property:** {selected_property.title}")
        st.write(f"**Agent:** {selected_property.agent_id[:8]}...")
        st.write(f"**Status:** {'Pending Validation' if selected_property.looking_for_notary else 'Validated'}")
        if selected_property.description:
            st.write(f"**Description:** {selected_property.description[:200]}...")

    st.divider()


def _select_property_for_chat(notary_properties):
    """Property selection for chat"""
    if 'notary_chat_property_id' in st.session_state and st.session_state['notary_chat_property_id'] in notary_properties:
        selected_property_id = st.session_state['notary_chat_property_id']
    else:
        property_options = {f"{prop.title} - {prop.city}": prop_id
                          for prop_id, prop in notary_properties.items()}

        if not property_options:
            return None

        selected_title = st.selectbox("Select Property for Chat:", options=list(property_options.keys()))
        selected_property_id = property_options[selected_title]

    return selected_property_id