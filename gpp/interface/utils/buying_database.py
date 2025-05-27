"""
Database utilities for buying transaction system
"""

import json
import os
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal

from gpp.classes.buying import Buying
from gpp.interface.utils.database import load_data, save_data

# File paths
BUYING_TRANSACTIONS_FILE = "data/buying_transactions.json"


def init_buying_database():
    """Initialize buying transactions database file"""
    if not os.path.exists(BUYING_TRANSACTIONS_FILE):
        save_data(BUYING_TRANSACTIONS_FILE, {})


def save_buying_transaction(buying_obj: Buying):
    """Save buying transaction to database"""
    init_buying_database()

    # Load existing transactions
    transactions = load_data(BUYING_TRANSACTIONS_FILE)

    # Convert to dict and handle datetime/decimal serialization
    transaction_dict = buying_obj.dict()

    # Convert datetime objects to ISO strings
    def convert_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime(item) for item in obj]
        return obj

    transaction_dict = convert_datetime(transaction_dict)

    # Save transaction
    transactions[buying_obj.buying_id] = transaction_dict
    save_data(BUYING_TRANSACTIONS_FILE, transactions)


def load_buying_transaction(buying_id: str) -> Optional[Buying]:
    """Load buying transaction from database"""
    init_buying_database()

    transactions = load_data(BUYING_TRANSACTIONS_FILE)

    if buying_id not in transactions:
        return None

    transaction_dict = transactions[buying_id]

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

    transaction_dict = convert_from_json(transaction_dict)

    # Convert final_price back to Decimal if it exists
    if transaction_dict.get('final_price') is not None:
        transaction_dict['final_price'] = Decimal(str(transaction_dict['final_price']))

    return Buying(**transaction_dict)


def get_all_buying_transactions() -> Dict[str, Buying]:
    """Get all buying transactions from database"""
    init_buying_database()

    transactions_dict = load_data(BUYING_TRANSACTIONS_FILE)
    transactions = {}

    for buying_id, transaction_data in transactions_dict.items():
        transaction = load_buying_transaction(buying_id)
        if transaction:
            transactions[buying_id] = transaction

    return transactions


def get_user_buying_transactions(user_id: str, user_type: str) -> Dict[str, Buying]:
    """Get buying transactions relevant to a specific user"""
    all_transactions = get_all_buying_transactions()
    relevant_transactions = {}

    for buying_id, buying_obj in all_transactions.items():
        if user_type == "agent" and buying_obj.agent_id == user_id:
            relevant_transactions[buying_id] = buying_obj
        elif user_type == "buyer" and buying_obj.buyer_id == user_id:
            relevant_transactions[buying_id] = buying_obj
        elif user_type == "notary":
            # Notaries see all transactions that need validation
            if buying_obj.status in ["documents_pending", "under_review"]:
                relevant_transactions[buying_id] = buying_obj

    return relevant_transactions


def delete_buying_transaction(buying_id: str) -> bool:
    """Delete buying transaction from database"""
    init_buying_database()

    transactions = load_data(BUYING_TRANSACTIONS_FILE)

    if buying_id in transactions:
        del transactions[buying_id]
        save_data(BUYING_TRANSACTIONS_FILE, transactions)
        return True

    return False


def get_buying_transactions_by_property(property_id: str) -> Dict[str, Buying]:
    """Get all buying transactions for a specific property"""
    all_transactions = get_all_buying_transactions()

    return {
        buying_id: transaction
        for buying_id, transaction in all_transactions.items()
        if transaction.property_id == property_id
    }


def get_active_buying_transactions() -> Dict[str, Buying]:
    """Get all active buying transactions (not completed or cancelled)"""
    all_transactions = get_all_buying_transactions()

    return {
        buying_id: transaction
        for buying_id, transaction in all_transactions.items()
        if transaction.status not in ["completed", "cancelled"]
    }