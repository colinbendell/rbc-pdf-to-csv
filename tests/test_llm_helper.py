"""Tests for LLMHelper functionality."""

import pytest
import base64
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

from rbc_pdf_to_csv.llm_helper import LLMHelper


class TestLLMHelper:
    """Test LLMHelper class."""

    def test_init_with_api_key(self):
        """Test initialization with custom API key."""
        api_key = "test-api-key"
        helper = LLMHelper(api_key)
        assert helper.api_key == api_key
        assert helper.model == "gemini-2.0-flash"
        assert "test-api-key" in helper.api_url

    @patch("rbc_pdf_to_csv.llm_helper.mysecrets.GEMINI_API_KEY", "default-key")
    def test_init_without_api_key(self):
        """Test initialization without API key uses default."""
        helper = LLMHelper()
        assert helper.api_key == "default-key"

    @patch("rbc_pdf_to_csv.llm_helper.requests.post")
    def test_prompt_single_bytes(self, mock_post):
        """Test prompting with single bytes object."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '{"candidates": [{"content": {"parts": [{"text": "Transaction Date,Posting Date,Description,Amount\\n2023/12/25,2023/12/26,\\"Test Transaction\\",100.00"}]}}]}'
        mock_post.return_value = mock_response

        helper = LLMHelper("test-key")
        result = helper.prompt("test prompt", b"fake-image-data")

        expected_text = "Transaction Date,Posting Date,Description,Amount\n2023/12/25,2023/12/26,\"Test Transaction\",100.00"
        assert result == expected_text

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["contents"][0]["parts"][0]["text"] == "test prompt"
        assert call_args[1]["json"]["contents"][0]["parts"][1]["inlineData"]["mimeType"] == "image/png"

    @patch("rbc_pdf_to_csv.llm_helper.requests.post")
    def test_prompt_list_of_bytes(self, mock_post):
        """Test prompting with list of bytes objects."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '{"candidates": [{"content": {"parts": [{"text": "Multiple images processed"}]}}]}'
        mock_post.return_value = mock_response

        helper = LLMHelper("test-key")
        result = helper.prompt("test prompt", [b"image1", b"image2"])

        assert result == "Multiple images processed"

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert len(call_args[1]["json"]["contents"][0]["parts"]) == 3  # text + 2 images
        assert call_args[1]["json"]["contents"][0]["parts"][1]["inlineData"]["mimeType"] == "image/png"
        assert call_args[1]["json"]["contents"][0]["parts"][2]["inlineData"]["mimeType"] == "image/png"

    @patch("rbc_pdf_to_csv.llm_helper.requests.post")
    def test_prompt_tuple_bytes_mimetype(self, mock_post):
        """Test prompting with tuple of bytes and mimetype."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '{"candidates": [{"content": {"parts": [{"text": "PDF processed"}]}}]}'
        mock_post.return_value = mock_response

        helper = LLMHelper("test-key")
        result = helper.prompt("test prompt", (b"fake-pdf-data", "application/pdf"))

        assert result == "PDF processed"

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["contents"][0]["parts"][1]["inlineData"]["mimeType"] == "application/pdf"

    @patch("rbc_pdf_to_csv.llm_helper.requests.post")
    def test_prompt_list_of_tuples(self, mock_post):
        """Test prompting with list of (bytes, mimetype) tuples."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '{"candidates": [{"content": {"parts": [{"text": "Mixed data processed"}]}}]}'
        mock_post.return_value = mock_response

        helper = LLMHelper("test-key")
        data = [(b"image1", "image/png"), (b"pdf1", "application/pdf")]
        result = helper.prompt("test prompt", data)

        assert result == "Mixed data processed"

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert len(call_args[1]["json"]["contents"][0]["parts"]) == 3  # text + 2 data items
        assert call_args[1]["json"]["contents"][0]["parts"][1]["inlineData"]["mimeType"] == "image/png"
        assert call_args[1]["json"]["contents"][0]["parts"][2]["inlineData"]["mimeType"] == "application/pdf"

    def test_prompt_invalid_data_type(self):
        """Test prompting with invalid data type raises ValueError."""
        helper = LLMHelper("test-key")
        with pytest.raises(ValueError, match="data must be None, bytes, list of bytes, tuple of \\(bytes, str\\), or list of \\(bytes, str\\) tuples"):
            helper.prompt("test prompt", StringIO("invalid data"))

    @patch("rbc_pdf_to_csv.llm_helper.requests.post")
    def test_prompt_with_csv_markers(self, mock_post):
        """Test prompting with CSV code block markers in response."""
        # Mock API response with CSV markers
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '{"candidates": [{"content": {"parts": [{"text": "```csv\\nTransaction Date,Description,Amount\\n2023/12/25,\\"Test\\",100.00\\n```"}]}}]}'
        mock_post.return_value = mock_response

        helper = LLMHelper("test-key")
        result = helper.prompt("test prompt", b"fake-image-data")

        expected_text = "```csv\nTransaction Date,Description,Amount\n2023/12/25,\"Test\",100.00\n```"
        assert result == expected_text

    @patch("rbc_pdf_to_csv.llm_helper.requests.post")
    def test_prompt_api_error(self, mock_post):
        """Test prompting with API error."""
        # Mock API error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_response

        helper = LLMHelper("test-key")
        with pytest.raises(Exception, match="API Error"):
            helper.prompt("test prompt", b"fake-image-data")

    @patch("rbc_pdf_to_csv.llm_helper.requests.post")
    def test_prompt_no_text_content(self, mock_post):
        """Test prompting with no text content in response."""
        # Mock API response with no text content
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '{"candidates": []}'
        mock_post.return_value = mock_response

        helper = LLMHelper("test-key")
        with pytest.raises(ValueError, match="No text content received from API"):
            helper.prompt("test prompt", b"fake-image-data")
