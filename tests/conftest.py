# /// script
# requires-python = ">=3.13"
# dependencies = [
#    "pytest",
#    "pytest-cov",
#    "pytest-mock",
#    "pytest-xdist",
# ]
# ///

"""Pytest configuration and fixtures."""

import pytest
import pandas as pd
from unittest.mock import MagicMock
from pathlib import Path
import base64
import tempfile
import shutil
import logging

CREDIT_CARD_PDFS = [
    "samples/business_visa_multi_card.pdf",
    "samples/business_visa_multi_page_2.pdf",
    "samples/business_visa_multi_page_3.pdf",
    "samples/business_visa_multi_page.pdf",
    "samples/business_visa_single_page.pdf",
    "samples/personal_visa_multi_page.pdf",
]

BANK_ACCOUNT_PDFS = [
    "samples/business_chequing_multi_line.pdf",
    "samples/personal_chequing_multi_page_2.pdf",
    "samples/personal_chequing_multi_page_3.pdf",
    "samples/personal_chequing_multi_page.pdf",
]

ALL_PDFS = CREDIT_CARD_PDFS + BANK_ACCOUNT_PDFS

@pytest.fixture
def logger(caplog):
    caplog.set_level(logging.INFO)
    return logging.getLogger(__name__)

@pytest.fixture
def samples_dir():
    """Get the samples directory path."""
    return Path(__file__).parent.parent / "samples"


@pytest.fixture
def temp_working_dir():
    """Create a temporary working directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_credit_card_df():
    """Sample credit card DataFrame for testing."""
    return pd.DataFrame({
        "Transaction Date": ["2023/12/25", "2023/12/26"],
        "Posting Date": ["2023/12/26", "2023/12/27"],
        "Description": ["Test Transaction 1", "Test Transaction 2"],
        "Amount": ["100.00", "200.00"]
    })


@pytest.fixture
def sample_bank_account_df():
    """Sample bank account DataFrame for testing."""
    return pd.DataFrame({
        "Date": ["2023/12/25", "2023/12/26"],
        "Description": ["Test Transaction 1", "Test Transaction 2"],
        "Withdrawals": ["100.00", "0.00"],
        "Deposit": ["0.00", "200.00"],
        "Balance": ["1000.00", "1200.00"]
    })


@pytest.fixture
def mock_pdf_converter():
    """Mock PDF converter for testing."""
    converter = MagicMock()
    converter.pdf_to_csv.return_value = "Transaction Date,Posting Date,Description,Amount\n2023/12/25,2023/12/26,\"Test\",100.00"
    return converter


@pytest.fixture
def credit_card_samples(samples_dir):
    """Get credit card sample files."""
    return [
        f for f in samples_dir.glob("*.pdf")
        if "visa" in f.name.lower() and f.suffix == ".pdf"
    ]


@pytest.fixture
def bank_account_samples(samples_dir):
    """Get bank account sample files."""
    return [
        f for f in samples_dir.glob("*.pdf")
        if "chequing" in f.name.lower() or "savings" in f.name.lower()
    ]


@pytest.fixture
def sample_credit_card_raw_text(samples_dir):
    """Get sample credit card raw text."""
    raw_text_path = samples_dir / "business_visa_single_page.raw.txt"
    if raw_text_path.exists():
        with open(raw_text_path, "r") as f:
            return f.read()
    return """```csv
Transaction Date,Posting Date,Description,Amount
2023/11/17,2023/11/20,"PAYMENT - THANK YOU / PAIEMENT - MERCI",-642.64
2023/11/21,2023/11/22,"MDBILLING.CA TORONTO ON",27.35
```"""


@pytest.fixture
def sample_bank_account_raw_text(samples_dir):
    """Get sample bank account raw text."""
    raw_text_path = samples_dir / "personal_chequing_multi_page.raw.txt"
    if raw_text_path.exists():
        with open(raw_text_path, "r") as f:
            return f.read()
    return """```csv
Date,Description,Withdrawals,Deposit,Balance
2025/03/21,"Online transfer received-7463",,2000.00,18454.29
2025/03/26,"Misc Payment Hydro Ottawa",83.70,,18370.59
```"""


@pytest.fixture
def sample_credit_card_csv(samples_dir):
    """Get sample credit card CSV data."""
    csv_path = samples_dir / "business_visa_single_page.csv"
    if csv_path.exists():
        with open(csv_path, "r") as f:
            return f.read()
    return """Transaction Date,Posting Date,Description,Amount
2023-11-17,2023-11-20,PAYMENT - THANK YOU / PAIEMENT - MERCI,642.64
2023-11-21,2023-11-22,MDBILLING.CA TORONTO ON,-27.35"""


@pytest.fixture
def sample_bank_account_csv(samples_dir):
    """Get sample bank account CSV data."""
    csv_path = samples_dir / "personal_chequing_multi_page.csv"
    if csv_path.exists():
        with open(csv_path, "r") as f:
            return f.read()
    return """Date,Description,Amount,Balance
2025-03-21,Online transfer received-7463,2000.0,18454.29
2025-03-26,Misc Payment Hydro Ottawa,-83.7,18370.59"""


@pytest.fixture
def sample_png_bytes(samples_dir):
    """Get sample PNG bytes from cached image."""
    png_path = samples_dir / "business_visa_single_page.combined.png"
    if png_path.exists():
        with open(png_path, "rb") as f:
            return f.read()
    # Return a minimal PNG if cached file doesn't exist
    return base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "Transaction Date,Posting Date,Description,Amount\n2023/12/25,2023/12/26,\"Test Transaction\",100.00"}
                    ]
                }
            }
        ]
    }


@pytest.fixture
def mock_api_response():
    """Mock API response for testing."""
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "```csv\nTransaction Date,Posting Date,Description,Amount\n2023/12/25,2023/12/26,\"Test Transaction\",100.00\n```"}
                    ]
                }
            }
        ]
    }
