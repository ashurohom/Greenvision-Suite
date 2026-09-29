from odoo import models, fields, api

class PerformanceDSR(models.Model):
    _name = 'employee.performance.dsr'
    _description = 'Daily Status Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('DSR Number', default='New', readonly=True)
    date = fields.Date('Date', required=True, default=fields.Date.context_today)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env.user.employee_id)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id')
    manager_id = fields.Many2one('hr.employee', string='Manager', related='employee_id.parent_id')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', tracking=True)
    submitted_date = fields.Datetime('Submitted Date', readonly=True)
    approved_date = fields.Datetime('Approved Date', readonly=True)
    remarks = fields.Text('Remarks')
    line_ids = fields.One2many('employee.performance.dsr.line', 'dsr_id', string='Tasks')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('employee.performance.dsr') or 'New'
        return super().create(vals_list)

    def action_submit(self):
        self.write({'status': 'submitted', 'submitted_date': fields.Datetime.now()})

    def action_under_review(self):
        self.write({'status': 'under_review'})

    def action_approve(self):
        self.write({'status': 'approved', 'approved_date': fields.Datetime.now()})

    def action_reject(self):
        self.write({'status': 'rejected'})
