"""
Chat Database Integration for Buying Transactions
Extends existing chat_database.py with buying transaction chat functionality
"""

import json
import os
from typing import Dict, Optional, List
from datetime import datetime

from gpp.classes.chat import PropertyChat, ChatMessage
from gpp.interface.utils.database import load_data, save_data

# File paths
BUYING_CHATS_FILE = "data/buying_chats.json"


def init_buying_chat_database():
    """Initialize buying chat database file"""
    if not os.path.exists(BUYING_CHATS_FILE):
        save_data(BUYING_CHATS_FILE, {})


def save_buying_chat(chat: PropertyChat):
    """Save buying transaction chat to database"""
    init_buying_chat_database()

    # Load existing chats
    chats = load_data(BUYING_CHATS_FILE)

    # Convert to dict and handle datetime serialization
    chat_dict = chat.dict()

    # Convert datetime objects to ISO strings
    def convert_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime(item) for item in obj]
        return obj

    chat_dict = convert_datetime(chat_dict)

    # Save chat
    chats[chat.chat_id] = chat_dict
    save_data(BUYING_CHATS_FILE, chats)


def load_buying_chat(chat_id: str) -> Optional[PropertyChat]:
    """Load buying transaction chat from database"""
    init_buying_chat_database()

    chats = load_data(BUYING_CHATS_FILE)

    if chat_id not in chats:
        return None

    chat_dict = chats[chat_id]

    # Convert ISO strings back to datetime objects
    def convert_from_json(obj):
        if isinstance(obj, str):
            # Try to parse as datetime
            for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(obj, fmt)
                except ValueError:
                    continue
            return obj
        elif isinstance(obj, dict):
            return {k: convert_from_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_from_json(item) for item in obj]
        return obj

    chat_dict = convert_from_json(chat_dict)

    return PropertyChat(**chat_dict)


def get_or_create_buying_transaction_chat(transaction_id: str) -> PropertyChat:
    """Get or create chat for buying transaction"""
    from gpp.interface.utils.buying_database import load_buying_transaction

    chat_id = f"buying_{transaction_id}"

    # Try to load existing chat
    existing_chat = load_buying_chat(chat_id)
    if existing_chat:
        return existing_chat

    # Load transaction to get details
    transaction = load_buying_transaction(transaction_id)
    if not transaction:
        raise ValueError(f"Transaction {transaction_id} not found")

    # Create new chat
    chat = PropertyChat(
        chat_id=chat_id,
        property_id=transaction.property_id,
        agent_id=transaction.agent_id
    )

    # Add buyer to participants
    if transaction.buyer_id not in chat.buyer_ids:
        chat.buyer_ids.append(transaction.buyer_id)
        chat.buyer_agent_chats[transaction.buyer_id] = []

    # Save new chat
    save_buying_chat(chat)

    return chat


def get_all_buying_chats() -> Dict[str, PropertyChat]:
    """Get all buying transaction chats"""
    init_buying_chat_database()

    chats_dict = load_data(BUYING_CHATS_FILE)
    chats = {}

    for chat_id, chat_data in chats_dict.items():
        chat = load_buying_chat(chat_id)
        if chat:
            chats[chat_id] = chat

    return chats


def get_user_buying_chats(user_id: str, user_type: str) -> Dict[str, PropertyChat]:
    """Get buying chats relevant to a specific user"""
    all_chats = get_all_buying_chats()
    relevant_chats = {}

    for chat_id, chat in all_chats.items():
        if user_type == "agent" and chat.agent_id == user_id:
            relevant_chats[chat_id] = chat
        elif user_type == "buyer" and user_id in chat.buyer_ids:
            relevant_chats[chat_id] = chat
        elif user_type == "notary" and chat.notary_id == user_id:
            relevant_chats[chat_id] = chat

    return relevant_chats


def get_unread_messages_count(chat: PropertyChat, user_id: str, user_type: str) -> int:
    """Get count of unread messages for a user in a chat"""
    unread_count = 0

    if user_type in ["agent", "notary"]:
        # Check agent-notary messages
        for msg in chat.agent_notary_messages:
            if msg.sender_id != user_id and not msg.is_read:
                unread_count += 1

    if user_type == "agent":
        # Check all buyer chats for agent
        for buyer_id, messages in chat.buyer_agent_chats.items():
            for msg in messages:
                if msg.sender_id != user_id and not msg.is_read:
                    unread_count += 1
    elif user_type == "buyer":
        # Check this buyer's chat with agent
        buyer_messages = chat.buyer_agent_chats.get(user_id, [])
        for msg in buyer_messages:
            if msg.sender_id != user_id and not msg.is_read:
                unread_count += 1

    return unread_count


