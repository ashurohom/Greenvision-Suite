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
        """Triggered by a button on the invoice/bill/credit note/debit note form or list action."""
        from ..services.invoice_service import InvoiceService
        from ..services.vendor_bill_service import VendorBillService
        from ..services.credit_note_service import CreditNoteService
        from ..services.debit_note_service import DebitNoteService
        from .notification_helper import tally_notification

        success_count = 0
        failed_count = 0
        skipped_count = 0
        last_error = ""
        last_vch_desc = _("Invoice")
        last_move_name = ""

        for move in self:
            is_debit_note = (
                move.move_type == 'in_refund' or
                bool(getattr(move, 'debit_origin_id', False)) or
                bool(move.name and any(move.name.startswith(p) for p in ('DBILL/', 'DBN/', 'DN/')))
            )
            
            if is_debit_note:
                vch_desc = _('Supplier Debit Note')
            elif move.move_type == 'in_invoice':
                vch_desc = _('Vendor Bill')
            elif move.move_type == 'out_refund':
                vch_desc = _('Customer Credit Note')
            else:
                vch_desc = _('Invoice')

            last_vch_desc = vch_desc
            last_move_name = move.name or ""

            if move.state != 'posted':
                failed_count += 1
                last_error = _("Only posted vouchers can be exported.")
                continue

            if not is_debit_note and move.move_type not in ('out_invoice', 'in_invoice', 'out_refund'):
                failed_count += 1
                last_error = _("Unsupported document type.")
                continue

            if move.sync_status == 'success':
                skipped_count += 1
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
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    last_error = response or _("Export rejected by Tally.")
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                move.sync_status = 'failed'
                failed_count += 1
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
                'error_message': error_msg or ('' if success else last_error),
                'duration': duration,
            })

        # Single record notification
        if len(self) == 1:
            if skipped_count == 1:
                return tally_notification(
                    title=_('Already Exported'),
                    message=_("%s '%s' is already synchronized with Tally.") % (last_vch_desc, last_move_name),
                    notification_type='info',
                    duration=5000,
                    reload=False
                )
            if success_count == 1:
                return tally_notification(
                    title=_('Export Successful'),
                    message=_("%s '%s' exported to Tally successfully.") % (last_vch_desc, last_move_name),
                    notification_type='success',
                    duration=5000,
                    reload=True
                )
            return tally_notification(
                title=_('Export Failed'),
                message=_("Failed to export %s '%s' to Tally: %s") % (last_vch_desc, last_move_name, last_error or _('Unknown Error')),
                notification_type='danger',
                duration=5000,
                reload=True
            )

        # Batch / Bulk export notification
        if failed_count == 0 and success_count > 0:
            return tally_notification(
                title=_('Export Successful'),
                message=_("Successfully exported %d record(s) to Tally.") % success_count,
                notification_type='success',
                duration=5000,
                reload=True
            )
        elif success_count == 0 and failed_count > 0:
            return tally_notification(
                title=_('Export Failed'),
                message=_("Failed to export %d record(s) to Tally. Error: %s") % (failed_count, last_error or _('Unknown Error')),
                notification_type='danger',
                duration=5000,
                reload=True
            )
        elif success_count > 0 and failed_count > 0:
            return tally_notification(
                title=_('Export Completed with Issues'),
                message=_("Tally export finished: %d succeeded, %d failed.") % (success_count, failed_count),
                notification_type='warning',
                duration=5000,
                reload=True
            )
        else:
            return tally_notification(
                title=_('No Changes'),
                message=_("All selected records are already exported to Tally."),
                notification_type='info',
                duration=5000,
                reload=False
            )

    def action_export_payments_to_tally(self):
        """Export payments reconciled with this invoice/bill to Tally as Payment / Receipt Vouchers."""
        from .notification_helper import tally_notification
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
                return tally_notification(
                    title=_('No Payments Found'),
                    message=_("No reconciled payments found for %s.") % move.name,
                    notification_type='warning',
                    duration=5000,
                    reload=False
                )
            all_payments |= payments

        return all_payments.action_export_to_tally()
