/**
 * @class TEIFValidator
 * @description A JavaScript class to validate a nested invoice object against the TEIF specification.
 * This version handles a hierarchical data structure that mirrors the XML format.
 */
class TEIFValidator {
    /**
     * @param {object} invoiceData - The invoice data as a nested JavaScript object.
     */
    constructor(invoiceData) {
        this.invoice = invoiceData;
        this.errors = [];
        
        // Regex for the Tunisian Matricule Fiscal format.
        // Example: 1234567A/B/M/000
        this.taxIdRegex = /^\d{7}[A-Z]\/[A-Z]\/[A-Z]\/\d{3}$/;

        // Known codes from the TEIF specification document.
        this.knownCodes = {
            partnerFunctions: ['I-61', 'I-62'], // I-61: Buyer, I-62: Supplier
            documentTypes: ['I-11'], // I-11: Facture
            dateFunctions: ['I-31'], // I-31: Date d'émission du document
            amountTypes: ['I-176', 'I-181', 'I-180', 'I-171', 'I-183'], // Totals, Line Net, Line Unit Price
            taxTypes: ['I-1602'] // I-1602: TVA
        };
    }

    /**
     * Runs all validation checks on the nested invoice object.
     * @returns {{isValid: boolean, errors: string[]}}
     */
    validate() {
        this.errors = []; // Reset errors

        this._validateRoot();
        this._validateHeader();
        this._validateBgmAndDtm();
        this._validatePartners();
        this._validateLines();
        this._validateTotals();

        return {
            isValid: this.errors.length === 0,
            errors: this.errors,
        };
    }

    _addError(message) {
        this.errors.push(message);
    }

    _validateRoot() {
        if (this.invoice.version !== '2.0') {
            this._addError("Root: TEIF version must be '2.0'.");
        }
        if (this.invoice.controlingAgency !== 'TTN') {
            this._addError("Root: 'controlingAgency' must be 'TTN'.");
        }
    }

    _validateHeader() {
        const header = this.invoice.InvoiceHeader;
        if (!header) {
            this._addError("Structure: 'InvoiceHeader' object is missing.");
            return;
        }

        const sender = header.MessageSenderIdentifier;
        if (!sender || !sender.value) {
            this._addError("Header: Sender 'MessageSenderIdentifier' is missing or empty.");
        } else if (!this.taxIdRegex.test(sender.value)) {
            this._addError(`Header: Sender Tax ID '${sender.value}' has an invalid format.`);
        }

        const receiver = header.MessageReceiverIdentifier;
        if (!receiver || !receiver.value) {
            this._addError("Header: Receiver 'MessageReceiverIdentifier' is missing or empty.");
        } else if (!this.taxIdRegex.test(receiver.value)) {
            this._addError(`Header: Receiver Tax ID '${receiver.value}' has an invalid format.`);
        }
    }

    _validateBgmAndDtm() {
        if (!this.invoice.Bgm || !this.invoice.Bgm.DocumentIdentifier) {
            this._addError("Body: 'Bgm.DocumentIdentifier' (Invoice ID) is missing.");
        }
        if (this.invoice.Bgm?.DocumentType?.code !== 'I-11') {
             this._addError("Body: 'Bgm.DocumentType.code' must be 'I-11' for an invoice.");
        }

        const issueDate = this.invoice.Dtm?.find(d => d.functionCode === 'I-31');
        if (!issueDate) {
            this._addError("Body: 'Dtm' entry with functionCode 'I-31' (Issue Date) is missing.");
        }
    }

    _validatePartners() {
        const partners = this.invoice.PartnerSection?.PartnerDetails;
        if (!partners || !Array.isArray(partners) || partners.length < 2) {
            this._addError("Partners: 'PartnerSection.PartnerDetails' must be an array with at least a supplier and a buyer.");
            return;
        }

        const supplier = partners.find(p => p.functionCode === 'I-62');
        if (!supplier) {
            this._addError("Partners: A supplier with functionCode 'I-62' is required.");
        } else if (!supplier.Nad?.PartnerIdentifier?.value || !supplier.Nad?.PartnerNom?.value) {
            this._addError("Partners: Supplier is missing 'PartnerIdentifier' or 'PartnerNom'.");
        }

        const buyer = partners.find(p => p.functionCode === 'I-61');
        if (!buyer) {
            this._addError("Partners: A buyer with functionCode 'I-61' is required.");
        } else if (!buyer.Nad?.PartnerIdentifier?.value || !buyer.Nad?.PartnerNom?.value) {
            this._addError("Partners: Buyer is missing 'PartnerIdentifier' or 'PartnerNom'.");
        }
    }

