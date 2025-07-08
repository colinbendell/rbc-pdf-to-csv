"""Core PDF processing functionality."""

import os
from io import StringIO
from typing import List, Optional

import pandas as pd

from .bank_statement import BankStatement
from .llm_helper import LLMHelper
from .prompts import CATEGORIZATION_PROMPT
from .utils import clean_date_column, sanitize_description


class PDFProcessor:
    """Main class for processing PDF statements and converting to CSV."""

    _debug: bool = False

    def __init__(self, debug: bool = False):
        self._debug = debug

    def process_credit_card_statement(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process credit card statement DataFrame.

        Args:
            df: Raw DataFrame from AI extraction

        Returns:
            Processed DataFrame
        """
        clean_date_column(df, "Transaction Date")
        clean_date_column(df, "Posting Date")
        df["Amount"] = df["Amount"].astype(float)

        # Make purchases on credit card negative, credits positive
        df["Amount"] = df["Amount"] * -1

        # Filter out automatic payment to pay off credit card balance
        if "Activity Description" in df.columns:
            df.rename(columns={"Activity Description": "Description"}, inplace=True)

        df["Description"] = df["Description"].apply(sanitize_description)

        df = df[["Transaction Date", "Posting Date", "File", "Description", "Amount"]]
        return df

    def process_bank_statement(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process bank statement DataFrame.

        Args:
            df: Raw DataFrame from AI extraction

        Returns:
            Processed DataFrame
        """
        clean_date_column(df, "Date")
        df["Withdrawals"] = df["Withdrawals"].astype(float)
        df["Deposit"] = df["Deposit"].astype(float)
        df.fillna(value={"Withdrawals": 0.0, "Deposit": 0.0}, inplace=True)
        df["Description"] = df["Description"].apply(sanitize_description)

        df["Amount"] = (df["Withdrawals"] * -1.0) + df["Deposit"]

        # Filter out rows that include "Opening or Closing Balance" in the description
        df = df[~df["Description"].str.contains("opening balance", na=False, case=False)]
        df = df[~df["Description"].str.contains("Closing balance", na=False, case=False)]

        df = df[["Date", "File", "Description", "Amount"]]
        return df

    def categorize_transactions(self, csv_path: str, training_data_csv: str) -> str:
        """Categorize transactions in a CSV file using LLM.

        Args:
            csv_path: Path to the CSV file with transactions
            sample_categories_path: Path to the sample categories CSV file

        Returns:
            Path to the categorized CSV file
        """
        # Read the transaction CSV
        with open(csv_path, 'r') as f:
            transactions_csv = f.read()

        # Read the sample categories CSV
        with open(training_data_csv, 'r') as f:
            categories_csv = f.read()

        # Create the prompt with both CSVs
        prompt = f"{CATEGORIZATION_PROMPT}\n\nReference categories:\n{categories_csv}\n\nTransactions to categorize:\n{transactions_csv}"

        # Get categorized CSV from LLM
        try:
            categorized_csv = LLMHelper.prompt(prompt, None)  # No image data needed for text-only prompt
            # Clean up the response by removing markdown code blocks if present
            categorized_csv = categorized_csv.removeprefix("```csv").removeprefix("```").removesuffix("```").strip()
        except Exception as e:
            raise RuntimeError(f"Failed to categorize transactions: {e}")

        # Write the categorized CSV back to the same file
        with open(csv_path, 'w') as f:
            f.write(categorized_csv)

        return csv_path

    def process_pdf(self, pdf_path: str, out_csv: Optional[str] = None, training_data_csv: Optional[str] = None) -> str:
        """Process a single PDF file and convert to CSV.

        Args:
            pdf_path: Path to the PDF file
            out_csv: Path to the output CSV file (defaults to pdf_path.csv)
            training_data_csv: Path to the training data CSV file (defaults to sample-categories.csv)

        Returns:
            Path to the generated CSV file
        """
        if out_csv is None:
            out_csv = pdf_path.removesuffix(".pdf") + ".csv"

        # Create BankStatement instance for this PDF
        statement = BankStatement(pdf_path, self._debug)

        try:
            csv_text = statement.pdf_to_csv()
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF {pdf_path}: {e}")

        try:
            df = pd.read_csv(StringIO(csv_text))
        except Exception as e:
            # Retry with more lenient parsing
            csv_text = statement.pdf_to_csv()
            df = pd.read_csv(StringIO(csv_text))

        # add a column with a static value on all rows
        df["File"] = os.path.basename(pdf_path)

        if statement.is_credit_card():
            df = self.process_credit_card_statement(df)
        else:
            df = self.process_bank_statement(df)

        df.to_csv(out_csv, index=False)

        if self._debug:
            df.to_csv(out_csv.removesuffix(".csv") + ".processed.csv", index=False)

        if training_data_csv is not None:
            # Add categorization step
            try:
                self.categorize_transactions(out_csv, training_data_csv)
            except Exception as e:
                # Log the error but don't fail the entire process
                print(f"Warning: Failed to categorize transactions: {e}")

        return out_csv
