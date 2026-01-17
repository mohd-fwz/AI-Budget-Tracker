"""
Unified parser orchestrator
Single interface for parsing CSV, PDF, and Excel files
"""
from typing import List, Dict, Optional
from .file_detector import detect_file_type
from .csv_parser import parse_csv_file
from .pdf_parser import parse_pdf_transactions
from .excel_parser import parse_excel_file
from .date_range_extractor import extract_date_range
from .exceptions import (
    UnsupportedFormatError,
    InvalidFileFormatError,
    PDFPasswordError
)


def parse_statement(
    file_content: bytes,
    file_type: Optional[str] = None,
    password: Optional[str] = None
) -> Dict:
    """
    Unified interface for parsing bank statements
    Automatically detects format and routes to appropriate parser

    Args:
        file_content: Raw file bytes
        file_type: Optional file type hint ('pdf', 'excel_xlsx', 'excel_xls', 'csv')
                  If None, will auto-detect
        password: Optional password for encrypted PDFs

    Returns:
        dict: {
            'transactions': List[Dict],  # Parsed transactions
            'date_range': Dict,          # Date range info
            'file_type': str,            # Detected file type
            'row_count': int             # Number of transactions
        }

    Raises:
        UnsupportedFormatError: If file format not supported
        InvalidFileFormatError: If file is corrupted
        PDFPasswordError: If PDF needs password
        ColumnDetectionError: If required columns not found

    Example:
        result = parse_statement(file_bytes, password='secret123')
        transactions = result['transactions']
        date_range = result['date_range']
    """
    # Auto-detect file type if not provided
    if file_type is None:
        file_type = detect_file_type(file_content)
        print(f"Auto-detected file type: {file_type}")

    # Validate file type
    supported_types = ['pdf', 'excel_xlsx', 'excel_xls', 'csv']
    if file_type not in supported_types:
        raise UnsupportedFormatError(
            f"Unsupported file type: {file_type}. "
            f"Supported formats: {', '.join(supported_types)}"
        )

    # Route to appropriate parser
    transactions = []

    try:
        if file_type == 'pdf':
            print("Using template-aware PDF parser...")
            # Try template-aware parser first
            from .template_aware_parser import parse_pdf_with_template
            transactions = parse_pdf_with_template(file_content, password)

        elif file_type == 'excel_xlsx':
            print("Using Excel (.xlsx) parser...")
            transactions = parse_excel_file(file_content, 'excel_xlsx')

        elif file_type == 'excel_xls':
            print("Using Excel (.xls) parser...")
            transactions = parse_excel_file(file_content, 'excel_xls')

        elif file_type == 'csv':
            print("Using CSV parser...")
            # CSV parser expects string, not bytes
            if isinstance(file_content, bytes):
                file_content_str = file_content.decode('utf-8')
            else:
                file_content_str = file_content

            transactions = parse_csv_file(file_content_str)

            if transactions is None:
                raise InvalidFileFormatError("Failed to parse CSV file")

    except (PDFPasswordError, InvalidFileFormatError, UnsupportedFormatError) as e:
        # Re-raise these specific exceptions
        raise

    except Exception as e:
        # Wrap unexpected errors
        raise InvalidFileFormatError(f"Failed to parse {file_type} file: {str(e)}")

    # Extract date range
    date_range_info = extract_date_range(transactions)

    # Return unified result
    return {
        'transactions': transactions,
        'date_range': date_range_info,
        'file_type': file_type,
        'row_count': len(transactions)
    }


def parse_statement_with_summary(
    file_content: bytes,
    file_type: Optional[str] = None,
    password: Optional[str] = None
) -> Dict:
    """
    Parse statement and include summary statistics

    Args:
        file_content: Raw file bytes
        file_type: Optional file type hint
        password: Optional password for encrypted PDFs

    Returns:
        dict: {
            'transactions': List[Dict],
            'date_range': Dict,
            'file_type': str,
            'row_count': int,
            'summary': {
                'total_amount': float,
                'average_amount': float,
                'max_amount': float,
                'min_amount': float,
                'date_summary': str
            }
        }
    """
    # Parse using main function
    result = parse_statement(file_content, file_type, password)

    transactions = result['transactions']

    # Calculate summary statistics
    if transactions:
        amounts = [t['amount'] for t in transactions]
        summary = {
            'total_amount': sum(amounts),
            'average_amount': sum(amounts) / len(amounts),
            'max_amount': max(amounts),
            'min_amount': min(amounts),
            'date_summary': f"{result['date_range']['min_date']} to {result['date_range']['max_date']}"
        }
    else:
        summary = {
            'total_amount': 0,
            'average_amount': 0,
            'max_amount': 0,
            'min_amount': 0,
            'date_summary': 'No transactions'
        }

    result['summary'] = summary
    return result
