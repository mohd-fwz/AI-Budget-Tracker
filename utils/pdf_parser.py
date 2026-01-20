"""
PDF parsing utilities for bank statement uploads
Handles password-protected and regular PDFs
Uses pdfplumber for table extraction and pikepdf for decryption
"""
import io
import pdfplumber
import pikepdf
from typing import List, Dict, Optional, Tuple
from .exceptions import PDFPasswordError, InvalidFileFormatError, ColumnDetectionError
from .csv_parser import _parse_date, _parse_amount, _find_column, _calculate_net_amount
from .income_detector import is_income_by_description


def is_pdf_encrypted(file_content: bytes) -> bool:
    """
    Check if PDF is password-protected

    Args:
        file_content: Raw PDF file bytes

    Returns:
        bool: True if encrypted, False otherwise

    Raises:
        InvalidFileFormatError: If file is not a valid PDF
    """
    try:
        with pikepdf.Pdf.open(io.BytesIO(file_content)) as pdf:
            # Successfully opened without password
            return False
    except pikepdf.PasswordError:
        # Password required
        return True
    except Exception as e:
        raise InvalidFileFormatError(f"Invalid or corrupted PDF file: {str(e)}")


def decrypt_pdf(file_content: bytes, password: str) -> bytes:
    """
    Decrypt password-protected PDF

    Args:
        file_content: Raw PDF file bytes
        password: PDF password

    Returns:
        bytes: Decrypted PDF content

    Raises:
        PDFPasswordError: If password is incorrect
        InvalidFileFormatError: If PDF is corrupted
    """
    try:
        with pikepdf.Pdf.open(io.BytesIO(file_content), password=password) as pdf:
            # Save decrypted PDF to memory
            output = io.BytesIO()
            pdf.save(output)
            return output.getvalue()
    except pikepdf.PasswordError:
        raise PDFPasswordError("Incorrect password. Please try again.")
    except Exception as e:
        raise InvalidFileFormatError(f"Failed to decrypt PDF: {str(e)}")


def _split_multiline_cells(rows: List[List[str]]) -> List[List[str]]:
    """
    Split rows where cells contain multiple lines into separate rows

    Some PDFs pack multiple transactions into a single cell with newlines.
    Example: Date cell might contain:
        '01/12/25\n02/12/25\n03/12/25'

    This function splits such rows into individual transaction rows.

    Args:
        rows: List of rows where each row is a list of cell values

    Returns:
        List of expanded rows with one transaction per row
    """
    expanded_rows = []

    for row in rows:
        # Check if any cell has newlines
        has_multiline = any('\n' in str(cell) for cell in row)

        if not has_multiline:
            # Normal row, keep as is
            expanded_rows.append(row)
            continue

        # Split all cells by newlines
        split_cells = [
            str(cell).split('\n') if cell else ['']
            for cell in row
        ]

        # Find max number of lines in any cell
        max_lines = max(len(cell_lines) for cell_lines in split_cells)

        # Create a new row for each line
        for line_idx in range(max_lines):
            new_row = []
            for cell_lines in split_cells:
                # Get the value at this line index, or empty string if not enough lines
                value = cell_lines[line_idx] if line_idx < len(cell_lines) else ''
                new_row.append(value.strip())

            # Only add non-empty rows
            if any(cell for cell in new_row if cell):
                expanded_rows.append(new_row)

    return expanded_rows


