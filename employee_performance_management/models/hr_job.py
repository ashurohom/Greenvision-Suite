from odoo import models, fields

class Job(models.Model):
    _inherit = 'hr.job'

    performance_template_id = fields.Many2one('employee.performance.template', string='Performance Template')
