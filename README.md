# GPP - Global Property Platform

*A comprehensive property management system connecting agents, buyers, and notaries in a unified digital platform.*

## 🏠 Overview

GPP (Global Property Platform) is a modern property management system designed to streamline the entire property transaction lifecycle. The platform connects three key stakeholders - **Agents**, **Buyers**, and **Notaries** - while managing all legal documentation and transaction processes digitally.

### Key Features
- 📄 **Digital Document Management** - Upload, validate, and track all property-related documents
- 🏘️ **Property Listing Management** - Complete property information with mandatory legal documentation
- 👥 **Multi-User System** - Separate interfaces for Agents, Buyers, and Notaries
- ✅ **Document Validation** - Notary-verified document authentication
- 💼 **Transaction Management** - End-to-end buying process management
- 💳 **Payment Integration** - Demo payment system for property reservations
- 💬 **Chat System** - Real-time communication between all parties
- 🔒 **Legal Compliance** - Built-in mandatory document requirements

---

## 🏗️ System Architecture & File Structure

The platform is built using **Streamlit** with **Pydantic** models for data validation and **JSON** files for data persistence.

### Complete Project Structure

```
forring/
├── .venv/                          # Virtual environment
├── data/                           # Data storage directory (auto-created)
│   ├── properties.json             # Property listings data
│   ├── documents.json              # Document metadata
│   ├── agents.json                 # Agent user data
│   ├── buyers.json                 # Buyer user data
│   ├── notaries.json               # Notary user data
│   ├── buying_transactions.json    # Property buying transactions
│   ├── chats.json                  # Chat conversations
│   ├── buying_chats.json           # Buying-specific chats
│   └── files/                      # Uploaded files directory
│       ├── documents/              # Property legal documents
│       ├── photos/                 # Property photos
│       ├── additional_docs/        # Additional property documents
│       └── buying_documents/       # Transaction-specific documents
├── app.py                          # 🔥 MAIN APPLICATION ENTRY POINT
├── gpp/                           # Main application package
│   ├── __init__.py
│   ├── classes/                   # 📊 CORE BUSINESS LOGIC
│   │   ├── __init__.py
│   │   ├── agent.py               # Agent data model & functions
│   │   ├── buyer.py               # Buyer data model & functions
│   │   ├── buying.py              # 💰 BUYING TRANSACTION SYSTEM
│   │   ├── chat.py                # Chat system data models
│   │   ├── document.py            # Document management
│   │   ├── notary.py              # Notary data model & functions
│   │   └── property.py            # Property data model & functions
│   └── interface/                 # 🖥️ USER INTERFACE LAYER
│       ├── __init__.py
│       ├── config/
│       │   ├── __init__.py
│       │   └── constants.py       # 🔧 APP CONFIGURATION & CONSTANTS
│       ├── dashboards/            # 📋 MAIN USER DASHBOARDS
│       │   ├── __init__.py
│       │   ├── agent_dashboard.py     # Agent main interface
│       │   ├── buyer_dashboard.py     # 🛒 BUYER MAIN INTERFACE
│       │   └── notary_dashboard.py    # Notary main interface
│       ├── components/            # 🧩 UI COMPONENTS
│       │   ├── agent/             # Agent-specific components
│       │   │   ├── __init__.py
│       │   │   ├── chat_management.py
│       │   │   ├── document_manager.py
│       │   │   ├── property_form.py
│       │   │   └── property_list.py
│       │   ├── buyer/             # Buyer-specific components
│       │   │   ├── __init__.py
│       │   │   └── chat_management.py
│       │   ├── notary/            # Notary-specific components
│       │   │   ├── __init__.py
│       │   │   ├── chat_management.py
│       │   │   ├── validated_properties.py
│       │   │   └── validation_queue.py
│       │   └── shared/            # 🔄 SHARED COMPONENTS
│       │       ├── __init__.py
│       │       ├── buying_components.py       # Buying transaction UI
│       │       ├── demo_payment_system.py     # 💳 PAYMENT SYSTEM
│       │       ├── enhanced_buying_process.py # Enhanced buying features
│       │       ├── buying_chat_system.py      # Transaction chats
│       │       └── chat_interface.py          # General chat UI
│       └── utils/                 # 🛠️ UTILITY FUNCTIONS
│           ├── __init__.py
│           ├── database.py            # 📁 MAIN DATABASE OPERATIONS
│           ├── buying_database.py     # Buying transaction database
│           ├── chat_database.py       # Chat system database
│           ├── property_helpers.py    # Property utility functions
│           ├── user_management.py     # User creation & management
│           └── file_storage.py        # File upload & storage
├── requirements.txt               # Python dependencies
└── README.md                     # This file
```

---

## 👥 User Roles & System Flow