def mark_messages_as_read_in_chat(chat: PropertyChat, user_id: str, user_type: str,
                                  buyer_id: str = None) -> PropertyChat:
    """Mark messages as read for a user in a chat"""
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


def delete_buying_chat(chat_id: str) -> bool:
    """Delete buying transaction chat"""
    init_buying_chat_database()

    chats = load_data(BUYING_CHATS_FILE)

    if chat_id in chats:
        del chats[chat_id]
        save_data(BUYING_CHATS_FILE, chats)
        return True

    return False


def search_chat_messages(chat: PropertyChat, search_term: str, user_id: str,
                         user_type: str) -> List[ChatMessage]:
    """Search for messages containing a term"""
    matching_messages = []

    # Search in agent-notary messages
    if user_type in ["agent", "notary"]:
        for msg in chat.agent_notary_messages:
            if search_term.lower() in msg.message.lower():
                matching_messages.append(msg)

    # Search in buyer-agent messages
    if user_type == "buyer" and user_id in chat.buyer_agent_chats:
        for msg in chat.buyer_agent_chats[user_id]:
            if search_term.lower() in msg.message.lower():
                matching_messages.append(msg)
    elif user_type == "agent":
        for buyer_id, messages in chat.buyer_agent_chats.items():
            for msg in messages:
                if search_term.lower() in msg.message.lower():
                    matching_messages.append(msg)

    # Sort by timestamp
    matching_messages.sort(key=lambda x: x.timestamp, reverse=True)

    return matching_messages


def get_chat_statistics(chat: PropertyChat) -> Dict[str, any]:
    """Get statistics for a chat"""
    stats = {
        "total_messages": 0,
        "agent_notary_messages": len(chat.agent_notary_messages),
        "buyer_agent_messages": 0,
        "participants": len(chat.buyer_ids) + 1,  # +1 for agent
        "created_date": chat.created_date,
        "last_activity": chat.last_activity,
        "most_active_participant": None,
        "message_count_by_user": {}
    }

    # Count buyer-agent messages
    for buyer_id, messages in chat.buyer_agent_chats.items():
        stats["buyer_agent_messages"] += len(messages)

        # Count messages by user
        for msg in messages:
            if msg.sender_id not in stats["message_count_by_user"]:
                stats["message_count_by_user"][msg.sender_id] = 0
            stats["message_count_by_user"][msg.sender_id] += 1

    # Count agent-notary messages by user
    for msg in chat.agent_notary_messages:
        if msg.sender_id not in stats["message_count_by_user"]:
            stats["message_count_by_user"][msg.sender_id] = 0
        stats["message_count_by_user"][msg.sender_id] += 1

    # Find most active participant
    if stats["message_count_by_user"]:
        most_active = max(stats["message_count_by_user"].items(), key=lambda x: x[1])
        stats["most_active_participant"] = most_active[0]

    stats["total_messages"] = stats["agent_notary_messages"] + stats["buyer_agent_messages"]

    return stats


def export_chat_history(chat: PropertyChat, format: str = "json") -> str:
    """Export chat history in specified format"""
    if format == "json":
        return json.dumps(chat.dict(), indent=2, default=str)

    elif format == "text":
        output = f"Chat History - {chat.chat_id}\n"
        output += f"Property: {chat.property_id}\n"
        output += f"Created: {chat.created_date}\n"
        output += "=" * 50 + "\n\n"

        # Agent-Notary Messages
        if chat.agent_notary_messages:
            output += "AGENT-NOTARY CONVERSATION\n"
            output += "-" * 30 + "\n"
            for msg in chat.agent_notary_messages:
                output += f"[{msg.timestamp}] {msg.sender_name or msg.sender_type}: {msg.message}\n"
            output += "\n"

        # Buyer-Agent Messages
        for buyer_id, messages in chat.buyer_agent_chats.items():
            if messages:
                output += f"BUYER-AGENT CONVERSATION (Buyer: {buyer_id[:8]}...)\n"
                output += "-" * 30 + "\n"
                for msg in messages:
                    output += f"[{msg.timestamp}] {msg.sender_name or msg.sender_type}: {msg.message}\n"
                output += "\n"

        return output

    else:
        raise ValueError("Unsupported export format. Use 'json' or 'text'")


