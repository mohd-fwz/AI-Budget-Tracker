"""
File type detection and validation utilities
Uses magic bytes to reliably detect file types
"""
import io
from typing import Optional
from .exceptions import UnsupportedFormatError, InvalidFileFormatError

# Magic bytes for file type detection
MAGIC_BYTES = {
    'pdf': b'%PDF',
    'xlsx': b'PK\x03\x04',  # XLSX is a ZIP file
    'xls': b'\xD0\xCF\x11\xE0',  # OLE2 format
}


def detect_file_type(file_content: bytes) -> str:
    """
    Detect file type using magic bytes

    Args:
        file_content: Raw file bytes

    Returns:
        str: One of 'pdf', 'excel_xlsx', 'excel_xls', 'csv', 'unknown'

    Detection Logic:
        1. Check first 4 bytes for magic bytes
        2. PDF: Starts with %PDF
        3. XLSX: Starts with PK (ZIP signature)
        4. XLS: Starts with 0xD0CF11E0 (OLE2 signature)
        5. CSV: Assume text-based if no binary signatures found
    """
    if not file_content:
        return 'unknown'

    # Check for PDF
    if file_content[:4] == MAGIC_BYTES['pdf']:
        return 'pdf'

    # Check for XLSX (ZIP format)
    if file_content[:4] == MAGIC_BYTES['xlsx']:
        # Further verify it's an Excel file by checking for Excel-specific content
        try:
            content_str = str(file_content[:1000])
            if 'xl/' in content_str or 'worksheets' in content_str:
                return 'excel_xlsx'
        except:
            pass
        # Could be a generic ZIP, but we'll treat as XLSX for now
        return 'excel_xlsx'

    # Check for XLS (OLE2 format)
    if file_content[:4] == MAGIC_BYTES['xls']:
        return 'excel_xls'

    # Check if it's likely a CSV (text-based)
    try:
        # Try to decode as UTF-8 text
        content_str = file_content.decode('utf-8', errors='strict')

        # Basic CSV characteristics:
        # - Contains commas
        # - Contains newlines
        # - First 1000 chars should be readable text
        first_1000 = content_str[:1000]

        if ',' in first_1000 and '\n' in first_1000:
            # Check for common CSV headers
            first_line = first_1000.split('\n')[0].lower()
            if any(keyword in first_line for keyword in ['date', 'description', 'amount', 'transaction']):
                return 'csv'
            # Generic CSV
            return 'csv'
    except (UnicodeDecodeError, AttributeError):
        pass

    return 'unknown'


def is_pdf_encrypted(file_content: bytes) -> bool:
    """
    Check if a PDF file is password-protected

    Args:
        file_content: Raw PDF file bytes

    Returns:
        bool: True if PDF is encrypted, False otherwise

    Raises:
        InvalidFileFormatError: If file is not a valid PDF

    Implementation:
        Uses pikepdf library to open the PDF
        If PasswordError is raised, the PDF is encrypted
    """
    import pikepdf

    # Verify it's a PDF first
    if detect_file_type(file_content) != 'pdf':
        raise InvalidFileFormatError("File is not a valid PDF")

    try:
        with pikepdf.Pdf.open(io.BytesIO(file_content)) as pdf:
            # Successfully opened without password
            return False
    except pikepdf.PasswordError:
        # Password required
        return True
    except Exception as e:
        raise InvalidFileFormatError(f"Invalid or corrupted PDF file: {str(e)}")


def validate_file_size(file_content: bytes, max_size_mb: int = 10) -> bool:
    """
    Validate that file size is within acceptable limits

    Args:
        file_content: Raw file bytes
        max_size_mb: Maximum allowed file size in megabytes

    Returns:
        bool: True if valid, False if too large

    Default limit: 10MB (10 * 1024 * 1024 bytes)
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return len(file_content) <= max_size_bytes


def get_file_info(file_content: bytes) -> dict:
    """
    Get comprehensive file information

    Args:
        file_content: Raw file bytes

    Returns:
        dict: {
            'type': str,              # File type
            'size_bytes': int,        # File size in bytes
            'size_mb': float,         # File size in MB
            'is_valid': bool,         # Is file type supported
            'is_encrypted': bool,     # Only for PDFs
            'error': str or None      # Error message if any
        }
    """
    info = {
        'type': None,
        'size_bytes': len(file_content),
        'size_mb': round(len(file_content) / (1024 * 1024), 2),
        'is_valid': False,
        'is_encrypted': False,
        'error': None
    }

    try:
        # Detect file type
        file_type = detect_file_type(file_content)
        info['type'] = file_type

        # Check if supported
        if file_type in ['pdf', 'excel_xlsx', 'excel_xls', 'csv']:
            info['is_valid'] = True
        else:
            info['error'] = 'Unsupported file format'
            return info

        # Check if PDF is encrypted
        if file_type == 'pdf':
            try:
                info['is_encrypted'] = is_pdf_encrypted(file_content)
            except Exception as e:
                info['error'] = str(e)
                info['is_valid'] = False

        # Validate size
        if not validate_file_size(file_content, max_size_mb=10):
            info['error'] = 'File size exceeds 10MB limit'
            info['is_valid'] = False

    except Exception as e:
        info['error'] = str(e)
        info['is_valid'] = False

    return info


def validate_file(file_content: bytes, max_size_mb: int = 10) -> None:
    """
    Validate file and raise appropriate exceptions if invalid

    Args:
        file_content: Raw file bytes
        max_size_mb: Maximum allowed file size in MB

    Raises:
        UnsupportedFormatError: If file type is not supported
        InvalidFileFormatError: If file is corrupted
        ValueError: If file is too large
    """
    # Check file size
    if not validate_file_size(file_content, max_size_mb):
        raise ValueError(f"File size exceeds {max_size_mb}MB limit")

    # Detect type
    file_type = detect_file_type(file_content)

    if file_type == 'unknown':
        raise UnsupportedFormatError(
            "Unsupported file format. Please upload PDF, Excel (.xlsx/.xls), or CSV file."
        )

    if file_type not in ['pdf', 'excel_xlsx', 'excel_xls', 'csv']:
        raise UnsupportedFormatError(f"File type '{file_type}' is not supported")

    # Validate PDF if applicable
    if file_type == 'pdf':
        try:
            is_pdf_encrypted(file_content)  # Just to validate it's a proper PDF
        except pikepdf.PdfError as e:
            raise InvalidFileFormatError(f"Corrupted or invalid PDF: {str(e)}")
