"""
Transaction Description Parser
Extracts structured data from Indian bank transaction descriptions

Handles patterns from major Indian banks:
- UPI IDs (name@paytm, number@ybl, etc.)
- Payment methods (UPI, NEFT, IMPS, RTGS, ATM, Card)
- Transaction reference IDs
- Merchant names
"""
import re
from typing import Dict, Optional


# Common UPI handle to merchant name mappings
UPI_MERCHANT_MAPPING = {
    # Payment Apps
    'paytm': 'Paytm',
    'ptybl': 'Paytm',  # Paytm Payments Bank Limited
    'ptyes': 'Paytm',  # Paytm YES Bank
    'phonepe': 'PhonePe',
    'ybl': 'PhonePe',  # Yes Bank Limited (PhonePe)
    'googlepay': 'Google Pay',
    'gpay': 'Google Pay',
    'okaxis': 'Google Pay',  # Axis Bank (Google Pay)
    'okhdfcbank': 'Google Pay',  # HDFC Bank (Google Pay)
    'okicici': 'Google Pay',  # ICICI Bank (Google Pay)
    'amazonpay': 'Amazon Pay',
    'apl': 'Amazon Pay',
    'bhim': 'BHIM UPI',

    # Food Delivery
    'swiggy': 'Swiggy',
    'zomato': 'Zomato',

    # E-commerce
    'flipkart': 'Flipkart',
    'amazon': 'Amazon',
    'icici': 'Amazon',  # Sometimes Amazon uses ICICI
    'myntra': 'Myntra',
    'ajio': 'Ajio',

    # Utilities
    'mobikwik': 'MobiKwik',
    'freecharge': 'Freecharge',
    'airtel': 'Airtel',
    'jio': 'Jio',
    'vodafone': 'Vodafone',

    # Transport
    'uber': 'Uber',
    'ola': 'Ola',
    'rapido': 'Rapido',

    # Others
    'irctc': 'IRCTC',
    'bookmyshow': 'BookMyShow',
}


def parse_transaction_description(description: str) -> Dict:
    """
    Extract structured data from transaction description

    Args:
        description: Raw transaction description from bank statement

    Returns:
        {
            'upi_id': str | None,
            'payment_method': str | None,  # UPI, NEFT, IMPS, RTGS, ATM, Card
            'transaction_ref': str | None,
            'merchant_name': str | None,
            'raw_description': str  # Original description
        }

    Examples:
        "UPI/297518249928/DR/Hai" -> {
            'payment_method': 'UPI',
            'transaction_ref': '297518249928',
            'merchant_name': 'Hai',
            ...
        }

        "e/YESB/-29411985@ptybl" -> {
            'upi_id': '29411985@ptybl',
            'payment_method': 'UPI',
            'merchant_name': 'Paytm',
            ...
        }
    """
    if not description:
        return _empty_result(description)

    result = {
        'upi_id': None,
        'payment_method': None,
        'transaction_ref': None,
        'merchant_name': None,
        'raw_description': description
    }

    # Extract UPI ID
    result['upi_id'] = extract_upi_id(description)

    # Extract payment method
    result['payment_method'] = extract_payment_method(description)

    # Extract transaction reference
    result['transaction_ref'] = extract_transaction_ref(description)

    # Extract merchant name
    result['merchant_name'] = extract_merchant_name(description, result['upi_id'])

    return result


