"""
Automatic Document Generation System
Handles creation of reservation agreements and contracts after payment success
"""

import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional

from gpp.classes.buying import Buying, add_document_to_buying, add_transaction_note
from gpp.classes.document import Document
from gpp.interface.utils.database import save_document, get_properties, get_agents, get_buyers
from gpp.interface.utils.buying_database import save_buying_transaction
from gpp.interface.config.constants import ENHANCED_BUYING_DOCUMENT_TYPES


def generate_reservation_agreement(buying_obj: Buying) -> bool:
    """
    Generate reservation agreement after successful payment
    This is called automatically when payment is processed
    """
    try:
        # Get transaction details
        properties = get_properties()
        agents = get_agents()
        buyers = get_buyers()

        property_data = properties.get(buying_obj.property_id)
        agent_data = agents.get(buying_obj.agent_id)
        buyer_data = buyers.get(buying_obj.buyer_id)

        if not all([property_data, agent_data, buyer_data]):
            return False

        # Generate reservation agreement content
        agreement_content = _create_reservation_agreement_content(
            property_data, agent_data, buyer_data, buying_obj
        )

        # Create document file
        filename = f"reservation_agreement_{buying_obj.buying_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        file_path = os.path.join("data", "files", "buying_documents", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write agreement content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(agreement_content)

        # Create document record
        doc = Document(
            document_name=f"Reservation Agreement - {property_data.title}",
            document_path=file_path,
            upload_id="system",
            validation_status=True,  # Auto-validated since system generated
            visibility=True
        )
        save_document(doc)

        # Add to buying transaction
        add_document_to_buying(buying_obj, "reservation_agreement", doc.document_id)

        # Add transaction note
        add_transaction_note(
            buying_obj,
            "Reservation Agreement automatically generated after successful payment",
            "system",
            "document_upload"
        )

        # Update phase to reservation (ensure we're in the right phase)
        if buying_obj.current_phase != "reservation":
            from gpp.classes.buying import advance_workflow_phase
            advance_workflow_phase(buying_obj, "reservation", "system")

        save_buying_transaction(buying_obj)
        return True

    except Exception as e:
        print(f"Error generating reservation agreement: {e}")
        return False


def _create_reservation_agreement_content(property_data, agent_data, buyer_data, buying_obj: Buying) -> str:
    """Create the content for reservation agreement"""

    reservation_fee = buying_obj.final_price * Decimal(
        "0.05") if buying_obj.final_price else property_data.price * Decimal("0.05")

    content = f"""
PROPERTY RESERVATION AGREEMENT

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Transaction ID: {buying_obj.buying_id}

=== PROPERTY DETAILS ===
Property: {property_data.title}
Address: {property_data.address}, {property_data.city}
Size: {property_data.dimension}
Price: €{property_data.price:,.2f}

=== PARTIES ===
AGENT:
- ID: {agent_data.agent_id}
- Contact: {getattr(agent_data, 'contact_info', 'N/A')}

BUYER:
- ID: {buyer_data.buyer_id}
- Contact: {getattr(buyer_data, 'contact_info', 'N/A')}

=== RESERVATION TERMS ===
1. The buyer hereby reserves the above property for purchase
2. Reservation fee paid: €{reservation_fee:,.2f} (5% of property price)
3. Reservation valid for 30 days from date of payment
4. Total purchase price: €{buying_obj.final_price or property_data.price:,.2f}

=== NEXT STEPS ===
1. Buyer must provide proof of funds or mortgage pre-approval
2. Notary will prepare preliminary contract
3. Deposit payment required upon preliminary contract signing
4. Final contract and payment to complete purchase

=== TERMS AND CONDITIONS ===
- This reservation is binding upon payment of reservation fee
- Buyer has 30 days to complete financial verification
- Property is removed from market during reservation period
- Reservation fee will be applied to final purchase price
- If buyer fails to proceed, reservation fee may be forfeited

DIGITAL SIGNATURES REQUIRED:
- Buyer: {buyer_data.buyer_id}
- Agent: {agent_data.agent_id}

Generated by GPP - Global Property Platform
""".strip()

    return content


