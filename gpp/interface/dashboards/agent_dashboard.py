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
from gpp.interface.components.shared.document_signing_ui import (
    show_signing_workflow_dashboard, integrate_signing_with_agent_dashboard, show_document_upload_modal
)
from gpp.interface.utils.buying_database import get_user_buying_transactions


def agent_dashboard(current_agent: Agent):
    """Main agent dashboard interface"""
    st.header(f"🏢 Agent Dashboard - {current_agent.agent_id[:8]}...")

    # Enhanced tabs for agent functions - ADD SIGNING TAB
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Add New Property",
        "📋 My Properties",
        "📎 Manage Documents",
        "✍️ Document Signing",  # NEW TAB
        "💬 Communications"
    ])

    with tab1:
        add_property_form(current_agent)

    with tab2:
        show_agent_properties(current_agent)

    with tab3:
        manage_additional_documents(current_agent)

    with tab4:
        # NEW SIGNING TAB CONTENT
        _show_agent_signing_dashboard(current_agent)

    with tab5:
        agent_chat_dashboard(current_agent)


def _show_agent_signing_dashboard(current_agent: Agent):
    """Enhanced agent signing dashboard with upload modal handling"""
    st.subheader("✍️ Document Signing & Transaction Management")

    # Get agent's transactions
    buying_transactions = get_user_buying_transactions(current_agent.agent_id, "agent")

    if not buying_transactions:
        st.info("📋 No active buying transactions. Transactions will appear here when buyers reserve your properties!")
        return

    # Show transaction statistics
    total_transactions = len(buying_transactions)
    pending_signatures = 0
    completed_transactions = 0

    for txn in buying_transactions.values():
        if txn.status == "completed":
            completed_transactions += 1
        else:
            from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES
            from gpp.classes.buying import can_user_sign_document

            for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
                if "agent" in doc_config.get("required_signers", []):
                    if txn.buying_documents.get(doc_type):
                        can_sign, _ = can_user_sign_document(txn, doc_type, current_agent.agent_id, "agent")
                        if can_sign:
                            pending_signatures += 1
                            break

    # Statistics display
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transactions", total_transactions)
    with col2:
        st.metric("Pending Signatures", pending_signatures)
    with col3:
        st.metric("Completed", completed_transactions)

    st.markdown("---")

    # Transaction selector if multiple transactions
    if len(buying_transactions) > 1:
        transaction_options = {}
        for txn_id, txn in buying_transactions.items():
            from gpp.interface.utils.database import get_properties
            properties = get_properties()
            prop_data = properties.get(txn.property_id)
            display_name = f"{prop_data.title if prop_data else txn.property_id[:8]}... - {txn.status}"
            transaction_options[display_name] = txn

        selected_option = st.selectbox(
            "Select Transaction:",
            options=list(transaction_options.keys())
        )
        selected_transaction = transaction_options[selected_option]
    else:
        selected_transaction = list(buying_transactions.values())[0]

    # Show signing workflow for selected transaction
    show_signing_workflow_dashboard(selected_transaction, current_agent, "agent")

    # Handle document upload modals
    from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES

    for doc_type in ENHANCED_BUYING_DOCUMENT_TYPES.keys():
        if st.session_state.get(f"upload_doc_{doc_type}"):
            show_document_upload_modal(selected_transaction, doc_type, current_agent, "agent")
            break