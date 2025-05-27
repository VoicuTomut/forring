"""
Buying Transaction Interface Components
Complete UI components for managing property buying transactions
"""

import streamlit as st
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
import os

# Import buying system classes and functions
from gpp.classes.buying import (
    Buying, create_buying_transaction, add_document_to_buying,
    schedule_meeting, add_transaction_note, update_buying_status,
    get_buying_progress, get_next_meeting, validate_buying_document,
    BUYING_DOCUMENT_TYPES, MEETING_TYPES, TRANSACTION_STATUSES,
    can_user_edit_transaction
)
from gpp.classes.document import Document

# Import database and utility functions
from gpp.interface.utils.database import save_document, get_properties
from gpp.interface.utils.buying_database import (
    save_buying_transaction, load_buying_transaction, get_user_buying_transactions
)
from gpp.interface.utils.file_storage import save_uploaded_file, file_exists, read_file_content
from gpp.interface.config.constants import ALLOWED_DOCUMENT_TYPES


def show_buying_dashboard(current_user, user_type: str):
    """Main buying dashboard for different user types"""
    st.title("🏠 Property Buying Transactions")

    # Get user ID based on user type
    user_id = getattr(current_user, f'{user_type.lower()}_id', None)
    if not user_id:
        st.error(f"Could not retrieve {user_type} ID")
        return

    # Load relevant transactions
    all_transactions = get_user_buying_transactions(user_id, user_type.lower())

    if not all_transactions:
        if user_type.lower() == "buyer":
            st.info("🏠 You haven't started any property purchases yet. Browse available properties to begin!")
            _show_available_properties_for_buying(current_user)
        else:
            st.info("📋 No active buying transactions.")
        return

    # Dashboard overview
    _render_buying_overview(all_transactions, user_type)

    # Transaction list
    _render_transaction_list(all_transactions, current_user, user_type)


def start_buying_process(property_id: str, buyer_id: str, agent_id: str):
    """Start a new buying transaction"""
    st.subheader("🏠 Start Property Purchase")

    # Get property details
    properties = get_properties()
    if property_id not in properties:
        st.error("Property not found")
        return

    property_data = properties[property_id]

    # Show property summary
    with st.container():
        col1, col2 = st.columns([2, 1])

        with col1:
            st.write(f"**🏠 Property:** {property_data.title}")
            st.write(f"**📍 Location:** {property_data.address}, {property_data.city}")
            st.write(f"**💰 Price:** €{property_data.price:,.2f}")
            st.write(f"**📐 Size:** {property_data.dimension}")

        with col2:
            st.write(f"**🏘️ Agent:** {agent_id[:8]}...")
            st.write(f"**👤 Buyer:** {buyer_id[:8]}...")

    st.markdown("---")

    # Initial transaction details
    with st.form("start_buying_form"):
        st.subheader("💰 Transaction Details")

        col1, col2 = st.columns(2)
        with col1:
            offered_price = st.number_input(
                "Your Offer (€)",
                min_value=0.0,
                value=float(property_data.price),
                step=1000.0,
                help="Enter your initial offer for this property"
            )

        with col2:
            initial_notes = st.text_area(
                "Additional Notes",
                placeholder="Any special conditions or requests...",
                help="Add any special conditions, financing details, or requests"
            )

        # Meeting scheduling
        st.subheader("📅 Schedule Initial Meeting")

        col1, col2 = st.columns(2)
        with col1:
            meeting_type = st.selectbox(
                "Meeting Type",
                options=list(MEETING_TYPES.keys()),
                format_func=lambda x: MEETING_TYPES[x],
                index=0  # Default to property viewing
            )

            meeting_date = st.date_input(
                "Meeting Date",
                min_value=datetime.now().date(),
                value=datetime.now().date() + timedelta(days=1)
            )

        with col2:
            meeting_time = st.time_input(
                "Meeting Time",
                value=datetime.now().time().replace(hour=14, minute=0, second=0, microsecond=0)
            )

            meeting_location = st.text_input(
                "Meeting Location",
                value=property_data.address,
                placeholder="Property address or office location"
            )

        meeting_agenda = st.text_area(
            "Meeting Agenda",
            placeholder="What would you like to discuss during the meeting?",
            value="Initial property viewing and purchase discussion"
        )

        # Submit button
        if st.form_submit_button("🚀 Start Buying Process", type="primary"):
            try:
                # Create buying transaction
                buying_transaction = create_buying_transaction(agent_id, buyer_id, property_id)
                buying_transaction.final_price = Decimal(str(offered_price))

                # Add initial note
                if initial_notes:
                    add_transaction_note(buying_transaction, initial_notes, buyer_id, "initial_offer")

                # Schedule meeting
                meeting_datetime = datetime.combine(meeting_date, meeting_time)
                meeting_data = {
                    "meeting_type": meeting_type,
                    "scheduled_date": meeting_datetime,
                    "participants": [agent_id, buyer_id],
                    "location": meeting_location,
                    "agenda": meeting_agenda,
                    "created_by": buyer_id
                }
                schedule_meeting(buying_transaction, meeting_data)

                # Save transaction
                save_buying_transaction(buying_transaction)

                st.success("🎉 Buying process started successfully!")
                st.success(f"📅 Meeting scheduled for {meeting_datetime.strftime('%Y-%m-%d %H:%M')}")
                st.info("💡 The agent will be notified and can upload required documents.")

                # Update session state
                st.session_state["active_buying_transaction"] = buying_transaction.buying_id
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error starting buying process: {str(e)}")


