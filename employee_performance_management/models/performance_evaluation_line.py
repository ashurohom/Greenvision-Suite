from odoo import models, fields

class PerformanceEvaluationLine(models.Model):
    _name = 'employee.performance.evaluation.line'
    _description = 'Evaluation Line'

    evaluation_id = fields.Many2one('employee.performance.evaluation', required=True, ondelete='cascade')
    type = fields.Selection([
        ('kpi', 'KPI'),
        ('kpa', 'KPA'),
        ('kra', 'KRA')
    ], string='Level', required=True)
    kra_id = fields.Many2one('employee.performance.kra', string='KRA')
    kpa_id = fields.Many2one('employee.performance.kpa', string='KPA')
    kpi_id = fields.Many2one('employee.performance.kpi', string='KPI')
    
    target_value = fields.Float('Target')
    actual_value = fields.Float('Actual')
    achievement_percentage = fields.Float('Achievement (%)')
    weightage = fields.Float('Weightage (%)')
    score = fields.Float('Calculated Score')
    
    parent_line_id = fields.Many2one('employee.performance.evaluation.line', string='Parent Line')
