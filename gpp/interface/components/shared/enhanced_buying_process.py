"""
Enhanced Buying Process Components
Includes document management, chat integration, and complete transaction workflow
"""

import streamlit as st
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
import uuid

# FIXED IMPORTS - Import constants from the correct location
from gpp.classes.buying import (
    Buying, add_document_to_buying, add_transaction_note, update_buying_status,
    get_buying_progress, validate_buying_document, ensure_enhanced_fields
)
from gpp.classes.document import Document

# Import constants from constants.py instead of buying.py
from gpp.interface.config.constants import (
    BUYING_DOCUMENT_TYPES, TRANSACTION_STATUSES
)

from gpp.interface.utils.database import save_document, get_properties
from gpp.interface.utils.buying_database import save_buying_transaction, load_buying_transaction

# Additional document types for buying process
BUYER_ADDITIONAL_DOCUMENTS = {
    "mortgage_preapproval": "Mortgage Pre-approval Letter",
    "financial_statement": "Financial Statement",
    "employment_verification": "Employment Verification",
    "additional_bank_statements": "Additional Bank Statements",
    "co_signer_documents": "Co-signer Documents"
}

AGENT_BUYING_DOCUMENTS = {
    "purchase_agreement": "Purchase Agreement Contract",
    "property_disclosure": "Property Disclosure Statement",
    "home_warranty": "Home Warranty Information",
    "closing_statement": "Closing Cost Statement",
    "final_walkthrough": "Final Walkthrough Report"
}


def show_enhanced_buying_dashboard(current_user, user_type: str):
    """Enhanced buying dashboard with payment integration"""
    st.title("🏠 Property Buying & Transactions")

    user_id = getattr(current_user, f'{user_type.lower()}_id', None)
    if not user_id:
        st.error(f"Could not retrieve {user_type} ID")
        return

    # Check if coming from successful payment
    if st.session_state.get("payment_successful") and st.session_state.get("buying_transaction_id"):
        _show_payment_success_summary()

    # Load user's buying transactions
    try:
        from gpp.interface.utils.buying_database import get_user_buying_transactions
        transactions = get_user_buying_transactions(user_id, user_type.lower())
    except Exception as e:
        st.error(f"Error loading transactions: {e}")
        transactions = {}

    if not transactions:
        if user_type.lower() == "buyer":
            st.info("🏠 No active purchases yet. Browse properties to start buying!")
            _show_available_properties_for_buying(current_user)
        else:
            st.info("📋 No buying transactions yet.")
        return

    # Dashboard overview with enhanced metrics
    _render_enhanced_buying_overview(transactions, user_type)

    # Enhanced transaction list
    _render_enhanced_transaction_list(transactions, current_user, user_type)


def _show_payment_success_summary():
    """Show payment success summary"""
    st.success("🎉 Property Successfully Reserved!")

    transaction_id = st.session_state.get("buying_transaction_id")
    property_id = st.session_state.get("reserved_property_id")

    if transaction_id and property_id:
        col1, col2 = st.columns(2)

        with col1:
            st.info(f"**Transaction ID:** {transaction_id[:12]}...")
            st.info(f"**Property ID:** {property_id[:12]}...")

        with col2:
            if st.button("📋 View Transaction Details"):
                st.session_state["selected_transaction"] = transaction_id
                st.rerun()

    st.markdown("---")


