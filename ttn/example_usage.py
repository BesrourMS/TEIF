"""
Example of how to use the TEIF XML generator.
"""
from map_json_to_teif import map_invoice_to_teif_xml
from teif_xml_builder import TeifXmlBuilder


# Sample invoice data
invoice_data = {
    'header': {
        'documentNumber': 'INV-001',
        'issueDate': '2024-01-15',
        'type': 'INVOICE'
    },
    'seller': {
        'name': 'Seller Corp',
        'identifier': 'TAX123456',
        'identifierType': 'FISCAL_ID',
        'address': {
            'street': '123 Main St',
            'city': 'Cairo',
            'country': 'EG'
        }
    },
    'buyer': {
        'name': 'Buyer Inc',
        'identifier': 'TAX654321',
        'identifierType': 'FISCAL_ID',
        'address': {
            'street': '456 Oak Ave',
            'city': 'Giza',
            'country': 'EG'
        }
    },
    'lines': [
        {
            'lineNumber': 1,
            'description': 'Product A',
            'quantity': 2,
            'unitPrice': {'amount': 100, 'currency': 'EGP'},
            'taxRate': 14
        },
        {
            'lineNumber': 2,
            'description': 'Service B',
            'quantity': 1,
            'unitPrice': {'amount': 50, 'currency': 'EGP'},
            'taxRate': 14
        }
    ],
    'totals': {
        'subtotalHT': {'amount': 260, 'currency': 'EGP'},
        'totalTax': {'amount': 36.4, 'currency': 'EGP'},
        'totalTTC': {'amount': 296.4, 'currency': 'EGP'}
    }
}


def main():
    """Generate TEIF XML from invoice data."""
    # Map invoice data to TEIF structure
    teif_data = map_invoice_to_teif_xml(invoice_data)
    
    # Build XML string
    xml_output = TeifXmlBuilder.build_teif_xml(teif_data)
    
    # Print or save the XML
    print(xml_output)
    
    # Optionally save to file
    with open('invoice.xml', 'w', encoding='utf-8') as f:
        f.write(xml_output)
    
    print("\nXML file saved to invoice.xml")


if __name__ == "__main__":
    main()