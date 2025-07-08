"""Tests for command-line interface."""

import pytest
import os
from unittest.mock import patch, call, MagicMock

from rbc_pdf_to_csv.cli import find_files, main


class TestFindFiles:
    """Test file discovery functionality."""

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    def test_find_files_single_pdf_file(self, mock_isdir, mock_isfile):
        """Test finding single PDF file."""
        mock_isfile.return_value = True
        mock_isdir.return_value = False

        result = find_files(["test.pdf"], "pdf")
        assert result == ["test.pdf"]

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    def test_find_files_single_csv_file(self, mock_isdir, mock_isfile):
        """Test finding single CSV file."""
        mock_isfile.return_value = True
        mock_isdir.return_value = False

        result = find_files(["test.csv"], "csv")
        assert result == ["test.csv"]

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    @patch("glob.glob")
    def test_find_files_directory_pdf(self, mock_glob, mock_isdir, mock_isfile):
        """Test finding PDF files in directory."""
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        mock_glob.return_value = ["dir/file1.pdf", "dir/file2.pdf"]

        result = find_files(["test_dir"], "pdf")
        assert result == ["dir/file1.pdf", "dir/file2.pdf"]
        mock_glob.assert_called_once_with("test_dir/**/*.pdf", recursive=True)

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    @patch("glob.glob")
    def test_find_files_directory_csv(self, mock_glob, mock_isdir, mock_isfile):
        """Test finding CSV files in directory."""
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        mock_glob.return_value = ["dir/file1.csv", "dir/file2.csv"]

        result = find_files(["test_dir"], "csv")
        assert result == ["dir/file1.csv", "dir/file2.csv"]
        mock_glob.assert_called_once_with("test_dir/**/*.csv", recursive=True)

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    def test_find_files_mixed_pdf(self, mock_isdir, mock_isfile):
        """Test finding PDF files from mixed file and directory inputs."""
        def isfile_side_effect(path):
            return path == "file1.pdf"

        def isdir_side_effect(path):
            return path == "test_dir"

        mock_isfile.side_effect = isfile_side_effect
        mock_isdir.side_effect = isdir_side_effect

        with patch("glob.glob", return_value=["test_dir/file2.pdf"]):
            result = find_files(["file1.pdf", "test_dir"], "pdf")
            assert result == ["file1.pdf", "test_dir/file2.pdf"]

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    def test_find_files_nonexistent(self, mock_isdir, mock_isfile):
        """Test finding files from nonexistent paths."""
        mock_isfile.return_value = False
        mock_isdir.return_value = False

        result = find_files(["nonexistent.pdf", "nonexistent_dir"], "pdf")
        assert result == []

    def test_find_files_empty_input(self):
        """Test finding files with empty input."""
        result = find_files([], "pdf")
        assert result == []

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    def test_find_files_extension_filtering(self, mock_isdir, mock_isfile):
        """Test that only files with the correct extension are returned."""
        def isfile_side_effect(path):
            return path in ["test.pdf", "test.csv", "test.txt"]

        def isdir_side_effect(path):
            return False

        mock_isfile.side_effect = isfile_side_effect
        mock_isdir.side_effect = isdir_side_effect

        result_pdf = find_files(["test.pdf", "test.csv", "test.txt"], "pdf")
        assert result_pdf == ["test.pdf"]

        result_csv = find_files(["test.pdf", "test.csv", "test.txt"], "csv")
        assert result_csv == ["test.csv"]


