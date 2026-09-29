from odoo import models, fields

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    tally_ledger_name = fields.Char(
        string='Tally Ledger Name',
        help='Name of the corresponding Bank or Cash ledger in Tally. If left blank, the Journal name or default account name is used.'
    )
