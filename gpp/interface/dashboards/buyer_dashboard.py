"""
Enhanced Buyer Dashboard - Property browsing interface for buyers
Now includes document viewing, favorites system, and reservation management
Integrates with existing constants and file structure
"""

import streamlit as st
from typing import Dict, List
from gpp.classes.buyer import Buyer, add_interest_to_buyer
from gpp.classes.property import get_property_additional_docs_count
from gpp.interface.utils.database import get_documents, load_data, save_data, get_properties
from gpp.interface.utils.property_helpers import get_validated_properties, get_property_validation_progress, \
    get_property_photos
from gpp.interface.components.buyer.chat_management import buyer_chat_dashboard
from gpp.interface.config.constants import (
    BUYERS_FILE, MANDATORY_DOCS, ADDITIONAL_DOC_CATEGORIES,
    BUYING_DOCUMENT_TYPES, TRANSACTION_STATUSES
)
from gpp.interface.utils.buying_database import get_user_buying_transactions


def buyer_dashboard(current_buyer: Buyer):
    """Main buyer dashboard interface"""
    st.header(f"💰 Buyer Dashboard - {current_buyer.buyer_id[:8]}...")

    # Enhanced tabs for buyer functions
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 Browse Properties",
        "❤️ My Favorites",
        "📄 My Documents",
        "💬 Communications"
    ])

    with tab1:
        _show_property_listings(current_buyer)

    with tab2:
        _show_buyer_favorites(current_buyer)

    with tab3:
        _show_buyer_documents(current_buyer)

    with tab4:
        buyer_chat_dashboard(current_buyer)


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


def _show_buyer_documents(current_buyer: Buyer):
    """Show documents accessible to buyer (reserved/purchased properties)"""
    st.subheader("📄 Property Documents Access")

    # Get buyer's transactions to see which properties they have access to
    buying_transactions = get_user_buying_transactions(current_buyer.buyer_id, "buyer")

    if not buying_transactions:
        st.info("You don't have any property transactions yet. Reserve a property to access its documents.")
        return

    st.write(f"You have access to documents for **{len(buying_transactions)}** properties:")

    # Show documents for each transaction
    for transaction_id, transaction in buying_transactions.items():
        _show_transaction_documents(transaction_id, transaction, current_buyer)


def _show_transaction_documents(transaction_id: str, transaction, current_buyer: Buyer):
    """Show documents for a specific transaction"""
    # Get property data
    all_properties = get_properties()
    property_data = all_properties.get(transaction.property_id)

    if not property_data:
        st.error(f"Property data not found for transaction {transaction_id[:8]}...")
        return

    with st.expander(f"🏠 {property_data.title} - Transaction {transaction_id[:8]}..."):
        # Transaction status
        status_emoji = {
            "pending": "🟡",
            "documents_pending": "📄",
            "under_review": "🔍",
            "approved": "✅",
            "completed": "🎉",
            "cancelled": "❌"
        }.get(transaction.status, "⚪")

        st.write(f"**Status:** {status_emoji} {transaction.status.replace('_', ' ').title()}")
        st.write(f"**Property:** {property_data.title}")
        st.write(f"**Price:** €{property_data.price:,.2f}")

        # Document sections
        col1, col2 = st.columns(2)

        with col1:
            st.write("**📋 Mandatory Legal Documents**")
            _show_mandatory_documents(property_data)

        with col2:
            st.write("**📎 Additional Documents**")
            _show_additional_documents(property_data)

        # Transaction-specific documents
        if transaction.buying_documents:
            st.write("**💼 Transaction Documents**")
            _show_transaction_specific_documents(transaction)


