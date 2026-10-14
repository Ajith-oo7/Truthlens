from __future__ import annotations

import json
import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger("truthlens.llm")

GEMINI_FALLBACKS = (
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
)


class LLMClient:
    _resolved_model: str | None = None

    def generate_json(self, system: str, user: str, fallback: dict[str, Any]) -> dict[str, Any]:
        settings = get_settings()
        if not settings.has_gemini:
            return fallback
        messages = [
            {"role": "system", "content": system + "\nReturn valid JSON only."},
            {"role": "user", "content": user},
        ]
        try:
            message = self._invoke(messages, temperature=0.1)
            text = message.content if isinstance(message.content, str) else str(message.content)
            text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception as exc:
            logger.warning("Gemini JSON generation failed, using fallback: %s", exc)
        return fallback

    def ocr_image(self, image_bytes: bytes, mime: str = "image/png") -> str:
        settings = get_settings()
        if not settings.has_gemini:
            return ""
        try:
            from langchain_core.messages import HumanMessage

            message = self._invoke(
                [
                    HumanMessage(
                        content=[
                            {
                                "type": "text",
                                "text": "Extract all visible claim text from this social/news screenshot. Return plain text only.",
                            },
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{_b64(image_bytes)}"}},
                        ]
                    )
                ],
                temperature=0,
            )
            return message.content if isinstance(message.content, str) else str(message.content)
        except Exception as exc:
            logger.warning("Gemini OCR failed: %s", exc)
            return ""

    def _invoke(self, messages: list[Any], temperature: float):
        from langchain_google_genai import ChatGoogleGenerativeAI

        settings = get_settings()
        last_error: Exception | None = None
        for name in self._model_names():
            try:
                model = ChatGoogleGenerativeAI(
                    model=name,
                    google_api_key=settings.gemini_api_key,
                    temperature=temperature,
                )
                result = model.invoke(messages)
                LLMClient._resolved_model = name
                if name != settings.gemini_model:
                    logger.info("Using Gemini model %s", name)
                return result
            except Exception as exc:
                last_error = exc
                if not _model_unavailable(exc):
                    raise
                logger.warning("Gemini model %s unavailable: %s", name, exc)
                LLMClient._resolved_model = None
        raise last_error or RuntimeError("No Gemini model available")

    def _model_names(self) -> list[str]:
        if self._resolved_model:
            return [self._resolved_model]
        settings = get_settings()
        names: list[str] = []
        for name in (settings.gemini_model, *GEMINI_FALLBACKS):
            if name and name not in names:
                names.append(name)
        return names


def _model_unavailable(exc: Exception) -> bool:
    text = str(exc).lower()
    return "no longer available" in text or "not found" in text or "404" in text


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


llm = LLMClient()
