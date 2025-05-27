from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class Document(BaseModel):
    """Document management class"""
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_name: str = Field(default="unnamed_doc", description="Name of the document")
    document_path: str = Field(default="", description="Path to the document file")
    upload_id: str = Field(default="", description="ID of person who uploaded")
    validation_status: bool = Field(default=False, description="True if validated, False if not")
    upload_date: datetime = Field(default_factory=datetime.now)
    validation_date: Optional[datetime] = Field(None, description="When document was validated")
    who_validate: Optional[str] = Field(None, description="ID of person who validated")
    visibility: bool = Field(default=True, description="Document visibility")

# Helper function for document validation
def validate_document(document: Document, validator_id: str) -> Document:
    """Mark document as validated"""
    document.validation_status = True
    document.validation_date = datetime.now()
    document.who_validate = validator_id
    return document