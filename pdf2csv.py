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
#    "charset-normalizer",
#    "idna",
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
from io import StringIO

from pdf2image import convert_from_path
from PIL import Image
import argparse
import pandas as pd
from pandas.api.types import is_float_dtype
from pandas.core.api import DataFrame
from datetime import datetime

import mysecrets

CREDIT_CARD_PROMPT = """You are a helpful assistant and an expert accountant. Extract transactions from the provided credit card statement, as if you were reading it naturally. Columns are right justified. Produce a CSV with the following columns:
  - "Transaction Date" with values in the format yyyy/mm/dd. Get the year from the line "Statement from month day, year to month day, year".
  - "Posting Date" with values in the format yyyy/mm/dd. Get the year from the line "Statement from month day, year to month day, year".
  - "Description" with values inside double quotes. Do not include double quotes (`"`) or commas (`,`) in the value. Include the foreign currency and value in paranthensis with the exchange rate prefixed with ` @ ` if available inside the double quotes.
  - "Amount" with values formatted as float with two decimal places. Do not put `$` or `,` in the value.

Only output a valid CSV file with no other explanations.
"""

BANK_ACCOUNT_PROMPT = """You are a helpful assistant and an expert accountant. Extract transactions from the provided bank statement, as if you were reading it naturally. Columns are right justified. Produce a CSV with the following columns:
  - "Date" with values in the format yyyy/mm/dd. Get the year from the line "Account statement from month day, year to month day, year".
  - "Description" with values inside double quotes. Do not include any `"` or `,` in the value. Include the foreign currency and value in paranthensis with the exchange rate prefixed with ` @ ` if available inside the double quotes.
  - "Withdrawals" (also might be called "Cheques & Debits"). Format the values as float with two decimal places. Do not put `$` or `,` in the value.
  - "Deposit" (also might be called "Credits" or the column just to the left of the "balance" column). Format the values as float with two decimal places. Do not put `$` or `,` in the value.
  - "Balance" with values formatted as float with two decimal places. Do not put `$` or `,` in the value.

Only output a valid CSV file with 5 fields and no other explanations.
"""

PDF_CREDITCARD_RE = re.compile(r"credit\s*card.*(visa|mastercard)", re.IGNORECASE | re.DOTALL | re.MULTILINE)

