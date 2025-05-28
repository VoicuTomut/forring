"""
Demo Payment System for Property Reservations
Handles fake payment processing for demonstration purposes with enhanced document generation
"""

import streamlit as st
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import time
from typing import Dict, Any

from gpp.classes.property import Property, reserve_property
from gpp.classes.buyer import Buyer
from gpp.classes.buying import create_buying_transaction, add_transaction_note
from gpp.interface.utils.database import save_property, get_properties, save_data
from gpp.interface.utils.buying_database import save_buying_transaction

# Try to import auto document generation - if not available, we'll handle it gracefully
try:
    from gpp.interface.utils.auto_document_generation import trigger_post_payment_document_generation

    AUTO_DOCUMENT_GENERATION_AVAILABLE = True
except ImportError:
    AUTO_DOCUMENT_GENERATION_AVAILABLE = False


class PaymentProcessor:
    """Demo payment processor for property reservations"""

    @staticmethod
    def validate_card_number(card_number: str) -> bool:
        """Basic card number validation (demo purposes)"""
        # Remove spaces and check if it's numeric and has correct length
        clean_number = card_number.replace(" ", "")
        return clean_number.isdigit() and len(clean_number) in [15, 16]

    @staticmethod
    def validate_expiry_date(expiry: str) -> bool:
        """Validate expiry date format MM/YY"""
        try:
            month, year = expiry.split("/")
            if len(month) != 2 or len(year) != 2:
                return False

            month_int = int(month)
            year_int = int(year) + 2000  # Convert YY to YYYY

            if month_int < 1 or month_int > 12:
                return False

            # Check if card is not expired
            current_date = datetime.now()
            expiry_date = datetime(year_int, month_int, 28)  # Use 28th as safe date

            return expiry_date > current_date
        except:
            return False

    @staticmethod
    def validate_cvv(cvv: str) -> bool:
        """Validate CVV"""
        return cvv.isdigit() and len(cvv) in [3, 4]

    @staticmethod
    def process_payment(amount: Decimal, card_details: Dict[str, Any]) -> Dict[str, Any]:
        """Process demo payment"""
        # Simulate payment processing delay
        time.sleep(2)

        # Demo: Always approve unless card number starts with "4000"
        if card_details["card_number"].startswith("4000"):
            return {
                "success": False,
                "error": "Payment declined - Insufficient funds",
                "transaction_id": None
            }

        transaction_id = str(uuid.uuid4())
        return {
            "success": True,
            "transaction_id": transaction_id,
            "amount": amount,
            "processed_at": datetime.now()
        }


def show_payment_page(property_id: str, current_buyer: Buyer):
    """Show demo payment page for property reservation"""
    st.title("💳 Property Reservation Payment")

    # Get property details
    properties = get_properties()
    if property_id not in properties:
        st.error("Property not found")
        return

    property_data = properties[property_id]

    # Calculate reservation fee (demo: 5% of property price)
    reservation_fee = property_data.price * Decimal("0.05")

    # Property summary
    with st.container():
        st.subheader("🏠 Property Summary")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Property:** {property_data.title}")
            st.write(f"**Location:** {property_data.address}, {property_data.city}")
            st.write(f"**Full Price:** €{property_data.price:,.2f}")

        with col2:
            st.write(f"**Reservation Fee:** €{reservation_fee:,.2f}")
            st.write(f"**Agent:** {property_data.agent_id[:8]}...")
            st.info("Reservation fee is 5% of property price")

    st.markdown("---")

    # Payment form
    with st.form("payment_form"):
        st.subheader("💳 Payment Details")

        # Card details
        col1, col2 = st.columns(2)

        with col1:
            card_number = st.text_input(
                "Card Number",
                placeholder="1234 5678 9012 3456",
                help="Enter 16-digit card number"
            )

            cardholder_name = st.text_input(
                "Cardholder Name",
                placeholder="John Doe"
            )

        with col2:
            expiry_date = st.text_input(
                "Expiry Date",
                placeholder="MM/YY",
                help="Format: MM/YY"
            )

            cvv = st.text_input(
                "CVV",
                placeholder="123",
                type="password",
                help="3 or 4 digit security code"
            )

        # Billing address
        st.subheader("📍 Billing Address")
        col1, col2 = st.columns(2)

        with col1:
            billing_address = st.text_input("Address")
            billing_city = st.text_input("City")

        with col2:
            billing_postal = st.text_input("Postal Code")
            billing_country = st.selectbox("Country", ["Romania", "Germany", "France", "Spain", "Italy"])

        # Terms and conditions
        st.markdown("---")
        agree_terms = st.checkbox(
            "I agree to the terms and conditions and understand this is a demonstration payment system"
        )

        # Submit payment
        if st.form_submit_button("💳 Pay €{:,.2f} & Reserve Property".format(reservation_fee), type="primary"):
            if not agree_terms:
                st.error("Please agree to terms and conditions")
                return

            # Validate payment details
            validation_errors = []

            if not PaymentProcessor.validate_card_number(card_number):
                validation_errors.append("Invalid card number")

            if not PaymentProcessor.validate_expiry_date(expiry_date):
                validation_errors.append("Invalid or expired card")

            if not PaymentProcessor.validate_cvv(cvv):
                validation_errors.append("Invalid CVV")

            if not cardholder_name.strip():
                validation_errors.append("Cardholder name is required")

            if validation_errors:
                for error in validation_errors:
                    st.error(f"❌ {error}")
                return

            # Process payment
            with st.spinner("Processing payment..."):
                card_details = {
                    "card_number": card_number,
                    "cardholder_name": cardholder_name,
                    "expiry_date": expiry_date,
                    "cvv": cvv
                }

                payment_result = PaymentProcessor.process_payment(reservation_fee, card_details)

            if payment_result["success"]:
                # Payment successful - reserve property and start buying process
                handle_successful_payment(property_id, property_data, current_buyer,
                                          payment_result, reservation_fee)
            else:
                st.error(f"❌ Payment failed: {payment_result['error']}")
                st.info("💡 Demo tip: Card numbers starting with '4000' will be declined")

    if st.session_state.get("payment_successful"):
        show_enhanced_payment_success()

