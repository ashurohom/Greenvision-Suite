from .tally_client import TallyAPIProvider
from .xml_generator import XMLGenerator
from .xml_parser import XMLParser
from odoo import _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class CreditNoteService:
    """Service to handle customer credit note synchronization with Tally."""

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

    def export_credit_note(self, credit_note):
        """Exports an Odoo customer credit note as a Tally Credit Note Voucher."""
        if credit_note.move_type != 'out_refund':
            raise UserError(_("Only customer credit notes can be exported to Tally as Credit Note Vouchers."))

        # 1. Ensure Customer exists in Tally masters
        if credit_note.partner_id:
            cust_payload = XMLGenerator.generate_partner_xml(credit_note.partner_id, partner_type='Customer')
            c_success, c_resp = self.client.send_request(cust_payload)
            if not c_success:
                _logger.warning("Auto-sync of customer '%s' to Tally returned: %s", credit_note.partner_id.name, c_resp)
            
        # 2. Export Credit Note Voucher
        payload = XMLGenerator.generate_credit_note_xml(credit_note)
        success, response = self.client.send_request(payload)
        
        return success, response, payload
