import streamlit as st
import json
import os
from datetime import datetime
from decimal import Decimal
import uuid
from typing import Dict, List, Optional

# Import our enhanced Pydantic classes
from gpp.classes.document import Document, validate_document as validate_doc_helper
from gpp.classes.property import (
    Property, add_document_to_property_mandatory, assign_notary_to_property,
    reserve_property, add_additional_document_to_property, replace_mandatory_document,
    add_agent_note_to_property, get_property_additional_docs_count, get_property_recent_activity
)
from gpp.classes.agent import Agent, add_document_to_agent, add_property_to_agent
from gpp.classes.buyer import Buyer, add_document_to_buyer, add_interest_to_buyer
from gpp.classes.notary import Notary, add_document_to_notary, add_work_to_notary
from gpp.classes.buying import Buying, create_buying_transaction

# Simple database mock using JSON files
DATA_DIR = "data"
PROPERTIES_FILE = os.path.join(DATA_DIR, "properties.json")
DOCUMENTS_FILE = os.path.join(DATA_DIR, "documents.json")
AGENTS_FILE = os.path.join(DATA_DIR, "agents.json")
BUYERS_FILE = os.path.join(DATA_DIR, "buyers.json")
NOTARIES_FILE = os.path.join(DATA_DIR, "notaries.json")
BUYING_FILE = os.path.join(DATA_DIR, "buying.json")

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)


# Initialize data files if they don't exist
def init_data_files():
    files = [PROPERTIES_FILE, DOCUMENTS_FILE, AGENTS_FILE, BUYERS_FILE, NOTARIES_FILE, BUYING_FILE]
    for file_path in files:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)


