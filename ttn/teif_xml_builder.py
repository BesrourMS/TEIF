"""
Clean & reliable TEIF XML Builder (using standard library - no more dicttoxml problems)
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
from teif_types import TeifInvoiceXml


class TeifXmlBuilder:
    """Builds correct TEIF XML without <False> or <key> tags."""

    @staticmethod
    def build_teif_xml(teif_data: TeifInvoiceXml) -> str:
        """Generate properly formatted TEIF XML."""
        # Root element
        root = ET.Element("TEIF")
        root.set("version", teif_data.version)
        root.set("controllingAgency", teif_data.controlling_agency)   # fixed typo

        # InvoiceHeader
        header = ET.SubElement(root, "InvoiceHeader")
        TeifXmlBuilder._add_identifier(header, "MessageSenderIdentifier",
                                       teif_data.invoice_header.message_sender_identifier)
        TeifXmlBuilder._add_identifier(header, "MessageReceiverIdentifier",   # fixed typo
                                       teif_data.invoice_header.message_receiver_identifier)

        # InvoiceBody
        body = ET.SubElement(root, "InvoiceBody")
        TeifXmlBuilder._build_body(body, teif_data.invoice_body)

        # Convert to pretty XML
        rough_string = ET.tostring(root, encoding="utf-8", method="xml")
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="    ")

        # Clean up (remove extra blank lines)
        clean_lines = [line for line in pretty_xml.split("\n") if line.strip()]
        return "\n".join(clean_lines)

    @staticmethod
    def _add_identifier(parent, tag: str, ident):
        elem = ET.SubElement(parent, tag)
        elem.set("type", ident.type)
        elem.text = ident.text

    @staticmethod
    def _build_body(body_elem, body):
        # Bgm
        bgm = ET.SubElement(body_elem, "Bgm")
        ET.SubElement(bgm, "DocumentIdentifier").text = body.bgm.document_identifier
        doc_type = ET.SubElement(bgm, "DocumentType")
        doc_type.set("code", body.bgm.document_type.code)
        doc_type.text = body.bgm.document_type.text

        # Dtm (multiple DateText)
        dtm = ET.SubElement(body_elem, "Dtm")
        for dt in body.dtm.date_text:
            d = ET.SubElement(dtm, "DateText")
            d.set("format", dt.format)
            d.set("functionCode", dt.function_code)
            d.text = dt.text

        # PartnerSection
        partner_sec = ET.SubElement(body_elem, "PartnerSection")
        for p in body.partner_section.partner_details:
            pd = ET.SubElement(partner_sec, "PartnerDetails")
            pd.set("functionCode", p.function_code)

            nad = ET.SubElement(pd, "Nad")
            # PartnerIdentifier
            pid = ET.SubElement(nad, "PartnerIdentifier")
            pid.set("type", p.nad.partner_identifier.type)
            pid.text = p.nad.partner_identifier.text
            # PartnerName
            pname = ET.SubElement(nad, "PartnerName")
            pname.set("nameType", p.nad.partner_name.name_type)
            pname.text = p.nad.partner_name.text
            # PartnerAdresses
            if p.nad.partner_addresses:
                pa = ET.SubElement(nad, "PartnerAdresses")
                pa.set("lang", p.nad.partner_addresses.lang)
                if p.nad.partner_addresses.street_name:
                    ET.SubElement(pa, "StreetName").text = p.nad.partner_addresses.street_name
                if p.nad.partner_addresses.city_name:
                    ET.SubElement(pa, "CityName").text = p.nad.partner_addresses.city_name
                if p.nad.partner_addresses.country_identification_code:
                    ET.SubElement(pa, "CountryIdentificationCode").text = p.nad.partner_addresses.country_identification_code

        # LinSection
        lin_sec = ET.SubElement(body_elem, "LinSection")
        for line in body.lin_section.lin:
            TeifXmlBuilder._build_line(lin_sec, line)

        # InvoiceMoa
        if body.invoice_moa:
            TeifXmlBuilder._build_invoice_moa(body_elem, body.invoice_moa)

        # InvoiceTax
        if body.invoice_tax:
            TeifXmlBuilder._build_invoice_tax(body_elem, body.invoice_tax)

    @staticmethod
    def _build_line(parent, line):
        lin = ET.SubElement(parent, "Lin")
        ET.SubElement(lin, "ItemIdentifier").text = line.item_identifier

        # LinImd
        imd = ET.SubElement(lin, "LinImd")
        imd.set("lang", line.lin_imd.lang)
        ET.SubElement(imd, "ItemDescription").text = line.lin_imd.item_description

        # LinQty
        if line.lin_qty:
            qty = ET.SubElement(lin, "LinQty")
            ET.SubElement(qty, "Quantity").text = line.lin_qty.quantity

        # LinTax
        if line.lin_tax:
            tax = ET.SubElement(lin, "LinTax")
            if line.lin_tax.tax_type_code:
                ET.SubElement(tax, "TaxTypeCode").text = line.lin_tax.tax_type_code
            if line.lin_tax.tax_rate:
                ET.SubElement(tax, "TaxRate").text = line.lin_tax.tax_rate

        # LinMoa
        if line.lin_moa:
            moa_elem = ET.SubElement(lin, "LinMoa")
            if line.lin_moa.unit_price_moa:
                up = ET.SubElement(moa_elem, "UnitPriceMoa")
                up.set("amountTypeCode", line.lin_moa.unit_price_moa.amount_type_code)
                if line.lin_moa.unit_price_moa.currency_code_list:
                    up.set("currencyCodeList", line.lin_moa.unit_price_moa.currency_code_list)
                ET.SubElement(up, "Amount").text = line.lin_moa.unit_price_moa.amount

            if line.lin_moa.line_total_moa:
                lt = ET.SubElement(moa_elem, "LineTotalMoa")
                lt.set("amountTypeCode", line.lin_moa.line_total_moa.amount_type_code)
                if line.lin_moa.line_total_moa.currency_code_list:
                    lt.set("currencyCodeList", line.lin_moa.line_total_moa.currency_code_list)
                ET.SubElement(lt, "Amount").text = line.lin_moa.line_total_moa.amount

    @staticmethod
    def _build_invoice_moa(parent, moa):
        moa_elem = ET.SubElement(parent, "InvoiceMoa")
        for detail in moa.amount_details:
            m = ET.SubElement(moa_elem, "Moa")          # repeated Moa (no <item>)
            m.set("amountTypeCode", detail.moa.amount_type_code)
            if detail.moa.currency_code_list:
                m.set("currencyCodeList", detail.moa.currency_code_list)
            ET.SubElement(m, "Amount").text = detail.moa.amount

    @staticmethod
    def _build_invoice_tax(parent, tax):
        tax_elem = ET.SubElement(parent, "InvoiceTax")
        for detail in tax.invoice_tax_details:
            td = ET.SubElement(tax_elem, "InvoiceTaxDetails")
            t = ET.SubElement(td, "Tax")
            if detail.tax.tax_type_code:
                ET.SubElement(t, "TaxTypeCode").text = detail.tax.tax_type_code
            if detail.tax.tax_rate:
                ET.SubElement(t, "TaxRate").text = detail.tax.tax_rate

            if detail.amount_details:
                for ad in detail.amount_details:
                    m = ET.SubElement(td, "Moa")
                    m.set("amountTypeCode", ad.moa.amount_type_code)
                    if ad.moa.currency_code_list:
                        m.set("currencyCodeList", ad.moa.currency_code_list)
                    ET.SubElement(m, "Amount").text = ad.moa.amount