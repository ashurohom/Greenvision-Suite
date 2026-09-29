from .tally_client import TallyAPIProvider
from .xml_generator import XMLGenerator
from .xml_parser import XMLParser
from odoo import _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ProductService:
    """Service to handle product synchronization."""

    def __init__(self, env):
        self.env = env
        config = self.env['tally.configuration'].search([('active', '=', True)], limit=1)
        if not config:
            raise UserError(_("No active Tally configuration found."))
        
        self.client = TallyAPIProvider(
            server_url=config.server_url,
            auth_type=config.auth_type,
            username=config.username,
            password=config.password,
            token=config.api_token,
            timeout=config.connection_timeout
        )

    def import_products(self):
        """Imports products from Tally."""
        # Using a payload to request List of Accounts but specifically looking for Stock Items
        # A more specific request for Stock Items could be "List of Accounts" with a different configuration
        # but in Tally we can use Collection of Stock Items
        payload = """<ENVELOPE>
  <HEADER>
    <TALLYREQUEST>Export Data</TALLYREQUEST>
  </HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Accounts</REPORTNAME>
        <STATICVARIABLES>
            <ACCOUNTTYPE>Stock Items</ACCOUNTTYPE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>"""
        success, response = self.client.send_request(payload)
        
        count = 0
        if success:
            items = XMLParser.parse_stock_items(response)
            Product = self.env['product.template']
            for item in items:
                product = Product.search([('tally_id', '=', item['guid'])], limit=1)
                if not product:
                    product = Product.search([('name', '=ilike', item['name'])], limit=1)
                
                vals = {
                    'name': item['name'],
                    'tally_id': item['guid'],
                    'sync_status': 'success',
                }
                if item['rate']:
                    vals['list_price'] = item['rate']
                
                if product:
                    product.write(vals)
                else:
                    product = Product.create(vals)
                
                # Optional: Handle starting inventory (this requires stock.quant which is more complex)
                # We will skip inventory adjustment for now unless it's specifically required, 
                # but setting the product is the first step.
                
                count += 1
        
        self.env['tally.sync.log'].create({
            'operation': 'import',
            'model': 'product',
            'status': 'success' if success else 'failed',
            'request': payload,
            'response': response,
            'error_message': '' if success else response,
        })
        
        return success, response, count

    def export_product(self, product):
        """Exports a single product to Tally as a Stock Item."""
        payload = XMLGenerator.generate_product_xml(product)
        success, response = self.client.send_request(payload)
        return success, response, payload
