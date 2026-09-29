from odoo import models, fields

class Employee(models.Model):
    _inherit = 'hr.employee'

    performance_assignment_ids = fields.One2many('employee.performance.assignment', 'employee_id', string='Performance Assignments')