# Data management functions using Pydantic models
def load_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_data(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def get_properties() -> Dict[str, Property]:
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
    properties = load_data(PROPERTIES_FILE)
    properties[property_obj.property_id] = property_obj.dict()
    save_data(PROPERTIES_FILE, properties)


def get_documents() -> Dict[str, Document]:
    data = load_data(DOCUMENTS_FILE)
    documents = {}
    for doc_id, doc_data in data.items():
        try:
            documents[doc_id] = Document(**doc_data)
        except Exception as e:
            st.error(f"Error loading document {doc_id}: {e}")
    return documents


def save_document(document_obj: Document):
    documents = load_data(DOCUMENTS_FILE)
    documents[document_obj.document_id] = document_obj.dict()
    save_data(DOCUMENTS_FILE, documents)


def get_agents() -> Dict[str, Agent]:
    data = load_data(AGENTS_FILE)
    agents = {}
    for agent_id, agent_data in data.items():
        try:
            agents[agent_id] = Agent(**agent_data)
        except Exception as e:
            st.error(f"Error loading agent {agent_id}: {e}")
    return agents


def save_agent(agent_obj: Agent):
    agents = load_data(AGENTS_FILE)
    agents[agent_obj.agent_id] = agent_obj.dict()
    save_data(AGENTS_FILE, agents)


# Mandatory legal documents list
MANDATORY_DOCS = {
    "title_deed": "Title Deed / Property Ownership Document",
    "land_registry_extract": "Land Registry Extract",
    "building_permit": "Building Permit",
    "habitation_certificate": "Habitation Certificate",
    "mortgage_lien_certificate": "Mortgage / Lien Certificate",
    "seller_id_document": "Seller's ID Document",
    "marital_status_documents": "Marital Status Documents",
    "power_of_attorney": "Power of Attorney",
    "litigation_certificate": "Litigation Certificate"
}

# NEW: Additional document categories
ADDITIONAL_DOC_CATEGORIES = {
    "supplementary_documents": "📋 Supplementary Legal Documents",
    "corrections": "🔧 Document Corrections/Updates",
    "clarifications": "💡 Clarification Documents",
    "agent_notes": "📝 Agent Notes & Explanations",
    "updated_photos": "📸 Additional/Updated Photos",
    "floor_plans": "📐 Floor Plans & Blueprints",
    "certificates": "🏆 Additional Certificates",
    "correspondence": "✉️ Email Exchanges & Letters",
    "other": "📁 Other Documents"
}


def main():
    st.set_page_config(
        page_title="GPP - Global Property Platform",
        page_icon="🏠",
        layout="wide"
    )

    init_data_files()

    # Header
    st.title("🏠 GPP - Global Property Platform")
    st.markdown("*Professional Property Management System*")

    # User Role Selection
    st.sidebar.header("👤 User Authentication")
    user_role = st.sidebar.selectbox(
        "Select Your Role:",
        ["Agent", "Notary", "Buyer"],
        help="Choose your role to access the appropriate dashboard"
    )

    # Get or create current user
    current_user = get_or_create_user(user_role)

    # Role-based navigation
    if user_role == "Agent":
        agent_dashboard(current_user)
    elif user_role == "Notary":
        notary_dashboard(current_user)
    elif user_role == "Buyer":
        buyer_dashboard(current_user)


def get_or_create_user(role):
    """Get or create a user for the selected role"""
    if f"current_{role.lower()}" not in st.session_state:
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

        st.session_state[f"current_{role.lower()}"] = user

    return st.session_state[f"current_{role.lower()}"]


def agent_dashboard(current_agent: Agent):
    st.header(f"🏢 Agent Dashboard - {current_agent.agent_id[:8]}...")

    # Tabs for different agent functions - ENHANCED with additional docs tab
    tab1, tab2, tab3 = st.tabs(["📝 Add New Property", "📋 My Properties", "📎 Manage Documents"])

    with tab1:
        add_property_form(current_agent)

    with tab2:
        show_agent_properties(current_agent)

    with tab3:
        manage_additional_documents(current_agent)


def add_property_form(current_agent: Agent):
    st.subheader("Add New Property")

    with st.form("add_property_form"):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Property Title*", placeholder="Beautiful Family House")
            price = st.number_input("Price (€)*", min_value=0.0, step=1000.0)
            dimension = st.text_input("Dimensions*", placeholder="150 sqm")

        with col2:
            description = st.text_area("Description*", placeholder="Detailed property description...")
            address = st.text_input("Address*", placeholder="123 Main Street")
            city = st.text_input("City*", placeholder="Sample City")

        # Additional property details
        st.subheader("📊 Property Details")
        col3, col4, col5 = st.columns(3)

        with col3:
            number_of_rooms = st.number_input("Number of Rooms", min_value=0, value=0)
        with col4:
            finishes = st.text_input("Finishes", placeholder="Modern, renovated")
        with col5:
            renovations = st.text_input("Renovations", placeholder="Kitchen renovated 2023")

        neighborhood_description = st.text_area("Neighborhood Description",
                                                placeholder="Close to schools, parks, transport...")

        # Property Photos
        st.subheader("📸 Property Photos")
        st.info("Upload multiple high-quality photos of your property")

        property_photos = st.file_uploader(
            "Property Photos",
            type=['jpg', 'jpeg', 'png'],
            accept_multiple_files=True,
            help="Upload multiple photos (interior, exterior, aerial views)"
        )

        if property_photos:
            st.write(f"📸 {len(property_photos)} photos uploaded")
            # Show preview of uploaded photos
            cols = st.columns(min(len(property_photos), 4))
            for i, photo in enumerate(property_photos[:4]):
                with cols[i]:
                    st.image(photo, caption=f"Photo {i + 1}", use_column_width=True)
            if len(property_photos) > 4:
                st.write(f"... and {len(property_photos) - 4} more photos")

        st.subheader("📄 Upload Mandatory Legal Documents")
        st.info("All 9 documents are required for property validation")

        uploaded_docs = {}

        # Create document upload fields
        for doc_key, doc_name in MANDATORY_DOCS.items():
            uploaded_file = st.file_uploader(
                doc_name,
                type=['pdf', 'jpg', 'jpeg', 'png'],
                key=f"doc_{doc_key}"
            )
            if uploaded_file:
                uploaded_docs[doc_key] = uploaded_file

        submitted = st.form_submit_button("🏠 Add Property", type="primary")

        if submitted:
            if not all([title, price, dimension, description, address, city]):
                st.error("Please fill in all required fields marked with *")
                return

            if len(uploaded_docs) != len(MANDATORY_DOCS):
                st.error(f"Please upload all {len(MANDATORY_DOCS)} mandatory documents")
                return

            # Save property photos as documents
            photo_doc_ids = []
            if property_photos:
                for i, photo in enumerate(property_photos):
                    photo_doc = Document(
                        document_name=f"Property Photo {i + 1}",
                        document_path=f"/photos/{photo.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        upload_id=current_agent.agent_id,
                        validation_status=True,  # Photos don't need validation
                        visibility=True
                    )
                    save_document(photo_doc)
                    photo_doc_ids.append(photo_doc.document_id)

            # Save mandatory documents
            doc_ids = {}
            for doc_key, uploaded_file in uploaded_docs.items():
                doc = Document(
                    document_name=MANDATORY_DOCS[doc_key],
                    document_path=f"/documents/{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    upload_id=current_agent.agent_id,
                    validation_status=False,
                    visibility=True
                )
                save_document(doc)
                doc_ids[doc_key] = doc.document_id

            # Create property using enhanced Pydantic class
            new_property = Property(
                agent_id=current_agent.agent_id,
                title=title,
                description=description,
                dimension=dimension,
                price=Decimal(str(price)),
                address=address,
                city=city,
                postal_code="",  # Can be added later
                country="",  # Can be added later
                number_of_rooms=number_of_rooms if number_of_rooms > 0 else None,
                finishes=finishes if finishes else None,
                renovations=renovations if renovations else None,
                neighborhood_description=neighborhood_description if neighborhood_description else None,
                status="active",
                looking_for_notary=True,
                document_ids=list(doc_ids.values()) + photo_doc_ids
            )

            # Update property's mandatory docs
            for doc_key, doc_id in doc_ids.items():
                new_property = add_document_to_property_mandatory(new_property, doc_key, doc_id)

            save_property(new_property)

            # Update agent's property list
            current_agent = add_property_to_agent(current_agent, new_property.property_id, "active")
            save_agent(current_agent)

            # Update session state
            st.session_state["current_agent"] = current_agent

            st.success(f"✅ Property '{title}' added successfully!")
            st.info("Property is now in validation queue for notary review.")


def show_agent_properties(current_agent: Agent):
    st.subheader("My Properties")

    properties = get_properties()
    agent_properties = {k: v for k, v in properties.items()
                        if k in current_agent.agent_active_prop_list}

    if not agent_properties:
        st.info("No properties added yet. Use the 'Add New Property' tab to get started.")
        return

    # Display properties in cards
    for prop_id, prop_data in agent_properties.items():
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.write(f"**{prop_data.title}**")
                st.write(f"€{prop_data.price:,.2f}")
                st.write(f"📍 {prop_data.address}, {prop_data.city}")
                if prop_data.number_of_rooms:
                    st.write(f"🏠 {prop_data.number_of_rooms} rooms")

            with col2:
                st.write(f"📏 {prop_data.dimension}")
                if prop_data.looking_for_notary:
                    st.warning("🔄 Pending Validation")
                elif prop_data.notary_attached:
                    st.success("✅ Notary Assigned")

                # Show photo count
                photo_count = len([doc_id for doc_id in prop_data.document_ids
                                   if
                                   get_documents().get(doc_id, Document()).document_name.startswith("Property Photo")])
                if photo_count > 0:
                    st.write(f"📸 {photo_count} photos uploaded")

                # NEW: Show additional documents count
                additional_count = sum(get_property_additional_docs_count(prop_data).values())
                if additional_count > 0:
                    st.write(f"📎 {additional_count} additional documents")

            with col3:
                validation_progress = get_property_validation_progress(prop_id)
                st.write(f"**{validation_progress['validated']}/{validation_progress['total']}**")
                st.progress(validation_progress['progress'])

                # NEW: Button to manage this property's documents
                if st.button("📎 Add Docs", key=f"add_docs_{prop_id}"):
                    st.session_state['manage_property_id'] = prop_id

        st.divider()


def manage_additional_documents(current_agent: Agent):
    """NEW: Interface for managing additional documents"""
    st.subheader("📎 Manage Additional Documents")

    properties = get_properties()
    agent_properties = {k: v for k, v in properties.items()
                        if k in current_agent.agent_active_prop_list}

    if not agent_properties:
        st.info("No properties to manage. Add a property first.")
        return

    # Property selection
    if 'manage_property_id' in st.session_state and st.session_state['manage_property_id'] in agent_properties:
        selected_property_id = st.session_state['manage_property_id']
    else:
        property_options = {f"{prop.title} - {prop.city}": prop_id
                            for prop_id, prop in agent_properties.items()}

        if not property_options:
            st.info("No properties available for document management.")
            return

        selected_title = st.selectbox("Select Property:", options=list(property_options.keys()))
        selected_property_id = property_options[selected_title]

    selected_property = agent_properties[selected_property_id]

    st.write(f"**Managing Documents for:** {selected_property.title}")

    # Show property status
    col1, col2, col3 = st.columns(3)
    with col1:
        validation_progress = get_property_validation_progress(selected_property_id)
        st.metric("Validation Progress", f"{validation_progress['validated']}/{validation_progress['total']}")

    with col2:
        additional_count = sum(get_property_additional_docs_count(selected_property).values())
        st.metric("Additional Documents", additional_count)

    with col3:
        if selected_property.looking_for_notary:
            st.warning("🔄 In Review")
        elif selected_property.notary_attached:
            st.success("✅ Validated")
        else:
            st.info("📋 Draft")

    # Tabs for different document management actions
    doc_tab1, doc_tab2, doc_tab3, doc_tab4 = st.tabs([
        "➕ Add Documents",
        "🔄 Replace Mandatory",
        "📝 Add Note",
        "📋 Document History"
    ])

    with doc_tab1:
        add_additional_documents_interface(selected_property, current_agent)

    with doc_tab2:
        replace_mandatory_documents_interface(selected_property, current_agent)

    with doc_tab3:
        add_agent_note_interface(selected_property, current_agent)

    with doc_tab4:
        show_document_history_interface(selected_property)


def add_additional_documents_interface(property_obj: Property, current_agent: Agent):
    """Interface for adding additional documents"""
    st.subheader("➕ Add Additional Documents")

    with st.form("add_additional_docs"):
        # Category selection
        category = st.selectbox(
            "Document Category:",
            options=list(ADDITIONAL_DOC_CATEGORIES.keys()),
            format_func=lambda x: ADDITIONAL_DOC_CATEGORIES[x]
        )

        # File upload
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
            accept_multiple_files=True,
            help="Upload documents related to your property"
        )

        # Agent note
        agent_note = st.text_area(
            "Note (Optional):",
            placeholder="Explain why you're adding these documents..."
        )

        submitted = st.form_submit_button("📎 Add Documents", type="primary")

        if submitted:
            if not uploaded_files:
                st.error("Please upload at least one document.")
                return

            # Save uploaded documents
            document_ids = []
            for uploaded_file in uploaded_files:
                doc = Document(
                    document_name=f"{ADDITIONAL_DOC_CATEGORIES[category]} - {uploaded_file.name}",
                    document_path=f"/additional_docs/{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    upload_id=current_agent.agent_id,
                    validation_status=False,
                    visibility=True
                )
                save_document(doc)
                document_ids.append(doc.document_id)

            # Add documents to property
            updated_property = property_obj
            for doc_id in document_ids:
                updated_property = add_additional_document_to_property(
                    updated_property, category, doc_id, agent_note
                )

            save_property(updated_property)

            st.success(f"✅ Added {len(document_ids)} documents to {ADDITIONAL_DOC_CATEGORIES[category]}")
            st.rerun()


