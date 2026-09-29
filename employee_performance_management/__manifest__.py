{
    'name': 'Employee Performance Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Comprehensive Employee Performance Management System',
    'description': """
        Employee Performance Management
        ===============================
        A clean, scalable, and modular performance management system supporting:
        - Job Description (JD)
        - Employee Performance Structure (KRA, KPA, KPI)
        - Performance Templates & Overrides
        - Fixed Tasks & Variable Tasks (via project.task)
        - Daily Status Report (DSR)
        - Manager Review
        - Monthly Task/Performance Evaluation
        - Overall Employee Performance Score
    """,
    'author': 'Expert Odoo Developer',
    'depends': ['hr', 'project', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/rating_data.xml',
        'views/menu.xml',
        'views/kra_views.xml',
        'views/kpa_views.xml',
        'views/kpi_views.xml',
        'views/template_views.xml',
        'views/rating_scale_views.xml',
        'views/hr_job_views.xml',
        'views/assignment_views.xml',
        'views/fixed_task_views.xml',
        'views/project_task_views.xml',
        'views/dsr_views.xml',
        'views/review_cycle_views.xml',
        'views/evaluation_views.xml',
        'views/dashboard_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
