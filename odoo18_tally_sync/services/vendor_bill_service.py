from .tally_client import TallyAPIProvider
from .xml_generator import XMLGenerator
from .xml_parser import XMLParser
from odoo import _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class VendorBillService:
    """Service to handle vendor bill synchronization with Tally."""

    def __init__(self, env):
        self.env = env
        config = self.env['tally.configuration'].search([('active', '=', True)], limit=1)
        if not config:
            raise UserError(_("No active Tally configuration found."))
        
        self.client = TallyAPIProvider(
            server_url=config.server_url,
            auth_type=config.auth_type,
            username=config.username,
            password=config.password,
            token=config.api_token,
            timeout=config.connection_timeout
        )

    def export_vendor_bill(self, bill):
        """Exports an Odoo vendor bill as a Tally Purchase Voucher."""
        if bill.move_type != 'in_invoice':
            raise UserError(_("Only vendor bills can be exported to Tally as Purchase Vouchers."))
            
        payload = XMLGenerator.generate_purchase_voucher_xml(bill)
        success, response = self.client.send_request(payload)
        
        return success, response, payload
