"""
Text-based transaction parser for banks with complex PDF layouts
Uses regex patterns to extract transactions directly from text
"""
import re
import io
import pdfplumber
from typing import List, Dict
from datetime import datetime
from .bank_template_loader import BankTemplate
from .csv_parser import _parse_date, _parse_amount, _calculate_net_amount


def parse_transactions_from_text(
    file_content: bytes,
    template: BankTemplate
) -> List[Dict]:
    """
    Parse transactions using text extraction and regex patterns

    Args:
        file_content: Raw PDF bytes (decrypted if needed)
        template: Bank template with regex pattern

    Returns:
        List[Dict]: Parsed transactions

    Algorithm:
        1. Extract text from all pages (or specific page if page_hint provided)
        2. Apply regex pattern to find transaction rows
        3. Parse each match into a transaction dict
        4. Handle debit/credit columns
        5. Skip rows matching skip_rows patterns
    """
    transactions = []

    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            print(f"Text-based parsing: {template.bank_name}")
            print(f"Total pages: {len(pdf.pages)}")

            # Determine which pages to process
            pages_to_process = []
            if template.page_hint:
                # Specific page (1-indexed)
                if template.page_hint <= len(pdf.pages):
                    pages_to_process = [pdf.pages[template.page_hint - 1]]
                    print(f"Processing page {template.page_hint} only")
            else:
                # All pages
                pages_to_process = pdf.pages
                print(f"Processing all {len(pdf.pages)} pages")

            # Extract text from each page and find transactions
            for page_num, page in enumerate(pages_to_process, 1):
                text = page.extract_text()
                if not text:
                    continue

                # Apply regex pattern
                pattern = re.compile(template.regex_pattern, re.MULTILINE)
                matches = pattern.finditer(text)

                for match in matches:
                    try:
                        transaction = _parse_match(match, template)
                        if transaction:
                            transactions.append(transaction)
                    except Exception as e:
                        # Skip problematic matches
                        print(f"  Warning: Skipping match due to error: {e}")
                        continue

        print(f"Text-based parsing found {len(transactions)} transactions")
        return transactions

    except Exception as e:
        print(f"Text-based parsing error: {e}")
        return []


def _parse_match(match: re.Match, template: BankTemplate) -> Dict:
    """
    Parse a regex match into a transaction dictionary

    Args:
        match: Regex match object
        template: Bank template

    Returns:
        Dict: Transaction with date, description, amount, type
        None: If transaction should be skipped
    """
    groups = match.groupdict()

    # Parse date
    date_str = groups.get('date', '').strip()
    if not date_str:
        return None

    # Check if this is a skip row
    description = groups.get('description', '').strip()
    if not description:
        return None

    for skip_pattern in template.skip_rows:
        if skip_pattern.lower() in description.lower():
            return None

    # Parse the date
    date = _parse_date_with_format(date_str, template.date_format)
    if not date:
        return None

    # Parse amounts
    debit_str = groups.get('debit', '').strip()
    credit_str = groups.get('credit', '').strip()

    # Calculate net amount
    result = _calculate_net_amount(debit_str, credit_str)
    if result is None:
        return None

    return {
        'date': date,
        'description': description,
        'amount': result['amount'],
        'type': result['type']
    }


def _parse_date_with_format(date_str: str, date_format: str) -> datetime:
    """
    Parse date string using template's date format

    Args:
        date_str: Date string
        date_format: Format like "DD/MM/YY", "DD-MMM-YYYY"

    Returns:
        datetime object or None
    """
    # Map template format to Python strptime format
    format_mapping = {
        'DD/MM/YY': '%d/%m/%y',
        'DD-MM-YY': '%d-%m-%y',
        'DD/MM/YYYY': '%d/%m/%Y',
        'DD-MM-YYYY': '%d-%m-%Y',
        'DD-MMM-YYYY': '%d-%b-%Y',
        'DD-MMM-YY': '%d-%b-%y',
        'DD MMM YYYY': '%d %b %Y',
        'D MMM YYYY': '%d %b %Y',
        'D/MM/YYYY': '%d/%m/%Y',
    }

    python_format = format_mapping.get(date_format)
    if not python_format:
        # Fall back to generic date parsing
        return _parse_date(date_str)

    try:
        return datetime.strptime(date_str, python_format)
    except ValueError:
        # Fall back to generic parsing
        return _parse_date(date_str)
