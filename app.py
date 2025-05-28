"""
Updated App.py - Integrated with Enhanced Buying System
Includes payment processing, document management, and chat system
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from gpp.interface.config.constants import APP_CONFIG
from gpp.interface.utils.database import init_data_files
from gpp.interface.utils.buying_database import init_buying_database
from gpp.interface.dashboards.agent_dashboard import agent_dashboard
from gpp.interface.dashboards.notary_dashboard import notary_dashboard
from gpp.interface.dashboards.buyer_dashboard import buyer_dashboard
from gpp.interface.utils.user_management import get_or_create_user

# Import enhanced buying system components
from gpp.interface.components.shared.buying_components import (
    show_buying_dashboard, start_buying_process, show_transaction_details
)

from gpp.interface.components.shared.enhanced_buying_process import (
    show_enhanced_buying_dashboard, show_document_upload_modal,
    show_notary_validation_interface, integrate_payment_system_with_buyer_dashboard,
    integrate_enhanced_buying_with_dashboards
)
from gpp.interface.components.shared.demo_payment_system import (
    show_payment_page, show_payment_demo_info
)
from gpp.interface.components.shared.buying_chat_system import (
    show_integrated_buying_chat, show_chat_notifications, get_active_buying_chats
)
from gpp.interface.utils.buying_database import get_user_buying_transactions


def main():
    """Main application entry point with enhanced buying system"""
    st.set_page_config(**APP_CONFIG)

    # Initialize data storage
    init_data_files()
    init_buying_database()

    # Display logos in header
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        # Display icon if it exists
        if os.path.exists("LOGO/IconsProAdvisor_Pro.png"):
            st.image("LOGO/IconsProAdvisor_Pro.png", width=80)

    with col2:
        # Display main logo if it exists
        if os.path.exists("LOGO/logo.png"):
            st.image("LOGO/logo.png", use_container_width=True)
        else:
            # Fallback to text header if logo not found
            st.title("🏠 GPP - Global Property Platform")

    with col3:
        # Empty column for spacing
        pass

    st.markdown("*Professional Property Management System with Integrated Buying Process*")

    # User Role Selection
    st.sidebar.header("👤 User Authentication")

    # Add logo to sidebar as well
    if os.path.exists("LOGO/logo.png"):
        st.sidebar.image("LOGO/logo.png", use_container_width=True)
        st.sidebar.markdown("---")

    user_role = st.sidebar.selectbox(
        "Select Your Role:",
        ["Agent", "Notary", "Buyer"],
        help="Choose your role to access the appropriate dashboard"
    )

    # Get or create current user
    current_user = get_or_create_user(user_role)

    # Store in session state for components
    st.session_state["current_user"] = current_user
    st.session_state["user_type"] = user_role.lower()

    # Check for special interfaces first (payment, uploads, etc.)
    if _handle_special_interfaces(current_user, user_role):
        return

    # Enhanced sidebar navigation with buying features
    st.sidebar.markdown("---")
    st.sidebar.header("🧭 Navigation")

    # Role-specific navigation options
    nav_options = _get_navigation_options(user_role)
    selected_nav = st.sidebar.selectbox(
        "Choose Section:",
        nav_options,
        help=f"Navigate through {user_role.lower()} features"
    )

    # Show enhanced metrics in sidebar
    if current_user:
        show_enhanced_sidebar_metrics(current_user, user_role)
        show_chat_notifications(getattr(current_user, f'{user_role.lower()}_id'), user_role.lower())

    # Route to appropriate dashboard based on selection
    route_to_enhanced_dashboard(current_user, user_role, selected_nav)


def _handle_special_interfaces(current_user, user_role):
    """Handle special interfaces like payment, document upload, etc."""

    # Payment page
    if st.session_state.get("payment_page_property"):
        property_id = st.session_state["payment_page_property"]
        st.sidebar.info("💳 Payment Process")

        if st.sidebar.button("⬅️ Back to Properties"):
            del st.session_state["payment_page_property"]
            st.rerun()

        show_payment_demo_info()
        show_payment_page(property_id, current_user)
        return True

    # Document upload modal
    if st.session_state.get("upload_docs_transaction"):
        transaction_id = st.session_state["upload_docs_transaction"]
        st.sidebar.info("📤 Document Upload")

        if st.sidebar.button("⬅️ Back to Transactions"):
            del st.session_state["upload_docs_transaction"]
            st.rerun()

        show_document_upload_modal(transaction_id, current_user, user_role.lower())
        return True

    # Notary validation interface
    if st.session_state.get("validate_transaction"):
        transaction_id = st.session_state["validate_transaction"]
        st.sidebar.info("⚖️ Document Validation")

        if st.sidebar.button("⬅️ Back to Transactions"):
            del st.session_state["validate_transaction"]
            st.rerun()

        show_notary_validation_interface(transaction_id, current_user)
        return True

    # Buying chat interface
    if st.session_state.get("buying_chat_transaction"):
        transaction_id = st.session_state["buying_chat_transaction"]
        st.sidebar.info("💬 Transaction Chat")

        if st.sidebar.button("⬅️ Back to Transactions"):
            del st.session_state["buying_chat_transaction"]
            st.rerun()

        show_integrated_buying_chat(transaction_id, current_user, user_role.lower())
        return True

    return False


def _get_navigation_options(user_role):
    """Get navigation options based on user role"""
    if user_role == "Agent":
        return [
            "🏠 Property Dashboard",
            "💰 Buying Management",
            "💬 Transaction Chats",
            "📊 Analytics",
            "👤 Profile"
        ]
    elif user_role == "Buyer":
        return [
            "🏠 Browse Properties",
            "💰 My Purchases",
            "💬 My Chats",
            "📋 Purchase History",
            "👤 Profile"
        ]
    elif user_role == "Notary":
        return [
            "⚖️ Validation Queue",
            "💰 Buying Validations",
            "💬 Transaction Chats",
            "📊 Statistics",
            "👤 Profile"
        ]


def show_enhanced_sidebar_metrics(current_user, user_role):
    """Show enhanced buying transaction metrics in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.header("💰 Buying Activity")

    try:
        user_id = getattr(current_user, f'{user_role.lower()}_id', None)
        if user_id:
            buying_transactions = get_user_buying_transactions(user_id, user_role.lower())
            active_chats = get_active_buying_chats(user_id, user_role.lower())

            if buying_transactions:
                # Show key metrics
                total_transactions = len(buying_transactions)
                active_transactions = len([
                    t for t in buying_transactions.values()
                    if t.status in ["pending", "documents_pending", "under_review"]
                ])
                completed_transactions = len([
                    t for t in buying_transactions.values()
                    if t.status == "completed"
                ])

                col1, col2 = st.sidebar.columns(2)
                with col1:
                    st.metric("Total", total_transactions)
                    st.metric("Active", active_transactions)
                with col2:
                    st.metric("Done", completed_transactions)

                    # Chat metrics
                    unread_chats = len([chat for chat in active_chats if chat["unread_count"] > 0])
                    if unread_chats > 0:
                        st.metric("💬 Unread", unread_chats, delta="New")

                # Show recent activity
                if buying_transactions:
                    st.sidebar.write("**Recent Activity:**")
                    recent_transactions = sorted(
                        buying_transactions.items(),
                        key=lambda x: x[1].last_updated,
                        reverse=True
                    )[:3]

                    for buying_id, transaction in recent_transactions:
                        status_emoji = {
                            "pending": "🟡",
                            "documents_pending": "📄",
                            "under_review": "🔍",
                            "approved": "✅",
                            "completed": "🎉",
                            "cancelled": "❌"
                        }.get(transaction.status, "⚪")

                        st.sidebar.caption(f"{status_emoji} {transaction.status.replace('_', ' ').title()}")
            else:
                st.sidebar.info("No buying activity yet")
    except Exception as e:
        st.sidebar.error(f"Error loading metrics: {e}")


