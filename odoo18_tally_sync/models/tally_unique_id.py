# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    tally_customer_id = fields.Char(
        string='Tally Customer ID',
        readonly=True,
        copy=False,
        index=True,
        help='Automatically generated unique ID for Customer (e.g. CUST-00001).',
    )
    tally_vendor_id = fields.Char(
        string='Tally Vendor ID',
        readonly=True,
        copy=False,
        index=True,
        help='Automatically generated unique ID for Vendor (e.g. VEND-00001).',
    )

    _sql_constraints = [
        ('tally_customer_id_uniq', 'unique(tally_customer_id)', 'Tally Customer ID must be unique!'),
        ('tally_vendor_id_uniq', 'unique(tally_vendor_id)', 'Tally Vendor ID must be unique!'),
    ]

    @api.constrains('tally_customer_id')
    def _check_tally_customer_id_unique(self):
        for record in self:
            if record.tally_customer_id:
                duplicate = self.search([
                    ('tally_customer_id', '=', record.tally_customer_id),
                    ('id', '!=', record.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(_("Tally Customer ID '%s' already exists for contact '%s'.") % (
                        record.tally_customer_id, duplicate.display_name or duplicate.name
                    ))

    @api.constrains('tally_vendor_id')
    def _check_tally_vendor_id_unique(self):
        for record in self:
            if record.tally_vendor_id:
                duplicate = self.search([
                    ('tally_vendor_id', '=', record.tally_vendor_id),
                    ('id', '!=', record.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(_("Tally Vendor ID '%s' already exists for contact '%s'.") % (
                        record.tally_vendor_id, duplicate.display_name or duplicate.name
                    ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            is_vendor = (
                vals.get('supplier_rank', 0) > 0 or
                self.env.context.get('res_partner_search_mode') in ('supplier', 'vendor') or
                self.env.context.get('default_supplier_rank', 0) > 0
            )
            is_customer = (
                vals.get('customer_rank', 0) > 0 or
                self.env.context.get('res_partner_search_mode') == 'customer' or
                self.env.context.get('default_customer_rank', 0) > 0
            )

            # Standard contacts without explicit rank default to customer
            if not is_vendor and not is_customer:
                is_customer = True

            if is_customer and not vals.get('tally_customer_id'):
                vals['tally_customer_id'] = self.env['ir.sequence'].next_by_code('tally.customer.id') or False

            if is_vendor and not vals.get('tally_vendor_id'):
                vals['tally_vendor_id'] = self.env['ir.sequence'].next_by_code('tally.vendor.id') or False

        return super().create(vals_list)

    def write(self, vals):
        # Prevent manual modification or clearing of already generated unique IDs
        clean_vals = dict(vals)
        if 'tally_customer_id' in clean_vals:
            for record in self:
                if record.tally_customer_id and clean_vals.get('tally_customer_id') != record.tally_customer_id:
                    clean_vals.pop('tally_customer_id', None)
                    break
        if 'tally_vendor_id' in clean_vals:
            for record in self:
                if record.tally_vendor_id and clean_vals.get('tally_vendor_id') != record.tally_vendor_id:
                    clean_vals.pop('tally_vendor_id', None)
                    break

        res = super().write(clean_vals)

        # Generate IDs if partner gains supplier_rank or customer_rank later and doesn't have an ID yet
        for record in self:
            updates = {}
            if record.supplier_rank > 0 and not record.tally_vendor_id:
                updates['tally_vendor_id'] = self.env['ir.sequence'].next_by_code('tally.vendor.id') or False
            if record.customer_rank > 0 and not record.tally_customer_id:
                updates['tally_customer_id'] = self.env['ir.sequence'].next_by_code('tally.customer.id') or False
            if updates:
                super(ResPartner, record).write(updates)

        return res

    def copy(self, default=None):
        default = dict(default or {})
        default['tally_customer_id'] = False
        default['tally_vendor_id'] = False
        return super().copy(default)


class AccountMove(models.Model):
    _inherit = 'account.move'

    tally_invoice_id = fields.Char(
        string='Tally Invoice ID',
        readonly=True,
        copy=False,
        index=True,
        help='Automatically generated unique ID for Customer Invoice (e.g. INV-00001).',
    )
    tally_purchase_id = fields.Char(
        string='Tally Purchase/Bill ID',
        readonly=True,
        copy=False,
        index=True,
        help='Automatically generated unique ID for Vendor Bill / Purchase (e.g. PUR-00001).',
    )
    tally_credit_note_id = fields.Char(
        string='Tally Credit Note ID',
        readonly=True,
        copy=False,
        index=True,
        help='Automatically generated unique ID for Customer Credit Note (e.g. CCN-00001).',
    )
    tally_debit_note_id = fields.Char(
        string='Tally Debit Note ID',
        readonly=True,
        copy=False,
        index=True,
        help='Automatically generated unique ID for Vendor Debit Note / Credit Note (e.g. DBN-00001).',
    )

    _sql_constraints = [
        ('tally_invoice_id_uniq', 'unique(tally_invoice_id)', 'Tally Invoice ID must be unique!'),
        ('tally_purchase_id_uniq', 'unique(tally_purchase_id)', 'Tally Purchase/Bill ID must be unique!'),
        ('tally_credit_note_id_uniq', 'unique(tally_credit_note_id)', 'Tally Credit Note ID must be unique!'),
        ('tally_debit_note_id_uniq', 'unique(tally_debit_note_id)', 'Tally Debit Note ID must be unique!'),
    ]

    @api.constrains('tally_invoice_id', 'tally_purchase_id', 'tally_credit_note_id', 'tally_debit_note_id')
    def _check_tally_move_unique_ids(self):
        for record in self:
            for field_name, label in [
                ('tally_invoice_id', _('Tally Invoice ID')),
                ('tally_purchase_id', _('Tally Purchase/Bill ID')),
                ('tally_credit_note_id', _('Tally Credit Note ID')),
                ('tally_debit_note_id', _('Tally Debit Note ID')),
            ]:
                val = record[field_name]
                if val:
                    duplicate = self.search([
                        (field_name, '=', val),
                        ('id', '!=', record.id)
                    ], limit=1)
                    if duplicate:
                        raise ValidationError(_("%s '%s' already exists for move '%s'.") % (
                            label, val, duplicate.name or duplicate.id
                        ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            move_type = vals.get('move_type') or self.env.context.get('default_move_type')
            if move_type == 'out_invoice' and not vals.get('tally_invoice_id'):
                vals['tally_invoice_id'] = self.env['ir.sequence'].next_by_code('tally.invoice.id') or False
            elif move_type == 'in_invoice' and not vals.get('tally_purchase_id'):
                vals['tally_purchase_id'] = self.env['ir.sequence'].next_by_code('tally.purchase.id') or False
            elif move_type == 'out_refund' and not vals.get('tally_credit_note_id'):
                vals['tally_credit_note_id'] = self.env['ir.sequence'].next_by_code('tally.credit.note.id') or False
            elif move_type == 'in_refund' and not vals.get('tally_debit_note_id'):
                vals['tally_debit_note_id'] = self.env['ir.sequence'].next_by_code('tally.debit.note.id') or False

        return super().create(vals_list)

    def write(self, vals):
        clean_vals = dict(vals)
        protected_fields = ['tally_invoice_id', 'tally_purchase_id', 'tally_credit_note_id', 'tally_debit_note_id']
        for field in protected_fields:
            if field in clean_vals:
                for record in self:
                    if record[field] and clean_vals.get(field) != record[field]:
                        clean_vals.pop(field, None)
                        break

        res = super().write(clean_vals)

        # Backfill unique ID if existing record did not have one
        for record in self:
            updates = {}
            if record.move_type == 'out_invoice' and not record.tally_invoice_id:
                updates['tally_invoice_id'] = self.env['ir.sequence'].next_by_code('tally.invoice.id') or False
            elif record.move_type == 'in_invoice' and not record.tally_purchase_id:
                updates['tally_purchase_id'] = self.env['ir.sequence'].next_by_code('tally.purchase.id') or False
            elif record.move_type == 'out_refund' and not record.tally_credit_note_id:
                updates['tally_credit_note_id'] = self.env['ir.sequence'].next_by_code('tally.credit.note.id') or False
            elif record.move_type == 'in_refund' and not record.tally_debit_note_id:
                updates['tally_debit_note_id'] = self.env['ir.sequence'].next_by_code('tally.debit.note.id') or False
            if updates:
                super(AccountMove, record).write(updates)

        return res

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'tally_invoice_id': False,
            'tally_purchase_id': False,
            'tally_credit_note_id': False,
            'tally_debit_note_id': False,
        })
        return super().copy(default)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    tally_customer_payment_id = fields.Char(
        string='Tally Customer Payment ID',
        readonly=True,
        copy=False,
        index=True,
        help='Automatically generated unique ID for Customer Payment (e.g. CPAY-00001).',
    )
    tally_vendor_payment_id = fields.Char(
        string='Tally Vendor Payment ID',
        readonly=True,
        copy=False,
        index=True,
        help='Automatically generated unique ID for Vendor Payment (e.g. VPAY-00001).',
    )

    _sql_constraints = [
        ('tally_customer_payment_id_uniq', 'unique(tally_customer_payment_id)', 'Tally Customer Payment ID must be unique!'),
        ('tally_vendor_payment_id_uniq', 'unique(tally_vendor_payment_id)', 'Tally Vendor Payment ID must be unique!'),
    ]

    @api.constrains('tally_customer_payment_id', 'tally_vendor_payment_id')
    def _check_tally_payment_unique_ids(self):
        for record in self:
            for field_name, label in [
                ('tally_customer_payment_id', _('Tally Customer Payment ID')),
                ('tally_vendor_payment_id', _('Tally Vendor Payment ID')),
            ]:
                val = record[field_name]
                if val:
                    duplicate = self.search([
                        (field_name, '=', val),
                        ('id', '!=', record.id)
                    ], limit=1)
                    if duplicate:
                        raise ValidationError(_("%s '%s' already exists for payment '%s'.") % (
                            label, val, duplicate.name or duplicate.id
                        ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            payment_type = vals.get('payment_type') or self.env.context.get('default_payment_type')
            if payment_type == 'inbound' and not vals.get('tally_customer_payment_id'):
                vals['tally_customer_payment_id'] = self.env['ir.sequence'].next_by_code('tally.customer.payment.id') or False
            elif payment_type == 'outbound' and not vals.get('tally_vendor_payment_id'):
                vals['tally_vendor_payment_id'] = self.env['ir.sequence'].next_by_code('tally.vendor.payment.id') or False

        return super().create(vals_list)

    def write(self, vals):
        clean_vals = dict(vals)
        protected_fields = ['tally_customer_payment_id', 'tally_vendor_payment_id']
        for field in protected_fields:
            if field in clean_vals:
                for record in self:
                    if record[field] and clean_vals.get(field) != record[field]:
                        clean_vals.pop(field, None)
                        break

        res = super().write(clean_vals)

        # Backfill unique ID if existing record did not have one
        for record in self:
            updates = {}
            if record.payment_type == 'inbound' and not record.tally_customer_payment_id:
                updates['tally_customer_payment_id'] = self.env['ir.sequence'].next_by_code('tally.customer.payment.id') or False
            elif record.payment_type == 'outbound' and not record.tally_vendor_payment_id:
                updates['tally_vendor_payment_id'] = self.env['ir.sequence'].next_by_code('tally.vendor.payment.id') or False
            if updates:
                super(AccountPayment, record).write(updates)

        return res

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'tally_customer_payment_id': False,
            'tally_vendor_payment_id': False,
        })
        return super().copy(default)
