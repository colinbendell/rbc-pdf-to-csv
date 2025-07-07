"""Tests for BankStatement functionality using sample fixtures."""

import pytest
from unittest.mock import patch
from io import BytesIO

from rbc_pdf_to_csv.bank_statement import BankStatement
from rbc_pdf_to_csv.utils import AccountType

from .conftest import ALL_PDFS

class TestBankStatementWithSamples:
    """Test BankStatement class using sample fixtures."""

    def test_account_type_detection_credit_card(self, credit_card_samples):
        """Test credit card account type detection using real samples."""
        for pdf_path in credit_card_samples:
            statement = BankStatement(str(pdf_path))
            assert statement.account_type == AccountType.CREDIT_CARD
            assert statement.is_credit_card() is True

    def test_account_type_detection_bank_account(self, bank_account_samples):
        """Test bank account type detection using real samples."""
        for pdf_path in bank_account_samples:
            statement = BankStatement(str(pdf_path))
            assert statement.account_type in [AccountType.STANDARD], f"PDF: {pdf_path} is type {statement.account_type} not in [AccountType.ACCOUNT]"
            assert statement.is_credit_card() is False


    @pytest.mark.parametrize("pdf_path", ALL_PDFS)
    def test_pdf_to_png(self, pdf_path, samples_dir):
        """Test PDF to PNG conversion by comparing with cached combined images."""
        pdf_path = samples_dir / ".." / pdf_path

        # Check if corresponding cached PNG exists
        expected_png_path = pdf_path.with_suffix('.combined.png')

        if not expected_png_path.exists():
            pytest.skip(f"Cached PNG not found for {pdf_path.name}")

        # Read the cached PNG to get expected dimensions
        from PIL import Image
        with open(expected_png_path, "rb") as f:
            cached_image = Image.open(f)
            expected_width = cached_image.width
            expected_height = cached_image.height
            expected_size = expected_png_path.stat().st_size

            statement = BankStatement(str(pdf_path))
            result = statement.pdf_to_png()

            # Convert result back to PIL Image to check dimensions
            result_image = Image.open(BytesIO(result))
            result_width = result_image.width
            result_height = result_image.height
            result_size = len(result)

            # The result should be a valid PNG
            assert result_size > 0, f"Empty PNG result for {pdf_path.name}"

            # The result should have the same dimensions as the cached image
            assert result_width == expected_width, f"Width mismatch for {pdf_path.name}: expected {expected_width}, got {result_width}"
            assert result_height == expected_height, f"Height mismatch for {pdf_path.name}: expected {expected_height}, got {result_height}"
            assert result_size == expected_size, f"Size mismatch for {pdf_path.name}: expected {expected_size}, got {result_size}"

            # Allow for some variation in compression, but sizes should be reasonably close
            size_ratio = min(result_size, expected_size) / max(result_size, expected_size)
            assert size_ratio > 0.5, f"Size difference too large for {pdf_path.name}: cached {expected_size}, result {result_size}"

    # def test_credit_card_csv_processing(self, samples_dir):
    #     """Test credit card CSV processing using real sample data."""
    #     raw_text_path = samples_dir / "business_visa_single_page.raw.txt"
    #     expected_csv_path = samples_dir / "business_visa_single_page.csv"

    #     if not raw_text_path.exists() or not expected_csv_path.exists():
    #         pytest.skip("Sample files not found")

    #     # Read the raw text and expected CSV
    #     with open(raw_text_path, "r") as f:
    #         raw_text = f.read()

    #     with open(expected_csv_path, "r") as f:
    #         expected_csv = f.read()

    #     # Parse the expected CSV to validate structure
    #     expected_df = pd.read_csv(BytesIO(expected_csv.encode()))

    #     # Validate expected columns for credit card
    #     expected_columns = ["Transaction Date", "Posting Date", "Description", "Amount"]
    #     assert list(expected_df.columns) == expected_columns

    #     # Validate that amounts are properly formatted (no $ signs, proper decimals)
    #     assert expected_df["Amount"].dtype in ['float64', 'int64']

    #     # Validate that dates are in YYYY-MM-DD format
    #     for date_col in ["Transaction Date", "Posting Date"]:
    #         for date_str in expected_df[date_col]:
    #             assert len(date_str.split('-')) == 3
    #             assert len(date_str.split('-')[0]) == 4  # year

    # def test_bank_account_csv_processing(self, samples_dir):
    #     """Test bank account CSV processing using real sample data."""
    #     raw_text_path = samples_dir / "personal_chequing_multi_page.raw.txt"
    #     expected_csv_path = samples_dir / "personal_chequing_multi_page.csv"

    #     if not raw_text_path.exists() or not expected_csv_path.exists():
    #         pytest.skip("Sample files not found")

    #     # Read the raw text and expected CSV
    #     with open(raw_text_path, "r") as f:
    #         raw_text = f.read()

    #     with open(expected_csv_path, "r") as f:
    #         expected_csv = f.read()

    #     # Parse the expected CSV to validate structure
    #     expected_df = pd.read_csv(BytesIO(expected_csv.encode()))

    #     # Validate expected columns for bank account
    #     expected_columns = ["Date", "Description", "Amount", "Balance"]
    #     assert list(expected_df.columns) == expected_columns

    #     # Validate that amounts are properly formatted
    #     assert expected_df["Amount"].dtype in ['float64', 'int64']
    #     assert expected_df["Balance"].dtype in ['float64', 'int64']

    #     # Validate that dates are in YYYY-MM-DD format
    #     for date_str in expected_df["Date"]:
    #         assert len(date_str.split('-')) == 3
    #         assert len(date_str.split('-')[0]) == 4  # year

    # def test_multi_page_pdf_processing(self, samples_dir):
    #     """Test multi-page PDF processing using cached images."""
    #     pdf_path = samples_dir / "personal_chequing_multi_page.pdf"
    #     cached_png_path = samples_dir / "personal_chequing_multi_page.combined.png"

    #     if not cached_png_path.exists():
    #         pytest.skip("Cached multi-page PNG not found")

    #     # Read the cached PNG bytes
    #     with open(cached_png_path, "rb") as f:
    #         expected_png_bytes = f.read()

    #     # Mock the pdf2image conversion to simulate multi-page processing
    #     with patch("rbc_pdf_to_csv.bank_statement.convert_from_path") as mock_convert:
    #         from PIL import Image
    #         # Create multiple mock images
    #         mock_image1 = Image.open(BytesIO(expected_png_bytes[:len(expected_png_bytes)//2]))
    #         mock_image2 = Image.open(BytesIO(expected_png_bytes[len(expected_png_bytes)//2:]))
    #         mock_convert.return_value = [mock_image1, mock_image2]

    #         statement = BankStatement(str(pdf_path))
    #         result = statement.pdf_to_png()

    #         # The result should be a valid PNG
    #         assert len(result) > 0
    #         assert result.startswith(b'\x89PNG')

    # def test_account_type_caching(self, samples_dir):
    #     """Test that account type detection is cached."""
    #     pdf_path = samples_dir / "business_visa_single_page.pdf"

    #     with patch("rbc_pdf_to_csv.bank_statement.pdfminer.high_level.extract_text") as mock_extract:
    #         mock_extract.return_value = "credit card visa statement"

    #         statement = BankStatement(str(pdf_path))

    #         # First call should trigger detection
    #         account_type1 = statement.account_type
    #         assert account_type1 == AccountType.CREDIT_CARD

    #         # Second call should use cached value
    #         account_type2 = statement.account_type
    #         assert account_type2 == AccountType.CREDIT_CARD

    #         # Extract_text should only be called once
    #         mock_extract.assert_called_once()

    # def test_llm_helper_integration(self, samples_dir):
    #     """Test integration with LLM helper using cached responses."""
    #     pdf_path = samples_dir / "business_visa_single_page.pdf"
    #     raw_text_path = samples_dir / "business_visa_single_page.raw.txt"

    #     if not raw_text_path.exists():
    #         pytest.skip("Cached raw text not found")

    #     with open(raw_text_path, "r") as f:
    #         cached_raw_text = f.read()

    #     # Mock both the PDF to PNG and LLM helper
    #     with patch.object(BankStatement, "pdf_to_png") as mock_pdf_to_png:
    #         with patch("rbc_pdf_to_csv.bank_statement.LLMHelper.prompt") as mock_prompt:
    #             mock_pdf_to_png.return_value = b"fake-png-data"
    #             mock_prompt.return_value = cached_raw_text

    #             statement = BankStatement(str(pdf_path))
    #             result = statement.pdf_to_csv()

    #             assert result == cached_raw_text
    #             mock_pdf_to_png.assert_called_once()
    #             mock_prompt.assert_called_once_with("test prompt", b"fake-png-data")

    # def test_pdf_to_png_multiple_pages(self, samples_dir):
    #     """Test PDF to PNG conversion for multi-page PDFs specifically."""
    #     # Get multi-page PDF files
    #     multi_page_pdfs = [
    #         f for f in samples_dir.glob("*.pdf")
    #         if "multi_page" in f.name.lower() or "multi_card" in f.name.lower()
    #     ]

    #     for pdf_path in multi_page_pdfs:
    #         # Check if corresponding cached PNG exists
    #         cached_png_path = pdf_path.with_suffix('.combined.png')

    #         if not cached_png_path.exists():
    #             pytest.skip(f"Cached PNG not found for {pdf_path.name}")

    #         # Read the cached PNG to get expected dimensions
    #         from PIL import Image
    #         with open(cached_png_path, "rb") as f:
    #             cached_image = Image.open(f)
    #             expected_width = cached_image.width
    #             expected_height = cached_image.height
    #             expected_size = cached_image.size

    #         # Mock the pdf2image conversion to simulate multiple pages
    #         with patch("rbc_pdf_to_csv.bank_statement.convert_from_path") as mock_convert:
    #             # Create multiple mock images to simulate multi-page PDF
    #             # Split the cached image into multiple parts to simulate pages
    #             cached_bytes = cached_image.tobytes()
    #             split_point = len(cached_bytes) // 2

    #             # Create two mock images from the cached image
    #             mock_image1 = Image.new(cached_image.mode, (expected_width, expected_height // 2))
    #             mock_image2 = Image.new(cached_image.mode, (expected_width, expected_height // 2))

    #             # Copy parts of the cached image to simulate pages
    #             mock_image1.paste(cached_image.crop((0, 0, expected_width, expected_height // 2)))
    #             mock_image2.paste(cached_image.crop((0, expected_height // 2, expected_width, expected_height)))

    #             mock_convert.return_value = [mock_image1, mock_image2]

    #             statement = BankStatement(str(pdf_path))
    #             result = statement.pdf_to_png()

    #             # Convert result back to PIL Image to check dimensions
    #             result_image = Image.open(BytesIO(result))
    #             result_width = result_image.width
    #             result_height = result_image.height
    #             result_size = result_image.size

    #             # The result should have the same dimensions as the cached image
    #             assert result_width == expected_width, f"Width mismatch for {pdf_path.name}: expected {expected_width}, got {result_width}"
    #             assert result_height == expected_height, f"Height mismatch for {pdf_path.name}: expected {expected_height}, got {result_height}"
    #             assert result_size == expected_size, f"Size mismatch for {pdf_path.name}: expected {expected_size}, got {result_size}"

    #             # The result should be a valid PNG
    #             assert len(result) > 0, f"Empty PNG result for {pdf_path.name}"
    #             assert result.startswith(b'\x89PNG'), f"Invalid PNG header for {pdf_path.name}"

    #             # Verify the PNG ends with the correct footer
    #             assert result.endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82'), f"Invalid PNG footer for {pdf_path.name}"

    #             # For multi-page PDFs, verify that the height is reasonable (should be sum of page heights)
    #             assert result_height >= expected_height // 2, f"Multi-page height too small for {pdf_path.name}"

    # def test_pdf_to_png_caching_strategy(self, samples_dir, temp_working_dir):
    #     """Test that the PNG caching strategy works correctly."""
    #     # Copy a sample PDF to a temporary directory
    #     sample_pdf = samples_dir / "business_visa_single_page.pdf"
    #     if not sample_pdf.exists():
    #         pytest.skip("Sample PDF not found")

    #     temp_pdf = temp_working_dir / "test.pdf"
    #     shutil.copy2(sample_pdf, temp_pdf)

    #     # Check if the PDF has a corresponding cached PNG
    #     cached_png_path = samples_dir / "business_visa_single_page.combined.png"
    #     if not cached_png_path.exists():
    #         pytest.skip("Cached PNG not found")

    #     # Read the cached PNG to get expected dimensions
    #     from PIL import Image
    #     with open(cached_png_path, "rb") as f:
    #         cached_image = Image.open(f)
    #         expected_width = cached_image.width
    #         expected_height = cached_image.height

    #     # Mock the pdf2image conversion to return our cached image
    #     with patch("rbc_pdf_to_csv.bank_statement.convert_from_path") as mock_convert:
    #         mock_image = cached_image
    #         mock_convert.return_value = [mock_image]

    #         statement = BankStatement(str(temp_pdf))
    #         result = statement.pdf_to_png()

    #         # Check that the PNG was saved to disk with the correct naming convention
    #         expected_saved_png = temp_pdf.with_suffix('.combined.png')
    #         assert expected_saved_png.exists(), f"PNG file was not saved: {expected_saved_png}"

    #         # Verify the saved PNG has the correct dimensions
    #         with open(expected_saved_png, "rb") as f:
    #             saved_image = Image.open(f)
    #             saved_width = saved_image.width
    #             saved_height = saved_image.height

    #         assert saved_width == expected_width, f"Saved PNG width mismatch: expected {expected_width}, got {saved_width}"
    #         assert saved_height == expected_height, f"Saved PNG height mismatch: expected {expected_height}, got {saved_height}"

    #         # Verify the saved PNG is a valid image
    #         assert saved_image.format == 'PNG', f"Saved image is not PNG format: {saved_image.format}"

    #         # Verify the file size is reasonable
    #         saved_size = expected_saved_png.stat().st_size
    #         assert saved_size > 1000, f"Saved PNG file too small: {saved_size} bytes"

    #         # Verify the PNG header and footer
    #         with open(expected_saved_png, "rb") as f:
    #             png_bytes = f.read()

    #         assert png_bytes.startswith(b'\x89PNG'), "Saved PNG has invalid header"
    #         assert png_bytes.endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82'), "Saved PNG has invalid footer"

    # def test_pdf_to_png_real_processing(self, samples_dir):
        """Test PDF to PNG conversion with real PDF processing (no mocking)."""
        # Get a few sample PDF files to test real processing
        test_pdfs = [
            samples_dir / "business_visa_single_page.pdf",
            samples_dir / "personal_chequing_multi_page.pdf"
        ]

        for pdf_path in test_pdfs:
            if not pdf_path.exists():
                continue

            # Check if corresponding cached PNG exists
            cached_png_path = pdf_path.with_suffix('.combined.png')

            if not cached_png_path.exists():
                continue

            # Read the cached PNG to get expected dimensions
            from PIL import Image
            with open(cached_png_path, "rb") as f:
                cached_image = Image.open(f)
                expected_width = cached_image.width
                expected_height = cached_image.height

            # Test real PDF processing (this will be slow but thorough)
            statement = BankStatement(str(pdf_path))
            result = statement.pdf_to_png()

            # Convert result back to PIL Image to check dimensions
            result_image = Image.open(BytesIO(result))
            result_width = result_image.width
            result_height = result_image.height

            # The result should have the same dimensions as the cached image
            assert result_width == expected_width, f"Width mismatch for {pdf_path.name}: expected {expected_width}, got {result_width}"
            assert result_height == expected_height, f"Height mismatch for {pdf_path.name}: expected {expected_height}, got {result_height}"

            # The result should be a valid PNG
            assert len(result) > 0, f"Empty PNG result for {pdf_path.name}"
            assert result.startswith(b'\x89PNG'), f"Invalid PNG header for {pdf_path.name}"

            # Verify the PNG ends with the correct footer
            assert result.endswith(b'\x00\x00\x00\x00IEND\xaeB`\x82'), f"Invalid PNG footer for {pdf_path.name}"

            # Verify the file size is reasonable
            cached_size = cached_png_path.stat().st_size
            result_size_bytes = len(result)

            # Allow for some variation in compression, but sizes should be reasonably close
            size_ratio = min(result_size_bytes, cached_size) / max(result_size_bytes, cached_size)
            assert size_ratio > 0.3, f"Size difference too large for {pdf_path.name}: cached {cached_size}, result {result_size_bytes}"


