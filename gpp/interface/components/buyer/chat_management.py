"""
Buyer chat management component
"""

import streamlit as st
from gpp.classes.buyer import Buyer
from gpp.interface.utils.property_helpers import get_validated_properties
from gpp.interface.utils.chat_database import create_or_get_property_chat, init_chat_storage
from gpp.interface.components.shared.chat_interface import render_buyer_agent_chat, render_chat_sidebar_summary


def buyer_chat_dashboard(current_buyer: Buyer):
    """Main chat dashboard for buyers"""
    st.subheader("💬 Chat with Property Agents")

    # Initialize chat storage
    init_chat_storage()

    # Get validated properties (only these are available to buyers)
    validated_properties = get_validated_properties()

    if not validated_properties:
        st.info("No properties available for chat yet. Properties will appear once validated by notaries.")
        return

    # Property selection
    selected_property_id = _select_property_for_chat(validated_properties)
    if not selected_property_id:
        return

    selected_property = validated_properties[selected_property_id]

    # Get or create chat for this property
    chat = create_or_get_property_chat(selected_property_id, selected_property.agent_id)

    # Show chat summary in sidebar
    render_chat_sidebar_summary(chat, current_buyer.buyer_id, "buyer", selected_property)

    # Show property context
    with st.expander("🏠 Property Details", expanded=False):
        st.write(f"**Property:** {selected_property.title}")
        st.write(f"**Price:** €{selected_property.price:,.2f}")
        st.write(f"**Location:** {selected_property.address}, {selected_property.city}")
        st.write(f"**Agent:** {selected_property.agent_id[:8]}...")
        if selected_property.description:
            st.write(f"**Description:** {selected_property.description}")

    st.divider()

    # Chat interface
    render_buyer_agent_chat(
        chat, current_buyer.buyer_id, "buyer",
        f"Buyer {current_buyer.buyer_id[:8]}", property_info=selected_property
    )


def _select_property_for_chat(validated_properties):
    """Property selection for chat"""
    if 'buyer_chat_property_id' in st.session_state and st.session_state['buyer_chat_property_id'] in validated_properties:
        selected_property_id = st.session_state['buyer_chat_property_id']
    else:
        property_options = {f"{prop.title} - €{prop.price:,.0f} - {prop.city}": prop_id
                          for prop_id, prop in validated_properties.items()}

        if not property_options:
            return None

        selected_title = st.selectbox("Select Property to Chat About:", options=list(property_options.keys()))
        selected_property_id = property_options[selected_title]

    return selected_property_id