"""
Shared chat interface component
"""

import streamlit as st
from typing import List, Optional
from datetime import datetime

from gpp.classes.chat import (
    PropertyChat, ChatMessage, add_agent_notary_message, add_buyer_agent_message,
    get_agent_notary_messages, get_buyer_agent_messages, mark_messages_as_read,
    get_unread_count
)

from gpp.interface.utils.chat_database import save_property_chat
from gpp.interface.utils.property_helpers import format_timestamp


def render_agent_notary_chat(chat: PropertyChat, current_user_id: str, current_user_type: str,
                           current_user_name: str = "", property_info=None):
    """Render chat interface between agent and notary"""

    # Show property context prominently
    if property_info:
        _render_property_context_header(property_info, "Agent-Notary Communication")
    else:
        st.subheader("💬 Agent-Notary Communication")

    if not chat.notary_id:
        st.info("Notary will be assigned when property enters validation queue.")
        return

    # Get messages for this user
    messages = get_agent_notary_messages(chat, current_user_id, current_user_type)

    if not messages:
        st.info("No messages yet. Start the conversation!")
    else:
        # Display messages
        _render_message_list(messages, current_user_id)

    # Message input
    _render_message_input(
        chat, current_user_id, current_user_type, current_user_name,
        "agent_notary", None
    )


def render_buyer_agent_chat(chat: PropertyChat, current_user_id: str, current_user_type: str,
                          current_user_name: str = "", buyer_id: str = None, property_info=None):
    """Render chat interface between buyer and agent"""

    # For buyers, buyer_id is their own ID
    if current_user_type == "buyer":
        buyer_id = current_user_id

    # Show property context prominently
    if property_info:
        if current_user_type == "buyer":
            _render_property_context_header(property_info, "Chat with Property Agent")
        else:
            _render_property_context_header(property_info, f"Chat with Buyer {buyer_id[:8]}...")
    else:
        if current_user_type == "buyer":
            st.subheader("💬 Chat with Property Agent")
        else:
            if not buyer_id:
                st.warning("No buyer selected for chat.")
                return
            st.subheader(f"💬 Chat with Buyer {buyer_id[:8]}...")

    # Get messages for this buyer-agent pair
    messages = get_buyer_agent_messages(chat, buyer_id, current_user_id, current_user_type)

    if not messages:
        st.info("No messages yet. Start the conversation!")
    else:
        # Display messages
        _render_message_list(messages, current_user_id)

    # Message input
    _render_message_input(
        chat, current_user_id, current_user_type, current_user_name,
        "buyer_agent", buyer_id
    )


