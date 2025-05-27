"""
Notary validation queue interface with working document download and image viewer
"""

import streamlit as st
from datetime import datetime
import os
import base64
from PIL import Image

from gpp.classes.notary import Notary, add_work_to_notary
from gpp.classes.property import Property, assign_notary_to_property, get_property_additional_docs_count
from gpp.classes.document import validate_document as validate_doc_helper
from gpp.interface.utils.database import get_documents, save_document, save_property, load_data, save_data
from gpp.interface.utils.property_helpers import get_pending_validation_properties, get_property_validation_progress, get_property_photos, format_timestamp
from gpp.interface.utils.file_storage import file_exists, read_file_content, get_file_info
from gpp.interface.config.constants import MANDATORY_DOCS, ADDITIONAL_DOC_CATEGORIES, MAX_RECENT_NOTES, NOTARIES_FILE


def show_validation_queue(current_notary: Notary):
    """Show properties awaiting validation"""
    st.subheader("Properties Awaiting Validation")

    pending_properties = get_pending_validation_properties()

    if not pending_properties:
        st.info("No properties in validation queue.")
        return

    # Display properties in card grid
    _display_pending_properties(pending_properties)

    # Show document review interface if property selected
    if 'selected_property' in st.session_state:
        _show_document_review(st.session_state['selected_property'], current_notary)


def _display_pending_properties(pending_properties):
    """Display pending properties in grid format"""
    cols = st.columns(3)

    for i, (prop_id, prop_data) in enumerate(pending_properties.items()):
        with cols[i % 3]:
            _render_pending_property_card(prop_id, prop_data)


def _render_pending_property_card(prop_id: str, prop_data: Property):
    """Render individual pending property card"""
    with st.container():
        st.write(f"**{prop_data.title}**")
        st.write(f"€{prop_data.price:,.2f}")
        st.write(f"📍 {prop_data.city}")

        # Show property photos if available
        photo_docs = get_property_photos(prop_data)
        if photo_docs:
            st.write(f"📸 {len(photo_docs)} photos")

        # Validation progress
        progress = get_property_validation_progress(prop_id)
        st.write(f"**Progress: {progress['validated']}/{progress['total']}**")
        st.progress(progress['progress'])

        # Show additional documents count
        additional_count = sum(get_property_additional_docs_count(prop_data).values())
        if additional_count > 0:
            st.write(f"📎 {additional_count} additional docs")

        if st.button("🔍 Review Documents", key=f"review_{prop_id}"):
            st.session_state['selected_property'] = prop_id


def _show_document_review(property_id: str, current_notary: Notary):
    """Show detailed document review interface"""
    from gpp.interface.utils.database import get_properties

    st.divider()
    st.subheader("📄 Document Review")

    properties = get_properties()
    documents = get_documents()

    if property_id not in properties:
        st.error("Property not found")
        return

    prop_data = properties[property_id]

    # Property overview
    _render_property_overview(prop_data)

    # Agent notes and additional documents
    _render_additional_info(prop_data, documents)

    # Mandatory document review
    _render_mandatory_doc_review(prop_data, documents, current_notary)

    # Final approval
    _render_approval_section(property_id, prop_data, current_notary)


def _render_property_overview(prop_data: Property):
    """Render property overview section"""
    st.write(f"**Property:** {prop_data.title}")
    st.write(f"**Price:** €{prop_data.price:,.2f}")
    st.write(f"**Description:** {prop_data.description}")

    # Show property photos with actual images
    photo_docs = get_property_photos(prop_data)
    if photo_docs:
        st.subheader("📸 Property Photos")
        cols = st.columns(min(len(photo_docs), 4))
        for i, photo_doc in enumerate(photo_docs[:4]):
            with cols[i]:
                st.write(f"Photo {i + 1}")
                # Try to display actual image
                if file_exists(photo_doc.document_path):
                    try:
                        image = Image.open(photo_doc.document_path)
                        st.image(image, caption=f"Photo {i + 1}", use_column_width=True)
                    except Exception as e:
                        st.info(f"📷 Image file: {os.path.basename(photo_doc.document_path)}")
                else:
                    st.info(f"📷 Path: {photo_doc.document_path}")
        if len(photo_docs) > 4:
            st.write(f"... and {len(photo_docs) - 4} more photos")

    # Progress bar
    progress = get_property_validation_progress(prop_data.property_id)
    st.write(f"**Documents Validated: {progress['validated']}/{progress['total']}**")
    st.progress(progress['progress'])


def _render_additional_info(prop_data: Property, documents):
    """Render agent notes and additional documents"""
    # Show agent notes if any
    if prop_data.agent_notes:
        with st.expander(f"📝 Agent Notes ({len(prop_data.agent_notes)})"):
            for note in reversed(prop_data.agent_notes[-MAX_RECENT_NOTES:]):  # Show last 5 notes
                st.write(f"**{format_timestamp(note['timestamp'])}** - {note['context'].replace('_', ' ').title()}")
                st.write(f"💬 {note['note']}")
                st.write("---")

    # Show additional documents
    additional_counts = get_property_additional_docs_count(prop_data)
    if any(count > 0 for count in additional_counts.values()):
        with st.expander("📎 Additional Documents"):
            for category, doc_ids in prop_data.additional_docs.items():
                if doc_ids:
                    st.write(f"**{ADDITIONAL_DOC_CATEGORIES[category]}** ({len(doc_ids)} documents)")
                    for doc_id in doc_ids:
                        if doc_id in documents:
                            doc = documents[doc_id]
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"• {doc.document_name}")
                            with col2:
                                if st.button("👁️", key=f"view_add_{doc_id}"):
                                    _show_document_viewer(doc)


