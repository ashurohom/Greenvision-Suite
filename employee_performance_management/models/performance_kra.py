from odoo import models, fields, api

class PerformanceKRA(models.Model):
    _name = 'employee.performance.kra'
    _description = 'Key Result Area'
    _order = 'sequence, id'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    weightage = fields.Float('Weightage (%)', default=100.0)
    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job', string='Job Position')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The KRA Code must be unique!')
    ]