def _score_table_for_transactions(table: List[List[str]]) -> int:
    """
    Score a table based on how likely it is to contain transaction data

    Args:
        table: List of rows from pdfplumber

    Returns:
        int: Score (higher = more likely to be transaction table)

    Scoring criteria:
        - Has date column: +10
        - Has description/narration column: +10
        - Has amount/debit/credit column: +10
        - Has balance column: +5
        - Has account info columns (account no, holder, etc.): -20 (summary table)
        - Minimum row count (at least 3 rows): +5
    """
    if not table or len(table) < 2:
        return 0

    score = 0

    # Get potential header row (usually first row)
    header_row = table[0] if table else []
    header_text = ' '.join(str(cell).lower() for cell in header_row if cell)

    # Transaction table indicators
    transaction_keywords = [
        ('date', 10),
        ('transaction date', 10),
        ('posting date', 10),
        ('txn date', 10),
        ('value date', 10),
        ('description', 10),
        ('narration', 10),
        ('particulars', 10),
        ('details', 10),
        ('amount', 10),
        ('debit', 10),
        ('credit', 10),
        ('withdrawal', 10),
        ('deposit', 10),
        ('balance', 5),
    ]

    for keyword, points in transaction_keywords:
        if keyword in header_text:
            score += points

    # Account summary table indicators (negative score)
    summary_keywords = [
        'account no',
        'account number',
        'account type',
        'holder name',
        'primary holder',
        'secondary holder',
        'lien amount',
        'available balance',
        'currency code',
    ]

    for keyword in summary_keywords:
        if keyword in header_text:
            score -= 20  # Strong penalty for summary tables

    # Minimum row count bonus
    if len(table) >= 3:
        score += 5

    return score


def extract_tables_from_pdf(file_content: bytes) -> List[List[str]]:
    """
    Extract tables from PDF using pdfplumber with smart table selection

    Args:
        file_content: Raw PDF file bytes (decrypted if was encrypted)

    Returns:
        List[List[str]]: All rows from all tables in the PDF
                         Each row is a list of cell values

    Algorithm:
        1. Open PDF with pdfplumber
        2. Iterate through all pages
        3. Extract tables from each page
        4. Score each table for transaction likelihood
        5. Only include tables with positive scores
        6. Combine all rows, skipping empty rows
        7. Clean cell values (strip whitespace)
        8. Split multi-line cells into separate rows
    """
    all_rows = []

    try:
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            print(f"Processing PDF with {len(pdf.pages)} page(s)...")

            for page_num, page in enumerate(pdf.pages, 1):
                # Try default table extraction first
                tables = page.extract_tables()

                # Also try with custom settings optimized for wrapped text
                # Using "lines" strategy to detect actual table lines instead of relying on text
                table_settings = {
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "intersection_y_tolerance": 10,  # Allow more vertical tolerance for wrapped text
                }
                custom_tables = page.extract_tables(table_settings)

                # Combine both results, preferring default if both found tables
                if not tables and custom_tables:
                    tables = custom_tables
                    print(f"  Page {page_num}: Found {len(tables)} table(s) (using custom settings)")
                elif tables and custom_tables and len(custom_tables) > len(tables):
                    # If custom found more tables, use those
                    tables = custom_tables
                    print(f"  Page {page_num}: Found {len(tables)} table(s) (custom found more)")
                elif tables:
                    print(f"  Page {page_num}: Found {len(tables)} table(s)")

                for table_num, table in enumerate(tables, 1):
                    # Score this table
                    score = _score_table_for_transactions(table)
                    print(f"    Table {table_num}: Score = {score}")

                    # Skip tables with negative or zero scores (likely not transaction data)
                    if score <= 0:
                        print(f"    Table {table_num}: Skipped (not transaction table)")
                        continue

                    # Clean and add rows
                    for row in table:
                        if row and any(cell for cell in row if cell):  # Skip empty rows
                            # Clean cells: strip whitespace, handle None
                            cleaned_row = [
                                cell.strip() if cell else ''
                                for cell in row
                            ]
                            all_rows.append(cleaned_row)

        # Split multi-line cells
        print(f"Total rows extracted (before splitting): {len(all_rows)}")
        all_rows = _split_multiline_cells(all_rows)
        print(f"Total rows after splitting multi-line cells: {len(all_rows)}")

        return all_rows

    except Exception as e:
        raise InvalidFileFormatError(f"Failed to extract tables from PDF: {str(e)}")


def _find_column_index(normalized_headers: Dict[int, str], possible_names: List[str]) -> Optional[int]:
    """
    Find column index by possible column names

    Args:
        normalized_headers: Dict mapping {column_index: normalized_name}
        possible_names: List of possible column names to match

    Returns:
        int: Column index if found
        None: If no match found
    """
    for idx, header in normalized_headers.items():
        if header in possible_names:
            return idx
    return None


