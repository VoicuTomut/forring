"""
User management utilities
"""

import streamlit as st
from gpp.classes.agent import Agent
from gpp.classes.buyer import Buyer
from gpp.classes.notary import Notary
from gpp.interface.utils.database import save_agent, save_buyer, save_notary, load_data, save_data
from gpp.interface.config.constants import BUYERS_FILE, NOTARIES_FILE


def get_or_create_user(role: str):
    """Get or create a user for the selected role"""
    session_key = f"current_{role.lower()}"

    if session_key not in st.session_state:
        if role == "Agent":
            user = Agent()
            save_agent(user)
        elif role == "Buyer":
            user = Buyer()
            buyers = load_data(BUYERS_FILE)
            buyers[user.buyer_id] = user.dict()
            save_data(BUYERS_FILE, buyers)
        elif role == "Notary":
            user = Notary()
            notaries = load_data(NOTARIES_FILE)
            notaries[user.notary_id] = user.dict()
            save_data(NOTARIES_FILE, notaries)
        else:
            raise ValueError(f"Unknown role: {role}")

        st.session_state[session_key] = user

    return st.session_state[session_key]