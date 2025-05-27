"""
File storage utilities for GPP Platform
Handles actual file uploads and storage
"""

import os
import uuid
import streamlit as st
from datetime import datetime
from typing import Optional, List
import shutil

from gpp.interface.config.constants import DATA_DIR

# File storage directories
STORAGE_DIR = os.path.join(DATA_DIR, "files")
DOCUMENTS_STORAGE = os.path.join(STORAGE_DIR, "documents")
PHOTOS_STORAGE = os.path.join(STORAGE_DIR, "photos")
ADDITIONAL_DOCS_STORAGE = os.path.join(STORAGE_DIR, "additional_docs")


def init_file_storage():
    """Initialize file storage directories"""
    directories = [STORAGE_DIR, DOCUMENTS_STORAGE, PHOTOS_STORAGE, ADDITIONAL_DOCS_STORAGE]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def save_uploaded_file(uploaded_file, storage_type="documents", custom_filename=None) -> Optional[str]:
    """
    Save uploaded file to storage and return the file path

    Args:
        uploaded_file: Streamlit uploaded file object
        storage_type: "documents", "photos", or "additional_docs"
        custom_filename: Optional custom filename

    Returns:
        str: File path if successful, None if failed
    """
    try:
        # Initialize storage if needed
        init_file_storage()

        # Determine storage directory
        if storage_type == "documents":
            storage_dir = DOCUMENTS_STORAGE
        elif storage_type == "photos":
            storage_dir = PHOTOS_STORAGE
        elif storage_type == "additional_docs":
            storage_dir = ADDITIONAL_DOCS_STORAGE
        else:
            storage_dir = DOCUMENTS_STORAGE

        # Generate unique filename
        if custom_filename:
            filename = custom_filename
        else:
            # Use original filename with timestamp to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = uploaded_file.name.split('.')[-1] if '.' in uploaded_file.name else 'txt'
            base_name = uploaded_file.name.rsplit('.', 1)[0] if '.' in uploaded_file.name else uploaded_file.name
            filename = f"{base_name}_{timestamp}.{file_extension}"

        # Full file path
        file_path = os.path.join(storage_dir, filename)

        # Save the file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"✅ File saved: {filename}")
        return file_path

    except Exception as e:
        st.error(f"❌ Error saving file: {str(e)}")
        return None


def save_multiple_files(uploaded_files: List, storage_type="documents") -> List[str]:
    """
    Save multiple uploaded files

    Args:
        uploaded_files: List of Streamlit uploaded file objects
        storage_type: Storage directory type

    Returns:
        List[str]: List of file paths
    """
    file_paths = []

    for uploaded_file in uploaded_files:
        file_path = save_uploaded_file(uploaded_file, storage_type)
        if file_path:
            file_paths.append(file_path)

    return file_paths


def file_exists(file_path: str) -> bool:
    """Check if file exists in storage"""
    return os.path.exists(file_path) and os.path.isfile(file_path)


def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path) if file_exists(file_path) else 0
    except:
        return 0


def get_file_info(file_path: str) -> dict:
    """Get comprehensive file information"""
    try:
        if not file_exists(file_path):
            return {"exists": False}

        stat = os.stat(file_path)
        return {
            "exists": True,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "extension": file_path.split('.')[-1].lower() if '.' in file_path else None
        }
    except Exception as e:
        return {"exists": False, "error": str(e)}


def delete_file(file_path: str) -> bool:
    """Delete file from storage"""
    try:
        if file_exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting file: {str(e)}")
        return False


def read_file_content(file_path: str) -> Optional[bytes]:
    """Read file content as bytes"""
    try:
        if file_exists(file_path):
            with open(file_path, "rb") as f:
                return f.read()
        return None
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None


