from .tally_client import TallyAPIProvider
from .xml_generator import XMLGenerator
from .xml_parser import XMLParser
from odoo import _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class CustomerService:
    """Service to handle customer synchronization."""

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

    def export_customer(self, partner):
        """Exports a single customer to Tally."""
        payload = XMLGenerator.generate_partner_xml(partner, partner_type='Customer')
        success, response = self.client.send_request(payload)
        
        # Parse response here
        parsed_response = XMLParser.parse_response(response) if success else {}
        
        # The true validation of success depends on Tally's response logic
        return success, response, payload

    def import_customers(self):
        """Imports customers from Tally."""
        payload = "<ENVELOPE><HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER><BODY><EXPORTDATA><REQUESTDESC><REPORTNAME>List of Accounts</REPORTNAME></REQUESTDESC></EXPORTDATA></BODY></ENVELOPE>"
        success, response = self.client.send_request(payload)
        
        if success:
            ledgers = XMLParser.parse_ledgers(response, group_filter="Sundry Debtors")
            Partner = self.env['res.partner']
            for ledger in ledgers:
                partner = Partner.search([('tally_id', '=', ledger['guid'])], limit=1)
                if not partner:
                    # Fallback to match by name
                    partner = Partner.search([('name', '=ilike', ledger['name'])], limit=1)
                
                vals = {
                    'name': ledger['name'],
                    'tally_id': ledger['guid'],
                    'email': ledger['email'] or False,
                    'phone': ledger['phone'] or False,
                    'mobile': ledger.get('mobile') or False,
                    'street': ledger.get('street') or False,
                    'street2': ledger.get('street2') or False,
                    'city': ledger.get('city') or False,
                    'zip': ledger.get('zip') or False,
                    'customer_rank': 1,
                    'sync_status': 'success',
                }
                # Remove False keys to prevent overwriting existing details if empty from Tally
                if partner:
                    update_vals = {k: v for k, v in vals.items() if v}
                    partner.write(update_vals)
                else:
                    Partner.create(vals)
        
        self.env['tally.sync.log'].create({
            'operation': 'import',
            'model': 'customer',
            'status': 'success' if success else 'failed',
            'request': payload,
            'response': response,
            'error_message': '' if success else response,
        })
        
        return success, response, len(ledgers) if success else 0
