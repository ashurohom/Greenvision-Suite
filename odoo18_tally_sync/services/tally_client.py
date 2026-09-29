import requests
import logging
from abc import ABC, abstractmethod

_logger = logging.getLogger(__name__)

class TallyClient(ABC):
    """Abstract Base Class for Tally API Communication."""

    def __init__(self, server_url, auth_type, username=None, password=None, token=None, timeout=30):
        self.server_url = server_url
        self.auth_type = auth_type
        self.username = username
        self.password = password
        self.token = token
        self.timeout = timeout

    @abstractmethod
    def test_connection(self):
        """Test the connection to the Tally Server."""
        pass

    @abstractmethod
    def send_request(self, payload):
        """Send a payload to Tally."""
        pass


class TallyAPIProvider(TallyClient):
    """Concrete Implementation of the Tally Client."""

    def _get_headers(self):
        headers = {'Content-Type': 'application/xml'}
        if self.auth_type == 'bearer' and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def _get_auth(self):
        if self.auth_type == 'basic' and self.username and self.password:
            return (self.username, self.password)
        return None

    def test_connection(self):
        """Placeholder for test connection. Replace with actual logic when API is known."""
        try:
            # Using a generic GET or basic POST to check connection
            response = requests.get(
                self.server_url, 
                headers=self._get_headers(), 
                auth=self._get_auth(),
                timeout=self.timeout
            )
            response.raise_for_status()
            return True, "Connection successful."
        except Exception as e:
            _logger.error("Tally test connection failed: %s", str(e))
            return False, str(e)

    def send_request(self, payload):
        """Sends request to Tally and checks for internal XML errors."""
        try:
            response = requests.post(
                self.server_url,
                data=payload,
                headers=self._get_headers(),
                auth=self._get_auth(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Tally often returns 200 OK even if there are XML/logic errors.
            response_text = response.text
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response_text)
                
                # Check for errors in Tally response
                errors = root.find('.//ERRORS')
                exceptions = root.find('.//EXCEPTIONS')
                line_error = root.find('.//LINEERROR')
                
                error_count = int(errors.text) if errors is not None and errors.text and errors.text.strip().isdigit() else 0
                exception_count = int(exceptions.text) if exceptions is not None and exceptions.text and exceptions.text.strip().isdigit() else 0
                error_msg = line_error.text if line_error is not None else ""
                
                if error_count > 0 or exception_count > 0 or error_msg:
                    # Include the raw response_text to see the exact error from Tally
                    return False, f"Tally Error: {error_msg} (Errors: {error_count}, Exceptions: {exception_count})\nRaw Response:\n{response_text}"
                    
            except ET.ParseError:
                pass # If it's not XML, just return true if no HTTP error
                
            return True, response_text
        except Exception as e:
            _logger.error("Tally send request failed: %s", str(e))
            return False, str(e)
