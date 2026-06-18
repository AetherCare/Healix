"""
ChromaDB vector store orchestration for health memory RAG engine.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_collection_cache: Dict[str, Any] = {}
_client_cache: Optional[Any] = None
_embedder_cache: Optional[Any] = None


def _get_chroma_client():
    """Lazy-initialize persistent ChromaDB client."""
    global _client_cache
    if _client_cache is None:
        import chromadb

        settings = get_settings()
        _client_cache = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _client_cache


def _get_embedder():
    """Lazy-initialize HuggingFace sentence-transformers embedder."""
    global _embedder_cache
    if _embedder_cache is None:
        from sentence_transformers import SentenceTransformer

        settings = get_settings()
        _embedder_cache = SentenceTransformer(settings.embedding_model)
    return _embedder_cache


def _get_user_collection(user_id: UUID):
    """Get or create a per-user ChromaDB collection."""
    collection_name = f"user_{str(user_id).replace('-', '_')}"
    if collection_name not in _collection_cache:
        client = _get_chroma_client()
        _collection_cache[collection_name] = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection_cache[collection_name]


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for embedding."""
    words = text.split()
    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks or [text]


def embed_and_store(
    user_id: UUID,
    text: str,
    source_type: str,
    source_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Chunk, embed, and persist health text into the user's ChromaDB collection.

    Returns:
        Number of chunks stored.
    """
    collection = _get_user_collection(user_id)
    embedder = _get_embedder()
    chunks = _chunk_text(text)
    embeddings = embedder.encode(chunks).tolist()

    ids = [f"{source_id}_{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "source_type": source_type,
            "source_id": source_id,
            "chunk_index": i,
            **(metadata or {}),
        }
        for i in range(len(chunks))
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )
    return len(chunks)


def similarity_search(
    user_id: UUID,
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Perform cosine similarity search across a user's health memory vectors.

    Returns:
        List of result dicts with document, metadata, and distance score.
    """
    collection = _get_user_collection(user_id)
    embedder = _get_embedder()
    query_embedding = embedder.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    output: List[Dict[str, Any]] = []
    if results and results["documents"]:
        for i, doc in enumerate(results["documents"][0]):
            output.append({
                "document": doc,
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0.0,
                "relevance_score": 1.0 - (results["distances"][0][i] if results["distances"] else 0.0),
            })
    return output
