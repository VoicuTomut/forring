"""
GPP - Global Property Platform
Main Application Entry Point
"""

import streamlit as st
from gpp.interface.config.constants import APP_CONFIG
from gpp.interface.utils.database import init_data_files
from gpp.interface.dashboards.agent_dashboard import agent_dashboard
from gpp.interface.dashboards.notary_dashboard import notary_dashboard
from gpp.interface.dashboards.buyer_dashboard import buyer_dashboard
from gpp.interface.utils.user_management import get_or_create_user


def main():
    """Main application entry point"""
    st.set_page_config(**APP_CONFIG)

    # Initialize data storage
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


if __name__ == "__main__":
    main()