def replace_mandatory_documents_interface(property_obj: Property, current_agent: Agent):
    """Interface for replacing mandatory documents"""
    st.subheader("🔄 Replace Mandatory Documents")

    # Show current mandatory documents
    documents = get_documents()

    with st.form("replace_mandatory_doc"):
        # Document type selection
        doc_type = st.selectbox(
            "Select Document to Replace:",
            options=list(MANDATORY_DOCS.keys()),
            format_func=lambda x: MANDATORY_DOCS[x]
        )

        # Show current document info
        current_doc_id = property_obj.mandatory_legal_docs.get(doc_type)
        if current_doc_id and current_doc_id in documents:
            current_doc = documents[current_doc_id]
            st.info(f"Current document: {current_doc.document_name}")
            if current_doc.validation_status:
                st.warning("⚠️ This document is already validated. Replacing it will require re-validation.")
        else:
            st.warning("No document currently uploaded for this type.")

        # New file upload
        new_file = st.file_uploader(
            "Upload Replacement Document",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="Upload the corrected/updated version"
        )

        # Reason for replacement
        reason = st.text_area(
            "Reason for Replacement*:",
            placeholder="Explain why you're replacing this document (e.g., 'Updated version with correct dates', 'Higher quality scan')"
        )

        submitted = st.form_submit_button("🔄 Replace Document", type="primary")

        if submitted:
            if not new_file:
                st.error("Please upload a replacement document.")
                return

            if not reason.strip():
                st.error("Please provide a reason for the replacement.")
                return

            # Save new document
            new_doc = Document(
                document_name=f"{MANDATORY_DOCS[doc_type]} (Replacement)",
                document_path=f"/documents/{new_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                upload_id=current_agent.agent_id,
                validation_status=False,  # Needs re-validation
                visibility=True
            )
            save_document(new_doc)

            # Replace document in property
            updated_property = replace_mandatory_document(
                property_obj, doc_type, new_doc.document_id, reason
            )
            save_property(updated_property)

            st.success(f"✅ Replaced {MANDATORY_DOCS[doc_type]} successfully!")
            st.info("The new document will need to be validated by a notary.")
            st.rerun()


