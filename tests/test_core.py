"""Tests for core PDF processing functionality."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from io import StringIO
import tempfile
import os

from rbc_pdf_to_csv.core import PDFProcessor

from .conftest import CREDIT_CARD_PDFS, BANK_ACCOUNT_PDFS

class TestCore:
    """Test core functionality using real sample data."""

    @pytest.mark.parametrize("pdf_path", CREDIT_CARD_PDFS)
    def test_process_credit_card_statement(self, pdf_path, samples_dir):
        """Test that credit card statements are processed correctly."""
        pdf_path = samples_dir / ".." / pdf_path

        raw_text_path = pdf_path.with_suffix(".raw.txt")
        if not raw_text_path.exists():
            raise RuntimeError(f"Expected source text file not found for {pdf_path.name}")

        out_csv = pdf_path.with_suffix(".csv")
        if not out_csv.exists():
            raise RuntimeError(f"Expected output CSV file not found for {pdf_path.name}")

        expected_csv = open(out_csv, "r").read()

        with open(raw_text_path, "r") as f:
            raw_text = f.read()
        raw_text = raw_text.removeprefix("```csv").removesuffix("```")

        df = pd.read_csv(StringIO(raw_text))
        # Add the File column as the core processing expects it
        df["File"] = pdf_path.name
        processor = PDFProcessor()
        processed_df = processor.process_credit_card_statement(df)

        result_csv = StringIO()
        processed_df.to_csv(result_csv, index=False)
        assert expected_csv == result_csv.getvalue()

    @pytest.mark.parametrize("pdf_path", BANK_ACCOUNT_PDFS)
    def test_process_bank_statement(self, pdf_path, samples_dir):
        """Test that bank account statements are processed correctly."""
        pdf_path = samples_dir / ".." / pdf_path

        raw_text_path = pdf_path.with_suffix(".raw.txt")
        if not raw_text_path.exists():
            raise RuntimeError(f"Expected source text file not found for {pdf_path.name}")

        out_csv = pdf_path.with_suffix(".csv")
        if not out_csv.exists():
            raise RuntimeError(f"Expected output CSV file already exists for {pdf_path.name}")

        expected_csv = open(out_csv, "r").read()

        with open(raw_text_path, "r") as f:
            raw_text = f.read()
        raw_text = raw_text.removeprefix("```csv").removesuffix("```")

        df = pd.read_csv(StringIO(raw_text))
        # Add the File column as the core processing expects it
        df["File"] = pdf_path.name
        processor = PDFProcessor()
        processed_df = processor.process_bank_statement(df)

        result_csv = StringIO()
        processed_df.to_csv(result_csv, index=False)
        assert expected_csv == result_csv.getvalue()

    def test_categorize_transactions(self):
        """Test that transaction categorization works correctly."""
        processor = PDFProcessor()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("""Description,Amount,Category