def cleanup_old_chats(days_old: int = 30) -> int:
    """Clean up chats older than specified days for completed transactions"""
    from gpp.interface.utils.buying_database import get_all_buying_transactions

    all_chats = get_all_buying_chats()
    all_transactions = get_all_buying_transactions()

    deleted_count = 0
    cutoff_date = datetime.now() - timedelta(days=days_old)

    for chat_id, chat in all_chats.items():
        # Extract transaction ID from chat ID
        if chat_id.startswith("buying_"):
            transaction_id = chat_id[7:]  # Remove "buying_" prefix

            # Check if transaction is completed and old enough
            if transaction_id in all_transactions:
                transaction = all_transactions[transaction_id]
                if (transaction.status in ["completed", "cancelled"] and
                        transaction.last_updated < cutoff_date):

                    if delete_buying_chat(chat_id):
                        deleted_count += 1

    return deleted_count


# Integration functions with existing chat system
def integrate_with_existing_chat_system():
    """Integration functions to work with existing chat_database.py"""

    # These functions bridge the gap between buying chats and property chats
    def save_chat(chat: PropertyChat):
        """Save chat - works for both property and buying chats"""
        if chat.chat_id.startswith("buying_"):
            save_buying_chat(chat)
        else:
            # Use existing property chat save function
            from gpp.interface.utils.chat_database import save_property_chat
            save_property_chat(chat)

    def load_chat(chat_id: str) -> Optional[PropertyChat]:
        """Load chat - works for both property and buying chats"""
        if chat_id.startswith("buying_"):
            return load_buying_chat(chat_id)
        else:
            # Use existing property chat load function
            from gpp.interface.utils.chat_database import load_property_chat
            return load_property_chat(chat_id)

    def get_or_create_chat(chat_id: str, property_id: str = None,
                           agent_id: str = None) -> PropertyChat:
        """Get or create chat - works for both types"""
        if chat_id.startswith("buying_"):
            return get_or_create_buying_transaction_chat(chat_id[7:])  # Remove "buying_" prefix
        else:
            # Use existing property chat creation
            from gpp.interface.utils.chat_database import create_or_get_property_chat
            return create_or_get_property_chat(property_id, agent_id)

    return save_chat, load_chat, get_or_create_chat


# Additional utility functions for the UI
def get_chat_preview(chat: PropertyChat, user_id: str, user_type: str) -> Dict[str, any]:
    """Get a preview of the chat for display in lists"""
    last_message = None
    unread_count = get_unread_messages_count(chat, user_id, user_type)

    # Get the most recent message
    all_messages = []

    if user_type in ["agent", "notary"]:
        all_messages.extend(chat.agent_notary_messages)

    if user_type == "buyer" and user_id in chat.buyer_agent_chats:
        all_messages.extend(chat.buyer_agent_chats[user_id])
    elif user_type == "agent":
        for messages in chat.buyer_agent_chats.values():
            all_messages.extend(messages)

    if all_messages:
        last_message = max(all_messages, key=lambda x: x.timestamp)

    return {
        "chat_id": chat.chat_id,
        "property_id": chat.property_id,
        "last_message": {
            "text": last_message.message[:50] + "..." if last_message and len(
                last_message.message) > 50 else last_message.message if last_message else "No messages",
            "sender": last_message.sender_name or last_message.sender_type if last_message else "System",
            "timestamp": last_message.timestamp if last_message else chat.created_date
        },
        "unread_count": unread_count,
        "is_active": chat.is_active,
        "participants_count": len(chat.buyer_ids) + 1 + (1 if chat.notary_id else 0)
    }


