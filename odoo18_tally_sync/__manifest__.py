{
    'name': 'Tally Integration Framework',
    'version': '18.0.1.0.0',
    'summary': 'Reusable Tally Integration Framework for Odoo 18',
    'description': """
        A generic and reusable Tally Integration Framework for synchronizing data 
        between Odoo and Tally ERP. 
        Supports:
        - Customer Import/Export
        - Vendor Import/Export
    """,
    'category': 'Extra Tools',
    'author': 'Expert Odoo Developer',
    'depends': ['base', 'contacts', 'product', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/menu.xml',
        'views/tally_configuration_views.xml',
        'views/sync_log_views.xml',
        'views/partner_views.xml',
        'views/product_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
        'views/account_journal_views.xml',
        'views/manual_sync_views.xml',
        'views/server_actions.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'odoo18_tally_sync/static/src/js/tally_notification.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
