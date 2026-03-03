"""
Maps invoice JSON/dict data to TEIF XML structure.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from teif_types import (
    TeifInvoiceXml, TeifInvoiceHeader, TeifMessageIdentifier,
    TeifInvoiceBody, TeifBgm, TeifDocumentType, TeifDtm, TeifDateText,
    TeifPartnerSection, TeifPartnerDetails, TeifNad, TeifIdentifier,
    TeifPartnerName, TeifPartnerAddresses, TeifLinSection, TeifLine,
    TeifLinImd, TeifLinQty, TeifLinTax, TeifLinMoa, TeifMoa,
    TeifInvoiceMoa, TeifAmountDetail, TeifInvoiceTax, TeifInvoiceTaxDetail,
    TeifTax
)


def format_amount(value: float) -> str:
    """Format amount to 3 decimal places."""
    return f"{value:.3f}"


def format_date_for_teif(date_input: str | datetime) -> str:
    """
    Format date to TEIF format (ddMMyy).
    
    Args:
        date_input: Date as string (YYYY-MM-DD) or datetime object
        
    Returns:
        Formatted date string (ddMMyy)
    """
    if isinstance(date_input, str):
        date_obj = datetime.strptime(date_input, "%Y-%m-%d")
    else:
        date_obj = date_input
    
    day = f"{date_obj.day:02d}"
    month = f"{date_obj.month:02d}"
    year = f"{date_obj.year % 100:02d}"
    
    return f"{day}{month}{year}"


def calculate_subtotal(lines: List[Dict[str, Any]]) -> float:
    """Calculate subtotal from invoice lines."""
    return sum(line['quantity'] * line['unitPrice']['amount'] for line in lines)


def calculate_tax_total(lines: List[Dict[str, Any]]) -> float:
    """Calculate total tax from invoice lines."""
    total = 0
    for line in lines:
        line_total = line['quantity'] * line['unitPrice']['amount']
        tax_amount = (line_total * line['taxRate']) / 100
        total += tax_amount
    return total


def calculate_grand_total(subtotal: float, tax_total: float) -> float:
    """Calculate grand total (subtotal + tax)."""
    return subtotal + tax_total


def build_partner_details(function_code: str, party: Dict[str, Any]) -> TeifPartnerDetails:
    """Build partner details from party information."""
    return TeifPartnerDetails(
        function_code=function_code,
        nad=TeifNad(
            partner_identifier=TeifIdentifier(
                type="I-01",
                text=party['identifier']
            ),
            partner_name=TeifPartnerName(
                name_type="Qualification",
                text=party['name']
            ),
            partner_addresses=TeifPartnerAddresses(
                lang="fr",
                street_name=party.get('address', {}).get('street'),
                city_name=party.get('address', {}).get('city'),
                country_identification_code=party.get('address', {}).get('country')
            )
        )
    )


def build_line(line_number: int, line: Dict[str, Any]) -> TeifLine:
    """Build a single invoice line."""
    line_total = line['quantity'] * line['unitPrice']['amount']
    
    return TeifLine(
        item_identifier=str(line_number),
        lin_imd=TeifLinImd(
            lang="fr",
            item_description=line['description']
        ),
        lin_qty=TeifLinQty(
            quantity=format_amount(line['quantity'])
        ),
        lin_tax=TeifLinTax(
            tax_type_code="VAT",
            tax_rate=format_amount(line['taxRate'])
        ),
        lin_moa=TeifLinMoa(
            unit_price_moa=TeifMoa(
                amount_type_code="I-179",
                amount=format_amount(line['unitPrice']['amount']),
                currency_code_list="ISO_4217"
            ),
            line_total_moa=TeifMoa(
                amount_type_code="I-180",
                amount=format_amount(line_total),
                currency_code_list="ISO_4217"
            )
        )
    )


def build_invoice_moa(subtotal: float, tax_total: float, grand_total: float) -> TeifInvoiceMoa:
    """Build invoice monetary amounts."""
    return TeifInvoiceMoa(
        amount_details=[
            TeifAmountDetail(
                moa=TeifMoa(
                    amount_type_code="I-179",
                    amount=format_amount(subtotal),
                    currency_code_list="ISO_4217"
                )
            ),
            TeifAmountDetail(
                moa=TeifMoa(
                    amount_type_code="I-180",
                    amount=format_amount(tax_total),
                    currency_code_list="ISO_4217"
                )
            ),
            TeifAmountDetail(
                moa=TeifMoa(
                    amount_type_code="I-176",
                    amount=format_amount(grand_total),
                    currency_code_list="ISO_4217"
                )
            )
        ]
    )


def build_invoice_tax(lines: List[Dict[str, Any]]) -> TeifInvoiceTax:
    """Build invoice tax details, aggregating by tax rate."""
    tax_map: Dict[float, Dict[str, float]] = {}
    
    for line in lines:
        rate = line['taxRate']
        line_total = line['quantity'] * line['unitPrice']['amount']
        tax_amount = (line_total * rate) / 100
        
        if rate in tax_map:
            tax_map[rate]['amount'] += tax_amount
        else:
            tax_map[rate] = {'amount': tax_amount, 'rate': rate}
    
    tax_details: List[TeifInvoiceTaxDetail] = []
    for tax in tax_map.values():
        tax_details.append(
            TeifInvoiceTaxDetail(
                tax=TeifTax(
                    tax_type_code="VAT",
                    tax_rate=format_amount(tax['rate'])
                ),
                amount_details=[
                    TeifAmountDetail(
                        moa=TeifMoa(
                            amount_type_code="I-181",
                            amount=format_amount(tax['amount']),
                            currency_code_list="ISO_4217"
                        )
                    )
                ]
            )
        )
    
    return TeifInvoiceTax(invoice_tax_details=tax_details)


def map_invoice_to_teif_xml(invoice_data: Dict[str, Any]) -> TeifInvoiceXml:
    """
    Convert invoice data to TEIF XML structure.
    
    Args:
        invoice_data: Invoice data dictionary containing:
            - header: Document header info (documentNumber, issueDate, type)
            - seller: Seller info (identifier, name, address)
            - buyer: Buyer info (identifier, name, address)
            - lines: List of invoice lines
            - totals: Invoice totals (optional, can be calculated)
            
    Returns:
        TeifInvoiceXml object ready to be converted to XML
    """
    subtotal = calculate_subtotal(invoice_data['lines'])
    tax_total = calculate_tax_total(invoice_data['lines'])
    grand_total = calculate_grand_total(subtotal, tax_total)
    
    return TeifInvoiceXml(
        version="1.8.8",
        controlling_agency="TTN",
        invoice_header=TeifInvoiceHeader(
            message_sender_identifier=TeifMessageIdentifier(
                type="I-01",
                text=invoice_data['seller']['identifier']
            ),
            message_receiver_identifier=TeifMessageIdentifier(
                type="I-01",
                text=invoice_data['buyer']['identifier']
            )
        ),
        invoice_body=TeifInvoiceBody(
            bgm=TeifBgm(
                document_identifier=invoice_data['header']['documentNumber'],
                document_type=TeifDocumentType(
                    code="I-11",
                    text="Facture"
                )
            ),
            dtm=TeifDtm(
                date_text=[
                    TeifDateText(
                        format="ddMMyy",
                        function_code="I-31",
                        text=format_date_for_teif(invoice_data['header']['issueDate'])
                    ),
                    TeifDateText(
                        format="ddMMyy",
                        function_code="I-32",
                        text=format_date_for_teif(invoice_data['header']['issueDate'])
                    )
                ]
            ),
            partner_section=TeifPartnerSection(
                partner_details=[
                    build_partner_details("I-62", invoice_data['seller']),
                    build_partner_details("I-64", invoice_data['buyer'])
                ]
            ),
            lin_section=TeifLinSection(
                lin=[build_line(i + 1, line) for i, line in enumerate(invoice_data['lines'])]
            ),
            invoice_moa=build_invoice_moa(subtotal, tax_total, grand_total),
            invoice_tax=build_invoice_tax(invoice_data['lines'])
        )
    )