def _render_mandatory_doc_review(prop_data: Property, documents, current_notary: Notary):
    """Render mandatory document review section"""
    st.divider()
    st.subheader("📋 Mandatory Document Review")

    for doc_key, doc_id in prop_data.mandatory_legal_docs.items():
        if doc_id and doc_id in documents:
            _render_document_validation_row(doc_key, doc_id, documents[doc_id], current_notary)


def _render_document_validation_row(doc_key: str, doc_id: str, doc_data, current_notary: Notary):
    """Render individual document validation row"""
    with st.container():
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Get document name with fallback
            try:
                doc_name = MANDATORY_DOCS[doc_key]
            except KeyError:
                doc_name = doc_key.replace('_', ' ').title()
                st.error(f"Document type '{doc_key}' not found in MANDATORY_DOCS")

            if doc_data.validation_status:
                st.write(f"✅ **{doc_name}** - Validated")
                if doc_data.validation_date:
                    st.write(f"   📅 {format_timestamp(doc_data.validation_date)}")
            else:
                st.write(f"📄 **{doc_name}** - Pending")
                # Show if this is a replacement
                if "Replacement" in doc_data.document_name:
                    st.warning("🔄 Replacement Document - Needs Re-validation")

        with col2:
            if st.button("👁️ View", key=f"view_{doc_id}"):
                _show_document_viewer(doc_data)

        with col3:
            if not doc_data.validation_status:
                col_validate, col_reject = st.columns(2)
                with col_validate:
                    if st.button("✅", key=f"validate_{doc_id}"):
                        validated_doc = validate_doc_helper(doc_data, current_notary.notary_id)
                        save_document(validated_doc)
                        st.rerun()
                with col_reject:
                    if st.button("❌", key=f"reject_{doc_id}"):
                        doc_data.validation_status = False
                        doc_data.validation_date = datetime.now()
                        doc_data.who_validate = current_notary.notary_id
                        save_document(doc_data)
                        st.rerun()

    st.divider()


def _show_document_viewer(doc_data):
    """Show enhanced document viewer with real image display and working download"""
    st.markdown("---")
    st.markdown("### 📄 Document Viewer")

    with st.container():
        # Document information header
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.write(f"**📄 {doc_data.document_name}**")
            st.caption(f"Document ID: {doc_data.document_id[:8]}...")

        with col2:
            # WORKING DOWNLOAD BUTTON
            if _render_download_button(doc_data):
                pass  # Download handled in the function

        with col3:
            # Full screen button
            if st.button("🔍 Full View", key=f"fullscreen_{doc_data.document_id}"):
                st.session_state[f'fullscreen_{doc_data.document_id}'] = True
                st.rerun()

    # Document details
    col1, col2 = st.columns([1, 1])

    with col1:
        st.write("**📋 Document Information**")
        st.write(f"• **File Path:** `{doc_data.document_path}`")

        # Show file info
        if file_exists(doc_data.document_path):
            file_info = get_file_info(doc_data.document_path)
            st.success(f"• **File Status:** ✅ Available ({file_info['size_mb']} MB)")
            st.write(f"• **File Type:** {file_info.get('extension', 'unknown').upper()}")
        else:
            st.error("• **File Status:** ❌ File not found")

        # Format upload date properly
        upload_date_str = format_timestamp(doc_data.upload_date) if doc_data.upload_date else "Unknown"
        st.write(f"• **Uploaded:** {upload_date_str}")

        # Show uploader info
        if doc_data.upload_id:
            st.write(f"• **Uploaded by:** {doc_data.upload_id[:8]}...")

        # Show validation status
        if doc_data.validation_status:
            st.success("✅ **Status:** Validated")
            if doc_data.validation_date:
                validation_date_str = format_timestamp(doc_data.validation_date)
                st.write(f"• **Validated on:** {validation_date_str}")
            if doc_data.who_validate:
                st.write(f"• **Validated by:** {doc_data.who_validate[:8]}...")
        else:
            st.warning("⏳ **Status:** Pending Validation")

    with col2:
        st.write("**👁️ Document Preview**")
        _render_actual_document_preview(doc_data)

    # Full screen view
    if st.session_state.get(f'fullscreen_{doc_data.document_id}', False):
        _render_fullscreen_viewer(doc_data)

    st.markdown("---")


