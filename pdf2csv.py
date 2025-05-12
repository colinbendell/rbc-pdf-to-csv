#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#    "certifi",
#    "numpy",
#    "pandas",
#    "requests",
#    "argparse",
#    "pdfminer.six",
#    "pdf2image (>=1.17.0,<2.0.0)",
# ]
# ///

import argparse
import json
import base64
import requests
import os
import sys
import glob
import re
import pdfminer.high_level
import io
from pdf2image import convert_from_path

import mysecrets

CREDIT_CARD_PROMPT = """The given file is a credit statement. Extract transactions as a CSV with the following columns:
  - "Transaction Date" with values in the format yyyy/mm/dd. Get the year from the line "Statement from month day, year to month day, year".
  - "Posting Date" with values in the format yyyy/mm/dd. Get the year from the line "Statement from month day, year to month day, year".
  - "Description" with values inside double quotes. Do not include any `"` or `,` in the value. Include the foreign currency and value in paranthensis with the exchange rate prefixed with ` @ ` if available inside the double quotes.
  - "Amount" with values formatted as float with two decimal places. Do not put `$` or `,` in the value.

Only output the CSV and no other explanations.
"""

BANK_ACCOUNT_PROMPT = """As an expert accountant, extract transactions from the provided bank statement. Columns are right justified. Produce a CSV with the following columns:
  - "Date" with values in the format yyyy/mm/dd. Get the year from the line "Account statement from month day, year to month day, year".
  - "Description" with values inside double quotes. Do not include any `"` or `,` in the value. Include the foreign currency and value in paranthensis with the exchange rate prefixed with ` @ ` if available inside the double quotes.
  - "Withdrawals" (also might be called "Cheques & Debits"). Format the values as float with two decimal places. Do not put `$` or `,` in the value.
  - "Deposit" (also might be called "Credits" or the column just to the left of the "balance" column). Format the values as float with two decimal places. Do not put `$` or `,` in the value.
  - "Balance" with values formatted as float with two decimal places. Do not put `$` or `,` in the value.

Only output the CSV and no other explanations.
"""

PDF_CREDITCARD_RE = re.compile(r"credit\s*card.*(visa|mastercard)", re.IGNORECASE | re.DOTALL | re.MULTILINE)

def pdf_to_png(pdf_path: str) -> bytes:
    """Convert a PDF file to PNG format using pdf2image. The output is a high resolution single PNG image.

    Args:
        pdf_path (str): path to the PDF to convert

    Returns:
        bytes: png image of the pdf file
    """
    # Convert PDF pages to a list of PIL Image objects
    images = convert_from_path(pdf_path, dpi=600, fmt="png", single_file=True)

    # Save the combined image to a bytes buffer
    buffer = io.BytesIO()
    images[0].save(buffer, format="PNG")
    return buffer.getvalue()


def pdf_to_csv(prompt: str, pdf_path: str, force: bool = False) -> bool:
    """Convert a PDF file to CSV using the Gemini API.
    Args:
        prompt (str): The prompt to use for the Gemini API.
        pdf_path (str): The path to the PDF file.
        force (bool): Whether to force overwrite the CSV file if it already exists.
    Returns:
        bool: True if the conversion was successful, False if the CSV file already exists.
    """

    out_csv = pdf_path.removesuffix(".pdf") + ".csv"
    if not force and os.path.exists(out_csv):
        return False
    model = "gemini-2.0-flash"
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}".format(
        model, mysecrets.GEMINI_API_KEY
    )
    parts = [{"text": prompt}]
    bytes = pdf_to_png(pdf_path)
    data = str(base64.b64encode(bytes), "utf-8")
    parts.append({"inlineData": {"mimeType": "image/png", "data": data}})
    body = {
        "contents": [
            {
                "parts": parts,
            }
        ],
    }
    resp = requests.post(api_url, json=body)
    resp = json.loads(resp.text)
    texts = []
    for candidate in resp.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            texts.append(part.get("text", "").strip())
    text = "\n".join(texts).removeprefix("```csv").removesuffix("```")
    with open(out_csv, "w") as ofp:
        ofp.write(text)
    return True


def contains_card_type(pdf_path: str) -> bool:
    text = pdfminer.high_level.extract_text(pdf_path)
    return PDF_CREDITCARD_RE.search(text)


def acct_pdf2csv(files: list[str], force: bool = False) -> None:
    for i, pdf_path in enumerate(files):
        print("Processing {}/{}: {}.".format(i + 1, len(files), pdf_path), end='', flush=True)
        prompt = CREDIT_CARD_PROMPT if contains_card_type(pdf_path) else BANK_ACCOUNT_PROMPT
        if pdf_to_csv(prompt=prompt, pdf_path=pdf_path, force=force):
            print("✅ Done")
        else:
            print("⏭️ Skipping")


def main(args):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="force overwrite of existing CSV files",
    )

    parser.add_argument(
        "pdf_files",
        default=glob.glob("**/*.pdf", recursive=True),
        nargs="*",
        help="input PDF statements (default: **/*.pdf)",
    )

    args = parser.parse_args()
    force = args.force
    pdf_files = [f for f in args.pdf_files if os.path.isfile(f)]
    pdf_files += [
        f
        for d in args.pdf_files
        if os.path.isdir(d)
        for f in glob.glob(d + "/**/*.pdf", recursive=True)
    ]

    if len(pdf_files) == 0:
        print("No PDF files found.")
        return 1
    pdf_files.sort()
    acct_pdf2csv(files=pdf_files, force=force)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
