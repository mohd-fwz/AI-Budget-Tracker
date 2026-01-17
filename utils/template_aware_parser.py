"""
Template-aware PDF parser
Uses bank templates when available, falls back to generic parsing
"""
import io
import pdfplumber
from typing import List, Dict, Optional
from .bank_template_loader import get_template_loader, BankTemplate
from .text_based_parser import parse_transactions_from_text
from .pdf_parser import parse_pdf_transactions as generic_pdf_parser


def parse_pdf_with_template(
    file_content: bytes,
    password: Optional[str] = None
) -> List[Dict]:
    """
    Parse PDF using bank template if available, otherwise use generic parser

    Args:
        file_content: Raw PDF bytes
        password: Optional PDF password

    Returns:
        List[Dict]: Parsed transactions

    Flow:
        1. Decrypt PDF if needed
        2. Extract text from first page
        3. Try to match a bank template
        4. If template found:
           - Use text-based parsing for HDFC/IndusInd
           - Use enhanced table parsing for others
        5. If no template, use generic parser
    """
    try:
        # Check if encrypted and decrypt if needed
        from .pdf_parser import is_pdf_encrypted, decrypt_pdf

        if is_pdf_encrypted(file_content):
            if not password:
                # Can't decrypt, use generic parser which will handle the error
                return generic_pdf_parser(file_content, password)
            # Decrypt
            file_content = decrypt_pdf(file_content, password)
            print("PDF decrypted successfully")

        # Extract first page text for bank detection
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            if not pdf.pages:
                raise ValueError("PDF has no pages")

            first_page_text = pdf.pages[0].extract_text() or ""

        # Try to match a bank template
        template_loader = get_template_loader()
        template = template_loader.match_template(first_page_text)

        if template:
            print(f"Using bank template: {template.bank_name}")

            # Route to appropriate parser based on extraction method
            if template.extraction_method == "text_regex":
                # Use text-based regex parsing (HDFC)
                return parse_transactions_from_text(file_content, template)
            elif template.extraction_method == "hybrid":
                # Use hybrid parsing (tries multiple strategies) - IndusInd
                from .hybrid_parser import parse_with_hybrid_strategy
                return parse_with_hybrid_strategy(file_content, template)
            elif template.extraction_method == "table":
                # Use template-guided table parsing (ICICI, Axis, Kotak)
                return parse_with_table_template(file_content, template)
            else:
                print(f"Unknown extraction method: {template.extraction_method}, using generic parser")
                return generic_pdf_parser(file_content, password)
        else:
            # No template matched, use generic parser
            print("No bank template matched, using generic parser")
            return generic_pdf_parser(file_content, password)

    except Exception as e:
        print(f"Template-aware parsing error: {e}, falling back to generic parser")
        return generic_pdf_parser(file_content, password)


def parse_with_table_template(
    file_content: bytes,
    template: BankTemplate
) -> List[Dict]:
    """
    Parse PDF using table extraction with template guidance

    For now, this delegates to the generic parser since table extraction
    already works well for banks like ICICI, Axis, and Kotak.

    Future enhancement: Use template to guide column detection more precisely.

    Args:
        file_content: Raw PDF bytes
        template: Bank template

    Returns:
        List[Dict]: Parsed transactions
    """
    print(f"Using table extraction for {template.bank_name}")

    # For now, delegate to generic parser
    # The generic parser already handles these banks well
    from .pdf_parser import parse_pdf_transactions
    return parse_pdf_transactions(file_content, password=None)
