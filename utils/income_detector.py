"""
Income detection utilities
Detects income/credit transactions from description keywords
Used as a fallback when column-based detection fails
"""
import re


# Keywords that indicate income/credit transactions
INCOME_KEYWORDS = [
    # Cash deposits
    'cashdeposit', 'cash deposit', 'cash dep', 'cdm deposit', 'atm deposit',

    # Salary and wages
    'salary', 'wages', 'payroll', 'income', 'stipend', 'bonus', 'commission',

    # Bank transfers (often income)
    'neft cr', 'imps cr', 'rtgs cr', 'upi cr',  # Indian banking credits
    'tpt',  # Third Party Transfer (often income)
    'fund transfer cr', 'transfer from', 'received from',

    # Refunds
    'refund', 'cashback', 'cash back', 'reversal', 'credit reversal',
    'chargeback', 'refunded', 'return credit',

    # Interest and dividends
    'interest credit', 'int credit', 'interest paid', 'dividend',
    'interest on', 'int on fd', 'int on rd',

    # Reimbursements
    'reimbursement', 'reimb', 'expense claim',

    # Other credits
    'credit', 'cr-', '-cr', 'credited', 'deposit',
    'maturity proceeds', 'fd maturity', 'rd maturity',
    'insurance claim', 'settlement',
]

# Patterns that strongly indicate income (regex patterns)
INCOME_PATTERNS = [
    r'\bCASHDEPOSIT\b',           # Exact match for CASHDEPOSIT
    r'\bTPT[-\s]',                 # TPT- or TPT followed by space (Third Party Transfer)
    r'\bNEFT[-/]CR\b',            # NEFT credit
    r'\bIMPS[-/]CR\b',            # IMPS credit
    r'\bRTGS[-/]CR\b',            # RTGS credit
    r'\bUPI[-/]CR\b',             # UPI credit
    r'\bSALARY\b',                # Salary
    r'\bREFUND\b',                # Refund
    r'\bCASHBACK\b',              # Cashback
    r'\bINTEREST\s*CREDIT',       # Interest credit
    r'\bDIVIDEND\b',              # Dividend
    r'\bMATURITY\b',              # FD/RD maturity
    r'/CR\b',                     # Ends with /CR
    r'\bCR\s*$',                  # Ends with CR
]


def is_income_by_description(description):
    """
    Detect if a transaction is income/credit based on description keywords

    Args:
        description (str): Transaction description

    Returns:
        bool: True if the description indicates income/credit

    This is a fallback detection method used when:
    - Bank statement doesn't have separate debit/credit columns
    - Amount column doesn't use negative values for credits
    """
    if not description:
        return False

    desc_lower = description.lower()
    desc_upper = description.upper()

    # Check regex patterns first (more precise)
    for pattern in INCOME_PATTERNS:
        if re.search(pattern, desc_upper, re.IGNORECASE):
            return True

    # Check keyword presence
    for keyword in INCOME_KEYWORDS:
        # Use word boundary-like matching to avoid partial matches
        # e.g., "credit" shouldn't match "credit card payment"

        # Skip generic words that might cause false positives
        if keyword in ['credit', 'deposit', 'transfer from']:
            # For generic keywords, be more strict - check context
            # "credit card" is expense, "credit to account" is income
            if keyword == 'credit':
                # Skip if followed by "card" or preceded by debit indicators
                if 'credit card' in desc_lower or 'cc ' in desc_lower:
                    continue
                if 'debit' in desc_lower:
                    continue
            if keyword == 'deposit':
                # Skip if it's "deposit to" (could be a payment)
                if 'deposit to' in desc_lower:
                    continue

        # Check for keyword presence
        if keyword in desc_lower:
            return True

    return False


def detect_transaction_type(description, amount=None, has_credit_column=False):
    """
    Comprehensive transaction type detection

    Args:
        description (str): Transaction description
        amount (float, optional): Transaction amount (negative = income in some formats)
        has_credit_column (bool): Whether the source has a separate credit column

    Returns:
        str: 'income' or 'expense'

    Priority:
    1. If has_credit_column=True, trust the column-based detection (caller handles this)
    2. If amount is negative, it's income
    3. If description matches income keywords, it's income
    4. Default to expense
    """
    # If amount is negative, it's typically income (bank statement convention)
    if amount is not None and amount < 0:
        return 'income'

    # Check description for income indicators
    if is_income_by_description(description):
        return 'income'

    # Default to expense
    return 'expense'
