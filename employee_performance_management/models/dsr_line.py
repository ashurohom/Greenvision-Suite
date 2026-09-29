from odoo import models, fields, api

class PerformanceDSRLine(models.Model):
    _name = 'employee.performance.dsr.line'
    _description = 'DSR Line'

    dsr_id = fields.Many2one('employee.performance.dsr', string='DSR', required=True, ondelete='cascade')
    task_type = fields.Selection([
        ('fixed', 'Fixed Task'),
        ('variable', 'Variable Task'),
        ('project', 'Project Task')
    ], string='Task Type', required=True)
    
    fixed_task_id = fields.Many2one('employee.performance.fixed.task.template', string='Fixed Task')
    project_task_id = fields.Many2one('project.task', string='Project/Variable Task')

    kra_id = fields.Many2one('employee.performance.kra', string='KRA', compute='_compute_performance_links', store=True)
    kpa_id = fields.Many2one('employee.performance.kpa', string='KPA', compute='_compute_performance_links', store=True)
    kpi_id = fields.Many2one('employee.performance.kpi', string='KPI', compute='_compute_performance_links', store=True)

    planned_hours = fields.Float('Planned Hours', compute='_compute_planned_hours', store=True, readonly=False)
    actual_hours = fields.Float('Actual Hours')
    progress = fields.Float('Progress (%)')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], string='Status', default='in_progress')
    remarks = fields.Text('Remarks')

    @api.depends('fixed_task_id', 'project_task_id', 'task_type')
    def _compute_performance_links(self):
        for line in self:
            if line.task_type == 'fixed' and line.fixed_task_id:
                line.kra_id = line.fixed_task_id.kra_id
                line.kpa_id = line.fixed_task_id.kpa_id
                line.kpi_id = line.fixed_task_id.kpi_id
            elif line.task_type in ('variable', 'project') and line.project_task_id:
                line.kra_id = line.project_task_id.kra_id
                line.kpa_id = line.project_task_id.kpa_id
                line.kpi_id = line.project_task_id.kpi_id

    @api.depends('fixed_task_id', 'task_type')
    def _compute_planned_hours(self):
        for line in self:
            if line.task_type == 'fixed' and line.fixed_task_id:
                line.planned_hours = line.fixed_task_id.planned_hours
            else:
                line.planned_hours = 0.0
