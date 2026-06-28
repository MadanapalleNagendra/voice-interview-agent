"""
app/services/retrieval_service.py
Retrieves relevant Q&A reference context for a given candidate answer or
interviewer question using the FAISS vector store.
"""

from app.core.logger import get_logger
from app.vectorstore import faiss_store

logger = get_logger(__name__)


async def retrieve_context(query: str, top_k: int = 3) -> list[dict]:
    """
    Semantic search: given the candidate's answer (or the current question),
    return the top-k most relevant Q&A records as grounding context.
    """
    results = await faiss_store.search(query, top_k=top_k)
    logger.debug(f"Retrieved {len(results)} context records for query '{query[:60]}…'")
    return results


async def get_question_by_id(question_id: int) -> dict | None:
    return await faiss_store.get_by_id(question_id)


def get_all_questions() -> list[dict]:
    return faiss_store.get_all_questions()