def generate_preliminary_contract(buying_obj: Buying, notary_id: str,
                                  contract_terms: str = "", special_conditions: str = "") -> bool:
    """
    Generate preliminary contract by notary
    """
    try:
        # Get transaction details
        properties = get_properties()
        agents = get_agents()
        buyers = get_buyers()

        property_data = properties.get(buying_obj.property_id)
        agent_data = agents.get(buying_obj.agent_id)
        buyer_data = buyers.get(buying_obj.buyer_id)

        if not all([property_data, agent_data, buyer_data]):
            return False

        # Generate preliminary contract content
        contract_content = _create_preliminary_contract_content(
            property_data, agent_data, buyer_data, buying_obj,
            contract_terms, special_conditions
        )

        # Create document file
        filename = f"preliminary_contract_{buying_obj.buying_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        file_path = os.path.join("data", "files", "buying_documents", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write contract content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(contract_content)

        # Create document record
        doc = Document(
            document_name=f"Preliminary Contract - {property_data.title}",
            document_path=file_path,
            upload_id=notary_id,
            validation_status=True,  # Auto-validated since notary generated
            visibility=True
        )
        save_document(doc)

        # Add to buying transaction
        add_document_to_buying(buying_obj, "preliminary_contract", doc.document_id)

        # Add transaction note
        add_transaction_note(
            buying_obj,
            f"Preliminary Contract generated by notary. Terms: {contract_terms[:100]}...",
            notary_id,
            "document_upload"
        )

        save_buying_transaction(buying_obj)
        return True

    except Exception as e:
        print(f"Error generating preliminary contract: {e}")
        return False


def _create_preliminary_contract_content(property_data, agent_data, buyer_data, buying_obj: Buying,
                                         contract_terms: str, special_conditions: str) -> str:
    """Create the content for preliminary contract"""

    deposit_amount = buying_obj.final_price * Decimal(
        "0.10") if buying_obj.final_price else property_data.price * Decimal("0.10")

    content = f"""
PRELIMINARY PURCHASE CONTRACT

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Transaction ID: {buying_obj.buying_id}
Contract prepared by: Notary

=== PROPERTY DETAILS ===
Property: {property_data.title}
Address: {property_data.address}, {property_data.city}
Size: {property_data.dimension}
Agreed Purchase Price: €{buying_obj.final_price or property_data.price:,.2f}

=== CONTRACTING PARTIES ===
SELLER (represented by Agent):
- Agent ID: {agent_data.agent_id}
- Contact: {getattr(agent_data, 'contact_info', 'N/A')}

BUYER:
- ID: {buyer_data.buyer_id}
- Contact: {getattr(buyer_data, 'contact_info', 'N/A')}

=== CONTRACT TERMS ===
1. PURCHASE PRICE: €{buying_obj.final_price or property_data.price:,.2f}
2. DEPOSIT REQUIRED: €{deposit_amount:,.2f} (10% of purchase price)
3. DEPOSIT DUE: Within 7 days of contract signing
4. COMPLETION DATE: 30 days from deposit payment

{f"ADDITIONAL TERMS:{chr(10)}{contract_terms}" if contract_terms else ""}

{f"SPECIAL CONDITIONS:{chr(10)}{special_conditions}" if special_conditions else ""}

=== DEPOSIT PAYMENT TERMS ===
- Deposit amount: €{deposit_amount:,.2f}
- Payment method: Bank transfer or certified check
- Deposit held in escrow until completion
- Upon completion, deposit applied to final purchase price

=== CONDITIONS PRECEDENT ===
1. Buyer's final mortgage approval (if applicable)
2. Satisfactory property inspection
3. Clear title verification
4. All legal requirements met

=== DEFAULT PROVISIONS ===
- If buyer defaults: Deposit may be forfeited
- If seller defaults: Deposit returned with damages
- Specific performance may be enforced

=== COMPLETION REQUIREMENTS ===
1. Final payment of remaining balance
2. All legal documents executed
3. Property keys and possession transferred
4. Title registered in buyer's name

DIGITAL SIGNATURES REQUIRED:
- Notary: (Document preparer)
- Buyer: {buyer_data.buyer_id}
- Agent: {agent_data.agent_id} (on behalf of seller)

This contract is governed by local property law.
Generated by GPP - Global Property Platform
""".strip()

    return content


