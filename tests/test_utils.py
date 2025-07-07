"""Tests for utility functions."""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from rbc_pdf_to_csv.utils import (
    iso8601_date,
    clean_date_column,
    sanitize_description,
)


class TestCanonDate:
    """Test date canonicalization function."""

    def test_yyyy_mm_dd_format(self):
        """Test YYYY/MM/DD format."""
        assert iso8601_date("2023/12/25") == "2023-12-25"

    def test_month_day_year_format(self):
        """Test Month Day, Year format."""
        assert iso8601_date("December 25, 2023") == "2023-12-25"

    def test_yyyy_mm_dd_dash_format(self):
        """Test YYYY-MM-DD format."""
        assert iso8601_date("2023-12-25") == "2023-12-25"

    def test_invalid_format(self):
        """Test invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="unsupported date format"):
            iso8601_date("invalid-date")

    def test_empty_string(self):
        """Test empty string raises ValueError."""
        with pytest.raises(ValueError):
            iso8601_date("")


class TestCleanDateColumn:
    """Test date column cleaning function."""

    def test_valid_dates(self):
        """Test cleaning column with valid dates."""
        df = pd.DataFrame({
            "Date": ["2023/12/25", "2023/12/26", "2023/12/27"]
        })
        clean_date_column(df, "Date")
        expected = ["2023-12-25", "2023-12-26", "2023-12-27"]
        assert df["Date"].tolist() == expected

    def test_mixed_date_formats(self):
        """Test cleaning column with mixed date formats."""
        df = pd.DataFrame({
            "Date": ["2023/12/25", "December 26, 2023", "2023-12-27"]
        })
        clean_date_column(df, "Date")
        expected = ["2023-12-25", "2023-12-26", "2023-12-27"]
        assert df["Date"].tolist() == expected

    def test_with_nan_values(self):
        """Test cleaning column with NaN values."""
        df = pd.DataFrame({
            "Date": ["2023/12/25", pd.NA, "2023/12/27"]
        })
        clean_date_column(df, "Date")
        # NaN should be filled with the minimum date
        assert df["Date"].iloc[1] == "2023-12-25"

    def test_no_valid_dates(self):
        """Test cleaning column with no valid dates."""
        df = pd.DataFrame({
            "Date": ["invalid", "also-invalid", "not-a-date"]
        })
        with pytest.raises(RuntimeError, match="no valid dates in column"):
            clean_date_column(df, "Date")

    def test_empty_dataframe(self):
        """Test cleaning empty DataFrame."""
        df = pd.DataFrame({"Date": []})
        with pytest.raises(RuntimeError):
            clean_date_column(df, "Date")

class TestSanitizeDescription:
    """Test description sanitization function."""

    def test_remove_newlines(self):
        """Test removing newlines from description."""
        description = "Transaction\nwith\nnewlines"
        result = sanitize_description(description)
        assert result == "Transaction with newlines"

    def test_no_newlines(self):
        """Test description without newlines."""
        description = "Simple transaction"
        result = sanitize_description(description)
        assert result == "Simple transaction"

    def test_multiple_newlines(self):
        """Test multiple consecutive newlines."""
        description = "Transaction\n\nwith\n\n\nmultiple\n\nnewlines"
        result = sanitize_description(description)
        assert result == "Transaction with multiple newlines"

    def test_empty_string(self):
        """Test empty string."""
        result = sanitize_description("")
        assert result == ""

    def test_only_newlines(self):
        """Test string with only newlines."""
        result = sanitize_description("\n\n\n")
        assert result == " "
