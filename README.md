# RBC PDF to CSV Converter

Convert RBC bank and credit card PDF statements to CSV format using AI-powered text extraction.

## Features

- Automatically detects credit card vs bank account statements
- Uses Google Gemini AI for accurate text extraction
- Handles multiple date formats and data cleaning
- Supports batch processing of multiple PDF files
- Generates standardized CSV output

## Installation

### Prerequisites

- Python 3.13 or higher
- Google Gemini API key

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd rbc-pdf-to-csv
```

2. Install dependencies:
```bash
pip install -e .
```

3. Create a `mysecrets.py` file with your Gemini API key:
```python
GEMINI_API_KEY = "your-api-key-here"
```

## Usage

### Command Line Interface

Process all PDF files in the current directory:
```bash
rbc-pdf-to-csv
```

Process specific PDF files:
```bash
rbc-pdf-to-csv file1.pdf file2.pdf
```

Process files in a directory:
```bash
rbc-pdf-to-csv /path/to/statements/
```

Force overwrite existing CSV files:
```bash
rbc-pdf-to-csv --force *.pdf
```

### Python API

```python
from rbc_pdf_to_csv import PDFProcessor

# Initialize processor
processor = PDFProcessor()

# Process a single file
result = processor.process_pdf("statement.pdf")

# Process multiple files
results = processor.process_files(["file1.pdf", "file2.pdf"], force=True)
```

## Project Structure

```
rbc-pdf-to-csv/
├── rbc_pdf_to_csv/          # Main package
│   ├── __init__.py          # Package initialization
│   ├── cli.py              # Command-line interface
│   ├── core.py             # Main processing logic
│   ├── pdf_converter.py    # PDF to image conversion
│   ├── prompts.py          # AI prompts
│   └── utils.py            # Utility functions
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Pytest configuration
│   ├── test_cli.py         # CLI tests
│   ├── test_core.py        # Core functionality tests
│   ├── test_pdf_converter.py # PDF converter tests
│   └── test_utils.py       # Utility function tests
├── pyproject.toml          # Project configuration
└── README.md              # This file
```

## Development

### Running Tests

Install test dependencies:
```bash
pip install -e ".[test]"
```

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=rbc_pdf_to_csv
```

### Code Quality

The project uses:
- **pytest** for testing
- **pytest-cov** for coverage reporting
- **pytest-mock** for mocking in tests
- **pytest-asyncio** for async test support

## Output Format

### Credit Card Statements
- Transaction Date (YYYY-MM-DD)
- Posting Date (YYYY-MM-DD)
- Description
- Amount (negative for purchases, positive for credits)

### Bank Account Statements
- Date (YYYY-MM-DD)
- Description
- Amount (negative for withdrawals, positive for deposits)
- Balance

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request