def get_chat_notifications(user_id: str, user_type: str) -> List[Dict[str, any]]:
    """Get chat notifications for a user"""
    user_chats = get_user_buying_chats(user_id, user_type)
    notifications = []

    for chat_id, chat in user_chats.items():
        unread_count = get_unread_messages_count(chat, user_id, user_type)

        if unread_count > 0:
            # Get the most recent unread message
            recent_unread = None

            if user_type in ["agent", "notary"]:
                for msg in reversed(chat.agent_notary_messages):
                    if msg.sender_id != user_id and not msg.is_read:
                        recent_unread = msg
                        break

            if user_type == "buyer" and user_id in chat.buyer_agent_chats:
                for msg in reversed(chat.buyer_agent_chats[user_id]):
                    if msg.sender_id != user_id and not msg.is_read:
                        recent_unread = msg
                        break
            elif user_type == "agent":
                for messages in chat.buyer_agent_chats.values():
                    for msg in reversed(messages):
                        if msg.sender_id != user_id and not msg.is_read:
                            if not recent_unread or msg.timestamp > recent_unread.timestamp:
                                recent_unread = msg

            if recent_unread:
                notifications.append({
                    "chat_id": chat_id,
                    "property_id": chat.property_id,
                    "unread_count": unread_count,
                    "recent_message": {
                        "text": recent_unread.message[:100],
                        "sender": recent_unread.sender_name or recent_unread.sender_type,
                        "timestamp": recent_unread.timestamp
                    }
                })

    # Sort by most recent message
    notifications.sort(key=lambda x: x["recent_message"]["timestamp"], reverse=True)

    return notifications


def bulk_mark_as_read(user_id: str, user_type: str, chat_ids: List[str] = None):
    """Mark multiple chats as read for a user"""
    if chat_ids is None:
        # Mark all chats as read
        user_chats = get_user_buying_chats(user_id, user_type)
        chat_ids = list(user_chats.keys())

    for chat_id in chat_ids:
        chat = load_buying_chat(chat_id)
        if chat:
            if user_type == "buyer":
                chat = mark_messages_as_read_in_chat(chat, user_id, user_type, user_id)
            else:
                chat = mark_messages_as_read_in_chat(chat, user_id, user_type)
            save_buying_chat(chat)


# Database maintenance functions
def validate_chat_integrity():
    """Validate chat database integrity"""
    issues = []
    all_chats = get_all_buying_chats()

    from gpp.interface.utils.buying_database import get_all_buying_transactions
    all_transactions = get_all_buying_transactions()

    for chat_id, chat in all_chats.items():
        # Check if buying chat has corresponding transaction
        if chat_id.startswith("buying_"):
            transaction_id = chat_id[7:]
            if transaction_id not in all_transactions:
                issues.append(f"Chat {chat_id} has no corresponding transaction")

        # Check if property_id exists
        from gpp.interface.utils.database import get_properties
        properties = get_properties()
        if chat.property_id not in properties:
            issues.append(f"Chat {chat_id} references non-existent property {chat.property_id}")

        # Validate message structure
        for msg in chat.agent_notary_messages:
            if not hasattr(msg, 'message_id') or not hasattr(msg, 'timestamp'):
                issues.append(f"Invalid message structure in chat {chat_id}")

        for buyer_id, messages in chat.buyer_agent_chats.items():
            for msg in messages:
                if not hasattr(msg, 'message_id') or not hasattr(msg, 'timestamp'):
                    issues.append(f"Invalid message structure in buyer chat {chat_id}")

    return issues


def repair_chat_database():
    """Repair common chat database issues"""
    repaired_count = 0
    all_chats = get_all_buying_chats()

    for chat_id, chat in all_chats.items():
        modified = False

        # Ensure all messages have required fields
        for msg in chat.agent_notary_messages:
            if not hasattr(msg, 'is_read'):
                msg.is_read = False
                modified = True
            if not hasattr(msg, 'message_type'):
                msg.message_type = "text"
                modified = True

        for buyer_id, messages in chat.buyer_agent_chats.items():
            for msg in messages:
                if not hasattr(msg, 'is_read'):
                    msg.is_read = False
                    modified = True
                if not hasattr(msg, 'message_type'):
                    msg.message_type = "text"
                    modified = True

        # Ensure chat has required metadata
        if not hasattr(chat, 'is_active'):
            chat.is_active = True
            modified = True

        if modified:
            save_buying_chat(chat)
            repaired_count += 1

    return repaired_count


# Export the main functions for use in other modules
__all__ = [
    'init_buying_chat_database',
    'save_buying_chat',
    'load_buying_chat',
    'get_or_create_buying_transaction_chat',
    'get_all_buying_chats',
    'get_user_buying_chats',
    'get_unread_messages_count',
    'mark_messages_as_read_in_chat',
    'search_chat_messages',
    'get_chat_statistics',
    'export_chat_history',
    'get_chat_preview',
    'get_chat_notifications',
    'bulk_mark_as_read',
    'validate_chat_integrity',
    'repair_chat_database',
    'integrate_with_existing_chat_system'
]