def add_agent_note_interface(property_obj: Property, current_agent: Agent):
    """Interface for adding agent notes"""
    st.subheader("📝 Add Agent Note")

    with st.form("add_agent_note"):
        note_context = st.selectbox(
            "Note Context:",
            options=["general", "document_clarification", "property_update", "notary_communication", "buyer_inquiry"],
            format_func=lambda x: x.replace("_", " ").title()
        )

        note_text = st.text_area(
            "Note*:",
            placeholder="Add any important information, clarifications, or updates about this property...",
            height=100
        )

        submitted = st.form_submit_button("📝 Add Note", type="primary")

        if submitted:
            if not note_text.strip():
                st.error("Please enter a note.")
                return

            updated_property = add_agent_note_to_property(property_obj, note_text.strip(), note_context)
            save_property(updated_property)

            st.success("✅ Note added successfully!")
            st.rerun()


def show_document_history_interface(property_obj: Property):
    """Show document history and recent activity"""
    st.subheader("📋 Document History & Activity")

    # Recent activity
    recent_activity = get_property_recent_activity(property_obj, limit=20)

    if not recent_activity:
        st.info("No activity recorded yet.")
        return

    # Show activity timeline
    for activity in recent_activity:
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                if activity["type"] == "document_activity":
                    st.write(f"📄 **{activity['description']}**")
                    details = activity["details"]
                    if "note" in details and details["note"]:
                        st.write(f"   💬 {details['note']}")
                else:  # agent_note
                    st.write(f"📝 **Agent Note:** {activity['details']['note']}")
                    st.write(f"   🏷️ Context: {activity['details']['context'].replace('_', ' ').title()}")

            with col2:
                # Handle both string and datetime timestamps
                timestamp = activity["timestamp"]
                if isinstance(timestamp, str):
                    st.write(f"🕒 {timestamp[:16]}")
                else:
                    st.write(f"🕒 {timestamp.strftime('%Y-%m-%d %H:%M')}")

        st.divider()

    # Show additional documents summary
    st.subheader("📊 Additional Documents Summary")
    additional_counts = get_property_additional_docs_count(property_obj)

    if any(count > 0 for count in additional_counts.values()):
        for category, count in additional_counts.items():
            if count > 0:
                st.write(f"• **{ADDITIONAL_DOC_CATEGORIES[category]}**: {count} documents")
    else:
        st.info("No additional documents uploaded yet.")