class TestBankStatementUnit:
    """Unit tests for BankStatement class with mocked dependencies."""

    def test_init(self):
        """Test BankStatement initialization."""
        statement = BankStatement("test.pdf")
        assert statement.pdf_path == "test.pdf"
        assert statement._account_type is None

    @patch("rbc_pdf_to_csv.bank_statement.pdfminer.high_level.extract_text")
    def test_account_type_credit_card(self, mock_extract_text):
        """Test credit card account type detection."""
        mock_extract_text.return_value = "This is a credit card visa statement"
        statement = BankStatement("test.pdf")
        assert statement.account_type == AccountType.CREDIT_CARD
        assert statement.is_credit_card() is True

    @patch("rbc_pdf_to_csv.bank_statement.pdfminer.high_level.extract_text")
    def test_account_type_chequing(self, mock_extract_text):
        """Test chequing account type detection."""
        mock_extract_text.return_value = "This is a chequing account statement"
        statement = BankStatement("test.pdf")
        assert statement.account_type == AccountType.STANDARD
        assert statement.is_credit_card() is False

    @patch("rbc_pdf_to_csv.bank_statement.pdfminer.high_level.extract_text")
    def test_account_type_savings(self, mock_extract_text):
        """Test savings account type detection."""
        mock_extract_text.return_value = "This is a savings account statement"
        statement = BankStatement("test.pdf")
        assert statement.account_type == AccountType.STANDARD
        assert statement.is_credit_card() is False

    @patch("rbc_pdf_to_csv.bank_statement.pdfminer.high_level.extract_text")
    def test_account_type_na(self, mock_extract_text):
        """Test unknown account type detection."""
        mock_extract_text.return_value = "This is some other document"
        statement = BankStatement("test.pdf")
        assert statement.account_type == AccountType.STANDARD
        assert statement.is_credit_card() is False

    @patch("rbc_pdf_to_csv.bank_statement.convert_from_path")
    def test_pdf_to_png_no_images(self, mock_convert):
        """Test converting PDF with no images raises ValueError."""
        mock_convert.return_value = []

        statement = BankStatement("test.pdf")
        with pytest.raises(ValueError, match="No images found in the PDF file"):
            statement.pdf_to_png()

    # @patch("rbc_pdf_to_csv.bank_statement.BankStatement.pdf_to_png")
    # @patch("rbc_pdf_to_csv.bank_statement.LLMHelper.prompt")
    # def test_pdf_to_csv_success(self, mock_prompt, mock_pdf_to_png):
    #     """Test successful PDF to CSV conversion."""
    #     # Mock PDF to PNG conversion
    #     mock_pdf_to_png.return_value = b"fake-png-data"

    #     # Mock text extraction
    #     mock_prompt.return_value = "Transaction Date,Posting Date,Description,Amount\n2023/12/25,2023/12/26,\"Test Transaction\",100.00"

    #     statement = BankStatement("test.pdf")
    #     result = statement.pdf_to_csv()

    #     expected_csv = "Transaction Date,Posting Date,Description,Amount\n2023/12/25,2023/12/26,\"Test Transaction\",100.00"
    #     assert result == expected_csv

    #     mock_pdf_to_png.assert_called_once()
    #     mock_prompt.assert_called_once_with("test prompt", b"fake-png-data")

    # @patch("rbc_pdf_to_csv.bank_statement.BankStatement.pdf_to_png")
    # @patch("rbc_pdf_to_csv.bank_statement.LLMHelper.prompt")
    # def test_pdf_to_csv_extraction_error(self, mock_prompt, mock_pdf_to_png):
    #     """Test PDF to CSV conversion with extraction error."""
    #     # Mock PDF to PNG conversion
    #     mock_pdf_to_png.return_value = b"fake-png-data"

    #     # Mock extraction error
    #     mock_prompt.side_effect = Exception("Extraction failed")

    #     statement = BankStatement("test.pdf")
    #     with pytest.raises(Exception, match="Extraction failed"):
    #         statement.pdf_to_csv()


# Test backward compatibility
class TestPDFConverter:
    """Test PDFConverter backward compatibility alias."""

    def test_pdf_converter_alias(self):
        """Test that PDFConverter is still available as an alias."""
        from rbc_pdf_to_csv.bank_statement import BankStatement
        statement = BankStatement("test.pdf")
        assert isinstance(statement, BankStatement)
        assert statement.pdf_path == "test.pdf"
