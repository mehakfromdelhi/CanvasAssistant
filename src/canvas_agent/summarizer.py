from __future__ import annotations

import re
from collections import Counter

from google import genai
from openai import OpenAI

from .config import AppConfig
from .utils import truncate_text


class Summarizer:
    def __init__(self, config: AppConfig) -> None:
        self.gemini_client = genai.Client(api_key=config.gemini_api_key) if config.gemini_api_key else None
        self.gemini_model = config.gemini_model
        self.openai_client = OpenAI(api_key=config.openai_api_key) if config.openai_api_key else None
        self.openai_model = config.openai_model

    def summarize(self, title: str, text: str) -> str:
        excerpt = truncate_text(text, 12000)
        prompt = (
            "You are an academic assistant. Summarize the reading for an MBA student.\n"
            "Return:\n"
            "1. A 3-5 sentence overview\n"
            "2. 5 key takeaways\n"
            "3. 3 discussion questions or class angles\n\n"
            f"Reading title: {title}\n\n"
            f"Reading text:\n{excerpt}"
        )
        try:
            if self.gemini_client:
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt,
                )
                if response.text:
                    return response.text.strip()
        except Exception as exc:
            gemini_error = str(exc)
        else:
            gemini_error = "Gemini returned an empty response."

        try:
            if self.openai_client:
                response = self.openai_client.responses.create(
                    model=self.openai_model,
                    input=prompt,
                )
                return response.output_text.strip()
        except Exception as exc:
            openai_error = str(exc)
        else:
            openai_error = "OpenAI returned an empty response."

        return self._fallback_summary(
            title,
            text,
            f"Gemini: {gemini_error} | OpenAI: {openai_error}",
        )

    def _fallback_summary(self, title: str, text: str, error_text: str) -> str:
        sentences = self._split_sentences(text)
        overview = " ".join(sentences[:4]) if sentences else "No readable text was extracted."
        takeaways = sentences[:5] or ["The reading content was captured, but AI summarization was unavailable."]
        keywords = self._top_keywords(text, limit=3)

        questions = [
            f"How does '{title}' connect to the main venture capital decisions discussed in class?",
            f"What assumptions in this reading deserve more scrutiny or debate?",
            f"How would you apply the ideas in this reading to a real investment or operating situation?",
        ]
        if keywords:
            questions[1] = f"How do the ideas around {', '.join(keywords)} shape the argument in this reading?"

        takeaway_lines = "\n".join(f"- {line}" for line in takeaways)
        question_lines = "\n".join(f"- {line}" for line in questions)
        return (
            "## Overview\n"
            f"{overview}\n\n"
            "## Key Takeaways\n"
            f"{takeaway_lines}\n\n"
            "## Discussion Questions\n"
            f"{question_lines}\n\n"
            "_Fallback summary used because the AI summary providers were unavailable during this run._\n"
            f"_Reason: {truncate_text(error_text, 180)}_"
        )

    def _split_sentences(self, text: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []
        parts = re.split(r"(?<=[.!?])\s+", normalized)
        return [part.strip() for part in parts if len(part.strip()) > 30][:12]

    def _top_keywords(self, text: str, limit: int) -> list[str]:
        stopwords = {
            "the",
            "and",
            "that",
            "with",
            "from",
            "this",
            "have",
            "will",
            "their",
            "about",
            "into",
            "there",
            "which",
            "these",
            "they",
            "them",
            "your",
            "more",
            "than",
            "been",
            "were",
            "what",
            "when",
            "where",
            "while",
            "would",
            "could",
            "should",
            "because",
            "each",
            "such",
            "also",
            "only",
        }
        words = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        counts = Counter(word for word in words if word not in stopwords)
        return [word for word, _ in counts.most_common(limit)]
