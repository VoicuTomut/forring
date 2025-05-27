"""
Chat system classes for GPP Platform
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
import uuid


class ChatMessage(BaseModel):
    """Individual chat message"""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = Field(..., description="ID of the message sender")
    sender_type: Literal["agent", "notary", "buyer", "system"] = Field(..., description="Type of sender")
    sender_name: str = Field(default="", description="Display name of sender")
    message: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    message_type: Literal["text", "document_reference", "system"] = Field(default="text")
    document_reference: Optional[str] = Field(None, description="Referenced document ID if applicable")
    is_read: bool = Field(default=False, description="Message read status")


class PropertyChat(BaseModel):
    """Chat for a specific property with privacy controls"""
    chat_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str = Field(..., description="Property this chat belongs to")
    agent_id: str = Field(..., description="Agent managing the property")

    # Chat channels with privacy separation
    agent_notary_messages: List[ChatMessage] = Field(
        default_factory=list,
        description="Private messages between agent and notary"
    )

    # Buyer conversations - each buyer has separate private chat with agent
    buyer_agent_chats: Dict[str, List[ChatMessage]] = Field(
        default_factory=dict,
        description="Private chats between each buyer and agent (buyer_id -> messages)"
    )

    # Participants tracking
    notary_id: Optional[str] = Field(None, description="Notary assigned to property")
    buyer_ids: List[str] = Field(default_factory=list, description="Buyers who have chatted")

    # Chat metadata
    created_date: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True)


# Helper functions for chat management
def create_property_chat(property_id: str, agent_id: str) -> PropertyChat:
    """Create a new property chat"""
    return PropertyChat(
        property_id=property_id,
        agent_id=agent_id
    )


def add_agent_notary_message(chat: PropertyChat, sender_id: str, sender_type: str,
                           message: str, sender_name: str = "",
                           document_reference: str = None) -> PropertyChat:
    """Add message to agent-notary private chat"""
    new_message = ChatMessage(
        sender_id=sender_id,
        sender_type=sender_type,
        sender_name=sender_name,
        message=message,
        document_reference=document_reference
    )

    chat.agent_notary_messages.append(new_message)
    chat.last_activity = datetime.now()

    return chat


def add_buyer_agent_message(chat: PropertyChat, buyer_id: str, sender_id: str,
                          sender_type: str, message: str, sender_name: str = "") -> PropertyChat:
    """Add message to buyer-agent private chat"""
    # Initialize buyer chat if doesn't exist
    if buyer_id not in chat.buyer_agent_chats:
        chat.buyer_agent_chats[buyer_id] = []
        if buyer_id not in chat.buyer_ids:
            chat.buyer_ids.append(buyer_id)

    new_message = ChatMessage(
        sender_id=sender_id,
        sender_type=sender_type,
        sender_name=sender_name,
        message=message
    )

    chat.buyer_agent_chats[buyer_id].append(new_message)
    chat.last_activity = datetime.now()

    return chat


def assign_notary_to_chat(chat: PropertyChat, notary_id: str) -> PropertyChat:
    """Assign notary to property chat"""
    chat.notary_id = notary_id
    return chat


def get_agent_notary_messages(chat: PropertyChat, user_id: str, user_type: str) -> List[ChatMessage]:
    """Get agent-notary messages (only for agent or notary)"""
    if user_type not in ["agent", "notary"]:
        return []

    if user_type == "agent" and user_id != chat.agent_id:
        return []

    if user_type == "notary" and user_id != chat.notary_id:
        return []

    return chat.agent_notary_messages


def get_buyer_agent_messages(chat: PropertyChat, buyer_id: str, user_id: str,
                           user_type: str) -> List[ChatMessage]:
    """Get buyer-agent messages (only for the specific buyer or the agent)"""
    if user_type == "buyer" and user_id != buyer_id:
        return []  # Buyers can't see other buyers' chats

    if user_type == "agent" and user_id != chat.agent_id:
        return []

    if user_type == "notary":
        return []  # Notaries can't see buyer-agent chats

    return chat.buyer_agent_chats.get(buyer_id, [])


def get_unread_count(chat: PropertyChat, user_id: str, user_type: str) -> Dict[str, int]:
    """Get unread message counts for a user"""
    unread_counts = {
        "agent_notary": 0,
        "buyer_chats": {}
    }

    if user_type in ["agent", "notary"]:
        # Count unread in agent-notary chat
        for msg in chat.agent_notary_messages:
            if msg.sender_id != user_id and not msg.is_read:
                unread_counts["agent_notary"] += 1

    if user_type == "agent":
        # Count unread in all buyer chats
        for buyer_id, messages in chat.buyer_agent_chats.items():
            unread_count = 0
            for msg in messages:
                if msg.sender_id != user_id and not msg.is_read:
                    unread_count += 1
            if unread_count > 0:
                unread_counts["buyer_chats"][buyer_id] = unread_count

    elif user_type == "buyer":
        # Count unread in this buyer's chat with agent
        buyer_messages = chat.buyer_agent_chats.get(user_id, [])
        unread_count = 0
        for msg in buyer_messages:
            if msg.sender_id != user_id and not msg.is_read:
                unread_count += 1
        if unread_count > 0:
            unread_counts["buyer_chats"][user_id] = unread_count

    return unread_counts


def mark_messages_as_read(chat: PropertyChat, user_id: str, user_type: str,
                        buyer_id: str = None) -> PropertyChat:
    """Mark messages as read for a user"""
    if user_type in ["agent", "notary"] and not buyer_id:
        # Mark agent-notary messages as read
        for msg in chat.agent_notary_messages:
            if msg.sender_id != user_id:
                msg.is_read = True

    if buyer_id and buyer_id in chat.buyer_agent_chats:
        # Mark buyer-agent messages as read
        for msg in chat.buyer_agent_chats[buyer_id]:
            if msg.sender_id != user_id:
                msg.is_read = True

    return chat


def add_system_message(chat: PropertyChat, message: str, target_chat: str = "agent_notary") -> PropertyChat:
    """Add system message (e.g., 'Property approved', 'Document uploaded')"""
    system_message = ChatMessage(
        sender_id="system",
        sender_type="system",
        sender_name="System",
        message=message,
        message_type="system"
    )

    if target_chat == "agent_notary":
        chat.agent_notary_messages.append(system_message)

    chat.last_activity = datetime.now()
    return chat