def show_transaction_details(buying_id: str, current_user, user_type: str):
    """Show detailed transaction view"""
    buying_transaction = load_buying_transaction(buying_id)
    if not buying_transaction:
        st.error("Transaction not found")
        return

    # Transaction header
    _render_transaction_header(buying_transaction)

    # Progress overview
    progress = get_buying_progress(buying_transaction)
    _render_progress_section(progress)

    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Documents", "📅 Meetings", "💬 Communication",
        "📊 Progress", "⚙️ Settings"
    ])

    with tab1:
        _render_documents_section(buying_transaction, current_user, user_type)

    with tab2:
        _render_meetings_section(buying_transaction, current_user, user_type)

    with tab3:
        _render_communication_section(buying_transaction, current_user, user_type)

    with tab4:
        _render_detailed_progress(buying_transaction)

    with tab5:
        _render_transaction_settings(buying_transaction, current_user, user_type)


def _show_available_properties_for_buying(current_user):
    """Show available validated properties for buying"""
    st.subheader("🏠 Available Properties")

    properties = get_properties()
    validated_properties = [
        (prop_id, prop) for prop_id, prop in properties.items()
        if prop.notary_attached and not prop.looking_for_notary
    ]

    if not validated_properties:
        st.info("No validated properties available at the moment.")
        return

    for prop_id, prop in validated_properties:
        with st.expander(f"🏠 {prop.title} - €{prop.price:,.2f}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**📍 Location:** {prop.address}, {prop.city}")
                st.write(f"**📐 Size:** {prop.dimension}")
                st.write(f"**🏠 Rooms:** {prop.nb_room}")
                st.write(f"**📝 Description:** {prop.description}")

            with col2:
                st.write(f"**💰 Price:** €{prop.price:,.2f}")
                st.write(f"**🏘️ Agent:** {prop.agent_id[:8]}...")

                if st.button("🛒 Start Buying Process", key=f"buy_{prop_id}"):
                    st.session_state["start_buying_property"] = prop_id
                    st.rerun()


def _render_buying_overview(transactions: Dict[str, Buying], user_type: str):
    """Render buying overview dashboard"""
    st.subheader("📊 Transaction Overview")

    # Statistics
    total = len(transactions)
    active = len([t for t in transactions.values() if t.status in ["pending", "documents_pending", "under_review"]])
    completed = len([t for t in transactions.values() if t.status == "completed"])

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Transactions", total)

    with col2:
        st.metric("Active", active)

    with col3:
        st.metric("Completed", completed)

    with col4:
        total_value = sum([float(t.final_price or 0) for t in transactions.values()])
        st.metric("Total Value", f"€{total_value:,.0f}")


