import xml.etree.ElementTree as ET
import logging

_logger = logging.getLogger(__name__)

class XMLGenerator:
    """Generic XML Generator for Tally Requests."""

    @staticmethod
    def generate_partner_xml(partner, partner_type='Customer'):
        """Generates XML for a Customer or Vendor with full address and contact details."""
        root = ET.Element("ENVELOPE")
        header = ET.SubElement(root, "HEADER")
        tally_request = ET.SubElement(header, "TALLYREQUEST")
        tally_request.text = "Import Data"
        
        body = ET.SubElement(root, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        report_name = ET.SubElement(request_desc, "REPORTNAME")
        report_name.text = "All Masters"
        
        request_data = ET.SubElement(import_data, "REQUESTDATA")
        tally_message = ET.SubElement(request_data, "TALLYMESSAGE", attrib={"xmlns:UDF": "TallyUDF"})
        
        partner_name = (partner.name or '').strip()
        # ACTION="Alter" creates the ledger if it doesn't exist, and updates if it does, preventing duplicates.
        ledger = ET.SubElement(tally_message, "LEDGER", attrib={"NAME": partner_name, "ACTION": "Alter"})
        
        # Name tags
        name_elem = ET.SubElement(ledger, "NAME")
        name_elem.text = partner_name
        
        name_list = ET.SubElement(ledger, "NAME.LIST", attrib={"TYPE": "String"})
        name = ET.SubElement(name_list, "NAME")
        name.text = partner_name
        
        # Mailing name is essential for Tally's Mailing Details block
        mailing_list = ET.SubElement(ledger, "MAILINGNAME.LIST", attrib={"TYPE": "String"})
        m_name = ET.SubElement(mailing_list, "MAILINGNAME")
        m_name.text = partner_name
        
        group = ET.SubElement(ledger, "PARENT")
        group.text = "Sundry Debtors" if partner_type == 'Customer' else "Sundry Creditors"
        
        # Address source resolution (fallback to parent if individual contact has no address)
        addr_source = partner
        if not (partner.street or partner.street2 or partner.city) and partner.parent_id:
            if partner.parent_id.street or partner.parent_id.street2 or partner.parent_id.city:
                addr_source = partner.parent_id
        
        address_lines = []
        if addr_source.street:
            for line in addr_source.street.split('\n'):
                line = line.strip()
                if line:
                    address_lines.append(line)
        if addr_source.street2:
            for line in addr_source.street2.split('\n'):
                line = line.strip()
                if line:
                    address_lines.append(line)
        if addr_source.city:
            city_val = addr_source.city.strip()
            if city_val and city_val not in address_lines:
                address_lines.append(city_val)
        
        state_name = ((addr_source.state_id and addr_source.state_id.name) or (partner.state_id and partner.state_id.name) or '').strip()
        country_name = ((addr_source.country_id and addr_source.country_id.name) or (partner.country_id and partner.country_id.name) or '').strip()
        pincode = (addr_source.zip or partner.zip or '').strip()
        
        # Top-level Address and Location fields for Tally.ERP 9 / TallyPrime
        if address_lines:
            address_list = ET.SubElement(ledger, "ADDRESS.LIST", attrib={"TYPE": "String"})
            for line in address_lines[:4]:
                addr = ET.SubElement(address_list, "ADDRESS")
                addr.text = line
                
        if state_name:
            state = ET.SubElement(ledger, "STATENAME")
            state.text = state_name
            state2 = ET.SubElement(ledger, "LEDGERSTATENAME")
            state2.text = state_name
            
        if country_name:
            country = ET.SubElement(ledger, "COUNTRYNAME")
            country.text = country_name
            country2 = ET.SubElement(ledger, "COUNTRYOFRESIDENCE")
            country2.text = country_name
            
        if pincode:
            pincode_el = ET.SubElement(ledger, "PINCODE")
            pincode_el.text = pincode
        
        # TallyPrime Multiple Mailing Details (Required by TallyPrime to display address in ledger master)
        if address_lines or state_name or country_name or pincode:
            mailing_details = ET.SubElement(ledger, "LEDMAILINGDETAILS.LIST")
            app_from = ET.SubElement(mailing_details, "APPLICABLEFROM")
            app_from.text = "20200101"
            md_name = ET.SubElement(mailing_details, "MAILINGNAME")
            md_name.text = partner_name
            if address_lines:
                m_address_list = ET.SubElement(mailing_details, "ADDRESS.LIST", attrib={"TYPE": "String"})
                for line in address_lines[:4]:
                    m_addr = ET.SubElement(m_address_list, "ADDRESS")
                    m_addr.text = line
            if pincode:
                m_pin = ET.SubElement(mailing_details, "PINCODE")
                m_pin.text = pincode
            if state_name:
                m_state = ET.SubElement(mailing_details, "STATE")
                m_state.text = state_name
            if country_name:
                m_country = ET.SubElement(mailing_details, "COUNTRY")
                m_country.text = country_name
        
        # Contact Person
        contact_name = False
        if not partner.is_company:
            contact_name = partner.name
        elif partner.child_ids:
            contacts = partner.child_ids.filtered(lambda c: c.type == 'contact')
            if contacts:
                contact_name = contacts[0].name
            elif partner.child_ids:
                contact_name = partner.child_ids[0].name
        if contact_name:
            contact_el = ET.SubElement(ledger, "LEDGERCONTACT")
            contact_el.text = contact_name.strip()
            
        # Contact Numbers (Phone & Mobile)
        phone = (partner.phone or (partner.parent_id.phone if partner.parent_id else '') or '').strip()
        mobile = (partner.mobile or (partner.parent_id.mobile if partner.parent_id else '') or '').strip()
        if phone and mobile:
            phone_el = ET.SubElement(ledger, "LEDGERPHONE")
            phone_el.text = phone
            mobile_el = ET.SubElement(ledger, "LEDGERMOBILE")
            mobile_el.text = mobile
        elif phone:
            phone_el = ET.SubElement(ledger, "LEDGERPHONE")
            phone_el.text = phone
            mobile_el = ET.SubElement(ledger, "LEDGERMOBILE")
            mobile_el.text = phone
        elif mobile:
            phone_el = ET.SubElement(ledger, "LEDGERPHONE")
            phone_el.text = mobile
            mobile_el = ET.SubElement(ledger, "LEDGERMOBILE")
            mobile_el.text = mobile
            
        # Mail ID (Email)
        email_val = (partner.email or (partner.parent_id.email if partner.parent_id else '') or '').strip()
        if email_val:
            emails = [e.strip() for e in email_val.replace(';', ',').split(',') if e.strip()]
            if emails:
                email_el = ET.SubElement(ledger, "EMAIL")
                email_el.text = emails[0]
                if len(emails) > 1:
                    cc_el = ET.SubElement(ledger, "EMAILCC")
                    cc_el.text = emails[1]
                    
        # Website
        website_val = (partner.website or (partner.parent_id.website if partner.parent_id else '') or '').strip()
        if website_val:
            website_el = ET.SubElement(ledger, "WEBSITE")
            website_el.text = website_val
            
        # GST Details & PAN
        vat = (partner.vat or (partner.parent_id.vat if partner.parent_id else '') or '').strip()
        if vat:
            gstin = ET.SubElement(ledger, "PARTYGSTIN")
            gstin.text = vat
            reg_type = "Regular" if len(vat) == 15 else "Consumer"
            gst_type = ET.SubElement(ledger, "GSTREGISTRATIONTYPE")
            gst_type.text = reg_type
            
            # TallyPrime 3.0+ GST registration details
            gst_reg_list = ET.SubElement(ledger, "LEDGSTREGDETAILS.LIST")
            gst_app_from = ET.SubElement(gst_reg_list, "APPLICABLEFROM")
            gst_app_from.text = "20200101"
            gst_reg_type = ET.SubElement(gst_reg_list, "GSTREGISTRATIONTYPE")
            gst_reg_type.text = reg_type
            if state_name:
                gst_state = ET.SubElement(gst_reg_list, "STATE")
                gst_state.text = state_name
            gst_num = ET.SubElement(gst_reg_list, "GSTIN")
            gst_num.text = vat
            
            # 15-char Indian GSTIN contains 10-char PAN from 3rd to 12th char
            if len(vat) == 15 and vat[:2].isdigit():
                pan = ET.SubElement(ledger, "INCOMETAXNUMBER")
                pan.text = vat[2:12]
        
        return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

    @staticmethod
    def generate_sales_voucher_xml(invoice):
        """Generates XML for a Sales Voucher based on Odoo account.move journal items."""
        root = ET.Element("ENVELOPE")
        header = ET.SubElement(root, "HEADER")
        tally_request = ET.SubElement(header, "TALLYREQUEST")
        tally_request.text = "Import Data"
        
        body = ET.SubElement(root, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        report_name = ET.SubElement(request_desc, "REPORTNAME")
        report_name.text = "Vouchers"
        
        request_data = ET.SubElement(import_data, "REQUESTDATA")
        tally_message = ET.SubElement(request_data, "TALLYMESSAGE", attrib={"xmlns:UDF": "TallyUDF"})
        
        # ACTION="Create" to insert a new voucher in Tally Edit Log compliant manner.
        voucher = ET.SubElement(tally_message, "VOUCHER", attrib={"VCHTYPE": "Sales", "ACTION": "Create"})
        
        date = ET.SubElement(voucher, "DATE")
        inv_date = invoice.invoice_date or invoice.date
        date_str = inv_date.strftime("%Y%m%d") if inv_date else ""
        date.text = date_str
        
        effective_date = ET.SubElement(voucher, "EFFECTIVEDATE")
        effective_date.text = date_str
        
        vch_type_name = ET.SubElement(voucher, "VOUCHERTYPENAME")
        vch_type_name.text = "Sales"
        
        is_invoice = ET.SubElement(voucher, "ISINVOICE")
        is_invoice.text = "No"
        
        vch_num = ET.SubElement(voucher, "VOUCHERNUMBER")
        vch_num.text = invoice.name or "DRAFT"
        
        party_name = ET.SubElement(voucher, "PARTYLEDGERNAME")
        party_name.text = invoice.partner_id.name
        
        narration_text = invoice.narration or invoice.payment_reference or invoice.name or "Exported from Odoo"
        from odoo.tools import html2plaintext
        if '<' in narration_text and '>' in narration_text:
            narration_text = html2plaintext(narration_text)
            
        narration = ET.SubElement(voucher, "NARRATION")
        narration.text = str(narration_text)[:250]
        
        # Aggregate journal items by account to prevent Tally from overwriting duplicate ledger names
        party_ledger_data = None
        other_ledgers = {}
        
        for line in invoice.line_ids.filtered(lambda l: l.display_type not in ('line_section', 'line_note')):
            if not line.balance:
                continue
                
            if line.account_id.account_type in ('asset_receivable', 'liability_payable'):
                if not party_ledger_data:
                    party_ledger_data = {'name': invoice.partner_id.name, 'balance': 0.0}
                party_ledger_data['balance'] += line.balance
            else:
                acc_name = line.account_id.name
                if acc_name not in other_ledgers:
                    other_ledgers[acc_name] = 0.0
                other_ledgers[acc_name] += line.balance
                
        # To make sure Tally's Sales Register shows the Customer Name in the Particulars column 
        # when ISINVOICE=No, the Party Ledger MUST be the very first entry in the XML!
        if party_ledger_data and round(party_ledger_data['balance'], 2) != 0.0:
            ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ledger_name_el = ET.SubElement(ledger_entry, "LEDGERNAME")
            ledger_name_el.text = party_ledger_data['name']
            
            is_party_ledger = ET.SubElement(ledger_entry, "ISPARTYLEDGER")
            is_party_ledger.text = "Yes"
            
            is_deemed_positive = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
            is_deemed_positive.text = "Yes" if party_ledger_data['balance'] > 0 else "No"
            
            amount = ET.SubElement(ledger_entry, "AMOUNT")
            amount.text = str(-party_ledger_data['balance'])
            
        for acc_name, balance in other_ledgers.items():
            if round(balance, 2) == 0.0:
                continue
                
            ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ledger_name_el = ET.SubElement(ledger_entry, "LEDGERNAME")
            ledger_name_el.text = acc_name
            
            is_party_ledger = ET.SubElement(ledger_entry, "ISPARTYLEDGER")
            is_party_ledger.text = "No"
                
            is_deemed_positive = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
            is_deemed_positive.text = "Yes" if balance > 0 else "No"
            
            amount = ET.SubElement(ledger_entry, "AMOUNT")
            amount.text = str(-balance)
            
        return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

    @staticmethod
    def generate_credit_note_xml(credit_note):
        """Generates XML for a Credit Note Voucher (Customer Credit Note) based on Odoo account.move journal items."""
        root = ET.Element("ENVELOPE")
        header = ET.SubElement(root, "HEADER")
        tally_request = ET.SubElement(header, "TALLYREQUEST")
        tally_request.text = "Import Data"
        
        body = ET.SubElement(root, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        report_name = ET.SubElement(request_desc, "REPORTNAME")
        report_name.text = "Vouchers"
        
        request_data = ET.SubElement(import_data, "REQUESTDATA")
        tally_message = ET.SubElement(request_data, "TALLYMESSAGE", attrib={"xmlns:UDF": "TallyUDF"})
        
        # ACTION="Create" to insert a new voucher in Tally Edit Log compliant manner.
        voucher = ET.SubElement(tally_message, "VOUCHER", attrib={"VCHTYPE": "Credit Note", "ACTION": "Create"})
        
        date = ET.SubElement(voucher, "DATE")
        inv_date = credit_note.invoice_date or credit_note.date
        date_str = inv_date.strftime("%Y%m%d") if inv_date else ""
        date.text = date_str
        
        effective_date = ET.SubElement(voucher, "EFFECTIVEDATE")
        effective_date.text = date_str
        
        vch_type_name = ET.SubElement(voucher, "VOUCHERTYPENAME")
        vch_type_name.text = "Credit Note"
        
        is_invoice = ET.SubElement(voucher, "ISINVOICE")
        is_invoice.text = "No"
        
        vch_num = ET.SubElement(voucher, "VOUCHERNUMBER")
        vch_num.text = credit_note.name or "DRAFT"
        
        ref_val = credit_note.ref or (credit_note.reversed_entry_id.name if hasattr(credit_note, 'reversed_entry_id') and credit_note.reversed_entry_id else '')
        if ref_val:
            reference = ET.SubElement(voucher, "REFERENCE")
            reference.text = str(ref_val)[:50]
            party_invoice_no = ET.SubElement(voucher, "PARTYINVOICENO")
            party_invoice_no.text = str(ref_val)[:50]
            
        if hasattr(credit_note, 'reversed_entry_id') and credit_note.reversed_entry_id and credit_note.reversed_entry_id.invoice_date:
            party_invoice_date = ET.SubElement(voucher, "PARTYINVOICEDATE")
            party_invoice_date.text = credit_note.reversed_entry_id.invoice_date.strftime("%Y%m%d")
            
        party_name = ET.SubElement(voucher, "PARTYLEDGERNAME")
        party_name.text = credit_note.partner_id.name
        
        narration_text = credit_note.narration or credit_note.payment_reference or credit_note.ref or credit_note.name or "Customer Credit Note exported from Odoo"
        if '<' in narration_text and '>' in narration_text:
            try:
                from odoo.tools import html2plaintext
                narration_text = html2plaintext(narration_text)
            except ImportError:
                import re
                narration_text = re.sub(r'<[^>]+>', '', narration_text)
            
        narration = ET.SubElement(voucher, "NARRATION")
        narration.text = str(narration_text)[:250]
        
        # Aggregate journal items by account to prevent Tally from overwriting duplicate ledger names
        party_ledger_data = None
        other_ledgers = {}
        
        move_lines = credit_note.line_ids.filtered(lambda l: l.display_type not in ('line_section', 'line_note')) if hasattr(credit_note.line_ids, 'filtered') else credit_note.line_ids
        for line in move_lines:
            if not line.balance:
                continue
                
            if line.account_id.account_type in ('asset_receivable', 'liability_payable'):
                if not party_ledger_data:
                    party_ledger_data = {'name': credit_note.partner_id.name, 'balance': 0.0}
                party_ledger_data['balance'] += line.balance
            else:
                acc_name = line.account_id.name
                if acc_name not in other_ledgers:
                    other_ledgers[acc_name] = 0.0
                other_ledgers[acc_name] += line.balance
                
        # To make sure Tally's Credit Note Register shows the Customer Name in the Particulars column,
        # the Party Ledger MUST be the very first entry in the XML!
        if party_ledger_data and round(party_ledger_data['balance'], 2) != 0.0:
            ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ledger_name_el = ET.SubElement(ledger_entry, "LEDGERNAME")
            ledger_name_el.text = party_ledger_data['name']
            
            is_party_ledger = ET.SubElement(ledger_entry, "ISPARTYLEDGER")
            is_party_ledger.text = "Yes"
            
            is_deemed_positive = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
            is_deemed_positive.text = "Yes" if party_ledger_data['balance'] > 0 else "No"
            
            amount = ET.SubElement(ledger_entry, "AMOUNT")
            amount.text = str(-party_ledger_data['balance'])
            
        for acc_name, balance in other_ledgers.items():
            if round(balance, 2) == 0.0:
                continue
                
            ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ledger_name_el = ET.SubElement(ledger_entry, "LEDGERNAME")
            ledger_name_el.text = acc_name
            
            is_party_ledger = ET.SubElement(ledger_entry, "ISPARTYLEDGER")
            is_party_ledger.text = "No"
                
            is_deemed_positive = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
            is_deemed_positive.text = "Yes" if balance > 0 else "No"
            
            amount = ET.SubElement(ledger_entry, "AMOUNT")
            amount.text = str(-balance)
            
        return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

    @staticmethod
    def generate_purchase_voucher_xml(invoice):
        """Generates XML for a Purchase Voucher based on Odoo account.move journal items."""
        root = ET.Element("ENVELOPE")
        header = ET.SubElement(root, "HEADER")
        tally_request = ET.SubElement(header, "TALLYREQUEST")
        tally_request.text = "Import Data"
        
        body = ET.SubElement(root, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        report_name = ET.SubElement(request_desc, "REPORTNAME")
        report_name.text = "Vouchers"
        
        request_data = ET.SubElement(import_data, "REQUESTDATA")
        tally_message = ET.SubElement(request_data, "TALLYMESSAGE", attrib={"xmlns:UDF": "TallyUDF"})
        
        # ACTION="Create" to insert a new voucher in Tally Edit Log compliant manner.
        voucher = ET.SubElement(tally_message, "VOUCHER", attrib={"VCHTYPE": "Purchase", "ACTION": "Create"})
        
        date = ET.SubElement(voucher, "DATE")
        inv_date = invoice.invoice_date or invoice.date
        date_str = inv_date.strftime("%Y%m%d") if inv_date else ""
        date.text = date_str
        
        effective_date = ET.SubElement(voucher, "EFFECTIVEDATE")
        effective_date.text = date_str
        
        vch_type_name = ET.SubElement(voucher, "VOUCHERTYPENAME")
        vch_type_name.text = "Purchase"
        
        is_invoice = ET.SubElement(voucher, "ISINVOICE")
        is_invoice.text = "No"
        
        vch_num = ET.SubElement(voucher, "VOUCHERNUMBER")
        vch_num.text = invoice.name or "DRAFT"
        
        if invoice.ref:
            party_invoice_no = ET.SubElement(voucher, "PARTYINVOICENO")
            party_invoice_no.text = invoice.ref
            
            # The Supplier Invoice Date can also be set if it differs from accounting date. 
            # In Odoo, invoice_date is usually the supplier's date, and date is accounting date.
            if invoice.invoice_date:
                party_invoice_date = ET.SubElement(voucher, "PARTYINVOICEDATE")
                party_invoice_date.text = invoice.invoice_date.strftime("%Y%m%d")
        
        party_name = ET.SubElement(voucher, "PARTYLEDGERNAME")
        party_name.text = invoice.partner_id.name
        
        narration_text = invoice.narration or invoice.ref or invoice.name or "Exported from Odoo"
        from odoo.tools import html2plaintext
        if '<' in narration_text and '>' in narration_text:
            narration_text = html2plaintext(narration_text)
            
        narration = ET.SubElement(voucher, "NARRATION")
        narration.text = str(narration_text)[:250]
        
        # Aggregate journal items by account to prevent Tally from overwriting duplicate ledger names
        party_ledger_data = None
        other_ledgers = {}
        
        for line in invoice.line_ids.filtered(lambda l: l.display_type not in ('line_section', 'line_note')):
            if not line.balance:
                continue
                
            if line.account_id.account_type in ('asset_receivable', 'liability_payable'):
                if not party_ledger_data:
                    party_ledger_data = {'name': invoice.partner_id.name, 'balance': 0.0}
                party_ledger_data['balance'] += line.balance
            else:
                acc_name = line.account_id.name
                if acc_name not in other_ledgers:
                    other_ledgers[acc_name] = 0.0
                other_ledgers[acc_name] += line.balance
                
        # To make sure Tally's Purchase Register shows the Vendor Name in the Particulars column 
        # when ISINVOICE=No, the Party Ledger MUST be the very first entry in the XML!
        if party_ledger_data and round(party_ledger_data['balance'], 2) != 0.0:
            ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ledger_name_el = ET.SubElement(ledger_entry, "LEDGERNAME")
            ledger_name_el.text = party_ledger_data['name']
            
            is_party_ledger = ET.SubElement(ledger_entry, "ISPARTYLEDGER")
            is_party_ledger.text = "Yes"
            
            is_deemed_positive = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
            is_deemed_positive.text = "Yes" if party_ledger_data['balance'] > 0 else "No"
            
            amount = ET.SubElement(ledger_entry, "AMOUNT")
            amount.text = str(-party_ledger_data['balance'])
            
        for acc_name, balance in other_ledgers.items():
            if round(balance, 2) == 0.0:
                continue
                
            ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ledger_name_el = ET.SubElement(ledger_entry, "LEDGERNAME")
            ledger_name_el.text = acc_name
            
            is_party_ledger = ET.SubElement(ledger_entry, "ISPARTYLEDGER")
            is_party_ledger.text = "No"
                
            is_deemed_positive = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
            is_deemed_positive.text = "Yes" if balance > 0 else "No"
            
            amount = ET.SubElement(ledger_entry, "AMOUNT")
            amount.text = str(-balance)
            
        return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

    @staticmethod
    def generate_debit_note_xml(debit_note):
        """Generates XML for a Debit Note Voucher (Supplier Debit Note / Refund) based on Odoo account.move journal items."""
        root = ET.Element("ENVELOPE")
        header = ET.SubElement(root, "HEADER")
        tally_request = ET.SubElement(header, "TALLYREQUEST")
        tally_request.text = "Import Data"
        
        body = ET.SubElement(root, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        report_name = ET.SubElement(request_desc, "REPORTNAME")
        report_name.text = "Vouchers"
        
        request_data = ET.SubElement(import_data, "REQUESTDATA")
        tally_message = ET.SubElement(request_data, "TALLYMESSAGE", attrib={"xmlns:UDF": "TallyUDF"})
        
        # ACTION="Create" to insert a new voucher in Tally Edit Log compliant manner.
        voucher = ET.SubElement(tally_message, "VOUCHER", attrib={"VCHTYPE": "Debit Note", "ACTION": "Create"})
        
        date = ET.SubElement(voucher, "DATE")
        inv_date = debit_note.invoice_date or debit_note.date
        date_str = inv_date.strftime("%Y%m%d") if inv_date else ""
        date.text = date_str
        
        effective_date = ET.SubElement(voucher, "EFFECTIVEDATE")
        effective_date.text = date_str
        
        vch_type_name = ET.SubElement(voucher, "VOUCHERTYPENAME")
        vch_type_name.text = "Debit Note"
        
        is_invoice = ET.SubElement(voucher, "ISINVOICE")
        is_invoice.text = "No"
        
        vch_num = ET.SubElement(voucher, "VOUCHERNUMBER")
        vch_num.text = debit_note.name or "DRAFT"
        
        ref_val = debit_note.ref or (debit_note.reversed_entry_id.name if hasattr(debit_note, 'reversed_entry_id') and debit_note.reversed_entry_id else '')
        if ref_val:
            reference = ET.SubElement(voucher, "REFERENCE")
            reference.text = str(ref_val)[:50]
            party_invoice_no = ET.SubElement(voucher, "PARTYINVOICENO")
            party_invoice_no.text = str(ref_val)[:50]
            
        if hasattr(debit_note, 'reversed_entry_id') and debit_note.reversed_entry_id and debit_note.reversed_entry_id.invoice_date:
            party_invoice_date = ET.SubElement(voucher, "PARTYINVOICEDATE")
            party_invoice_date.text = debit_note.reversed_entry_id.invoice_date.strftime("%Y%m%d")
            
        party_name = ET.SubElement(voucher, "PARTYLEDGERNAME")
        party_name.text = debit_note.partner_id.name
        
        narration_text = debit_note.narration or debit_note.payment_reference or debit_note.ref or debit_note.name or "Supplier Debit Note exported from Odoo"
        if '<' in narration_text and '>' in narration_text:
            try:
                from odoo.tools import html2plaintext
                narration_text = html2plaintext(narration_text)
            except ImportError:
                import re
                narration_text = re.sub(r'<[^>]+>', '', narration_text)
            
        narration = ET.SubElement(voucher, "NARRATION")
        narration.text = str(narration_text)[:250]
        
        # Aggregate journal items by account to prevent Tally from overwriting duplicate ledger names
        party_ledger_data = None
        other_ledgers = {}
        
        move_lines = debit_note.line_ids.filtered(lambda l: l.display_type not in ('line_section', 'line_note')) if hasattr(debit_note.line_ids, 'filtered') else debit_note.line_ids
        for line in move_lines:
            if not line.balance:
                continue
                
            if line.account_id.account_type in ('asset_receivable', 'liability_payable'):
                if not party_ledger_data:
                    party_ledger_data = {'name': debit_note.partner_id.name, 'balance': 0.0}
                party_ledger_data['balance'] += line.balance
            else:
                acc_name = line.account_id.name
                if acc_name not in other_ledgers:
                    other_ledgers[acc_name] = 0.0
                other_ledgers[acc_name] += line.balance
                
        # To make sure Tally's Debit Note Register shows the Vendor Name in the Particulars column,
        # the Party Ledger MUST be the very first entry in the XML!
        if party_ledger_data and round(party_ledger_data['balance'], 2) != 0.0:
            ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ledger_name_el = ET.SubElement(ledger_entry, "LEDGERNAME")
            ledger_name_el.text = party_ledger_data['name']
            
            is_party_ledger = ET.SubElement(ledger_entry, "ISPARTYLEDGER")
            is_party_ledger.text = "Yes"
            
            is_deemed_positive = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
            is_deemed_positive.text = "Yes" if party_ledger_data['balance'] > 0 else "No"
            
            amount = ET.SubElement(ledger_entry, "AMOUNT")
            amount.text = str(-party_ledger_data['balance'])
            
        for acc_name, balance in other_ledgers.items():
            if round(balance, 2) == 0.0:
                continue
                
            ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ledger_name_el = ET.SubElement(ledger_entry, "LEDGERNAME")
            ledger_name_el.text = acc_name
            
            is_party_ledger = ET.SubElement(ledger_entry, "ISPARTYLEDGER")
            is_party_ledger.text = "No"
                
            is_deemed_positive = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
            is_deemed_positive.text = "Yes" if balance > 0 else "No"
            
            amount = ET.SubElement(ledger_entry, "AMOUNT")
            amount.text = str(-balance)
            
        return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

    @staticmethod
    def generate_product_xml(product):
        """Generates XML for a Product (Stock Item). Uses Alter to avoid duplicates."""
        root = ET.Element("ENVELOPE")
        header = ET.SubElement(root, "HEADER")
        tally_request = ET.SubElement(header, "TALLYREQUEST")
        tally_request.text = "Import Data"
        
        body = ET.SubElement(root, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        report_name = ET.SubElement(request_desc, "REPORTNAME")
        report_name.text = "All Masters"
        
        request_data = ET.SubElement(import_data, "REQUESTDATA")
        tally_message = ET.SubElement(request_data, "TALLYMESSAGE", attrib={"xmlns:UDF": "TallyUDF"})
        
        stock_item = ET.SubElement(tally_message, "STOCKITEM", attrib={"NAME": product.display_name, "ACTION": "Alter"})
        
        name_list = ET.SubElement(stock_item, "NAME.LIST", attrib={"TYPE": "String"})
        name = ET.SubElement(name_list, "NAME")
        name.text = product.display_name
        
        # Base unit is required by Tally in most cases. If missing, it might fail.
        base_units = ET.SubElement(stock_item, "BASEUNITS")
        base_units.text = product.uom_id.name if product.uom_id else "Nos"
        
        if product.standard_price:
            std_cost = ET.SubElement(stock_item, "STANDARDCOST")
            std_cost.text = str(product.standard_price)
            
        if product.list_price:
            std_price = ET.SubElement(stock_item, "STANDARDPRICE")
            std_price.text = str(product.list_price)
            
        return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

    @staticmethod
    def get_bank_cash_ledger_name(journal):
        """Resolves the Tally Bank or Cash ledger name from an Odoo account.journal."""
        if not journal:
            return "Bank"
        
        # 1. Custom Tally Ledger Name set on journal
        if hasattr(journal, 'tally_ledger_name') and journal.tally_ledger_name:
            name = journal.tally_ledger_name.strip()
            if name:
                return name
                
        # 2. Cash journal in Tally is predefined as "Cash"
        journal_type = getattr(journal, 'type', None)
        if journal_type == 'cash':
            return "Cash"
            
        # 3. Check journal's default account name if it is not an interim account
        default_account = getattr(journal, 'default_account_id', None)
        if default_account and default_account.name:
            acc_name = default_account.name.strip()
            if 'outstanding' not in acc_name.lower() and acc_name not in ('Outstanding Payments', 'Outstanding Receipts'):
                return acc_name
                
        # 4. Use journal name if it doesn't contain 'outstanding'
        journal_name = getattr(journal, 'name', '') or ''
        if journal_name and 'outstanding' not in journal_name.lower():
            return journal_name.strip()
            
        return "Bank"

    @staticmethod
    def generate_simple_ledger_xml(ledger_name, parent_group="Bank Accounts"):
        """Generates minimal XML to ensure a Master Ledger exists in Tally using ACTION='Alter'."""
        root = ET.Element("ENVELOPE")
        header = ET.SubElement(root, "HEADER")
        tally_request = ET.SubElement(header, "TALLYREQUEST")
        tally_request.text = "Import Data"
        
        body = ET.SubElement(root, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        report_name = ET.SubElement(request_desc, "REPORTNAME")
        report_name.text = "All Masters"
        
        request_data = ET.SubElement(import_data, "REQUESTDATA")
        tally_message = ET.SubElement(request_data, "TALLYMESSAGE", attrib={"xmlns:UDF": "TallyUDF"})
        
        ledger_name_str = (ledger_name or '').strip()
        ledger = ET.SubElement(tally_message, "LEDGER", attrib={"NAME": ledger_name_str, "ACTION": "Alter"})
        
        name_elem = ET.SubElement(ledger, "NAME")
        name_elem.text = ledger_name_str
        
        name_list = ET.SubElement(ledger, "NAME.LIST", attrib={"TYPE": "String"})
        name = ET.SubElement(name_list, "NAME")
        name.text = ledger_name_str
        
        parent = ET.SubElement(ledger, "PARENT")
        parent.text = parent_group
        
        return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

    @staticmethod
    def generate_receipt_voucher_xml(payment):
        """Generates XML for a Receipt / Payment Voucher based on Odoo account.payment."""
        root = ET.Element("ENVELOPE")
        header = ET.SubElement(root, "HEADER")
        tally_request = ET.SubElement(header, "TALLYREQUEST")
        tally_request.text = "Import Data"
        
        body = ET.SubElement(root, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        request_desc = ET.SubElement(import_data, "REQUESTDESC")
        report_name = ET.SubElement(request_desc, "REPORTNAME")
        report_name.text = "Vouchers"
        
        request_data = ET.SubElement(import_data, "REQUESTDATA")
        tally_message = ET.SubElement(request_data, "TALLYMESSAGE", attrib={"xmlns:UDF": "TallyUDF"})
        
        vch_type = "Receipt" if payment.payment_type == 'inbound' else "Payment"
        voucher = ET.SubElement(tally_message, "VOUCHER", attrib={"VCHTYPE": vch_type, "ACTION": "Create"})
        
        date = ET.SubElement(voucher, "DATE")
        inv_date = payment.date
        date_str = inv_date.strftime("%Y%m%d") if inv_date else ""
        date.text = date_str
        
        effective_date = ET.SubElement(voucher, "EFFECTIVEDATE")
        effective_date.text = date_str
        
        vch_type_name = ET.SubElement(voucher, "VOUCHERTYPENAME")
        vch_type_name.text = vch_type
        
        is_invoice = ET.SubElement(voucher, "ISINVOICE")
        is_invoice.text = "No"
        
        vch_num = ET.SubElement(voucher, "VOUCHERNUMBER")
        vch_num.text = payment.name or "DRAFT"
        
        party_name_str = payment.partner_id.name if payment.partner_id else ""
        party_name = ET.SubElement(voucher, "PARTYLEDGERNAME")
        party_name.text = party_name_str
        
        narration = ET.SubElement(voucher, "NARRATION")
        memo = payment.memo if hasattr(payment, 'memo') else getattr(payment, 'ref', '')
        default_narration = f"Payment from {party_name_str}" if payment.payment_type == 'inbound' else f"Payment to {party_name_str}"
        narration.text = memo or default_narration
        
        # Aggregate journal items by account so the Party Ledger is placed as the VERY FIRST entry
        party_ledger_data = None
        other_ledgers = {}
        
        move_lines = payment.move_id.line_ids.filtered(lambda l: l.display_type not in ('line_section', 'line_note')) if hasattr(payment.move_id.line_ids, 'filtered') else payment.move_id.line_ids
        for line in move_lines:
            if not line.balance:
                continue
                
            if line.account_id.account_type in ('asset_receivable', 'liability_payable') and payment.partner_id:
                if not party_ledger_data:
                    party_ledger_data = {'name': party_name_str, 'balance': 0.0}
                party_ledger_data['balance'] += line.balance
            else:
                acc_name = (line.account_id.name or '').strip()
                # In Odoo 18, bank/cash payments post to interim accounts like 'Outstanding Payments' or 'Outstanding Receipts'.
                # Tally vouchers must reference the actual Bank or Cash ledger, not Odoo's internal interim account.
                if 'outstanding' in acc_name.lower() or acc_name in ('Outstanding Payments', 'Outstanding Receipts') or (payment.journal_id and line.account_id == payment.journal_id.default_account_id):
                    acc_name = XMLGenerator.get_bank_cash_ledger_name(payment.journal_id)
                
                if acc_name not in other_ledgers:
                    other_ledgers[acc_name] = 0.0
                other_ledgers[acc_name] += line.balance
                
        # Fallback if lines did not match receivable/payable account types
        if not party_ledger_data and payment.partner_id:
            party_balance = -payment.amount if payment.payment_type == 'inbound' else payment.amount
            party_ledger_data = {'name': party_name_str, 'balance': party_balance}
            
        # Fallback if other_ledgers is empty
        if not other_ledgers and payment.journal_id:
            bank_ledger_name = XMLGenerator.get_bank_cash_ledger_name(payment.journal_id)
            bank_balance = payment.amount if payment.payment_type == 'inbound' else -payment.amount
            other_ledgers[bank_ledger_name] = bank_balance
            
        # To make sure Tally's Voucher Register (Receipt / Payment Register) shows the Customer / Vendor Name
        # in the Particulars column, the Party Ledger MUST be the very first entry in ALLLEDGERENTRIES.LIST!
        if party_ledger_data and round(party_ledger_data['balance'], 2) != 0.0:
            ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ledger_name_el = ET.SubElement(ledger_entry, "LEDGERNAME")
            ledger_name_el.text = party_ledger_data['name']
            
            is_party_ledger = ET.SubElement(ledger_entry, "ISPARTYLEDGER")
            is_party_ledger.text = "Yes"
            
            is_deemed_positive = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
            is_deemed_positive.text = "Yes" if party_ledger_data['balance'] > 0 else "No"
            
            amount = ET.SubElement(ledger_entry, "AMOUNT")
            amount.text = str(-party_ledger_data['balance'])
            
        for acc_name, balance in other_ledgers.items():
            if round(balance, 2) == 0.0:
                continue
                
            ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ledger_name_el = ET.SubElement(ledger_entry, "LEDGERNAME")
            ledger_name_el.text = acc_name
            
            is_party_ledger = ET.SubElement(ledger_entry, "ISPARTYLEDGER")
            is_party_ledger.text = "No"
                
            is_deemed_positive = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
            is_deemed_positive.text = "Yes" if balance > 0 else "No"
            
            amount = ET.SubElement(ledger_entry, "AMOUNT")
            amount.text = str(-balance)
            
        return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')

    @staticmethod
    def generate_payment_voucher_xml(payment):
        """Generates XML for a Payment Voucher (Supplier Payment) based on Odoo account.payment."""
        return XMLGenerator.generate_receipt_voucher_xml(payment)