    _validateLines() {
        const lines = this.invoice.LinSection?.[0]?.Lin;
        if (!lines || !Array.isArray(lines) || lines.length === 0) {
            this._addError("Lines: 'LinSection[0].Lin' must be an array with at least one line item.");
            return;
        }

        lines.forEach((line, index) => {
            if (!line.ItemIdentifier || !line.Description) {
                this._addError(`Line ${index + 1}: 'ItemIdentifier' or 'Description' is missing.`);
            }
            if (typeof line.Quantity !== 'number' || line.Quantity <= 0) {
                this._addError(`Line ${index + 1}: 'Quantity' must be a positive number.`);
            }
            if (typeof line.UnitPrice !== 'number' || line.UnitPrice < 0) {
                this._addError(`Line ${index + 1}: 'UnitPrice' must be a non-negative number.`);
            }
        });
    }

    _validateTotals() {
        const amounts = this.invoice.InvoiceMoa?.AmountDetails;
        if (!amounts || !Array.isArray(amounts)) {
            this._addError("Totals: 'InvoiceMoa.AmountDetails' array is missing.");
            return;
        }

        const totalHT = amounts.find(a => a.amountTypeCode === 'I-176');
        if (!totalHT) {
            this._addError("Totals: Amount with type 'I-176' (Total HT) is missing.");
        }

        const totalTTC = amounts.find(a => a.amountTypeCode === 'I-180');
        if (!totalTTC) {
            this._addError("Totals: Amount with type 'I-180' (Total TTC) is missing.");
        }

        const taxInfo = this.invoice.InvoiceTax;
        if(!taxInfo){
             this._addError("Tax: 'InvoiceTax' object is missing.");
        } else if (taxInfo.TaxTypeCode !== 'I-1602') { // I-1602 for TVA
             this._addError("Tax: 'TaxTypeCode' for main tax should be 'I-1602' (TVA).");
        }
    }
}


// --- EXAMPLE USAGE ---

// This data structure matches the user's provided format, but uses the correct codes from the TEIF guide.
const validInvoiceData = {
    "version": "2.0",
    "controlingAgency": "TTN",
    "InvoiceHeader": {
        "MessageSenderIdentifier": { "type": "I-01", "value": "1234567A/B/M/000" },
        "MessageReceiverIdentifier": { "type": "I-01", "value": "7654321C/D/N/000" }
    },
    "Bgm": {
        "DocumentIdentifier": "INV-2025-001",
        "DocumentType": { "code": "I-11", "name": "Facture" } // Correct code for Invoice
    },
    "Dtm": [
        { "functionCode": "I-31", "format": "DDMMYY", "DateText": "190825" } // Correct code for Issue Date
    ],
    "PartnerSection": {
        "PartnerDetails": [
            {
                "functionCode": "I-62", // Correct code for Supplier
                "Nad": {
                    "PartnerIdentifier": { "type": "I-01", "value": "1234567A/B/M/000" },
                    "PartnerNom": { "value": "Tech Solutions SARL" },
                    "PartnerAdresses": [{ "CityName": "Tunis", "Country": "TN" }]
                }
            },
            {
                "functionCode": "I-61", // Correct code for Buyer
                "Nad": {
                    "PartnerIdentifier": { "type": "I-01", "value": "7654321C/D/N/000" },
                    "PartnerNom": { "value": "Alpha Distribution SA" },
                    "PartnerAdresses": [{ "CityName": "Sfax", "Country": "TN" }]
                }
            }
        ]
    },
    "LinSection": [{
        "Lin": [
            { "ItemIdentifier": "PRD-001", "Description": "Laptop", "Quantity": 2, "UnitPrice": 1200.0, "LineTotal": 2400.0 },
            { "ItemIdentifier": "PRD-002", "Description": "Printer", "Quantity": 1, "UnitPrice": 600.0, "LineTotal": 600.0 }
        ]
    }],
    "InvoiceMoa": {
        "AmountDetails": [
            { "amountTypeCode": "I-176", "Amount": 3000.0 }, // Total HT
            { "amountTypeCode": "I-180", "Amount": 3570.0 }  // Total TTC
        ]
    },
    "InvoiceTax": {
        "TaxTypeCode": "I-1602", // Correct code for TVA
        "TaxRate": 19.0,
        "TaxAmount": 570.0
    }
};

// --- RUN VALIDATION ---
console.log("--- Validating a correct nested invoice ---");
const validator = new TEIFValidator(validInvoiceData);
const result = validator.validate();

console.log("Is Valid:", result.isValid);
if (!result.isValid) {
    console.log("Errors:", result.errors);
}