def _show_available_properties_for_buying(current_buyer):
    """Show available properties with buy button that leads to payment"""
    st.subheader("🏠 Available Properties")

    try:
        from gpp.interface.utils.property_helpers import get_validated_properties
        validated_properties = get_validated_properties()
    except ImportError:
        # Fallback to getting properties directly
        properties = get_properties()
        validated_properties = {
            prop_id: prop for prop_id, prop in properties.items()
            if getattr(prop, 'notary_attached', False) and not getattr(prop, 'looking_for_notary', True)
        }

    if not validated_properties:
        st.info("No validated properties available at the moment.")
        return

    for prop_id, prop in validated_properties.items():
        # Skip if already reserved
        if getattr(prop, 'reserved', False):
            continue

        with st.expander(f"🏠 {prop.title} - €{prop.price:,.2f}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**📍 Location:** {getattr(prop, 'address', 'N/A')}, {getattr(prop, 'city', 'N/A')}")
                st.write(f"**📐 Size:** {getattr(prop, 'dimension', 'N/A')}")
                st.write(f"**🏠 Rooms:** {getattr(prop, 'nb_room', 'N/A')}")
                description = getattr(prop, 'description', 'N/A')
                if len(description) > 100:
                    description = description[:100] + "..."
                st.write(f"**📝 Description:** {description}")

            with col2:
                st.write(f"**💰 Price:** €{prop.price:,.2f}")
                st.write(f"**🏘️ Agent:** {getattr(prop, 'agent_id', 'Unknown')[:8]}...")

                reservation_fee = prop.price * Decimal("0.05")
                st.write(f"**💳 Reservation Fee:** €{reservation_fee:,.2f}")
                st.caption("(5% of property price)")

                if st.button("🛒 Reserve & Buy", key=f"reserve_{prop_id}", type="primary"):
                    st.session_state["payment_page_property"] = prop_id
                    st.rerun()


def _render_enhanced_buying_overview(transactions: Dict[str, Buying], user_type: str):
    """Enhanced buying overview with more detailed metrics"""
    st.subheader("📊 Transaction Overview")

    # Calculate enhanced metrics
    total = len(transactions)
    active = len([t for t in transactions.values()
                  if t.status in ["pending", "documents_pending", "under_review"]])
    completed = len([t for t in transactions.values() if t.status == "completed"])
    cancelled = len([t for t in transactions.values() if t.status == "cancelled"])

    total_value = sum([float(t.final_price or 0) for t in transactions.values()])
    avg_value = total_value / total if total > 0 else 0

    # Metrics display
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total", total)

    with col2:
        st.metric("Active", active, delta=f"{(active / total * 100):.0f}%" if total > 0 else "0%")

    with col3:
        st.metric("Completed", completed)

    with col4:
        st.metric("Total Value", f"€{total_value:,.0f}")

    with col5:
        st.metric("Avg. Value", f"€{avg_value:,.0f}")

    # Progress visualization
    if active > 0:
        st.subheader("📈 Active Transactions Progress")
        progress_data = []

        for buying_id, transaction in transactions.items():
            if transaction.status in ["pending", "documents_pending", "under_review"]:
                progress = get_buying_progress(transaction)
                progress_data.append({
                    "Transaction": buying_id[:8] + "...",
                    "Progress": progress['progress_percentage'],
                    "Status": transaction.status.replace('_', ' ').title()
                })

        if progress_data:
            for data in progress_data:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**{data['Transaction']}**")
                with col2:
                    st.progress(data['Progress'] / 100)
                with col3:
                    st.write(f"{data['Progress']:.0f}% - {data['Status']}")


def _render_enhanced_transaction_list(transactions: Dict[str, Buying], current_user, user_type: str):
    """Enhanced transaction list with better filtering and display"""
    st.subheader("📋 Your Transactions")

    # Enhanced filters
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All"] + list(set(t.status for t in transactions.values()))
        )

    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Recent", "Price", "Status", "Progress"]
        )

    with col3:
        view_mode = st.selectbox(
            "View Mode",
            ["Cards", "Table"]
        )

    # Apply filters
    filtered_transactions = transactions
    if status_filter != "All":
        filtered_transactions = {
            k: v for k, v in transactions.items() if v.status == status_filter
        }

    # Sort transactions
    if sort_by == "Recent":
        sorted_items = sorted(filtered_transactions.items(),
                              key=lambda x: x[1].last_updated, reverse=True)
    elif sort_by == "Price":
        sorted_items = sorted(filtered_transactions.items(),
                              key=lambda x: float(x[1].final_price or 0), reverse=True)
    elif sort_by == "Progress":
        sorted_items = sorted(filtered_transactions.items(),
                              key=lambda x: get_buying_progress(x[1])['progress_percentage'], reverse=True)
    else:  # Status
        sorted_items = sorted(filtered_transactions.items(), key=lambda x: x[1].status)

    # Display transactions
    if view_mode == "Cards":
        _render_transaction_cards(sorted_items, current_user, user_type)
    else:
        _render_transaction_table(sorted_items, current_user, user_type)


