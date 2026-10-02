"""Unified LLM model adapter for Loglan Bench supporting Google GenAI (Gemma), Ollama, and baselines."""

import json
import os
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any

try:
    from src.config import (
        GEMINI_API_KEY,
        OLLAMA_BASE_URL,
        OPENAI_API_KEY,
        ANTHROPIC_API_KEY,
        DEFAULT_MODEL,
        FALLBACK_GEMINI_MODEL
    )
except ImportError:
    from config import (
        GEMINI_API_KEY,
        OLLAMA_BASE_URL,
        OPENAI_API_KEY,
        ANTHROPIC_API_KEY,
        DEFAULT_MODEL,
        FALLBACK_GEMINI_MODEL
    )


@dataclass
class ModelResponse:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_sec: float = 0.0
    provider: str = "unknown"
    metadata: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract interface for language model providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> ModelResponse:
        pass


class GoogleGenAIProvider(BaseLLMProvider):
    """Provider for Google GenAI SDK (Gemma 3 & Gemini models)."""

    def __init__(self, model_name: str = DEFAULT_MODEL, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please provide it via .env or GEMINI_API_KEY environment variable."
            )
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "The 'google-genai' package is required. Install it with: pip install google-genai"
            )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> ModelResponse:
        from google.genai import types

        start_time = time.time()
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_prompt if system_prompt else None,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
        except Exception as e:
            # If the specific Gemma model isn't active on the endpoint, try fallback gemini model
            if self.model_name != FALLBACK_GEMINI_MODEL and "not found" in str(e).lower():
                print(f"[Warning] Model '{self.model_name}' not available on endpoint; trying fallback '{FALLBACK_GEMINI_MODEL}'")
                response = self.client.models.generate_content(
                    model=FALLBACK_GEMINI_MODEL,
                    contents=prompt,
                    config=config,
                )
                self.model_name = FALLBACK_GEMINI_MODEL
            else:
                raise e

        latency = time.time() - start_time
        text = response.text or ""
        in_tokens = 0
        out_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            in_tokens = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
            out_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

        return ModelResponse(
            content=text,
            model=self.model_name,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            latency_sec=latency,
            provider="google-genai",
        )


class OllamaProvider(BaseLLMProvider):
    """Local inference via Ollama (Gemma, Llama, etc.)."""

    def __init__(self, model_name: str = "gemma:27b", base_url: str = OLLAMA_BASE_URL):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> ModelResponse:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )

        start_time = time.time()
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Failed to connect to Ollama at {self.base_url}. Is Ollama running? Error: {e}"
            )

        latency = time.time() - start_time
        return ModelResponse(
            content=res_json.get("response", ""),
            model=self.model_name,
            input_tokens=res_json.get("prompt_eval_count", 0),
            output_tokens=res_json.get("eval_count", 0),
            latency_sec=latency,
            provider="ollama"
        )


class MockProvider(BaseLLMProvider):
    """Deterministic mock provider for offline testing and automated verification."""

    def __init__(self, model_name: str = "mock-gemma-3"):
        self.model_name = model_name

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1500,
    ) -> ModelResponse:
        start_time = time.time()
        q_lower = prompt.lower()

        if "donsu" in q_lower or "give" in q_lower:
            reply = (
                "### Analysis of 'donsu'\n"
                "According to [LOD: donsu (Prim)], the predicate represents the giving relationship.\n\n"
                "**Argument Slots**:\n"
                "- **x1 (Subject/Giver)**: Donor / giver\n"
                "- **x2 (Patient/Theme)**: Gift / present / donation (`nu donsu`)\n"
                "- **x3 (Recipient/Destination)**: Recipient / receiver (`fu donsu`)\n\n"
                "**Zero-Ambiguity Syntax Example**:\n"
                "`La Far pa donsu beu ne kangi dio la Djein.`\n"
                "Here, the case tag `beu` marks slot x2 (puppy) and `dio` marks slot x3 (Jane).\n"
                "Even if word order changes (`La Far pa donsu dio la Djein, beu ne kangi`), the parse tree is identical with zero ambiguity."
            )
        elif "pretty little girls" in q_lower:
            reply = (
                "### Syntactic Ambiguity: 'Pretty little girls\' school'\n\n"
                "#### 1. English Ambiguity (5 Valid Parses)\n"
                "In English, modifiers stack ambiguously without grouping markers:\n"
                "- **Parse 1**: `[[[Pretty little] girls'] school]` — a school for girls who are unusually small.\n"
                "- **Parse 2**: `[[Pretty [little girls']] school]` — a school for little girls that is attractive.\n"
                "- **Parse 3**: `[Pretty [little [girls' school]]]` — a little school for girls that is attractive.\n"
                "- **Parse 4**: `[[[Pretty] [little] girls'] school]` — girl-students who are both pretty and small.\n"
                "- **Parse 5**: `[[Pretty little] [girls' school]]` — an attractive, small institution for girls.\n\n"
                "#### 2. Loglan Unambiguous Structure\n"
                "In Loglan, grouping particles (`ge`, `ci`, `ke...gu`) enforce strict parenthesization:\n"
                "- `le bilti cmalo nirli ckela` = left-to-right default grouping `(((bilti cmalo) nirli) ckela)`.\n"
                "- `le bilti ge cmalo nirli ckela` = `(bilti (cmalo (nirli ckela)))`.\n"
                "Each distinct meaning requires a distinct phonetic particle. Zero syntactic ambiguity!"
            )
        else:
            reply = (
                "### Loglan Grammatical Breakdown\n"
                f"Based on the provided LOD context, Loglan constructs unambiguous predicates using fixed slot ordering "
                f"and grouping operators. Every grammatical sentence resolves to exactly ONE parse tree.\n\n"
                "[LOD: Verified via export.db] | [Reference: Easy Loglan Introduction]"
            )

        latency = time.time() - start_time
        return ModelResponse(
            content=reply,
            model=self.model_name,
            input_tokens=len(prompt.split()),
            output_tokens=len(reply.split()),
            latency_sec=latency,
            provider="mock"
        )


def get_model_provider(
    model_name: Optional[str] = None,
    provider: str = "auto",
    mock: bool = False
) -> BaseLLMProvider:
    """Factory to instantiate the appropriate provider."""
    if mock:
        return MockProvider(model_name or "mock-gemma")

    target_model = model_name or DEFAULT_MODEL

    if provider == "ollama" or target_model.startswith("ollama/"):
        clean_model = target_model.replace("ollama/", "")
        return OllamaProvider(model_name=clean_model)

    if provider == "google" or provider == "auto":
        if GEMINI_API_KEY:
            try:
                return GoogleGenAIProvider(model_name=target_model)
            except Exception as e:
                print(f"[Notice] Could not initialize GoogleGenAIProvider: {e}")
        # Fall back to mock if no keys and auto
        if provider == "auto":
            print("[Notice] No GEMINI_API_KEY detected. Using MockProvider for deterministic execution.")
            return MockProvider(model_name=f"mock-{target_model}")

    raise ValueError(f"Unknown or unconfigured provider '{provider}' for model '{target_model}'")