def _render_transaction_list(transactions: Dict[str, Buying], current_user, user_type: str):
    """Render list of transactions"""
    st.subheader("📋 Your Transactions")

    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All"] + list(set(t.status for t in transactions.values()))
        )

    with col2:
        sort_by = st.selectbox("Sort by", ["Recent", "Price", "Status"])

    # Apply filters
    filtered_transactions = transactions
    if status_filter != "All":
        filtered_transactions = {
            k: v for k, v in transactions.items() if v.status == status_filter
        }

    # Sort transactions
    if sort_by == "Recent":
        sorted_items = sorted(filtered_transactions.items(), key=lambda x: x[1].last_updated, reverse=True)
    elif sort_by == "Price":
        sorted_items = sorted(filtered_transactions.items(), key=lambda x: float(x[1].final_price or 0), reverse=True)
    else:  # Status
        sorted_items = sorted(filtered_transactions.items(), key=lambda x: x[1].status)

    # Display transactions
    for buying_id, transaction in sorted_items:
        _render_transaction_card(buying_id, transaction, current_user, user_type)


def _render_transaction_card(buying_id: str, transaction: Buying, current_user, user_type: str):
    """Render individual transaction card"""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.write(f"**Transaction:** {buying_id[:12]}...")
            st.write(f"**Property:** {transaction.property_id[:12]}...")
            if transaction.final_price:
                st.write(f"**Price:** €{transaction.final_price:,.2f}")

        with col2:
            status_display = TRANSACTION_STATUSES.get(transaction.status, transaction.status)
            st.write(f"**Status:** {status_display}")
            st.write(f"**Updated:** {transaction.last_updated.strftime('%m/%d/%Y')}")

        with col3:
            progress = get_buying_progress(transaction)
            st.write(f"**Progress:** {progress['progress_percentage']:.0f}%")
            st.progress(progress['progress_percentage'] / 100)

        with col4:
            if st.button("View Details", key=f"view_{buying_id}"):
                st.session_state["selected_transaction"] = buying_id
                st.rerun()

        st.markdown("---")


def _render_transaction_header(buying_transaction: Buying):
    """Render transaction header with key information"""
    properties = get_properties()
    property_data = properties.get(buying_transaction.property_id)

    if not property_data:
        st.error("Property data not found")
        return

    # Header section
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.title(f"🏠 {property_data.title}")
        st.write(f"**📍** {property_data.address}, {property_data.city}")
        st.write(f"**💰** €{buying_transaction.final_price or property_data.price:,.2f}")
        st.caption(f"Transaction ID: {buying_transaction.buying_id[:12]}...")

    with col2:
        status_display = TRANSACTION_STATUSES.get(buying_transaction.status, buying_transaction.status)
        st.metric("Status", status_display)
        st.write(f"**Created:** {buying_transaction.created_date.strftime('%m/%d/%Y')}")

    with col3:
        next_meeting = get_next_meeting(buying_transaction)
        if next_meeting:
            st.metric("Next Meeting", next_meeting["scheduled_date"].strftime("%m/%d %H:%M"))
            st.write(f"**Type:** {MEETING_TYPES.get(next_meeting['meeting_type'], 'Meeting')}")
        else:
            st.metric("Next Meeting", "None scheduled")


