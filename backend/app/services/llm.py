from __future__ import annotations

import json
import logging
from typing import Any

from app.config import get_settings

logger = logging.getLogger("truthlens.llm")


class LLMClient:
    def generate_json(self, system: str, user: str, fallback: dict[str, Any]) -> dict[str, Any]:
        settings = get_settings()
        if not settings.has_gemini:
            return fallback
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            model = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.gemini_api_key,
                temperature=0.1,
            )
            message = model.invoke(
                [
                    {"role": "system", "content": system + "\nReturn valid JSON only."},
                    {"role": "user", "content": user},
                ]
            )
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
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage

            model = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.gemini_api_key,
                temperature=0,
            )
            message = model.invoke(
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
                ]
            )
            return message.content if isinstance(message.content, str) else str(message.content)
        except Exception as exc:
            logger.warning("Gemini OCR failed: %s", exc)
            return ""


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


llm = LLMClient()
