"""
Notary Dashboard - Document validation interface for notaries
"""

import streamlit as st
from gpp.classes.notary import Notary
from gpp.interface.components.notary.validation_queue import show_validation_queue
from gpp.interface.components.notary.validated_properties import show_validated_properties
from gpp.interface.components.notary.chat_management import notary_chat_dashboard


def notary_dashboard(current_notary: Notary):
    """Main notary dashboard interface"""
    st.header(f"⚖️ Notary Dashboard - {current_notary.notary_id[:8]}...")

    tab1, tab2, tab3 = st.tabs([
        "🔍 Validation Queue",
        "✅ Validated Properties",
        "💬 Communications"
    ])

    with tab1:
        show_validation_queue(current_notary)

    with tab2:
        show_validated_properties(current_notary)

    with tab3:
        notary_chat_dashboard(current_notary)