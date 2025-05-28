"""
Updated buyer_dashboard.py - Integration with Enhanced Document Viewer
Replace your existing _show_buyer_documents function with the enhanced version
"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
from gpp.classes.buyer import Buyer, add_interest_to_buyer
from gpp.classes.property import get_property_additional_docs_count
from gpp.interface.utils.database import get_documents, load_data, save_data, get_properties
from gpp.interface.utils.property_helpers import get_validated_properties, get_property_validation_progress, \
    get_property_photos
from gpp.interface.components.buyer.chat_management import buyer_chat_dashboard
from gpp.interface.config.constants import (
    BUYERS_FILE, MANDATORY_DOCS, ADDITIONAL_DOC_CATEGORIES,
    BUYING_DOCUMENT_TYPES, TRANSACTION_STATUSES, TRANSACTION_NOTE_TYPES
)
from gpp.interface.utils.buying_database import get_user_buying_transactions
from gpp.interface.components.shared.document_signing_ui import (
    show_signing_workflow_dashboard, integrate_signing_with_buyer_dashboard, show_document_upload_modal
)
from gpp.interface.utils.buying_database import get_user_buying_transactions


def buyer_dashboard(current_buyer: Buyer):
    """Main buyer dashboard interface"""
    st.header(f"💰 Buyer Dashboard - {current_buyer.buyer_id[:8]}...")

    # Enhanced tabs for buyer functions - ADD SIGNING TAB
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Browse Properties",
        "❤️ My Favorites",
        "📄 My Documents",
        "✍️ Document Signing",  # NEW TAB
        "💬 Communications"
    ])

    with tab1:
        _show_property_listings(current_buyer)

    with tab2:
        _show_buyer_favorites(current_buyer)

    with tab3:
        show_enhanced_buyer_documents(current_buyer)

    with tab4:
        # NEW SIGNING TAB CONTENT
        _show_buyer_signing_dashboard(current_buyer)

    with tab5:
        buyer_chat_dashboard(current_buyer)


# ========== ENHANCED DOCUMENT VIEWER ==========
# This replaces the old _show_buyer_documents function

def show_enhanced_buyer_documents(current_buyer: Buyer):
    """Enhanced document viewing interface for buyers"""
    st.subheader("📄 Property Documents Access")

    # Get buyer's transactions to see which properties they have access to
    buying_transactions = get_user_buying_transactions(current_buyer.buyer_id, "buyer")

    if not buying_transactions:
        _show_no_access_message()
        return

    # Property selection for multi-property buyers
    selected_transaction = _handle_property_selection(buying_transactions)
    if not selected_transaction:
        return

    # Show transaction overview
    _show_transaction_overview(selected_transaction)

    # Enhanced document tabs
    _show_enhanced_document_tabs(selected_transaction, current_buyer)

    st.markdown("---")

    # Get buyer's transactions for signing integration
    buying_transactions = get_user_buying_transactions(current_buyer.buyer_id, "buyer")
    if buying_transactions:
        selected_transaction = list(buying_transactions.values())[0]  # Use first transaction
        integrate_signing_with_buyer_dashboard(selected_transaction, current_buyer)


def _show_no_access_message():
    """Show message when buyer has no document access"""
    st.info("🔒 You don't have any property transactions yet.")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("""
        **To access property documents, you need to:**
        1. Browse available properties in the "🏠 Browse Properties" tab
        2. Add properties to your favorites ❤️
        3. Reserve a property with payment 💳
        4. Documents will become available here after reservation
        """)

    with col2:
        st.info("💡 **Tip:** Go to the 'Browse Properties' tab to start exploring available properties!")


def _handle_property_selection(buying_transactions: Dict) -> Optional[object]:
    """Handle property selection for document viewing"""
    if len(buying_transactions) == 1:
        # Single transaction - auto-select
        return list(buying_transactions.values())[0]

    # Multiple transactions - show selector
    st.write(f"You have access to documents for **{len(buying_transactions)}** properties:")

    # Create property options
    all_properties = get_properties()
    property_options = {}

    for transaction_id, transaction in buying_transactions.items():
        property_data = all_properties.get(transaction.property_id)
        if property_data:
            status_emoji = _get_status_emoji(transaction.status)
            option_text = f"{property_data.title} - {status_emoji} {transaction.status.replace('_', ' ').title()}"
            property_options[option_text] = transaction

    if not property_options:
        st.error("Unable to load property information.")
        return None

    selected_option = st.selectbox(
        "Select Property:",
        options=list(property_options.keys()),
        help="Choose which property's documents you want to view"
    )

    return property_options[selected_option]


def _show_transaction_overview(transaction):
    """Show transaction overview with key metrics"""
    all_properties = get_properties()
    property_data = all_properties.get(transaction.property_id)

    if not property_data:
        st.error("Property data not found.")
        return

    # Transaction header
    col1, col2 = st.columns([3, 1])

    with col1:
        st.write(f"## 🏠 {property_data.title}")
        st.write(f"**📍 Location:** {property_data.address}, {property_data.city}")
        st.write(f"**💰 Price:** €{property_data.price:,.2f}")

    with col2:
        status_emoji = _get_status_emoji(transaction.status)
        st.metric(
            "Transaction Status",
            f"{status_emoji} {transaction.status.replace('_', ' ').title()}",
            delta=None
        )

    # Progress metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mandatory_count = len([doc_id for doc_id in property_data.mandatory_legal_docs.values() if doc_id])
        st.metric("Legal Documents", mandatory_count)

    with col2:
        additional_count = sum(len(docs) for docs in property_data.additional_docs.values())
        st.metric("Additional Documents", additional_count)

    with col3:
        transaction_docs = len([doc_id for doc_id in transaction.buying_documents.values() if doc_id])
        st.metric("Transaction Documents", transaction_docs)

    with col4:
        # Calculate overall validation progress
        progress = _calculate_document_progress(transaction, property_data)
        st.metric("Validation Progress", f"{progress['validated']}/{progress['total']}")
        if progress['total'] > 0:
            st.progress(progress['percentage'] / 100)


def _show_enhanced_document_tabs(transaction, current_buyer: Buyer):
    """Show enhanced document tabs with rich viewing experience"""

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Legal Documents",
        "📎 Additional Documents",
        "💼 Transaction Documents",
        "📊 Document Timeline"
    ])

    with tab1:
        _show_enhanced_mandatory_documents(transaction)

    with tab2:
        _show_enhanced_additional_documents(transaction)

    with tab3:
        _show_enhanced_transaction_documents(transaction)

    with tab4:
        _show_document_timeline(transaction)


def _show_enhanced_mandatory_documents(transaction):
    """Show mandatory legal documents with rich information"""
    st.subheader("📋 Mandatory Legal Documents")
    st.caption("Required legal documents validated by notary")

    all_properties = get_properties()
    property_data = all_properties.get(transaction.property_id)
    documents = get_documents()

    if not property_data:
        st.error("Property data not found.")
        return

    # Group documents by validation status
    validated_docs = []
    pending_docs = []
    missing_docs = []

    for doc_type, doc_name in MANDATORY_DOCS.items():
        doc_id = property_data.mandatory_legal_docs.get(doc_type)

        if doc_id and doc_id in documents:
            document = documents[doc_id]
            if document.validation_status:
                validated_docs.append((doc_type, doc_name, document))
            else:
                pending_docs.append((doc_type, doc_name, document))
        else:
            missing_docs.append((doc_type, doc_name, None))

    # Show validation summary
    total_mandatory = len(MANDATORY_DOCS)
    validated_count = len(validated_docs)

    if validated_count == total_mandatory:
        st.success(f"✅ All {total_mandatory} mandatory documents validated!")
    else:
        st.info(f"📊 Progress: {validated_count}/{total_mandatory} documents validated")

    # Show documents by category
    if validated_docs:
        st.write("### ✅ Validated Documents")
        for doc_type, doc_name, document in validated_docs:
            _render_enhanced_document_card(document, doc_name, "validated")

    if pending_docs:
        st.write("### ⏳ Pending Validation")
        for doc_type, doc_name, document in pending_docs:
            _render_enhanced_document_card(document, doc_name, "pending")

    if missing_docs:
        st.write("### ❌ Missing Documents")
        for doc_type, doc_name, _ in missing_docs:
            st.error(f"📄 {doc_name} - Not uploaded by agent yet")


def _show_enhanced_additional_documents(transaction):
    """Show additional documents with categorization"""
    st.subheader("📎 Additional Property Documents")
    st.caption("Supplementary documents provided by the agent")

    all_properties = get_properties()
    property_data = all_properties.get(transaction.property_id)
    documents = get_documents()

    if not property_data:
        st.error("Property data not found.")
        return

    # Check if there are any additional documents
    has_additional = any(
        doc_ids for doc_ids in property_data.additional_docs.values()
    )

    if not has_additional:
        st.info("📋 No additional documents have been uploaded by the agent yet.")
        return

    # Show documents by category
    for category, doc_ids in property_data.additional_docs.items():
        if doc_ids and category in ADDITIONAL_DOC_CATEGORIES:
            category_name = ADDITIONAL_DOC_CATEGORIES[category]

            with st.expander(f"{category_name} ({len(doc_ids)} documents)", expanded=True):
                for doc_id in doc_ids:
                    if doc_id in documents:
                        document = documents[doc_id]
                        _render_enhanced_document_card(document, document.document_name, "additional")


def _show_enhanced_transaction_documents(transaction):
    """Show transaction-specific documents"""
    st.subheader("💼 Transaction Documents")
    st.caption("Documents specific to your purchase transaction")

    documents = get_documents()

    # Check if there are transaction documents
    has_transaction_docs = any(
        doc_id for doc_id in transaction.buying_documents.values() if doc_id
    )

    if not has_transaction_docs:
        st.info("📋 No transaction documents uploaded yet.")
        st.write("""
        **Transaction documents may include:**
        - Purchase contracts
        - Payment proofs  
        - Bank loan approvals
        - Property inspection reports
        - Insurance policies
        """)
        return

    # Group by validation status
    validated_docs = []
    pending_docs = []

    for doc_type, doc_name in BUYING_DOCUMENT_TYPES.items():
        doc_id = transaction.buying_documents.get(doc_type)

        if doc_id and doc_id in documents:
            document = documents[doc_id]
            validation_info = transaction.document_validation_status.get(doc_type, {})
            is_validated = validation_info.get("validation_status", False)

            doc_info = (doc_type, doc_name, document, validation_info)

            if is_validated:
                validated_docs.append(doc_info)
            else:
                pending_docs.append(doc_info)

    # Show validation progress
    total_docs = len(validated_docs) + len(pending_docs)
    if total_docs > 0:
        progress_pct = (len(validated_docs) / total_docs) * 100
        st.progress(progress_pct / 100)
        st.caption(f"Transaction document validation: {len(validated_docs)}/{total_docs} completed")

    # Show documents
    if validated_docs:
        st.write("### ✅ Validated Transaction Documents")
        for doc_type, doc_name, document, validation_info in validated_docs:
            _render_transaction_document_card(document, doc_name, validation_info, "validated")

    if pending_docs:
        st.write("### ⏳ Pending Validation")
        for doc_type, doc_name, document, validation_info in pending_docs:
            _render_transaction_document_card(document, doc_name, validation_info, "pending")


def _show_document_timeline(transaction):
    """Show document timeline and history"""
    st.subheader("📊 Document Timeline")
    st.caption("Chronological view of all document activities")

    # Collect timeline events
    timeline_events = []

    # Add transaction document events
    for doc_type, validation_info in transaction.document_validation_status.items():
        upload_date = validation_info.get("upload_date")
        validation_date = validation_info.get("validation_date")

        if upload_date:
            if isinstance(upload_date, str):
                upload_date = datetime.fromisoformat(upload_date)

            timeline_events.append({
                "timestamp": upload_date,
                "type": "transaction_upload",
                "action": f"Uploaded {BUYING_DOCUMENT_TYPES.get(doc_type, doc_type)}",
                "details": validation_info,
                "category": "Transaction Documents"
            })

        if validation_date:
            if isinstance(validation_date, str):
                validation_date = datetime.fromisoformat(validation_date)

            timeline_events.append({
                "timestamp": validation_date,
                "type": "validation",
                "action": f"Validated {BUYING_DOCUMENT_TYPES.get(doc_type, doc_type)}",
                "details": validation_info,
                "category": "Validation"
            })

    # Sort by timestamp (most recent first)
    timeline_events.sort(key=lambda x: x["timestamp"], reverse=True)

    if not timeline_events:
        st.info("📋 No document activity recorded yet.")
        return

    # Display timeline
    for event in timeline_events:
        _render_timeline_event(event)


def _render_enhanced_document_card(document, doc_name: str, doc_status: str):
    """Render an enhanced document card with rich information"""

    with st.container():
        # Card header
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            # Document name and type
            if doc_status == "validated":
                st.success(f"✅ **{doc_name}**")
            elif doc_status == "pending":
                st.warning(f"⏳ **{doc_name}**")
            else:
                st.info(f"📄 **{doc_name}**")

            # Document metadata
            st.caption(f"📁 {document.document_name}")
            st.caption(f"📅 Uploaded: {document.upload_date.strftime('%Y-%m-%d %H:%M')}")

        with col2:
            # Validation info
            if document.validation_status and document.validation_date:
                st.success("**Validated**")
                st.caption(f"🕒 {document.validation_date.strftime('%Y-%m-%d')}")
            else:
                st.warning("**Pending**")
                st.caption("Awaiting notary")

        with col3:
            # Action buttons
            if st.button("👁️ View", key=f"view_{document.document_id}", help="View document"):
                _show_document_viewer(document, doc_name)

            if st.button("⬇️ Download", key=f"download_{document.document_id}", help="Download document"):
                _handle_document_download(document, doc_name)

        st.divider()


def _render_transaction_document_card(document, doc_name: str, validation_info: dict, status: str):
    """Render transaction document card with validation details"""

    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            if status == "validated":
                st.success(f"✅ **{doc_name}**")
            else:
                st.warning(f"⏳ **{doc_name}**")

            st.caption(f"📁 {document.document_name}")

            # Show upload details
            upload_date = validation_info.get("upload_date")
            if upload_date:
                if isinstance(upload_date, str):
                    upload_date = datetime.fromisoformat(upload_date)
                st.caption(f"📅 Uploaded: {upload_date.strftime('%Y-%m-%d %H:%M')}")

        with col2:
            if status == "validated":
                validation_date = validation_info.get("validation_date")
                if validation_date:
                    if isinstance(validation_date, str):
                        validation_date = datetime.fromisoformat(validation_date)
                    st.success("**Validated**")
                    st.caption(f"🕒 {validation_date.strftime('%Y-%m-%d')}")
            else:
                st.warning("**Under Review**")
                st.caption("Notary validation")

        with col3:
            if st.button("👁️ View", key=f"view_trans_{document.document_id}"):
                _show_document_viewer(document, doc_name)

            if st.button("⬇️ Download", key=f"download_trans_{document.document_id}"):
                _handle_document_download(document, doc_name)

        # Show validation notes if available
        validation_notes = validation_info.get("validation_notes", "")
        if validation_notes:
            st.info(f"💬 **Notary Note:** {validation_notes}")

        st.divider()


def _render_timeline_event(event):
    """Render a single timeline event"""

    col1, col2, col3 = st.columns([1, 3, 1])

    with col1:
        # Event type icon
        if event["type"] == "transaction_upload":
            st.write("📤")
        elif event["type"] == "validation":
            st.write("✅")
        else:
            st.write("📄")

    with col2:
        # Event description
        st.write(f"**{event['action']}**")
        st.caption(f"Category: {event['category']}")

        # Additional details
        details = event["details"]
        if event["type"] == "validation" and details.get("validation_notes"):
            st.caption(f"💬 Note: {details['validation_notes']}")

    with col3:
        # Timestamp
        timestamp = event["timestamp"]
        st.caption(f"🕒 {timestamp.strftime('%Y-%m-%d')}")
        st.caption(f"{timestamp.strftime('%H:%M')}")

    st.divider()


def _handle_document_download(document, doc_name: str):
    """Handle document download with actual file serving"""
    from gpp.interface.utils.file_storage import file_exists, read_file_content, get_file_info
    import os

    if not file_exists(document.document_path):
        st.error(f"📥 File not available: {doc_name}")
        st.warning("The document file could not be found in storage.")
        return

    # Read file content
    file_content = read_file_content(document.document_path)
    if not file_content:
        st.error(f"📥 Cannot read file: {doc_name}")
        return

    # Get safe filename and MIME type
    safe_filename = _get_safe_filename(document.document_name, document.document_path)
    mime_type = _get_mime_type(document.document_path)

    # Show download success message
    st.success(f"📥 Download ready for: {doc_name}")

    # Create actual download button
    st.download_button(
        label=f"⬇️ Download {doc_name}",
        data=file_content,
        file_name=safe_filename,
        mime=mime_type,
        key=f"download_action_{document.document_id}",
        type="primary"
    )


def _show_document_viewer(document, doc_name: str):
    """Enhanced document viewer with actual image display and working download like notary interface"""
    from gpp.interface.utils.file_storage import file_exists, read_file_content, get_file_info
    from PIL import Image
    import base64
    import os

    st.markdown("---")
    st.markdown("### 📄 Document Viewer")

    with st.container():
        # Document information header
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.write(f"**📄 {doc_name}**")
            st.caption(f"File: {document.document_name}")
            st.caption(f"Document ID: {document.document_id[:8]}...")

        with col2:
            # WORKING DOWNLOAD BUTTON
            if _render_download_button(document, doc_name):
                pass  # Download handled in the function

        with col3:
            # Full screen button
            if st.button("🔍 Full View", key=f"fullscreen_{document.document_id}"):
                st.session_state[f'fullscreen_{document.document_id}'] = True
                st.rerun()

    # Document details
    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("**📋 Document Information**")
        st.write(f"• **File Path:** `{document.document_path}`")

        # Show file info
        if file_exists(document.document_path):
            file_info = get_file_info(document.document_path)
            st.success(f"• **File Status:** ✅ Available ({file_info['size_mb']} MB)")
            st.write(f"• **File Type:** {file_info.get('extension', 'unknown').upper()}")
        else:
            st.error("• **File Status:** ❌ File not found")

        # Format upload date properly
        upload_date_str = document.upload_date.strftime('%Y-%m-%d %H:%M') if document.upload_date else "Unknown"
        st.write(f"• **Uploaded:** {upload_date_str}")

        # Show uploader info
        if document.upload_id:
            st.write(f"• **Uploaded by:** {document.upload_id[:8]}...")

        # Show validation status
        if document.validation_status:
            st.success("✅ **Status:** Validated")
            if document.validation_date:
                validation_date_str = document.validation_date.strftime('%Y-%m-%d %H:%M')
                st.write(f"• **Validated on:** {validation_date_str}")
            if document.who_validate:
                st.write(f"• **Validated by:** Notary {document.who_validate[:8]}...")
        else:
            st.warning("⏳ **Status:** Pending Validation")

    with col2:
        st.write("**👁️ Document Preview**")
        _render_actual_document_preview(document)

    # Full screen view
    if st.session_state.get(f'fullscreen_{document.document_id}', False):
        _render_fullscreen_viewer(document, doc_name)

    st.markdown("---")


def _render_download_button(document, doc_name: str):
    """Render working download button exactly like notary interface"""
    from gpp.interface.utils.file_storage import file_exists, read_file_content, get_file_info

    if not file_exists(document.document_path):
        st.button("📥 Download", disabled=True, help="File not available")
        return False

    # Read file content
    file_content = read_file_content(document.document_path)
    if not file_content:
        st.button("📥 Download", disabled=True, help="Cannot read file")
        return False

    # Get safe filename and MIME type
    safe_filename = _get_safe_filename(document.document_name, document.document_path)
    mime_type = _get_mime_type(document.document_path)

    # Create download button
    st.download_button(
        label="📥 Download",
        data=file_content,
        file_name=safe_filename,
        mime=mime_type,
        key=f"download_{document.document_id}"
    )
    return True


def _render_actual_document_preview(document):
    """Render actual document preview with real content like notary interface"""
    from gpp.interface.utils.file_storage import file_exists, get_file_info
    from PIL import Image

    if not file_exists(document.document_path):
        st.error("📄 **File Not Found**")
        st.write("File is not available in storage")
        return

    file_path = document.document_path.lower()

    # IMAGE FILES - Show actual images
    if file_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
        try:
            # Open and display the actual image
            image = Image.open(document.document_path)
            st.success("📷 **Image Document**")
            st.image(image, caption=document.document_name, use_container_width=True)

            # Show image info
            st.write(f"• **Dimensions:** {image.size[0]} x {image.size[1]} pixels")
            st.write(f"• **Format:** {image.format}")
            st.write(f"• **Mode:** {image.mode}")

        except Exception as e:
            st.error(f"📷 **Image Error:** {str(e)}")
            st.write("Could not display image")

    # PDF FILES
    elif file_path.endswith('.pdf'):
        st.info("📄 **PDF Document**")
        file_info = get_file_info(document.document_path)
        st.write("📄 PDF file ready for download")
        st.write(f"• **Size:** {file_info['size_mb']} MB")
        st.write("• Click Download to view in PDF reader")
        st.write("• Full View for embedded viewer")

    # TEXT FILES - Show content preview
    elif file_path.endswith(('.txt', '.md', '.py', '.js', '.html', '.css')):
        try:
            with open(document.document_path, 'r', encoding='utf-8') as f:
                content = f.read()

            st.info("📝 **Text Document**")
            # Show first 500 characters
            preview = content[:500]
            if len(content) > 500:
                preview += "..."

            st.code(preview, language=None)
            st.write(f"• **Lines:** {len(content.splitlines())}")
            st.write(f"• **Characters:** {len(content)}")

        except Exception as e:
            st.error(f"📝 **Text Error:** {str(e)}")

    # OFFICE DOCUMENTS
    elif file_path.endswith(('.doc', '.docx')):
        st.info("📝 **Word Document**")
        file_info = get_file_info(document.document_path)
        st.write("📝 Microsoft Word document")
        st.write(f"• **Size:** {file_info['size_mb']} MB")
        st.write("• Download to open in Word")

    elif file_path.endswith(('.xls', '.xlsx')):
        st.info("📊 **Excel Document**")
        file_info = get_file_info(document.document_path)
        st.write("📊 Microsoft Excel spreadsheet")
        st.write(f"• **Size:** {file_info['size_mb']} MB")
        st.write("• Download to open in Excel")

    # GENERIC FILES
    else:
        st.info("📄 **Document File**")
        file_info = get_file_info(document.document_path)
        extension = file_info.get('extension', '').upper()
        st.write(f"📄 {extension} file" if extension else "📄 Binary file")
        st.write(f"• **Size:** {file_info['size_mb']} MB")
        st.write("• Download to view in appropriate application")


def _render_fullscreen_viewer(document, doc_name: str):
    """Render full screen document viewer with actual content like notary interface"""
    from gpp.interface.utils.file_storage import file_exists, get_file_info
    from PIL import Image
    import base64

    st.markdown("---")
    st.markdown("### 🔍 Full Screen Document Viewer")

    # Header with controls
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    with col1:
        st.write(f"**📄 {doc_name}**")

    with col2:
        # Download button in fullscreen
        _render_download_button(document, doc_name)

    with col3:
        if st.button("🖨️ Print", key=f"fs_print_{document.document_id}"):
            st.info("🖨️ Print: Right-click on image/document and select Print")

    with col4:
        if st.button("✖️ Close", key=f"close_{document.document_id}"):
            st.session_state[f'fullscreen_{document.document_id}'] = False
            st.rerun()

    # Full document content
    st.markdown("---")

    if not file_exists(document.document_path):
        st.error("📄 **File Not Available**")
        st.write("The file is not available in storage.")
        return

    file_path = document.document_path.lower()

    # FULL SCREEN IMAGE VIEWER
    if file_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
        try:
            image = Image.open(document.document_path)
            st.markdown("### 📷 Full Screen Image Viewer")

            # Zoom controls
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                zoom_level = st.select_slider(
                    "🔍 Zoom Level",
                    options=[25, 50, 75, 100, 125, 150, 200],
                    value=100,
                    key=f"zoom_{document.document_id}"
                )

            # Calculate display width
            max_width = min(800, int(image.size[0] * zoom_level / 100))

            # Display image
            st.image(
                image,
                caption=f"{doc_name} ({zoom_level}%)",
                width=max_width
            )

            # Image info
            st.info(f"📐 Original size: {image.size[0]} x {image.size[1]} pixels | Current zoom: {zoom_level}%")

        except Exception as e:
            st.error(f"Cannot display image: {str(e)}")

    # FULL SCREEN PDF VIEWER (Embedded)
    elif file_path.endswith('.pdf'):
        st.markdown("### 📄 PDF Viewer")

        # Try to embed PDF
        try:
            with open(document.document_path, "rb") as f:
                pdf_bytes = f.read()

            # Create base64 encoded PDF for embedding
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

            # Embed PDF viewer
            pdf_viewer = f"""
            <iframe 
                src="data:application/pdf;base64,{pdf_base64}" 
                width="100%" 
                height="800px"
                style="border: none;">
            </iframe>
            """

            st.markdown(pdf_viewer, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Cannot display PDF: {str(e)}")
            st.info("💡 Download the file to view in your PDF reader")

    # FULL SCREEN TEXT VIEWER
    elif file_path.endswith(('.txt', '.md', '.py', '.js', '.html', '.css', '.json')):
        try:
            with open(document.document_path, 'r', encoding='utf-8') as f:
                content = f.read()

            st.markdown("### 📝 Text Document Viewer")

            # Language detection for syntax highlighting
            language = None
            if file_path.endswith('.py'):
                language = 'python'
            elif file_path.endswith('.js'):
                language = 'javascript'
            elif file_path.endswith('.html'):
                language = 'html'
            elif file_path.endswith('.css'):
                language = 'css'
            elif file_path.endswith('.json'):
                language = 'json'

            # Display content with syntax highlighting
            st.code(content, language=language)

            # Document stats
            lines = len(content.splitlines())
            chars = len(content)
            words = len(content.split())
            st.info(f"📊 Document stats: {lines} lines, {words} words, {chars} characters")

        except Exception as e:
            st.error(f"Cannot display text file: {str(e)}")

    # OTHER FILES
    else:
        st.markdown("### 📄 Document Information")
        file_info = get_file_info(document.document_path)

        col1, col2 = st.columns(2)
        with col1:
            st.write("**File Details:**")
            st.write(f"• **Size:** {file_info['size_mb']} MB")
            st.write(f"• **Type:** {file_info.get('extension', 'unknown').upper()}")
            st.write(f"• **Created:** {file_info.get('created', 'Unknown')}")
            st.write(f"• **Modified:** {file_info.get('modified', 'Unknown')}")

        with col2:
            st.write("**Actions:**")
            st.write("• Use Download button to save file")
            st.write("• Open in appropriate application")
            st.write("• File preview not available for this type")

    st.markdown("---")


def _get_safe_filename(doc_name, file_path):
    """Get a safe filename for download"""
    import os

    if doc_name and '.' in doc_name:
        return doc_name

    # Extract filename from path
    if file_path:
        filename = os.path.basename(file_path)
        if filename:
            return filename

    # Fallback
    return doc_name if doc_name else "document.txt"


def _get_mime_type(file_path):
    """Get MIME type based on file extension"""
    if not file_path:
        return "application/octet-stream"

    extension = file_path.lower().split('.')[-1] if '.' in file_path else ''

    mime_types = {
        'pdf': 'application/pdf',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'txt': 'text/plain',
        'csv': 'text/csv',
        'html': 'text/html',
        'css': 'text/css',
        'js': 'application/javascript',
        'py': 'text/x-python',
        'json': 'application/json'
    }

    return mime_types.get(extension, 'application/octet-stream')


def _get_status_emoji(status: str) -> str:
    """Get emoji for transaction status"""
    return {
        "pending": "🟡",
        "documents_pending": "📄",
        "under_review": "🔍",
        "approved": "✅",
        "completed": "🎉",
        "cancelled": "❌",
        "on_hold": "⏸️"
    }.get(status, "⚪")
    """Get emoji for transaction status"""
    return {
        "pending": "🟡",
        "documents_pending": "📄",
        "under_review": "🔍",
        "approved": "✅",
        "completed": "🎉",
        "cancelled": "❌",
        "on_hold": "⏸️"
    }.get(status, "⚪")


def _calculate_document_progress(transaction, property_data) -> Dict:
    """Calculate overall document validation progress"""

    total_documents = 0
    validated_documents = 0

    # Count mandatory documents
    documents = get_documents()
    for doc_id in property_data.mandatory_legal_docs.values():
        if doc_id and doc_id in documents:
            total_documents += 1
            if documents[doc_id].validation_status:
                validated_documents += 1

    # Count transaction documents
    for doc_type, validation_info in transaction.document_validation_status.items():
        if transaction.buying_documents.get(doc_type):
            total_documents += 1
            if validation_info.get("validation_status", False):
                validated_documents += 1

    percentage = (validated_documents / total_documents * 100) if total_documents > 0 else 0

    return {
        "total": total_documents,
        "validated": validated_documents,
        "percentage": percentage
    }


# ========== EXISTING FUNCTIONS (Keep unchanged) ==========

def _show_property_listings(current_buyer: Buyer):
    """Show property listings for buyers"""
    st.subheader("Available Properties")

    # Show debug info
    with st.expander("🔍 Debug Information"):
        _show_debug_info()

    # Get validated properties
    validated_properties = get_validated_properties()

    if not validated_properties:
        st.info(
            "No validated properties available yet. Properties will appear here once notaries complete their validation.")
        return

    # Display properties in card grid
    _display_property_grid(validated_properties, current_buyer)


def _show_buyer_favorites(current_buyer: Buyer):
    """Show buyer's favorite properties"""
    st.subheader("❤️ My Favorite Properties")

    if not current_buyer.interested_properties:
        st.info(
            "You haven't added any properties to your favorites yet. Browse properties and click '❤️ Favorite' to add them here.")
        return

    # Get all properties and filter favorites
    all_properties = get_properties()
    favorite_properties = {
        prop_id: prop_data for prop_id, prop_data in all_properties.items()
        if prop_id in current_buyer.interested_properties
    }

    if not favorite_properties:
        st.warning("Some of your favorite properties may no longer be available.")
        return

    # Display favorite properties
    st.write(f"You have **{len(favorite_properties)}** favorite properties:")

    for i, (prop_id, prop_data) in enumerate(favorite_properties.items()):
        with st.expander(f"🏠 {prop_data.title} - €{prop_data.price:,.2f}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write(f"**📏 Size:** {prop_data.dimension}")
                st.write(f"**📍 Location:** {prop_data.address}, {prop_data.city}")
                if prop_data.number_of_rooms:
                    st.write(f"**🏠 Rooms:** {prop_data.number_of_rooms}")
                st.write(f"**📝 Description:** {prop_data.description}")

                # Show validation status
                progress = get_property_validation_progress(prop_id)
                if progress['validated'] == progress['total'] and progress['total'] > 0:
                    st.success("✅ Fully Validated by Notary")
                else:
                    st.warning(f"⏳ Validation in progress ({progress['validated']}/{progress['total']})")

            with col2:
                # Action buttons
                if st.button("🏠 Reserve Now", key=f"reserve_fav_{prop_id}", type="primary"):
                    st.session_state["payment_page_property"] = prop_id
                    st.rerun()

                if st.button("💬 Chat", key=f"chat_fav_{prop_id}"):
                    st.session_state['buyer_chat_property_id'] = prop_id
                    st.info("Go to Communications tab to start chatting!")

                if st.button("💔 Remove", key=f"remove_fav_{prop_id}"):
                    # Remove from favorites
                    current_buyer.interested_properties.remove(prop_id)
                    buyers = load_data(BUYERS_FILE)
                    buyers[current_buyer.buyer_id] = current_buyer.dict()
                    save_data(BUYERS_FILE, buyers)
                    st.success("Removed from favorites!")
                    st.rerun()


def _show_debug_info():
    """Show debug information about properties"""
    properties = get_properties()
    st.write(f"**Total properties in system:** {len(properties)}")

    for prop_id, prop_data in properties.items():
        progress = get_property_validation_progress(prop_id)
        st.write(f"**{prop_data.title}:**")
        st.write(f"  - Progress: {progress['validated']}/{progress['total']}")
        st.write(f"  - Notary attached: {prop_data.notary_attached}")
        st.write(f"  - Looking for notary: {prop_data.looking_for_notary}")
        st.write("---")


def _display_property_grid(validated_properties, current_buyer):
    """Display properties in a grid layout"""
    cols = st.columns(2)

    for i, (prop_id, prop_data) in enumerate(validated_properties.items()):
        with cols[i % 2]:
            _render_property_card(prop_id, prop_data, current_buyer)

        if i % 2 == 1:  # Add spacing after every two properties
            st.write("")


def _render_property_card(prop_id: str, prop_data, current_buyer: Buyer):
    """Render individual property card for buyers with actual image display"""
    with st.container():
        # Show property photos if available - ENHANCED WITH ACTUAL IMAGES
        photo_docs = get_property_photos(prop_data)

        if photo_docs:
            # Show first photo + count if multiple
            from PIL import Image
            from gpp.interface.utils.file_storage import file_exists

            first_photo = photo_docs[0]  # Get first photo document

            if file_exists(first_photo.document_path):
                try:
                    # Display actual image
                    image = Image.open(first_photo.document_path)
                    st.image(image, caption=prop_data.title, use_container_width=True)

                    # Show photo count if multiple
                    if len(photo_docs) > 1:
                        st.caption(f"📸 {len(photo_docs)} photos available")
                except Exception as e:
                    # Fallback if image can't be loaded
                    st.image("https://via.placeholder.com/300x200?text=Image+Error",
                             caption=prop_data.title)
                    st.caption(f"📸 {len(photo_docs)} photos available (display error)")
            else:
                # File not found, show placeholder
                st.image("https://via.placeholder.com/300x200?text=Photo+Not+Found",
                         caption=prop_data.title)
                st.caption(f"📸 {len(photo_docs)} photos available (file missing)")
        else:
            # No photos, show placeholder as before
            st.image("https://via.placeholder.com/300x200?text=Property+Photo",
                     caption=prop_data.title)

        # Property Information Section (unchanged)
        st.write(f"**{prop_data.title}**")
        st.write(f"**€{prop_data.price:,.2f}**")
        st.write(f"📏 {prop_data.dimension}")
        st.write(f"📍 {prop_data.address}, {prop_data.city}")

        if prop_data.number_of_rooms:
            st.write(f"🏠 {prop_data.number_of_rooms} rooms")

        st.write(f"📝 {prop_data.description[:100]}...")

        # Show validation status
        st.success("✅ Fully Validated by Notary")

        # Show if property has additional documentation
        additional_count = sum(get_property_additional_docs_count(prop_data).values())
        if additional_count > 0:
            st.info(f"📎 {additional_count} additional documents available")

        # Check if buyer has reserved this property
        buying_transactions = get_user_buying_transactions(current_buyer.buyer_id, "buyer")
        has_reserved = any(t.property_id == prop_id for t in buying_transactions.values())

        if has_reserved:
            st.success("🎉 You have reserved this property!")

        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            # Show different heart based on favorite status
            is_favorite = prop_id in current_buyer.interested_properties
            heart_icon = "💔" if is_favorite else "❤️"
            heart_text = "Unfavorite" if is_favorite else "Favorite"

            if st.button(f"{heart_icon} {heart_text}", key=f"fav_{prop_id}"):
                if is_favorite:
                    # Remove from favorites
                    current_buyer.interested_properties.remove(prop_id)
                    st.success("Removed from favorites!")
                else:
                    # Add to favorites
                    updated_buyer = add_interest_to_buyer(current_buyer, prop_id, "interested")
                    current_buyer.interested_properties = updated_buyer.interested_properties
                    st.success("Added to favorites!")

                # Save changes
                buyers = load_data(BUYERS_FILE)
                buyers[current_buyer.buyer_id] = current_buyer.dict()
                save_data(BUYERS_FILE, buyers)
                st.rerun()

        with col2:
            if st.button("💬 Chat", key=f"chat_{prop_id}"):
                st.session_state['buyer_chat_property_id'] = prop_id
                st.info("Go to Communications tab to start chatting!")

        with col3:
            # Reserve button - show different states
            if has_reserved:
                if st.button("📄 View Docs", key=f"docs_{prop_id}", type="secondary"):
                    st.info("Go to 'My Documents' tab to view property documents!")
            else:
                if st.button("🏠 Reserve", key=f"reserve_{prop_id}", type="primary"):
                    # Set session state to trigger payment page
                    st.session_state["payment_page_property"] = prop_id
                    st.rerun()




def _show_buyer_signing_dashboard(current_buyer: Buyer):
    """Show buyer signing dashboard"""
    st.subheader("✍️ Document Signing & Workflow")

    # Get buyer's transactions
    buying_transactions = get_user_buying_transactions(current_buyer.buyer_id, "buyer")

    if not buying_transactions:
        st.info("📋 No active transactions. Reserve a property to start the signing process!")
        return

    # Transaction selector if multiple transactions
    if len(buying_transactions) > 1:
        transaction_options = {}
        for txn_id, txn in buying_transactions.items():
            # Get property info for display
            from gpp.interface.utils.database import get_properties
            properties = get_properties()
            prop_data = properties.get(txn.property_id)
            display_name = f"{prop_data.title if prop_data else txn.property_id[:8]}... - {txn.status}"
            transaction_options[display_name] = txn

        selected_option = st.selectbox(
            "Select Transaction:",
            options=list(transaction_options.keys())
        )
        selected_transaction = transaction_options[selected_option]
    else:
        selected_transaction = list(buying_transactions.values())[0]

    # Show signing workflow for selected transaction
    show_signing_workflow_dashboard(selected_transaction, current_buyer, "buyer")

    # Handle document upload modals
    for doc_type in ["proof_of_funds", "mortgage_pre_approval", "deposit_payment_proof",
                     "due_diligence_documents", "final_payment_proof"]:
        if st.session_state.get(f"upload_doc_{doc_type}"):
            show_document_upload_modal(selected_transaction, doc_type, current_buyer, "buyer")
            break