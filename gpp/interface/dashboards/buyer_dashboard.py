"""
Buyer Dashboard - Property browsing interface for buyers
"""

import streamlit as st
from gpp.classes.buyer import Buyer, add_interest_to_buyer
from gpp.classes.property import reserve_property, get_property_additional_docs_count
from gpp.interface.utils.database import get_documents, save_buyer, load_data, save_data, save_property
from gpp.interface.utils.property_helpers import get_validated_properties, get_property_validation_progress, get_property_photos
from gpp.interface.components.buyer.chat_management import buyer_chat_dashboard
from gpp.interface.config.constants import BUYERS_FILE


def buyer_dashboard(current_buyer: Buyer):
    """Main buyer dashboard interface"""
    st.header(f"💰 Buyer Dashboard - {current_buyer.buyer_id[:8]}...")

    # Tabs for buyer functions - ENHANCED with chat
    tab1, tab2 = st.tabs(["🏠 Browse Properties", "💬 Communications"])

    with tab1:
        _show_property_listings(current_buyer)

    with tab2:
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


def _show_debug_info():
    """Show debug information about properties"""
    from gpp.interface.utils.database import get_properties
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

        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("❤️ Favorite", key=f"fav_{prop_id}"):
                updated_buyer = add_interest_to_buyer(current_buyer, prop_id, "interested")
                buyers = load_data(BUYERS_FILE)
                buyers[current_buyer.buyer_id] = updated_buyer.dict()
                save_data(BUYERS_FILE, buyers)
                st.success("Added to favorites!")

        with col2:
            if st.button("💬 Chat", key=f"chat_{prop_id}"):
                st.session_state['buyer_chat_property_id'] = prop_id
                st.info("Go to Communications tab to start chatting!")

        with col3:
            if st.button("🏠 Reserve", key=f"reserve_{prop_id}"):
                updated_buyer = add_interest_to_buyer(current_buyer, prop_id, "reserved")
                buyers = load_data(BUYERS_FILE)
                buyers[current_buyer.buyer_id] = updated_buyer.dict()
                save_data(BUYERS_FILE, buyers)

                # Reserve the property
                updated_property = reserve_property(prop_data, current_buyer.buyer_id)
                save_property(updated_property)

                st.success("Property reserved!")