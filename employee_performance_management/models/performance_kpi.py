from odoo import models, fields, api

class PerformanceKPI(models.Model):
    _name = 'employee.performance.kpi'
    _description = 'Key Performance Indicator'
    _order = 'sequence, id'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    kpa_id = fields.Many2one('employee.performance.kpa', string='KPA', required=True, ondelete='cascade')
    description = fields.Text('Description')
    measurement_type = fields.Selection([
        ('number', 'Number'),
        ('percentage', 'Percentage'),
        ('currency', 'Currency'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('manual', 'Manual Rating'),
    ], string='Measurement Type', required=True, default='number')
    target_value = fields.Float('Target Value')
    minimum_value = fields.Float('Minimum Value')
    maximum_value = fields.Float('Maximum Value')
    weightage = fields.Float('Weightage (%)', default=100.0)
    calculation_method = fields.Selection([
        ('manual', 'Manual'),
        ('automatic', 'Automatic')
    ], string='Calculation Method', required=True, default='automatic')
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The KPI Code must be unique!')
    ]