def route_to_enhanced_dashboard(current_user, user_role, selected_nav):
    """Route to appropriate dashboard with enhanced buying features"""

    if user_role == "Agent":
        handle_enhanced_agent_navigation(current_user, selected_nav)
    elif user_role == "Buyer":
        handle_enhanced_buyer_navigation(current_user, selected_nav)
    elif user_role == "Notary":
        handle_enhanced_notary_navigation(current_user, selected_nav)


def handle_enhanced_agent_navigation(current_user, selected_nav):
    """Handle agent navigation with enhanced buying features"""

    if selected_nav == "🏠 Property Dashboard":
        agent_dashboard(current_user)

        # Add enhanced buying quick actions
        st.markdown("---")
        st.subheader("💰 Buying Management Quick Actions")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📊 View All Transactions", type="secondary"):
                st.session_state["show_buying_dashboard"] = True
                st.rerun()

        with col2:
            user_id = getattr(current_user, 'agent_id', None)
            if user_id:
                active_count = len([
                    t for t in get_user_buying_transactions(user_id, "agent").values()
                    if t.status in ["pending", "documents_pending", "under_review"]
                ])
                st.metric("Active Purchases", active_count)

        with col3:
            if st.button("💬 Active Chats"):
                _show_active_chats_summary(current_user, "agent")

        with col4:
            if st.button("📄 Pending Docs"):
                _show_pending_documents_summary(current_user, "agent")

    elif selected_nav == "💰 Buying Management":
        if st.session_state.get("selected_transaction"):
            show_transaction_details(
                st.session_state["selected_transaction"],
                current_user,
                "agent"
            )
            if st.button("⬅️ Back to Buying Management"):
                del st.session_state["selected_transaction"]
                st.rerun()
        else:
            show_enhanced_buying_dashboard(current_user, "agent")

    elif selected_nav == "💬 Transaction Chats":
        _show_all_transaction_chats(current_user, "agent")

    elif selected_nav == "📊 Analytics":
        show_agent_analytics(current_user)

    elif selected_nav == "👤 Profile":
        show_agent_profile(current_user)


