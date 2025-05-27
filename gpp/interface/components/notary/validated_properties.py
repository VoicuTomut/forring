"""
Validated properties view for notaries
"""

import streamlit as st
from gpp.classes.notary import Notary
from gpp.classes.property import get_property_additional_docs_count
from gpp.interface.utils.database import get_properties
from gpp.interface.utils.property_helpers import format_timestamp


def show_validated_properties(current_notary: Notary):
    """Show properties that have been validated by this notary"""
    st.subheader("Properties I've Validated")

    properties = get_properties()
    validated_properties = {k: v for k, v in properties.items()
                            if k in current_notary.checked_prop_list}

    if not validated_properties:
        st.info("No validated properties yet.")
        return

    # Display validated properties
    for prop_id, prop_data in validated_properties.items():
        _render_validated_property_card(prop_data)


def _render_validated_property_card(prop_data):
    """Render individual validated property card"""
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
                st.write(f"🗓️ {format_timestamp(prop_data.validation_date)}")

    st.divider()