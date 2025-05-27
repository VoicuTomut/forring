"""
Agent chat management component
"""

import streamlit as st
from gpp.classes.agent import Agent
from gpp.classes.property import Property
from gpp.interface.utils.database import get_properties
from gpp.interface.utils.chat_database import create_or_get_property_chat, init_chat_storage
from gpp.interface.components.shared.chat_interface import (
    render_agent_notary_chat, render_buyer_agent_chat,
    render_chat_sidebar_summary, render_buyer_selection_for_agent
)


def agent_chat_dashboard(current_agent: Agent):
    """Main chat dashboard for agents"""
    st.subheader("💬 Property Communications")

    # Initialize chat storage
    init_chat_storage()

    # Get agent's properties
    properties = get_properties()
    agent_properties = {k: v for k, v in properties.items()
                        if k in current_agent.agent_active_prop_list}

    if not agent_properties:
        st.info("No properties to chat about. Add a property first.")
        return

    # Property selection
    selected_property_id = _select_property_for_chat(agent_properties)
    if not selected_property_id:
        return

    selected_property = agent_properties[selected_property_id]

    # Get or create chat for this property
    chat = create_or_get_property_chat(selected_property_id, current_agent.agent_id)

    # Show chat summary in sidebar
    render_chat_sidebar_summary(chat, current_agent.agent_id, "agent")

    # Chat interface tabs
    tab1, tab2 = st.tabs(["⚖️ Chat with Notary", "👥 Chat with Buyers"])

    with tab1:
        render_agent_notary_chat(
            chat, current_agent.agent_id, "agent",
            f"Agent {current_agent.agent_id[:8]}"
        )

    with tab2:
        _render_agent_buyer_chats(chat, current_agent, selected_property)


def _select_property_for_chat(agent_properties):
    """Property selection for chat"""
    if 'chat_property_id' in st.session_state and st.session_state['chat_property_id'] in agent_properties:
        selected_property_id = st.session_state['chat_property_id']
    else:
        property_options = {f"{prop.title} - {prop.city}": prop_id
                          for prop_id, prop in agent_properties.items()}

        if not property_options:
            return None

        selected_title = st.selectbox("Select Property for Chat:", options=list(property_options.keys()))
        selected_property_id = property_options[selected_title]

    return selected_property_id


def _render_agent_buyer_chats(chat, current_agent, selected_property):
    """Render buyer chat interface for agents"""
    # Select buyer to chat with
    selected_buyer_id = render_buyer_selection_for_agent(chat)

    if selected_buyer_id:
        st.divider()
        render_buyer_agent_chat(
            chat, current_agent.agent_id, "agent",
            f"Agent {current_agent.agent_id[:8]}", selected_buyer_id, selected_property
        )