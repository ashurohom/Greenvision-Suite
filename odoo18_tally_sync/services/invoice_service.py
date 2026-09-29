from .tally_client import TallyAPIProvider
from .xml_generator import XMLGenerator
from .xml_parser import XMLParser
from odoo import _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class InvoiceService:
    """Service to handle invoice synchronization with Tally."""

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

    def export_invoice(self, invoice):
        """Exports an Odoo customer invoice as a Tally Sales Voucher."""
        if invoice.move_type != 'out_invoice':
            raise UserError(_("Only customer invoices can be exported to Tally as Sales Vouchers."))
            
        payload = XMLGenerator.generate_sales_voucher_xml(invoice)
        success, response = self.client.send_request(payload)
        
        return success, response, payload