def canon_date(d: str) -> str:
    try:
        return datetime.strptime(d, "%Y/%m/%d").strftime("%Y-%m-%d")
    except ValueError:
        pass
    try:
        return datetime.strptime(d, "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError:
        pass
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        pass
    raise ValueError("unsupported date format: {}".format(d))


def clean_date_column(df: pd.DataFrame, column: str):
    d = pd.to_datetime(df[column], format="%Y/%m/%d", errors="coerce").min()
    if pd.isna(d):
        raise RuntimeError("no valid dates in column {}".format(column))
    for i in range(len(df)):
        cur = df.loc[i, column]
        if pd.isna(cur):
            df.loc[i, column] = d
            continue
        try:
            d = canon_date(cur)
        except ValueError:
            pass
        df.loc[i, column] = d

def pdf_to_png(pdf_path: str) -> bytes:
    """Convert a PDF file to PNG format using pdf2image. The output is a high resolution single PNG image.

    Args:
        pdf_path (str): path to the PDF to convert

    Returns:
        bytes: png image of the pdf file
    """
    # Convert PDF pages to a list of PIL Image objects
    images = convert_from_path(pdf_path, dpi=600, fmt="png")

    # merge all the images into a single image
    if len(images) == 0:
        raise ValueError("No images found in the PDF file.")
    # Create a new image with the total height of all images and the width of the first image
    total_height = sum(image.height for image in images)
    width = images[0].width
    combined_image = Image.new("RGB", (width, total_height))
    # Paste each image into the combined image
    y_offset = 0
    for image in images:
        combined_image.paste(image, (0, y_offset))
        y_offset += image.height

    # save the combined image to a file
    combined_image.save(pdf_path.removesuffix(".pdf") + ".combined.png", format="PNG")
    # Save the combined image to a bytes buffer
    buffer = io.BytesIO()
    combined_image.save(buffer, format="PNG")
    return buffer.getvalue()

def pdf_to_csv(prompt: str, pdf_path: str, force: bool = False) -> str:
    """Convert a PDF file to CSV using the Gemini API.
    Args:
        prompt (str): The prompt to use for the Gemini API.
        pdf_path (str): The path to the PDF file.
        force (bool): Whether to force overwrite the CSV file if it already exists.
    Returns:
        bool: True if the conversion was successful, False if the CSV file already exists.
    """

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
    raw_text = "\n".join(texts)
    # safe the raw text to a file
    with open(pdf_path.removesuffix(".pdf") + ".raw.txt", "w") as ofp:
        ofp.write(raw_text)
    text = "\n".join(texts).removeprefix("```csv").removesuffix("```")
    return text

def write_csv(csv_path: str, text: str) -> None:
    """Write the given text to a CSV file.

    Args:
        csv_path (str): The path to the CSV file.
        text (str): The text to write to the CSV file.
    """
    with open(csv_path, "w") as ofp:
        ofp.write(text)

def contains_card_type(pdf_path: str) -> bool:
    text = pdfminer.high_level.extract_text(pdf_path)
    return PDF_CREDITCARD_RE.search(text)


def acct_pdf2csv(files: list[str], force: bool = False) -> None:
    for i, pdf_path in enumerate(files):
        print("Processing {}/{}: {}.".format(i + 1, len(files), pdf_path), end='', flush=True)

        out_csv = pdf_path.removesuffix(".pdf") + ".csv"
        if not force and os.path.exists(out_csv):
            print("⏭️ Skipping")
            continue

        is_credit_card = contains_card_type(pdf_path)
        prompt = CREDIT_CARD_PROMPT if is_credit_card else BANK_ACCOUNT_PROMPT
        csv = pdf_to_csv(prompt=prompt, pdf_path=pdf_path, force=force)
        try:
            df = pd.read_csv(StringIO(csv))
        except Exception as e:
            print(f"Failed to parse CSV: {e}")
            print("Retrying...")
            # Retry with more lenient parsing
            df = pd.read_csv(StringIO(csv), on_bad_lines='warn', engine='python')

        if is_credit_card:
            clean_date_column(df, "Transaction Date")
            clean_date_column(df, "Posting Date")
            df["Amount"] = df["Amount"].astype(float)

            # Make purchases on credit card negative, credits positive.
            df["Amount"] = df["Amount"] * -1
            # Filter out automatic payment to pay off credit card balance.
            if "Activity Description" in df.columns:
                df.rename(columns={"Activity Description": "Description"}, inplace=True)
            df["Description"] = df["Description"].apply(lambda d: d.replace("\n", " "))
        else:
            clean_date_column(df, "Date")
            df["Withdrawals"] = df["Withdrawals"].astype(float)
            df["Deposit"] = df["Deposit"].astype(float)
            df.fillna(value={"Withdrawals": 0.0, "Deposit": 0.0}, inplace=True)
            df["Description"] = df["Description"].apply(lambda d: d.replace("\n", " "))

            df["Amount"] = (df["Withdrawals"] * -1.0) + df["Deposit"]
            df.drop(columns=["Withdrawals", "Deposit"], inplace=True)
            df = df[["Date", "Description", "Amount", "Balance"]]

            # filter out rows that include "Opening or Closing Balance" in the description
            df = df[~df["Description"].str.contains("opening balance", na=False, case=False)]
            df = df[~df["Description"].str.contains("Closing balance", na=False, case=False)]
        # remove trailing slashes in the base_dir filename and replace leading "." with empty string
        df.to_csv(out_csv, index=False)

        print("✅ Done")


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
