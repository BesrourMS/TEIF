import pdfplumber
from pydantic import ValidationError
import xml.etree.ElementTree as ET
from typing import List, Optional
from pydantic import BaseModel, Field


# ========================
# 1️⃣ PYDANTIC MODELS
# ========================

class MessageSenderIdentifier(BaseModel):
    type: str
    value: str


class MessageReceiverIdentifier(BaseModel):
    type: str
    value: str


class InvoiceHeader(BaseModel):
    MessageSenderIdentifier: MessageSenderIdentifier
    MessageReceiverIdentifier: MessageReceiverIdentifier


class DocumentType(BaseModel):
    code: str
    name: str


class Bgm(BaseModel):
    DocumentIdentifier: str
    DocumentType: DocumentType


class Dtm(BaseModel):
    functionCode: str
    format: str
    DateText: str


class PartnerIdentifier(BaseModel):
    type: str
    value: str


class PartnerName(BaseModel):
    value: str


class PartnerAddress(BaseModel):
    Street: Optional[str]
    CityName: Optional[str]
    PostalCode: Optional[str]
    Country: str


class Nad(BaseModel):
    PartnerIdentifier: PartnerIdentifier
    PartnerNom: PartnerName
    PartnerAdresses: List[PartnerAddress]


class PartnerDetails(BaseModel):
    functionCode: str
    Nad: Nad


class PartnerSection(BaseModel):
    PartnerDetails: List[PartnerDetails]


class LinItem(BaseModel):
    ItemIdentifier: str
    Description: str
    Quantity: float
    UnitPrice: float
    LineTotal: float


class LinSection(BaseModel):
    Lin: List[LinItem]


class AmountDetail(BaseModel):
    currencyCodeList: str
    amountTypeCode: str
    Amount: float


class InvoiceMoa(BaseModel):
    AmountDetails: List[AmountDetail]


class InvoiceTax(BaseModel):
    TaxTypeCode: str
    TaxRate: float
    TaxAmount: float


class TEIF(BaseModel):
    version: str
    controlingAgency: str
    InvoiceHeader: InvoiceHeader
    Bgm: Bgm
    Dtm: List[Dtm]
    PartnerSection: PartnerSection
    LinSection: List[LinSection]
    InvoiceMoa: InvoiceMoa
    InvoiceTax: InvoiceTax


# ========================
# 2️⃣ PARSE PDF (DEMO)
# ========================

def parse_pdf_invoice(pdf_path: str) -> dict:
    """
    Dummy extractor: in real-world, you'd detect text blocks properly.
    For now, hardcoded example mimicking extracted PDF fields.
    """
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages)

    # Demo extraction - replace with regex or NLP parsing
    return {
        "version": "2.0",
        "controlingAgency": "TTN",
        "InvoiceHeader": {
            "MessageSenderIdentifier": {"type": "I-01", "value": "1234567AAM000"},
            "MessageReceiverIdentifier": {"type": "I-01", "value": "7654321PBN000"}
        },
        "Bgm": {
            "DocumentIdentifier": "INV-2025-001",
            "DocumentType": {"code": "380", "name": "Facture"}
        },
        "Dtm": [
            {"functionCode": "137", "format": "DDMMYY", "DateText": "190825"}
        ],
        "PartnerSection": {
            "PartnerDetails": [
                {
                    "functionCode": "SU",
                    "Nad": {
                        "PartnerIdentifier": {"type": "I-01", "value": "1234567AAM000"},
                        "PartnerNom": {"value": "Tech Solutions SARL"},
                        "PartnerAdresses": [
                            {"Street": "Av. Habib Bourguiba", "CityName": "Tunis", "PostalCode": "1000", "Country": "TN"}
                        ]
                    }
                },
                {
                    "functionCode": "BY",
                    "Nad": {
                        "PartnerIdentifier": {"type": "I-01", "value": "7654321PBN000"},
                        "PartnerNom": {"value": "Alpha Distribution SA"},
                        "PartnerAdresses": [
                            {"Street": "Rue de Marseille", "CityName": "Sfax", "PostalCode": "3000", "Country": "TN"}
                        ]
                    }
                }
            ]
        },
        "LinSection": [
            {"Lin": [
                {"ItemIdentifier": "PRD-001", "Description": "Laptop", "Quantity": 2, "UnitPrice": 1200.0, "LineTotal": 2400.0},
                {"ItemIdentifier": "PRD-002", "Description": "Printer", "Quantity": 1, "UnitPrice": 600.0, "LineTotal": 600.0}
            ]}
        ],
        "InvoiceMoa": {
            "AmountDetails": [
                {"currencyCodeList": "TND", "amountTypeCode": "I-189", "Amount": 3000.0}
            ]
        },
        "InvoiceTax": {
            "TaxTypeCode": "I-1601", "TaxRate": 19.0, "TaxAmount": 570.0
        }
    }