def handle_successful_payment(property_id: str, property_data: Property, current_buyer: Buyer,
                              payment_result: Dict[str, Any], reservation_fee: Decimal):
    """Handle successful payment and trigger document generation"""

    st.success("🎉 Payment Successful!")
    st.success(f"💰 Reservation fee of €{reservation_fee:,.2f} has been processed")
    st.info(f"📄 Transaction ID: {payment_result['transaction_id']}")

    try:
        # Reserve the property
        property_data = reserve_property(property_data, current_buyer.buyer_id)
        property_data.status = "reserved"

        # Save updated property - FIX: Correct parameter order
        properties = get_properties()
        properties[property_id] = property_data
        save_data("properties.json", properties)  # FIX: File path first, data second

        # Create buying transaction
        buying_transaction = create_buying_transaction(
            property_data.agent_id,
            current_buyer.buyer_id,
            property_id
        )

        # Set initial price and add payment info
        buying_transaction.final_price = property_data.price

        # Add payment note
        payment_note = (
            f"Reservation payment processed successfully. "
            f"Amount: €{reservation_fee:,.2f}, "
            f"Transaction ID: {payment_result['transaction_id']}"
        )
        add_transaction_note(
            buying_transaction,
            payment_note,
            current_buyer.buyer_id,
            "payment"
        )

        # Save buying transaction
        save_buying_transaction(buying_transaction)

        # *** NEW: Generate reservation agreement automatically ***
        document_generated = False
        if AUTO_DOCUMENT_GENERATION_AVAILABLE:
            try:
                document_generated = trigger_post_payment_document_generation(buying_transaction)
            except Exception as e:
                st.warning(f"Document generation failed: {e}")
                document_generated = False

        # Update session state
        st.session_state["payment_successful"] = True
        st.session_state["buying_transaction_id"] = buying_transaction.buying_id
        st.session_state["reserved_property_id"] = property_id
        st.session_state["document_auto_generated"] = document_generated

        if document_generated:
            st.success("📄 Reservation Agreement automatically generated!")
            st.info("✍️ Please proceed to sign the reservation agreement in the Document Signing tab.")
        else:
            st.info("📄 Reservation Agreement will be generated shortly by the agent.")

        # REMOVE THIS LINE - it causes the button error:
        # show_enhanced_payment_success()

    except Exception as e:
        st.error(f"❌ Error processing reservation: {str(e)}")
        st.info("Payment was successful, but there was an error creating the buying process. Please contact support.")

        # Debug information
        import traceback
        st.error(f"Debug info: {traceback.format_exc()}")



