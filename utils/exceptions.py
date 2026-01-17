"""
Custom exceptions for bank statement parsing
"""


class StatementParsingError(Exception):
    """Base exception for all statement parsing errors"""
    pass


class PDFPasswordError(StatementParsingError):
    """
    Raised when a PDF is password-protected and either:
    - No password was provided
    - The provided password is incorrect
    """
    pass


class InvalidFileFormatError(StatementParsingError):
    """
    Raised when a file format is invalid or corrupted
    Examples: corrupted PDF, invalid Excel file, malformed CSV
    """
    pass


class UnsupportedFormatError(StatementParsingError):
    """
    Raised when the file type is not supported
    Supported formats: PDF, Excel (.xlsx, .xls), CSV
    """
    pass


class DateRangeError(StatementParsingError):
    """
    Raised when date range specification is invalid
    """
    pass


class ColumnDetectionError(StatementParsingError):
    """
    Raised when required columns (date, description, amount) cannot be identified
    """
    pass


class SessionExpiredError(StatementParsingError):
    """
    Raised when an upload session cannot be found or has expired
    """
    pass
