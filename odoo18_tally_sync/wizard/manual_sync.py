from odoo import models, fields, api, _

class TallyManualSync(models.TransientModel):
    _name = 'tally.manual.sync'
    _description = 'Tally Manual Sync Wizard'

    operation = fields.Selection([
        ('import', 'Import from Tally'),
        ('export', 'Export to Tally')
    ], string='Operation', required=True, default='import')

    sync_model = fields.Selection([
        ('customers', 'Customers'),
        ('vendors', 'Vendors'),
        ('products', 'Products'),
        ('customer_payments', 'Customer Payments (Receipts)'),
        ('supplier_payments', 'Supplier Payments (Payments)'),
        ('credit_notes', 'Customer Credit Notes'),
        ('debit_notes', 'Supplier Debit Notes')
    ], string='Model to Sync', required=True, default='customers')

    result_message = fields.Text(string='Result', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')
    ], string='State', default='draft')

    def action_sync(self):
        self.ensure_one()
        from ..services.customer_service import CustomerService
        from ..services.vendor_service import VendorService

        success_count = 0
        failed_count = 0
        
        try:
            if self.sync_model == 'customers':
                service = CustomerService(self.env)
                if self.operation == 'export':
                    partners = self.env['res.partner'].search([('customer_rank', '>', 0)])
                    for p in partners:
                        success, resp, req = service.export_customer(p)
                        if success:
                            success_count += 1
                        else:
                            failed_count += 1
                else:
                    success, resp, count = service.import_customers()
                    if success:
                        success_count += count
                    else:
                        failed_count += 1

            elif self.sync_model == 'vendors':
                service = VendorService(self.env)
                if self.operation == 'export':
                    partners = self.env['res.partner'].search([('supplier_rank', '>', 0)])
                    for p in partners:
                        success, resp, req = service.export_vendor(p)
                        if success:
                            success_count += 1
                        else:
                            failed_count += 1
                else:
                    success, resp, count = service.import_vendors()
                    if success:
                        success_count += count
                    else:
                        failed_count += 1

            elif self.sync_model == 'products':
                from ..services.product_service import ProductService
                service = ProductService(self.env)
                if self.operation == 'export':
                    products = self.env['product.template'].search([])
                    for p in products:
                        success, resp, req = service.export_product(p)
                        if success:
                            success_count += 1
                        else:
                            failed_count += 1
                else:
                    success, resp, count = service.import_products()
                    if success:
                        success_count += count
                    else:
                        failed_count += 1

            elif self.sync_model == 'customer_payments':
                from ..services.payment_service import PaymentService
                service = PaymentService(self.env)
                if self.operation == 'export':
                    payments = self.env['account.payment'].search([
                        ('payment_type', '=', 'inbound'),
                        ('state', 'in', ('in_process', 'paid')),
                    ])
                    for p in payments:
                        success, resp, req = service.export_payment(p)
                        if success:
                            p.sync_status = 'success'
                            p.last_sync = fields.Datetime.now()
                            success_count += 1
                        else:
                            p.sync_status = 'failed'
                            failed_count += 1
                else:
                    self.result_message = _("Customer Payment import from Tally is not supported.")
                    self.state = 'done'
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'tally.manual.sync',
                        'res_id': self.id,
                        'view_mode': 'form',
                        'target': 'new',
                    }

            elif self.sync_model == 'supplier_payments':
                from ..services.payment_service import PaymentService
                service = PaymentService(self.env)
                if self.operation == 'export':
                    payments = self.env['account.payment'].search([
                        ('payment_type', '=', 'outbound'),
                        ('state', 'in', ('in_process', 'paid')),
                    ])
                    for p in payments:
                        success, resp, req = service.export_payment(p)
                        if success:
                            p.sync_status = 'success'
                            p.last_sync = fields.Datetime.now()
                            success_count += 1
                        else:
                            p.sync_status = 'failed'
                            failed_count += 1
                else:
                    self.result_message = _("Supplier Payment import from Tally is not supported.")
                    self.state = 'done'
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'tally.manual.sync',
                        'res_id': self.id,
                        'view_mode': 'form',
                        'target': 'new',
                    }

            elif self.sync_model == 'credit_notes':
                from ..services.credit_note_service import CreditNoteService
                service = CreditNoteService(self.env)
                if self.operation == 'export':
                    credit_notes = self.env['account.move'].search([
                        ('move_type', '=', 'out_refund'),
                        ('state', '=', 'posted'),
                    ])
                    for cn in credit_notes:
                        success, resp, req = service.export_credit_note(cn)
                        if success:
                            cn.sync_status = 'success'
                            cn.last_sync = fields.Datetime.now()
                            success_count += 1
                        else:
                            cn.sync_status = 'failed'
                            failed_count += 1
                else:
                    self.result_message = _("Customer Credit Note import from Tally is not supported.")
                    self.state = 'done'
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'tally.manual.sync',
                        'res_id': self.id,
                        'view_mode': 'form',
                        'target': 'new',
                    }

            elif self.sync_model == 'debit_notes':
                from ..services.debit_note_service import DebitNoteService
                service = DebitNoteService(self.env)
                if self.operation == 'export':
                    debit_notes = self.env['account.move'].search([
                        ('state', '=', 'posted'),
                        '|', '|',
                        ('move_type', '=', 'in_refund'),
                        ('debit_origin_id', '!=', False),
                        ('name', '=like', 'DBILL%'),
                    ])
                    for dn in debit_notes:
                        success, resp, req = service.export_debit_note(dn)
                        if success:
                            dn.sync_status = 'success'
                            dn.last_sync = fields.Datetime.now()
                            success_count += 1
                        else:
                            dn.sync_status = 'failed'
                            failed_count += 1
                else:
                    self.result_message = _("Supplier Debit Note import from Tally is not supported.")
                    self.state = 'done'
                    return {
                        'type': 'ir.actions.act_window',
                        'res_model': 'tally.manual.sync',
                        'res_id': self.id,
                        'view_mode': 'form',
                        'target': 'new',
                    }

            self.result_message = _("Sync Completed.\nSuccess: %d\nFailed: %d") % (success_count, failed_count)
            self.state = 'done'

            notif_type = 'success' if failed_count == 0 else ('warning' if success_count > 0 else 'danger')
            notif_title = _('Sync Successful') if failed_count == 0 else _('Sync Completed with Issues')

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': notif_title,
                    'message': _('Tally Sync Finished: %d succeeded, %d failed.') % (success_count, failed_count),
                    'type': notif_type,
                    'sticky': False,
                    'duration': 5000,
                    'next': {
                        'type': 'ir.actions.act_window',
                        'res_model': 'tally.manual.sync',
                        'res_id': self.id,
                        'view_mode': 'form',
                        'target': 'new',
                    },
                }
            }

        except Exception as e:
            self.result_message = _("Error occurred during sync: %s") % str(e)
            self.state = 'done'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Failed'),
                    'message': _('Error occurred during sync: %s') % str(e),
                    'type': 'danger',
                    'sticky': False,
                    'duration': 5000,
                    'next': {
                        'type': 'ir.actions.act_window',
                        'res_model': 'tally.manual.sync',
                        'res_id': self.id,
                        'view_mode': 'form',
                        'target': 'new',
                    },
                }
            }
