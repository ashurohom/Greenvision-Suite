from odoo import models, fields
import logging
import time

_logger = logging.getLogger(__name__)

class ShopifyPaymentSyncService(models.AbstractModel):
    _name = 'shopify.payment.sync.service'
    _description = 'Shopify Payment Sync Service'

    def sync_payments(self, instance):
        log_vals = {
            'instance_id': instance.id,
            'sync_type': 'payment',
            'status': 'success',
        }
        start_time = time.time()
        imported = 0
        skipped = 0
        failed = 0
        error_msg = ""
        
        api_service = self.env['shopify.api.service']
        
        # Only import payments for paid orders or partially paid
        params = {'financial_status': 'paid'}
        if instance.last_sync_datetime:
            params['updated_at_min'] = instance.last_sync_datetime.isoformat()

        try:
            # First fetch orders that are paid
            orders = api_service.get(instance, '/orders.json', params=params)
            for order in orders:
                try:
                    # Then fetch transactions for these orders
                    order_id = str(order.get('id'))
                    transactions = api_service.get(instance, f'/orders/{order_id}/transactions.json')
                    for trans in transactions:
                        if trans.get('status') == 'success' and trans.get('kind') in ['sale', 'capture']:
                            res = self._sync_single_payment(instance, order_id, trans)
                            if res == 'imported':
                                imported += 1
                            else:
                                skipped += 1
                except Exception as e:
                    _logger.error("Failed to sync payments for order %s: %s", order.get('id'), str(e))
                    failed += 1
                    error_msg += f"Payment for Order {order.get('id')}: {str(e)}\n"
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

    def _sync_single_payment(self, instance, order_id, trans_data):
        payment_obj = self.env['shopify.payment']
        trans_id = str(trans_data.get('id'))
        
        existing = payment_obj.search([('transaction_id', '=', trans_id)], limit=1)
        if existing:
            return 'skipped'
            
        # Find the sale order in Odoo
        so = self.env['sale.order'].search([('shopify_order_id', '=', order_id)], limit=1)
        if not so:
            _logger.warning("Skipping payment %s: Sales Order %s not found in Odoo.", trans_id, order_id)
            return 'skipped'
        
        date_trans = trans_data.get('created_at')
        if date_trans:
            date_trans = date_trans[:19].replace('T', ' ')
            
        currency = self.env['res.currency'].search([('name', '=', trans_data.get('currency'))], limit=1)
            
        vals = {
            'transaction_id': trans_id,
            'payment_gateway': trans_data.get('gateway'),
            'amount': float(trans_data.get('amount') or 0.0),
            'currency_id': currency.id if currency else False,
            'payment_date': date_trans or fields.Datetime.now(),
            'payment_status': trans_data.get('status'),
            'sale_order_id': so.id if so else False,
            'company_id': instance.company_id.id,
        }
        
        payment_record = payment_obj.create(vals)
        
        # Odoo Accounting Integration: Auto-Invoice and Auto-Pay
        if so and so.state in ['sale', 'done']:
            # Find or create invoice
            invoices = so.invoice_ids.filtered(lambda inv: inv.state == 'posted' and inv.payment_state in ('not_paid', 'partial'))
            if not invoices:
                invoices = so._create_invoices()
                invoices.action_post()
                
            if invoices:
                invoice = invoices[0]
                # Default to a bank journal
                journal = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', instance.company_id.id)], limit=1)
                
                if journal:
                    payment_vals = {
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'partner_id': so.partner_id.id,
                        'amount': vals['amount'],
                        'currency_id': vals['currency_id'] or so.currency_id.id,
                        'date': vals['payment_date'],
                        'journal_id': journal.id,
                        'ref': trans_id,
                    }
                    acc_payment = self.env['account.payment'].create(payment_vals)
                    acc_payment.action_post()
                    
                    # Reconcile payment with the invoice
                    domain = [
                        ('account_type', 'in', ('asset_receivable', 'liability_payable')),
                        ('reconciled', '=', False),
                    ]
                    payment_lines = acc_payment.line_ids.filtered_domain(domain)
                    invoice_lines = invoice.line_ids.filtered_domain(domain)
                    
                    if payment_lines and invoice_lines:
                        (payment_lines + invoice_lines).reconcile()
                        
        return 'imported'