def _render_transaction_cards(transactions, current_user, user_type: str):
    """Render transactions as cards"""
    for buying_id, transaction in transactions:
        _render_enhanced_transaction_card(buying_id, transaction, current_user, user_type)


def _render_enhanced_transaction_card(buying_id: str, transaction: Buying, current_user, user_type: str):
    """Enhanced transaction card with more details"""
    # Ensure enhanced fields
    transaction = ensure_enhanced_fields(transaction)

    # Get property details
    properties = get_properties()
    property_data = properties.get(transaction.property_id)

    with st.container():
        # Header with status indicator
        status_colors = {
            "pending": "🟡",
            "documents_pending": "📄",
            "under_review": "🔍",
            "approved": "✅",
            "completed": "🎉",
            "cancelled": "❌",
            "on_hold": "⏸️"
        }

        status_icon = status_colors.get(transaction.status, "⚪")
        st.subheader(f"{status_icon} Transaction {buying_id[:12]}...")

        # Main content
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            if property_data:
                st.write(f"**🏠 Property:** {property_data.title}")
                st.write(
                    f"**📍 Location:** {getattr(property_data, 'address', 'N/A')}, {getattr(property_data, 'city', 'N/A')}")
            else:
                st.write(f"**🏠 Property ID:** {transaction.property_id[:12]}...")

            if transaction.final_price:
                st.write(f"**💰 Price:** €{transaction.final_price:,.2f}")

        with col2:
            status_display = TRANSACTION_STATUSES.get(transaction.status, transaction.status)
            st.write(f"**Status:** {status_display}")
            st.write(f"**Created:** {transaction.created_date.strftime('%m/%d/%Y')}")
            st.write(f"**Updated:** {transaction.last_updated.strftime('%m/%d/%Y')}")

        with col3:
            progress = get_buying_progress(transaction)
            st.write(f"**Progress:** {progress['progress_percentage']:.0f}%")
            st.progress(progress['progress_percentage'] / 100)

            # Document status
            st.write(f"**Documents:** {progress['validated_documents']}/{progress['total_documents']}")
            if progress['active_meetings'] > 0:
                st.write(f"**Meetings:** {progress['active_meetings']} scheduled")

        with col4:
            if st.button("📋 Details", key=f"view_{buying_id}"):
                st.session_state["selected_transaction"] = buying_id
                st.rerun()

            if st.button("💬 Chat", key=f"chat_{buying_id}"):
                st.session_state["buying_chat_transaction"] = buying_id
                st.rerun()

        # Quick actions based on user type and transaction status
        _render_quick_actions(transaction, current_user, user_type)

        st.markdown("---")


def _render_quick_actions(transaction: Buying, current_user, user_type: str):
    """Render quick action buttons based on user type and transaction status"""
    user_id = getattr(current_user, f'{user_type.lower()}_id', None)
    if not user_id:
        return

    col1, col2, col3, col4 = st.columns(4)

    if user_type.lower() == "buyer":
        with col1:
            if transaction.status == "pending" and st.button("📤 Upload Docs", key=f"upload_{transaction.buying_id}"):
                st.session_state["upload_docs_transaction"] = transaction.buying_id
                st.rerun()

        with col2:
            if transaction.status in ["documents_pending", "under_review"]:
                st.info("⏳ Awaiting Review")

    elif user_type.lower() == "agent":
        with col1:
            if transaction.status == "pending" and st.button("📄 Add Contract", key=f"contract_{transaction.buying_id}"):
                st.session_state["add_contract_transaction"] = transaction.buying_id
                st.rerun()

        with col2:
            if transaction.status == "documents_pending":
                st.info("⏳ Awaiting Buyer Docs")

    elif user_type.lower() == "notary":
        with col1:
            if transaction.status in ["documents_pending", "under_review"]:
                if st.button("✅ Validate", key=f"validate_{transaction.buying_id}"):
                    st.session_state["validate_transaction"] = transaction.buying_id
                    st.rerun()

        with col2:
            if transaction.status == "approved":
                if st.button("🎉 Complete", key=f"complete_{transaction.buying_id}"):
                    transaction = update_buying_status(transaction, "completed", "Transaction completed by notary")
                    save_buying_transaction(transaction)
                    st.success("Transaction completed!")
                    st.rerun()


