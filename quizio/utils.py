import base64
from io import BytesIO
from urllib.parse import parse_qs

import qrcode


def parse_query_string(query_string):
    """
    Parses a byte string query string into a dictionary.

    Args:
        query_string (bytes): The raw query string from `scope["query_string"]`.

    Returns:
        dict: The parsed query parameters as a dictionary.
    """
    decoded_string = query_string.decode(
        "utf-8"
    )  # Decode the byte string to a normal string
    parsed_params = parse_qs(decoded_string)  # Parse the query string
    # Convert lists to single values if there's only one value for a key
    return {
        key: value[0] if len(value) == 1 else value
        for key, value in parsed_params.items()
    }


def generate_qr_code(string: str):
    """Generate a QR code for the join link and return it as a base64 string."""
    img = qrcode.make(string)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return qr_code_base64