def _render_progress_section(progress: Dict[str, Any]):
    """Render progress overview"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Documents", f"{progress['validated_documents']}/{progress['total_documents']}")

    with col2:
        st.metric("Progress", f"{progress['progress_percentage']:.0f}%")

    with col3:
        st.metric("Meetings", f"{progress['active_meetings']} active")

    with col4:
        st.metric("Last Updated", progress['last_updated'].strftime("%m/%d"))

    # Progress bar
    if progress['total_documents'] > 0:
        st.progress(progress['progress_percentage'] / 100)
    else:
        st.info("No documents uploaded yet")


def _render_documents_section(buying_transaction: Buying, current_user, user_type: str):
    """Render documents management section"""
    st.subheader("📄 Transaction Documents")

    # Document upload (if user can edit)
    if user_type.lower() in ["agent", "buyer"]:
        with st.expander("📎 Upload New Document"):
            _render_document_upload(buying_transaction, current_user, user_type)

    # Document list
    st.subheader("📋 Required Documents")

    for doc_type, doc_name in BUYING_DOCUMENT_TYPES.items():
        _render_document_row(buying_transaction, doc_type, doc_name, current_user, user_type)


def _render_document_upload(buying_transaction: Buying, current_user, user_type: str):
    """Render document upload form"""
    user_id = getattr(current_user, f'{user_type.lower()}_id', None)

    with st.form(f"upload_doc_{buying_transaction.buying_id}"):
        col1, col2 = st.columns(2)

        with col1:
            doc_type = st.selectbox(
                "Document Type",
                options=list(BUYING_DOCUMENT_TYPES.keys()),
                format_func=lambda x: BUYING_DOCUMENT_TYPES[x]
            )

        with col2:
            uploaded_file = st.file_uploader(
                "Select Document",
                type=ALLOWED_DOCUMENT_TYPES,
                help="Upload PDF, Word document, or image file"
            )

        upload_notes = st.text_area(
            "Document Notes",
            placeholder="Any additional information about this document..."
        )

        if st.form_submit_button("📤 Upload Document"):
            if uploaded_file and user_id:
                try:
                    # Save file
                    file_path = save_uploaded_file(uploaded_file, "buying_documents")

                    if file_path:
                        # Create document record
                        doc = Document(
                            document_name=f"{BUYING_DOCUMENT_TYPES[doc_type]} - {uploaded_file.name}",
                            document_path=file_path,
                            upload_id=user_id,
                            validation_status=False,
                            visibility=True
                        )
                        save_document(doc)

                        # Add to buying transaction
                        add_document_to_buying(buying_transaction, doc_type, doc.document_id)

                        # Add note about upload
                        add_transaction_note(
                            buying_transaction,
                            f"Document uploaded: {BUYING_DOCUMENT_TYPES[doc_type]}. {upload_notes}".strip(),
                            user_id,
                            "document_upload"
                        )

                        # Update transaction status
                        if buying_transaction.status == "pending":
                            update_buying_status(buying_transaction, "documents_pending")

                        save_buying_transaction(buying_transaction)

                        st.success(f"✅ {BUYING_DOCUMENT_TYPES[doc_type]} uploaded successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to save document")
                except Exception as e:
                    st.error(f"❌ Error uploading document: {str(e)}")
            else:
                st.error("❌ Please select a document to upload")


def _render_document_row(buying_transaction: Buying, doc_type: str, doc_name: str, current_user, user_type: str):
    """Render individual document row"""
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    doc_id = buying_transaction.buying_documents.get(doc_type)
    validation_info = buying_transaction.document_validation_status.get(doc_type, {})

    with col1:
        if doc_id:
            if validation_info.get("validation_status", False):
                st.success(f"✅ **{doc_name}** - Validated")
                if validation_info.get("validation_date"):
                    st.caption(f"Validated: {validation_info['validation_date'].strftime('%Y-%m-%d')}")
            else:
                st.warning(f"⏳ **{doc_name}** - Pending Validation")
                if validation_info.get("upload_date"):
                    st.caption(f"Uploaded: {validation_info['upload_date'].strftime('%Y-%m-%d')}")
        else:
            st.error(f"❌ **{doc_name}** - Not Uploaded")

    with col2:
        if doc_id and user_type.lower() == "notary":
            if st.button("✅ Validate", key=f"validate_{doc_type}"):
                validate_buying_document(buying_transaction, doc_type,
                                       getattr(current_user, 'notary_id'), True)
                save_buying_transaction(buying_transaction)
                st.rerun()

    with col3:
        if doc_id and user_type.lower() == "notary":
            if st.button("❌ Reject", key=f"reject_{doc_type}"):
                validate_buying_document(buying_transaction, doc_type,
                                       getattr(current_user, 'notary_id'), False)
                save_buying_transaction(buying_transaction)
                st.rerun()

    with col4:
        if doc_id:
            if st.button("👁️ View", key=f"view_doc_{doc_type}"):
                st.session_state[f"view_document_{doc_id}"] = True
                st.rerun()


def _render_meetings_section(buying_transaction: Buying, current_user, user_type: str):
    """Render meetings section"""
    st.subheader("📅 Scheduled Meetings")

    # Schedule new meeting
    if can_user_edit_transaction(buying_transaction, getattr(current_user, f'{user_type.lower()}_id'), user_type):
        with st.expander("📅 Schedule New Meeting"):
            _render_meeting_scheduler(buying_transaction, current_user, user_type)

    # Display meetings
    if buying_transaction.scheduled_meetings:
        for meeting in buying_transaction.scheduled_meetings:
            _render_meeting_card(meeting, buying_transaction, current_user, user_type)
    else:
        st.info("No meetings scheduled yet")


def _render_meeting_scheduler(buying_transaction: Buying, current_user, user_type: str):
    """Render meeting scheduling form"""
    user_id = getattr(current_user, f'{user_type.lower()}_id')

    with st.form(f"schedule_meeting_{buying_transaction.buying_id}"):
        col1, col2 = st.columns(2)

        with col1:
            meeting_type = st.selectbox(
                "Meeting Type",
                options=list(MEETING_TYPES.keys()),
                format_func=lambda x: MEETING_TYPES[x]
            )

            meeting_date = st.date_input(
                "Meeting Date",
                min_value=datetime.now().date(),
                value=datetime.now().date() + timedelta(days=1)
            )

        with col2:
            meeting_time = st.time_input(
                "Meeting Time",
                value=datetime.now().time().replace(hour=14, minute=0, second=0, microsecond=0)
            )

            meeting_location = st.text_input(
                "Meeting Location",
                placeholder="Enter meeting location"
            )

        meeting_agenda = st.text_area(
            "Meeting Agenda",
            placeholder="What will be discussed in this meeting?"
        )

        if st.form_submit_button("📅 Schedule Meeting"):
            try:
                meeting_datetime = datetime.combine(meeting_date, meeting_time)
                meeting_data = {
                    "meeting_type": meeting_type,
                    "scheduled_date": meeting_datetime,
                    "participants": [buying_transaction.agent_id, buying_transaction.buyer_id],
                    "location": meeting_location,
                    "agenda": meeting_agenda,
                    "created_by": user_id
                }

                schedule_meeting(buying_transaction, meeting_data)
                save_buying_transaction(buying_transaction)

                st.success(f"✅ Meeting scheduled for {meeting_datetime.strftime('%Y-%m-%d %H:%M')}")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error scheduling meeting: {str(e)}")


def _render_meeting_card(meeting: Dict[str, Any], buying_transaction: Buying, current_user, user_type: str):
    """Render individual meeting card"""
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.write(f"**📅 {MEETING_TYPES.get(meeting['meeting_type'], 'Meeting')}**")
            st.write(f"**🕐 Date:** {meeting['scheduled_date'].strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**📍 Location:** {meeting.get('location', 'TBD')}")

        with col2:
            st.write(f"**📋 Agenda:** {meeting.get('agenda', 'No agenda set')}")
            st.write(f"**👤 Created by:** {meeting.get('created_by', 'Unknown')[:8]}...")
            st.write(f"**Status:** {meeting.get('status', 'scheduled').title()}")

        with col3:
            if meeting.get('status') == 'scheduled':
                if st.button("✅ Complete", key=f"complete_meeting_{meeting.get('meeting_id')}"):
                    # Mark meeting as completed
                    for m in buying_transaction.scheduled_meetings:
                        if m.get('meeting_id') == meeting.get('meeting_id'):
                            m['status'] = 'completed'
                            break
                    save_buying_transaction(buying_transaction)
                    st.rerun()

        st.markdown("---")


def _render_communication_section(buying_transaction: Buying, current_user, user_type: str):
    """Render communication/notes section"""
    st.subheader("💬 Transaction Communication")

    # Add new note
    user_id = getattr(current_user, f'{user_type.lower()}_id')

    with st.form(f"add_note_{buying_transaction.buying_id}"):
        note_text = st.text_area("Add Note", placeholder="Add a note to this transaction...")
        note_type = st.selectbox("Note Type", ["general", "document", "meeting", "urgent"])

        if st.form_submit_button("💬 Add Note"):
            if note_text:
                add_transaction_note(buying_transaction, note_text, user_id, note_type)
                save_buying_transaction(buying_transaction)
                st.success("Note added successfully!")
                st.rerun()

    # Display notes
    if buying_transaction.transaction_notes:
        st.subheader("📝 Transaction History")

        # Sort notes by timestamp (newest first)
        sorted_notes = sorted(buying_transaction.transaction_notes,
                            key=lambda x: x.get('timestamp', datetime.now()), reverse=True)

        for note in sorted_notes:
            _render_note_card(note)
    else:
        st.info("No communication history yet")


def _render_note_card(note: Dict[str, Any]):
    """Render individual note card"""
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**{note.get('note', '')}**")
            st.caption(f"Type: {note.get('note_type', 'general').title()}")

        with col2:
            st.write(f"**Author:** {note.get('author_id', 'Unknown')[:8]}...")
            if note.get('timestamp'):
                st.write(f"**Date:** {note['timestamp'].strftime('%m/%d/%Y %H:%M')}")

        st.markdown("---")


def _render_detailed_progress(buying_transaction: Buying):
    """Render detailed progress view"""
    st.subheader("📊 Detailed Progress")

    progress = get_buying_progress(buying_transaction)

    # Progress overview
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Overall Progress", f"{progress['progress_percentage']:.1f}%")
        st.progress(progress['progress_percentage'] / 100)

        st.write("**Document Status:**")
        for doc_type, doc_name in BUYING_DOCUMENT_TYPES.items():
            doc_id = buying_transaction.buying_documents.get(doc_type)
            validation_info = buying_transaction.document_validation_status.get(doc_type, {})

            if doc_id and validation_info.get("validation_status", False):
                st.success(f"✅ {doc_name}")
            elif doc_id:
                st.warning(f"⏳ {doc_name}")
            else:
                st.error(f"❌ {doc_name}")

    with col2:
        st.write("**Transaction Timeline:**")
        timeline_events = []

        # Add creation event
        timeline_events.append({
            "date": buying_transaction.created_date,
            "event": "Transaction created",
            "type": "creation"
        })

        # Add document uploads
        for doc_type, validation_info in buying_transaction.document_validation_status.items():
            if validation_info.get("upload_date"):
                timeline_events.append({
                    "date": validation_info["upload_date"],
                    "event": f"Document uploaded: {BUYING_DOCUMENT_TYPES.get(doc_type, doc_type)}",
                    "type": "upload"
                })

            if validation_info.get("validation_date"):
                timeline_events.append({
                    "date": validation_info["validation_date"],
                    "event": f"Document validated: {BUYING_DOCUMENT_TYPES.get(doc_type, doc_type)}",
                    "type": "validation"
                })

        # Add meetings
        for meeting in buying_transaction.scheduled_meetings:
            timeline_events.append({
                "date": meeting.get("scheduled_date", datetime.now()),
                "event": f"Meeting: {MEETING_TYPES.get(meeting['meeting_type'], 'Meeting')}",
                "type": "meeting"
            })

        # Sort timeline by date
        timeline_events.sort(key=lambda x: x["date"], reverse=True)

        for event in timeline_events[:10]:  # Show last 10 events
            st.write(f"**{event['date'].strftime('%m/%d %H:%M')}** - {event['event']}")


def _render_transaction_settings(buying_transaction: Buying, current_user, user_type: str):
    """Render transaction settings and actions"""
    st.subheader("⚙️ Transaction Settings")

    user_id = getattr(current_user, f'{user_type.lower()}_id')

    # Status management (for authorized users)
    if user_type.lower() in ["agent", "notary"] or buying_transaction.buyer_id == user_id:
        st.write("**Status Management:**")

        col1, col2 = st.columns(2)

        with col1:
            current_status = buying_transaction.status
            new_status = st.selectbox(
                "Change Status",
                options=list(TRANSACTION_STATUSES.keys()),
                index=list(TRANSACTION_STATUSES.keys()).index(current_status),
                format_func=lambda x: TRANSACTION_STATUSES[x]
            )

        with col2:
            status_notes = st.text_input("Status Change Notes", placeholder="Reason for status change...")

        if st.button("💾 Update Status") and new_status != current_status:
            try:
                update_buying_status(buying_transaction, new_status, status_notes)
                save_buying_transaction(buying_transaction)
                st.success(f"Status updated to: {TRANSACTION_STATUSES[new_status]}")
                st.rerun()
            except Exception as e:
                st.error(f"Error updating status: {e}")

    st.markdown("---")

    # Transaction actions
    st.write("**Transaction Actions:**")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Generate Report"):
            _generate_transaction_report(buying_transaction)

    with col2:
        if st.button("📧 Send Notification"):
            st.info("Notification system not implemented yet")

    with col3:
        if user_type.lower() == "notary" or buying_transaction.buyer_id == user_id:
            if st.button("❌ Cancel Transaction", type="secondary"):
                if st.button("⚠️ Confirm Cancellation", type="secondary"):
                    update_buying_status(buying_transaction, "cancelled", "Transaction cancelled by user")
                    save_buying_transaction(buying_transaction)
                    st.success("Transaction cancelled")
                    st.rerun()


def _generate_transaction_report(buying_transaction: Buying):
    """Generate a transaction report"""
    st.subheader("📊 Transaction Report")

    # Get property details
    properties = get_properties()
    property_data = properties.get(buying_transaction.property_id)

    if not property_data:
        st.error("Property data not found")
        return

    # Report content
    report_content = f"""
