from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ShopifyInstance(models.Model):
    _name = 'shopify.instance'
    _description = 'Shopify Instance Configuration'

    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    store_url = fields.Char('Store URL', required=True, help="e.g. https://your-store.myshopify.com")
    api_version = fields.Char('API Version', required=True, default='2023-10')
    access_token = fields.Char('Admin API Access Token', required=True)
    connection_status = fields.Selection([
        ('not_tested', 'Not Tested'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string='Connection Status', default='not_tested', readonly=True)
    auto_sync = fields.Boolean('Auto Sync')
    last_sync_datetime = fields.Datetime('Last Sync Datetime', readonly=True)
    active = fields.Boolean('Active', default=True)

    def test_connection(self):
        self.ensure_one()
        api_service = self.env['shopify.api.service']
        success = api_service.test_connection(self)
        if success:
            self.connection_status = 'success'
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Successful'),
                    'message': _('Successfully connected to Shopify.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            self.connection_status = 'failed'
            raise UserError(_('Connection to Shopify failed. Please check your credentials and store URL.'))

    def action_sync_customers(self):
        self.ensure_one()
        self.env['shopify.customer.sync.service'].sync_customers(self)

    def action_sync_orders(self):
        self.ensure_one()
        self.env['shopify.order.sync.service'].sync_orders(self)

    def action_sync_payments(self):
        self.ensure_one()
        self.env['shopify.payment.sync.service'].sync_payments(self)

    def action_sync_all(self):
        self.ensure_one()
        self.action_sync_customers()
        self.action_sync_orders()
        self.action_sync_payments()
        self.last_sync_datetime = fields.Datetime.now()
