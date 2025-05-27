# BUYING PROCESS SPECIFIC FILES

## gpp/interface/utils/buying_database.py
**Key Components:**
```python
def init_buying_database():
    """Initialize buying transactions database file"""
    if not os.path.exists(BUYING_TRANSACTIONS_FILE):
        save_data(BUYING_TRANSACTIONS_FILE, {})


def save_buying_transaction(buying_obj: Buying):

def save_buying_transaction(buying_obj: Buying):
    """Save buying transaction to database"""
    init_buying_database()

    # Load existing transactions
    transactions = load_data(BUYING_TRANSACTIONS_FILE)

    # Convert to dict and handle datetime/decimal serialization
    transaction_dict = buying_obj.dict()


    def convert_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_datetime(item) for item in obj]
        return obj

def load_buying_transaction(buying_id: str) -> Optional[Buying]:
    """Load buying transaction from database"""
    init_buying_database()

    transactions = load_data(BUYING_TRANSACTIONS_FILE)

    if buying_id not in transactions:
        return None

    transaction_dict = transactions[buying_id]

    def convert_from_json(obj):
        if isinstance(obj, str):
            # Try to parse as datetime
            for fmt in ["%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(obj, fmt)
                except ValueError:
                    continue
            return obj
        elif isinstance(obj, dict):

def get_all_buying_transactions() -> Dict[str, Buying]:
    """Get all buying transactions from database"""
    init_buying_database()

    transactions_dict = load_data(BUYING_TRANSACTIONS_FILE)
    transactions = {}

    for buying_id, transaction_data in transactions_dict.items():
        transaction = load_buying_transaction(buying_id)
        if transaction:

def get_user_buying_transactions(user_id: str, user_type: str) -> Dict[str, Buying]:
    """Get buying transactions relevant to a specific user"""
    all_transactions = get_all_buying_transactions()
    relevant_transactions = {}

    for buying_id, buying_obj in all_transactions.items():
        if user_type == "agent" and buying_obj.agent_id == user_id:
            relevant_transactions[buying_id] = buying_obj
        elif user_type == "buyer" and buying_obj.buyer_id == user_id:
            relevant_transactions[buying_id] = buying_obj

def delete_buying_transaction(buying_id: str) -> bool:
    """Delete buying transaction from database"""
    init_buying_database()

    transactions = load_data(BUYING_TRANSACTIONS_FILE)

    if buying_id in transactions:
        del transactions[buying_id]
        save_data(BUYING_TRANSACTIONS_FILE, transactions)
        return True

def get_buying_transactions_by_property(property_id: str) -> Dict[str, Buying]:
    """Get all buying transactions for a specific property"""
    all_transactions = get_all_buying_transactions()

    return {
        buying_id: transaction
        for buying_id, transaction in all_transactions.items()
        if transaction.property_id == property_id
    }


def get_active_buying_transactions() -> Dict[str, Buying]:
    """Get all active buying transactions (not completed or cancelled)"""
    all_transactions = get_all_buying_transactions()

    return {
        buying_id: transaction
        for buying_id, transaction in all_transactions.items()
        if transaction.status not in ["completed", "cancelled"]
    }
```

## analysis_chunks/buying_process_files.md
```
# BUYING PROCESS SPECIFIC FILES

## gpp/interface/utils/buying_database.py
**Key Components:**
```python
def init_buying_database():
    """Initialize buying transactions database file"""
    if not os.path.exists(BUYING_TRANSACTIONS_FILE):
        save_data(BUYING_TRANSACTIONS_FILE, {})


def save_buying_transaction(buying_obj: Buying):