def _render_transaction_table(transactions, current_user, user_type: str):
    """Render transactions as a table"""
    if not transactions:
        st.info("No transactions to display")
        return

    # Prepare table data
    table_data = []
    for buying_id, transaction in transactions:
        properties = get_properties()
        property_data = properties.get(transaction.property_id)
        progress = get_buying_progress(transaction)

        table_data.append({
            "ID": buying_id[:8] + "...",
            "Property": property_data.title if property_data else transaction.property_id[:8] + "...",
            "Price": f"€{transaction.final_price:,.0f}" if transaction.final_price else "N/A",
            "Status": transaction.status.replace('_', ' ').title(),
            "Progress": f"{progress['progress_percentage']:.0f}%",
            "Documents": f"{progress['validated_documents']}/{progress['total_documents']}",
            "Last Updated": transaction.last_updated.strftime('%m/%d/%Y'),
            "Actions": buying_id  # We'll use this for action buttons
        })

    # Display table (simplified version - in a real app you'd use a proper data table component)
    for row in table_data:
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(8)

        with col1:
            st.write(row["ID"])
        with col2:
            st.write(row["Property"])
        with col3:
            st.write(row["Price"])
        with col4:
            st.write(row["Status"])
        with col5:
            progress_val = float(row["Progress"].replace('%', ''))
            st.progress(progress_val / 100)
        with col6:
            st.write(row["Documents"])
        with col7:
            st.write(row["Last Updated"])
        with col8:
            if st.button("View", key=f"table_view_{row['Actions']}"):
                st.session_state["selected_transaction"] = row["Actions"]
                st.rerun()


def show_document_upload_modal(transaction_id: str, current_user, user_type: str):
    """Show document upload modal for buyers"""
    st.subheader("📤 Upload Additional Documents")

    transaction = load_buying_transaction(transaction_id)
    if not transaction:
        st.error("Transaction not found")
        return

    # Ensure enhanced fields
    transaction = ensure_enhanced_fields(transaction)

    user_id = getattr(current_user, f'{user_type.lower()}_id', None)
    if not user_id:
        st.error("Could not retrieve user ID")
        return

    # Document categories based on user type
    if user_type.lower() == "buyer":
        available_docs = BUYER_ADDITIONAL_DOCUMENTS
    elif user_type.lower() == "agent":
        available_docs = AGENT_BUYING_DOCUMENTS
    else:
        st.error("Document upload not available for this user type")
        return

    with st.form(f"upload_additional_docs_{transaction_id}"):
        col1, col2 = st.columns(2)

        with col1:
            doc_type = st.selectbox(
                "Document Type",
                options=list(available_docs.keys()),
                format_func=lambda x: available_docs[x]
            )

        with col2:
            uploaded_file = st.file_uploader(
                "Select Document",
                type=["pdf", "doc", "docx", "jpg", "jpeg", "png"],
                help="Upload PDF, Word document, or image file"
            )

        upload_notes = st.text_area(
            "Document Notes",
            placeholder="Any additional information about this document..."
        )

        if st.form_submit_button("📤 Upload Document"):
            if uploaded_file and user_id:
                try:
                    # Save file
                    from gpp.interface.utils.file_storage import save_uploaded_file
                    file_path = save_uploaded_file(uploaded_file, "buying_documents")

                    if file_path:
                        # Create document record
                        doc = Document(
                            document_name=f"{available_docs[doc_type]} - {uploaded_file.name}",
                            document_path=file_path,
                            upload_id=user_id,
                            validation_status=False,
                            visibility=True
                        )
                        save_document(doc)

                        # Add to buying transaction
                        transaction = add_document_to_buying(transaction, doc_type, doc.document_id)

                        # Add note about upload
                        transaction = add_transaction_note(
                            transaction,
                            f"Additional document uploaded: {available_docs[doc_type]}. {upload_notes}".strip(),
                            user_id,
                            "document_upload"
                        )

                        # Update transaction status if needed
                        if transaction.status == "pending":
                            transaction = update_buying_status(transaction, "documents_pending")

                        save_buying_transaction(transaction)

                        st.success(f"✅ {available_docs[doc_type]} uploaded successfully!")

                        # Clear session state
                        if "upload_docs_transaction" in st.session_state:
                            del st.session_state["upload_docs_transaction"]
                        st.rerun()
                    else:
                        st.error("❌ Failed to save document")
                except Exception as e:
                    st.error(f"❌ Error uploading document: {str(e)}")
            else:
                st.error("❌ Please select a document to upload")

    if st.button("❌ Cancel Upload"):
        if "upload_docs_transaction" in st.session_state:
            del st.session_state["upload_docs_transaction"]
        st.rerun()


