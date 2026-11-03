import re

def redact_pii(text: str) -> str:
    """
    Redacts Personally Identifiable Information (PII) like emails and phone numbers.
    """
    # Simple email regex
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    text = re.sub(email_pattern, "[EMAIL_REDACTED]", text)
    
    # Simple phone number regex (US format for example)
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    text = re.sub(phone_pattern, "[PHONE_REDACTED]", text)
    
    return text
