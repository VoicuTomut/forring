"""
Notary Dashboard - Document validation interface for notaries
"""

import streamlit as st
from gpp.classes.notary import Notary
from gpp.interface.components.notary.validation_queue import show_validation_queue
from gpp.interface.components.notary.validated_properties import show_validated_properties
from gpp.interface.components.notary.chat_management import notary_chat_dashboard
from gpp.interface.components.shared.document_signing_ui import (
    show_signing_workflow_dashboard, integrate_signing_with_notary_dashboard
)
from gpp.interface.utils.buying_database import get_all_buying_transactions


def notary_dashboard(current_notary: Notary):
    """Main notary dashboard interface"""
    st.header(f"⚖️ Notary Dashboard - {current_notary.notary_id[:8]}...")

    # Enhanced tabs for notary functions - ADD SIGNING TAB
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Validation Queue",
        "✅ Validated Properties",
        "✍️ Document Signing",  # NEW TAB
        "💬 Communications"
    ])

    with tab1:
        show_validation_queue(current_notary)

    with tab2:
        show_validated_properties(current_notary)

    with tab3:
        # NEW SIGNING TAB CONTENT
        _show_notary_signing_dashboard(current_notary)

    with tab4:
        notary_chat_dashboard(current_notary)


# ADD this new function:
def _show_notary_signing_dashboard(current_notary: Notary):
    """Show notary signing dashboard"""
    st.subheader("✍️ Document Signing & Contract Generation")

    # Get all buying transactions (notaries can see all transactions)
    all_transactions = get_all_buying_transactions()

    # Filter transactions that need notary action
    notary_transactions = {}
    for txn_id, txn in all_transactions.items():
        # Include transactions that are not completed/cancelled
        if txn.status not in ["completed", "cancelled"]:
            notary_transactions[txn_id] = txn

    if not notary_transactions:
        st.info("📋 No transactions requiring notary action at this time.")
        return

    # Show transaction statistics
    total_transactions = len(notary_transactions)
    pending_validations = 0
    pending_signatures = 0
    documents_to_generate = 0

    for txn in notary_transactions.values():
        # Check for pending validations
        for doc_type, validation_status in txn.document_validation_status.items():
            if not validation_status.get("validation_status", False):
                pending_validations += 1
                break

        # Check for pending signatures and documents to generate
        from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES
        from gpp.classes.buying import can_user_sign_document

        for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
            # Check if notary needs to generate document
            if (doc_config.get("auto_generated") and
                    doc_config.get("generated_by") == "notary" and
                    not txn.buying_documents.get(doc_type)):
                documents_to_generate += 1

            # Check if notary needs to sign
            elif "notary" in doc_config.get("required_signers", []):
                if txn.buying_documents.get(doc_type):
                    can_sign, _ = can_user_sign_document(txn, doc_type, current_notary.notary_id, "notary")
                    if can_sign:
                        pending_signatures += 1

    # Statistics display
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Transactions", total_transactions)
    with col2:
        st.metric("Pending Validations", pending_validations)
    with col3:
        st.metric("Documents to Generate", documents_to_generate)
    with col4:
        st.metric("Pending Signatures", pending_signatures)

    st.markdown("---")

    # Priority Actions Section
    st.subheader("🚨 Priority Actions")

    priority_actions = []

    for txn_id, txn in notary_transactions.items():
        # Get property info
        from gpp.interface.utils.database import get_properties
        properties = get_properties()
        prop_data = properties.get(txn.property_id)
        property_name = prop_data.title if prop_data else txn.property_id[:8] + "..."

        # Check for documents to generate
        from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES
        for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
            if (doc_config.get("auto_generated") and
                    doc_config.get("generated_by") == "notary" and
                    not txn.buying_documents.get(doc_type)):
                priority_actions.append({
                    "type": "generate",
                    "action": f"Generate {doc_config['name']}",
                    "property": property_name,
                    "transaction_id": txn_id,
                    "doc_type": doc_type,
                    "priority": "high"
                })

        # Check for documents to sign
        from gpp.classes.buying import can_user_sign_document
        for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
            if "notary" in doc_config.get("required_signers", []):
                if txn.buying_documents.get(doc_type):
                    can_sign, _ = can_user_sign_document(txn, doc_type, current_notary.notary_id, "notary")
                    if can_sign:
                        priority_actions.append({
                            "type": "sign",
                            "action": f"Sign {doc_config['name']}",
                            "property": property_name,
                            "transaction_id": txn_id,
                            "doc_type": doc_type,
                            "priority": "medium"
                        })

    # Display priority actions
    if priority_actions:
        for action in priority_actions:
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                priority_icon = "🔴" if action["priority"] == "high" else "🟡"
                st.write(f"{priority_icon} **{action['action']}**")
                st.caption(f"Property: {action['property']}")

            with col2:
                st.write(f"Transaction: {action['transaction_id'][:8]}...")

            with col3:
                if st.button("🔧 Action", key=f"priority_{action['transaction_id']}_{action['doc_type']}"):
                    st.session_state["selected_notary_transaction"] = action['transaction_id']
                    st.rerun()
    else:
        st.success("✅ No priority actions required at this time!")

    st.markdown("---")

    # Transaction selector for detailed view
    if len(notary_transactions) > 1:
        st.subheader("📋 Detailed Transaction View")

        transaction_options = {}
        for txn_id, txn in notary_transactions.items():
            # Get property info for display
            properties = get_properties()
            prop_data = properties.get(txn.property_id)
            display_name = f"{prop_data.title if prop_data else txn.property_id[:8]}... - {txn.status} - Phase: {txn.current_phase}"
            transaction_options[display_name] = txn

        selected_option = st.selectbox(
            "Select Transaction for Detailed View:",
            options=list(transaction_options.keys()),
            key="detailed_transaction_selector"
        )
        selected_transaction = transaction_options[selected_option]
    else:
        selected_transaction = list(notary_transactions.values())[0]

    # Show signing workflow for selected transaction
    show_signing_workflow_dashboard(selected_transaction, current_notary, "notary")

    # Integrate additional notary signing features
    integrate_signing_with_notary_dashboard(selected_transaction, current_notary)
    