def _detect_header_row(rows: List[List[str]], cached_header: Optional[List[str]] = None) -> Tuple[int, List[str]]:
    """
    Detect which row contains the header

    Bank PDFs often have multiple rows before the actual data:
    - Logo/bank name
    - Account holder info
    - Statement period
    - THEN the column headers
    - THEN the transaction data

    Args:
        rows: All extracted rows
        cached_header: Header from previous page (for multi-page statements)

    Returns:
        Tuple[int, List[str]]: (header_row_index, header_values)

    Detection criteria:
        - Contains keywords: date, description, amount, transaction, etc.
        - Usually within first 20 rows
        - If row starts with dates (DD/MM/YY), it's data not header
    """
    import re

    for idx, row in enumerate(rows[:20]):  # Check first 20 rows
        # Check if this row looks like transaction data (starts with a date)
        first_cell = str(row[0] if row else '').strip()
        # Date patterns: DD/MM/YY, DD-MM-YY, DD/MM/YYYY, DD-MMM-YYYY
        date_patterns = [
            r'^\d{2}/\d{2}/\d{2}',  # DD/MM/YY
            r'^\d{2}-\d{2}-\d{2}',  # DD-MM-YY
            r'^\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'^\d{2}-[A-Za-z]{3}-\d{4}',  # DD-MMM-YYYY
        ]

        if any(re.match(pattern, first_cell) for pattern in date_patterns):
            # This row starts with a date - it's data, not a header
            # Use cached header if available, otherwise look for header before this
            if cached_header:
                print(f"Row {idx} is data (starts with date), using cached header")
                return -1, cached_header
            # No cached header and we found data - check if there's a header before this row
            if idx > 0:
                print(f"Row {idx} is data, using row 0 as header")
                return 0, rows[0]
            # First row is data and no cached header - this is a problem
            # Fall through to look for header keywords

        # Join row values and check for header keywords
        row_text = ' '.join(str(cell).lower() for cell in row if cell)

        # Check if this row looks like a header
        header_keywords = [
            'date', 'description', 'amount', 'transaction',
            'payee', 'merchant', 'debit', 'credit', 'balance',
            'narration', 'withdrawal', 'deposit'
        ]

        if any(keyword in row_text for keyword in header_keywords):
            # Verify it's not data that happens to have these words
            if not any(re.match(pattern, first_cell) for pattern in date_patterns):
                print(f"Detected header row at index {idx}: {row}")
                return idx, row

    # Default to first row if no header detected
    print("No clear header detected, using first row")
    return 0, rows[0] if rows else []