def extract_upi_id(text: str) -> Optional[str]:
    """
    Extract UPI ID from transaction description

    Patterns:
    - name@bank (e.g., john@paytm)
    - number@bank (e.g., 9876543210@ybl)
    - merchant.bank@bank (e.g., swiggy.food@paytm)

    Args:
        text: Transaction description

    Returns:
        UPI ID string or None

    Examples:
        "e/YESB/-29411985@ptybl" -> "-29411985@ptybl"
        "UPI-john.doe@okaxis-123" -> "john.doe@okaxis"
        "Transfer to swiggy@paytm" -> "swiggy@paytm"
    """
    if not text:
        return None

    # Pattern 1: UPI ID with slash separator (IndusInd format - negative numbers)
    # Example: "/-29411985@ptybl" in "e/YESB/-29411985@ptybl"
    pattern1 = r'/(-\d+@[a-zA-Z]+)'
    match = re.search(pattern1, text)
    if match:
        return match.group(1)

    # Pattern 2: UPI prefix format "UPI-xxx@bank-..."
    # Extract just the "xxx@bank" part, excluding "UPI-" prefix and trailing parts
    # Example: "UPI-merchant@ybl-123456" -> "merchant@ybl"
    # Example: "UPI-zomato@paytm-Order123" -> "zomato@paytm"
    pattern2 = r'UPI-([a-zA-Z0-9._-]+@[a-zA-Z]+)(?:-|$)'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        return match.group(1)

    # Pattern 3: Standard UPI ID format with @ symbol
    # Match alphanumeric + . _ - followed by @bank_name
    # Allow dash in the ID itself (merchant-123@googlepay)
    # For multiple @, findall and return the last valid one
    pattern3 = r'(?:[/@\s]|^)([a-zA-Z0-9._-]+@[a-zA-Z]+)(?:[/\s-]|$)'
    matches = re.findall(pattern3, text)
    if matches:
        # Return the last match (most likely to be the actual UPI ID)
        return matches[-1]

    return None


def extract_payment_method(text: str) -> Optional[str]:
    """
    Extract payment method from transaction description

    Returns one of: UPI, NEFT, IMPS, RTGS, ATM, Card, Cash, Cheque

    Args:
        text: Transaction description

    Returns:
        Payment method string or None

    Examples:
        "UPI/297518249928/DR/Hai" -> "UPI"
        "NEFT Transfer to John" -> "NEFT"
        "ATM WDL-123456" -> "ATM"
        "POS Purchase" -> "Card"
    """
    if not text:
        return None

    text_upper = text.upper()

    # Priority order matters - check more specific patterns first

    # UPI patterns
    if 'UPI' in text_upper or '@' in text:
        return 'UPI'

    # RTGS (before IMPS/NEFT as it's more specific)
    if 'RTGS' in text_upper:
        return 'RTGS'

    # IMPS
    if 'IMPS' in text_upper:
        return 'IMPS'

    # NEFT
    if 'NEFT' in text_upper:
        return 'NEFT'

    # ATM
    if 'ATM' in text_upper or 'ATM WDL' in text_upper or 'CASH WITHDRAWAL' in text_upper:
        return 'ATM'

    # Cheque (check before Card to avoid false positives)
    if re.search(r'\bCHQ\b|\bCHEQUE\b|\bCHECK\b', text_upper):
        return 'Cheque'

    # Cash deposit/withdrawal (check before Card)
    if re.search(r'\bCASH\s+DEP(OSIT)?\b', text_upper):
        return 'Cash'

    # Card payments (POS, Debit Card, Credit Card) - check last to avoid catching CHQ/CASH
    if any(keyword in text_upper for keyword in ['POS', 'DEBIT CARD', 'CREDIT CARD', 'CARD PURCHASE']):
        return 'Card'

    # Default: None if no pattern matches
    return None


