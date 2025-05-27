from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid


class Agent(BaseModel):
    """Agent class - posts and manages properties"""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Property Management Lists
    agent_active_prop_list: List[str] = Field(
        default_factory=list,
        description="List of active property IDs"
    )
    agent_sold_prop: List[str] = Field(
        default_factory=list,
        description="List of sold property IDs"
    )
    agent_notary_pending_prop: List[str] = Field(
        default_factory=list,
        description="List of properties pending notary validation"
    )

    # Agent Authentication Documents
    documents: Dict[str, Optional[str]] = Field(
        default_factory=lambda: {
            "id_document": None,  # ID/Passport
            "professional_license": None,  # Real estate license
            "business_registration": None,  # Business registration
        },
        description="Dictionary of agent documents with document IDs"
    )

    # Additional documents can be added
    additional_docs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Possibility to add more documents"
    )


# Helper functions for agent management
def add_document_to_agent(agent_obj: Agent, doc_type: str, document_id: str) -> Agent:
    """Add document ID to agent's document dictionary"""
    if doc_type in agent_obj.documents:
        agent_obj.documents[doc_type] = document_id
    return agent_obj


def add_property_to_agent(agent_obj: Agent, property_id: str, list_type: str = "active") -> Agent:
    """Add property to agent's appropriate list"""
    if list_type == "active":
        if property_id not in agent_obj.agent_active_prop_list:
            agent_obj.agent_active_prop_list.append(property_id)
    elif list_type == "sold":
        if property_id not in agent_obj.agent_sold_prop:
            agent_obj.agent_sold_prop.append(property_id)
    elif list_type == "pending":
        if property_id not in agent_obj.agent_notary_pending_prop:
            agent_obj.agent_notary_pending_prop.append(property_id)
    return agent_obj