def get_storage_stats() -> dict:
    """Get storage statistics"""
    try:
        init_file_storage()

        stats = {
            "documents": {"count": 0, "size": 0},
            "photos": {"count": 0, "size": 0},
            "additional_docs": {"count": 0, "size": 0},
            "total": {"count": 0, "size": 0}
        }

        # Count files in each directory
        for storage_type, directory in [
            ("documents", DOCUMENTS_STORAGE),
            ("photos", PHOTOS_STORAGE),
            ("additional_docs", ADDITIONAL_DOCS_STORAGE)
        ]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        stats[storage_type]["count"] += 1
                        stats[storage_type]["size"] += file_size
                        stats["total"]["count"] += 1
                        stats["total"]["size"] += file_size

        # Convert sizes to MB
        for category in stats:
            stats[category]["size_mb"] = round(stats[category]["size"] / (1024 * 1024), 2)

        return stats

    except Exception as e:
        return {"error": str(e)}


def cleanup_orphaned_files():
    """Clean up files that are no longer referenced in database"""
    try:
        from gpp.interface.utils.database import get_documents

        # Get all document records
        documents = get_documents()
        referenced_files = set()

        # Collect all referenced file paths
        for doc in documents.values():
            if doc.document_path and file_exists(doc.document_path):
                referenced_files.add(doc.document_path)

        # Check each storage directory
        orphaned_files = []
        for directory in [DOCUMENTS_STORAGE, PHOTOS_STORAGE, ADDITIONAL_DOCS_STORAGE]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path) and file_path not in referenced_files:
                        orphaned_files.append(file_path)

        return orphaned_files

    except Exception as e:
        st.error(f"Error during cleanup: {str(e)}")
        return []


def show_storage_info():
    """Display storage information in Streamlit"""
    st.subheader("📊 File Storage Information")

    stats = get_storage_stats()

    if "error" in stats:
        st.error(f"Error getting storage stats: {stats['error']}")
        return

    # Display stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📄 Documents", stats["documents"]["count"], f"{stats['documents']['size_mb']} MB")

    with col2:
        st.metric("📸 Photos", stats["photos"]["count"], f"{stats['photos']['size_mb']} MB")

    with col3:
        st.metric("📎 Additional", stats["additional_docs"]["count"], f"{stats['additional_docs']['size_mb']} MB")

    with col4:
        st.metric("📦 Total", stats["total"]["count"], f"{stats['total']['size_mb']} MB")

    # Storage locations
    with st.expander("📁 Storage Locations"):
        st.write(f"**Documents:** `{DOCUMENTS_STORAGE}`")
        st.write(f"**Photos:** `{PHOTOS_STORAGE}`")
        st.write(f"**Additional Docs:** `{ADDITIONAL_DOCS_STORAGE}`")

    # Cleanup option
    with st.expander("🧹 Cleanup Tools"):
        if st.button("🔍 Find Orphaned Files"):
            orphaned = cleanup_orphaned_files()
            if orphaned:
                st.warning(f"Found {len(orphaned)} orphaned files:")
                for file_path in orphaned[:10]:  # Show first 10
                    st.write(f"• {file_path}")
                if len(orphaned) > 10:
                    st.write(f"... and {len(orphaned) - 10} more")
            else:
                st.success("✅ No orphaned files found!")


# Helper function to create sample files for testing
def create_sample_files():
    """Create sample files for testing purposes"""
    init_file_storage()

    sample_files = [
        ("sample_deed.txt", "documents",
         "TITLE DEED\n\nProperty Owner: John Doe\nProperty Address: 123 Main St\nDate: 2024-01-15"),
        ("sample_permit.txt", "documents",
         "BUILDING PERMIT\n\nPermit Number: BP-2024-001\nIssued to: John Doe\nValid until: 2025-01-15"),
        ("house_front.txt", "photos", "PHOTO: Front view of the house\nTaken: 2024-01-15\nCamera: Professional"),
    ]

    created_files = []

    for filename, storage_type, content in sample_files:
        try:
            if storage_type == "documents":
                storage_dir = DOCUMENTS_STORAGE
            elif storage_type == "photos":
                storage_dir = PHOTOS_STORAGE
            else:
                storage_dir = ADDITIONAL_DOCS_STORAGE

            file_path = os.path.join(storage_dir, filename)

            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                created_files.append(file_path)
        except Exception as e:
            st.error(f"Error creating sample file {filename}: {e}")

    return created_files