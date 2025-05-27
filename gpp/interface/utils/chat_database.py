"""
Chat database operations
Extended with buying transaction chat functionality
"""

import json
import os
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import streamlit as st

from gpp.classes.chat import PropertyChat, ChatMessage
from gpp.interface.config.constants import DATA_DIR

# Chat data files
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")
BUYING_CHATS_FILE = os.path.join(DATA_DIR, "buying_chats.json")


def init_chat_storage():
    """Initialize chat storage files"""
    # Initialize regular property chats
    if not os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, 'w') as f:
            json.dump({}, f)

    # Initialize buying transaction chats
    if not os.path.exists(BUYING_CHATS_FILE):
        with open(BUYING_CHATS_FILE, 'w') as f:
            json.dump({}, f)


def load_chat_data() -> dict:
    """Load regular property chat data from file"""
    try:
        with open(CHATS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def load_buying_chat_data() -> dict:
    """Load buying transaction chat data from file"""
    try:
        with open(BUYING_CHATS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_chat_data(data: dict):
    """Save regular property chat data to file"""
    with open(CHATS_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def save_buying_chat_data(data: dict):
    """Save buying transaction chat data to file"""
    with open(BUYING_CHATS_FILE, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def get_property_chat(property_id: str) -> Optional[PropertyChat]:
    """Get chat for a property"""
    data = load_chat_data()
    if property_id in data:
        try:
            return PropertyChat(**data[property_id])
        except Exception as e:
            st.error(f"Error loading chat for property {property_id}: {e}")
    return None


def save_property_chat(chat: PropertyChat):
    """Save property chat"""
    data = load_chat_data()
    data[chat.property_id] = chat.dict()
    save_chat_data(data)


def get_all_chats_for_user(user_id: str, user_type: str) -> Dict[str, PropertyChat]:
    """Get all chats where user is a participant"""
    data = load_chat_data()
    user_chats = {}

    for property_id, chat_data in data.items():
        try:
            chat = PropertyChat(**chat_data)

            # Check if user is participant
            is_participant = False

            if user_type == "agent" and chat.agent_id == user_id:
                is_participant = True
            elif user_type == "notary" and chat.notary_id == user_id:
                is_participant = True
            elif user_type == "buyer" and user_id in chat.buyer_ids:
                is_participant = True

            if is_participant:
                user_chats[property_id] = chat

        except Exception as e:
            st.error(f"Error loading chat {property_id}: {e}")

    return user_chats


def create_or_get_property_chat(property_id: str, agent_id: str) -> PropertyChat:
    """Create new chat or get existing one for property"""
    existing_chat = get_property_chat(property_id)

    if existing_chat:
        return existing_chat

    # Create new chat
    from gpp.classes.chat import create_property_chat
    new_chat = create_property_chat(property_id, agent_id)
    save_property_chat(new_chat)
    return new_chat


# ================================
# BUYING TRANSACTION CHAT FUNCTIONS
# ================================

def convert_datetime_to_json(obj):
    """Convert datetime objects to ISO strings for JSON serialization"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_datetime_to_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_json(item) for item in obj]
    return obj


def convert_datetime_from_json(obj):
    """Convert ISO strings back to datetime objects"""
    if isinstance(obj, str):
        # Try to parse as datetime
        for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return datetime.strptime(obj, fmt)
            except ValueError:
                continue
        return obj
    elif isinstance(obj, dict):
        return {k: convert_datetime_from_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_from_json(item) for item in obj]
    return obj


def get_buying_chat(chat_id: str) -> Optional[PropertyChat]:
    """Get buying transaction chat by ID"""
    data = load_buying_chat_data()
    if chat_id in data:
        try:
            chat_dict = convert_datetime_from_json(data[chat_id])
            return PropertyChat(**chat_dict)
        except Exception as e:
            st.error(f"Error loading buying chat {chat_id}: {e}")
    return None


def save_buying_chat(chat: PropertyChat):
    """Save buying transaction chat"""
    data = load_buying_chat_data()
    chat_dict = convert_datetime_to_json(chat.dict())
    data[chat.chat_id] = chat_dict
    save_buying_chat_data(data)


def get_or_create_buying_chat(transaction_id: str) -> PropertyChat:
    """Get or create chat for buying transaction"""
    from gpp.interface.utils.buying_database import load_buying_transaction

    chat_id = f"buying_{transaction_id}"

    # Try to load existing chat
    existing_chat = get_buying_chat(chat_id)
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
    data = load_buying_chat_data()
    chats = {}

    for chat_id, chat_data in data.items():
        try:
            chat_dict = convert_datetime_from_json(chat_data)
            chats[chat_id] = PropertyChat(**chat_dict)
        except Exception as e:
            st.error(f"Error loading buying chat {chat_id}: {e}")

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


def mark_messages_as_read(chat: PropertyChat, user_id: str, user_type: str,
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


def get_chat_notifications(user_id: str, user_type: str) -> List[Dict[str, any]]:
    """Get chat notifications for a user (both regular and buying chats)"""
    notifications = []

    # Get regular property chat notifications
    regular_chats = get_all_chats_for_user(user_id, user_type)
    for property_id, chat in regular_chats.items():
        unread_count = get_unread_messages_count(chat, user_id, user_type)
        if unread_count > 0:
            notifications.append({
                "type": "property",
                "id": property_id,
                "unread_count": unread_count,
                "last_activity": chat.last_activity
            })

    # Get buying chat notifications
    buying_chats = get_user_buying_chats(user_id, user_type)
    for chat_id, chat in buying_chats.items():
        unread_count = get_unread_messages_count(chat, user_id, user_type)
        if unread_count > 0:
            notifications.append({
                "type": "buying",
                "id": chat_id,
                "property_id": chat.property_id,
                "unread_count": unread_count,
                "last_activity": chat.last_activity
            })

    # Sort by most recent activity
    notifications.sort(key=lambda x: x["last_activity"], reverse=True)

    return notifications


def get_active_buying_chats(user_id: str, user_type: str) -> List[Dict[str, any]]:
    """Get all active buying chats for a user with metadata"""
    buying_chats = get_user_buying_chats(user_id, user_type)
    active_chats = []

    for chat_id, chat in buying_chats.items():
        # Extract transaction ID from chat ID
        transaction_id = chat_id.replace("buying_", "") if chat_id.startswith("buying_") else None

        if transaction_id:
            try:
                from gpp.interface.utils.buying_database import load_buying_transaction
                transaction = load_buying_transaction(transaction_id)

                if transaction and transaction.status not in ["completed", "cancelled"]:
                    unread_count = get_unread_messages_count(chat, user_id, user_type)

                    active_chats.append({
                        "transaction_id": transaction_id,
                        "property_id": chat.property_id,
                        "status": transaction.status,
                        "unread_count": unread_count,
                        "last_activity": chat.last_activity
                    })
            except Exception as e:
                st.error(f"Error loading transaction for chat {chat_id}: {e}")

    return sorted(active_chats, key=lambda x: x["last_activity"], reverse=True)


def delete_buying_chat(chat_id: str) -> bool:
    """Delete buying transaction chat"""
    data = load_buying_chat_data()

    if chat_id in data:
        del data[chat_id]
        save_buying_chat_data(data)
        return True

    return False


def cleanup_old_chats(days_old: int = 30) -> int:
    """Clean up old chats for completed transactions"""
    deleted_count = 0
    cutoff_date = datetime.now() - timedelta(days=days_old)

    # Clean up buying chats
    all_buying_chats = get_all_buying_chats()

    for chat_id, chat in all_buying_chats.items():
        if chat_id.startswith("buying_"):
            transaction_id = chat_id[7:]  # Remove "buying_" prefix

            try:
                from gpp.interface.utils.buying_database import load_buying_transaction
                transaction = load_buying_transaction(transaction_id)

                if (transaction and
                    transaction.status in ["completed", "cancelled"] and
                    transaction.last_updated < cutoff_date):

                    if delete_buying_chat(chat_id):
                        deleted_count += 1
            except Exception:
                pass

    return deleted_count


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


# ================================
# UNIFIED CHAT FUNCTIONS
# ================================

def save_chat(chat: PropertyChat):
    """Save chat - works for both property and buying chats"""
    if chat.chat_id.startswith("buying_"):
        save_buying_chat(chat)
    else:
        save_property_chat(chat)


def load_chat(chat_id: str) -> Optional[PropertyChat]:
    """Load chat - works for both property and buying chats"""
    if chat_id.startswith("buying_"):
        return get_buying_chat(chat_id)
    else:
        # For property chats, chat_id is the property_id
        return get_property_chat(chat_id)


def get_or_create_chat(chat_id: str, property_id: str = None,
                      agent_id: str = None) -> PropertyChat:
    """Get or create chat - works for both types"""
    if chat_id.startswith("buying_"):
        transaction_id = chat_id[7:]  # Remove "buying_" prefix
        return get_or_create_buying_chat(transaction_id)
    else:
        return create_or_get_property_chat(property_id or chat_id, agent_id)


# Initialize chat storage when module is imported
init_chat_storage()