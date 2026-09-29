from odoo import models, fields

class PerformanceAssignmentLine(models.Model):
    _name = 'employee.performance.assignment.line'
    _description = 'Performance Assignment Line'

    assignment_id = fields.Many2one('employee.performance.assignment', required=True, ondelete='cascade')
    kra_id = fields.Many2one('employee.performance.kra', string='KRA')
    kpa_id = fields.Many2one('employee.performance.kpa', string='KPA')
    kpi_id = fields.Many2one('employee.performance.kpi', string='KPI', required=True)
    weightage_override = fields.Float('Weightage Override (%)')
    target_value_override = fields.Float('Target Override')
    is_applicable = fields.Boolean('Applicable', default=True)
