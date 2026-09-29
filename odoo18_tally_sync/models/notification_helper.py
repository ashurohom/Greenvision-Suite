from odoo import _

def tally_notification(title, message, notification_type='success', duration=5000, reload=True):
    """
    Builds a client action for a 5-second popup notification in Odoo 18.
    
    :param title: Notification title (str)
    :param message: Notification message body (str)
    :param notification_type: 'success', 'danger', 'warning', or 'info'
    :param duration: Milliseconds to display popup (default: 5000ms = 5 seconds)
    :param reload: Whether to trigger client view reload after notification dismisses
    :return: dict client action for display_notification
    """
    params = {
        'title': title,
        'message': message,
        'type': notification_type,
        'sticky': False,
        'duration': duration,
    }
    if reload:
        params['next'] = {'type': 'ir.actions.client', 'tag': 'reload'}

    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': params,
    }
