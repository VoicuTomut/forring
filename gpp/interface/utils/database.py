"""
Database operations and data management utilities
"""

import json
import os
import streamlit as st
from decimal import Decimal
from typing import Dict

from gpp.interface.config.constants import (
    DATA_DIR, PROPERTIES_FILE, DOCUMENTS_FILE, AGENTS_FILE,
    BUYERS_FILE, NOTARIES_FILE, BUYING_FILE
)
from gpp.classes.property import Property
from gpp.classes.document import Document
from gpp.classes.agent import Agent
from gpp.classes.buyer import Buyer
from gpp.classes.notary import Notary


def init_data_files():
    """Initialize data files if they don't exist"""
    os.makedirs(DATA_DIR, exist_ok=True)

    files = [PROPERTIES_FILE, DOCUMENTS_FILE, AGENTS_FILE, BUYERS_FILE, NOTARIES_FILE, BUYING_FILE]
    for file_path in files:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)


def load_data(file_path: str) -> dict:
    """Load data from JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_data(file_path: str, data: dict):
    """Save data to JSON file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


# Property operations
def get_properties() -> Dict[str, Property]:
    """Get all properties from database"""
    data = load_data(PROPERTIES_FILE)
    properties = {}
    for prop_id, prop_data in data.items():
        try:
            # Convert price back to Decimal
            if 'price' in prop_data:
                prop_data['price'] = Decimal(str(prop_data['price']))
            properties[prop_id] = Property(**prop_data)
        except Exception as e:
            st.error(f"Error loading property {prop_id}: {e}")
    return properties


def save_property(property_obj: Property):
    """Save property to database"""
    properties = load_data(PROPERTIES_FILE)
    properties[property_obj.property_id] = property_obj.dict()
    save_data(PROPERTIES_FILE, properties)


# Document operations
def get_documents() -> Dict[str, Document]:
    """Get all documents from database"""
    data = load_data(DOCUMENTS_FILE)
    documents = {}
    for doc_id, doc_data in data.items():
        try:
            documents[doc_id] = Document(**doc_data)
        except Exception as e:
            st.error(f"Error loading document {doc_id}: {e}")
    return documents


def save_document(document_obj: Document):
    """Save document to database"""
    documents = load_data(DOCUMENTS_FILE)
    documents[document_obj.document_id] = document_obj.dict()
    save_data(DOCUMENTS_FILE, documents)


# Agent operations
def get_agents() -> Dict[str, Agent]:
    """Get all agents from database"""
    data = load_data(AGENTS_FILE)
    agents = {}
    for agent_id, agent_data in data.items():
        try:
            agents[agent_id] = Agent(**agent_data)
        except Exception as e:
            st.error(f"Error loading agent {agent_id}: {e}")
    return agents


def save_agent(agent_obj: Agent):
    """Save agent to database"""
    agents = load_data(AGENTS_FILE)
    agents[agent_obj.agent_id] = agent_obj.dict()
    save_data(AGENTS_FILE, agents)


# Buyer operations
def get_buyers() -> Dict[str, Buyer]:
    """Get all buyers from database"""
    data = load_data(BUYERS_FILE)
    buyers = {}
    for buyer_id, buyer_data in data.items():
        try:
            buyers[buyer_id] = Buyer(**buyer_data)
        except Exception as e:
            st.error(f"Error loading buyer {buyer_id}: {e}")
    return buyers


def save_buyer(buyer_obj: Buyer):
    """Save buyer to database"""
    buyers = load_data(BUYERS_FILE)
    buyers[buyer_obj.buyer_id] = buyer_obj.dict()
    save_data(BUYERS_FILE, buyers)


# Notary operations
def get_notaries() -> Dict[str, Notary]:
    """Get all notaries from database"""
    data = load_data(NOTARIES_FILE)
    notaries = {}
    for notary_id, notary_data in data.items():
        try:
            notaries[notary_id] = Notary(**notary_data)
        except Exception as e:
            st.error(f"Error loading notary {notary_id}: {e}")
    return notaries


def save_notary(notary_obj: Notary):
    """Save notary to database"""
    notaries = load_data(NOTARIES_FILE)
    notaries[notary_obj.notary_id] = notary_obj.dict()
    save_data(NOTARIES_FILE, notaries)