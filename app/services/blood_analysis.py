"""
Blood report AI analysis using LLM with schema-guaranteed JSON parsing.
"""

import json
import logging
from datetime import date
from typing import Any, Dict

from app.services.llm import create_llm_provider

logger = logging.getLogger(__name__)

BLOOD_ANALYSIS_SYSTEM_PROMPT = """You are a clinical laboratory report analyzer.
Extract all biomarker values from the provided blood report text.
Return ONLY valid JSON with this structure:
{
  "biomarkers": {
    "<marker_name>": {"value": <number_or_string>, "unit": "<unit>", "reference_range": "<range>", "status": "normal|low|high|critical"}
  },
  "abnormal_findings": ["<description>"],
  "summary": "<brief clinical summary>"
}
Identify deficiencies, abnormal values, and structural health concerns."""


async def analyze_blood_report_text(report_text: str) -> Dict[str, Any]:
    """
    Send extracted report text to LLM and parse structured biomarker JSON.

    Args:
        report_text: OCR/parsed plain text from a blood report document.

    Returns:
        Parsed analysis dict with biomarkers, abnormal findings, and summary.
    """
    llm = create_llm_provider()
    messages = [
        {"role": "system", "content": BLOOD_ANALYSIS_SYSTEM_PROMPT},
        {"role": "user", "content": f"Analyze this blood report:\n\n{report_text}"},
    ]

    raw = ""
    try:
        raw = await llm.complete(messages, json_mode=True)
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON blood analysis; wrapping raw response")
        return {
            "biomarkers": {},
            "abnormal_findings": [],
            "summary": raw or "Analysis unavailable",
        }
    except Exception as exc:
        logger.error("Blood report analysis failed: %s", exc)
        return {
            "biomarkers": {},
            "abnormal_findings": [],
            "summary": f"Analysis failed: {exc}",
        }