def generate_final_purchase_contract(buying_obj: Buying, notary_id: str) -> bool:
    """
    Generate final purchase contract by notary
    """
    try:
        # Get transaction details
        properties = get_properties()
        agents = get_agents()
        buyers = get_buyers()

        property_data = properties.get(buying_obj.property_id)
        agent_data = agents.get(buying_obj.agent_id)
        buyer_data = buyers.get(buying_obj.buyer_id)

        if not all([property_data, agent_data, buyer_data]):
            return False

        # Generate final contract content
        contract_content = _create_final_contract_content(
            property_data, agent_data, buyer_data, buying_obj
        )

        # Create document file
        filename = f"final_contract_{buying_obj.buying_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        file_path = os.path.join("data", "files", "buying_documents", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write contract content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(contract_content)

        # Create document record
        doc = Document(
            document_name=f"Final Purchase Contract - {property_data.title}",
            document_path=file_path,
            upload_id=notary_id,
            validation_status=True,  # Auto-validated since notary generated
            visibility=True
        )
        save_document(doc)

        # Add to buying transaction
        add_document_to_buying(buying_obj, "final_purchase_contract", doc.document_id)

        # Add transaction note
        add_transaction_note(
            buying_obj,
            "Final Purchase Contract generated by notary",
            notary_id,
            "document_upload"
        )

        save_buying_transaction(buying_obj)
        return True

    except Exception as e:
        print(f"Error generating final contract: {e}")
        return False


def _create_final_contract_content(property_data, agent_data, buyer_data, buying_obj: Buying) -> str:
    """Create the content for final purchase contract"""

    final_payment = buying_obj.final_price - (
                buying_obj.final_price * Decimal("0.15")) if buying_obj.final_price else property_data.price * Decimal(
        "0.85")

    content = f"""
FINAL PURCHASE CONTRACT

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Transaction ID: {buying_obj.buying_id}
Contract prepared by: Notary

=== PROPERTY DETAILS ===
Property: {property_data.title}
Address: {property_data.address}, {property_data.city}
Size: {property_data.dimension}
Final Purchase Price: €{buying_obj.final_price or property_data.price:,.2f}

=== CONTRACTING PARTIES ===
SELLER (represented by Agent):
- Agent ID: {agent_data.agent_id}
- Contact: {getattr(agent_data, 'contact_info', 'N/A')}

BUYER:
- ID: {buyer_data.buyer_id}
- Contact: {getattr(buyer_data, 'contact_info', 'N/A')}

=== FINANCIAL SUMMARY ===
Total Purchase Price: €{buying_obj.final_price or property_data.price:,.2f}
Less: Reservation Fee: €{(buying_obj.final_price or property_data.price) * Decimal('0.05'):,.2f}
Less: Deposit Paid: €{(buying_obj.final_price or property_data.price) * Decimal('0.10'):,.2f}
FINAL PAYMENT DUE: €{final_payment:,.2f}

=== COMPLETION TERMS ===
1. Final payment due on execution of this contract
2. Property keys transferred upon payment
3. Possession granted immediately upon completion
4. Title registration to be completed within 30 days

=== WARRANTIES AND REPRESENTATIONS ===
1. Property sold "as is" with all fixtures
2. Seller warrants clear title and right to sell
3. All utilities and services to be transferred
4. Property taxes current as of completion date

=== CLOSING CONDITIONS ===
1. All prior contracts and agreements superseded
2. Transaction subject to notarial supervision
3. Title insurance recommended
4. Final walkthrough completed satisfactorily

=== LEGAL COMPLETION ===
This contract represents the final and complete agreement between parties.
Upon execution and payment, ownership transfers to buyer.
All legal requirements have been verified and satisfied.

DIGITAL SIGNATURES REQUIRED:
- Notary: (Contract supervisor)
- Buyer: {buyer_data.buyer_id}
- Agent: {agent_data.agent_id} (on behalf of seller)

CONTRACT EXECUTION DATE: {datetime.now().strftime('%Y-%m-%d')}
Generated by GPP - Global Property Platform
""".strip()

    return content


