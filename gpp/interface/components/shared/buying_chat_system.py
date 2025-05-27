"""
Buying Transaction Chat System
Integrated chat for agent, buyer, and notary during property transactions
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from gpp.classes.buying import Buying, add_transaction_note
from gpp.classes.chat import ChatMessage, PropertyChat, create_property_chat
from gpp.interface.utils.buying_database import save_buying_transaction, load_buying_transaction
from gpp.interface.utils.chat_database import save_chat, load_chat, get_or_create_buying_chat


class BuyingTransactionChat:
    """Enhanced chat system for buying transactions"""

    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        self.transaction = load_buying_transaction(transaction_id)
        self.chat = get_or_create_buying_chat(transaction_id)

    def add_message(self, sender_id: str, sender_type: str, message: str,
                    sender_name: str = "", message_type: str = "text",
                    document_reference: str = None) -> bool:
        """Add message to transaction chat"""
        try:
            # Create chat message
            chat_message = ChatMessage(
                sender_id=sender_id,
                sender_type=sender_type,
                sender_name=sender_name,
                message=message,
                message_type=message_type,
                document_reference=document_reference
            )

            # Add to appropriate chat channel based on participants
            if sender_type in ["agent", "notary"]:
                self.chat.agent_notary_messages.append(chat_message)

            if sender_type in ["buyer", "agent"]:
                buyer_id = self.transaction.buyer_id if sender_type == "buyer" else sender_id
                if buyer_id not in self.chat.buyer_agent_chats:
                    self.chat.buyer_agent_chats[buyer_id] = []
                self.chat.buyer_agent_chats[buyer_id].append(chat_message)

            # Update chat metadata
            self.chat.last_activity = datetime.now()

            # Also add to transaction notes for record keeping
            add_transaction_note(
                self.transaction,
                f"[CHAT] {message}",
                sender_id,
                "chat"
            )

            # Save everything
            save_chat(self.chat)
            save_buying_transaction(self.transaction)

            return True

        except Exception as e:
            st.error(f"Error adding message: {e}")
            return False

    def get_messages_for_user(self, user_id: str, user_type: str) -> Dict[str, List[ChatMessage]]:
        """Get all relevant messages for a user"""
        messages = {
            "agent_notary": [],
            "buyer_agent": []
        }

        if user_type in ["agent", "notary"]:
            # Can see agent-notary messages
            if user_type == "agent" and user_id == self.transaction.agent_id:
                messages["agent_notary"] = self.chat.agent_notary_messages
            elif user_type == "notary" and user_id == self.chat.notary_id:
                messages["agent_notary"] = self.chat.agent_notary_messages

        if user_type == "buyer":
            # Can see their own chat with agent
            messages["buyer_agent"] = self.chat.buyer_agent_chats.get(user_id, [])
        elif user_type == "agent" and user_id == self.transaction.agent_id:
            # Agent can see all buyer chats
            messages["buyer_agent"] = self.chat.buyer_agent_chats.get(self.transaction.buyer_id, [])

        return messages


def show_integrated_buying_chat(transaction_id: str, current_user, user_type: str):
    """Show integrated chat interface for buying transaction"""
    st.title("💬 Transaction Chat")

    # Initialize chat system
    chat_system = BuyingTransactionChat(transaction_id)

    if not chat_system.transaction:
        st.error("Transaction not found")
        return

    user_id = getattr(current_user, f'{user_type.lower()}_id')
    user_name = f"{user_type.title()} {user_id[:8]}..."

    # Show transaction context
    _show_transaction_context(chat_system.transaction)

    # Chat interface based on user type
    if user_type.lower() == "buyer":
        _show_buyer_chat_interface(chat_system, user_id, user_name)
    elif user_type.lower() == "agent":
        _show_agent_chat_interface(chat_system, user_id, user_name)
    elif user_type.lower() == "notary":
        _show_notary_chat_interface(chat_system, user_id, user_name)

    # Chat actions and quick responses
    _show_chat_actions(chat_system, user_id, user_type)


def _show_transaction_context(transaction: Buying):
    """Show transaction context at top of chat"""
    from gpp.interface.utils.database import get_properties
    from gpp.classes.buying import get_buying_progress, TRANSACTION_STATUSES

    properties = get_properties()
    property_data = properties.get(transaction.property_id)
    progress = get_buying_progress(transaction)

    with st.container():
        col1, col2, col3 = st.columns(3)

        with col1:
            if property_data:
                st.info(f"**🏠 Property:** {property_data.title}")
                st.caption(f"Price: €{transaction.final_price:,.2f}")
            else:
                st.info(f"**🏠 Property ID:** {transaction.property_id[:8]}...")

        with col2:
            status_display = TRANSACTION_STATUSES.get(transaction.status, transaction.status)
            st.info(f"**📊 Status:** {status_display}")
            st.caption(f"Progress: {progress['progress_percentage']:.0f}%")

        with col3:
            st.info(f"**📅 Created:** {transaction.created_date.strftime('%m/%d/%Y')}")
            st.caption(f"Last Update: {transaction.last_updated.strftime('%m/%d %H:%M')}")

    st.markdown("---")


def _show_buyer_chat_interface(chat_system: BuyingTransactionChat, user_id: str, user_name: str):
    """Chat interface for buyers - can only chat with agent"""
    st.subheader("💬 Chat with Agent")

    messages = chat_system.get_messages_for_user(user_id, "buyer")
    buyer_agent_messages = messages["buyer_agent"]

    # Display messages
    _render_chat_messages(buyer_agent_messages, user_id, "buyer")

    # Send message form
    _render_send_message_form(chat_system, user_id, "buyer", user_name, "agent")


def _show_agent_chat_interface(chat_system: BuyingTransactionChat, user_id: str, user_name: str):
    """Chat interface for agents - can chat with both buyer and notary"""

    # Tabs for different conversations
    tab1, tab2 = st.tabs(["💰 Buyer Chat", "⚖️ Notary Chat"])

    messages = chat_system.get_messages_for_user(user_id, "agent")

    with tab1:
        st.subheader("💬 Chat with Buyer")

        buyer_agent_messages = messages["buyer_agent"]
        _render_chat_messages(buyer_agent_messages, user_id, "agent")
        _render_send_message_form(chat_system, user_id, "agent", user_name, "buyer")

    with tab2:
        st.subheader("💬 Chat with Notary")

        # Check if notary is assigned
        if chat_system.chat.notary_id:
            agent_notary_messages = messages["agent_notary"]
            _render_chat_messages(agent_notary_messages, user_id, "agent")
            _render_send_message_form(chat_system, user_id, "agent", user_name, "notary")
        else:
            st.info("⏳ Notary not yet assigned to this transaction")


def _show_notary_chat_interface(chat_system: BuyingTransactionChat, user_id: str, user_name: str):
    """Chat interface for notaries - can only chat with agent"""
    st.subheader("💬 Chat with Agent")

    # Assign notary to chat if not already assigned
    if not chat_system.chat.notary_id:
        chat_system.chat.notary_id = user_id
        from gpp.interface.utils.chat_database import save_chat
        save_chat(chat_system.chat)

    messages = chat_system.get_messages_for_user(user_id, "notary")
    agent_notary_messages = messages["agent_notary"]

    # Display messages
    _render_chat_messages(agent_notary_messages, user_id, "notary")

    # Send message form
    _render_send_message_form(chat_system, user_id, "notary", user_name, "agent")


def _render_chat_messages(messages: List[ChatMessage], current_user_id: str, user_type: str):
    """Render chat messages with proper styling"""
    if not messages:
        st.info("No messages yet. Start the conversation!")
        return

    # Show messages in a scrollable container
    chat_container = st.container()

    with chat_container:
        for message in messages[-20:]:  # Show last 20 messages
            timestamp = message.timestamp.strftime('%m/%d %H:%M')

            # Determine message alignment and styling
            is_own_message = message.sender_id == current_user_id

            if is_own_message:
                # Own messages - align right, blue background
                col1, col2 = st.columns([1, 3])
                with col2:
                    st.markdown(f"""
                    <div style="background-color: #1f77b4; color: white; padding: 10px; 
                                border-radius: 10px; margin: 5px 0; text-align: right;">
                        <strong>You</strong> ({timestamp})<br>
                        {message.message}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # Other messages - align left, gray background
                col1, col2 = st.columns([3, 1])
                with col1:
                    sender_name = message.sender_name or f"{message.sender_type.title()}"
                    st.markdown(f"""
                    <div style="background-color: #f0f0f0; color: black; padding: 10px; 
                                border-radius: 10px; margin: 5px 0;">
                        <strong>{sender_name}</strong> ({timestamp})<br>
                        {message.message}
                    </div>
                    """, unsafe_allow_html=True)

            # Show document reference if exists
            if message.document_reference:
                st.caption(f"📎 Referenced document: {message.document_reference}")


