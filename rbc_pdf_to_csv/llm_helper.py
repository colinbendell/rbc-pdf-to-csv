"""LLM helper functionality for AI operations using Gemini API."""

import base64
import json
from typing import Optional, Union, List, Tuple

import requests

import mysecrets

class LLMHelper:
    """Helper class for LLM operations using Gemini API."""

    _instance = None

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM helper only once.

        Args:
            api_key: Gemini API key. If None, uses mysecrets.GEMINI_API_KEY
        """
        self.api_key = api_key or mysecrets.GEMINI_API_KEY
        self.model = "gemini-2.0-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    @classmethod
    def initialize(cls, api_key: Optional[str] = None) -> 'LLMHelper':
        """Initialize the singleton instance.

        Args:
            api_key: Gemini API key. If None, uses mysecrets.GEMINI_API_KEY

        Returns:
            The initialized LLMHelper instance
        """
        return cls(api_key)

    @classmethod
    def get_instance(cls, api_key: Optional[str] = None) -> 'LLMHelper':
        """Get the singleton instance.

        Returns:
            The LLMHelper instance

        Raises:
            RuntimeError: If the instance hasn't been initialized yet
        """
        if cls._instance is None:
            cls._instance = cls(api_key)
        return cls._instance

    def send_prompt(self, prompt_text: str, data: Union[bytes, List[bytes], Tuple[bytes, str], List[Tuple[bytes, str]], None] = None) -> str:
        """Internal implementation of prompt functionality.

        Args:
            prompt_text: The text prompt to send to the API
            data: Can be one of:
                - None: Text-only prompt (no data)
                - bytes: Single image/data bytes (assumes image/png)
                - List[bytes]: Multiple image/data bytes (assumes image/png for all)
                - Tuple[bytes, str]: Single bytes with mimetype
                - List[Tuple[bytes, str]]: Multiple bytes with their mimetypes

        Returns:
            Extracted text from the API response

        Raises:
            requests.RequestException: If API request fails
            ValueError: If API response is invalid
        """
        parts = [{"text": prompt_text}]

        # Handle different input types
        if data is None:
            # Text-only prompt, no data to add
            data_list = []
        elif isinstance(data, bytes):
            # Single bytes object - assume image/png
            data_list = [(data, "image/png")]
        elif isinstance(data, list):
            if data and isinstance(data[0], tuple):
                # List of (bytes, mimetype) tuples
                data_list = data
            else:
                # List of bytes - assume image/png for all
                data_list = [(item, "image/png") for item in data]
        elif isinstance(data, tuple):
            # Single (bytes, mimetype) tuple
            data_list = [data]
        else:
            raise ValueError("data must be None, bytes, list of bytes, tuple of (bytes, str), or list of (bytes, str) tuples")

        # Add all data parts
        for item_bytes, mimetype in data_list:
            data_b64 = str(base64.b64encode(item_bytes), "utf-8")
            parts.append({"inlineData": {"mimeType": mimetype, "data": data_b64}})

        body = {
            "contents": [
                {
                    "parts": parts,
                }
            ],
        }

        resp = requests.post(self.api_url, json=body)
        resp.raise_for_status()

        resp_data = json.loads(resp.text)
        texts = []

        for candidate in resp_data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                texts.append(part.get("text", "").strip())

        if not texts:
            raise ValueError("No text content received from API")

        return "\n".join(texts)

    def prompt(self, prompt_text: str, data: Union[bytes, List[bytes], Tuple[bytes, str], List[Tuple[bytes, str]], None] = None) -> str:
        """Send a prompt to the Gemini API with optional data.

        Args:
            prompt_text: The text prompt to send to the API
            data: Can be one of:
                - None: Text-only prompt (no data)
                - bytes: Single image/data bytes (assumes image/png)
                - List[bytes]: Multiple image/data bytes (assumes image/png for all)
                - Tuple[bytes, str]: Single bytes with mimetype
                - List[Tuple[bytes, str]]: Multiple bytes with their mimetypes

        Returns:
            Extracted text from the API response

        Raises:
            requests.RequestException: If API request fails
            ValueError: If API response is invalid
        """
        return self.send_prompt(prompt_text, data)

    @classmethod
    def prompt(cls, prompt_text: str, data: Union[bytes, List[bytes], Tuple[bytes, str], List[Tuple[bytes, str]], None] = None, api_key: Optional[str] = None) -> str:
        """Send a prompt to the Gemini API with optional data. Auto-initializes the singleton if needed.

        Args:
            prompt_text: The text prompt to send to the API
            data: Can be one of:
                - None: Text-only prompt (no data)
                - bytes: Single image/data bytes (assumes image/png)
                - List[bytes]: Multiple image/data bytes (assumes image/png for all)
                - Tuple[bytes, str]: Single bytes with mimetype
                - List[Tuple[bytes, str]]: Multiple bytes with their mimetypes
            api_key: Gemini API key. If None, uses mysecrets.GEMINI_API_KEY

        Returns:
            Extracted text from the API response

        Raises:
            requests.RequestException: If API request fails
            ValueError: If API response is invalid
        """
        # Get or create the singleton instance
        instance = cls.get_instance()
        return instance.send_prompt(prompt_text, data)