def show_notary_validation_interface(transaction_id: str, current_user):
    """Show document validation interface for notaries"""
    st.subheader("⚖️ Document Validation")

    transaction = load_buying_transaction(transaction_id)
    if not transaction:
        st.error("Transaction not found")
        return

    # Ensure enhanced fields
    transaction = ensure_enhanced_fields(transaction)

    notary_id = getattr(current_user, 'notary_id', None)
    if not notary_id:
        st.error("Could not retrieve notary ID")
        return

    # Show transaction summary
    properties = get_properties()
    property_data = properties.get(transaction.property_id)

    if property_data:
        st.info(f"**Property:** {property_data.title} - €{transaction.final_price:,.2f}")

    # Document validation interface
    st.write("**Documents to Validate:**")

    all_doc_types = {**BUYING_DOCUMENT_TYPES, **BUYER_ADDITIONAL_DOCUMENTS, **AGENT_BUYING_DOCUMENTS}

    validation_actions = []

    for doc_type, doc_name in all_doc_types.items():
        if doc_type in transaction.buying_documents and transaction.buying_documents[doc_type]:
            doc_id = transaction.buying_documents[doc_type]
            validation_info = transaction.document_validation_status.get(doc_type, {})

            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                if validation_info.get("validation_status", False):
                    st.success(f"✅ **{doc_name}** - Validated")
                    if validation_info.get("validation_date"):
                        st.caption(f"Validated: {validation_info['validation_date'].strftime('%Y-%m-%d')}")
                else:
                    st.warning(f"⏳ **{doc_name}** - Pending Validation")
                    if validation_info.get("upload_date"):
                        st.caption(f"Uploaded: {validation_info['upload_date'].strftime('%Y-%m-%d')}")

            with col2:
                if st.button("👁️ View", key=f"view_doc_{doc_type}_{transaction_id}"):
                    st.session_state[f"view_document_{doc_id}"] = True
                    st.rerun()

            with col3:
                if not validation_info.get("validation_status", False):
                    if st.button("✅ Approve", key=f"approve_{doc_type}_{transaction_id}"):
                        validation_actions.append(("approve", doc_type))

            with col4:
                if not validation_info.get("validation_status", False):
                    if st.button("❌ Reject", key=f"reject_{doc_type}_{transaction_id}"):
                        validation_actions.append(("reject", doc_type))

    # Process validation actions
    if validation_actions:
        for action, doc_type in validation_actions:
            if action == "approve":
                transaction = validate_buying_document(transaction, doc_type, notary_id, True)
            else:
                transaction = validate_buying_document(transaction, doc_type, notary_id, False)

        save_buying_transaction(transaction)
        st.rerun()

    # Bulk actions
    st.markdown("---")
    st.subheader("🔄 Bulk Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Approve All Documents", type="primary"):
            for doc_type in transaction.buying_documents:
                if transaction.buying_documents[doc_type]:
                    transaction = validate_buying_document(transaction, doc_type, notary_id, True)

            transaction = update_buying_status(transaction, "approved", "All documents approved by notary")
            save_buying_transaction(transaction)
            st.success("All documents approved!")
            st.rerun()

    with col2:
        if st.button("🔄 Request More Documents"):
            transaction = update_buying_status(transaction, "documents_pending", "Additional documents requested")
            save_buying_transaction(transaction)
            st.info("Status updated - more documents requested")
            st.rerun()

    with col3:
        if st.button("❌ Reject Transaction"):
            transaction = update_buying_status(transaction, "cancelled", "Transaction rejected by notary")
            save_buying_transaction(transaction)
            st.error("Transaction rejected")
            st.rerun()


