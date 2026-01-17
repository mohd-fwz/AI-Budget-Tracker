"""
Unit tests for transaction_parser.py
Tests based on real IndusInd Bank statement examples
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.transaction_parser import (
    parse_transaction_description,
    extract_upi_id,
    extract_payment_method,
    extract_transaction_ref,
    extract_merchant_name,
    parse_transactions_batch
)


class TestUPIExtraction:
    """Test UPI ID extraction from various formats"""

    def test_standard_upi_format(self):
        """Test standard name@bank format"""
        assert extract_upi_id("Transfer to swiggy@paytm") == "swiggy@paytm"
        assert extract_upi_id("Payment from john.doe@okaxis") == "john.doe@okaxis"
        assert extract_upi_id("UPI-merchant@ybl-123456") == "merchant@ybl"

    def test_numeric_upi_id(self):
        """Test numeric UPI IDs"""
        assert extract_upi_id("e/YESB/-29411985@ptybl") == "-29411985@ptybl"
        assert extract_upi_id("UPI/9876543210@paytm/CR") == "9876543210@paytm"

    def test_complex_upi_patterns(self):
        """Test UPI IDs with dots and underscores"""
        assert extract_upi_id("swiggy.food@paytm") == "swiggy.food@paytm"
        assert extract_upi_id("user_name@phonepe") == "user_name@phonepe"
        assert extract_upi_id("merchant-123@googlepay") == "merchant-123@googlepay"

    def test_no_upi_id(self):
        """Test descriptions without UPI IDs"""
        assert extract_upi_id("ATM Withdrawal") is None
        assert extract_upi_id("NEFT Transfer") is None
        assert extract_upi_id("Cash Deposit") is None


class TestPaymentMethodExtraction:
    """Test payment method detection"""

    def test_upi_detection(self):
        """Test UPI payment detection"""
        assert extract_payment_method("UPI/297518249928/DR/Hai") == "UPI"
        assert extract_payment_method("UPI CreditAdj - 393805551233") == "UPI"
        assert extract_payment_method("Transfer to merchant@paytm") == "UPI"
        assert extract_payment_method("e/YESB/-29411985@ptybl") == "UPI"

    def test_neft_detection(self):
        """Test NEFT detection"""
        assert extract_payment_method("NEFT Transfer to John Doe") == "NEFT"
        assert extract_payment_method("NEFT-R123456789") == "NEFT"

    def test_imps_detection(self):
        """Test IMPS detection"""
        assert extract_payment_method("IMPS Transfer") == "IMPS"
        assert extract_payment_method("IMPS-123456") == "IMPS"

    def test_rtgs_detection(self):
        """Test RTGS detection"""
        assert extract_payment_method("RTGS Transfer - 500000") == "RTGS"

    def test_atm_detection(self):
        """Test ATM withdrawal detection"""
        assert extract_payment_method("ATM WDL-123456") == "ATM"
        assert extract_payment_method("CASH WITHDRAWAL ATM") == "ATM"

    def test_card_detection(self):
        """Test card payment detection"""
        assert extract_payment_method("POS Purchase") == "Card"
        assert extract_payment_method("DEBIT CARD PURCHASE") == "Card"

    def test_cheque_detection(self):
        """Test cheque detection"""
        assert extract_payment_method("CHQ Deposit") == "Cheque"
        assert extract_payment_method("CHEQUE-123456") == "Cheque"

    def test_cash_detection(self):
        """Test cash deposit detection"""
        assert extract_payment_method("CASH DEPOSIT") == "Cash"
        assert extract_payment_method("CASH DEP-1000") == "Cash"


class TestTransactionRefExtraction:
    """Test transaction reference ID extraction"""

    def test_upi_reference(self):
        """Test UPI reference extraction"""
        assert extract_transaction_ref("UPI/297518249928/DR/Hai") == "297518249928"
        assert extract_transaction_ref("UPI-123456789-CR") == "123456789"

    def test_explicit_ref(self):
        """Test explicit REF: patterns"""
        assert extract_transaction_ref("NEFT-REF123456789") == "123456789"  # Extracts just the ID
        assert extract_transaction_ref("Reference: ABC123456") == "ABC123456"

    def test_transaction_id(self):
        """Test Transaction ID patterns"""
        assert extract_transaction_ref("Transaction ID: 999888777") == "999888777"
        assert extract_transaction_ref("TXN:ABC123") == "ABC123"

    def test_long_numeric_sequence(self):
        """Test long numeric sequences as reference"""
        result = extract_transaction_ref("Transfer-1234567890123")
        assert result == "1234567890123"

    def test_no_reference(self):
        """Test descriptions without clear reference"""
        # Short numbers should not be extracted
        assert extract_transaction_ref("Amount: 500") is None


class TestMerchantNameExtraction:
    """Test merchant name extraction"""

    def test_slash_separated_name(self):
        """Test extraction from slash-separated format"""
        assert extract_merchant_name("UPI/297518249928/DR/Hai") == "Hai"
        assert extract_merchant_name("UPI/123/CR/Swiggy Food") == "Swiggy Food"

    def test_to_from_patterns(self):
        """Test TO/FROM patterns"""
        assert extract_merchant_name("Transfer to John Doe") == "John Doe"
        assert extract_merchant_name("Payment from Amazon India") == "Amazon India"

    def test_upi_merchant_mapping(self):
        """Test known UPI merchant mapping"""
        assert extract_merchant_name("payment", "swiggy@paytm") == "Swiggy"
        assert extract_merchant_name("txn", "zomato@paytm") == "Zomato"
        assert extract_merchant_name("order", "user@phonepe") == "PhonePe"

    def test_capitalized_words(self):
        """Test extraction of capitalized words"""
        result = extract_merchant_name("Payment to Amazon India Limited")
        assert result is not None
        assert "Amazon" in result

    def test_name_from_upi_id(self):
        """Test extraction from UPI ID name part"""
        assert extract_merchant_name("transaction", "swiggy.food@paytm") == "Swiggy"
        result = extract_merchant_name("payment", "john.doe@okaxis")
        assert result is not None


class TestFullParsing:
    """Test complete transaction parsing"""

    def test_indusind_upi_transaction_1(self):
        """Test: UPI/297518249928/DR/Hai"""
        result = parse_transaction_description("UPI/297518249928/DR/Hai")
        assert result['payment_method'] == "UPI"
        assert result['transaction_ref'] == "297518249928"
        assert result['merchant_name'] == "Hai"
        assert result['upi_id'] is None  # No @ symbol

    def test_indusind_upi_transaction_2(self):
        """Test: e/YESB/-29411985@ptybl"""
        result = parse_transaction_description("e/YESB/-29411985@ptybl")
        assert result['payment_method'] == "UPI"
        assert result['upi_id'] == "-29411985@ptybl"
        assert result['merchant_name'] == "Paytm"  # Mapped from @ptybl

    def test_indusind_upi_credit(self):
        """Test: UPI CreditAdj - 393805551233"""
        result = parse_transaction_description("UPI CreditAdj - 393805551233")
        assert result['payment_method'] == "UPI"
        assert result['transaction_ref'] == "393805551233"

    def test_swiggy_payment(self):
        """Test: UPI-swiggy@paytm-123456789"""
        result = parse_transaction_description("UPI-swiggy@paytm-123456789")
        assert result['payment_method'] == "UPI"
        assert result['upi_id'] == "swiggy@paytm"
        assert result['merchant_name'] == "Swiggy"

    def test_neft_transfer(self):
        """Test: NEFT Transfer to John Doe REF:ABC123"""
        result = parse_transaction_description("NEFT Transfer to John Doe REF:ABC123")
        assert result['payment_method'] == "NEFT"
        assert result['transaction_ref'] == "ABC123"
        assert result['merchant_name'] == "John Doe"

    def test_atm_withdrawal(self):
        """Test: ATM WDL-123456 HDFC Bank"""
        result = parse_transaction_description("ATM WDL-123456 HDFC Bank")
        assert result['payment_method'] == "ATM"
        # transaction_ref might be extracted
        assert result['upi_id'] is None

    def test_empty_description(self):
        """Test empty description handling"""
        result = parse_transaction_description("")
        assert result['payment_method'] is None
        assert result['upi_id'] is None
        assert result['transaction_ref'] is None
        assert result['merchant_name'] is None

    def test_none_description(self):
        """Test None description handling"""
        result = parse_transaction_description(None)
        assert result['payment_method'] is None


class TestBatchParsing:
    """Test batch processing of transactions"""

    def test_batch_parsing(self):
        """Test parsing multiple transactions at once"""
        descriptions = [
            "UPI/297518249928/DR/Hai",
            "e/YESB/-29411985@ptybl",
            "NEFT Transfer to John",
            "ATM WDL-123456"
        ]
        results = parse_transactions_batch(descriptions)

        assert len(results) == 4
        assert results[0]['payment_method'] == "UPI"
        assert results[1]['upi_id'] == "-29411985@ptybl"
        assert results[2]['payment_method'] == "NEFT"
        assert results[3]['payment_method'] == "ATM"

    def test_empty_batch(self):
        """Test empty batch handling"""
        results = parse_transactions_batch([])
        assert len(results) == 0


class TestRealWorldExamples:
    """Test with real-world transaction descriptions from Indian banks"""

    def test_phonepe_transaction(self):
        """Test PhonePe transaction"""
        result = parse_transaction_description("UPI/PhonePe/user@ybl/DR/9876543210")
        assert result['payment_method'] == "UPI"
        assert result['upi_id'] == "user@ybl"

    def test_google_pay_transaction(self):
        """Test Google Pay transaction"""
        result = parse_transaction_description("UPI-merchant@okaxis-GPay")
        assert result['payment_method'] == "UPI"
        assert result['upi_id'] == "merchant@okaxis"

    def test_salary_credit(self):
        """Test salary credit NEFT"""
        result = parse_transaction_description("NEFT-SALARY-COMPANY_NAME-R123456789")
        assert result['payment_method'] == "NEFT"
        assert result['transaction_ref'] == "R123456789"

    def test_online_shopping(self):
        """Test online shopping transaction"""
        result = parse_transaction_description("UPI/Amazon Pay/amazon@icici/DR")
        assert result['payment_method'] == "UPI"
        # Merchant name extracted from path segment
        assert "Amazon" in result['merchant_name']

    def test_food_delivery(self):
        """Test food delivery"""
        result = parse_transaction_description("UPI-zomato@paytm-Order123")
        assert result['payment_method'] == "UPI"
        assert result['upi_id'] == "zomato@paytm"
        assert result['merchant_name'] == "Zomato"

    def test_electricity_bill(self):
        """Test utility bill payment"""
        result = parse_transaction_description("IMPS/BESCOM/Electricity/R987654321")
        assert result['payment_method'] == "IMPS"
        assert result['transaction_ref'] == "R987654321"


class TestEdgeCases:
    """Test edge cases and potential issues"""

    def test_special_characters(self):
        """Test descriptions with special characters"""
        result = parse_transaction_description("UPI/Transaction@#$/merchant@paytm")
        assert result['upi_id'] == "merchant@paytm"

    def test_multiple_at_symbols(self):
        """Test multiple @ symbols"""
        result = parse_transaction_description("Payment @merchant @user@paytm")
        assert result['upi_id'] == "user@paytm"

    def test_very_long_description(self):
        """Test very long description"""
        long_desc = "UPI " + "A" * 500 + " merchant@paytm"
        result = parse_transaction_description(long_desc)
        assert result['upi_id'] == "merchant@paytm"

    def test_mixed_case(self):
        """Test mixed case handling"""
        result = parse_transaction_description("uPi/123/Dr/MeRcHaNt")
        assert result['payment_method'] == "UPI"

    def test_unicode_characters(self):
        """Test Unicode characters in merchant names"""
        result = parse_transaction_description("UPI/123/DR/Café Royal")
        assert result['merchant_name'] is not None


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
