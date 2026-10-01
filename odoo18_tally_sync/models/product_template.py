from odoo import models, fields, api, _
import time
from .notification_helper import tally_notification

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tally_id = fields.Char(string='Tally ID', help='Unique identifier from Tally.', copy=False)
    last_sync = fields.Datetime(string='Last Sync', readonly=True, copy=False)
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string='Sync Status', default='pending', copy=False)

    def action_export_to_tally(self):
        """Triggered by button on product form or bulk action on product list."""
        from ..services.product_service import ProductService

        success_count = 0
        failed_count = 0
        skipped_count = 0
        last_error = ""
        last_name = ""

        for product in self:
            last_name = product.display_name or product.name or ""

            if product.sync_status == 'success':
                skipped_count += 1
                continue

            start_time = time.time()
            success = False
            response = ""
            payload = ""
            error_msg = ""
            try:
                service = ProductService(self.env)
                success, response, payload = service.export_product(product)

                product.sync_status = 'success' if success else 'failed'
                product.last_sync = fields.Datetime.now()
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    last_error = response or _("Export rejected by Tally.")
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                product.sync_status = 'failed'
                failed_count += 1

            duration = time.time() - start_time

            # Log the operation
            self.env['tally.sync.log'].create({
                'operation': 'export',
                'model': 'product',
                'status': 'success' if success else 'failed',
                'request': payload,
                'response': response,
                'error_message': error_msg or ('' if success else last_error),
                'duration': duration,
            })

        # Single product notification
        if len(self) == 1:
            if skipped_count == 1:
                return tally_notification(
                    title=_('Already Exported'),
                    message=_("Product '%s' is already synchronized with Tally.") % last_name,
                    notification_type='info',
                    duration=5000,
                    reload=False
                )
            if success_count == 1:
                return tally_notification(
                    title=_('Export Successful'),
                    message=_("Product '%s' exported to Tally successfully.") % last_name,
                    notification_type='success',
                    duration=5000,
                    reload=True
                )
            return tally_notification(
                title=_('Export Failed'),
                message=_("Failed to export product '%s' to Tally: %s") % (last_name, last_error or _('Unknown Error')),
                notification_type='danger',
                duration=5000,
                reload=True
            )

        # Batch / Bulk export notification
        if failed_count == 0 and success_count > 0:
            return tally_notification(
                title=_('Export Successful'),
                message=_("Successfully exported %d product(s) to Tally.") % success_count,
                notification_type='success',
                duration=5000,
                reload=True
            )
        elif success_count == 0 and failed_count > 0:
            return tally_notification(
                title=_('Export Failed'),
                message=_("Failed to export %d product(s) to Tally. Error: %s") % (failed_count, last_error or _('Unknown Error')),
                notification_type='danger',
                duration=5000,
                reload=True
            )
        elif success_count > 0 and failed_count > 0:
            return tally_notification(
                title=_('Export Completed with Issues'),
                message=_("Tally product export finished: %d succeeded, %d failed.") % (success_count, failed_count),
                notification_type='warning',
                duration=5000,
                reload=True
            )
        else:
            return tally_notification(
                title=_('No Changes'),
                message=_("All selected products are already exported to Tally."),
                notification_type='info',
                duration=5000,
                reload=False
            )