def generate_notary_validation_certificate(buying_obj: Buying, notary_id: str) -> bool:
    """
    Generate notary validation certificate for final completion
    """
    try:
        # Get transaction details
        properties = get_properties()
        property_data = properties.get(buying_obj.property_id)

        if not property_data:
            return False

        # Generate certificate content
        certificate_content = _create_validation_certificate_content(
            property_data, buying_obj, notary_id
        )

        # Create document file
        filename = f"notary_certificate_{buying_obj.buying_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        file_path = os.path.join("data", "files", "buying_documents", filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write certificate content to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(certificate_content)

        # Create document record
        doc = Document(
            document_name=f"Notary Validation Certificate - {property_data.title}",
            document_path=file_path,
            upload_id=notary_id,
            validation_status=True,  # Auto-validated since notary generated
            visibility=True
        )
        save_document(doc)

        # Add to buying transaction
        add_document_to_buying(buying_obj, "notary_validation_certificate", doc.document_id)

        # Add transaction note
        add_transaction_note(
            buying_obj,
            "Notary Validation Certificate generated - Transaction ready for completion",
            notary_id,
            "document_upload"
        )

        save_buying_transaction(buying_obj)
        return True

    except Exception as e:
        print(f"Error generating validation certificate: {e}")
        return False


def _create_validation_certificate_content(property_data, buying_obj: Buying, notary_id: str) -> str:
    """Create the content for notary validation certificate"""

    content = f"""
NOTARY VALIDATION CERTIFICATE

Certificate ID: CERT_{buying_obj.buying_id}_{datetime.now().strftime('%Y%m%d_%H%M')}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Transaction ID: {buying_obj.buying_id}

=== NOTARIAL CERTIFICATION ===
I, as authorized notary, hereby certify that:

=== PROPERTY TRANSACTION DETAILS ===
Property: {property_data.title}
Address: {property_data.address}, {property_data.city}
Transaction Value: €{buying_obj.final_price or property_data.price:,.2f}
Transaction Phase: {buying_obj.current_phase}

=== DOCUMENT VALIDATION STATUS ===
All required documents have been reviewed and validated:
✓ Reservation Agreement - Signed and verified
✓ Financial Documents - Reviewed and approved
✓ Preliminary Contract - Executed and filed
✓ Due Diligence - Completed satisfactorily
✓ Final Purchase Contract - Executed and notarized

=== LEGAL COMPLIANCE VERIFICATION ===
✓ All parties have legal capacity to contract
✓ Property title is clear and marketable
✓ All financial requirements have been met
✓ Transaction complies with applicable laws
✓ All signatures are authentic and witnessed

=== FINAL CERTIFICATION ===
This transaction has been completed in accordance with:
- Local property transfer laws
- Notarial supervision requirements
- Financial compliance standards
- Due diligence requirements

TRANSACTION STATUS: LEGALLY COMPLETE
EFFECTIVE DATE: {datetime.now().strftime('%Y-%m-%d')}

=== NOTARIAL SEAL ===
Notary ID: {notary_id}
Digital Signature Required: ✓
Date of Certification: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This certificate serves as official confirmation that the property transaction
has been completed in accordance with all legal requirements.

CERTIFIED BY GPP - Global Property Platform
Notarial Services Division
""".strip()

    return content


# Integration function for payment system
def trigger_post_payment_document_generation(buying_obj: Buying) -> bool:
    """
    Called after successful payment to generate reservation agreement
    This integrates with your existing payment system
    """
    return generate_reservation_agreement(buying_obj)