### 🏢 **Agents**
- **Primary Function:** Post and manage property listings
- **Key Files:** 
  - `gpp/interface/dashboards/agent_dashboard.py` - Main interface
  - `gpp/classes/agent.py` - Agent data model
  - `gpp/interface/components/agent/` - Agent-specific UI components
- **Capabilities:**
  - Create and manage property listings
  - Upload mandatory legal documents
  - Upload additional property documents
  - Track active, sold, and pending properties
  - Manage client relationships via chat
  - Handle buying transactions from seller side

### 💰 **Buyers** 
- **Primary Function:** Search and purchase properties
- **Key Files:**
  - `gpp/interface/dashboards/buyer_dashboard.py` - **MAIN BUYER INTERFACE**
  - `gpp/classes/buyer.py` - Buyer data model
  - `gpp/interface/components/buyer/` - Buyer-specific UI components
- **Capabilities:**
  - Browse validated property listings
  - Add properties to favorites ❤️
  - Reserve properties with payment system 💳
  - Access property documents after reservation 📄
  - Manage buying transaction documents
  - Chat with agents and notaries 💬

### ⚖️ **Notaries**
- **Primary Function:** Validate documents and oversee legal compliance
- **Key Files:**
  - `gpp/interface/dashboards/notary_dashboard.py` - Main interface
  - `gpp/classes/notary.py` - Notary data model
  - `gpp/interface/components/notary/` - Notary-specific UI components
- **Capabilities:**
  - Review and validate property documents
  - Verify buyer credentials and transaction documents
  - Approve/reject buying transactions
  - Manage validation queues
  - Complete property transactions (only notaries can mark as complete)

---

## 🔄 Complete Transaction Workflow

### 1. **Property Listing Phase**
- **File:** `gpp/interface/components/agent/property_form.py`
- Agent creates property listing with mandatory documents
- Documents stored in `data/files/documents/`
- Property enters validation queue

### 2. **Document Validation Phase**
- **File:** `gpp/interface/components/notary/validation_queue.py`
- Notary reviews all mandatory legal documents
- Documents marked as validated/rejected
- Property moves to "available" status when fully validated

### 3. **Buyer Interest & Reservation**
- **File:** `gpp/interface/dashboards/buyer_dashboard.py`
- Buyer browses validated properties
- Adds properties to favorites
- Clicks "Reserve" → triggers payment system

### 4. **Payment & Transaction Creation**
- **File:** `gpp/interface/components/shared/demo_payment_system.py`
- Demo payment processing (5% reservation fee)
- Creates buying transaction in `gpp/classes/buying.py`
- Property status changes to "reserved"

### 5. **Document Upload & Validation**
- **Files:** 
  - `gpp/interface/components/shared/enhanced_buying_process.py`
  - `gpp/classes/buying.py`
- Buyer uploads financial documents
- Agent uploads contracts
- Notary validates all transaction documents

### 6. **Transaction Completion**
- **File:** `gpp/classes/buying.py` - `update_buying_status()`
- **ONLY NOTARIES** can mark transactions as "completed"
- Final contracts signed
- Property ownership transferred

---

## 📋 Document Management System

### Document Categories & File Locations

#### 🏠 **Property Documents (Mandatory Legal Requirements)**
- **Configuration:** `gpp/interface/config/constants.py` → `MANDATORY_DOCS`
- **Storage:** `data/files/documents/`
- **Data Model:** `gpp/classes/property.py` → `mandatory_legal_docs`

**Required Documents:**
1. **Title Deed** - Property ownership verification
2. **Land Registry Extract** - Ownership, boundaries, encumbrances  
3. **Building Permit** - Construction/modification authorization

#### 📎 **Additional Property Documents**
- **Configuration:** `gpp/interface/config/constants.py` → `ADDITIONAL_DOC_CATEGORIES`
- **Storage:** `data/files/additional_docs/`
- **Data Model:** `gpp/classes/property.py` → `additional_docs`

#### 💼 **Buying Transaction Documents**
- **Configuration:** `gpp/interface/config/constants.py` → `BUYING_DOCUMENT_TYPES`
- **Storage:** `data/files/buying_documents/`
- **Data Model:** `gpp/classes/buying.py` → `buying_documents`

### Document Access Control
- **File:** `gpp/interface/dashboards/buyer_dashboard.py` → `_show_buyer_documents()`
- **Rule:** Buyers can ONLY see documents for properties they have reserved
- **Implementation:** Uses `get_user_buying_transactions()` to check access rights

---

## 💳 Payment & Buying System

### Payment Flow
1. **Trigger:** Buyer clicks "Reserve" button in property card
2. **File:** `gpp/interface/dashboards/buyer_dashboard.py` → `_render_property_card()`
3. **Session State:** `st.session_state["payment_page_property"] = prop_id`
4. **Payment Page:** `gpp/interface/components/shared/demo_payment_system.py`
5. **Success Handler:** Creates buying transaction in `gpp/classes/buying.py`

