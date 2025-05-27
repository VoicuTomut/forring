"""
Chat database operations
"""

import json
import os
from typing import Dict, Optional
import streamlit as st

from gpp.classes.chat import PropertyChat
from gpp.interface.config.constants import DATA_DIR

# Chat data file
CHATS_FILE = os.path.join(DATA_DIR, "chats.json")


def init_chat_storage():
    """Initialize chat storage file"""
    if not os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, 'w') as f:
            json.dump({}, f)


def load_chat_data() -> dict:
    """Load chat data from file"""
    try:
        with open(CHATS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_chat_data(data: dict):
    """Save chat data to file"""
    with open(CHATS_FILE, 'w') as f:
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