def save_buying_transaction(buying_obj: Buying):
    """Save buying transaction to database"""
    init_buying_database()

    # Load existing transactions
    transactions = load_data(BUYING_TRANSACTIONS_FILE)

    # Convert to dict and handle datetime/decimal serialization
    transaction_dict = buying_obj.dict()


    def convert_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_datetime(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert...
```

## gpp/interface/components/shared/buying_components.py
**Key Components:**
```python
def show_buying_dashboard(current_user, user_type: str):
    """Main buying dashboard for different user types"""
    st.title("🏠 Property Buying Transactions")

    # Get user ID based on user type
    user_id = getattr(current_user, f'{user_type.lower()}_id', None)
    if not user_id:
        st.error(f"Could not retrieve {user_type} ID")
        return


def start_buying_process(property_id: str, buyer_id: str, agent_id: str):
    """Start a new buying transaction"""
    st.subheader("🏠 Start Property Purchase")

    # Get property details
    properties = get_properties()
    if property_id not in properties:
        st.error("Property not found")
        return


def show_transaction_details(buying_id: str, current_user, user_type: str):
    """Show detailed transaction view"""
    buying_transaction = load_buying_transaction(buying_id)
    if not buying_transaction:
        st.error("Transaction not found")
        return

    # Transaction header
    _render_transaction_header(buying_transaction)


def _show_available_properties_for_buying(current_user):
    """Show available validated properties for buying"""
    st.subheader("🏠 Available Properties")

    properties = get_properties()
    validated_properties = [
        (prop_id, prop) for prop_id, prop in properties.items()
        if prop.notary_attached and not prop.looking_for_notary
    ]


def _render_buying_overview(transactions: Dict[str, Buying], user_type: str):
    """Render buying overview dashboard"""
    st.subheader("📊 Transaction Overview")

    # Statistics
    total = len(transactions)
    active = len([t for t in transactions.values() if t.status in ["pending", "documents_pending", "under_review"]])
    completed = len([t for t in transactions.values() if t.status == "completed"])

    col1, col2, col3, col4 = st.columns(4)

def _render_transaction_list(transactions: Dict[str, Buying], current_user, user_type: str):
    """Render list of transactions"""
    st.subheader("📋 Your Transactions")

    # Filter options
    col1, col2 = st.columns(2)

    with col1:
        status_filter = st.selectbox(
            "Filter by Status",

def _render_transaction_card(buying_id: str, transaction: Buying, current_user, user_type: str):
    """Render individual transaction card"""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.write(f"**Transaction:** {buying_id[:12]}...")
            st.write(f"**Property:** {transaction.property_id[:12]}...")
            if transaction.final_price:
                st.write(f"**Price:** €{transaction.final_price:,.2f}")

def _render_transaction_header(buying_transaction: Buying):
    """Render transaction header with key information"""
    properties = get_properties()
    property_data = properties.get(buying_transaction.property_id)

    if not property_data:
        st.error("Property data not found")
        return

    # Header section

def _render_progress_section(progress: Dict[str, Any]):
    """Render progress overview"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Documents", f"{progress['validated_documents']}/{progress['total_documents']}")

    with col2:
        st.metric("Progress", f"{progress['progress_percentage']:.0f}%")


def _render_documents_section(buying_transaction: Buying, current_user, user_type: str):
    """Render documents management section"""
    st.subheader("📄 Transaction Documents")

    # Document upload (if user can edit)
    if user_type.lower() in ["agent", "buyer"]:
        with st.expander("📎 Upload New Document"):
            _render_document_upload(buying_transaction, current_user, user_type)

    # Document list

def _render_document_upload(buying_transaction: Buying, current_user, user_type: str):
    """Render document upload form"""
    user_id = getattr(current_user, f'{user_type.lower()}_id', None)

    with st.form(f"upload_doc_{buying_transaction.buying_id}"):
        col1, col2 = st.columns(2)

        with col1:
            doc_type = st.selectbox(
                "Document Type",

def _render_document_row(buying_transaction: Buying, doc_type: str, doc_name: str, current_user, user_type: str):
    """Render individual document row"""
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

    doc_id = buying_transaction.buying_documents.get(doc_type)
    validation_info = buying_transaction.document_validation_status.get(doc_type, {})

    with col1:
        if doc_id:
            if validation_info.get("validation_status", False):

def _render_meetings_section(buying_transaction: Buying, current_user, user_type: str):
    """Render meetings section"""
    st.subheader("📅 Scheduled Meetings")

    # Schedule new meeting
    if can_user_edit_transaction(buying_transaction, getattr(current_user, f'{user_type.lower()}_id'), user_type):
        with st.expander("📅 Schedule New Meeting"):
            _render_meeting_scheduler(buying_transaction, current_user, user_type)

    # Display meetings

def _render_meeting_scheduler(buying_transaction: Buying, current_user, user_type: str):
    """Render meeting scheduling form"""
    user_id = getattr(current_user, f'{user_type.lower()}_id')

    with st.form(f"schedule_meeting_{buying_transaction.buying_id}"):
        col1, col2 = st.columns(2)

        with col1:
            meeting_type = st.selectbox(
                "Meeting Type",

def _render_meeting_card(meeting: Dict[str, Any], buying_transaction: Buying, current_user, user_type: str):
    """Render individual meeting card"""
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.write(f"**📅 {MEETING_TYPES.get(meeting['meeting_type'], 'Meeting')}**")
            st.write(f"**🕐 Date:** {meeting['scheduled_date'].strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**📍 Location:** {meeting.get('location', 'TBD')}")


def _render_communication_section(buying_transaction: Buying, current_user, user_type: str):
    """Render communication/notes section"""
    st.subheader("💬 Transaction Communication")

    # Add new note
    user_id = getattr(current_user, f'{user_type.lower()}_id')

    with st.form(f"add_note_{buying_transaction.buying_id}"):
        note_text = st.text_area("Add Note", placeholder="Add a note to this transaction...")
        note_type = st.selectbox("Note Type", ["general", "document", "meeting", "urgent"])

def _render_note_card(note: Dict[str, Any]):
    """Render individual note card"""
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**{note.get('note', '')}**")
            st.caption(f"Type: {note.get('note_type', 'general').title()}")

        with col2:

def _render_detailed_progress(buying_transaction: Buying):
    """Render detailed progress view"""
    st.subheader("📊 Detailed Progress")

    progress = get_buying_progress(buying_transaction)

    # Progress overview
    col1, col2 = st.columns(2)

    with col1:

def _render_transaction_settings(buying_transaction: Buying, current_user, user_type: str):
    """Render transaction settings and actions"""
    st.subheader("⚙️ Transaction Settings")

    user_id = getattr(current_user, f'{user_type.lower()}_id')

    # Status management (for authorized users)
    if user_type.lower() in ["agent", "notary"] or buying_transaction.buyer_id == user_id:
        st.write("**Status Management:**")


def _generate_transaction_report(buying_transaction: Buying):
    """Generate a transaction report"""
    st.subheader("📊 Transaction Report")

    # Get property details
    properties = get_properties()
    property_data = properties.get(buying_transaction.property_id)

    if not property_data:
        st.error("Property data not found")
```

## gpp/classes/buyer.py
**Key Components:**
```python
class Buyer(BaseModel):
    """Buyer class - similar to agent with financial documents"""
    buyer_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Financial Information
    bank_account: Optional[str] = Field(None, description="Bank account information")
    income_segment: Optional[str] = Field(None, description="Income bracket/segment")

    # Property Interest Lists
    interested_properties: List[str] = Field(

def add_document_to_buyer(buyer_obj: Buyer, doc_type: str, document_id: str) -> Buyer:
    """Add document ID to buyer's document dictionary"""
    if doc_type in buyer_obj.documents:
        buyer_obj.documents[doc_type] = document_id
    return buyer_obj


def add_interest_to_buyer(buyer_obj: Buyer, property_id: str, interest_type: str = "interested") -> Buyer:

def add_interest_to_buyer(buyer_obj: Buyer, property_id: str, interest_type: str = "interested") -> Buyer:
    """Add property to buyer's interest lists"""
    if interest_type == "interested":
        if property_id not in buyer_obj.interested_properties:
            buyer_obj.interested_properties.append(property_id)
    elif interest_type == "reserved":
        if property_id not in buyer_obj.reserved_properties:
            buyer_obj.reserved_properties.append(property_id)
    return buyer_obj
```

