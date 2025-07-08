"""LLM helper functionality for AI operations using Gemini API."""

import base64
import json
import os
import time
from typing import Optional, Union, List, Tuple

import requests

import mysecrets

# Retry configuration constants
MAX_RETRIES = 5
BASE_DELAY = 3  # seconds

class LLMHelper:
    """Helper class for LLM operations using Gemini API."""

    _instance = None

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM helper only once.

        Args:
            api_key: Gemini API key. If None, uses mysecrets.GEMINI_API_KEY
        """
        self.api_key = api_key or mysecrets.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self.model = "gemini-2.5-flash"
        self.api_url = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent?key={self.api_key}"

        self.session = requests.Session()

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

        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = self.session.post(self.api_url, json=body)

                # If it's a 5xx error and we haven't exhausted retries, retry
                if 500 <= resp.status_code < 600 and attempt < MAX_RETRIES:
                    delay = BASE_DELAY * (2 ** attempt)  # Exponential backoff
                    print(f"\n ... delaying {delay}s ({status_code}) #{attempt + 1}/{MAX_RETRIES}", end='', flush=True)
                    # Close the connection to force reconnection on next request
                    self.session.close()
                    time.sleep(delay)
                    continue

                # For all other cases, raise the status error
                resp.raise_for_status()
                break

            except requests.RequestException as e:
                # Close the connection on any error to force reconnection
                self.session.close()

                status_code = getattr(e.response, 'status_code', 0)
                if status_code == 429:
                    # look for type.googleapis.com/google.rpc.RetryInfo in the response text and extract the retry delay
                    if e.response.headers.get("content-type").startswith("application/json"):
                        error_body = json.loads(e.response.text)
                        # look in error.details[3].retryDelay where the details entry has "@type": "type.googleapis.com/google.rpc.RetryInfo",
                        retry_info = next((detail for detail in error_body.get("error", {}).get("details", []) if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo"), None)
                        retry_delay = retry_info.get("retryDelay", "0s") if retry_info else "0s"
                        # convert to int if it is a string with a number and a unit
                        if isinstance(retry_delay, str):
                            delay = int(retry_delay.removesuffix("s")) + 1
                        else:
                            delay = retry_delay + 1
                        print(f"\n ... delaying {delay}s ({status_code}) #{attempt + 1}/{MAX_RETRIES}", end='', flush=True)
                        time.sleep(delay)
                        continue

                # If it's the last attempt or not a 5xx error, re-raise
                if attempt == MAX_RETRIES or not (500 <= status_code < 600):
                    raise

                # Otherwise, retry with exponential backoff
                delay = BASE_DELAY * (2 ** attempt)
                print(f"\n ... delaying {delay}s ({status_code}) #{attempt + 1}/{MAX_RETRIES}", end='', flush=True)
                time.sleep(delay)

        resp_data = json.loads(resp.text)
        texts = []

        for candidate in resp_data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                texts.append(part.get("text", "").strip())

        if not texts:
            raise ValueError("No text content received from API")

        return "\n".join(texts)

    def close(self):
        """Close the session and clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()

    def __del__(self):
        """Cleanup when the object is destroyed."""
        self.close()

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
