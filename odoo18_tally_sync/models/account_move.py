from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time

class AccountMove(models.Model):
    _inherit = 'account.move'

    tally_id = fields.Char(string='Tally ID', help='Unique identifier from Tally.', copy=False)
    last_sync = fields.Datetime(string='Last Sync', readonly=True, copy=False)
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string='Sync Status', default='pending', copy=False)

    def action_export_to_tally(self):
        """Triggered by a button on the invoice/bill/credit note/debit note form."""
        from ..services.invoice_service import InvoiceService
        from ..services.vendor_bill_service import VendorBillService
        from ..services.credit_note_service import CreditNoteService
        from ..services.debit_note_service import DebitNoteService
        
        for move in self:
            if move.state != 'posted':
                raise UserError(_("Only posted invoices/bills/credit notes/debit notes can be exported to Tally."))
            
            is_debit_note = (
                move.move_type == 'in_refund' or
                bool(getattr(move, 'debit_origin_id', False)) or
                bool(move.name and any(move.name.startswith(p) for p in ('DBILL/', 'DBN/', 'DN/')))
            )
            
            if not is_debit_note and move.move_type not in ('out_invoice', 'in_invoice', 'out_refund'):
                raise UserError(_("Only Customer Invoices, Vendor Bills, Customer Credit Notes, and Supplier Debit Notes can be exported."))
            if move.sync_status == 'success':
                continue
            
            start_time = time.time()
            success = False
            response = ""
            payload = ""
            error_msg = ""
            try:
                if is_debit_note:
                    service = DebitNoteService(self.env)
                    success, response, payload = service.export_debit_note(move)
                    model_log = 'debit_note'
                elif move.move_type == 'out_invoice':
                    service = InvoiceService(self.env)
                    success, response, payload = service.export_invoice(move)
                    model_log = 'invoice'
                elif move.move_type == 'in_invoice':
                    service = VendorBillService(self.env)
                    success, response, payload = service.export_vendor_bill(move)
                    model_log = 'vendor_bill'
                elif move.move_type == 'out_refund':
                    service = CreditNoteService(self.env)
                    success, response, payload = service.export_credit_note(move)
                    model_log = 'credit_note'
                
                move.sync_status = 'success' if success else 'failed'
                move.last_sync = fields.Datetime.now()
            except Exception as e:
                error_msg = str(e)
                move.sync_status = 'failed'
                if is_debit_note:
                    model_log = 'debit_note'
                elif move.move_type == 'out_invoice':
                    model_log = 'invoice'
                elif move.move_type == 'in_invoice':
                    model_log = 'vendor_bill'
                else:
                    model_log = 'credit_note'
            
            duration = time.time() - start_time
            
            # Log the operation
            self.env['tally.sync.log'].create({
                'operation': 'export',
                'model': model_log,
                'status': 'success' if success else 'failed',
                'request': payload,
                'response': response,
                'error_message': error_msg,
                'duration': duration,
            })
            
            if not success:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Export Failed'),
                        'message': _('Failed to export to Tally: %s' % (error_msg or response or "Unknown Error")),
                        'type': 'danger',
                        'sticky': True,
                    }
                }
                
            if is_debit_note:
                vch_desc = _('Supplier Debit Note')
            elif move.move_type == 'in_invoice':
                vch_desc = _('Vendor Bill')
            elif move.move_type == 'out_refund':
                vch_desc = _('Customer Credit Note')
            else:
                vch_desc = _('Invoice')
                
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Export Successful'),
                    'message': _('%s exported to Tally successfully.') % vch_desc,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                }
            }

    def action_export_payments_to_tally(self):
        """Export payments reconciled with this invoice/bill to Tally as Payment / Receipt Vouchers."""
        all_payments = self.env['account.payment']
        for move in self:
            payments = self.env['account.payment']
            if hasattr(move, '_get_reconciled_payments'):
                payments = move._get_reconciled_payments()
            if not payments and hasattr(move, 'payment_ids'):
                payments = move.payment_ids
            if not payments:
                pay_term_lines = move.line_ids.filtered(lambda l: l.account_type in ('asset_receivable', 'liability_payable'))
                for line in pay_term_lines:
                    for partial in (line.matched_debit_ids | line.matched_credit_ids):
                        rec_line = partial.debit_move_id if partial.credit_move_id == line else partial.credit_move_id
                        if rec_line.payment_id:
                            payments |= rec_line.payment_id
            if not payments:
                raise UserError(_("No payments found for %s.") % move.name)
            all_payments |= payments

        return all_payments.action_export_to_tally()
