from .tally_client import TallyAPIProvider
from .xml_generator import XMLGenerator
from odoo import _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class PaymentService:
    """Service to handle customer payment synchronization with Tally."""

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

    def export_payment(self, payment):
        """Exports an Odoo payment as a Tally Receipt or Payment Voucher."""
        if payment.payment_type not in ('inbound', 'outbound'):
            raise UserError(_("Only Customer Receipts (Inbound) or Vendor Payments (Outbound) can be exported to Tally."))
            
        # 1. Ensure Party Ledger (Vendor / Customer) exists in Tally masters
        if payment.partner_id:
            partner_type = 'Vendor' if payment.payment_type == 'outbound' else 'Customer'
            partner_payload = XMLGenerator.generate_partner_xml(payment.partner_id, partner_type=partner_type)
            p_success, p_resp = self.client.send_request(partner_payload)
            if not p_success:
                _logger.warning("Auto-sync of partner master '%s' to Tally returned: %s", payment.partner_id.name, p_resp)

        # 2. Ensure Bank / Cash Ledger exists in Tally masters
        if payment.journal_id:
            bank_ledger_name = XMLGenerator.get_bank_cash_ledger_name(payment.journal_id)
            parent_group = "Cash-in-hand" if getattr(payment.journal_id, 'type', None) == 'cash' else "Bank Accounts"
            ledger_payload = XMLGenerator.generate_simple_ledger_xml(bank_ledger_name, parent_group=parent_group)
            l_success, l_resp = self.client.send_request(ledger_payload)
            if not l_success:
                _logger.warning("Auto-sync of bank/cash ledger master '%s' to Tally returned: %s", bank_ledger_name, l_resp)

        # 3. Export Voucher
        if payment.payment_type == 'outbound':
            payload = XMLGenerator.generate_payment_voucher_xml(payment)
        else:
            payload = XMLGenerator.generate_receipt_voucher_xml(payment)
            
        success, response = self.client.send_request(payload)
        return success, response, payload

    def export_vendor_payment(self, payment):
        """Helper to export a supplier/vendor payment as a Tally Payment Voucher."""
        return self.export_payment(payment)
