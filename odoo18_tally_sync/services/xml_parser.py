import xml.etree.ElementTree as ET
import logging

_logger = logging.getLogger(__name__)

class XMLParser:
    """Generic XML Parser for Tally Responses."""

    @staticmethod
    def sanitize_xml(xml_string):
        if not xml_string:
            return xml_string
        import re
        # Remove invalid XML character references (e.g. &#x4;, &#x0;, &#11;)
        # Valid XML 1.0 chars: #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
        xml_string = re.sub(r'&#x(?:[0-8BCEF]|1[0-9A-F]);', '', xml_string, flags=re.IGNORECASE)
        xml_string = re.sub(r'&#(?:[0-8]|1[12]|1[4-9]|2[0-9]|3[01]);', '', xml_string)
        # Also strip literal control characters
        xml_string = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml_string)
        return xml_string

    @staticmethod
    def parse_response(xml_string):
        """Parses Tally XML response into a Python dictionary."""
        try:
            if not xml_string:
                return {}
            
            xml_string = XMLParser.sanitize_xml(xml_string)
            root = ET.fromstring(xml_string)
            result = {}
            for child in root:
                result[child.tag] = child.text
            return result
        except ET.ParseError as e:
            _logger.error("Failed to parse XML response: %s", str(e))
            return {}

    @staticmethod
    def parse_ledgers(xml_string, group_filter=None):
        """Extracts ledgers from Tally List of Accounts XML."""
        ledgers = []
        try:
            if not xml_string:
                return ledgers
            
            xml_string = XMLParser.sanitize_xml(xml_string)
            root = ET.fromstring(xml_string)
            for ledger in root.iter('LEDGER'):
                name_elem = ledger.attrib.get('NAME') or ledger.findtext('NAME') or ''
                if not name_elem:
                    name_list = ledger.find('NAME.LIST')
                    if name_list is not None:
                        name_elem = name_list.findtext('NAME') or ''
                
                parent = ledger.findtext('PARENT') or ''
                
                if not name_elem or not parent:
                    continue
                
                if group_filter and group_filter.lower() not in parent.lower():
                    continue
                
                email = ledger.findtext('EMAIL') or ''
                phone = ledger.findtext('LEDGERPHONE') or ledger.findtext('PHONE') or ''
                mobile = ledger.findtext('LEDGERMOBILE') or ledger.findtext('MOBILE') or ''
                
                # Extract address lines if available
                address_lines = []
                address_list = ledger.find('ADDRESS.LIST')
                if address_list is not None:
                    for addr in address_list.findall('ADDRESS'):
                        if addr.text and addr.text.strip():
                            address_lines.append(addr.text.strip())
                street = address_lines[0] if len(address_lines) > 0 else ''
                street2 = address_lines[1] if len(address_lines) > 1 else ''
                city = address_lines[2] if len(address_lines) > 2 else ''
                pincode = ledger.findtext('PINCODE') or ''
                
                guid = ledger.findtext('GUID') or ledger.attrib.get('NAME')
                
                ledgers.append({
                    'name': name_elem,
                    'parent': parent,
                    'guid': guid,
                    'email': email,
                    'phone': phone,
                    'mobile': mobile,
                    'street': street,
                    'street2': street2,
                    'city': city,
                    'zip': pincode,
                })
            
            return ledgers
        except ET.ParseError as e:
            _logger.error("Failed to parse XML response: %s", str(e))
            return []

    @staticmethod
    def parse_stock_items(xml_string):
        """Extracts stock items from Tally XML."""
        items = []
        try:
            if not xml_string:
                return items
            
            xml_string = XMLParser.sanitize_xml(xml_string)
            root = ET.fromstring(xml_string)
            for item in root.iter('STOCKITEM'):
                name_elem = item.attrib.get('NAME') or item.findtext('NAME') or ''
                if not name_elem:
                    name_list = item.find('NAME.LIST')
                    if name_list is not None:
                        name_elem = name_list.findtext('NAME') or ''
                
                if not name_elem:
                    continue
                
                parent = item.findtext('PARENT') or ''
                guid = item.findtext('GUID') or item.attrib.get('NAME')
                uom = item.findtext('BASEUNITS') or ''
                
                # Try to extract rate/price if available (usually STANDARDCOST or OPENINGRATE)
                rate_str = item.findtext('OPENINGRATE') or ''
                rate = 0.0
                if rate_str:
                    # e.g., "1000.00/NoS"
                    import re
                    match = re.search(r'([\d.]+)', rate_str)
                    if match:
                        rate = float(match.group(1))

                qty_str = item.findtext('OPENINGBALANCE') or ''
                qty = 0.0
                if qty_str:
                    import re
                    match = re.search(r'([-]?[\d.]+)', qty_str)
                    if match:
                        qty = float(match.group(1))
                
                items.append({
                    'name': name_elem,
                    'parent': parent,
                    'guid': guid,
                    'uom': uom,
                    'rate': rate,
                    'qty': qty
                })
            
            return items
        except ET.ParseError as e:
            _logger.error("Failed to parse XML response: %s", str(e))
            return []
