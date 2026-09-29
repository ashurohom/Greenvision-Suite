from odoo import models, fields, api

class PerformanceEvaluation(models.Model):
    _name = 'employee.performance.evaluation'
    _description = 'Monthly Performance Evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Evaluation Number', default='New', readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id')
    job_id = fields.Many2one('hr.job', string='Job Position', related='employee_id.job_id')
    manager_id = fields.Many2one('hr.employee', string='Manager', related='employee_id.parent_id')
    review_cycle_id = fields.Many2one('employee.performance.review.cycle', string='Review Cycle', required=True)
    start_date = fields.Date('Start Date', related='review_cycle_id.start_date')
    end_date = fields.Date('End Date', related='review_cycle_id.end_date')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('manager_review', 'Manager Review'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    overall_score = fields.Float('Overall Score (%)', compute='_compute_overall_score', store=True, tracking=True)
    rating_id = fields.Many2one('employee.performance.rating.scale', string='Performance Rating', compute='_compute_rating', store=True)
    manager_comments = fields.Text('Manager Comments')
    employee_comments = fields.Text('Employee Comments')

    line_ids = fields.One2many('employee.performance.evaluation.line', 'evaluation_id', string='Score Details')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('employee.performance.evaluation') or 'New'
        return super().create(vals_list)

    @api.depends('line_ids.score', 'line_ids.weightage')
    def _compute_overall_score(self):
        for eval in self:
            kra_lines = eval.line_ids.filtered(lambda l: l.type == 'kra')
            total_score = sum(l.score * (l.weightage / 100.0) for l in kra_lines if l.weightage)
            eval.overall_score = total_score

    @api.depends('overall_score')
    def _compute_rating(self):
        for eval in self:
            rating = self.env['employee.performance.rating.scale'].search([
                ('min_score', '<=', eval.overall_score),
                ('max_score', '>=', eval.overall_score)
            ], limit=1)
            eval.rating_id = rating.id

    def action_calculate(self):
        self.env['performance.score.calculator'].calculate_evaluation(self)
        self.write({'status': 'in_progress'})

    def action_submit_manager(self):
        self.write({'status': 'manager_review'})

    def action_complete(self):
        self.write({'status': 'completed'})

    def action_cancel(self):
        self.write({'status': 'cancelled'})