STARBUCKS 16466 OTTAWA ON,-6.50,Food
LOBLAWS 82.2 NEPEAN ON,-57.80,Food
BELL CANADA (OB) MONTREAL QC,-123.74,Food""")
            temp_category_training_csv = f.name

        # Create a temporary CSV file with sample transactions
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("""Date,Description,Amount,File
2024-01-01,STARBUCKS 16466 OTTAWA ON,-6.50,test.pdf
2024-01-02,LOBLAWS 82.2 NEPEAN ON,-57.80,test.pdf
2024-01-03,BELL CANADA (OB) MONTREAL QC,-123.74,test.pdf""")
            temp_csv_path = f.name

        try:
            # Test categorization
            result_path = processor.categorize_transactions(temp_csv_path, temp_category_training_csv)

            # Verify the file was updated
            assert result_path == temp_csv_path

            # Read the categorized CSV and check for Category column
            df = pd.read_csv(temp_csv_path)
            assert "Category" in df.columns

            # Verify the original columns are still there
            assert "Date" in df.columns
            assert "Description" in df.columns
            assert "Amount" in df.columns
            assert "File" in df.columns

        finally:
            # Clean up
            if os.path.exists(temp_csv_path):
                os.unlink(temp_csv_path)
            if os.path.exists(temp_category_training_csv):
                os.unlink(temp_category_training_csv)

    # def test_csv_structure_validation(self, samples_dir):
    #     """Test that all sample CSV files have the correct structure."""
    #     csv_files = list(samples_dir.glob("*.csv"))

    #     for csv_path in csv_files:
    #         with open(csv_path, "r") as f:
    #             csv_content = f.read()

    #         # Parse CSV to validate structure
    #         df = pd.read_csv(BytesIO(csv_content.encode()))

    #         # Check if it's a credit card or bank account CSV based on filename
    #         if "visa" in csv_path.name.lower():
    #             # Credit card CSV should have these columns
    #             expected_columns = ["Transaction Date", "Posting Date", "Description", "Amount"]
    #             assert list(df.columns) == expected_columns, f"Credit card CSV {csv_path.name} has wrong columns"

    #             # Validate data types
    #             assert df["Amount"].dtype in ['float64', 'int64'], f"Amount column in {csv_path.name} is not numeric"

    #             # Validate date formats
    #             for date_col in ["Transaction Date", "Posting Date"]:
    #                 for date_str in df[date_col]:
    #                     assert len(date_str.split('-')) == 3, f"Date format error in {csv_path.name}"
    #                     assert len(date_str.split('-')[0]) == 4, f"Year format error in {csv_path.name}"

    #         elif "chequing" in csv_path.name.lower() or "savings" in csv_path.name.lower():
    #             # Bank account CSV should have these columns
    #             expected_columns = ["Date", "Description", "Amount", "Balance"]
    #             assert list(df.columns) == expected_columns, f"Bank account CSV {csv_path.name} has wrong columns"

    #             # Validate data types
    #             assert df["Amount"].dtype in ['float64', 'int64'], f"Amount column in {csv_path.name} is not numeric"
    #             assert df["Balance"].dtype in ['float64', 'int64'], f"Balance column in {csv_path.name} is not numeric"

    #             # Validate date formats
    #             for date_str in df["Date"]:
    #                 assert len(date_str.split('-')) == 3, f"Date format error in {csv_path.name}"
    #                 assert len(date_str.split('-')[0]) == 4, f"Year format error in {csv_path.name}"

    # def test_raw_text_to_csv_processing(self, samples_dir):
    #     """Test processing raw text to CSV format."""
    #     # Test credit card processing
    #     raw_text_path = samples_dir / "business_visa_single_page.raw.txt"
    #     expected_csv_path = samples_dir / "business_visa_single_page.csv"

    #     if raw_text_path.exists() and expected_csv_path.exists():
    #         with open(raw_text_path, "r") as f:
    #             raw_text = f.read()

    #         with open(expected_csv_path, "r") as f:
    #             expected_csv = f.read()

    #         # Parse both to compare structure
    #         raw_df = pd.read_csv(BytesIO(raw_text.removeprefix("```csv").removesuffix("```").encode()))
    #         raw_df = pd.read_csv(BytesIO(expected_csv.encode()))

    #         # The processed CSV should have the same number of rows
    #         assert len(raw_df) == len(expected_df), "Row count mismatch"

    #         # The processed CSV should have the same columns
    #         assert list(raw_df.columns) == list(expected_df.columns), "Column mismatch"

    # def test_date_formatting_consistency(self, samples_dir):
    #     """Test that date formatting is consistent across all samples."""
    #     csv_files = list(samples_dir.glob("*.csv"))

    #     for csv_path in csv_files:
    #         with open(csv_path, "r") as f:
    #             csv_content = f.read()

    #         df = pd.read_csv(BytesIO(csv_content.encode()))

    #         # Check date columns
    #         date_columns = [col for col in df.columns if "date" in col.lower() or col.lower() == "date"]

    #         for date_col in date_columns:
    #             for date_str in df[date_col]:
    #                 # All dates should be in YYYY-MM-DD format
    #                 parts = date_str.split('-')
    #                 assert len(parts) == 3, f"Date format error in {csv_path.name}: {date_str}"
    #                 assert len(parts[0]) == 4, f"Year format error in {csv_path.name}: {date_str}"
    #                 assert len(parts[1]) == 2, f"Month format error in {csv_path.name}: {date_str}"
    #                 assert len(parts[2]) == 2, f"Day format error in {csv_path.name}: {date_str}"

    # def test_amount_formatting_consistency(self, samples_dir):
    #     """Test that amount formatting is consistent across all samples."""
    #     csv_files = list(samples_dir.glob("*.csv"))

    #     for csv_path in csv_files:
    #         with open(csv_path, "r") as f:
    #             csv_content = f.read()

    #         df = pd.read_csv(BytesIO(csv_content.encode()))

    #         # Check amount columns
    #         amount_columns = [col for col in df.columns if "amount" in col.lower() or col.lower() in ["balance", "withdrawals", "deposit"]]

    #         for amount_col in amount_columns:
    #             # All amount columns should be numeric
    #             assert df[amount_col].dtype in ['float64', 'int64'], f"Amount column {amount_col} in {csv_path.name} is not numeric"

    #             # Check that there are no currency symbols or commas in the data
    #             for value in df[amount_col]:
    #                 if pd.notna(value):
    #                     value_str = str(value)
    #                     assert '$' not in value_str, f"Currency symbol found in {csv_path.name}: {value_str}"
    #                     assert ',' not in value_str, f"Comma found in {csv_path.name}: {value_str}"

    # def test_multi_page_pdf_processing(self, samples_dir):
    #     """Test that multi-page PDFs are processed correctly."""
    #     multi_page_pdfs = [
    #         f for f in samples_dir.glob("*.pdf")
    #         if "multi_page" in f.name.lower() or "multi_card" in f.name.lower()
    #     ]

    #     for pdf_path in multi_page_pdfs:
    #         # Check if corresponding PNG exists
    #         png_path = pdf_path.with_suffix('.combined.png')
    #         if png_path.exists():
    #             # Verify the PNG is a valid image file
    #             with open(png_path, "rb") as f:
    #                 png_bytes = f.read()

    #             assert png_bytes.startswith(b'\x89PNG'), f"Invalid PNG file: {png_path.name}"
    #             assert len(png_bytes) > 1000, f"PNG file too small: {png_path.name}"

    # def test_credit_card_amount_sign_convention(self, samples_dir):
    #     """Test that credit card amounts follow the correct sign convention."""
    #     credit_card_csvs = [f for f in samples_dir.glob("*.csv") if "visa" in f.name.lower()]

    #     for csv_path in credit_card_csvs:
    #         with open(csv_path, "r") as f:
    #             csv_content = f.read()

    #         df = pd.read_csv(BytesIO(csv_content.encode()))

    #         # Credit card amounts should be negative for purchases, positive for credits
    #         # This is a business rule that should be validated
    #         for _, row in df.iterrows():
    #             amount = row["Amount"]
    #             description = row["Description"].lower()

    #             # Payments should be positive (credits)
    #             if "payment" in description:
    #                 assert amount > 0, f"Payment should be positive: {description} = {amount}"

    #             # Most other transactions should be negative (purchases)
    #             elif "payment" not in description and "credit" not in description:
    #                 # This is a general rule, but there might be exceptions
    #                 pass

    # def test_bank_account_balance_consistency(self, samples_dir):
    #     """Test that bank account balances are consistent."""
    #     bank_csvs = [f for f in samples_dir.glob("*.csv") if "chequing" in f.name.lower() or "savings" in f.name.lower()]

    #     for csv_path in bank_csvs:
    #         with open(csv_path, "r") as f:
    #             csv_content = f.read()

    #         df = pd.read_csv(BytesIO(csv_content.encode()))

    #         # Check that balance column exists and is numeric
    #         assert "Balance" in df.columns, f"Balance column missing in {csv_path.name}"
    #         assert df["Balance"].dtype in ['float64', 'int64'], f"Balance column not numeric in {csv_path.name}"

    #         # Check that balances are generally positive (for normal accounts)
    #         # This is a business rule assumption
    #         positive_balances = (df["Balance"] > 0).sum()
    #         total_balances = len(df["Balance"])

    #         # At least 50% of balances should be positive (allowing for overdrafts)
    #         assert positive_balances / total_balances >= 0.5, f"Too many negative balances in {csv_path.name}"

    # def test_description_sanitization(self, samples_dir):
    #     """Test that descriptions are properly sanitized."""
    #     csv_files = list(samples_dir.glob("*.csv"))

    #     for csv_path in csv_files:
    #         with open(csv_path, "r") as f:
    #             csv_content = f.read()

    #         df = pd.read_csv(BytesIO(csv_content.encode()))

    #         # Check that descriptions don't contain newlines
    #         description_col = "Description"
    #         if description_col in df.columns:
    #             for description in df[description_col]:
    #                 if pd.notna(description):
    #                     assert '\n' not in str(description), f"Newline found in description: {description}"

    # def test_csv_encoding_consistency(self, samples_dir):
    #     """Test that all CSV files use consistent encoding."""
    #     csv_files = list(samples_dir.glob("*.csv"))

    #     for csv_path in csv_files:
    #         # Try to read with UTF-8 encoding
    #         try:
    #             with open(csv_path, "r", encoding="utf-8") as f:
    #                 content = f.read()
    #             # If successful, the file is UTF-8 encoded
    #             assert True
    #         except UnicodeDecodeError:
    #             pytest.fail(f"CSV file {csv_path.name} is not UTF-8 encoded")

    # def test_pdf_to_png_caching_strategy(self, samples_dir):
    #     """Test that the caching strategy for PNG files works correctly."""
    #     pdf_files = list(samples_dir.glob("*.pdf"))

    #     for pdf_path in pdf_files:
    #         png_path = pdf_path.with_suffix('.combined.png')

    #         if png_path.exists():
    #             # Verify the cached PNG is larger than a minimal file
    #             png_size = png_path.stat().st_size
    #             assert png_size > 1000, f"Cached PNG too small: {png_path.name} ({png_size} bytes)"

    #             # Verify the PNG is a valid image
    #             with open(png_path, "rb") as f:
    #                 png_bytes = f.read()

    #             assert png_bytes.startswith(b'\x89PNG'), f"Invalid PNG header: {png_path.name}"

    #             # Verify the PNG ends with the correct footer
    #             assert png_bytes.endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82'), f"Invalid PNG footer: {png_path.name}"

    # def test_raw_text_format_consistency(self, samples_dir):
    #     """Test that raw text files have consistent format."""
    #     raw_text_files = list(samples_dir.glob("*.raw.txt"))

    #     for raw_text_path in raw_text_files:
    #         with open(raw_text_path, "r") as f:
    #             content = f.read()

    #         # Raw text should start with ```csv
    #         assert content.startswith("```csv"), f"Raw text doesn't start with ```csv: {raw_text_path.name}"

    #         # Raw text should end with ```
    #         assert content.endswith("```"), f"Raw text doesn't end with ```: {raw_text_path.name}"

    #         # Should contain CSV data between the markers
    #         csv_content = content.removeprefix("```csv").removesuffix("```").strip()
    #         assert len(csv_content) > 0, f"No CSV content in raw text: {raw_text_path.name}"

    #         # Should contain at least one comma (CSV delimiter)
    #         assert ',' in csv_content, f"No CSV delimiter found: {raw_text_path.name}"


# class TestPDFProcessor:
#     """Test PDF processor class."""

#     def test_init(self):
#         """Test PDF processor initialization."""
#         processor = PDFProcessor()
#         assert processor.api_key is None

#     def test_init_with_api_key(self):
#         """Test PDF processor initialization with API key."""
#         processor = PDFProcessor("test-key")
#         assert processor.api_key == "test-key"

#     def test_process_credit_card_statement(self):
#         """Test processing credit card statement DataFrame."""
#         df = pd.DataFrame({
#             "Transaction Date": ["2023/12/25", "2023/12/26"],
#             "Posting Date": ["2023/12/26", "2023/12/27"],
#             "Description": ["Test Transaction\n1", "Test Transaction\n2"],
#             "Amount": ["100.00", "200.00"]
#         })

#         processor = PDFProcessor()
#         result = processor.process_credit_card_statement(df)

#         # Check date formatting
#         assert result["Transaction Date"].iloc[0] == "2023-12-25"
#         assert result["Posting Date"].iloc[0] == "2023-12-26"

#         # Check amount conversion (should be negative for credit card)
#         assert result["Amount"].iloc[0] == -100.0
#         assert result["Amount"].iloc[1] == -200.0

#         # Check description sanitization
#         assert result["Description"].iloc[0] == "Test Transaction 1"
#         assert result["Description"].iloc[1] == "Test Transaction 2"

#     def test_process_credit_card_statement_with_activity_description(self):
#         """Test processing credit card statement with Activity Description column."""
#         df = pd.DataFrame({
#             "Transaction Date": ["2023/12/25"],
#             "Posting Date": ["2023/12/26"],
#             "Activity Description": ["Test Transaction"],
#             "Amount": ["100.00"]
#         })

#         processor = PDFProcessor()
#         result = processor.process_credit_card_statement(df)

#         # Check column renaming
#         assert "Description" in result.columns
#         assert "Activity Description" not in result.columns

#     def test_process_bank_statement(self):
#         """Test processing bank statement DataFrame."""
#         df = pd.DataFrame({
#             "Date": ["2023/12/25", "2023/12/26"],
#             "Description": ["Test Transaction\n1", "Test Transaction\n2"],
#             "Withdrawals": ["100.00", "0.00"],
#             "Deposit": ["0.00", "200.00"],
#             "Balance": ["1000.00", "1200.00"]
#         })

#         processor = PDFProcessor()
#         result = processor.process_bank_statement(df)

#         # Check date formatting
#         assert result["Date"].iloc[0] == "2023-12-25"
#         assert result["Date"].iloc[1] == "2023-12-26"

#         # Check amount calculation (withdrawals negative, deposits positive)
#         assert result["Amount"].iloc[0] == -100.0
#         assert result["Amount"].iloc[1] == 200.0

#         # Check description sanitization
#         assert result["Description"].iloc[0] == "Test Transaction 1"
#         assert result["Description"].iloc[1] == "Test Transaction 2"

#         # Check column structure
#         expected_columns = ["Date", "Description", "Amount", "Balance"]
#         assert list(result.columns) == expected_columns

#     def test_process_bank_statement_with_nan_values(self):
#         """Test processing bank statement with NaN values."""
#         df = pd.DataFrame({
#             "Date": ["2023/12/25"],
#             "Description": ["Test Transaction"],
#             "Withdrawals": [pd.NA],
#             "Deposit": ["100.00"],
#             "Balance": ["1000.00"]
#         })

#         processor = PDFProcessor()
#         result = processor.process_bank_statement(df)

#         # Check NaN handling
#         assert result["Amount"].iloc[0] == 100.0  # 0 + 100

#     def test_process_bank_statement_filters_balance_rows(self):
#         """Test processing bank statement filters balance rows."""
#         df = pd.DataFrame({
#             "Date": ["2023/12/25", "2023/12/26", "2023/12/27"],
#             "Description": ["Normal Transaction", "Opening balance", "Closing balance"],
#             "Withdrawals": ["100.00", "0.00", "0.00"],
#             "Deposit": ["0.00", "0.00", "0.00"],
#             "Balance": ["1000.00", "1000.00", "1000.00"]
#         })

#         processor = PDFProcessor()
#         result = processor.process_bank_statement(df)

#         # Should only have the normal transaction
#         assert len(result) == 1
#         assert result["Description"].iloc[0] == "Normal Transaction"

#     @patch("rbc_pdf_to_csv.core.BankStatement")
#     @patch("builtins.open", new_callable=mock_open)
#     def test_process_pdf_credit_card(self, mock_file, mock_bank_statement_class):
#         """Test processing credit card PDF."""
#         # Mock BankStatement
#         mock_statement = MagicMock()
#         mock_statement.is_credit_card.return_value = True
#         mock_statement.pdf_to_csv.return_value = "Transaction Date,Posting Date,Description,Amount\n2023/12/25,2023/12/26,\"Test\",100.00"
#         mock_bank_statement_class.return_value = mock_statement

#         # Mock file existence check
#         with patch("os.path.exists", return_value=False):
#             processor = PDFProcessor()
#             result = processor.process_pdf("test.pdf")

#         assert result == "test.csv"
#         mock_bank_statement_class.assert_called_once_with("test.pdf", api_key=None)
#         mock_statement.pdf_to_csv.assert_called_once()

#     @patch("rbc_pdf_to_csv.core.BankStatement")
#     @patch("builtins.open", new_callable=mock_open)
#     def test_process_pdf_bank_account(self, mock_file, mock_bank_statement_class):
#         """Test processing bank account PDF."""
#         # Mock BankStatement
#         mock_statement = MagicMock()
#         mock_statement.is_credit_card.return_value = False
#         mock_statement.pdf_to_csv.return_value = "Date,Description,Withdrawals,Deposit,Balance\n2023/12/25,\"Test\",100.00,0.00,1000.00"
#         mock_bank_statement_class.return_value = mock_statement

#         # Mock file existence check
#         with patch("os.path.exists", return_value=False):
#             processor = PDFProcessor("test-key")
#             result = processor.process_pdf("test.pdf")

#         assert result == "test.csv"
#         mock_bank_statement_class.assert_called_once_with("test.pdf", api_key="test-key")
#         mock_statement.pdf_to_csv.assert_called_once()

#     @patch("os.path.exists")
#     def test_process_pdf_skip_existing(self, mock_exists):
#         """Test processing PDF skips existing CSV when force=False."""
#         mock_exists.return_value = True

#         processor = PDFProcessor()
#         result = processor.process_pdf("test.pdf", force=False)

#         assert result is None

#     @patch("rbc_pdf_to_csv.core.BankStatement")
#     def test_process_pdf_conversion_error(self, mock_bank_statement_class):
#         """Test processing PDF with conversion error."""
#         mock_statement = MagicMock()
#         mock_statement.is_credit_card.return_value = True
#         mock_statement.pdf_to_csv.side_effect = Exception("Conversion failed")
#         mock_bank_statement_class.return_value = mock_statement

#         processor = PDFProcessor()
#         with pytest.raises(RuntimeError, match="Failed to convert PDF test.pdf"):
#             processor.process_pdf("test.pdf")

#     @patch("rbc_pdf_to_csv.core.BankStatement")
#     @patch("builtins.open", new_callable=mock_open)
#     def test_process_pdf_csv_parsing_error(self, mock_file, mock_bank_statement_class):
#         """Test processing PDF with CSV parsing error."""
#         mock_statement = MagicMock()
#         mock_statement.is_credit_card.return_value = True
#         mock_statement.pdf_to_csv.return_value = "invalid,csv,data"
#         mock_bank_statement_class.return_value = mock_statement

#         # Mock file existence check
#         with patch("os.path.exists", return_value=False):
#             processor = PDFProcessor()
#             # Should not raise exception, should retry with lenient parsing
#             result = processor.process_pdf("test.pdf")

#         assert result == "test.csv"

#     @patch("rbc_pdf_to_csv.core.PDFProcessor.process_pdf")
#     def test_process_files(self, mock_process_pdf):
#         """Test processing multiple files."""
#         mock_process_pdf.side_effect = ["file1.csv", None, "file3.csv"]

#         processor = PDFProcessor()
#         result = processor.process_files(["file1.pdf", "file2.pdf", "file3.pdf"])

#         assert result == ["file1.csv", "file3.csv"]
#         assert mock_process_pdf.call_count == 3

#     @patch("rbc_pdf_to_csv.core.PDFProcessor.process_pdf")
#     def test_process_files_with_error(self, mock_process_pdf):
#         """Test processing files with error handling."""
#         mock_process_pdf.side_effect = ["file1.csv", Exception("Error"), "file3.csv"]

#         processor = PDFProcessor()
#         result = processor.process_files(["file1.pdf", "file2.pdf", "file3.pdf"])

#         assert result == ["file1.csv", "file3.csv"]
#         assert mock_process_pdf.call_count == 3