def extract_transaction_ref(text: str) -> Optional[str]:
    """
    Extract transaction reference ID from description

    Patterns:
    - UPI/123456789/DR
    - REF:ABC123456
    - Transaction ID: 987654321
    - Numbers after slashes

    Args:
        text: Transaction description

    Returns:
        Transaction reference ID or None

    Examples:
        "UPI/297518249928/DR/Hai" -> "297518249928"
        "NEFT-REF123456789" -> "REF123456789"
        "Transaction ID: 999888777" -> "999888777"
    """
    if not text:
        return None

    # Pattern 1: UPI reference (UPI/NUMBER/...)
    # Example: "UPI/297518249928/DR/Hai"
    pattern1 = r'UPI[/-](\d{8,})[/-]'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        return match.group(1)

    # Pattern 2: REF: or Reference: followed by alphanumeric
    # Example: "REF:ABC123456" or "Reference: 999888777" or "REF123456789"
    pattern2 = r'REF(?:ERENCE)?[:\s]*([A-Z0-9]+)'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        ref = match.group(1)
        # Make sure we got the actual reference, not just "REF"
        if ref.upper() != 'REF' and len(ref) > 3:
            return ref

    # Pattern 3: Transaction ID or TXN ID
    # Example: "Transaction ID: 123456789" or "TXN:ABC123"
    pattern3 = r'(?:TRANSACTION|TXN)\s*(?:ID)?[:\s]+([A-Z0-9]+)'
    match = re.search(pattern3, text, re.IGNORECASE)
    if match:
        return match.group(1)

    # Pattern 4: Alphanumeric code after slash or dash (R followed by digits)
    # Example: "NEFT/R123456789/John" -> "R123456789" or "NEFT-R123456789" -> "R123456789"
    pattern4 = r'[/-]([R]\d{7,})(?:[/-]|$)'
    match = re.search(pattern4, text)
    if match:
        return match.group(1)

    # Pattern 5: Long numeric sequences (10+ digits)
    # Example: "Transfer-1234567890123"
    pattern5 = r'\b(\d{10,})\b'
    match = re.search(pattern5, text)
    if match:
        return match.group(1)

    return None


