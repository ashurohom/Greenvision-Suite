from odoo import models, fields, api

class PerformanceAssignment(models.Model):
    _name = 'employee.performance.assignment'
    _description = 'Employee Performance Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', compute='_compute_name', store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    job_id = fields.Many2one('hr.job', string='Job Position', related='employee_id.job_id', store=True)
    template_id = fields.Many2one('employee.performance.template', string='Performance Template', required=True, tracking=True)
    start_date = fields.Date('Start Date', required=True, tracking=True)
    end_date = fields.Date('End Date', tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    line_ids = fields.One2many('employee.performance.assignment.line', 'assignment_id', string='KPI Assignments/Overrides')

    @api.depends('employee_id', 'template_id')
    def _compute_name(self):
        for rec in self:
            emp = rec.employee_id.name or 'New'
            temp = rec.template_id.name or 'Assignment'
            rec.name = f"{emp} - {temp}"
