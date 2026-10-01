from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time

class ResPartner(models.Model):
    _inherit = 'res.partner'

    tally_id = fields.Char(string='Tally ID', help='Unique identifier from Tally.', copy=False)
    last_sync = fields.Datetime(string='Last Sync', readonly=True, copy=False)
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string='Sync Status', default='pending', copy=False)

    def action_export_to_tally(self):
        """Triggered by a button on the partner form or list action."""
        from ..services.customer_service import CustomerService
        from ..services.vendor_service import VendorService
        from .notification_helper import tally_notification

        success_count = 0
        failed_count = 0
        skipped_count = 0
        last_error = ""
        last_desc = _("Contact")
        last_name = ""

        for partner in self:
            partner_desc = _('Vendor') if partner.supplier_rank > 0 else _('Customer')
            last_desc = partner_desc
            last_name = partner.display_name or partner.name or ""

            if partner.sync_status == 'success':
                skipped_count += 1
                continue

            start_time = time.time()
            success = False
            response = ""
            payload = ""
            error_msg = ""
            try:
                if partner.supplier_rank > 0:
                    service = VendorService(self.env)
                    success, response, payload = service.export_vendor(partner)
                else:
                    service = CustomerService(self.env)
                    success, response, payload = service.export_customer(partner)

                partner.sync_status = 'success' if success else 'failed'
                partner.last_sync = fields.Datetime.now()
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    last_error = response or _("Export rejected by Tally.")
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                partner.sync_status = 'failed'
                failed_count += 1

            duration = time.time() - start_time

            # Log the operation
            self.env['tally.sync.log'].create({
                'operation': 'export',
                'model': 'vendor' if partner.supplier_rank > 0 else 'customer',
                'status': 'success' if success else 'failed',
                'request': payload,
                'response': response,
                'error_message': error_msg or ('' if success else last_error),
                'duration': duration,
            })

        # Single partner notification
        if len(self) == 1:
            if skipped_count == 1:
                return tally_notification(
                    title=_('Already Exported'),
                    message=_("%s '%s' is already synchronized with Tally.") % (last_desc, last_name),
                    notification_type='info',
                    duration=5000,
                    reload=False
                )
            if success_count == 1:
                return tally_notification(
                    title=_('Export Successful'),
                    message=_("%s '%s' exported to Tally successfully.") % (last_desc, last_name),
                    notification_type='success',
                    duration=5000,
                    reload=True
                )
            return tally_notification(
                title=_('Export Failed'),
                message=_("Failed to export %s '%s' to Tally: %s") % (last_desc, last_name, last_error or _('Unknown Error')),
                notification_type='danger',
                duration=5000,
                reload=True
            )

        # Bulk / Batch partner notification
        if failed_count == 0 and success_count > 0:
            return tally_notification(
                title=_('Export Successful'),
                message=_("Successfully exported %d contact(s) to Tally.") % success_count,
                notification_type='success',
                duration=5000,
                reload=True
            )
        elif success_count == 0 and failed_count > 0:
            return tally_notification(
                title=_('Export Failed'),
                message=_("Failed to export %d contact(s) to Tally. Error: %s") % (failed_count, last_error or _('Unknown Error')),
                notification_type='danger',
                duration=5000,
                reload=True
            )
        elif success_count > 0 and failed_count > 0:
            return tally_notification(
                title=_('Export Completed with Issues'),
                message=_("Tally contact export finished: %d succeeded, %d failed.") % (success_count, failed_count),
                notification_type='warning',
                duration=5000,
                reload=True
            )
        else:
            return tally_notification(
                title=_('No Changes'),
                message=_("All selected contacts are already exported to Tally."),
                notification_type='info',
                duration=5000,
                reload=False
            )
            
    def action_import_from_tally(self):
        """Action for importing from tally (usually a batch process, but can be a single refresh)."""
        # Placeholder implementation
        pass
