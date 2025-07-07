"""Tests for command-line interface."""

import pytest
import os
from unittest.mock import patch, call, MagicMock

from rbc_pdf_to_csv.cli import find_pdf_files, main


class TestFindPDFFiles:
    """Test PDF file discovery functionality."""

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    def test_find_pdf_files_single_file(self, mock_isdir, mock_isfile):
        """Test finding single PDF file."""
        mock_isfile.return_value = True
        mock_isdir.return_value = False

        result = find_pdf_files(["test.pdf"])
        assert result == ["test.pdf"]

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    @patch("glob.glob")
    def test_find_pdf_files_directory(self, mock_glob, mock_isdir, mock_isfile):
        """Test finding PDF files in directory."""
        mock_isfile.return_value = False
        mock_isdir.return_value = True
        mock_glob.return_value = ["dir/file1.pdf", "dir/file2.pdf"]

        result = find_pdf_files(["test_dir"])
        assert result == ["dir/file1.pdf", "dir/file2.pdf"]
        mock_glob.assert_called_once_with("test_dir/**/*.pdf", recursive=True)

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    def test_find_pdf_files_mixed(self, mock_isdir, mock_isfile):
        """Test finding PDF files from mixed file and directory inputs."""
        def isfile_side_effect(path):
            return path == "file1.pdf"

        def isdir_side_effect(path):
            return path == "test_dir"

        mock_isfile.side_effect = isfile_side_effect
        mock_isdir.side_effect = isdir_side_effect

        with patch("glob.glob", return_value=["test_dir/file2.pdf"]):
            result = find_pdf_files(["file1.pdf", "test_dir"])
            assert result == ["file1.pdf", "test_dir/file2.pdf"]

    @patch("os.path.isfile")
    @patch("os.path.isdir")
    def test_find_pdf_files_nonexistent(self, mock_isdir, mock_isfile):
        """Test finding PDF files from nonexistent paths."""
        mock_isfile.return_value = False
        mock_isdir.return_value = False

        result = find_pdf_files(["nonexistent.pdf", "nonexistent_dir"])
        assert result == []

    def test_find_pdf_files_empty_input(self):
        """Test finding PDF files with empty input."""
        result = find_pdf_files([])
        assert result == []


class TestMain:
    """Test main CLI function."""

    @patch("rbc_pdf_to_csv.cli.find_pdf_files")
    @patch("rbc_pdf_to_csv.cli.PDFProcessor")
    def test_main_success(self, mock_processor_class, mock_find_files):
        """Test successful main execution."""
        mock_find_files.return_value = ["file1.pdf", "file2.pdf"]
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        result = main(["--force", "file1.pdf", "file2.pdf"])

        assert result == 0
        mock_find_files.assert_called_once_with(["file1.pdf", "file2.pdf"])
        mock_processor.assert_has_calls(
            [
                call.process_pdf("file1.pdf", out_csv="file1.csv"),
                call.process_pdf("file2.pdf", out_csv="file2.csv"),
            ]
        )

    @patch("rbc_pdf_to_csv.cli.find_pdf_files")
    def test_main_no_files_found(self, mock_find_files):
        """Test main execution with no PDF files found."""
        mock_find_files.return_value = []

        result = main(["file1.pdf"])

        assert result == 2

    @patch("rbc_pdf_to_csv.cli.find_pdf_files")
    @patch("rbc_pdf_to_csv.cli.PDFProcessor")
    def test_main_default_files(self, mock_processor_class, mock_find_files):
        """Test main execution with default file discovery."""
        mock_find_files.return_value = ["default1.pdf", "default2.pdf"]
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor

        result = main([])

        assert result == 0

    @patch("rbc_pdf_to_csv.cli.find_pdf_files")
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
                call.process_pdf("file1.pdf", out_csv="file1.csv"),
            ]
        )

    @patch("rbc_pdf_to_csv.cli.find_pdf_files")
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