### Demo Payment System
- **Location:** `gpp/interface/components/shared/demo_payment_system.py`
- **Test Cards:** 
  - ✅ Success: Any card except starting with "4000"
  - ❌ Decline: Cards starting with "4000"
- **Reservation Fee:** 5% of property price
- **No real money processed**

---

## 💬 Chat & Communication System

### Chat Architecture
- **Base Model:** `gpp/classes/chat.py` → `PropertyChat`
- **Privacy:** Separate channels for different user pairs
  - Agent ↔ Notary (private)
  - Agent ↔ Buyer (private per buyer)
  - Buyers cannot see each other's conversations

### Chat Database
- **Files:** `gpp/interface/utils/chat_database.py` + `gpp/interface/utils/chat_database_integration.py`
- **Storage:** `data/chats.json` + `data/buying_chats.json`
- **Integration:** Buying transactions have dedicated chat channels

### Chat UI Components
- **General:** `gpp/interface/components/shared/chat_interface.py`
- **Buying-specific:** `gpp/interface/components/shared/buying_chat_system.py`

---

## 🛠️ Development Guide for LLM Assistance

### 🔥 Common Issues & Where to Look

#### **1. Button Form Errors**
- **Problem:** `st.button()` inside `st.form()` causes errors
- **Solution Location:** `gpp/interface/dashboards/buyer_dashboard.py` → `_render_property_card()`
- **Fix:** Move buttons outside forms or use `st.form_submit_button()`

#### **2. Favorites System Not Working**
- **Data Model:** `gpp/classes/buyer.py` → `interested_properties`
- **UI Implementation:** `gpp/interface/dashboards/buyer_dashboard.py` → `_show_buyer_favorites()`
- **Save Function:** Uses `gpp/interface/config/constants.py` → `BUYERS_FILE`

#### **3. Document Visibility Issues**
- **Access Control:** `gpp/interface/dashboards/buyer_dashboard.py` → `_show_buyer_documents()`
- **Permission Check:** Uses `get_user_buying_transactions()` to verify access
- **Document Loading:** `gpp/interface/utils/database.py` → `get_documents()`

#### **4. Payment System Integration**
- **Entry Point:** `app.py` → `_handle_special_interfaces()`
- **Session State:** `st.session_state["payment_page_property"]`
- **Payment Processing:** `gpp/interface/components/shared/demo_payment_system.py`

#### **5. Transaction Status Management**
- **Status Updates:** `gpp/classes/buying.py` → `update_buying_status()`
- **Status Constants:** `gpp/interface/config/constants.py` → `TRANSACTION_STATUSES`
- **Notary Completion:** Only notaries can set status to "completed"

### 🔧 Key Configuration Files

#### **Constants & Configuration**
```python
# gpp/interface/config/constants.py
- APP_CONFIG: Streamlit page configuration
- File paths: PROPERTIES_FILE, BUYERS_FILE, etc.
- MANDATORY_DOCS: Required legal documents
- BUYING_DOCUMENT_TYPES: Transaction documents
- TRANSACTION_STATUSES: Status definitions
```

#### **Database Operations**
```python
# gpp/interface/utils/database.py
- init_data_files(): Initialize all JSON files
- get_properties(), get_documents(), etc.
- save_data(), load_data(): Generic JSON operations

# gpp/interface/utils/buying_database.py  
- save_buying_transaction()
- get_user_buying_transactions()
- load_buying_transaction()
```

### 🚀 Main Application Entry Points

#### **Primary Entry Point**
- **File:** `app.py` → `main()`
- **Navigation:** `_get_navigation_options()` → Role-specific menus
- **Routing:** `route_to_enhanced_dashboard()` → Directs to user dashboards

#### **Dashboard Entry Points**
```python
# Agent Dashboard
gpp/interface/dashboards/agent_dashboard.py → agent_dashboard()

# Buyer Dashboard (MAIN BUYER INTERFACE)
gpp/interface/dashboards/buyer_dashboard.py → buyer_dashboard()

# Notary Dashboard  
gpp/interface/dashboards/notary_dashboard.py → notary_dashboard()
```

### 🔍 Debugging & Troubleshooting

#### **Session State Variables**
```python
# Key session state variables to check:
st.session_state["current_user"]           # Current logged-in user
st.session_state["user_type"]              # "agent", "buyer", or "notary"
st.session_state["payment_page_property"]  # Property ID for payment
st.session_state["selected_transaction"]   # Selected buying transaction
st.session_state["upload_docs_transaction"] # Document upload modal
```