# ========================
# 3️⃣ JSON → TEIF XML
# ========================

def teif_to_xml(teif: TEIF) -> str:
    root = ET.Element("TEIF", version=teif.version, controlingAgency=teif.controlingAgency)

    # Header
    header = ET.SubElement(root, "InvoiceHeader")
    sender = ET.SubElement(header, "MessageSenderIdentifier", type=teif.InvoiceHeader.MessageSenderIdentifier.type)
    sender.text = teif.InvoiceHeader.MessageSenderIdentifier.value
    receiver = ET.SubElement(header, "MessageReceiverIdentifier", type=teif.InvoiceHeader.MessageReceiverIdentifier.type)
    receiver.text = teif.InvoiceHeader.MessageReceiverIdentifier.value

    # Body
    body = ET.SubElement(root, "InvoiceBody")
    bgm = ET.SubElement(body, "Bgm")
    doc_id = ET.SubElement(bgm, "DocumentIdentifier")
    doc_id.text = teif.Bgm.DocumentIdentifier
    doc_type = ET.SubElement(bgm, "DocumentType", code=teif.Bgm.DocumentType.code)
    doc_type.text = teif.Bgm.DocumentType.name

    for dtm in teif.Dtm:
        dtm_el = ET.SubElement(body, "Dtm", functionCode=dtm.functionCode, format=dtm.format)
        date_text = ET.SubElement(dtm_el, "DateText")
        date_text.text = dtm.DateText

    # Lines
    for section in teif.LinSection:
        lin_section = ET.SubElement(body, "LinSection")
        for line in section.Lin:
            lin = ET.SubElement(lin_section, "Lin")
            ET.SubElement(lin, "ItemIdentifier").text = line.ItemIdentifier
            ET.SubElement(lin, "Description").text = line.Description
            ET.SubElement(lin, "Quantity").text = str(line.Quantity)
            ET.SubElement(lin, "UnitPrice").text = str(line.UnitPrice)
            ET.SubElement(lin, "LineTotal").text = str(line.LineTotal)

    # Totals
    moa = ET.SubElement(body, "InvoiceMoa")
    for amt in teif.InvoiceMoa.AmountDetails:
        amt_details = ET.SubElement(moa, "AmountDetails",
                                    currencyCodeList=amt.currencyCodeList,
                                    amountTypeCode=amt.amountTypeCode)
        ET.SubElement(amt_details, "Amount").text = str(amt.Amount)

    tax = ET.SubElement(body, "InvoiceTax")
    ET.SubElement(tax, "TaxTypeCode").text = teif.InvoiceTax.TaxTypeCode
    ET.SubElement(tax, "TaxRate").text = str(teif.InvoiceTax.TaxRate)
    ET.SubElement(tax, "TaxAmount").text = str(teif.InvoiceTax.TaxAmount)

    return ET.tostring(root, encoding="utf-8", pretty_print=True if hasattr(ET, "pretty_print") else False).decode("utf-8")


# ========================
# DEMO RUN
# ========================

if __name__ == "__main__":
    pdf_data = parse_pdf_invoice("invoice.pdf")  # Replace with real PDF
    try:
        teif_obj = TEIF(**pdf_data)
        xml_output = teif_to_xml(teif_obj)
        print(xml_output)
    except ValidationError as e:
        print("Validation error:", e.json())