def _render_send_message_form(chat_system: BuyingTransactionChat, user_id: str,
                              user_type: str, user_name: str, target_type: str):
    """Render send message form"""

    with st.form(f"send_message_{chat_system.transaction_id}_{target_type}"):
        col1, col2 = st.columns([4, 1])

        with col1:
            new_message = st.text_area(
                f"Message to {target_type.title()}:",
                placeholder=f"Type your message to the {target_type}...",
                height=100,
                key=f"message_input_{target_type}"
            )

        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing

            # Quick response buttons
            if st.form_submit_button("📤 Send", type="primary"):
                if new_message.strip():
                    success = chat_system.add_message(
                        sender_id=user_id,
                        sender_type=user_type,
                        message=new_message.strip(),
                        sender_name=user_name
                    )

                    if success:
                        st.success("Message sent!")
                        st.rerun()
                    else:
                        st.error("Failed to send message")
                else:
                    st.error("Please enter a message")


def _show_chat_actions(chat_system: BuyingTransactionChat, user_id: str, user_type: str):
    """Show quick chat actions and templates"""
    st.markdown("---")
    st.subheader("⚡ Quick Actions")

    # Quick response templates based on user type
    if user_type == "buyer":
        quick_responses = [
            "Can you provide more details about the property?",
            "When can we schedule a viewing?",
            "What documents do I need to prepare?",
            "I have uploaded the required documents.",
            "Is there any update on the transaction status?"
        ]
    elif user_type == "agent":
        quick_responses = [
            "Documents have been received and forwarded to notary.",
            "Please upload the required financial documents.",
            "Property viewing can be scheduled this week.",
            "Contract is ready for your review.",
            "Transaction is progressing well."
        ]
    else:  # notary
        quick_responses = [
            "Documents are under review.",
            "Additional documentation is required.",
            "All documents have been validated.",
            "Transaction approved for completion.",
            "Please schedule a meeting for final signing."
        ]

    # Display quick response buttons
    cols = st.columns(3)
    for i, response in enumerate(quick_responses):
        with cols[i % 3]:
            if st.button(f"💬 {response[:30]}...", key=f"quick_{i}"):
                # Determine target type
                if user_type == "buyer":
                    target_type = "agent"
                elif user_type == "agent":
                    target_type = "buyer"  # Default to buyer, could be enhanced
                else:
                    target_type = "agent"

                success = chat_system.add_message(
                    sender_id=user_id,
                    sender_type=user_type,
                    message=response,
                    sender_name=f"{user_type.title()} {user_id[:8]}..."
                )

                if success:
                    st.success("Quick response sent!")
                    st.rerun()


