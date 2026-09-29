from .tally_client import TallyAPIProvider
from .xml_generator import XMLGenerator
from .xml_parser import XMLParser
from odoo import _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class DebitNoteService:
    """Service to handle supplier debit note / refund synchronization with Tally."""

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

    def export_debit_note(self, debit_note):
        """Exports an Odoo supplier refund / debit note as a Tally Debit Note Voucher."""
        is_debit_note = (
            debit_note.move_type == 'in_refund' or
            bool(getattr(debit_note, 'debit_origin_id', False)) or
            bool(debit_note.name and any(debit_note.name.startswith(p) for p in ('DBILL/', 'DBN/', 'DN/')))
        )
        if not is_debit_note:
            raise UserError(_("Only Debit Notes or Supplier Refunds can be exported to Tally as Debit Note Vouchers."))

        # 1. Ensure Vendor exists in Tally masters
        if debit_note.partner_id:
            vendor_payload = XMLGenerator.generate_partner_xml(debit_note.partner_id, partner_type='Vendor')
            v_success, v_resp = self.client.send_request(vendor_payload)
            if not v_success:
                _logger.warning("Auto-sync of vendor '%s' to Tally returned: %s", debit_note.partner_id.name, v_resp)
            
        # 2. Export Debit Note Voucher
        payload = XMLGenerator.generate_debit_note_xml(debit_note)
        success, response = self.client.send_request(payload)
        
        return success, response, payload
