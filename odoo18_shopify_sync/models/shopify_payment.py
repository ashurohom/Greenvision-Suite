from odoo import models, fields

class ShopifyPayment(models.Model):
    _name = 'shopify.payment'
    _description = 'Shopify Payment'
    _order = 'payment_date desc'

    transaction_id = fields.Char('Shopify Transaction ID', required=True, index=True)
    payment_gateway = fields.Char('Payment Gateway')
    amount = fields.Monetary('Amount')
    currency_id = fields.Many2one('res.currency', string='Currency')
    payment_date = fields.Datetime('Payment Date')
    payment_status = fields.Char('Payment Status')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    _sql_constraints = [
        ('transaction_id_uniq', 'unique(transaction_id)', 'Shopify Transaction ID must be unique!')
    ]
