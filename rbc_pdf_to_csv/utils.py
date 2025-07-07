"""Utility functions for date handling and data processing."""

import re
from datetime import datetime
from enum import Enum
from typing import Union

import pandas as pd
import pdfminer.high_level


class AccountType(Enum):
    """Enumeration of account types."""
    CREDIT_CARD = "credit_card"
    STANDARD = "standard"

def iso8601_date(d: str) -> str:
    """Convert various date formats to YYYY-MM-DD format.

    Args:
        d: Date string in various formats

    Returns:
        Date string in YYYY-MM-DD format

    Raises:
        ValueError: If date format is not supported
    """
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
    raise ValueError(f"unsupported date format: {d}")


def clean_date_column(df: pd.DataFrame, column: str) -> None:
    """Clean and standardize date column in DataFrame.

    Args:
        df: DataFrame containing the date column
        column: Name of the date column to clean
    """
    d = pd.to_datetime(df[column], format="%Y/%m/%d", errors="coerce").min()
    if pd.isna(d):
        raise RuntimeError(f"no valid dates in column {column}")

    for i in range(len(df)):
        cur = df.loc[i, column]
        if pd.isna(cur):
            df.loc[i, column] = d
            continue
        try:
            d = iso8601_date(cur)
        except ValueError:
            pass
        df.loc[i, column] = d

def sanitize_description(description: str) -> str:
    """Sanitize transaction description by removing newlines.

    Args:
        description: Raw description string

    Returns:
        Sanitized description string
    """
    return re.sub(r"\n+", " ", description)