def handle_enhanced_buyer_navigation(current_user, selected_nav):
    """Handle buyer navigation with enhanced buying features"""

    if selected_nav == "🏠 Browse Properties":
        # Check if we should show payment page first
        if st.session_state.get("payment_page_property"):
            property_id = st.session_state["payment_page_property"]

            show_payment_demo_info()
            show_payment_page(property_id, current_user)
            return

        # Show normal buyer dashboard
        buyer_dashboard(current_user)

        # Add buying initiation if property selected for purchase
        if st.session_state.get("start_buying_property"):
            property_id = st.session_state["start_buying_property"]
            from gpp.interface.utils.database import get_properties
            properties = get_properties()
            property_data = properties.get(property_id)

            if property_data:
                user_id = getattr(current_user, 'buyer_id', None)
                if user_id:
                    start_buying_process(property_id, user_id, property_data.agent_id)

            if st.button("⬅️ Back to Properties"):
                del st.session_state["start_buying_property"]
                st.rerun()

    elif selected_nav == "💰 My Purchases":
        if st.session_state.get("selected_transaction"):
            show_transaction_details(
                st.session_state["selected_transaction"],
                current_user,
                "buyer"
            )
            if st.button("⬅️ Back to My Purchases"):
                del st.session_state["selected_transaction"]
                st.rerun()
        else:
            show_enhanced_buying_dashboard(current_user, "buyer")

    elif selected_nav == "💬 My Chats":
        _show_all_transaction_chats(current_user, "buyer")

    elif selected_nav == "📋 Purchase History":
        show_buyer_purchase_history(current_user)

    elif selected_nav == "👤 Profile":
        show_buyer_profile(current_user)


