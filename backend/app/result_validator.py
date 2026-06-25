from app.candidate_builder import Candidate
from app.schemas import BookSearchResult, LlmRerankResponse


def clamp_score(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def vector_only_results(candidates: list[Candidate], top_k: int) -> list[BookSearchResult]:
    sorted_candidates = sorted(candidates, key=lambda item: item.vector_score, reverse=True)
    return [
        BookSearchResult(
            isbn=candidate.isbn,
            title=candidate.title,
            authors=candidate.authors,
            publisher=candidate.publisher,
            publish_date=candidate.publish_date,
            language=candidate.language,
            subjects=candidate.subjects,
            description=candidate.description,
            vector_score=round(candidate.vector_score, 6),
            final_score=round(clamp_score(candidate.vector_score), 6),
            payload=candidate.payload,
        )
        for candidate in sorted_candidates[:top_k]
    ]


def reranked_results(
    candidates: list[Candidate],
    llm_response: LlmRerankResponse,
    llm_min_score: float,
    top_k: int,
) -> list[BookSearchResult]:
    by_id = {candidate.candidate_id: candidate for candidate in candidates}
    best_by_id: dict[str, tuple[float, str]] = {}
    for item in llm_response.selected:
        if item.candidate_id not in by_id:
            continue
        score = clamp_score(item.score)
        if score < llm_min_score:
            continue
        current = best_by_id.get(item.candidate_id)
        if current is None or score > current[0]:
            best_by_id[item.candidate_id] = (score, item.reason)

    results: list[BookSearchResult] = []
    for candidate_id, (llm_score, reason) in best_by_id.items():
        candidate = by_id[candidate_id]
        vector_score = clamp_score(candidate.vector_score)
        final_score = vector_score * 0.35 + llm_score * 0.65
        results.append(
            BookSearchResult(
                isbn=candidate.isbn,
                title=candidate.title,
                authors=candidate.authors,
                publisher=candidate.publisher,
                publish_date=candidate.publish_date,
                language=candidate.language,
                subjects=candidate.subjects,
                description=candidate.description,
                vector_score=round(candidate.vector_score, 6),
                llm_score=round(llm_score, 6),
                final_score=round(final_score, 6),
                reason=reason,
                payload=candidate.payload,
            )
        )

    results.sort(key=lambda item: (item.final_score, item.vector_score), reverse=True)
    deduped: list[BookSearchResult] = []
    seen_isbns: set[str] = set()
    for result in results:
        if result.isbn in seen_isbns:
            continue
        seen_isbns.add(result.isbn)
        deduped.append(result)
        if len(deduped) >= top_k:
            break
    return deduped
