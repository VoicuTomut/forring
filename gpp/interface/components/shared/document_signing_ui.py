"""
Enhanced Document Signing UI Components
Complete signing interface with download buttons for notaries and simple upload system
FIXED: Simple direct signing without confirmation modal
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List, Optional

from gpp.classes.buying import (
    Buying, can_user_sign_document, sign_document, get_document_signing_status,
    is_document_fully_signed, get_current_phase_requirements, validate_buying_document
)
from gpp.interface.config.constants import (
    ENHANCED_BUYING_DOCUMENT_TYPES, ENHANCED_WORKFLOW_PHASES,
    SIGNATURE_BUTTON_STYLES, PHASE_PROGRESSION_MESSAGES
)
from gpp.interface.utils.buying_database import save_buying_transaction
from gpp.interface.utils.database import get_documents
from gpp.interface.utils.file_storage import file_exists, read_file_content, get_file_info


def show_signing_workflow_dashboard(buying_obj: Buying, current_user, user_type: str):
    """Main signing workflow dashboard with enhanced notary features"""
    st.title("✍️ Document Signing Workflow")

    user_id = getattr(current_user, f'{user_type.lower()}_id')

    # Phase overview
    _render_workflow_progress(buying_obj)

    # Current phase requirements
    _render_current_phase_requirements(buying_obj)

    # Documents section with enhanced notary features
    _render_enhanced_documents_section(buying_obj, user_id, user_type)

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
    st.subheader(
        f"📋 Current Phase: {ENHANCED_WORKFLOW_PHASES.get(buying_obj.current_phase, {}).get('name', buying_obj.current_phase)}")

    requirements = get_current_phase_requirements(buying_obj)

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Required Documents:**")
        for doc_type in requirements["required_documents"]:
            doc_config = ENHANCED_BUYING_DOCUMENT_TYPES.get(doc_type, {})
            doc_name = doc_config.get("name", doc_type)

            if buying_obj.buying_documents.get(doc_type):
                validation_status = buying_obj.document_validation_status.get(doc_type, {})
                if validation_status.get("validation_status", False):
                    if is_document_fully_signed(buying_obj, doc_type):
                        st.success(f"✅ {doc_name}")
                    else:
                        st.warning(f"⏳ {doc_name} - Needs signatures")
                else:
                    st.info(f"🔍 {doc_name} - Needs validation")
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


def _render_enhanced_documents_section(buying_obj: Buying, user_id: str, user_type: str):
    """Enhanced documents section with notary download capabilities"""
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
                    _render_enhanced_document_card(buying_obj, doc_type, doc_config, user_id, user_type)


def _render_enhanced_document_card(buying_obj: Buying, doc_type: str, doc_config: Dict[str, Any],
                                   user_id: str, user_type: str):
    """Enhanced document card with download buttons for notaries"""
    doc_name = doc_config.get("name", doc_type)

    with st.container():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            st.write(f"**{doc_name}**")

            # Document upload status
            if buying_obj.buying_documents.get(doc_type):
                st.success("📄 Uploaded")

                # Show document info for notaries
                if user_type == "notary":
                    doc_id = buying_obj.buying_documents.get(doc_type)
                    documents = get_documents()
                    if doc_id and doc_id in documents:
                        doc_data = documents[doc_id]
                        st.caption(f"📁 {doc_data.document_name}")
                        if file_exists(doc_data.document_path):
                            file_info = get_file_info(doc_data.document_path)
                            st.caption(f"📊 {file_info['size_mb']} MB")
            else:
                st.error("📄 Not uploaded")
                # Show upload button for authorized users
                if user_type in doc_config.get("uploadable_by", []):
                    if st.button(f"📤 Upload", key=f"upload_{doc_type}"):
                        st.session_state[f"upload_doc_{doc_type}"] = True
                        st.rerun()

        with col2:
            # Enhanced validation status with notary validation button
            validation_status = buying_obj.document_validation_status.get(doc_type, {})
            if validation_status.get("validation_status", False):
                st.success("✅ Validated")
                if validation_status.get("validation_date"):
                    st.caption(f"🕒 {validation_status['validation_date'].strftime('%m-%d')}")
            elif buying_obj.buying_documents.get(doc_type):
                if user_type == "notary":
                    # Notary can validate documents
                    if st.button("✅ Validate", key=f"validate_{doc_type}", type="primary"):
                        validate_buying_document(buying_obj, doc_type, user_id, True, "Document validated by notary")
                        save_buying_transaction(buying_obj)
                        st.success("✅ Document validated!")
                        st.rerun()
                else:
                    st.warning("⏳ Pending validation")
            else:
                st.info("⚪ Awaiting upload")

        with col3:
            # Enhanced signing status
            signing_status = get_document_signing_status(buying_obj, doc_type)
            if signing_status["fully_signed"]:
                st.success("✍️ Fully signed")
            elif signing_status["required_signers"]:
                missing = len(signing_status["missing_signers"])
                total = len(signing_status["required_signers"])
                st.warning(f"⏳ {total - missing}/{total} signed")

                # Show who has signed
                if signing_status["signatures"]:
                    signed_types = [sig.get("signer_type", "Unknown") for sig in signing_status["signatures"]]
                    st.caption(f"✍️ {', '.join(signed_types)}")
            else:
                st.info("📄 No signatures required")

        with col4:
            # Enhanced action buttons with download for ALL users
            if buying_obj.buying_documents.get(doc_type):
                doc_id = buying_obj.buying_documents.get(doc_type)
                documents = get_documents()
                if doc_id and doc_id in documents:
                    doc_data = documents[doc_id]

                    # Show download button for everyone
                    _render_universal_download_button(doc_data, doc_type, user_type)

                    # Show signing button if applicable
                    required_signers = doc_config.get("required_signers", [])
                    if required_signers and user_type in required_signers:
                        _render_simple_signing_button(buying_obj, doc_type, doc_config, user_id, user_type)
            else:
                # No document uploaded yet, just show signing button if applicable
                required_signers = doc_config.get("required_signers", [])
                if required_signers and user_type in required_signers:
                    st.info("📄 Upload first")
                elif user_type in doc_config.get("uploadable_by", []):
                    st.info("📤 Can upload")

        st.divider()


def _render_enhanced_action_buttons(buying_obj: Buying, doc_type: str, doc_config: Dict[str, Any],
                                    user_id: str, user_type: str):
    """Enhanced action buttons with download capability for ALL users"""

    # Download button for ALL users (not just notaries)
    if buying_obj.buying_documents.get(doc_type):
        doc_id = buying_obj.buying_documents.get(doc_type)
        documents = get_documents()
        if doc_id and doc_id in documents:
            doc_data = documents[doc_id]
            # Show download button for everyone
            col1, col2 = st.columns(2)
            with col1:
                if _render_universal_download_button(doc_data, doc_type, user_type):
                    pass  # Download handled in function
            with col2:
                # FIXED: Simple direct signing button
                required_signers = doc_config.get("required_signers", [])
                if required_signers and user_type in required_signers:
                    _render_simple_signing_button(buying_obj, doc_type, doc_config, user_id, user_type)
    else:
        # No document to download, just show signing button if applicable
        required_signers = doc_config.get("required_signers", [])
        if required_signers and user_type in required_signers:
            _render_simple_signing_button(buying_obj, doc_type, doc_config, user_id, user_type)


def _render_universal_download_button(doc_data, doc_type: str, user_type: str):
    """Render download button for ALL users (not just notaries) - FIXED DUPLICATE KEY"""
    import time  # Add this import

    if not file_exists(doc_data.document_path):
        st.button("📥 Download", disabled=True, help="File not available",
                  key=f"dl_{doc_type}_{doc_data.document_id}_{user_type}_disabled_{int(time.time() * 1000)}")
        return False

    # Read file content
    file_content = read_file_content(doc_data.document_path)
    if not file_content:
        st.button("📥 Download", disabled=True, help="Cannot read file",
                  key=f"dl_{doc_type}_{doc_data.document_id}_{user_type}_error_{int(time.time() * 1000)}")
        return False

    # Get safe filename and MIME type
    safe_filename = _get_safe_filename(doc_data.document_name, doc_data.document_path)
    mime_type = _get_mime_type(doc_data.document_path)

    # Create download button for all users - FIXED WITH TIMESTAMP
    st.download_button(
        label="📥 Download",
        data=file_content,
        file_name=safe_filename,
        mime=mime_type,
        key=f"dl_{doc_type}_{doc_data.document_id}_{user_type}_{int(time.time() * 1000)}",
        help=f"Download {safe_filename}"
    )
    return True


def _render_simple_signing_button(buying_obj: Buying, doc_type: str, doc_config: Dict[str, Any],
                                  user_id: str, user_type: str):
    """FIXED: Simple direct signing button - no modal, just sign directly"""
    required_signers = doc_config.get("required_signers", [])

    if not required_signers or user_type not in required_signers:
        return

    # Check if user can sign
    can_sign, reason = can_user_sign_document(buying_obj, doc_type, user_id, user_type)

    if can_sign:
        # User can sign - DIRECT SIGNING
        button_config = SIGNATURE_BUTTON_STYLES["ready_to_sign"]
        if st.button(
                f"{button_config['icon']} Sign",
                key=f"sign_{doc_type}_{user_id}",
                type=button_config["style"]
        ):
            # DIRECT SIGNING - No modal confirmation
            doc_name = doc_config.get("name", doc_type)

            with st.spinner(f"Signing {doc_name}..."):
                success, message = sign_document(buying_obj, doc_type, user_id, user_type)

                if success:
                    save_buying_transaction(buying_obj)
                    st.success(f"✅ {message}")
                    st.success(f"🎉 You have successfully signed: {doc_name}")

                    # Check if this completed the phase
                    if is_document_fully_signed(buying_obj, doc_type):
                        st.success(f"🎉 {doc_name} is now fully signed by all parties!")

                    # Auto-refresh to show updated status
                    st.rerun()
                else:
                    st.error(f"❌ Signature failed: {message}")

    elif "already signed" in reason.lower():
        # User already signed
        button_config = SIGNATURE_BUTTON_STYLES["already_signed"]
        st.button(
            f"{button_config['icon']} Signed",
            key=f"signed_{doc_type}_{user_id}",
            disabled=True
        )

    elif "not validated" in reason.lower():
        # Document not validated yet
        st.button(
            "⏳ Validation",
            key=f"wait_validation_{doc_type}_{user_id}",
            disabled=True,
            help="Waiting for document validation"
        )

    else:
        # Cannot sign for other reasons
        button_config = SIGNATURE_BUTTON_STYLES["cannot_sign"]
        st.button(
            f"{button_config['icon']} Wait",
            key=f"cannot_{doc_type}_{user_id}",
            disabled=True,
            help=reason
        )


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
    """Enhanced document upload modal with simplified interface"""
    doc_config = ENHANCED_BUYING_DOCUMENT_TYPES.get(doc_type, {})
    doc_name = doc_config.get("name", doc_type)

    st.subheader(f"📤 Upload: {doc_name}")

    user_id = getattr(current_user, f'{user_type.lower()}_id')

    # Check if user can upload this document
    if user_type not in doc_config.get("uploadable_by", []):
        st.error(f"❌ You are not authorized to upload {doc_name}")
        return

    # Show document description
    if doc_config.get("description"):
        st.info(doc_config["description"])

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


# Integration functions for dashboards (updated with download buttons for all users)
def integrate_signing_with_buyer_dashboard(buying_obj: Buying, current_buyer):
    """Integration function for buyer dashboard with download capability"""
    st.markdown("---")
    st.subheader("✍️ Your Action Items")

    # Show documents that buyer can sign or upload
    buyer_actions = []

    for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
        # Check if buyer can upload
        if "buyer" in doc_config.get("uploadable_by", []):
            if not buying_obj.buying_documents.get(doc_type):
                buyer_actions.append({
                    "type": "upload",
                    "doc_type": doc_type,
                    "doc_name": doc_config.get("name", doc_type),
                    "action": f"📤 Upload {doc_config.get('name', doc_type)}"
                })

        # Check if buyer can sign
        if "buyer" in doc_config.get("required_signers", []):
            if buying_obj.buying_documents.get(doc_type):
                can_sign, reason = can_user_sign_document(buying_obj, doc_type, current_buyer.buyer_id, "buyer")
                if can_sign:
                    buyer_actions.append({
                        "type": "sign",
                        "doc_type": doc_type,
                        "doc_name": doc_config.get("name", doc_type),
                        "action": f"✍️ Sign {doc_config.get('name', doc_type)}"
                    })

        # Add download option for uploaded documents
        if buying_obj.buying_documents.get(doc_type):
            buyer_actions.append({
                "type": "download",
                "doc_type": doc_type,
                "doc_name": doc_config.get("name", doc_type),
                "action": f"📥 Download {doc_config.get('name', doc_type)}"
            })

    if buyer_actions:
        for action in buyer_actions:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{action['action']}**")
            with col2:
                if action["type"] == "upload":
                    if st.button(f"📤 Upload", key=f"buyer_action_{action['doc_type']}"):
                        st.session_state[f"upload_doc_{action['doc_type']}"] = True
                        st.rerun()
                elif action["type"] == "sign":
                    # FIXED: Direct signing for buyer dashboard
                    if st.button(f"✍️ Sign", key=f"buyer_action_{action['doc_type']}"):
                        with st.spinner(f"Signing {action['doc_name']}..."):
                            success, message = sign_document(buying_obj, action['doc_type'], current_buyer.buyer_id,
                                                             "buyer")

                            if success:
                                save_buying_transaction(buying_obj)
                                st.success(f"✅ {message}")
                                st.success(f"🎉 You have successfully signed: {action['doc_name']}")

                                # Check if this completed the phase
                                if is_document_fully_signed(buying_obj, action['doc_type']):
                                    st.success(f"🎉 {action['doc_name']} is now fully signed by all parties!")

                                st.rerun()
                            else:
                                st.error(f"❌ Signature failed: {message}")
                elif action["type"] == "download":
                    # Add download functionality to buyer dashboard
                    doc_id = buying_obj.buying_documents.get(action['doc_type'])
                    if doc_id:
                        documents = get_documents()
                        if doc_id in documents:
                            doc_data = documents[doc_id]
                            _render_universal_download_button(doc_data, action['doc_type'], "buyer")
    else:
        st.info("📋 No immediate actions required. Check back later for updates!")


def integrate_signing_with_agent_dashboard(buying_obj: Buying, current_agent):
    """Integration function for agent dashboard with download capability"""
    st.markdown("---")
    st.subheader("✍️ Agent Actions")

    # Show documents that agent can work with
    agent_actions = []

    for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
        # Check if agent can sign
        if "agent" in doc_config.get("required_signers", []):
            if buying_obj.buying_documents.get(doc_type):
                can_sign, reason = can_user_sign_document(buying_obj, doc_type, current_agent.agent_id, "agent")
                if can_sign:
                    agent_actions.append({
                        "type": "sign",
                        "doc_type": doc_type,
                        "doc_name": doc_config.get("name", doc_type),
                        "action": f"✍️ Sign {doc_config.get('name', doc_type)}"
                    })
                elif "already signed" in reason.lower():
                    agent_actions.append({
                        "type": "signed",
                        "doc_type": doc_type,
                        "doc_name": doc_config.get("name", doc_type),
                        "action": f"✅ Signed {doc_config.get('name', doc_type)}"
                    })

        # Add download option for uploaded documents
        if buying_obj.buying_documents.get(doc_type):
            agent_actions.append({
                "type": "download",
                "doc_type": doc_type,
                "doc_name": doc_config.get("name", doc_type),
                "action": f"📥 Download {doc_config.get('name', doc_type)}"
            })

    if agent_actions:
        for action in agent_actions:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{action['action']}**")
            with col2:
                if action["type"] == "sign":
                    if st.button(f"✍️ Sign", key=f"agent_action_{action['doc_type']}"):
                        with st.spinner(f"Signing {action['doc_name']}..."):
                            success, message = sign_document(buying_obj, action['doc_type'], current_agent.agent_id,
                                                             "agent")

                            if success:
                                save_buying_transaction(buying_obj)
                                st.success(f"✅ {message}")
                                st.success(f"🎉 You have successfully signed: {action['doc_name']}")

                                if is_document_fully_signed(buying_obj, action['doc_type']):
                                    st.success(f"🎉 {action['doc_name']} is now fully signed by all parties!")

                                st.rerun()
                            else:
                                st.error(f"❌ Signature failed: {message}")
                elif action["type"] == "signed":
                    st.success("✅ Signed")
                elif action["type"] == "download":
                    # Add download functionality to agent dashboard
                    doc_id = buying_obj.buying_documents.get(action['doc_type'])
                    if doc_id:
                        documents = get_documents()
                        if doc_id in documents:
                            doc_data = documents[doc_id]
                            _render_universal_download_button(doc_data, action['doc_type'], "agent")
    else:
        st.info("📋 No documents available for action at this time.")


def integrate_signing_with_notary_dashboard(buying_obj: Buying, current_notary):
    """Enhanced integration function for notary dashboard with download capability"""
    st.markdown("---")
    st.subheader("✍️ Notary Actions")

    # Show documents that notary can work with
    notary_actions = []

    for doc_type, doc_config in ENHANCED_BUYING_DOCUMENT_TYPES.items():
        # Check if notary needs to upload this document
        if ("notary" in doc_config.get("uploadable_by", []) and
                not buying_obj.buying_documents.get(doc_type)):
            notary_actions.append({
                "type": "upload",
                "doc_type": doc_type,
                "doc_name": doc_config.get("name", doc_type),
                "action": f"📤 Upload {doc_config.get('name', doc_type)}"
            })

        # Check if notary can validate
        if ("notary" in doc_config.get("validatable_by", []) and
                buying_obj.buying_documents.get(doc_type)):
            validation_status = buying_obj.document_validation_status.get(doc_type, {})
            if not validation_status.get("validation_status", False):
                notary_actions.append({
                    "type": "validate",
                    "doc_type": doc_type,
                    "doc_name": doc_config.get("name", doc_type),
                    "action": f"✅ Validate {doc_config.get('name', doc_type)}"
                })

        # Check if notary can sign
        if "notary" in doc_config.get("required_signers", []):
            if buying_obj.buying_documents.get(doc_type):
                can_sign, reason = can_user_sign_document(buying_obj, doc_type, current_notary.notary_id, "notary")
                if can_sign:
                    notary_actions.append({
                        "type": "sign",
                        "doc_type": doc_type,
                        "doc_name": doc_config.get("name", doc_type),
                        "action": f"✍️ Sign {doc_config.get('name', doc_type)}"
                    })

        # Add download option for uploaded documents
        if buying_obj.buying_documents.get(doc_type):
            notary_actions.append({
                "type": "download",
                "doc_type": doc_type,
                "doc_name": doc_config.get("name", doc_type),
                "action": f"📥 Download {doc_config.get('name', doc_type)}"
            })

    if notary_actions:
        for action in notary_actions:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{action['action']}**")
            with col2:
                if action["type"] == "upload":
                    if st.button(f"📤 Upload", key=f"notary_upload_{action['doc_type']}"):
                        st.session_state[f"upload_doc_{action['doc_type']}"] = True
                        st.rerun()
                elif action["type"] == "validate":
                    if st.button(f"✅ Validate", key=f"notary_validate_{action['doc_type']}"):
                        validate_buying_document(buying_obj, action['doc_type'], current_notary.notary_id, True,
                                                 "Document validated by notary")
                        save_buying_transaction(buying_obj)
                        st.success("✅ Document validated!")
                        st.rerun()
                elif action["type"] == "sign":
                    if st.button(f"✍️ Sign", key=f"notary_sign_{action['doc_type']}"):
                        with st.spinner(f"Signing {action['doc_name']}..."):
                            success, message = sign_document(buying_obj, action['doc_type'], current_notary.notary_id,
                                                             "notary")

                            if success:
                                save_buying_transaction(buying_obj)
                                st.success(f"✅ {message}")
                                st.success(f"🎉 You have successfully signed: {action['doc_name']}")

                                if is_document_fully_signed(buying_obj, action['doc_type']):
                                    st.success(f"🎉 {action['doc_name']} is now fully signed by all parties!")

                                st.rerun()
                            else:
                                st.error(f"❌ Signature failed: {message}")
                elif action["type"] == "download":
                    # Add download functionality to notary dashboard
                    doc_id = buying_obj.buying_documents.get(action['doc_type'])
                    if doc_id:
                        documents = get_documents()
                        if doc_id in documents:
                            doc_data = documents[doc_id]
                            _render_universal_download_button(doc_data, action['doc_type'], "notary")
    else:
        st.info("📋 No documents available for action at this time.")

# REMOVED: The old modal confirmation function since we're doing direct signing now
# _show_signing_confirmation_modal function has been removed as it's no longer needed