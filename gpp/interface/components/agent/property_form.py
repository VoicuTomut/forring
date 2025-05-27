"""
Property creation form component for agents - WITH REAL FILE STORAGE
"""

import streamlit as st
from decimal import Decimal
from datetime import datetime

from gpp.classes.agent import Agent, add_property_to_agent
from gpp.classes.property import Property, add_document_to_property_mandatory
from gpp.classes.document import Document
from gpp.interface.utils.database import save_property, save_document, save_agent
from gpp.interface.utils.file_storage import save_uploaded_file, save_multiple_files, init_file_storage
from gpp.interface.config.constants import MANDATORY_DOCS, ALLOWED_PHOTO_TYPES, ALLOWED_DOCUMENT_TYPES


def add_property_form(current_agent: Agent):
    """Property creation form interface with real file storage"""
    st.subheader("Add New Property")

    # Initialize file storage
    init_file_storage()

    with st.form("add_property_form"):
        # Basic property information
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

        neighborhood_description = st.text_area(
            "Neighborhood Description",
            placeholder="Close to schools, parks, transport..."
        )

        # Property Photos Section
        property_photos = _render_photo_upload_section()

        # Mandatory Documents Section
        uploaded_docs = _render_mandatory_docs_section()

        # Submit button
        submitted = st.form_submit_button("🏠 Add Property", type="primary")

        if submitted:
            _handle_property_submission(
                current_agent, title, price, dimension, description, address, city,
                number_of_rooms, finishes, renovations, neighborhood_description,
                property_photos, uploaded_docs
            )


def _render_photo_upload_section():
    """Render property photos upload section"""
    st.subheader("📸 Property Photos")
    st.info("Upload multiple high-quality photos of your property")

    property_photos = st.file_uploader(
        "Property Photos",
        type=ALLOWED_PHOTO_TYPES,
        accept_multiple_files=True,
        help="Upload multiple photos (interior, exterior, aerial views)"
    )

    if property_photos:
        st.write(f"📸 {len(property_photos)} photos selected")
        # Show preview of uploaded photos
        cols = st.columns(min(len(property_photos), 4))
        for i, photo in enumerate(property_photos[:4]):
            with cols[i]:
                st.image(photo, caption=f"Photo {i + 1}", use_column_width=True)
        if len(property_photos) > 4:
            st.write(f"... and {len(property_photos) - 4} more photos")

    return property_photos


def _render_mandatory_docs_section():
    """Render mandatory documents upload section"""
    st.subheader("📄 Upload Mandatory Legal Documents")
    st.info("All 9 documents are required for property validation")

    uploaded_docs = {}

    # Create document upload fields
    for doc_key, doc_name in MANDATORY_DOCS.items():
        uploaded_file = st.file_uploader(
            doc_name,
            type=ALLOWED_DOCUMENT_TYPES,
            key=f"doc_{doc_key}"
        )
        if uploaded_file:
            uploaded_docs[doc_key] = uploaded_file

    return uploaded_docs


def _handle_property_submission(current_agent, title, price, dimension, description,
                              address, city, number_of_rooms, finishes, renovations,
                              neighborhood_description, property_photos, uploaded_docs):
    """Handle property form submission with real file storage"""

    # Validation
    if not all([title, price, dimension, description, address, city]):
        st.error("Please fill in all required fields marked with *")
        return

    if len(uploaded_docs) != len(MANDATORY_DOCS):
        st.error(f"Please upload all {len(MANDATORY_DOCS)} mandatory documents")
        return

    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        # Step 1: Save property photos to storage
        status_text.text("Saving property photos...")
        progress_bar.progress(20)

        photo_doc_ids = []
        if property_photos:
            saved_photo_paths = save_multiple_files(property_photos, "photos")

            for i, (photo, file_path) in enumerate(zip(property_photos, saved_photo_paths)):
                if file_path:  # Only create document if file was saved successfully
                    photo_doc = Document(
                        document_name=f"Property Photo {i + 1}",
                        document_path=file_path,  # Use actual saved file path
                        upload_id=current_agent.agent_id,
                        validation_status=True,  # Photos don't need validation
                        visibility=True
                    )
                    save_document(photo_doc)
                    photo_doc_ids.append(photo_doc.document_id)

        # Step 2: Save mandatory documents to storage
        status_text.text("Saving mandatory documents...")
        progress_bar.progress(50)

        doc_ids = {}
        for doc_key, uploaded_file in uploaded_docs.items():
            # Save file to storage
            file_path = save_uploaded_file(uploaded_file, "documents")

            if file_path:  # Only create document if file was saved successfully
                doc = Document(
                    document_name=MANDATORY_DOCS[doc_key],
                    document_path=file_path,  # Use actual saved file path
                    upload_id=current_agent.agent_id,
                    validation_status=False,
                    visibility=True
                )
                save_document(doc)
                doc_ids[doc_key] = doc.document_id
            else:
                st.error(f"Failed to save {MANDATORY_DOCS[doc_key]}")
                return

        # Step 3: Create property
        status_text.text("Creating property record...")
        progress_bar.progress(70)

        new_property = Property(
            agent_id=current_agent.agent_id,
            title=title,
            description=description,
            dimension=dimension,
            price=Decimal(str(price)),
            address=address,
            city=city,
            postal_code="",
            country="",
            number_of_rooms=number_of_rooms if number_of_rooms > 0 else None,
            finishes=finishes if finishes else None,
            renovations=renovations if renovations else None,
            neighborhood_description=neighborhood_description if neighborhood_description else None,
            status="active",
            looking_for_notary=True,
            document_ids=list(doc_ids.values()) + photo_doc_ids
        )

        # Step 4: Update property's mandatory docs
        status_text.text("Linking documents to property...")
        progress_bar.progress(85)

        for doc_key, doc_id in doc_ids.items():
            new_property = add_document_to_property_mandatory(new_property, doc_key, doc_id)

        save_property(new_property)

        # Step 5: Update agent's property list
        status_text.text("Updating agent records...")
        progress_bar.progress(95)

        current_agent = add_property_to_agent(current_agent, new_property.property_id, "active")
        save_agent(current_agent)

        # Update session state
        st.session_state["current_agent"] = current_agent

        # Complete
        progress_bar.progress(100)
        status_text.text("Property created successfully!")

        st.success(f"✅ Property '{title}' added successfully!")
        st.success(f"📄 {len(doc_ids)} documents saved to storage")
        st.success(f"📸 {len(photo_doc_ids)} photos saved to storage")
        st.info("Property is now in validation queue for notary review.")

        # Show file storage stats
        with st.expander("📊 File Storage Summary"):
            st.write("**Saved Files:**")
            for doc_key, uploaded_file in uploaded_docs.items():
                st.write(f"• {MANDATORY_DOCS[doc_key]}: `{uploaded_file.name}`")

            if property_photos:
                st.write("**Saved Photos:**")
                for i, photo in enumerate(property_photos):
                    st.write(f"• Photo {i + 1}: `{photo.name}`")

    except Exception as e:
        st.error(f"❌ Error creating property: {str(e)}")
        st.error("Please try again or contact support.")
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()