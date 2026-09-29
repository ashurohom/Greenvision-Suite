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
        """Triggered by a button on the payment form."""
        from ..services.payment_service import PaymentService
        
        for payment in self:
            if payment.state not in ('in_process', 'paid'):
                raise UserError(_("Only validated payments (In Process or Paid) can be exported to Tally."))
            if payment.payment_type not in ('inbound', 'outbound'):
                raise UserError(_("Only Customer Receipts or Vendor Payments can be exported."))
            if payment.sync_status == 'success':
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
            except Exception as e:
                error_msg = str(e)
                payment.sync_status = 'failed'
            
            duration = time.time() - start_time
            
            # Log the operation
            model_log = 'supplier_payment' if payment.payment_type == 'outbound' else 'payment'
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
                
            vch_desc = _('Supplier Payment') if payment.payment_type == 'outbound' else _('Customer Receipt')
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
