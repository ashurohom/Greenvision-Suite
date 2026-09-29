from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tally_id = fields.Char(string='Tally ID', help='Unique identifier from Tally.', copy=False)
    last_sync = fields.Datetime(string='Last Sync', readonly=True, copy=False)
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed')
    ], string='Sync Status', default='pending', copy=False)