class TestMain:
    """Test main CLI function."""

    @patch("rbc_pdf_to_csv.cli.find_files")
    @patch("rbc_pdf_to_csv.cli.PDFProcessor")
    def test_main_success(self, mock_processor_class, mock_find_files):
        """Test successful main execution."""
        mock_find_files.return_value = ["file1.pdf", "file2.pdf"]
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        result = main(["--force", "file1.pdf", "file2.pdf"])

        mock_find_files.assert_called_once_with(["file1.pdf", "file2.pdf"], "pdf")
        assert result == 0
        mock_processor.assert_has_calls(
            [
                call.process_pdf("file1.pdf", out_csv="file1.csv", training_data_csv=None),
                call.process_pdf("file2.pdf", out_csv="file2.csv", training_data_csv=None),
            ]
        )

    @patch("rbc_pdf_to_csv.cli.find_files")
    def test_main_no_files_found(self, mock_find_files):
        """Test main execution with no PDF files found."""
        mock_find_files.return_value = []

        result = main(["file1.pdf"])

        assert result == 2

    @patch("rbc_pdf_to_csv.cli.find_files")
    @patch("rbc_pdf_to_csv.cli.PDFProcessor")
    def test_main_default_files(self, mock_processor_class, mock_find_files):
        """Test main execution with default file discovery."""
        mock_find_files.return_value = ["default1.pdf", "default2.pdf"]
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        result = main([])

        assert result == 0

    @patch("rbc_pdf_to_csv.cli.find_files")
    @patch("rbc_pdf_to_csv.cli.PDFProcessor")
    def test_main_force_flag(self, mock_processor_class, mock_find_files):
        """Test main execution with force flag."""
        mock_find_files.return_value = ["file1.pdf"]
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        result = main(["-f", "file1.pdf"])

        assert result == 0
        mock_processor.assert_has_calls(
            [
                call.process_pdf("file1.pdf", out_csv="file1.csv", training_data_csv=None),
            ]
        )

    @patch("rbc_pdf_to_csv.cli.find_files")
    @patch("rbc_pdf_to_csv.cli.PDFProcessor")
    def test_main_processor_error(self, mock_processor_class, mock_find_files):
        """Test main execution with processor error."""
        mock_find_files.return_value = ["file1.pdf"]
        mock_processor = MagicMock()
        mock_processor.process_pdf.side_effect = Exception("Processing error")
        mock_processor_class.return_value = mock_processor

        # Should not raise exception, just return 0
        result = main(["file1.pdf"])

        assert result == 1

    @patch("rbc_pdf_to_csv.cli.find_files")
    @patch("rbc_pdf_to_csv.cli.PDFProcessor")
    def test_main_categorize_csv_specific_files(self, mock_processor_class, mock_find_files):
        """Test main execution with --categorize-only and specific files."""
        mock_find_files.return_value = ["file1.csv", "file2.csv"]
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        result = main(["--categorize-only", "file1.csv", "file2.csv"])

        assert result == 0
        mock_find_files.assert_called_once_with(["file1.csv", "file2.csv"], "csv")
        mock_processor.assert_has_calls(
            [
                call.categorize_transactions("file1.csv", None),
                call.categorize_transactions("file2.csv", None),
            ]
        )

    @patch("rbc_pdf_to_csv.cli.find_files")
    @patch("rbc_pdf_to_csv.cli.PDFProcessor")
    def test_main_categorize_csv_no_files(self, mock_processor_class, mock_find_files):
        """Test main execution with --categorize-only and no files found."""
        mock_find_files.return_value = []
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        result = main(["--categorize-only", "nonexistent.csv"])

        assert result == 2

    @patch("rbc_pdf_to_csv.cli.find_files")
    @patch("rbc_pdf_to_csv.cli.PDFProcessor")
    def test_main_categorize_csv_error(self, mock_processor_class, mock_find_files):
        """Test main execution with --categorize-only and processing error."""
        mock_find_files.return_value = ["file1.csv"]
        mock_processor = MagicMock()
        mock_processor.categorize_transactions.side_effect = Exception("Categorization error")
        mock_processor_class.return_value = mock_processor

        result = main(["--categorize-only", "file1.csv"])

        assert result == 1

    @patch("rbc_pdf_to_csv.cli.find_files")
    @patch("rbc_pdf_to_csv.cli.PDFProcessor")
    def test_main_categorize_csv_with_custom_categories(self, mock_processor_class, mock_find_files):
        """Test main execution with --categorize-only and custom categories file."""
        mock_find_files.return_value = ["file1.csv"]
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        result = main(["--categorize-only", "file1.csv", "--training-data", "custom-categories.csv"])

        assert result == 0
        mock_find_files.assert_called_once_with(["file1.csv"], "csv")
        mock_processor.assert_has_calls(
            [
                call.categorize_transactions("file1.csv", "custom-categories.csv"),
            ]
        )

    @patch("rbc_pdf_to_csv.cli.find_files")
    @patch("rbc_pdf_to_csv.cli.PDFProcessor")
    def test_main_pdf_with_custom_categories(self, mock_processor_class, mock_find_files):
        """Test main execution with PDF processing and custom categories file."""
        mock_find_files.return_value = ["file1.pdf"]
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        result = main(["--force", "file1.pdf", "--training-data", "custom-categories.csv"])

        assert result == 0
        mock_find_files.assert_called_once_with(["file1.pdf"], "pdf")
        mock_processor.assert_has_calls(
            [
                call.process_pdf("file1.pdf", out_csv="file1.csv", training_data_csv="custom-categories.csv"),
            ]
        )
