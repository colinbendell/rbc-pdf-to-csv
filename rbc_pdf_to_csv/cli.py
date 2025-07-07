"""Command-line interface for the RBC PDF to CSV converter."""

import argparse
import glob
import os
import sys
from typing import List

from .core import PDFProcessor


def find_pdf_files(paths: List[str]) -> List[str]:
    """Find PDF files from the given paths.

    Args:
        paths: List of file or directory paths

    Returns:
        List of PDF file paths
    """
    pdf_files = []

    for path in paths:
        if os.path.isfile(path):
            pdf_files.append(path)
        elif os.path.isdir(path):
            pdf_files.extend(glob.glob(os.path.join(path, "**/*.pdf"), recursive=True))

    return sorted(pdf_files)


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
            "pdf_files",
            default=glob.glob("**/*.pdf", recursive=True),
            nargs="*",
            help="Input PDF statements (default: **/*.pdf)",
        )

        parsed_args = parser.parse_args(args)

        pdf_files = find_pdf_files(parsed_args.pdf_files)

        if len(pdf_files) == 0:
            print("No PDF files found.")
            return 2

        processor = PDFProcessor()

        for i, pdf_path in enumerate(pdf_files):
            print(f"Processing {i + 1}/{len(pdf_files)}: {pdf_path}.", end='', flush=True)

            try:
                out_csv = pdf_path.removesuffix(".pdf") + ".csv"
                if os.path.exists(out_csv) and not parsed_args.force:
                    print("⏭️ Skipping")
                    continue

                processor.process_pdf(pdf_path, out_csv=out_csv)
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