def extract_merchant_name(text: str, upi_id: Optional[str] = None) -> Optional[str]:
    """
    Extract merchant name from transaction description

    Strategies:
    1. If UPI ID present, map to known merchant
    2. Extract name from common patterns (TO/FROM name)
    3. Extract last segment after slashes
    4. Clean up common banking keywords

    Args:
        text: Transaction description
        upi_id: Extracted UPI ID (optional, helps with mapping)

    Returns:
        Merchant name or None

    Examples:
        "UPI/297518249928/DR/Hai" -> "Hai"
        "swiggy@paytm" -> "Swiggy"
        "Transfer to John Doe" -> "John Doe"
    """
    if not text:
        return None

    # Strategy 1: Map UPI handle to merchant name
    if upi_id:
        merchant = _map_upi_to_merchant(upi_id)
        if merchant:
            return merchant

    # Strategy 2: Look for "TO" or "FROM" patterns
    # Example: "Transfer to John Doe" or "Transfer to John Doe REF:ABC"
    to_from_pattern = r'(?:TO|FROM)\s+([A-Za-z\s]+?)(?:\s+(?:REF|REFERENCE|TXN)|$)'
    match = re.search(to_from_pattern, text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        if len(name) > 2:  # Avoid single letters
            cleaned = _clean_merchant_name(name)
            if cleaned:  # Only return if cleaning produced a result
                return cleaned

    # Strategy 3: Extract last segment after slashes (common in UPI)
    # Example: "UPI/297518249928/DR/Hai" -> "Hai"
    # Example: "UPI/Amazon Pay/amazon@icici/DR" -> "Amazon Pay"
    if '/' in text:
        segments = text.split('/')
        # Get last non-empty segment that's not a banking code
        for segment in reversed(segments):
            segment = segment.strip()
            # Skip common banking codes and UPI IDs
            if segment and segment.upper() not in ['DR', 'CR', 'UPI', 'NEFT', 'IMPS', 'RTGS']:
                # Skip pure numbers and UPI IDs
                if not segment.isdigit() and '@' not in segment:
                    cleaned = _clean_merchant_name(segment)
                    if cleaned and len(cleaned) > 1:
                        return cleaned

    # Strategy 4: Extract name before @ in UPI ID (if no mapping found)
    if upi_id and '@' in upi_id:
        name_part = upi_id.split('@')[0]
        # Skip if it's just a number
        if not name_part.isdigit() and not name_part.startswith('-'):
            return _clean_merchant_name(name_part.replace('.', ' ').replace('_', ' '))

    # Strategy 5: Extract capitalized words (likely merchant names)
    # Example: "Payment to Amazon India" -> "Amazon India"
    cap_words_pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b'
    matches = re.findall(cap_words_pattern, text)
    if matches:
        # Get longest match (likely the merchant name)
        longest = max(matches, key=len)
        if len(longest) > 3:  # Avoid abbreviations
            return _clean_merchant_name(longest)

    return None


def _map_upi_to_merchant(upi_id: str) -> Optional[str]:
    """
    Map UPI ID to known merchant name

    Priority:
    1. Check name part (before @) for merchant names (swiggy@paytm -> Swiggy)
    2. Check handle (after @) for payment apps (123@ybl -> PhonePe)

    Args:
        upi_id: UPI ID (e.g., swiggy@paytm, 123@ybl)

    Returns:
        Merchant name or None
    """
    if not upi_id or '@' not in upi_id:
        return None

    name_part = upi_id.split('@')[0].lower()
    handle = upi_id.split('@')[1].lower()

    # List of bank handles (not merchant names)
    bank_handles = ['ybl', 'paytm', 'ptybl', 'ptyes', 'okaxis', 'okhdfcbank', 'okicici', 'icici', 'apl']

    # Priority 1: Check if name part matches known merchant (swiggy@paytm -> Swiggy)
    for key, merchant in UPI_MERCHANT_MAPPING.items():
        if key in name_part and key not in bank_handles:
            # Only match on name part if it's an actual merchant, not a bank handle
            return merchant

    # Priority 2: Check if handle matches known payment app (123@ybl -> PhonePe, user@ybl -> PhonePe)
    if handle in UPI_MERCHANT_MAPPING:
        # Return handle mapping if:
        # - name_part is numeric OR
        # - name_part is a generic word (user, customer, etc.) indicating it's not a merchant
        if name_part.replace('-', '').isdigit() or len(name_part) < 6:
            return UPI_MERCHANT_MAPPING[handle]

    return None


def _clean_merchant_name(name: str) -> str:
    """
    Clean up merchant name by removing common banking keywords

    Args:
        name: Raw merchant name

    Returns:
        Cleaned merchant name
    """
    # Remove common banking keywords
    keywords_to_remove = [
        'PAYMENT', 'TRANSFER', 'UPI', 'NEFT', 'IMPS', 'RTGS',
        'DEBIT', 'CREDIT', 'TRANSACTION', 'TXN',
        'DR', 'CR', 'A/C', 'ACCOUNT'
    ]

    cleaned = name
    for keyword in keywords_to_remove:
        # Case-insensitive replacement
        cleaned = re.sub(r'\b' + keyword + r'\b', '', cleaned, flags=re.IGNORECASE)

    # Remove extra whitespace
    cleaned = ' '.join(cleaned.split())

    # Capitalize properly
    cleaned = cleaned.title()

    return cleaned.strip()


def _empty_result(description: str = '') -> Dict:
    """
    Return empty result structure

    Args:
        description: Original description (optional)

    Returns:
        Empty result dictionary
    """
    return {
        'upi_id': None,
        'payment_method': None,
        'transaction_ref': None,
        'merchant_name': None,
        'raw_description': description
    }


def get_payment_method_emoji(payment_method: Optional[str]) -> str:
    """
    Get emoji representation for payment method (for UI display)

    Args:
        payment_method: Payment method string

    Returns:
        Emoji string
    """
    emoji_map = {
        'UPI': '📱',
        'NEFT': '🏦',
        'IMPS': '⚡',
        'RTGS': '💼',
        'ATM': '🏧',
        'Card': '💳',
        'Cheque': '📝',
        'Cash': '💵'
    }

    return emoji_map.get(payment_method, '💰')


# Utility function for bulk parsing
def parse_transactions_batch(descriptions: list) -> list:
    """
    Parse multiple transaction descriptions in batch

    Args:
        descriptions: List of transaction description strings

    Returns:
        List of parsed results
    """
    return [parse_transaction_description(desc) for desc in descriptions]
