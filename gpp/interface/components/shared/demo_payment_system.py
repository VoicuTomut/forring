"""
Demo Payment System for Property Reservations
Handles fake payment processing for demonstration purposes
"""

import streamlit as st
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import time
from typing import Dict, Any

from gpp.classes.property import Property
from gpp.classes.buyer import Buyer
from gpp.classes.buying import create_buying_transaction, add_transaction_note
from gpp.interface.utils.database import save_property, get_properties
from gpp.interface.utils.buying_database import save_buying_transaction


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
                _handle_successful_payment(property_id, property_data, current_buyer,
                                         payment_result, reservation_fee)
            else:
                st.error(f"❌ Payment failed: {payment_result['error']}")
                st.info("💡 Demo tip: Card numbers starting with '4000' will be declined")


def _handle_successful_payment(property_id: str, property_data: Property, current_buyer: Buyer,
                             payment_result: Dict[str, Any], reservation_fee: Decimal):
    """Handle successful payment and start buying process"""

    st.success("🎉 Payment Successful!")
    st.success(f"💰 Reservation fee of €{reservation_fee:,.2f} has been processed")
    st.info(f"📄 Transaction ID: {payment_result['transaction_id']}")

    try:
        # Reserve the property
        property_data.reserved = True
        property_data.status = "reserved"
        save_property(property_data)

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

        # Update session state
        st.session_state["payment_successful"] = True
        st.session_state["buying_transaction_id"] = buying_transaction.buying_id
        st.session_state["reserved_property_id"] = property_id

        # Show next steps
        st.markdown("---")
        st.subheader("📋 Next Steps")

        col1, col2 = st.columns(2)

        with col1:
            st.info("""
            **What happens next:**
            1. Property is now reserved for you
            2. Agent will prepare buying documents
            3. You'll need to upload additional documents
            4. Notary will validate all documents
            5. Final contract signing and completion
            """)

        with col2:
            st.success("""
            **Your buying process has started!**
            - Go to "My Purchases" tab to track progress
            - Upload required documents when requested
            - Communicate with agent and notary via chat
            """)

        # Action buttons (outside of any form)
        st.markdown("### 🎯 Next Steps")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📋 View Buying Process", key="view_buying_process"):
                st.session_state["selected_transaction"] = buying_transaction.buying_id
                st.session_state["show_buying_details"] = True
                st.rerun()

        with col2:
            if st.button("💬 Start Chat", key="start_chat_process"):
                st.session_state["start_buying_chat"] = property_id
                st.rerun()

        with col3:
            if st.button("🏠 Back to Properties", key="back_to_properties"):
                # Clear payment session state
                if "payment_page_property" in st.session_state:
                    del st.session_state["payment_page_property"]
                st.rerun()

    except Exception as e:
        st.error(f"❌ Error processing reservation: {str(e)}")
        st.info("Payment was successful, but there was an error creating the buying process. Please contact support.")


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
        
        **No real money is processed in this demo system.**
        """)