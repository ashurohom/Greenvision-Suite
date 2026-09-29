from odoo import models, fields

class ProjectTask(models.Model):
    _inherit = 'project.task'

    performance_task_type = fields.Selection([
        ('variable', 'Variable'),
        ('project', 'Project')
    ], string='Performance Task Type')
    kra_id = fields.Many2one('employee.performance.kra', string='KRA')
    kpa_id = fields.Many2one('employee.performance.kpa', string='KPA')
    kpi_id = fields.Many2one('employee.performance.kpi', string='KPI')
    performance_weightage = fields.Float('Performance Weightage')
    performance_relevant = fields.Boolean('Performance Relevant', default=False)
    planned_performance_score = fields.Float('Planned Performance Score')
    actual_performance_score = fields.Float('Actual Performance Score')
    manager_rating = fields.Float('Manager Rating')
