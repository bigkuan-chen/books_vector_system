import time
import uuid
import re

from app.candidate_builder import build_candidates
from app.embedding import build_query_embedding_text, embed_texts
from app.llm_reranker import rerank_candidates
from app.qdrant_service import find_books_by_isbn, search_books
from app.query_preprocessor import normalize_query
from app.result_validator import reranked_results, vector_only_results
from app.schemas import BookSearchRequest, BookSearchResponse, SearchMetadata


def search(request: BookSearchRequest) -> BookSearchResponse:
    started = time.perf_counter()
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    normalized_query = normalize_query(request.query)

    vector_started = time.perf_counter()
    isbn_query = re.sub(r"[-\s]", "", normalized_query)
    if re.fullmatch(r"\d{10}|\d{13}", isbn_query):
        points = find_books_by_isbn(isbn_query, request.candidate_limit)
    else:
        query_vector = embed_texts([build_query_embedding_text(normalized_query)])[0]
        points = search_books(
            query_vector=query_vector,
            limit=request.candidate_limit,
            score_threshold=request.score_threshold,
            filters=request.filters,
        )
    candidates = build_candidates(points)
    vector_elapsed_ms = int((time.perf_counter() - vector_started) * 1000)

    llm_rerank_used = False
    fallback_reason: str | None = None
    llm_elapsed_ms: int | None = None
    if request.use_llm_rerank and candidates:
        llm_started = time.perf_counter()
        try:
            llm_response = rerank_candidates(normalized_query, candidates, request.llm_min_score)
            results = reranked_results(candidates, llm_response, request.llm_min_score, request.top_k)
            llm_elapsed_ms = int((time.perf_counter() - llm_started) * 1000)
            llm_rerank_used = True
            if not results:
                fallback_reason = "LLM_NO_SELECTED_CANDIDATES"
                results = vector_only_results(candidates, request.top_k)
        except Exception as exc:
            llm_elapsed_ms = int((time.perf_counter() - llm_started) * 1000)
            import traceback
            traceback.print_exc()
            fallback_reason = exc.__class__.__name__
            results = vector_only_results(candidates, request.top_k)
    else:
        if request.use_llm_rerank and not candidates:
            fallback_reason = "NO_QDRANT_CANDIDATES"
        results = vector_only_results(candidates, request.top_k)

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    isbns = [result.isbn for result in results]
    return BookSearchResponse(
        request_id=request_id,
        query=normalized_query,
        count=len(isbns),
        isbns=isbns,
        results=results if request.include_details else None,
        metadata=SearchMetadata(
            qdrant_candidates=len(candidates),
            llm_filtered_candidates=len(results) if llm_rerank_used else 0,
            returned_results=len(results),
            llm_rerank_used=llm_rerank_used,
            fallback_reason=fallback_reason,
            elapsed_ms=elapsed_ms,
            vector_elapsed_ms=vector_elapsed_ms,
            llm_elapsed_ms=llm_elapsed_ms,
        ),
    )
