"""
Type definitions for TEIF XML invoice structure.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class TeifMessageIdentifier:
    """Represents a message identifier in TEIF."""
    type: str
    text: str


@dataclass
class TeifDateText:
    """Represents a date text element in TEIF."""
    format: str
    function_code: str
    text: str


@dataclass
class TeifDocumentType:
    """Represents a document type in TEIF."""
    code: str
    text: str


@dataclass
class TeifBgm:
    """Represents the Bgm section (document information)."""
    document_identifier: str
    document_type: TeifDocumentType


@dataclass
class TeifDtm:
    """Represents the Dtm section (dates)."""
    date_text: List[TeifDateText]


@dataclass
class TeifIdentifier:
    """Represents an identifier."""
    type: str
    text: str


@dataclass
class TeifPartnerName:
    """Represents a partner name."""
    name_type: str
    text: str


@dataclass
class TeifPartnerAddresses:
    """Represents partner addresses."""
    lang: str
    street_name: Optional[str] = None
    city_name: Optional[str] = None
    country_subdivision_code: Optional[str] = None
    post_code_identifier: Optional[str] = None
    country_identification_code: Optional[str] = None


@dataclass
class TeifNad:
    """Represents the Nad section (name and address)."""
    partner_identifier: TeifIdentifier
    partner_name: TeifPartnerName
    partner_addresses: Optional[TeifPartnerAddresses] = None


@dataclass
class TeifPartnerDetails:
    """Represents partner details."""
    function_code: str
    nad: TeifNad


@dataclass
class TeifPartnerSection:
    """Represents the partner section."""
    partner_details: List[TeifPartnerDetails]


@dataclass
class TeifLinQty:
    """Represents line quantity."""
    quantity: str
    unit_basis_quantity: Optional[str] = None


@dataclass
class TeifLinTax:
    """Represents line tax information."""
    tax_type_code: Optional[str] = None
    tax_category_code: Optional[str] = None
    tax_rate: Optional[str] = None


@dataclass
class TeifMoa:
    """Represents a monetary amount."""
    amount_type_code: str
    amount: str
    currency_code_list: Optional[str] = None


@dataclass
class TeifLinImd:
    """Represents line item description."""
    lang: str
    item_description: str


@dataclass
class TeifLinMoa:
    """Represents line monetary amounts."""
    unit_price_moa: Optional[TeifMoa] = None
    line_total_moa: Optional[TeifMoa] = None
    allowance_charge_moa: Optional[List[TeifMoa]] = None


@dataclass
class TeifLine:
    """Represents an invoice line."""
    item_identifier: str
    lin_imd: TeifLinImd
    lin_qty: Optional[TeifLinQty] = None
    lin_tax: Optional[TeifLinTax] = None
    lin_moa: Optional[TeifLinMoa] = None


@dataclass
class TeifLinSection:
    """Represents the line section."""
    lin: List[TeifLine]


@dataclass
class TeifAmountDetail:
    """Represents an amount detail."""
    moa: TeifMoa


@dataclass
class TeifInvoiceMoa:
    """Represents invoice monetary amounts."""
    amount_details: List[TeifAmountDetail]


@dataclass
class TeifTax:
    """Represents tax information."""
    tax_type_code: Optional[str] = None
    tax_category_code: Optional[str] = None
    tax_rate: Optional[str] = None


@dataclass
class TeifInvoiceTaxDetail:
    """Represents invoice tax details."""
    tax: TeifTax
    amount_details: Optional[List[TeifAmountDetail]] = None


@dataclass
class TeifInvoiceTax:
    """Represents the invoice tax section."""
    invoice_tax_details: List[TeifInvoiceTaxDetail]


@dataclass
class TeifInvoiceBody:
    """Represents the invoice body."""
    bgm: TeifBgm
    dtm: TeifDtm
    partner_section: TeifPartnerSection
    lin_section: TeifLinSection
    invoice_moa: Optional[TeifInvoiceMoa] = None
    invoice_tax: Optional[TeifInvoiceTax] = None
    pyt_section: Optional[Any] = None


@dataclass
class TeifInvoiceHeader:
    """Represents the invoice header."""
    message_sender_identifier: TeifMessageIdentifier
    message_receiver_identifier: TeifMessageIdentifier


@dataclass
class TeifInvoiceXml:
    """Root structure for TEIF invoice XML."""
    version: str
    controlling_agency: str
    invoice_header: TeifInvoiceHeader
    invoice_body: TeifInvoiceBody