def handle_enhanced_notary_navigation(current_user, selected_nav):
    """Handle notary navigation with enhanced buying features"""

    if selected_nav == "⚖️ Validation Queue":
        notary_dashboard(current_user)

    elif selected_nav == "💰 Buying Validations":
        if st.session_state.get("selected_transaction"):
            show_transaction_details(
                st.session_state["selected_transaction"],
                current_user,
                "notary"
            )
            if st.button("⬅️ Back to Buying Validations"):
                del st.session_state["selected_transaction"]
                st.rerun()
        else:
            show_enhanced_buying_dashboard(current_user, "notary")

    elif selected_nav == "💬 Transaction Chats":
        _show_all_transaction_chats(current_user, "notary")

    elif selected_nav == "📊 Statistics":
        show_notary_statistics(current_user)

    elif selected_nav == "👤 Profile":
        show_notary_profile(current_user)


def _show_active_chats_summary(current_user, user_type):
    """Show summary of active chats"""
    st.subheader("💬 Active Transaction Chats")

    user_id = getattr(current_user, f'{user_type}_id')
    active_chats = get_active_buying_chats(user_id, user_type)

    if not active_chats:
        st.info("No active chats")
        return

    for chat in active_chats:
        with st.expander(f"Transaction {chat['transaction_id'][:8]}... - {chat['status'].title()}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Status:** {chat['status'].replace('_', ' ').title()}")
                st.write(f"**Property:** {chat['property_id'][:8]}...")

            with col2:
                st.write(f"**Last Activity:** {chat['last_activity'].strftime('%m/%d %H:%M')}")
                if chat['unread_count'] > 0:
                    st.write(f"**Unread:** {chat['unread_count']} messages")

            with col3:
                if st.button("💬 Open Chat", key=f"open_chat_{chat['transaction_id']}"):
                    st.session_state["buying_chat_transaction"] = chat['transaction_id']
                    st.rerun()


def _show_pending_documents_summary(current_user, user_type):
    """Show summary of pending documents"""
    st.subheader("📄 Pending Documents")

    user_id = getattr(current_user, f'{user_type}_id')
    transactions = get_user_buying_transactions(user_id, user_type)

    pending_docs = []
    for transaction_id, transaction in transactions.items():
        if transaction.status in ["documents_pending", "under_review"]:
            from gpp.classes.buying import get_buying_progress
            progress = get_buying_progress(transaction)

            pending_docs.append({
                "transaction_id": transaction_id,
                "property_id": transaction.property_id,
                "status": transaction.status,
                "progress": progress
            })

    if not pending_docs:
        st.info("No pending documents")
        return

    for doc_info in pending_docs:
        with st.expander(f"Transaction {doc_info['transaction_id'][:8]}..."):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Property:** {doc_info['property_id'][:8]}...")
                st.write(f"**Status:** {doc_info['status'].replace('_', ' ').title()}")

            with col2:
                progress = doc_info['progress']
                st.write(f"**Documents:** {progress['validated_documents']}/{progress['total_documents']}")
                st.progress(progress['progress_percentage'] / 100)

                if st.button("📋 View Details", key=f"view_docs_{doc_info['transaction_id']}"):
                    st.session_state["selected_transaction"] = doc_info['transaction_id']
                    st.rerun()


