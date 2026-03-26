import hashlib
import urllib.parse
from django.conf import settings

def generate_payfast_signature(data, pass_phrase=None):
    """
    Generates a PayFast signature for the given data dictionary.
    """
    # Create query string
    payload = ""
    for key, value in data.items():
        if value is not None and value != "":
            payload += f"{key}={urllib.parse.quote_plus(str(value).strip())}&"
    
    # Remove last ampersand
    payload = payload[:-1]
    
    if pass_phrase:
        payload += f"&passphrase={urllib.parse.quote_plus(pass_phrase.strip())}"
        
    return hashlib.md5(payload.encode()).hexdigest()

def get_payfast_url():
    if settings.DEBUG:
        return "https://sandbox.payfast.co.za/eng/process"
    return "https://www.payfast.co.za/eng/process"
