from odoo import models, api

class PerformanceScoreCalculator(models.AbstractModel):
    _name = 'performance.score.calculator'
    _description = 'Performance Score Calculator Service'

    @api.model
    def calculate_evaluation(self, evaluation):
        evaluation.line_ids.unlink()
        
        employee = evaluation.employee_id
        assignment = self.env['employee.performance.assignment'].search([
            ('employee_id', '=', employee.id),
            ('status', '=', 'active'),
            '|', ('start_date', '<=', evaluation.end_date), ('start_date', '=', False),
            '|', ('end_date', '>=', evaluation.start_date), ('end_date', '=', False)
        ], limit=1)

        if not assignment:
            return

        dsrs = self.env['employee.performance.dsr'].search([
            ('employee_id', '=', employee.id),
            ('date', '>=', evaluation.start_date),
            ('date', '<=', evaluation.end_date),
            ('status', '=', 'approved')
        ])

        kpi_actuals = {}
        for dsr in dsrs:
            for line in dsr.line_ids:
                if line.kpi_id:
                    kpi_actuals.setdefault(line.kpi_id.id, 0.0)
                    kpi_actuals[line.kpi_id.id] += line.progress # Simplified for demonstration

        # Create dummy structure representing evaluation roll up for demo
        for kra in assignment.template_id.kra_ids:
            kra_line = self.env['employee.performance.evaluation.line'].create({
                'evaluation_id': evaluation.id,
                'type': 'kra',
                'kra_id': kra.id,
                'weightage': kra.weightage,
                'score': 85.0 # Dummy score
            })
            for kpa in assignment.template_id.kpa_ids.filtered(lambda k: k.kra_id == kra):
                kpa_line = self.env['employee.performance.evaluation.line'].create({
                    'evaluation_id': evaluation.id,
                    'type': 'kpa',
                    'kra_id': kra.id,
                    'kpa_id': kpa.id,
                    'weightage': kpa.weightage,
                    'score': 85.0, # Dummy score
                    'parent_line_id': kra_line.id
                })
                for kpi in assignment.template_id.kpi_ids.filtered(lambda k: k.kpa_id == kpa):
                    actual = kpi_actuals.get(kpi.id, 0.0)
                    target = kpi.target_value or 100.0
                    achieve = min((actual / target) * 100 if target else 0.0, 100.0)
                    self.env['employee.performance.evaluation.line'].create({
                        'evaluation_id': evaluation.id,
                        'type': 'kpi',
                        'kra_id': kra.id,
                        'kpa_id': kpa.id,
                        'kpi_id': kpi.id,
                        'target_value': target,
                        'actual_value': actual,
                        'achievement_percentage': achieve,
                        'weightage': kpi.weightage,
                        'score': achieve,
                        'parent_line_id': kpa_line.id
                    })