#### **Data File Locations**
```
data/
├── properties.json          # All property listings
├── buyers.json             # Buyer profiles & favorites
├── buying_transactions.json # All buying transactions
├── documents.json          # Document metadata
└── files/                  # Actual uploaded files
```

#### **Common Data Flow Issues**
1. **Property not showing:** Check validation status in `get_validated_properties()`
2. **Favorites not saving:** Check `BUYERS_FILE` path and `save_data()` calls
3. **Documents not accessible:** Verify `get_user_buying_transactions()` returns data
4. **Payment not working:** Check `st.session_state["payment_page_property"]` is set

---

## 🎯 Platform Benefits

### For Agents
- **Streamlined Listings** - Quick property posting with document templates
- **Client Management** - Track all properties and buyer interactions
- **Legal Compliance** - Built-in mandatory document requirements
- **Sales Pipeline** - Clear visibility of property status progression

### For Buyers
- **Verified Properties** - All listings backed by validated legal documents
- **Favorites System** - Save and manage interested properties
- **Transparent Process** - Clear view of required documentation
- **Secure Transactions** - Notary-verified buying process
- **Document Access** - View property documents after reservation
- **Integrated Payment** - Simple reservation with demo payment system

### For Notaries
- **Efficient Workflow** - Queue-based document review system
- **Digital Validation** - Streamlined document verification process
- **Transaction Control** - Only notaries can complete transactions
- **Audit Trail** - Complete history of all validations
- **Legal Compliance** - Standardized validation procedures

---

## 🚀 Technical Implementation

### Backend Structure
- **Framework:** Streamlit for web interface
- **Data Models:** Pydantic for type-safe validation
- **Storage:** JSON files for data persistence
- **File Handling:** Local file system storage
- **Session Management:** Streamlit session state

### Key Technical Features
- **UUID Generation** - Unique identifiers for all entities
- **Datetime Tracking** - Complete audit trail timestamps
- **Status Management** - Property and transaction status tracking
- **Validation Logic** - Built-in business rule enforcement
- **Document Access Control** - Role-based document visibility
- **Real-time Chat** - WebSocket-like chat via Streamlit

### Performance Considerations
- **File Storage** - Uses local file system (can be upgraded to cloud storage)
- **Data Loading** - JSON files loaded on demand
- **Session State** - Efficient state management for user sessions
- **Memory Usage** - Optimized for small to medium datasets

---

## 🔧 Development Setup

### Prerequisites
```bash
Python 3.8+
pip install streamlit pydantic
```

### Quick Start
```bash
# Clone/download the project
cd forring/

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

### Data Reset
To clean all data and start fresh:
```bash
# Delete data directory
rm -rf data/

# Restart application (will recreate empty files)
streamlit run app.py
```

---

## 📱 Current Status & Roadmap

### ✅ Completed Features
- Complete user role system (Agent, Buyer, Notary)
- Property listing and document management
- Document validation workflow
- Demo payment system integration
- Buying transaction management
- Real-time chat system
- Favorites system for buyers
- Document access control
- Multi-tab dashboards for all user types

### 🔄 In Progress
- Enhanced document viewer
- Advanced search and filtering
- Notification system
- Transaction analytics
- File download functionality

### 📋 Planned Features
- Real email notifications
- Advanced analytics dashboard
- Mobile-responsive design
- API for third-party integrations
- Multi-language support
- Cloud storage integration
- Real payment gateway integration

---

## 💡 Innovation Points

- **Document-Centric Design** - Everything revolves around proper documentation
- **Multi-Party Validation** - Notary involvement ensures legal compliance
- **Integrated Payment** - Seamless reservation to transaction flow
- **Role-Based Access** - Secure document visibility controls
- **Status-Driven Workflow** - Clear property and transaction lifecycle
- **Chat Integration** - Real-time communication between all parties
- **Audit Trail** - Complete history of all actions and validations

---

## 🎯 Target Market

- **Real Estate Agencies** - Streamline property listings and sales
- **Independent Agents** - Professional tools for property management  
- **Property Buyers** - Secure and transparent buying process
- **Notaries** - Efficient document validation workflows
- **Legal Firms** - Compliance and document management tools

---

*GPP - Transforming property transactions through digital innovation and legal compliance.*

---

## 🆘 Quick Help for Developers


1. **Main App:** `app.py` - Application routing and navigation
2. **Buyer Interface:** `gpp/interface/dashboards/buyer_dashboard.py` - Most buyer issues
3. **Constants:** `gpp/interface/config/constants.py` - All configuration
4. **Database:** `gpp/interface/utils/database.py` - Data operations
5. **Buying System:** `gpp/classes/buying.py` - Transaction logic
6. **Payment System:** `gpp/interface/components/shared/demo_payment_system.py`

**Most common issues:** Form/button conflicts, data not saving, document access, session state management.