def show_enhanced_payment_success():
    """Show enhanced payment success message with next steps"""
    if st.session_state.get("payment_successful"):

        st.markdown("---")
        st.subheader("📋 Next Steps")

        if st.session_state.get("document_auto_generated"):
            col1, col2 = st.columns(2)

            with col1:
                st.info("""
                **Your Complete Buying Journey:**
                1. ✅ **Payment Completed** - Reservation secured
                2. ✍️ **Sign Reservation Agreement** - Auto-generated
                3. 💰 **Upload Proof of Funds** - Financial verification
                4. 📋 **Preliminary Contract** - Agent prepares contract
                5. 🔍 **Due Diligence** - Property inspection & research
                6. ✍️ **Final Contract Signing** - Legal completion
                7. 💳 **Final Payment** - Complete purchase
                8. 🔑 **Receive Keys** - Property ownership transfer
                """)

            with col2:
                transaction_id = st.session_state.get("buying_transaction_id", "")
                if transaction_id:
                    st.metric("Transaction ID", transaction_id[:12] + "...")

                st.success("**Document Auto-Generated!**")
                st.write("📄 Reservation Agreement is ready for signing")

                if st.button("✍️ Go to Document Signing", type="primary", key="go_to_signing"):
                    # Clear payment session state
                    if "payment_page_property" in st.session_state:
                        del st.session_state["payment_page_property"]

                    # Set navigation to signing
                    st.session_state["navigate_to_signing"] = True
                    st.session_state["selected_transaction"] = transaction_id
                    st.rerun()

        else:
            col1, col2 = st.columns(2)

            with col1:
                st.info("""
                **What happens next:**
                1. ✅ Property is now reserved for you
                2. 📄 Agent will prepare buying documents
                3. 💼 You'll need to upload additional documents
                4. ⚖️ Notary will validate all documents
                5. ✍️ Final contract signing and completion
                """)

            with col2:
                st.success("""
                **Your buying process has started!**
                - Go to "My Purchases" tab to track progress
                - Upload required documents when requested
                - Communicate with agent and notary via chat
                """)

        # Action buttons (outside of any form)
        st.markdown("### 🎯 Available Actions")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📋 View Buying Process", key="view_buying_process"):
                transaction_id = st.session_state.get("buying_transaction_id")
                if transaction_id:
                    st.session_state["selected_transaction"] = transaction_id
                    st.session_state["show_buying_details"] = True
                    if "payment_page_property" in st.session_state:
                        del st.session_state["payment_page_property"]
                    st.rerun()

        with col2:
            if st.button("💬 Start Chat", key="start_chat_process"):
                property_id = st.session_state.get("reserved_property_id")
                if property_id:
                    st.session_state["start_buying_chat"] = property_id
                    if "payment_page_property" in st.session_state:
                        del st.session_state["payment_page_property"]
                    st.rerun()

        with col3:
            if st.button("📄 My Documents", key="view_documents"):
                if "payment_page_property" in st.session_state:
                    del st.session_state["payment_page_property"]
                # Navigate to buyer dashboard documents section
                st.session_state["buyer_tab"] = "documents"
                st.rerun()

        with col4:
            if st.button("🏠 Back to Properties", key="back_to_properties"):
                # Clear payment session state
                clear_payment_session()
                st.rerun()

        st.markdown("---")


def show_payment_demo_info():
    """Show demo payment information"""
    with st.expander("💡 Demo Payment Information"):
        st.markdown("""
        ### Demo Payment System Information

        This is a **demonstration payment system** for testing purposes only.

        **Test Card Numbers:**
        - ✅ **Successful payment:** Any card number except those starting with "4000"
        - ❌ **Failed payment:** Card numbers starting with "4000" (simulates insufficient funds)

        **Valid Test Cards:**
        - `4242 4242 4242 4242` (Visa)
        - `5555 5555 5555 4444` (Mastercard)
        - `3782 8224 6310 005` (American Express)

        **Invalid Test Card:**
        - `4000 0000 0000 0002` (Declined - insufficient funds)

        **Other Requirements:**
        - Expiry date must be in the future (MM/YY format)
        - CVV must be 3 or 4 digits
        - All fields must be filled

        **Enhanced Features:**
        - 📄 Automatic document generation after payment
        - ✍️ Digital signature workflow integration
        - 💬 Chat system activation
        - 📊 Progress tracking

        **No real money is processed in this demo system.**
        """)


def get_payment_fee_info(property_price: float) -> dict:
    """Get payment fee information"""
    reservation_percentage = 5.0
    reservation_amount = property_price * (reservation_percentage / 100)
    remaining_amount = property_price - reservation_amount

    return {
        "property_price": property_price,
        "reservation_percentage": reservation_percentage,
        "reservation_amount": reservation_amount,
        "remaining_amount": remaining_amount,
        "currency": "EUR"
    }


def show_payment_calculator(property_price: float):
    """Show payment calculation breakdown"""
    fee_info = get_payment_fee_info(property_price)

    st.subheader("💰 Payment Breakdown")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Total Property Price",
            f"€{fee_info['property_price']:,.2f}"
        )
        st.metric(
            "Reservation Fee (5%)",
            f"€{fee_info['reservation_amount']:,.2f}",
            help="This amount secures your reservation"
        )

    with col2:
        st.metric(
            "Due at Closing",
            f"€{fee_info['remaining_amount']:,.2f}",
            help="Remaining amount to be paid when completing purchase"
        )

    # Payment schedule
    with st.expander("📅 Payment Schedule"):
        st.write("**Today:** Reservation fee to secure the property")
        st.write("**At Closing:** Remaining balance when finalizing purchase")
        st.write("**Note:** Final closing amount may vary based on inspections and negotiations")