def notary_dashboard(current_notary: Notary):
    st.header(f"⚖️ Notary Dashboard - {current_notary.notary_id[:8]}...")

    tab1, tab2 = st.tabs(["🔍 Validation Queue", "✅ Validated Properties"])

    with tab1:
        show_validation_queue(current_notary)

    with tab2:
        show_validated_properties(current_notary)


def show_validation_queue(current_notary: Notary):
    st.subheader("Properties Awaiting Validation")

    properties = get_properties()
    pending_properties = {k: v for k, v in properties.items()
                          if v.looking_for_notary and not v.notary_attached}

    if not pending_properties:
        st.info("No properties in validation queue.")
        return

    # Display properties in card grid
    cols = st.columns(3)

    for i, (prop_id, prop_data) in enumerate(pending_properties.items()):
        with cols[i % 3]:
            with st.container():
                st.write(f"**{prop_data.title}**")
                st.write(f"€{prop_data.price:,.2f}")
                st.write(f"📍 {prop_data.city}")

                # Show property photos if available
                documents = get_documents()
                photo_docs = [doc for doc_id, doc in documents.items()
                              if doc_id in prop_data.document_ids and doc.document_name.startswith("Property Photo")]

                if photo_docs:
                    st.write(f"📸 {len(photo_docs)} photos")

                # Validation progress
                progress = get_property_validation_progress(prop_id)
                st.write(f"**Progress: {progress['validated']}/{progress['total']}**")
                st.progress(progress['progress'])

                # NEW: Show additional documents count
                additional_count = sum(get_property_additional_docs_count(prop_data).values())
                if additional_count > 0:
                    st.write(f"📎 {additional_count} additional docs")

                if st.button("🔍 Review Documents", key=f"review_{prop_id}"):
                    st.session_state['selected_property'] = prop_id

    # Show document review interface if property selected
    if 'selected_property' in st.session_state:
        show_document_review(st.session_state['selected_property'], current_notary)


