from odoo import models, fields, api

class PerformanceKPA(models.Model):
    _name = 'employee.performance.kpa'
    _description = 'Key Performance Area'
    _order = 'sequence, id'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    kra_id = fields.Many2one('employee.performance.kra', string='KRA', required=True, ondelete='cascade')
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    weightage = fields.Float('Weightage (%)', default=100.0)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The KPA Code must be unique!')
    ]