def show_payment_success_page(transaction_id: str, property_id: str):
    """Show payment success confirmation page"""
    st.title("🎉 Payment Successful!")

    st.success("Your property reservation has been confirmed!")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Transaction Details")
        st.write(f"**Transaction ID:** {transaction_id[:8]}...")
        st.write(f"**Property ID:** {property_id[:8]}...")
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.write(f"**Status:** Reserved")

    with col2:
        st.subheader("📞 Contact Information")
        st.info("The property agent will contact you within 24 hours to discuss next steps.")

        st.subheader("📋 Next Steps")
        st.write("1. Upload financial documents")
        st.write("2. Schedule property inspection")
        st.write("3. Review purchase contract")
        st.write("4. Complete transaction")

    # Navigation buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏠 Browse More Properties"):
            clear_payment_session()
            st.rerun()

    with col2:
        if st.button("📋 View My Reservations"):
            clear_payment_session()
            st.session_state["show_buying_dashboard"] = True
            st.rerun()

    with col3:
        if st.button("💬 Contact Agent"):
            st.info("Agent contact feature coming soon!")


def validate_payment_form(card_number: str, card_name: str, expiry_date: str,
                          cvv: str, billing_address: str) -> tuple[bool, str]:
    """Validate payment form data"""

    # Card number validation
    if not card_number or len(card_number.replace(" ", "")) < 13:
        return False, "Please enter a valid card number"

    # Cardholder name validation
    if not card_name or len(card_name.strip()) < 2:
        return False, "Please enter cardholder name"

    # Expiry date validation (basic format check)
    if not expiry_date or len(expiry_date) != 5 or "/" not in expiry_date:
        return False, "Please enter expiry date in MM/YY format"

    # CVV validation
    if not cvv or len(cvv) < 3:
        return False, "Please enter a valid CVV"

    # Billing address validation
    if not billing_address or len(billing_address.strip()) < 5:
        return False, "Please enter billing address"

    return True, "Valid"


def clear_payment_session():
    """Clear payment-related session state"""
    keys_to_clear = [
        "payment_page_property",
        "payment_form_data",
        "payment_processing",
        "payment_successful",
        "buying_transaction_id",
        "reserved_property_id",
        "document_auto_generated"
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def integrate_payment_with_dashboard():
    """Integration helper for payment system with buyer dashboard"""
    if st.session_state.get("payment_page_property"):
        return True
    return False


def show_payment_demo():
    """Show payment system demo"""
    st.title("💳 Payment System Demo")

    show_payment_demo_info()

    # Mock property for demo
    mock_property_price = 250000.0
    show_payment_calculator(mock_property_price)

    st.info("This demo shows the payment interface. Use the 'Browse Properties' section to make actual reservations.")


# New enhanced functions for post-payment workflow
def show_post_payment_workflow_info():
    """Show information about what happens after payment"""
    st.subheader("🔄 Post-Payment Workflow")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Immediate Actions:**")
        st.write("✅ Property reserved in your name")
        st.write("📄 Reservation agreement auto-generated")
        st.write("💬 Chat system activated")
        st.write("📊 Progress tracking enabled")

    with col2:
        st.write("**Next 24-48 Hours:**")
        st.write("📞 Agent will contact you")
        st.write("📋 Document upload requests")
        st.write("🏠 Property inspection scheduling")
        st.write("⚖️ Notary assignment")


def get_reservation_summary(property_id: str, transaction_id: str) -> dict:
    """Get summary of reservation for display"""
    properties = get_properties()
    property_data = properties.get(property_id)

    if not property_data:
        return {}

    reservation_fee = property_data.price * Decimal("0.05")

    return {
        "property_title": property_data.title,
        "property_address": f"{property_data.address}, {property_data.city}",
        "total_price": float(property_data.price),
        "reservation_fee": float(reservation_fee),
        "remaining_amount": float(property_data.price - reservation_fee),
        "transaction_id": transaction_id,
        "reserved_date": datetime.now(),
        "agent_id": property_data.agent_id
    }


def show_reservation_summary(property_id: str, transaction_id: str):
    """Show detailed reservation summary"""
    summary = get_reservation_summary(property_id, transaction_id)

    if not summary:
        st.error("Unable to load reservation summary")
        return

    st.subheader("📋 Reservation Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Property:** {summary['property_title']}")
        st.write(f"**Location:** {summary['property_address']}")
        st.write(f"**Reserved:** {summary['reserved_date'].strftime('%Y-%m-%d %H:%M')}")

    with col2:
        st.write(f"**Total Price:** €{summary['total_price']:,.2f}")
        st.write(f"**Paid Today:** €{summary['reservation_fee']:,.2f}")
        st.write(f"**Due at Closing:** €{summary['remaining_amount']:,.2f}")