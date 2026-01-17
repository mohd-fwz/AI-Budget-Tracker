"""
Bank Template Loader
Loads and manages bank-specific parsing templates
"""
import json
import os
import re
from typing import Dict, Optional, List


class BankTemplate:
    """
    Represents a bank-specific parsing template
    """
    def __init__(self, template_data: Dict):
        self.bank_name = template_data['bank_name']
        self.identifiers = template_data['identifiers']
        self.extraction_method = template_data['extraction_method']
        self.column_mappings = template_data['column_mappings']
        self.date_format = template_data.get('date_format', 'DD/MM/YY')
        self.skip_rows = template_data.get('skip_rows', [])
        self.page_hint = template_data.get('page_hint')

        # Optional fields for different extraction methods
        self.regex_pattern = template_data.get('regex_pattern')
        self.table_settings = template_data.get('table_settings')
        self.amount_indicator = template_data.get('amount_indicator')  # For Dr/Cr columns

    def matches_pdf(self, text_content: str) -> bool:
        """
        Check if this template matches the PDF content

        Args:
            text_content: Text extracted from first page of PDF

        Returns:
            bool: True if this template should be used for this PDF
        """
        text_lower = text_content.lower()

        # Check if any of the bank identifiers appear in the text
        for identifier in self.identifiers:
            if identifier.lower() in text_lower:
                return True

        return False


class BankTemplateLoader:
    """
    Manages loading and matching of bank templates
    """
    def __init__(self, templates_dir: str = None):
        """
        Initialize template loader

        Args:
            templates_dir: Path to templates directory (default: bank_templates/)
        """
        if templates_dir is None:
            # Default to bank_templates/ in project root
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            templates_dir = os.path.join(current_dir, 'bank_templates')

        self.templates_dir = templates_dir
        self.templates: List[BankTemplate] = []
        self._load_templates()

    def _load_templates(self):
        """Load all JSON templates from the templates directory"""
        if not os.path.exists(self.templates_dir):
            print(f"Warning: Templates directory not found: {self.templates_dir}")
            return

        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.templates_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                        template = BankTemplate(template_data)
                        self.templates.append(template)
                        print(f"Loaded template: {template.bank_name}")
                except Exception as e:
                    print(f"Error loading template {filename}: {e}")

    def match_template(self, pdf_text: str) -> Optional[BankTemplate]:
        """
        Find the best matching template for a PDF

        Args:
            pdf_text: Text content from first page of PDF

        Returns:
            BankTemplate if match found, None otherwise
        """
        for template in self.templates:
            if template.matches_pdf(pdf_text):
                print(f"Matched bank template: {template.bank_name}")
                return template

        print("No matching bank template found, using generic parser")
        return None

    def get_template_by_name(self, bank_name: str) -> Optional[BankTemplate]:
        """
        Get a template by bank name

        Args:
            bank_name: Name of the bank

        Returns:
            BankTemplate if found, None otherwise
        """
        for template in self.templates:
            if template.bank_name.lower() == bank_name.lower():
                return template
        return None


# Global template loader instance
_template_loader = None

def get_template_loader() -> BankTemplateLoader:
    """Get or create the global template loader instance"""
    global _template_loader
    if _template_loader is None:
        _template_loader = BankTemplateLoader()
    return _template_loader
