"""
CSV parsing utilities for bank statement uploads
Handles common bank statement formats and extracts transactions
NO PANDAS - Uses built-in csv module
"""
import csv
from datetime import datetime
from io import StringIO
import re
from utils.income_detector import is_income_by_description


def parse_csv_file(file_content):
    """
    Parse CSV file content and extract transactions

    Args:
        file_content (str or bytes): CSV file content

    Returns:
        list: List of transaction dictionaries
        None: If parsing fails

    Expected CSV formats (flexible):
        1. Date, Description, Amount
        2. Date, Description, Debit, Credit
        3. Transaction Date, Description, Amount, Balance
        4. Date, Payee, Amount, Category (optional)

    Common column names supported:
        - Date: date, transaction date, posting date, trans date
        - Description: description, payee, merchant, details, memo
        - Amount: amount, debit, credit, withdrawal, deposit
    """
    try:
        # Handle bytes or string
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8')

        # Read CSV
        csv_reader = csv.DictReader(StringIO(file_content))

        # Get headers and normalize them
        if not csv_reader.fieldnames:
            raise ValueError("CSV file has no headers")

        # Normalize column names (lowercase, strip whitespace)
        normalized_headers = {col: col.lower().strip() for col in csv_reader.fieldnames}

        # Identify column mappings with expanded patterns for multi-bank support
        date_col = _find_column(normalized_headers.values(), [
            'date', 'transaction date', 'posting date', 'trans date',
            'trans. date', 'txn date', 'tran date', 'value date', 'booking date'
        ])
        desc_col = _find_column(normalized_headers.values(), [
            'description', 'payee', 'merchant', 'details', 'memo', 'narrative',
            'narration', 'particulars', 'transaction description', 'remarks',
            'transaction remarks', 'transaction details'
        ])
        amount_col = _find_column(normalized_headers.values(), [
            'amount', 'debit', 'withdrawal', 'payment',
            'dr', 'debit amt', 'debit amount', 'withdrawal amt',
            'withdrawal amt.', 'withdrawalamt.', 'withdrawals'
        ])

        if not all([date_col, desc_col, amount_col]):
            raise ValueError("Could not identify required columns (date, description, amount)")

        # Find original column names
        date_orig = next(k for k, v in normalized_headers.items() if v == date_col)
        desc_orig = next(k for k, v in normalized_headers.items() if v == desc_col)
        amount_orig = next(k for k, v in normalized_headers.items() if v == amount_col)

        # Parse transactions
        transactions = []

        for row in csv_reader:
            try:
                # Parse date
                date = _parse_date(row.get(date_orig, ''))

                # Parse description
                description = str(row.get(desc_orig, '')).strip()

                # Validate date and description
                if not date:
                    continue
                if not description:
                    continue

                # Handle amount calculation - check for separate debit/credit columns
                credit_col = _find_column(normalized_headers.values(), [
                    'credit', 'deposit', 'deposits', 'depositamt.',
                    'cr', 'credit amt', 'credit amount', 'deposit amt', 'deposit amt.'
                ])

                transaction_type = 'expense'  # Default

                if credit_col and credit_col != amount_col:
                    # Both debit and credit columns exist - calculate net amount
                    credit_orig = next((k for k, v in normalized_headers.items() if v == credit_col), None)
                    if credit_orig:
                        result = _calculate_net_amount(
                            row.get(amount_orig, ''),
                            row.get(credit_orig, '')
                        )

                        if result is None:
                            continue  # Skip empty or balanced rows

                        amount = result['amount']
                        transaction_type = result['type']
                else:
                    # Single amount column only
                    amount = _parse_amount(row.get(amount_orig, ''))
                    if not amount or amount == 0:
                        continue

                    # Check if amount is negative (indicates income in single-column format)
                    if amount < 0:
                        amount = abs(amount)
                        transaction_type = 'income'
                    else:
                        transaction_type = 'expense'

                # FALLBACK: Check description for income indicators
                # This catches cases where column-based detection fails
                if transaction_type == 'expense' and is_income_by_description(description):
                    transaction_type = 'income'

                transactions.append({
                    'date': date,
                    'description': description,
                    'amount': amount,
                    'type': transaction_type
                })

            except Exception as e:
                # Skip problematic rows
                print(f"Warning: Skipping row due to error: {str(e)}")
                continue

        return transactions

    except Exception as e:
        print(f"CSV parsing error: {str(e)}")
        return None


def _find_column(columns, possible_names):
    """
    Find a column by possible names

    Args:
        columns (iterable): Column names
        possible_names (list): List of possible column names

    Returns:
        str: Actual column name found
        None: If no match found
    """
    for col in columns:
        if col in possible_names:
            return col

    return None


