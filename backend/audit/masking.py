import re
from typing import Any, Dict, List, Union

SENSITIVE_KEYS = {
    "password", "passwd", "secret", "token", "access_token", "refresh_token",
    "api_key", "apikey", "authorization", "ssn", "aadhaar", "credit_card",
    "private_key", "pin"
}

MASK_VALUE = "***MASKED***"


def mask_sensitive_data(data: Any) -> Any:
    """
    Recursively masks sensitive fields in dictionaries or lists.
    """
    if data is None:
        return None

    if isinstance(data, dict):
        masked_dict = {}
        for key, val in data.items():
            key_lower = str(key).lower()
            if any(sens in key_lower for sens in SENSITIVE_KEYS):
                masked_dict[key] = MASK_VALUE
            else:
                masked_dict[key] = mask_sensitive_data(val)
        return masked_dict

    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]

    elif isinstance(data, str):
        # Additional regex patterns if needed (e.g. Bearer tokens)
        if re.match(r"^Bearer\s+[A-Za-z0-9\-._~+/]+=*$", data, re.IGNORECASE):
            return "Bearer ***MASKED***"
        return data

    return data