def show_document_review(property_id, current_notary: Notary):
    st.divider()
    st.subheader("📄 Document Review")

    properties = get_properties()
    documents = get_documents()

    if property_id not in properties:
        st.error("Property not found")
        return

    prop_data = properties[property_id]
    st.write(f"**Property:** {prop_data.title}")
    st.write(f"**Price:** €{prop_data.price:,.2f}")
    st.write(f"**Description:** {prop_data.description}")

    # Show property photos
    photo_docs = [doc for doc_id, doc in documents.items()
                  if doc_id in prop_data.document_ids and doc.document_name.startswith("Property Photo")]

    if photo_docs:
        st.subheader("📸 Property Photos")
        cols = st.columns(min(len(photo_docs), 4))
        for i, photo_doc in enumerate(photo_docs[:4]):
            with cols[i]:
                st.write(f"Photo {i + 1}")
                st.info(f"Path: {photo_doc.document_path}")
        if len(photo_docs) > 4:
            st.write(f"... and {len(photo_docs) - 4} more photos")

    # Progress bar
    progress = get_property_validation_progress(property_id)
    st.write(f"**Documents Validated: {progress['validated']}/{progress['total']}**")
    st.progress(progress['progress'])

    # NEW: Show agent notes if any
    if prop_data.agent_notes:
        with st.expander(f"📝 Agent Notes ({len(prop_data.agent_notes)})"):
            for note in reversed(prop_data.agent_notes[-5:]):  # Show last 5 notes
                timestamp = note["timestamp"]
                if isinstance(timestamp, str):
                    time_str = timestamp[:16]
                else:
                    time_str = timestamp.strftime('%Y-%m-%d %H:%M')
                st.write(f"**{time_str}** - {note['context'].replace('_', ' ').title()}")
                st.write(f"💬 {note['note']}")
                st.write("---")

    # NEW: Show additional documents
    additional_counts = get_property_additional_docs_count(prop_data)
    if any(count > 0 for count in additional_counts.values()):
        with st.expander("📎 Additional Documents"):
            for category, doc_ids in prop_data.additional_docs.items():
                if doc_ids:
                    st.write(f"**{ADDITIONAL_DOC_CATEGORIES[category]}** ({len(doc_ids)} documents)")
                    for doc_id in doc_ids:
                        if doc_id in documents:
                            doc = documents[doc_id]
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"• {doc.document_name}")
                            with col2:
                                if st.button("👁️", key=f"view_add_{doc_id}"):
                                    st.info(f"Viewing: {doc.document_path}")

    st.divider()

    # Document review interface for mandatory documents
    st.subheader("📋 Mandatory Document Review")
    for doc_key, doc_id in prop_data.mandatory_legal_docs.items():
        if doc_id and doc_id in documents:
            doc_data = documents[doc_id]

            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    doc_name = MANDATORY_DOCS[doc_key]
                    if doc_data.validation_status:
                        st.write(f"✅ **{doc_name}** - Validated")
                        if doc_data.validation_date:
                            # Handle both string and datetime objects
                            if isinstance(doc_data.validation_date, str):
                                st.write(f"   📅 {doc_data.validation_date[:10]}")
                            else:
                                st.write(f"   📅 {doc_data.validation_date.strftime('%Y-%m-%d')}")
                    else:
                        st.write(f"📄 **{doc_name}** - Pending")
                        # Show if this is a replacement
                        if "Replacement" in doc_data.document_name:
                            st.warning("🔄 Replacement Document - Needs Re-validation")

                with col2:
                    if st.button("👁️ View", key=f"view_{doc_id}"):
                        st.info(f"Viewing: {doc_data.document_name}")
                        st.write(f"File: {doc_data.document_path}")
                        st.write(f"Uploaded: {doc_data.upload_date[:10]}")
                        # In real app, would show PDF viewer here

                with col3:
                    if not doc_data.validation_status:
                        col_validate, col_reject = st.columns(2)
                        with col_validate:
                            if st.button("✅", key=f"validate_{doc_id}"):
                                validated_doc = validate_doc_helper(doc_data, current_notary.notary_id)
                                save_document(validated_doc)
                                st.rerun()
                        with col_reject:
                            if st.button("❌", key=f"reject_{doc_id}"):
                                doc_data.validation_status = False
                                doc_data.validation_date = datetime.now()
                                doc_data.who_validate = current_notary.notary_id
                                save_document(doc_data)
                                st.rerun()

            st.divider()

    # Check if all documents are validated
    if progress['validated'] == progress['total']:
        if st.button("🎉 Approve Property for Public Listing", type="primary"):
            # Assign notary to property
            updated_property = assign_notary_to_property(prop_data, current_notary.notary_id)
            updated_property.looking_for_notary = False
            updated_property.validation_date = datetime.now()
            updated_property.notary_attached = current_notary.notary_id

            save_property(updated_property)

            # Update notary's work lists
            updated_notary = add_work_to_notary(current_notary, property_id, "property_checked")
            notaries = load_data(NOTARIES_FILE)
            notaries[current_notary.notary_id] = updated_notary.dict()
            save_data(NOTARIES_FILE, notaries)

            st.success("Property approved and moved to public listings!")
            st.rerun()