def _show_mandatory_documents(property_data):
    """Show mandatory legal documents using constants"""
    documents = get_documents()

    for doc_type, doc_name in MANDATORY_DOCS.items():
        doc_id = property_data.mandatory_legal_docs.get(doc_type)

        if doc_id and doc_id in documents:
            document = documents[doc_id]

            col_a, col_b = st.columns([3, 1])
            with col_a:
                if document.validation_status:
                    st.success(f"✅ {doc_name}")
                else:
                    st.warning(f"⏳ {doc_name}")

            with col_b:
                if st.button("👁️", key=f"view_mandatory_{doc_id}", help="View document"):
                    _show_document_viewer(document)
        else:
            st.error(f"❌ {doc_name} - Missing")


def _show_additional_documents(property_data):
    """Show additional documents uploaded by agent using constants"""
    documents = get_documents()

    has_additional = False

    for category, doc_ids in property_data.additional_docs.items():
        if doc_ids and category in ADDITIONAL_DOC_CATEGORIES:
            has_additional = True
            category_name = ADDITIONAL_DOC_CATEGORIES[category]
            st.write(f"**{category_name}:**")

            for doc_id in doc_ids:
                if doc_id in documents:
                    document = documents[doc_id]

                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"• {document.document_name}")
                        st.caption(f"Uploaded: {document.upload_date.strftime('%Y-%m-%d %H:%M')}")

                    with col_b:
                        if st.button("👁️", key=f"view_additional_{doc_id}", help="View document"):
                            _show_document_viewer(document)

    if not has_additional:
        st.info("No additional documents available")


def _show_transaction_specific_documents(transaction):
    """Show transaction-specific documents using constants"""
    documents = get_documents()

    has_transaction_docs = False

    for doc_type, doc_name in BUYING_DOCUMENT_TYPES.items():
        doc_id = transaction.buying_documents.get(doc_type)

        if doc_id and doc_id in documents:
            has_transaction_docs = True
            document = documents[doc_id]

            # Check validation status if available
            validation_info = transaction.document_validation_status.get(doc_type, {})
            is_validated = validation_info.get("validation_status", False)

            col_a, col_b = st.columns([3, 1])
            with col_a:
                if is_validated:
                    st.success(f"✅ {doc_name}")
                else:
                    st.warning(f"⏳ {doc_name} - Pending validation")

                # Show validation notes if available
                validation_notes = validation_info.get("validation_notes", "")
                if validation_notes:
                    st.caption(f"Note: {validation_notes}")

            with col_b:
                if st.button("👁️", key=f"view_transaction_{doc_id}", help="View document"):
                    _show_document_viewer(document)

    if not has_transaction_docs:
        st.info("No transaction documents uploaded yet")


def _show_document_viewer(document):
    """Show document viewer in a modal-like expander"""
    with st.expander(f"📄 Viewing: {document.document_name}", expanded=True):
        st.write(f"**Document:** {document.document_name}")
        st.write(f"**Uploaded:** {document.upload_date.strftime('%Y-%m-%d %H:%M')}")
        st.write(f"**Status:** {'✅ Validated' if document.validation_status else '⏳ Pending validation'}")

        if document.validation_date:
            st.write(f"**Validated:** {document.validation_date.strftime('%Y-%m-%d %H:%M')}")

        # Document content
        if document.document_path:
            st.write(f"**File:** {document.document_path}")

            # Try to determine file type and show appropriate preview
            file_extension = document.document_path.lower().split('.')[-1] if '.' in document.document_path else ''

            if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
                try:
                    st.image(document.document_path, caption=document.document_name)
                except:
                    st.info("📸 Image file - Click to download")
            elif file_extension == 'pdf':
                st.info("📄 PDF Document - Use download link below")
            else:
                st.info(f"📎 {file_extension.upper()} file - Use download link below")

            # Download button placeholder
            if st.button("⬇️ Download Document", key=f"download_{document.document_id}"):
                st.info("Download functionality will be implemented based on your file storage system")
        else:
            st.warning("Document file path not available")


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
    """Render individual property card for buyers"""
    with st.container():
        # Show property photos if available
        photo_docs = get_property_photos(prop_data)

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