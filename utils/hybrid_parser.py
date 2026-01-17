"""
Hybrid PDF parser - combines multiple extraction strategies for robustness
Tries text extraction first, falls back to positional extraction if patterns change
"""
import re
import io
import pdfplumber
from typing import List, Dict, Optional
from datetime import datetime
from .bank_template_loader import BankTemplate
from .csv_parser import _parse_date, _parse_amount, _calculate_net_amount


def parse_with_hybrid_strategy(
    file_content: bytes,
    template: BankTemplate
) -> List[Dict]:
    """
    Hybrid parsing strategy that tries multiple approaches:
    1. Regex pattern matching (fast, precise when format matches)
    2. Positional text extraction (flexible, handles format variations)
    3. Smart table reconstruction (robust fallback)

    Args:
        file_content: Raw PDF bytes
        template: Bank template

    Returns:
        List[Dict]: Parsed transactions
    """
    transactions = []

    # Strategy 1: Try regex pattern first (current approach)
    print(f"Strategy 1: Trying regex pattern extraction...")
    try:
        from .text_based_parser import parse_transactions_from_text
        transactions = parse_transactions_from_text(file_content, template)

        if transactions and len(transactions) > 5:
            print(f"[OK] Success with regex: {len(transactions)} transactions")
            return transactions
        else:
            print(f"[SKIP] Regex found only {len(transactions)} transactions, trying next strategy...")
    except Exception as e:
        print(f"[SKIP] Regex extraction failed: {e}")

    # Strategy 2: Positional text extraction (more flexible)
    print(f"Strategy 2: Trying positional text extraction...")
    try:
        transactions = parse_with_positional_extraction(file_content, template)

        if transactions and len(transactions) > 5:
            print(f"[OK] Success with positional extraction: {len(transactions)} transactions")
            return transactions
        else:
            print(f"[SKIP] Positional extraction found only {len(transactions)} transactions, trying next strategy...")
    except Exception as e:
        print(f"[SKIP] Positional extraction failed: {e}")

    # Strategy 3: Smart table reconstruction
    print(f"Strategy 3: Trying smart table reconstruction...")
    try:
        transactions = parse_with_smart_table_reconstruction(file_content, template)

        if transactions:
            print(f"[OK] Success with smart table reconstruction: {len(transactions)} transactions")
            return transactions
    except Exception as e:
        print(f"[SKIP] Smart table reconstruction failed: {e}")

    # All strategies failed
    print(f"[SKIP] All extraction strategies failed")
    return []


def parse_with_positional_extraction(
    file_content: bytes,
    template: BankTemplate
) -> List[Dict]:
    """
    Extract transactions using column positions detected from headers
    More flexible than regex - handles format variations

    Algorithm:
    1. Find "Date" column position (x-coordinate)
    2. Find "Withdrawal"/"Deposit" column positions
    3. Extract text at those x-positions for each line
    4. Parse dates and amounts from extracted text
    """
    transactions = []

    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            # Extract text with layout preserved
            text = page.extract_text(layout=True)
            if not text:
                continue

            lines = text.split('\n')

            # Find header line to detect column positions
            header_line = None
            header_idx = -1

            for idx, line in enumerate(lines):
                line_lower = line.lower()
                # Look for characteristic header keywords
                if ('date' in line_lower and
                    'particulars' in line_lower and
                    'withdrawal' in line_lower):
                    header_line = line
                    header_idx = idx
                    break

            if not header_line or header_idx == -1:
                continue

            # Detect column positions from header
            date_pos = header_line.lower().find('date')
            withdrawal_pos = header_line.lower().find('withdrawal')
            deposit_pos = header_line.lower().find('deposit')

            if date_pos == -1 or withdrawal_pos == -1:
                continue

            print(f"  Page {page_num}: Column positions detected - Date:{date_pos}, Withdrawal:{withdrawal_pos}, Deposit:{deposit_pos}")

            # Parse transaction lines after header
            for line_idx in range(header_idx + 1, len(lines)):
                line = lines[line_idx]

                # Skip empty lines
                if not line.strip():
                    continue

                # Skip lines that are clearly not transactions
                if any(skip in line for skip in template.skip_rows):
                    continue

                try:
                    # Extract date (first ~15 characters typically contain date)
                    date_text = line[date_pos:date_pos+15].strip() if len(line) > date_pos else ''

                    # Try to parse date
                    date = None
                    for date_format in ['%d %b %Y', '%d-%b-%Y', '%d/%m/%Y', '%d/%m/%y']:
                        try:
                            # Extract just the date part (first word sequence that looks like a date)
                            date_match = re.search(r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}', date_text)
                            if not date_match:
                                date_match = re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', date_text)

                            if date_match:
                                date = datetime.strptime(date_match.group(), date_format)
                                break
                        except ValueError:
                            continue

                    if not date:
                        continue

                    # Extract amounts from their column positions
                    # Withdrawal amount (typically 10-15 chars wide)
                    withdrawal_text = ''
                    if len(line) > withdrawal_pos:
                        withdrawal_text = line[withdrawal_pos:withdrawal_pos+12].strip()

                    # Deposit amount
                    deposit_text = ''
                    if deposit_pos != -1 and len(line) > deposit_pos:
                        deposit_text = line[deposit_pos:deposit_pos+12].strip()

                    # Description is between date and amounts
                    description = ''
                    if len(line) > date_pos + 15 and withdrawal_pos > date_pos + 15:
                        description = line[date_pos+15:withdrawal_pos].strip()

                    # Parse amounts
                    result = _calculate_net_amount(withdrawal_text, deposit_text)
                    if result is None:
                        continue

                    transactions.append({
                        'date': date,
                        'description': description or 'Transaction',
                        'amount': result['amount'],
                        'type': result['type']
                    })

                except Exception as e:
                    # Skip problematic lines
                    continue

    return transactions


