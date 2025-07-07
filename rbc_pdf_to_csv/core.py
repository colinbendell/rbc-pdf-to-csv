"""Core PDF processing functionality."""

import os
from io import StringIO
from typing import List, Optional

import pandas as pd

from .bank_statement import BankStatement
from .utils import clean_date_column, sanitize_description


class PDFProcessor:
    """Main class for processing PDF statements and converting to CSV."""

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
        df.drop(columns=["Withdrawals", "Deposit"], inplace=True)
        df = df[["Date", "Description", "Amount", "Balance"]]

        # Filter out rows that include "Opening or Closing Balance" in the description
        df = df[~df["Description"].str.contains("opening balance", na=False, case=False)]
        df = df[~df["Description"].str.contains("Closing balance", na=False, case=False)]

        return df

    def process_pdf(self, pdf_path: str, out_csv: Optional[str] = None) -> str:
        """Process a single PDF file and convert to CSV.

        Args:
            pdf_path: Path to the PDF file
            out_csv: Path to the output CSV file (defaults to pdf_path.csv)

        Returns:
            Path to the generated CSV file
        """
        if out_csv is None:
            out_csv = pdf_path.removesuffix(".pdf") + ".csv"

        # Create BankStatement instance for this PDF
        statement = BankStatement(pdf_path)

        try:
            csv_text = statement.pdf_to_csv()
        except Exception as e:
            raise RuntimeError(f"Failed to convert PDF {pdf_path}: {e}")

        try:
            df = pd.read_csv(StringIO(csv_text))
        except Exception as e:
            # Retry with more lenient parsing
            df = pd.read_csv(StringIO(csv_text), on_bad_lines='warn', engine='python')

        if statement.is_credit_card():
            df = self.process_credit_card_statement(df)
        else:
            df = self.process_bank_statement(df)

        df.to_csv(out_csv, index=False)
        return out_csv