def _render_property_context_header(property_info, chat_title):
    """Render property context header with key information"""
    st.subheader(f"💬 {chat_title}")

    # Property context card
    with st.container():
        # Use colored background to make it prominent
        st.markdown("""
        <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.write(f"🏠 **{property_info.title}**")
            st.write(f"📍 {property_info.address}, {property_info.city}")

        with col2:
            st.write(f"💰 **€{property_info.price:,.2f}**")
            st.write(f"📏 {property_info.dimension}")
            if property_info.number_of_rooms:
                st.write(f"🏠 {property_info.number_of_rooms} rooms")

        with col3:
            # Status indicator
            if property_info.looking_for_notary:
                st.warning("🔄 In Review")
            elif property_info.notary_attached:
                st.success("✅ Validated")
            else:
                st.info("📋 Draft")

        st.markdown("</div>", unsafe_allow_html=True)


def render_chat_sidebar_summary(chat: PropertyChat, current_user_id: str, current_user_type: str, property_info=None):
    """Render chat summary in sidebar with property context"""
    st.sidebar.subheader("💬 Chat Summary")

    # Show property info in sidebar too
    if property_info:
        st.sidebar.markdown("**🏠 Property:**")
        st.sidebar.write(f"{property_info.title}")
        st.sidebar.write(f"€{property_info.price:,.0f} - {property_info.city}")
        st.sidebar.divider()

    # Get unread counts
    unread_counts = get_unread_count(chat, current_user_id, current_user_type)

    # Agent-Notary chat summary
    if current_user_type in ["agent", "notary"]:
        agent_notary_count = len(chat.agent_notary_messages)
        unread_an = unread_counts.get("agent_notary", 0)

        if unread_an > 0:
            st.sidebar.error(f"Agent-Notary: {agent_notary_count} messages ({unread_an} unread)")
        else:
            st.sidebar.info(f"Agent-Notary: {agent_notary_count} messages")

    # Buyer chats summary
    if current_user_type == "agent":
        st.sidebar.write("**Buyer Conversations:**")
        if not chat.buyer_agent_chats:
            st.sidebar.write("No buyer conversations yet")
        else:
            for buyer_id, messages in chat.buyer_agent_chats.items():
                unread_buyer = unread_counts["buyer_chats"].get(buyer_id, 0)
                if unread_buyer > 0:
                    st.sidebar.error(f"Buyer {buyer_id[:8]}: {len(messages)} messages ({unread_buyer} unread)")
                else:
                    st.sidebar.info(f"Buyer {buyer_id[:8]}: {len(messages)} messages")

    elif current_user_type == "buyer":
        buyer_messages = chat.buyer_agent_chats.get(current_user_id, [])
        unread_buyer = unread_counts["buyer_chats"].get(current_user_id, 0)
        if unread_buyer > 0:
            st.sidebar.error(f"Your conversation: {len(buyer_messages)} messages ({unread_buyer} unread)")
        else:
            st.sidebar.info(f"Your conversation: {len(buyer_messages)} messages")


def _render_message_list(messages: List[ChatMessage], current_user_id: str):
    """Render list of chat messages"""
    # Create scrollable message container
    message_container = st.container()

    with message_container:
        for message in messages:
            _render_single_message(message, current_user_id)


def _render_single_message(message: ChatMessage, current_user_id: str):
    """Render individual message"""
    is_own_message = message.sender_id == current_user_id

    # Message container with alignment
    if is_own_message:
        col1, col2 = st.columns([1, 3])
        with col2:
            _render_message_bubble(message, is_own_message)
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            _render_message_bubble(message, is_own_message)


def _render_message_bubble(message: ChatMessage, is_own_message: bool):
    """Render message bubble"""
    # Message styling
    if message.message_type == "system":
        st.info(f"🤖 {message.message}")
    else:
        # User message
        sender_display = message.sender_name if message.sender_name else f"{message.sender_type.title()} {message.sender_id[:8]}"

        if is_own_message:
            st.success(f"**You:** {message.message}")
        else:
            st.write(f"**{sender_display}:** {message.message}")

        # Document reference if exists
        if message.document_reference:
            st.caption(f"📄 Referenced document: {message.document_reference}")

        # Timestamp
        st.caption(f"🕒 {format_timestamp(message.timestamp)}")

    st.write("")  # Add spacing


def _render_message_input(chat: PropertyChat, current_user_id: str, current_user_type: str,
                        current_user_name: str, chat_type: str, buyer_id: str):
    """Render message input form"""
    with st.form(f"message_form_{chat_type}_{buyer_id or 'notary'}", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])

        with col1:
            message_text = st.text_area(
                "Type your message:",
                height=80,
                placeholder="Type your message here...",
                label_visibility="collapsed"
            )

        with col2:
            st.write("")  # Spacing
            st.write("")  # Spacing
            submitted = st.form_submit_button("📤 Send", type="primary")

        if submitted and message_text.strip():
            # Add message to appropriate chat
            if chat_type == "agent_notary":
                updated_chat = add_agent_notary_message(
                    chat, current_user_id, current_user_type,
                    message_text.strip(), current_user_name
                )
            elif chat_type == "buyer_agent":
                updated_chat = add_buyer_agent_message(
                    chat, buyer_id, current_user_id, current_user_type,
                    message_text.strip(), current_user_name
                )

            # Save chat
            save_property_chat(updated_chat)

            # Mark own messages as read and rerun
            mark_messages_as_read(updated_chat, current_user_id, current_user_type, buyer_id)
            save_property_chat(updated_chat)

            st.rerun()


def render_buyer_selection_for_agent(chat: PropertyChat):
    """Render buyer selection interface for agents"""
    if not chat.buyer_ids:
        st.info("No buyers have started conversations yet.")
        return None

    st.subheader("👥 Select Buyer to Chat With")

    # Show buyers with message counts
    buyer_options = {}
    for buyer_id in chat.buyer_ids:
        message_count = len(chat.buyer_agent_chats.get(buyer_id, []))
        unread_count = sum(1 for msg in chat.buyer_agent_chats.get(buyer_id, [])
                          if not msg.is_read and msg.sender_type == "buyer")

        display_name = f"Buyer {buyer_id[:8]} ({message_count} messages"
        if unread_count > 0:
            display_name += f", {unread_count} unread"
        display_name += ")"

        buyer_options[display_name] = buyer_id

    if buyer_options:
        selected_display = st.selectbox("Choose buyer:", list(buyer_options.keys()))
        return buyer_options[selected_display]

    return None