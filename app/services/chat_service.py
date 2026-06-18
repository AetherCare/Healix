"""
RAG-augmented health chatbot with streaming SSE support.
"""

import json
from typing import Any, AsyncGenerator, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medication import Medication
from app.models.wearable_data import WearableData
from app.services.llm import create_llm_provider
from app.services.vector_store import similarity_search

CHAT_SYSTEM_TEMPLATE = """You are MediVault AI, a personal health assistant with access to the user's health vault.
Use the provided context from their medical history, medications, and wearable data to give accurate, helpful responses.
Always recommend consulting a healthcare professional for medical decisions.
Never diagnose conditions definitively.

--- HEALTH MEMORY CONTEXT ---
{rag_context}

--- CURRENT MEDICATIONS ---
{medications}

--- RECENT WEARABLE TELEMETRY ---
{wearables}
"""


async def _build_health_context(
    db: AsyncSession,
    user_id: UUID,
    query: str,
) -> str:
    """Assemble RAG context, medications, and wearable data for the system prompt."""
    rag_results = similarity_search(user_id, query, top_k=5)
    rag_context = "\n".join(
        f"[{r['metadata'].get('source_type', 'unknown')}] {r['document']}"
        for r in rag_results
    ) or "No relevant health memory found."

    med_result = await db.execute(
        select(Medication).where(Medication.user_id == user_id).limit(10)
    )
    medications = med_result.scalars().all()
    med_text = "\n".join(
        f"- {m.medication_name} {m.dosage} ({m.frequency})"
        for m in medications
    ) or "No active medications."

    wearable_result = await db.execute(
        select(WearableData)
        .where(WearableData.user_id == user_id)
        .order_by(WearableData.timestamp.desc())
        .limit(3)
    )
    wearables = wearable_result.scalars().all()
    wearable_text = "\n".join(
        f"- HR: {w.heart_rate}, SpO2: {w.oxygen}, Activity: {w.activity}"
        for w in wearables
    ) or "No recent wearable data."

    return CHAT_SYSTEM_TEMPLATE.format(
        rag_context=rag_context,
        medications=med_text,
        wearables=wearable_text,
    )


async def stream_health_chat(
    db: AsyncSession,
    user_id: UUID,
    message: str,
) -> AsyncGenerator[str, None]:
    """
    Stream SSE-formatted chat responses with RAG context injection.

    Yields:
        SSE data lines in ``data: {...}\\n\\n`` format.
    """
    system_prompt = await _build_health_context(db, user_id, message)
    llm = create_llm_provider()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    yield f"data: {json.dumps({'type': 'start'})}\n\n"

    async for token in llm.stream(messages):
        payload = json.dumps({"type": "token", "content": token})
        yield f"data: {payload}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"