def _show_all_transaction_chats(current_user, user_type):
    """Show all transaction chats for a user"""
    st.title("💬 All Transaction Chats")

    user_id = getattr(current_user, f'{user_type}_id')
    active_chats = get_active_buying_chats(user_id, user_type)

    if not active_chats:
        st.info("No active transaction chats")
        return

    # Chat list with quick access
    for chat in active_chats:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                st.write(f"**Transaction:** {chat['transaction_id'][:12]}...")
                st.write(f"**Property:** {chat['property_id'][:12]}...")

            with col2:
                st.write(f"**Status:** {chat['status'].replace('_', ' ').title()}")
                st.write(f"**Last Activity:** {chat['last_activity'].strftime('%m/%d %H:%M')}")

            with col3:
                if chat['unread_count'] > 0:
                    st.error(f"🔔 {chat['unread_count']} unread messages")
                else:
                    st.success("✅ All messages read")

            with col4:
                if st.button("💬 Open", key=f"open_chat_list_{chat['transaction_id']}"):
                    st.session_state["buying_chat_transaction"] = chat['transaction_id']
                    st.rerun()

            st.markdown("---")


# Fixed analytics and purchase history functions (no circular imports)
def show_buyer_purchase_history(current_user):
    """Show detailed buyer purchase history"""
    st.title("📋 Purchase History")

    user_id = getattr(current_user, 'buyer_id', None)
    if not user_id:
        st.error("Could not retrieve buyer ID")
        return

    transactions = get_user_buying_transactions(user_id, "buyer")

    if not transactions:
        st.info("📋 No purchase history yet. Start buying properties to see your history here!")
        return

    # Show completed/cancelled transactions
    completed_transactions = {
        k: v for k, v in transactions.items()
        if v.status in ["completed", "cancelled"]
    }

    if completed_transactions:
        st.subheader(f"📊 Completed Transactions ({len(completed_transactions)})")
        for txn_id, txn in completed_transactions.items():
            with st.expander(f"Transaction {txn_id[:8]}... - {txn.status.replace('_', ' ').title()}"):
                st.write(f"**Property:** {txn.property_id[:8]}...")
                st.write(f"**Price:** €{txn.final_price:,.2f}" if txn.final_price else "Price: N/A")
                st.write(f"**Status:** {txn.status.replace('_', ' ').title()}")
                st.write(f"**Date:** {txn.last_updated.strftime('%Y-%m-%d')}")
    else:
        st.info("📋 No completed purchases yet.")


def show_agent_analytics(current_user):
    """Enhanced agent analytics with buying data"""
    st.title("📊 Agent Analytics")

    user_id = getattr(current_user, 'agent_id', None)
    if not user_id:
        st.error("Could not retrieve agent ID")
        return

    transactions = get_user_buying_transactions(user_id, "agent")

    if not transactions:
        st.info("📊 No transaction data available yet.")
        return

    # Basic analytics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Transactions", len(transactions))
    with col2:
        completed = len([t for t in transactions.values() if t.status == "completed"])
        st.metric("Completed", completed)
    with col3:
        total_value = sum([float(t.final_price or 0) for t in transactions.values() if t.status == "completed"])
        st.metric("Total Sales", f"€{total_value:,.0f}")


def show_notary_statistics(current_user):
    """Enhanced notary statistics with buying data"""
    st.title("📊 Notary Statistics")

    user_id = getattr(current_user, 'notary_id', None)
    if not user_id:
        st.error("Could not retrieve notary ID")
        return

    transactions = get_user_buying_transactions(user_id, "notary")

    if not transactions:
        st.info("📊 No validation data available yet.")
        return

    # Basic statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Validations", len(transactions))
    with col2:
        pending = len([t for t in transactions.values() if t.status in ["documents_pending", "under_review"]])
        st.metric("Pending Review", pending)
    with col3:
        completed = len([t for t in transactions.values() if t.status == "completed"])
        st.metric("Completed", completed)


# Simple profile functions
def show_agent_profile(current_user):
    """Show agent profile"""
    st.title("👤 Agent Profile")
    st.info("Enhanced profile management coming soon...")


def show_buyer_profile(current_user):
    """Show buyer profile"""
    st.title("👤 Buyer Profile")
    st.info("Enhanced profile management coming soon...")


def show_notary_profile(current_user):
    """Show notary profile"""
    st.title("👤 Notary Profile")
    st.info("Enhanced profile management coming soon...")


if __name__ == "__main__":
    main()