def _parse_date(date_value):
    """
    Parse date from various formats

    Args:
        date_value: Date value (string or datetime)

    Returns:
        datetime: Parsed date
        None: If parsing fails

    Supports formats:
        - YYYY-MM-DD
        - MM/DD/YYYY
        - DD/MM/YYYY
        - DD-Mon-YYYY
        - ISO format
    """
    if not date_value or date_value.strip() == '':
        return None

    if isinstance(date_value, datetime):
        return date_value

    # Try common date formats
    date_formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%d/%m/%y',  # DD/MM/YY format (e.g., 05/12/25)
        '%m-%d-%Y',
        '%d-%m-%Y',
        '%d-%m-%y',  # DD-MM-YY format
        '%Y/%m/%d',
        '%d-%b-%Y',
        '%d-%B-%Y',
        '%b %d, %Y',
        '%B %d, %Y',
    ]

    date_str = str(date_value).strip()

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def _parse_amount(amount_value):
    """
    Parse amount from various formats

    Args:
        amount_value: Amount value (string, float, or int)

    Returns:
        float: Parsed amount
        None: If parsing fails

    Handles:
        - Currency symbols ($, €, £, etc.)
        - Comma separators (1,234.56)
        - Parentheses for negative amounts (123.45)
        - Negative signs
    """
    if not amount_value or amount_value == '':
        return None

    # If already a number, return it
    if isinstance(amount_value, (int, float)):
        return float(amount_value)

    # Clean the string
    amount_str = str(amount_value).strip()

    # Remove currency symbols
    amount_str = re.sub(r'[$€£¥₹]', '', amount_str)

    # Remove whitespace
    amount_str = amount_str.replace(' ', '')

    # Handle parentheses (negative amounts)
    is_negative = False
    if amount_str.startswith('(') and amount_str.endswith(')'):
        is_negative = True
        amount_str = amount_str[1:-1]

    # Remove commas (thousand separators)
    amount_str = amount_str.replace(',', '')

    # Parse the number
    try:
        amount = float(amount_str)
        return -amount if is_negative else amount
    except ValueError:
        return None


def _calculate_net_amount(debit_value, credit_value):
    """
    Calculate net transaction amount from debit and credit columns

    Args:
        debit_value: Raw debit amount (str, float, or None)
        credit_value: Raw credit amount (str, float, or None)

    Returns:
        dict: {'amount': float, 'type': 'expense' | 'income'}
        None: If both values are 0/blank (skip row)

    Logic:
        - Both blank/0: Return None (skip)
        - Debit only: {'amount': debit, 'type': 'expense'}
        - Credit only: {'amount': credit, 'type': 'income'}
        - Both present: Calculate net = debit - credit
          - If net > 0: {'amount': net, 'type': 'expense'}
          - If net < 0: {'amount': abs(net), 'type': 'income'}
          - If net = 0: Return None (skip balanced transfer)
    """
    debit = _parse_amount(debit_value) or 0
    credit = _parse_amount(credit_value) or 0

    # Skip if both are zero
    if debit == 0 and credit == 0:
        return None

    # Calculate net
    net = debit - credit

    # Skip balanced transfers (net = 0)
    if net == 0:
        return None

    # Return result based on net
    if net > 0:
        return {'amount': net, 'type': 'expense'}
    else:
        return {'amount': abs(net), 'type': 'income'}


def validate_csv_format(file_content):
    """
    Validate that a CSV file has the expected format

    Args:
        file_content (str or bytes): CSV file content

    Returns:
        dict: Validation result with 'valid' (bool) and 'message' (str)
    """
    try:
        # Handle bytes or string
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8')

        # Read CSV
        csv_reader = csv.DictReader(StringIO(file_content))

        if not csv_reader.fieldnames:
            return {
                'valid': False,
                'message': 'CSV file has no headers'
            }

        # Normalize column names
        normalized_headers = {col: col.lower().strip() for col in csv_reader.fieldnames}

        # Check for required columns
        date_col = _find_column(normalized_headers.values(), ['date', 'transaction date', 'posting date', 'trans date'])
        desc_col = _find_column(normalized_headers.values(), ['description', 'payee', 'merchant', 'details', 'memo'])
        amount_col = _find_column(normalized_headers.values(), ['amount', 'debit', 'credit', 'withdrawal', 'deposit'])

        if not date_col:
            return {
                'valid': False,
                'message': 'Missing date column. Expected one of: date, transaction date, posting date'
            }

        if not desc_col:
            return {
                'valid': False,
                'message': 'Missing description column. Expected one of: description, payee, merchant, details'
            }

        if not amount_col:
            return {
                'valid': False,
                'message': 'Missing amount column. Expected one of: amount, debit, credit, withdrawal'
            }

        # Count rows
        row_count = sum(1 for _ in csv_reader)

        if row_count == 0:
            return {
                'valid': False,
                'message': 'CSV file is empty'
            }

        return {
            'valid': True,
            'message': f'Valid CSV format. Found {row_count} rows.',
            'rows': row_count
        }

    except Exception as e:
        return {
            'valid': False,
            'message': f'CSV validation error: {str(e)}'
        }