# Buying Chat System Integration
def show_buying_chat_interface(transaction_id: str, current_user, user_type: str):
    """Show chat interface for buying transaction"""
    st.subheader("💬 Transaction Chat")

    transaction = load_buying_transaction(transaction_id)
    if not transaction:
        st.error("Transaction not found")
        return

    # Ensure enhanced fields
    transaction = ensure_enhanced_fields(transaction)

    user_id = getattr(current_user, f'{user_type.lower()}_id', None)
    if not user_id:
        st.error("Could not retrieve user ID")
        return

    # Chat tabs based on user type
    if user_type.lower() == "buyer":
        # Buyer can chat with agent
        _render_buyer_agent_chat(transaction, user_id)
    elif user_type.lower() == "agent":
        # Agent can chat with buyer and notary
        tab1, tab2 = st.tabs(["💰 Buyer Chat", "⚖️ Notary Chat"])

        with tab1:
            _render_buyer_agent_chat(transaction, user_id)

        with tab2:
            _render_agent_notary_chat(transaction, user_id)

    elif user_type.lower() == "notary":
        # Notary can chat with agent and see overall status
        _render_agent_notary_chat(transaction, user_id)


def _render_buyer_agent_chat(transaction: Buying, user_id: str):
    """Render chat between buyer and agent"""
    st.write("**Chat with Agent**")

    # Get chat messages from transaction notes (simplified)
    chat_messages = [note for note in transaction.transaction_notes
                     if note.get('note_type') in ['general', 'chat']]

    # Display chat messages
    for message in chat_messages[-10:]:  # Show last 10 messages
        sender_type = "You" if message.get('author_id') == user_id else "Agent"
        timestamp = message.get('timestamp', datetime.now()).strftime('%H:%M')

        if message.get('author_id') == user_id:
            st.markdown(f"**{sender_type}** ({timestamp}): {message.get('note', '')}")
        else:
            st.markdown(f"*{sender_type}* ({timestamp}): {message.get('note', '')}")

    # Send new message
    with st.form(f"chat_form_{transaction.buying_id}"):
        new_message = st.text_input("Type your message...")
        if st.form_submit_button("📤 Send"):
            if new_message:
                transaction = add_transaction_note(transaction, new_message, user_id, "chat")
                save_buying_transaction(transaction)
                st.rerun()


def _render_agent_notary_chat(transaction: Buying, user_id: str):
    """Render chat between agent and notary"""
    st.write("**Chat with Notary**")

    # Similar implementation as buyer-agent chat
    # This would integrate with the PropertyChat system from your existing code
    st.info("Notary chat integration - would connect to PropertyChat system")


# Integration functions for the main application
def integrate_payment_system_with_buyer_dashboard():
    """Integration point for buyer dashboard"""
    # Check if payment page should be shown
    if st.session_state.get("payment_page_property"):
        try:
            from gpp.interface.components.shared.demo_payment_system import show_payment_page, show_payment_demo_info

            property_id = st.session_state["payment_page_property"]
            current_buyer = st.session_state.get("current_user")  # Assume this is set

            show_payment_demo_info()
            show_payment_page(property_id, current_buyer)
            return True
        except ImportError:
            st.error("Payment system not available")
            return False

    return False


def integrate_enhanced_buying_with_dashboards():
    """Integration point for all dashboards"""
    # Check for various session states and show appropriate interfaces

    if st.session_state.get("upload_docs_transaction"):
        transaction_id = st.session_state["upload_docs_transaction"]
        current_user = st.session_state.get("current_user")
        user_type = st.session_state.get("user_type", "buyer")

        show_document_upload_modal(transaction_id, current_user, user_type)
        return True

    if st.session_state.get("validate_transaction"):
        transaction_id = st.session_state["validate_transaction"]
        current_user = st.session_state.get("current_user")

        show_notary_validation_interface(transaction_id, current_user)
        return True

    if st.session_state.get("buying_chat_transaction"):
        transaction_id = st.session_state["buying_chat_transaction"]
        current_user = st.session_state.get("current_user")
        user_type = st.session_state.get("user_type", "buyer")

        show_buying_chat_interface(transaction_id, current_user, user_type)
        return True

    return False


