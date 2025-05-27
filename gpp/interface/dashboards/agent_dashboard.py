"""
Agent Dashboard - Property management interface for agents
"""

import streamlit as st
from typing import Dict

from gpp.classes.agent import Agent
from gpp.classes.property import Property
from gpp.interface.components.agent.property_form import add_property_form
from gpp.interface.components.agent.property_list import show_agent_properties
from gpp.interface.components.agent.document_manager import manage_additional_documents
from gpp.interface.components.agent.chat_management import agent_chat_dashboard

def agent_dashboard(current_agent: Agent):
    """Main agent dashboard interface"""
    st.header(f"🏢 Agent Dashboard - {current_agent.agent_id[:8]}...")

    # Tabs for different agent functions - ENHANCED with chat
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Add New Property",
        "📋 My Properties",
        "📎 Manage Documents",
        "💬 Communications"
    ])

    with tab1:
        add_property_form(current_agent)

    with tab2:
        show_agent_properties(current_agent)

    with tab3:
        manage_additional_documents(current_agent)

    with tab4:
        agent_chat_dashboard(current_agent)