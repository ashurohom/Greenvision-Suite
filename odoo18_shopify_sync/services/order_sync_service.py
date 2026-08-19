from odoo import models, fields
import logging
import time
import json
from datetime import datetime

_logger = logging.getLogger(__name__)

class ShopifyOrderSyncService(models.AbstractModel):
    _name = 'shopify.order.sync.service'
    _description = 'Shopify Order Sync Service'

    def sync_orders(self, instance):
        log_vals = {
            'instance_id': instance.id,
            'sync_type': 'order',
            'status': 'success',
        }
        start_time = time.time()
        imported = 0
        skipped = 0
        failed = 0
        error_msg = ""
        
        api_service = self.env['shopify.api.service']
        
        params = {'status': 'any'}
        if instance.last_sync_datetime:
            params['updated_at_min'] = instance.last_sync_datetime.isoformat()

        try:
            orders = api_service.get(instance, '/orders.json', params=params)
            for order in orders:
                try:
                    res = self._sync_single_order(instance, order)
                    if res == 'imported':
                        imported += 1
                    else:
                        skipped += 1
                except Exception as e:
                    _logger.error("Failed to sync order %s: %s", order.get('id'), str(e))
                    failed += 1
                    error_msg += f"Order {order.get('id')}: {str(e)}\n"
        except Exception as e:
            log_vals['status'] = 'failed'
            error_msg = str(e)
            
        if failed > 0 and log_vals['status'] == 'success':
            log_vals['status'] = 'partial'
            
        log_vals.update({
            'duration': time.time() - start_time,
            'imported_count': imported,
            'skipped_count': skipped,
            'failed_count': failed,
            'error_message': error_msg,
        })
        self.env['shopify.sync.log'].create(log_vals)

    def _sync_single_order(self, instance, order_data):
        so_obj = self.env['sale.order']
        shopify_id = str(order_data.get('id'))
        
        existing = so_obj.search([('shopify_order_id', '=', shopify_id)], limit=1)
        if existing:
            # For phase 1, we just skip or update basic status
            existing.write({
                'shopify_financial_status': order_data.get('financial_status'),
                'shopify_fulfillment_status': order_data.get('fulfillment_status'),
            })
            return 'skipped'
            
        # 1. Resolve Customer
        customer = False
        cust_data = order_data.get('customer')
        if cust_data:
            self.env['shopify.customer.sync.service']._sync_single_customer(cust_data)
            customer = self.env['res.partner'].search([('shopify_customer_id', '=', str(cust_data.get('id')))], limit=1)
            
        if not customer:
            # Fallback for orders without customer details
            customer = self.env.user.company_id.partner_id
            
        # 2. Date
        date_order = order_data.get('created_at')
        if date_order:
            # Simple parsing, Odoo handles standard ISO natively in fields.Datetime.to_datetime, 
            # but string slicing works for simple ISO
            date_order = date_order[:19].replace('T', ' ')
            
        # 3. Create Sale Order
        so_vals = {
            'partner_id': customer.id,
            'shopify_order_id': shopify_id,
            'client_order_ref': order_data.get('name'),
            'date_order': date_order or fields.Datetime.now(),
            'company_id': instance.company_id.id,
            'shopify_financial_status': order_data.get('financial_status'),
            'shopify_fulfillment_status': order_data.get('fulfillment_status'),
            'shopify_raw_json': json.dumps(order_data),
        }
        
        order = so_obj.create(so_vals)
        
        # 4. Order Lines
        product_service = self.env['shopify.product.sync.service']
        for line in order_data.get('line_items', []):
            product = product_service.get_or_create_product(line)
            
            self.env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': product.id,
                'name': line.get('title') or product.name,
                'product_uom_qty': float(line.get('quantity') or 1.0),
                'price_unit': float(line.get('price') or 0.0),
            })
            
        # Shipping line (optional but good practice)
        for shipping in order_data.get('shipping_lines', []):
            product = product_service.get_or_create_product({'name': 'Shipping', 'sku': 'SHIPPING', 'price': shipping.get('price')})
            self.env['sale.order.line'].create({
                'order_id': order.id,
                'product_id': product.id,
                'name': shipping.get('title') or 'Shipping',
                'product_uom_qty': 1.0,
                'price_unit': float(shipping.get('price') or 0.0),
            })
            
        # Auto-confirm the order
        if order.state in ['draft', 'sent']:
            order.action_confirm()
            
        return 'imported'