def show_validated_properties(current_notary: Notary):
    st.subheader("Properties I've Validated")

    properties = get_properties()
    validated_properties = {k: v for k, v in properties.items()
                            if k in current_notary.checked_prop_list}

    if not validated_properties:
        st.info("No validated properties yet.")
        return

    for prop_id, prop_data in validated_properties.items():
        with st.container():
            col1, col2 = st.columns([3, 1])

            with col1:
                st.write(f"**{prop_data.title}**")
                st.write(f"€{prop_data.price:,.2f} | 📍 {prop_data.city}")

                # Show additional docs count if any
                additional_count = sum(get_property_additional_docs_count(prop_data).values())
                if additional_count > 0:
                    st.write(f"📎 {additional_count} additional documents added by agent")

            with col2:
                st.write("✅ **Validated**")
                if prop_data.validation_date:
                    # Handle both string and datetime objects
                    if isinstance(prop_data.validation_date, str):
                        st.write(f"🗓️ {prop_data.validation_date[:10]}")
                    else:
                        st.write(f"🗓️ {prop_data.validation_date.strftime('%Y-%m-%d')}")

        st.divider()


def buyer_dashboard(current_buyer: Buyer):
    st.header(f"💰 Buyer Dashboard - {current_buyer.buyer_id[:8]}...")

    st.subheader("Available Properties")

    # Show debug info
    with st.expander("🔍 Debug Information"):
        properties = get_properties()
        st.write(f"**Total properties in system:** {len(properties)}")

        for prop_id, prop_data in properties.items():
            progress = get_property_validation_progress(prop_id)
            st.write(f"**{prop_data.title}:**")
            st.write(f"  - Progress: {progress['validated']}/{progress['total']}")
            st.write(f"  - Notary attached: {prop_data.notary_attached}")
            st.write(f"  - Looking for notary: {prop_data.looking_for_notary}")
            st.write("---")

    properties = get_properties()
    documents = get_documents()

    # Show properties that are fully validated by notary
    validated_properties = {}
    for prop_id, prop_data in properties.items():
        # Check if all mandatory documents are validated
        progress = get_property_validation_progress(prop_id)
        if progress['validated'] == progress['total'] and progress['total'] > 0:
            # Also check if notary is attached (property was approved)
            if prop_data.notary_attached:
                validated_properties[prop_id] = prop_data

    if not validated_properties:
        st.info(
            "No validated properties available yet. Properties will appear here once notaries complete their validation.")
        return

    # Display properties in card grid
    cols = st.columns(2)

    for i, (prop_id, prop_data) in enumerate(validated_properties.items()):
        with cols[i % 2]:
            with st.container():
                # Show property photos if available
                photo_docs = [doc for doc_id, doc in documents.items()
                              if doc_id in prop_data.document_ids and doc.document_name.startswith("Property Photo")]

                if photo_docs:
                    st.info(f"📸 {len(photo_docs)} photos available")
                else:
                    st.image("https://via.placeholder.com/300x200?text=Property+Photo",
                             caption=prop_data.title)

                st.write(f"**{prop_data.title}**")
                st.write(f"**€{prop_data.price:,.2f}**")
                st.write(f"📏 {prop_data.dimension}")
                st.write(f"📍 {prop_data.address}, {prop_data.city}")

                if prop_data.number_of_rooms:
                    st.write(f"🏠 {prop_data.number_of_rooms} rooms")

                st.write(f"📝 {prop_data.description[:100]}...")

                # Show validation status
                st.success("✅ Fully Validated by Notary")

                # NEW: Show if property has additional documentation
                additional_count = sum(get_property_additional_docs_count(prop_data).values())
                if additional_count > 0:
                    st.info(f"📎 {additional_count} additional documents available")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("❤️ Favorite", key=f"fav_{prop_id}"):
                        updated_buyer = add_interest_to_buyer(current_buyer, prop_id, "interested")
                        buyers = load_data(BUYERS_FILE)
                        buyers[current_buyer.buyer_id] = updated_buyer.dict()
                        save_data(BUYERS_FILE, buyers)
                        st.success("Added to favorites!")

                with col2:
                    if st.button("🏠 Reserve", key=f"reserve_{prop_id}"):
                        updated_buyer = add_interest_to_buyer(current_buyer, prop_id, "reserved")
                        buyers = load_data(BUYERS_FILE)
                        buyers[current_buyer.buyer_id] = updated_buyer.dict()
                        save_data(BUYERS_FILE, buyers)

                        # Reserve the property
                        updated_property = reserve_property(prop_data, current_buyer.buyer_id)
                        save_property(updated_property)

                        st.success("Property reserved!")

        if i % 2 == 1:  # Add spacing after every two properties
            st.write("")


def get_property_validation_progress(property_id):
    properties = get_properties()
    documents = get_documents()

    if property_id not in properties:
        return {"validated": 0, "total": 0, "progress": 0.0}

    prop_data = properties[property_id]
    doc_ids = prop_data.mandatory_legal_docs

    total_docs = len([doc_id for doc_id in doc_ids.values() if doc_id])
    validated_docs = 0

    for doc_id in doc_ids.values():
        if doc_id and doc_id in documents and documents[doc_id].validation_status:
            validated_docs += 1

    progress = validated_docs / total_docs if total_docs > 0 else 0

    return {
        "validated": validated_docs,
        "total": total_docs,
        "progress": progress
    }


if __name__ == "__main__":
    main()