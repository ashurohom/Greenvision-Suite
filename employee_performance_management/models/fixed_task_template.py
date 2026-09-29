from odoo import models, fields

class FixedTaskTemplate(models.Model):
    _name = 'employee.performance.fixed.task.template'
    _description = 'Fixed Task Template'

    name = fields.Char('Task Name', required=True)
    task_type = fields.Selection([('fixed', 'Fixed')], default='fixed', readonly=True)
    template_id = fields.Many2one('employee.performance.template', string='Performance Template')
    job_id = fields.Many2one('hr.job', string='Job Position')
    employee_id = fields.Many2one('hr.employee', string='Specific Employee')
    frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], string='Frequency', required=True, default='daily')
    target = fields.Float('Target per Frequency')
    kra_id = fields.Many2one('employee.performance.kra', string='KRA')
    kpa_id = fields.Many2one('employee.performance.kpa', string='KPA')
    kpi_id = fields.Many2one('employee.performance.kpi', string='KPI', required=True)
    planned_hours = fields.Float('Planned Hours')
    active = fields.Boolean('Active', default=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
