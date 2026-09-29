from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class TallyConfiguration(models.Model):
    _name = 'tally.configuration'
    _description = 'Tally Integration Configuration'

    name = fields.Char(string='Name', required=True, default='Tally Server')
    server_url = fields.Char(string='Server URL', required=True, help='URL of the Tally ERP 9 / Prime server API.')
    company_name = fields.Char(string='Company Name', help='Target company name in Tally.')
    username = fields.Char(string='Username')
    password = fields.Char(string='Password')
    api_token = fields.Char(string='API Token')
    auth_type = fields.Selection([
        ('basic', 'Basic'),
        ('bearer', 'Bearer'),
        ('none', 'None')
    ], string='Authentication Type', default='none', required=True)
    
    connection_timeout = fields.Integer(string='Connection Timeout', default=30)
    auto_sync = fields.Boolean(string='Auto Sync', default=False)
    active = fields.Boolean(string='Active', default=True)
    
    last_connection = fields.Datetime(string='Last Connection', readonly=True)
    connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('disconnected', 'Not Connected'),
        ('failed', 'Not Connected')
    ], string='Connection Status', default='disconnected', readonly=True)

    def action_test_connection(self):
        """Tests the connection to the Tally Server via the TallyAPIProvider service."""
        for record in self:
            from ..services.tally_client import TallyAPIProvider
            
            client = TallyAPIProvider(
                server_url=record.server_url,
                auth_type=record.auth_type,
                username=record.username,
                password=record.password,
                token=record.api_token,
                timeout=record.connection_timeout
            )
            
            success, message = client.test_connection()
            
            record.last_connection = fields.Datetime.now()
            if success:
                record.connection_status = 'connected'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Successfully connected to Tally server.'),
                        'type': 'success',
                        'sticky': False,
                        'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                    }
                }
            else:
                record.connection_status = 'disconnected'
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Connection Failed'),
                        'message': _('Failed to connect to Tally server: %s' % message),
                        'type': 'danger',
                        'sticky': True,
                        'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                    }
                }

    @api.model
    def _cron_check_connection(self):
        """Automatically checks connection status for all active Tally configurations."""
        configs = self.search([('active', '=', True)])
        from ..services.tally_client import TallyAPIProvider
        for record in configs:
            client = TallyAPIProvider(
                server_url=record.server_url,
                auth_type=record.auth_type,
                username=record.username,
                password=record.password,
                token=record.api_token,
                timeout=record.connection_timeout
            )
            success, message = client.test_connection()
            
            record.last_connection = fields.Datetime.now()
            if success:
                record.connection_status = 'connected'
            else:
                record.connection_status = 'disconnected'
