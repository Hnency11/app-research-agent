import json
import httpx
from typing import Optional, Type, TypeVar

from google import genai
from google.genai import types

from pydantic import BaseModel, ValidationError

from core.config import settings
from core.logger import logger
from core.utils import retry_async
from services.base import BaseLLMService

T = TypeVar("T", bound=BaseModel)


class LLMService(BaseLLMService):
    """Production LLM API client supporting structured schema extraction."""

    def __init__(self, api_key: Optional[str] = None, provider: str = "gemini"):
        self.api_key = api_key
        self.provider = provider.lower()

        if self.provider == "gemini":
            self._client = genai.Client(
                api_key=self.api_key or settings.GEMINI_API_KEY)
        else:
            self._client = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT_SECONDS
        )

        logger.debug(f"LLMService initialized. Provider={self.provider}")

    def is_available(self) -> bool:
        if self.provider == "gemini":
            key = self.api_key or settings.GEMINI_API_KEY
        else:
            key = self.api_key or settings.OPENAI_API_KEY

        return bool(

            key
            and key.strip()
            and "your_" not in key
        )

    def sanitize_json(self, raw_text: str) -> str:
        """Public method to strip markdown code-fence wrappers from JSON responses.

        Prefer this over the private _sanitize_json() method from external callers.
        """
        return self._sanitize_json(raw_text)

    async def aclose(self) -> None:
        """Close the shared HTTP client and release connection pool resources."""
        if self.provider == "openai":
            await self._client.aclose()

    @retry_async(max_retries=3, exceptions=(httpx.HTTPError, Exception))
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate textual completion for a prompt.

        Args:
            prompt: User prompt content.
            system_prompt: Optional instructing system prompt.

        Returns:
            str: Generated text answer.
        """
        return await self._call_llm_api(prompt, system_prompt, response_json=False)

    @retry_async(max_retries=3, exceptions=(ValidationError, Exception))
    async def generate_structured(
        self, 
        prompt: str, 
        response_model: Type[T], 
        system_prompt: Optional[str] = None
    ) -> T:
        """Generate structured data conforming to a target Pydantic schema.

        Args:
            prompt: User prompt.
            response_model: The Pydantic model subclass defining the expected structure.
            system_prompt: Optional system prompt context.

        Returns:
            T: An instance of the requested Pydantic model.
        """
        logger.info(f"Generating structured response for model: {response_model.__name__}")

        # Inject JSON schema details to guide the LLM
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        enriched_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: You must return ONLY a JSON object that conforms strictly to this JSON Schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Do not include markdown wrappers, thoughts, or explanations. Respond with pure JSON."
        )

        raw_response = await self._call_llm_api(enriched_prompt, system_prompt, response_json=True)
        sanitized_response = self.sanitize_json(raw_response)

        try:
            return response_model.model_validate_json(sanitized_response)
        except ValidationError as e:
            logger.error(f"Structured validation failed on response: {sanitized_response}. Error: {str(e)}")
            raise

    async def _call_llm_api(self, prompt: str, system_prompt: Optional[str] = None, response_json: bool = False) -> str:
        """Helper to invoke OpenAI or Gemini APIs, falling back to mock outputs if key is missing."""
        
        # 1. Determine key and invoke provider (reuses is_available() logic)
        if self.provider == "gemini":
            api_key = self.api_key or settings.GEMINI_API_KEY
            if self.is_available():
                return await self._call_gemini(prompt, system_prompt, api_key, response_json)
        
        elif self.provider == "openai":
            api_key = self.api_key or settings.OPENAI_API_KEY
            if self.is_available():
                return await self._call_openai(prompt, system_prompt, api_key, response_json)

        # 2. Fallback to mock data if key not configured
        logger.warning(
            f"LLM API Key for {self.provider} not configured or uses placeholder values. "
            "Generating mock string response."
        )
        if response_json:
            # We return a JSON string representing mock data
            # To know which schema, we check the prompt keywords
            if "VerificationResult" in prompt:
                mock_model_name = "VerificationResult"
            elif "ResearchStatistics" in prompt:
                mock_model_name = "ResearchStatistics"
            else:
                mock_model_name = "AppResearch"
            
            # Reconstruct mock models dict
            from core.models import AppResearch, VerificationResult, ResearchStatistics
            dummy_dict = {}
            if mock_model_name == "AppResearch":
                # Get the app name if possible
                app_name = "MockApp"
                for line in prompt.split("\n"):
                    if "Extract information about the application:" in line:
                        app_name = line.split(":")[-1].replace('"', '').strip()
                dummy_dict = {
                    "app_name": app_name,
                    "category": "Developer Tooling",
                    "description": f"Official developer APIs and services of {app_name}.",
                    "auth_methods": ["API Key", "OAuth2"],
                    "self_serve_status": "self-serve",
                    "api_surface": "Public Cloud API documentation portal.",
                    "api_types": ["REST", "Webhooks"],
                    "sdk_available": True,
                    "webhook_support": True,
                    "mcp_support": False,
                    "buildability_verdict": "buildable",
                    "main_blocker": None,
                    "evidence": [
                        {
                            "url": "https://docs.example.com",
                            "title": "API Reference Documentation",
                            "snippet": "We support OAuth2 and REST webhooks.",
                            "extracted_at": "2026-07-09T18:55:00Z"
                        }
                    ],
                    "confidence_score": 90.0,
                    "verification_status": "unverified",
                    "verification_notes": None,
                    "last_updated": "2026-07-09T18:55:00Z"
                }
            elif mock_model_name == "VerificationResult":
                dummy_dict = {
                    "is_verified": True,
                    "verified_fields": ["auth_methods", "api_types"],
                    "mismatches": {},
                    "notes": "Verified against provided excerpts.",
                    "verified_at": "2026-07-09T18:55:00Z"
                }
            return json.dumps(dummy_dict)
        
        return f"Mock text response for {self.provider}."

    async def _call_gemini(
        self,
        prompt: str,
        system_prompt: Optional[str],
        api_key: str,
        response_json: bool,
    ) -> str:
        """Call Gemini using the official Google GenAI SDK."""

        contents = prompt
        if system_prompt:
            contents = f"{system_prompt}\n\n{prompt}"

        config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.95,
            max_output_tokens=8192,
        )

        if response_json:
            config.response_mime_type = "application/json"

        response = self._client.models.generate_content(
            model="models/gemini-3-flash-preview",
            contents=contents,
            config=config,
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        return response.text

    async def _call_openai(self, prompt: str, system_prompt: Optional[str], api_key: str, response_json: bool) -> str:
        """Call OpenAI chat/completions API."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload: dict = {"model": "gpt-4o-mini", "messages": messages}
        if response_json:
            payload["response_format"] = {"type": "json_object"}

        # Use shared client — no per-call context manager
        response = await self._client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Unexpected structure from OpenAI API: {data}")
            raise ValueError("Could not parse OpenAI API text output.") from e

    def _sanitize_json(self, raw_text: str) -> str:
        """Clean markdown markers to retrieve pure JSON data."""
        text = raw_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()
