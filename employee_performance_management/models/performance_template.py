from odoo import models, fields

class PerformanceTemplate(models.Model):
    _name = 'employee.performance.template'
    _description = 'Performance Template'

    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
    kra_ids = fields.Many2many('employee.performance.kra', string='KRAs')
    kpa_ids = fields.Many2many('employee.performance.kpa', string='KPAs')
    kpi_ids = fields.Many2many('employee.performance.kpi', string='KPIs')
    job_id = fields.Many2one('hr.job', string='Default for Job Position')
    active = fields.Boolean('Active', default=True)
