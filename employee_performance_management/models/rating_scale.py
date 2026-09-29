from odoo import models, fields

class RatingScale(models.Model):
    _name = 'employee.performance.rating.scale'
    _description = 'Performance Rating Scale'
    _order = 'min_score desc'

    name = fields.Char('Rating Name', required=True)
    min_score = fields.Float('Minimum Score', required=True)
    max_score = fields.Float('Maximum Score', required=True)
    description = fields.Text('Description')