def _render_download_button(doc_data):
    """Render working download button"""
    if not file_exists(doc_data.document_path):
        st.button("📥 Download", disabled=True, help="File not available")
        return False

    # Read file content
    file_content = read_file_content(doc_data.document_path)
    if not file_content:
        st.button("📥 Download", disabled=True, help="Cannot read file")
        return False

    # Get safe filename and MIME type
    safe_filename = _get_safe_filename(doc_data.document_name, doc_data.document_path)
    mime_type = _get_mime_type(doc_data.document_path)

    # Create download button
    st.download_button(
        label="📥 Download",
        data=file_content,
        file_name=safe_filename,
        mime=mime_type,
        key=f"download_{doc_data.document_id}"
    )
    return True


def _render_actual_document_preview(doc_data):
    """Render actual document preview with real content"""
    if not file_exists(doc_data.document_path):
        st.error("📄 **File Not Found**")
        st.write("File is not available in storage")
        return

    file_path = doc_data.document_path.lower()

    # IMAGE FILES - Show actual images
    if file_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
        try:
            # Open and display the actual image
            image = Image.open(doc_data.document_path)
            st.success("📷 **Image Document**")
            st.image(image, caption=doc_data.document_name, use_column_width=True)

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
        file_info = get_file_info(doc_data.document_path)
        st.write("📄 PDF file ready for download")
        st.write(f"• **Size:** {file_info['size_mb']} MB")
        st.write("• Click Download to view in PDF reader")
        st.write("• Full View for embedded viewer")

    # TEXT FILES - Show content preview
    elif file_path.endswith(('.txt', '.md', '.py', '.js', '.html', '.css')):
        try:
            with open(doc_data.document_path, 'r', encoding='utf-8') as f:
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
        file_info = get_file_info(doc_data.document_path)
        st.write("📝 Microsoft Word document")
        st.write(f"• **Size:** {file_info['size_mb']} MB")
        st.write("• Download to open in Word")

    elif file_path.endswith(('.xls', '.xlsx')):
        st.info("📊 **Excel Document**")
        file_info = get_file_info(doc_data.document_path)
        st.write("📊 Microsoft Excel spreadsheet")
        st.write(f"• **Size:** {file_info['size_mb']} MB")
        st.write("• Download to open in Excel")

    # GENERIC FILES
    else:
        st.info("📄 **Document File**")
        file_info = get_file_info(doc_data.document_path)
        extension = file_info.get('extension', '').upper()
        st.write(f"📄 {extension} file" if extension else "📄 Binary file")
        st.write(f"• **Size:** {file_info['size_mb']} MB")
        st.write("• Download to view in appropriate application")


def _render_fullscreen_viewer(doc_data):
    """Render full screen document viewer with actual content"""
    st.markdown("---")
    st.markdown("### 🔍 Full Screen Document Viewer")

    # Header with controls
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    with col1:
        st.write(f"**📄 {doc_data.document_name}**")

    with col2:
        # Download button in fullscreen
        _render_download_button(doc_data)

    with col3:
        if st.button("🖨️ Print", key=f"fs_print_{doc_data.document_id}"):
            st.info("🖨️ Print: Right-click on image/document and select Print")

    with col4:
        if st.button("✖️ Close", key=f"close_{doc_data.document_id}"):
            st.session_state[f'fullscreen_{doc_data.document_id}'] = False
            st.rerun()

    # Full document content
    st.markdown("---")

    if not file_exists(doc_data.document_path):
        st.error("📄 **File Not Available**")
        st.write("The file is not available in storage.")
        return

    file_path = doc_data.document_path.lower()

    # FULL SCREEN IMAGE VIEWER
    if file_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
        try:
            image = Image.open(doc_data.document_path)
            st.markdown("### 📷 Full Screen Image Viewer")

            # Zoom controls
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                zoom_level = st.select_slider(
                    "🔍 Zoom Level",
                    options=[25, 50, 75, 100, 125, 150, 200],
                    value=100,
                    key=f"zoom_{doc_data.document_id}"
                )

            # Calculate display width
            max_width = min(800, int(image.size[0] * zoom_level / 100))

            # Display image
            st.image(
                image,
                caption=f"{doc_data.document_name} ({zoom_level}%)",
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
            with open(doc_data.document_path, "rb") as f:
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
            with open(doc_data.document_path, 'r', encoding='utf-8') as f:
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
        file_info = get_file_info(doc_data.document_path)

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


def _render_approval_section(property_id: str, prop_data: Property, current_notary: Notary):
    """Render final approval section"""
    # Check if all documents are validated
    progress = get_property_validation_progress(property_id)
    if progress['validated'] == progress['total']:
        if st.button("🎉 Approve Property for Public Listing", type="primary"):
            # Assign notary to property
            updated_property = assign_notary_to_property(prop_data, current_notary.notary_id)
            updated_property.looking_for_notary = False
            updated_property.validation_date = datetime.now()
            updated_property.notary_attached = current_notary.notary_id

            save_property(updated_property)

            # Update notary's work lists
            updated_notary = add_work_to_notary(current_notary, property_id, "property_checked")
            notaries = load_data(NOTARIES_FILE)
            notaries[current_notary.notary_id] = updated_notary.dict()
            save_data(NOTARIES_FILE, notaries)

            st.success("Property approved and moved to public listings!")
            st.rerun()