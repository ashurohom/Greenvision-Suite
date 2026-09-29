from odoo import models, fields

class ReviewCycle(models.Model):
    _name = 'employee.performance.review.cycle'
    _description = 'Performance Review Cycle'
    _order = 'start_date desc'

    name = fields.Char('Name', required=True)
    cycle_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('half_yearly', 'Half-Yearly'),
        ('yearly', 'Yearly')
    ], string='Type', required=True, default='monthly')
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed')
    ], string='Status', default='draft')
