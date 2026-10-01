from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    tally_id = fields.Char(string='Tally ID', help='Unique identifier from Tally.', copy=False)
    last_sync = fields.Datetime(string='Last Sync', readonly=True, copy=False)
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string='Sync Status', default='pending', copy=False)

    def action_export_to_tally(self):
        """Triggered by a button on the payment form or list action."""
        from ..services.payment_service import PaymentService
        from .notification_helper import tally_notification

        success_count = 0
        failed_count = 0
        skipped_count = 0
        last_error = ""
        last_vch_desc = _("Payment")
        last_payment_name = ""

        for payment in self:
            vch_desc = _('Supplier Payment') if payment.payment_type == 'outbound' else _('Customer Receipt')
            last_vch_desc = vch_desc
            last_payment_name = payment.name or ""

            if payment.state not in ('in_process', 'paid'):
                failed_count += 1
                last_error = _("Only validated payments (In Process or Paid) can be exported.")
                continue

            if payment.payment_type not in ('inbound', 'outbound'):
                failed_count += 1
                last_error = _("Only Customer Receipts or Vendor Payments can be exported.")
                continue

            if payment.sync_status == 'success':
                skipped_count += 1
                continue

            start_time = time.time()
            success = False
            response = ""
            payload = ""
            error_msg = ""
            try:
                service = PaymentService(self.env)
                success, response, payload = service.export_payment(payment)

                payment.sync_status = 'success' if success else 'failed'
                payment.last_sync = fields.Datetime.now()
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    last_error = response or _("Export rejected by Tally.")
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                payment.sync_status = 'failed'
                failed_count += 1

            duration = time.time() - start_time

            # Log the operation
            model_log = 'supplier_payment' if payment.payment_type == 'outbound' else 'payment'
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
                    message=_("%s '%s' is already synchronized with Tally.") % (last_vch_desc, last_payment_name),
                    notification_type='info',
                    duration=5000,
                    reload=False
                )
            if success_count == 1:
                return tally_notification(
                    title=_('Export Successful'),
                    message=_("%s '%s' exported to Tally successfully.") % (last_vch_desc, last_payment_name),
                    notification_type='success',
                    duration=5000,
                    reload=True
                )
            return tally_notification(
                title=_('Export Failed'),
                message=_("Failed to export %s '%s' to Tally: %s") % (last_vch_desc, last_payment_name, last_error or _('Unknown Error')),
                notification_type='danger',
                duration=5000,
                reload=True
            )

        # Batch / Bulk export notification
        if failed_count == 0 and success_count > 0:
            return tally_notification(
                title=_('Export Successful'),
                message=_("Successfully exported %d payment(s) to Tally.") % success_count,
                notification_type='success',
                duration=5000,
                reload=True
            )
        elif success_count == 0 and failed_count > 0:
            return tally_notification(
                title=_('Export Failed'),
                message=_("Failed to export %d payment(s) to Tally. Error: %s") % (failed_count, last_error or _('Unknown Error')),
                notification_type='danger',
                duration=5000,
                reload=True
            )
        elif success_count > 0 and failed_count > 0:
            return tally_notification(
                title=_('Export Completed with Issues'),
                message=_("Tally payment export finished: %d succeeded, %d failed.") % (success_count, failed_count),
                notification_type='warning',
                duration=5000,
                reload=True
            )
        else:
            return tally_notification(
                title=_('No Changes'),
                message=_("All selected payments are already exported to Tally."),
                notification_type='info',
                duration=5000,
                reload=False
            )