# Transaction Report

**Transaction ID:** {buying_transaction.buying_id}
**Property:** {property_data.title}
**Address:** {property_data.address}, {property_data.city}
**Price:** €{buying_transaction.final_price or property_data.price:,.2f}

## Parties Involved
- **Agent:** {buying_transaction.agent_id}
- **Buyer:** {buying_transaction.buyer_id}

## Transaction Status
- **Current Status:** {TRANSACTION_STATUSES.get(buying_transaction.status, buying_transaction.status)}
- **Created:** {buying_transaction.created_date.strftime('%Y-%m-%d %H:%M')}
- **Last Updated:** {buying_transaction.last_updated.strftime('%Y-%m-%d %H:%M')}

## Document Status
"""

    for doc_type, doc_name in BUYING_DOCUMENT_TYPES.items():
        doc_id = buying_transaction.buying_documents.get(doc_type)
        validation_info = buying_transaction.document_validation_status.get(doc_type, {})

        if doc_id and validation_info.get("validation_status", False):
            status = "✅ Validated"
        elif doc_id:
            status = "⏳ Pending Validation"
        else:
            status = "❌ Not Uploaded"

        report_content += f"- **{doc_name}:** {status}\n"

    # Progress
    progress = get_buying_progress(buying_transaction)
    report_content += f"\n## Progress Overview\n"
    report_content += f"- **Overall Progress:** {progress['progress_percentage']:.1f}%\n"
    report_content += f"- **Documents:** {progress['validated_documents']}/{progress['total_documents']} validated\n"
    report_content += f"- **Meetings:** {progress['active_meetings']} scheduled\n"

    # Meetings
    if buying_transaction.scheduled_meetings:
        report_content += f"\n## Scheduled Meetings\n"
        for meeting in buying_transaction.scheduled_meetings:
            meeting_name = MEETING_TYPES.get(meeting['meeting_type'], 'Meeting')
            meeting_date = meeting['scheduled_date'].strftime('%Y-%m-%d %H:%M')
            report_content += f"- **{meeting_name}:** {meeting_date} at {meeting.get('location', 'TBD')}\n"

    # Notes
    if buying_transaction.transaction_notes:
        report_content += f"\n## Recent Communication\n"
        recent_notes = sorted(buying_transaction.transaction_notes,
                            key=lambda x: x.get('timestamp', datetime.now()), reverse=True)[:5]
        for note in recent_notes:
            note_date = note.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M')
            report_content += f"- **{note_date}:** {note.get('note', '')}\n"

    # Display report
    st.markdown(report_content)

    # Download option
    st.download_button(
        label="📥 Download Report",
        data=report_content,
        file_name=f"transaction_report_{buying_transaction.buying_id[:8]}.md",
        mime="text/markdown"
    )