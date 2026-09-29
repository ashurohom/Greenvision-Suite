from odoo import models, fields

class TallySyncLog(models.Model):
    _name = 'tally.sync.log'
    _description = 'Tally Synchronization Log'
    _order = 'create_date desc'

    date = fields.Datetime(string='Date', default=fields.Datetime.now, readonly=True)
    operation = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export')
    ], string='Operation', required=True, readonly=True)
    
    model = fields.Selection([
        ('partner', 'Partner'),
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('product', 'Product'),
        ('invoice', 'Invoice'),
        ('vendor_bill', 'Vendor Bill'),
        ('payment', 'Payment'),
        ('supplier_payment', 'Supplier Payment'),
        ('credit_note', 'Credit Note'),
        ('debit_note', 'Debit Note')
    ], string='Model', required=True, readonly=True)
    
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending')
    ], string='Status', required=True, readonly=True)
    
    request = fields.Text(string='Request Payload', readonly=True)
    response = fields.Text(string='Response Payload', readonly=True)
    error_message = fields.Text(string='Error Message', readonly=True)
    
    duration = fields.Float(string='Duration (s)', readonly=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, readonly=True)
