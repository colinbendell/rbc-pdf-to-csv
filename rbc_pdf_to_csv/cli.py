"""Command-line interface for the RBC PDF to CSV converter."""

import argparse
import glob
import os
import sys
from typing import List

from .core import PDFProcessor


def find_files(paths: List[str], extension: str = "pdf") -> List[str]:
    """Find files with the given extension from the given paths.

    Args:
        paths: List of file or directory paths
        extension: File extension to search for (without the dot)

    Returns:
        List of file paths with the specified extension
    """
    files = []

    for path in paths:
        if os.path.isfile(path):
            if path.lower().endswith(f".{extension.lower()}"):
                files.append(path)
        elif os.path.isdir(path):
            files.extend(glob.glob(os.path.join(path, f"**/*.{extension}"), recursive=True))

    return sorted(files)


def main(args: List[str] = None) -> int:
    """Main CLI entry point.

    Args:
        args: Command line arguments. If None, uses sys.argv[1:]

    Returns:
        Exit code (0 for success, 1 for general error, 2 for no files found)
    """
    try:
        if args is None:
            args = sys.argv[1:]

        parser = argparse.ArgumentParser(
            description="Convert RBC bank and credit card PDF statements to CSV format"
        )

        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Force overwrite of existing CSV files",
        )

        parser.add_argument(
            "-c",
            "--categorize-only",
            action="store_true",
            help="Categorize existing CSV file(s) with a Category column using the LLM. If no files specified, finds all CSV files in current directory and subdirectories."
        )

        parser.add_argument(
            "-t",
            "--training-data",
            default=None,
            help="Path to the training data CSV file to use for categorization"
        )

        parser.add_argument(
            "files",
            default=glob.glob("**/*.pdf", recursive=True),
            nargs="*",
            help="Input PDF statements (default: **/*.pdf)",
        )

        parsed_args = parser.parse_args(args)

        processor = PDFProcessor()

        # If --categorize-only is used, process those CSVs and exit
        if parsed_args.categorize_only:
            csv_files = find_files(parsed_args.files, "csv")

            if len(csv_files) == 0:
                print("No CSV files found.")
                return 2

            for i, csv_path in enumerate(csv_files):
                print(f"Categorizing {i + 1}/{len(csv_files)}: {csv_path}...", end='', flush=True)
                try:
                    processor.categorize_transactions(csv_path, parsed_args.training_data)
                    print("✅ Done")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    return 1
            return 0

        pdf_files = find_files(parsed_args.files, "pdf")

        if len(pdf_files) == 0:
            print("No PDF files found.")
            return 2

        for i, pdf_path in enumerate(pdf_files):
            print(f"Processing {i + 1}/{len(pdf_files)}: {pdf_path}.", end='', flush=True)

            try:
                out_csv = pdf_path.removesuffix(".pdf") + ".csv"
                if os.path.exists(out_csv) and not parsed_args.force:
                    print("⏭️ Skipping")
                    continue

                processor.process_pdf(pdf_path, out_csv=out_csv, training_data_csv=parsed_args.training_data)
                print("✅ Done")
            except Exception as e:
                print(f"❌ Error: {e}")
                return 1

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 130  # Standard exit code for Ctrl+C
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return 1
    except PermissionError as e:
        print(f"Error: Permission denied - {e}")
        return 1
    except ValueError as e:
        print(f"Error: Invalid input - {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
