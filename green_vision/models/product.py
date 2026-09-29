from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def read(self, fields=None, load='_classic_read'):
        res = super().read(fields=fields, load=load)
        if not self.env.user.has_group('green_vision.group_show_product_reference'):
            for record in res:
                if 'default_code' in record:
                    record['default_code'] = False
        return res

    def _compute_display_name(self):
        super()._compute_display_name()
        if not self.env.user.has_group('green_vision.group_show_product_reference'):
            for template in self:
                if template.display_name and template.default_code and template.display_name.startswith(f'[{template.default_code}] '):
                    template.display_name = template.display_name.replace(f'[{template.default_code}] ', '', 1)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def read(self, fields=None, load='_classic_read'):
        res = super().read(fields=fields, load=load)
        if not self.env.user.has_group('green_vision.group_show_product_reference'):
            for record in res:
                if 'default_code' in record:
                    record['default_code'] = False
        return res

    def _compute_display_name(self):
        if not self.env.user.has_group('green_vision.group_show_product_reference'):
            records_with_context = self.with_context(display_default_code=False)
            super(ProductProduct, records_with_context)._compute_display_name()
            for record, record_ctx in zip(self, records_with_context):
                record.display_name = record_ctx.display_name
        else:
            super(ProductProduct, self)._compute_display_name()