def parse_pdf_transactions(
    file_content: bytes,
    password: Optional[str] = None
) -> List[Dict]:
    """
    Main entry point for PDF parsing

    Args:
        file_content: Raw PDF file bytes
        password: Optional password for encrypted PDFs

    Returns:
        List[Dict]: List of transaction dictionaries with keys:
                   - date: datetime object
                   - description: str
                   - amount: float

    Raises:
        PDFPasswordError: If password needed or incorrect
        InvalidFileFormatError: If PDF corrupted or can't be parsed
        ColumnDetectionError: If required columns not found

    Flow:
        1. Check if encrypted → decrypt if password provided
        2. Extract tables using pdfplumber
        3. Detect header row
        4. Find date/description/amount columns
        5. Parse each transaction row
        6. Return cleaned transaction list
    """
    # Check if encrypted
    if is_pdf_encrypted(file_content):
        if not password:
            raise PDFPasswordError("PDF is password-protected. Please provide password.")
        # Decrypt
        file_content = decrypt_pdf(file_content, password)
        print("PDF decrypted successfully")

    # Extract tables
    rows = extract_tables_from_pdf(file_content)

    if not rows or len(rows) < 2:  # Need at least header + 1 data row
        raise InvalidFileFormatError("No transaction data found in PDF")

    # Detect header row (first pass without cached header)
    header_row_idx, header_row = _detect_header_row(rows, cached_header=None)

    # Cache the header for subsequent pages
    cached_header = header_row if header_row_idx >= 0 else None

    # If header_row_idx is -1, it means all rows are data (virtual header)
    if header_row_idx == -1:
        # This shouldn't happen on first detection, but handle it
        header_row_idx = -1
        data_start_idx = 0
    else:
        data_start_idx = header_row_idx + 1

    # Normalize headers
    normalized_headers = {
        i: col.lower().strip()
        for i, col in enumerate(header_row)
        if col
    }

    print(f"Normalized headers: {normalized_headers}")
    print(f"Header row index: {header_row_idx}, Data starts at: {data_start_idx}")

    # Find columns
    date_col_idx = _find_column_index(
        normalized_headers,
        ['date', 'transaction date', 'posting date', 'trans date', 'trans. date',
         'transaction', 'posted date', 'txn date', 'tran date', 'value date', 'booking date']
    )

    desc_col_idx = _find_column_index(
        normalized_headers,
        ['description', 'narration', 'payee', 'merchant', 'details', 'memo',
         'narrative', 'particulars', 'transaction details', 'transaction description',
         'remarks', 'transaction remarks']
    )

    amount_col_idx = _find_column_index(
        normalized_headers,
        ['amount', 'debit', 'withdrawal', 'withdrawalamt.', 'payment',
         'debit amount', 'withdrawals', 'withdrawal amt.', 'withdrawal amt',
         'dr', 'debit amt']
    )

    # Validate required columns found
    if date_col_idx is None:
        raise ColumnDetectionError(
            f"Could not identify date column. Found headers: {list(normalized_headers.values())}"
        )

    if desc_col_idx is None:
        raise ColumnDetectionError(
            f"Could not identify description column. Found headers: {list(normalized_headers.values())}"
        )

    if amount_col_idx is None:
        raise ColumnDetectionError(
            f"Could not identify amount column. Found headers: {list(normalized_headers.values())}"
        )

    print(f"Detected columns - Date: {date_col_idx}, Description: {desc_col_idx}, Amount: {amount_col_idx}")

    # Check for credit column (for net amount calculation)
    credit_col_idx = _find_column_index(
        normalized_headers,
        ['credit', 'deposit', 'deposits', 'depositamt.', 'credit amount',
         'deposit amt.', 'deposit amt', 'cr', 'credit amt']
    )

    # Parse transactions (skip header row and any rows before it)
    transactions = []

    for row_idx in range(data_start_idx, len(rows)):
        row = rows[row_idx]

        try:
            # Skip rows that are too short
            max_col_needed = max(date_col_idx, desc_col_idx, amount_col_idx)
            if len(row) <= max_col_needed:
                continue

            # Parse date
            date_cell = row[date_col_idx] if date_col_idx < len(row) else ''
            date = _parse_date(date_cell)

            # Parse description
            desc_cell = row[desc_col_idx] if desc_col_idx < len(row) else ''
            description = str(desc_cell).strip()

            # Validate date and description
            if not date:
                print(f"  Skipping row {row_idx}: Invalid date '{date_cell}'")
                continue

            if not description:
                print(f"  Skipping row {row_idx}: Empty description")
                continue

            # Handle amount calculation - check for separate debit/credit columns
            transaction_type = 'expense'  # Default

            if credit_col_idx is not None and credit_col_idx < len(row):
                # Both debit and credit columns exist - calculate net amount
                amount_cell = row[amount_col_idx] if amount_col_idx < len(row) else ''
                credit_cell = row[credit_col_idx]

                result = _calculate_net_amount(amount_cell, credit_cell)

                if result is None:
                    print(f"  Skipping row {row_idx}: Empty or balanced transaction")
                    continue

                amount = result['amount']
                transaction_type = result['type']
            else:
                # Single amount column only
                amount_cell = row[amount_col_idx] if amount_col_idx < len(row) else ''
                amount = _parse_amount(amount_cell)

                if not amount or amount == 0:
                    print(f"  Skipping row {row_idx}: Invalid amount '{amount_cell}'")
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
            print(f"  Warning: Skipping row {row_idx} due to error: {str(e)}")
            continue

    if not transactions:
        raise InvalidFileFormatError(
            "No valid transactions found in PDF. Please check the file format."
        )

    print(f"Successfully parsed {len(transactions)} transaction(s)")
    return transactions
