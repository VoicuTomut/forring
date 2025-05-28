"""
Document Signing UI Components
Complete signing interface for all user types
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional

from gpp.classes.buying import (
    Buying, can_user_sign_document, sign_document, get_document_signing_status,
    is_document_fully_signed, get_current_phase_requirements
)
from gpp.interface.config.constants import (
    ENHANCED_BUYING_DOCUMENT_TYPES, ENHANCED_WORKFLOW_PHASES,
    SIGNATURE_BUTTON_STYLES, PHASE_PROGRESSION_MESSAGES
)
from gpp.interface.utils.buying_database import save_buying_transaction


def show_signing_workflow_dashboard(buying_obj: Buying, current_user, user_type: str):
    """Main signing workflow dashboard"""
    st.title("✍️ Document Signing Workflow")

    user_id = getattr(current_user, f'{user_type.lower()}_id')

    # Phase overview
    _render_workflow_progress(buying_obj)

    # Current phase requirements
    _render_current_phase_requirements(buying_obj)

    # Documents section
    _render_signing_documents_section(buying_obj, user_id, user_type)

    # Phase progression check
    _check_phase_progression(buying_obj)


def _render_workflow_progress(buying_obj: Buying):
    """Render workflow progress bar"""
    st.subheader("📊 Transaction Progress")

    phases = list(ENHANCED_WORKFLOW_PHASES.keys())
    current_phase_index = phases.index(buying_obj.current_phase) if buying_obj.current_phase in phases else 0

    # Progress bar
    progress = (current_phase_index + 1) / len(phases) * 100
    st.progress(progress / 100, text=f"Phase {current_phase_index + 1} of {len(phases)}")

    # Phase indicators
    cols = st.columns(len(phases))
    for i, (phase_key, phase_config) in enumerate(ENHANCED_WORKFLOW_PHASES.items()):
        with cols[i]:
            if i < current_phase_index:
                st.success(f"✅ {phase_config['name']}")
            elif i == current_phase_index:
                st.info(f"🔄 {phase_config['name']}")
            else:
                st.write(f"⏳ {phase_config['name']}")


def _render_current_phase_requirements(buying_obj: Buying):
    """Render current phase requirements"""
    st.subheader(f"📋 Current Phase: {ENHANCED_WORKFLOW_PHASES.get(buying_obj.current_phase, {}).get('name', buying_obj.current_phase)}")

    requirements = get_current_phase_requirements(buying_obj)

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Required Documents:**")
        for doc_type in requirements["required_documents"]:
            doc_config = ENHANCED_BUYING_DOCUMENT_TYPES.get(doc_type, {})
            doc_name = doc_config.get("name", doc_type)

            if buying_obj.buying_documents.get(doc_type):
                if is_document_fully_signed(buying_obj, doc_type):
                    st.success(f"✅ {doc_name}")
                else:
                    st.warning(f"⏳ {doc_name} - Needs signatures")
            else:
                st.error(f"❌ {doc_name} - Not uploaded")

    with col2:
        st.write("**Required Signatures:**")
        for doc_type in requirements["required_signatures"]:
            doc_config = ENHANCED_BUYING_DOCUMENT_TYPES.get(doc_type, {})
            doc_name = doc_config.get("name", doc_type)

            signing_status = get_document_signing_status(buying_obj, doc_type)
            if signing_status["fully_signed"]:
                st.success(f"✅ {doc_name}")
            else:
                missing = ", ".join(signing_status["missing_signers"])
                st.warning(f"⏳ {doc_name} - Waiting: {missing}")


def _render_signing_documents_section(buying_obj: Buying, user_id: str, user_type: str):
    """Render documents section with signing buttons"""
    st.subheader("📄 Documents & Signatures")

    # Group documents by phase
    phases_with_docs = {}
    for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
        phase = doc_config.get("phase", "unknown")
        if phase not in phases_with_docs:
            phases_with_docs[phase] = []
        phases_with_docs[phase].append((doc_type, doc_config))

    # Render each phase
    for phase_key in ENHANCED_WORKFLOW_PHASES.keys():
        if phase_key in phases_with_docs:
            phase_config = ENHANCED_WORKFLOW_PHASES[phase_key]

            with st.expander(f"{phase_config['name']}", expanded=(phase_key == buying_obj.current_phase)):
                for doc_type, doc_config in phases_with_docs[phase_key]:
                    _render_document_signing_card(buying_obj, doc_type, doc_config, user_id, user_type)


def _render_document_signing_card(buying_obj: Buying, doc_type: str, doc_config: Dict[str, Any],
                                 user_id: str, user_type: str):
    """Render individual document signing card"""
    doc_name = doc_config.get("name", doc_type)

    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.write(f"**{doc_name}**")

            # Document upload status
            if buying_obj.buying_documents.get(doc_type):
                st.success("📄 Uploaded")
            else:
                st.error("📄 Not uploaded")
                if user_type in doc_config.get("uploadable_by", []):
                    if st.button(f"📤 Upload", key=f"upload_{doc_type}"):
                        st.session_state[f"upload_doc_{doc_type}"] = True
                        st.rerun()

        with col2:
            # Validation status
            validation_status = buying_obj.document_validation_status.get(doc_type, {})
            if validation_status.get("validation_status", False):
                st.success("✅ Validated")
            elif buying_obj.buying_documents.get(doc_type):
                st.warning("⏳ Pending validation")
            else:
                st.info("⚪ Awaiting upload")

        with col3:
            # Signing status
            signing_status = get_document_signing_status(buying_obj, doc_type)
            if signing_status["fully_signed"]:
                st.success("✍️ Fully signed")
            elif signing_status["required_signers"]:
                missing = len(signing_status["missing_signers"])
                total = len(signing_status["required_signers"])
                st.warning(f"⏳ {total - missing}/{total} signed")
            else:
                st.info("📄 No signatures required")

        with col4:
            # Signing button
            _render_signing_button(buying_obj, doc_type, doc_config, user_id, user_type)

        # Show signature details
        if signing_status["signatures"]:
            st.write("**Signatures:**")
            for sig in signing_status["signatures"]:
                signer_type = sig.get("signer_type", "Unknown")
                timestamp = sig.get("timestamp", datetime.now())
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                st.caption(f"✍️ {signer_type.title()} - {timestamp.strftime('%Y-%m-%d %H:%M')}")

        st.divider()


def _render_signing_button(buying_obj: Buying, doc_type: str, doc_config: Dict[str, Any],
                          user_id: str, user_type: str):
    """Render signing button with appropriate state"""
    required_signers = doc_config.get("required_signers", [])

    if not required_signers:
        return  # No signatures required

    if user_type not in required_signers:
        st.write("🚫 Cannot sign")
        return

    # Check if user can sign
    can_sign, reason = can_user_sign_document(buying_obj, doc_type, user_id, user_type)

    if can_sign:
        # User can sign
        button_config = SIGNATURE_BUTTON_STYLES["ready_to_sign"]
        if st.button(
            f"{button_config['icon']} {button_config['text']}",
            key=f"sign_{doc_type}_{user_id}",
            type=button_config["style"]
        ):
            # Show signing confirmation modal
            _show_signing_confirmation_modal(buying_obj, doc_type, doc_config, user_id, user_type)

    elif "already signed" in reason.lower():
        # User already signed
        button_config = SIGNATURE_BUTTON_STYLES["already_signed"]
        st.button(
            f"{button_config['icon']} {button_config['text']}",
            key=f"signed_{doc_type}_{user_id}",
            disabled=True
        )

    elif "waiting" in reason.lower():
        # Waiting for others to sign first
        button_config = SIGNATURE_BUTTON_STYLES["waiting_for_others"]
        st.button(
            f"{button_config['icon']} {button_config['text']}",
            key=f"waiting_{doc_type}_{user_id}",
            disabled=True,
            help=reason
        )

    else:
        # Cannot sign for other reasons
        button_config = SIGNATURE_BUTTON_STYLES["cannot_sign"]
        st.button(
            f"{button_config['icon']} {button_config['text']}",
            key=f"cannot_{doc_type}_{user_id}",
            disabled=True,
            help=reason
        )


def _show_signing_confirmation_modal(buying_obj: Buying, doc_type: str, doc_config: Dict[str, Any],
                                   user_id: str, user_type: str):
    """Show signing confirmation modal"""
    doc_name = doc_config.get("name", doc_type)

    st.subheader(f"✍️ Sign Document: {doc_name}")

    # Document preview
    st.write("**Document Information:**")
    st.info(f"You are about to sign: **{doc_name}**")

    # Signing confirmation
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✍️ Confirm Signature", type="primary", key=f"confirm_sign_{doc_type}"):
            # Perform the signing
            success, message = sign_document(buying_obj, doc_type, user_id, user_type)

            if success:
                save_buying_transaction(buying_obj)
                st.success(f"✅ {message}")
                st.success(f"🎉 You have successfully signed: {doc_name}")

                # Check if this completed the phase
                if is_document_fully_signed(buying_obj, doc_type):
                    st.success(f"🎉 {doc_name} is now fully signed by all parties!")

                st.rerun()
            else:
                st.error(f"❌ Signature failed: {message}")

    with col2:
        if st.button("❌ Cancel", key=f"cancel_sign_{doc_type}"):
            st.rerun()


def _check_phase_progression(buying_obj: Buying):
    """Check and display phase progression status"""
    from gpp.classes.buying import check_and_advance_phase

    # Check if phase can advance
    if check_and_advance_phase(buying_obj):
        save_buying_transaction(buying_obj)

        # Show progression message
        current_phase = buying_obj.current_phase
        phase_config = ENHANCED_WORKFLOW_PHASES.get(current_phase, {})
        completion_message = phase_config.get("completion_message", f"Advanced to {current_phase}")

        st.success(f"🎉 {completion_message}")
        st.rerun()


def show_document_upload_modal(buying_obj: Buying, doc_type: str, current_user, user_type: str):
    """Show document upload modal for specific document type"""
    doc_config = ENHANCED_BUYING_DOCUMENT_TYPES.get(doc_type, {})
    doc_name = doc_config.get("name", doc_type)

    st.subheader(f"📤 Upload: {doc_name}")

    user_id = getattr(current_user, f'{user_type.lower()}_id')

    # Check if user can upload this document
    if user_type not in doc_config.get("uploadable_by", []):
        st.error(f"❌ You are not authorized to upload {doc_name}")
        return

    with st.form(f"upload_form_{doc_type}"):
        uploaded_file = st.file_uploader(
            f"Select {doc_name}",
            type=["pdf", "doc", "docx", "jpg", "jpeg", "png"],
            help=f"Upload {doc_name} document"
        )

        upload_notes = st.text_area(
            "Notes (Optional)",
            placeholder=f"Any additional information about this {doc_name}..."
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("📤 Upload Document", type="primary"):
                if uploaded_file:
                    try:
                        # Save file
                        from gpp.interface.utils.file_storage import save_uploaded_file
                        from gpp.classes.document import Document
                        from gpp.interface.utils.database import save_document
                        from gpp.classes.buying import add_document_to_buying, add_transaction_note

                        file_path = save_uploaded_file(uploaded_file, "buying_documents")

                        if file_path:
                            # Create document record
                            doc = Document(
                                document_name=f"{doc_name} - {uploaded_file.name}",
                                document_path=file_path,
                                upload_id=user_id,
                                validation_status=False,
                                visibility=True
                            )
                            save_document(doc)

                            # Add to buying transaction
                            add_document_to_buying(buying_obj, doc_type, doc.document_id)

                            # Add note about upload
                            add_transaction_note(
                                buying_obj,
                                f"Document uploaded: {doc_name}. {upload_notes}".strip(),
                                user_id,
                                "document_upload"
                            )

                            save_buying_transaction(buying_obj)

                            st.success(f"✅ {doc_name} uploaded successfully!")

                            # Clear session state
                            if f"upload_doc_{doc_type}" in st.session_state:
                                del st.session_state[f"upload_doc_{doc_type}"]
                            st.rerun()
                        else:
                            st.error("❌ Failed to save document")
                    except Exception as e:
                        st.error(f"❌ Error uploading document: {str(e)}")
                else:
                    st.error("❌ Please select a document to upload")

        with col2:
            if st.form_submit_button("❌ Cancel"):
                if f"upload_doc_{doc_type}" in st.session_state:
                    del st.session_state[f"upload_doc_{doc_type}"]
                st.rerun()


def show_phase_summary(buying_obj: Buying):
    """Show summary of all phases and their completion status"""
    st.subheader("📊 Complete Workflow Summary")

    for phase_key, phase_config in ENHANCED_WORKFLOW_PHASES.items():
        with st.expander(f"{phase_config['name']}", expanded=(phase_key == buying_obj.current_phase)):

            # Phase status
            if phase_key == buying_obj.current_phase:
                st.info("🔄 Current Phase")
            elif phase_config.get("order", 0) < ENHANCED_WORKFLOW_PHASES.get(buying_obj.current_phase, {}).get("order", 0):
                st.success("✅ Completed")
            else:
                st.write("⏳ Upcoming")

            # Required documents for this phase
            required_docs = phase_config.get("required_documents", [])
            if required_docs:
                st.write("**Required Documents:**")
                for doc_type in required_docs:
                    doc_config = ENHANCED_BUYING_DOCUMENT_TYPES.get(doc_type, {})
                    doc_name = doc_config.get("name", doc_type)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"📄 {doc_name}")

                    with col2:
                        if buying_obj.buying_documents.get(doc_type):
                            validation_status = buying_obj.document_validation_status.get(doc_type, {})
                            if validation_status.get("validation_status", False):
                                st.success("✅ Validated")
                            else:
                                st.warning("⏳ Pending")
                        else:
                            st.error("❌ Missing")

                    with col3:
                        if doc_config.get("required_signers"):
                            if is_document_fully_signed(buying_obj, doc_type):
                                st.success("✍️ Signed")
                            else:
                                st.warning("⏳ Unsigned")
                        else:
                            st.info("📄 No signature required")

            # Show completion message
            if phase_config.get("completion_message"):
                st.info(f"💬 {phase_config['completion_message']}")


# Integration functions for dashboards
def integrate_signing_with_buyer_dashboard(buying_obj: Buying, current_buyer):
    """Integration function for buyer dashboard"""
    st.markdown("---")
    st.subheader("✍️ Document Signing")

    # Show documents that buyer can sign
    buyer_signable_docs = []
    for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
        if "buyer" in doc_config.get("required_signers", []):
            if buying_obj.buying_documents.get(doc_type):
                can_sign, reason = can_user_sign_document(buying_obj, doc_type, current_buyer.buyer_id, "buyer")
                if can_sign or "already signed" in reason.lower():
                    buyer_signable_docs.append((doc_type, doc_config, can_sign, reason))

    if buyer_signable_docs:
        for doc_type, doc_config, can_sign, reason in buyer_signable_docs:
            _render_document_signing_card(buying_obj, doc_type, doc_config, current_buyer.buyer_id, "buyer")
    else:
        st.info("📋 No documents available for signing at this time.")


def integrate_signing_with_agent_dashboard(buying_obj: Buying, current_agent):
    """Integration function for agent dashboard"""
    st.markdown("---")
    st.subheader("✍️ Document Signing")

    # Show documents that agent can sign
    agent_signable_docs = []
    for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
        if "agent" in doc_config.get("required_signers", []):
            if buying_obj.buying_documents.get(doc_type):
                can_sign, reason = can_user_sign_document(buying_obj, doc_type, current_agent.agent_id, "agent")
                if can_sign or "already signed" in reason.lower():
                    agent_signable_docs.append((doc_type, doc_config, can_sign, reason))

    if agent_signable_docs:
        for doc_type, doc_config, can_sign, reason in agent_signable_docs:
            _render_document_signing_card(buying_obj, doc_type, doc_config, current_agent.agent_id, "agent")
    else:
        st.info("📋 No documents available for signing at this time.")


def integrate_signing_with_notary_dashboard(buying_obj: Buying, current_notary):
    """Integration function for notary dashboard"""
    st.markdown("---")
    st.subheader("✍️ Document Signing & Generation")

    # Show documents that notary can sign or generate
    notary_docs = []
    for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
        if ("notary" in doc_config.get("required_signers", []) or
            "notary" in doc_config.get("uploadable_by", [])):
            notary_docs.append((doc_type, doc_config))

    if notary_docs:
        for doc_type, doc_config in notary_docs:
            # Check if notary needs to generate this document
            if (doc_config.get("auto_generated") and
                doc_config.get("generated_by") == "notary" and
                not buying_obj.buying_documents.get(doc_type)):

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.warning(f"📄 {doc_config['name']} - Ready to generate")
                with col2:
                    if st.button(f"📝 Generate", key=f"generate_{doc_type}"):
                        _generate_notary_document(buying_obj, doc_type, current_notary)
            else:
                _render_document_signing_card(buying_obj, doc_type, doc_config, current_notary.notary_id, "notary")
    else:
        st.info("📋 No documents available for action at this time.")


def _generate_notary_document(buying_obj: Buying, doc_type: str, current_notary):
    """Generate a notary document (placeholder for actual document generation)"""
    doc_config = ENHANCED_BUYING_DOCUMENT_TYPES.get(doc_type, {})
    doc_name = doc_config.get("name", doc_type)

    st.subheader(f"📝 Generate: {doc_name}")

    # This is a placeholder - in a real system, you'd integrate with document generation services
    st.info("🔧 Document generation feature - would integrate with legal document templates")

    # For demo purposes, show a form to "generate" the document
    with st.form(f"generate_form_{doc_type}"):
        st.write(f"**Generating {doc_name}**")

        # Placeholder fields that would be used in document generation
        contract_terms = st.text_area(
            "Contract Terms",
            placeholder="Enter specific terms for this contract...",
            height=150
        )

        special_conditions = st.text_area(
            "Special Conditions",
            placeholder="Any special conditions or clauses..."
        )

        if st.form_submit_button("📝 Generate Document", type="primary"):
            # In a real system, this would:
            # 1. Use a document template
            # 2. Fill in property and transaction details
            # 3. Generate a PDF
            # 4. Save it to the system

            # For now, create a placeholder document
            from gpp.classes.document import Document
            from gpp.interface.utils.database import save_document
            from gpp.classes.buying import add_document_to_buying, add_transaction_note

            # Create placeholder document
            doc = Document(
                document_name=f"Generated {doc_name} - {datetime.now().strftime('%Y%m%d_%H%M')}",
                document_path=f"placeholder_path_{doc_type}_{buying_obj.buying_id}",
                upload_id=current_notary.notary_id,
                validation_status=True,  # Auto-validated since notary generated it
                visibility=True
            )
            save_document(doc)

            # Add to buying transaction
            add_document_to_buying(buying_obj, doc_type, doc.document_id)

            # Add note
            add_transaction_note(
                buying_obj,
                f"Document generated by notary: {doc_name}",
                current_notary.notary_id,
                "document_upload"
            )

            save_buying_transaction(buying_obj)
            st.success(f"✅ {doc_name} generated successfully!")
            st.rerun()