def show_chat_notifications(user_id: str, user_type: str):
    """Show chat notifications in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Chat Notifications")

    # This would integrate with your existing notification system
    # For now, showing a placeholder
    unread_count = 0  # This would come from actual chat system

    if unread_count > 0:
        st.sidebar.error(f"🔔 {unread_count} unread messages")
    else:
        st.sidebar.success("✅ All messages read")


# Integration with existing chat database functions
def get_or_create_buying_chat(transaction_id: str) -> PropertyChat:
    """Get or create chat for buying transaction"""
    # This integrates with your existing chat_database.py
    from gpp.interface.utils.buying_database import load_buying_transaction

    transaction = load_buying_transaction(transaction_id)
    if not transaction:
        raise ValueError("Transaction not found")

    # Try to load existing chat or create new one
    try:
        chat = load_chat(f"buying_{transaction_id}")
        if chat:
            return chat
    except:
        pass

    # Create new chat
    chat = PropertyChat(
        chat_id=f"buying_{transaction_id}",
        property_id=transaction.property_id,
        agent_id=transaction.agent_id
    )

    # Add buyer to participants
    if transaction.buyer_id not in chat.buyer_ids:
        chat.buyer_ids.append(transaction.buyer_id)
        chat.buyer_agent_chats[transaction.buyer_id] = []

    return chat


# Additional utility functions for integration
def get_active_buying_chats(user_id: str, user_type: str) -> List[Dict[str, Any]]:
    """Get all active buying chats for a user"""
    from gpp.interface.utils.buying_database import get_user_buying_transactions

    transactions = get_user_buying_transactions(user_id, user_type)
    active_chats = []

    for transaction_id, transaction in transactions.items():
        if transaction.status not in ["completed", "cancelled"]:
            chat_system = BuyingTransactionChat(transaction_id)

            # Get unread count (simplified)
            unread_count = 0  # This would be calculated from actual messages

            active_chats.append({
                "transaction_id": transaction_id,
                "property_id": transaction.property_id,
                "status": transaction.status,
                "unread_count": unread_count,
                "last_activity": chat_system.chat.last_activity
            })

    return sorted(active_chats, key=lambda x: x["last_activity"], reverse=True)