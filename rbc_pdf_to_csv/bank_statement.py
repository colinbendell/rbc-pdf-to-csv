"""PDF to image conversion and AI processing functionality."""

import io
import re
from typing import Optional

from pdf2image import convert_from_path
from PIL import Image
import pdfminer.high_level

from .llm_helper import LLMHelper
from .prompts import BANK_ACCOUNT_PROMPT, CREDIT_CARD_PROMPT
from .utils import AccountType

# Because we convert the image to a PNG, we need to disable the PIL max image pixels limit
Image.MAX_IMAGE_PIXELS = None

class BankStatement:
    """Handles PDF to image conversion and AI processing for bank statements."""

    _png_bytes: Optional[bytes] = None

    def __init__(self, pdf_path: str):
        """Initialize the bank statement processor.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = pdf_path

        # Detect and store the account type
        self._account_type = None

    @property
    def account_type(self) -> AccountType:
        """Get the detected account type for this statement.

        Returns:
            AccountType enum indicating the detected account type
        """
        if self._account_type is None:
            self._account_type = self._detect_account_type()
        return self._account_type

    def _detect_account_type(self) -> AccountType:
        """Detect the type of account from PDF content.

        Returns:
            AccountType enum indicating the detected account type
        """
        text = pdfminer.high_level.extract_text(self.pdf_path)

        # Check for credit card indicators
        credit_card_pattern = re.compile(r"credit\s*card.*(visa|mastercard)", re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if credit_card_pattern.search(text):
            return AccountType.CREDIT_CARD
        return AccountType.STANDARD

    def is_credit_card(self) -> bool:
        """Check if this is a credit card statement.

        Returns:
            True if this is a credit card statement
        """
        return self.account_type == AccountType.CREDIT_CARD

    def pdf_to_png(self) -> bytes:
        """Convert the PDF file to PNG format using pdf2image.

        Returns:
            PNG image bytes of the PDF file

        Raises:
            ValueError: If no images found in PDF
        """
        if self._png_bytes is not None:
            return self._png_bytes

        # Convert PDF pages to a list of PIL Image objects
        images = convert_from_path(self.pdf_path, dpi=600)

        if len(images) == 0:
            raise ValueError("No images found in the PDF file.")

        if len(images) == 1:
            combined_image = images[0]
        else:
            # Create a new image with the total height of all images and the width of the first image
            total_height = sum(image.height for image in images)
            width = images[0].width
            combined_image = Image.new("RGB", (width, total_height))

            # Paste each image into the combined image
            y_offset = 0
            for image in images:
                combined_image.paste(image, (0, y_offset))
                y_offset += image.height

        # Save the combined image to a bytes buffer
        buffer = io.BytesIO()
        combined_image.save(buffer, format="PNG")
        self._png_bytes = buffer.getvalue()
        return self._png_bytes

    def pdf_to_csv(self) -> str:
        """Convert the PDF file to CSV using the Gemini API.

        Returns:
            CSV text extracted from the PDF

        Raises:
            requests.RequestException: If API request fails
            ValueError: If API response is invalid
        """

        prompt = CREDIT_CARD_PROMPT if self.is_credit_card() else BANK_ACCOUNT_PROMPT
        png_bytes = self.pdf_to_png()
        result = LLMHelper.prompt(prompt, png_bytes)
        return result.removeprefix("```csv").removesuffix("```")