# Additional helper functions for safe operations
def get_property_safe_attribute(prop, attr_name: str, default="N/A"):
    """Safely get property attribute with fallback"""
    return getattr(prop, attr_name, default)


def format_currency_safe(amount):
    """Format currency amount safely"""
    try:
        if amount is None:
            return "€0.00"
        return f"€{float(amount):,.2f}"
    except (ValueError, TypeError):
        return "€0.00"


def format_date_safe(date_obj, format_str="%m/%d/%Y"):
    """Safely format date with fallback"""
    try:
        if date_obj:
            return date_obj.strftime(format_str)
        return "N/A"
    except (AttributeError, ValueError):
        return "N/A"


def get_user_id_safe(user_obj, user_type: str):
    """Safely get user ID based on user type"""
    try:
        return getattr(user_obj, f'{user_type.lower()}_id', None)
    except AttributeError:
        return None


def validate_transaction_access(buying_transaction: Buying, user_id: str, user_type: str) -> bool:
    """Validate if user has access to transaction"""
    if not user_id:
        return False

    if user_type.lower() == "notary":
        return True  # Notaries can access all transactions
    elif user_type.lower() == "agent":
        return buying_transaction.agent_id == user_id
    elif user_type.lower() == "buyer":
        return buying_transaction.buyer_id == user_id

    return False


def handle_transaction_error(error: Exception, context: str = "transaction operation"):
    """Handle transaction errors gracefully"""
    error_msg = f"Error in {context}: {str(error)}"
    st.error(f"❌ {error_msg}")

    # Log error for debugging (you can implement proper logging here)
    print(f"ENHANCED_BUYING_PROCESS ERROR: {error_msg}")

    return None


def create_safe_session_key(prefix: str, transaction_id: str) -> str:
    """Create safe session state key"""
    return f"{prefix}_{transaction_id[:8]}"


def ensure_transaction_enhanced_fields(transaction: Buying) -> Buying:
    """Ensure transaction has all required enhanced fields"""
    try:
        return ensure_enhanced_fields(transaction)
    except Exception as e:
        st.error(f"Error ensuring enhanced fields: {e}")
        return transaction


def safe_get_progress(transaction: Buying) -> Dict[str, Any]:
    """Safely get transaction progress with error handling"""
    try:
        return get_buying_progress(transaction)
    except Exception as e:
        st.error(f"Error calculating progress: {e}")
        return {
            'progress_percentage': 0,
            'validated_documents': 0,
            'total_documents': 0,
            'active_meetings': 0,
            'last_updated': datetime.now()
        }


def safe_load_transaction(transaction_id: str) -> Optional[Buying]:
    """Safely load transaction with error handling"""
    try:
        transaction = load_buying_transaction(transaction_id)
        if transaction:
            return ensure_enhanced_fields(transaction)
        return None
    except Exception as e:
        st.error(f"Error loading transaction: {e}")
        return None


def safe_save_transaction(transaction: Buying) -> bool:
    """Safely save transaction with error handling"""
    try:
        save_buying_transaction(transaction)
        return True
    except Exception as e:
        st.error(f"Error saving transaction: {e}")
        return False


# Export main functions for use in other modules
__all__ = [
    'show_enhanced_buying_dashboard',
    'show_document_upload_modal',
    'show_notary_validation_interface',
    'show_buying_chat_interface',
    'integrate_payment_system_with_buyer_dashboard',
    'integrate_enhanced_buying_with_dashboards',
    'get_property_safe_attribute',
    'format_currency_safe',
    'format_date_safe',
    'get_user_id_safe',
    'validate_transaction_access',
    'handle_transaction_error',
    'safe_get_progress',
    'safe_load_transaction',
    'safe_save_transaction'
]