def parse_with_smart_table_reconstruction(
    file_content: bytes,
    template: BankTemplate
) -> List[Dict]:
    """
    Reconstruct table from merged cells by analyzing text structure

    Algorithm:
    1. Extract all text lines
    2. Identify lines with dates (transaction lines)
    3. Parse each transaction line using multiple regex patterns
    4. Extract date, description, amounts using flexible patterns
    """
    transactions = []

    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')

            for line in lines:
                # Skip empty or very short lines
                if len(line.strip()) < 15:
                    continue

                # Skip header lines and summary rows
                if any(skip in line for skip in template.skip_rows):
                    continue
                if 'Date' in line and 'Particulars' in line:
                    continue

                # Try to parse as transaction line
                # Pattern: Date (flexible) + Description + Amounts
                # Example: "28 Dec 2025 UPI/297518249928/DR/Hai S2621703 49.00 0.00 41.38"

                # Extract date at start of line
                date = None
                date_formats = [
                    (r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', '%d %b %Y'),
                    (r'(\d{1,2}-[A-Za-z]{3}-\d{4})', '%d-%b-%Y'),
                    (r'(\d{1,2}/\d{1,2}/\d{4})', '%d/%m/%Y'),
                    (r'(\d{1,2}/\d{1,2}/\d{2})', '%d/%m/%y'),
                ]

                for pattern, fmt in date_formats:
                    match = re.search(pattern, line)
                    if match:
                        try:
                            date = datetime.strptime(match.group(1), fmt)
                            # Remove date from line for easier amount extraction
                            line_after_date = line[match.end():].strip()
                            break
                        except ValueError:
                            continue

                if not date:
                    continue

                # Extract amounts (looking for patterns like "49.00" or "1,234.56")
                # Usually there are 2-3 amounts at the end: withdrawal, deposit, balance
                amount_pattern = r'[\d,]+\.\d{2}'
                amounts = re.findall(amount_pattern, line_after_date)

                if len(amounts) < 2:
                    continue

                # Typically: amounts[-3] = withdrawal, amounts[-2] = deposit, amounts[-1] = balance
                # Or: amounts[-2] = withdrawal, amounts[-1] = deposit (if no balance)
                withdrawal_str = amounts[-3] if len(amounts) >= 3 else amounts[-2]
                deposit_str = amounts[-2] if len(amounts) >= 3 else amounts[-1]

                # Extract description (everything between date and first amount)
                # Find position of first amount
                first_amount_pos = line_after_date.find(amounts[0])
                description = line_after_date[:first_amount_pos].strip() if first_amount_pos > 0 else ''

                # Limit description length for readability
                if len(description) > 50:
                    description = description[:50] + '...'

                # Calculate net amount
                result = _calculate_net_amount(withdrawal_str, deposit_str)
                if result is None:
                    continue

                transactions.append({
                    'date': date,
                    'description': description or 'Transaction',
                    'amount': result['amount'],
                    'type': result['type']
                })

    return transactions
