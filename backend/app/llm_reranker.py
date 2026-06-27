import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.candidate_builder import Candidate
from app.config import LLM_API_BASE, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT_SECONDS, API_TIMEOUT_SECONDS
from app.schemas import LlmRerankResponse, LlmDebugInfo


SYSTEM_PROMPT = """You are a book relevance evaluator, not a recommendation system.

Your task is to evaluate EVERY candidate book independently against the user's query.

STRICT REQUIREMENTS:

1. You MUST return exactly one evaluation for every input candidate.
2. The number of objects in "evaluations" MUST equal the provided candidate_count.
3. Every input candidate_id MUST appear exactly once in the output.
4. Do not omit candidates, even when their relevance score is 0.
5. Do not return only the best, relevant, or recommended books.
6. Do not stop after finding several relevant books.
7. Evaluate candidates independently. One candidate's score must not affect another candidate.
8. Score semantic relevance from 0.0 to 1.0.
9. A score of 0.0 is valid and must still be returned.
10. Missing information means uncertainty, not automatic irrelevance.
11. Do not invent, modify, or normalize candidate IDs.
12. Do not invent or return ISBNs.
13. Keep each reason under 100 characters.
14. Return valid JSON only. Do not use Markdown or explanatory text.
15. Preserve the original candidate order.

Before responding, verify internally that:
- evaluations.length equals candidate_count
- every candidate_id appears exactly once
- no candidate_id is missing or duplicated"""


def is_configured() -> bool:
    return bool(LLM_API_BASE and LLM_API_KEY and LLM_MODEL)


def _endpoint() -> str:
    return f"{LLM_API_BASE.rstrip('/')}/chat/completions"


def rerank_candidates(query: str, candidates: list[Candidate], llm_min_score: float, system_prompt: str | None = None, timeout: int | None = None) -> tuple[LlmRerankResponse, LlmDebugInfo]:
    if not is_configured():
        raise RuntimeError("LLM is not configured")
    try:
        print("candidates:"+candidates.__str__())
    except Exception:
        pass
    
    candidates_json = json.dumps([candidate.for_llm() for candidate in candidates], ensure_ascii=False)
    candidate_count = len(candidates)
    user_prompt = (
        "Input:\n\n"
        "user_query:\n"
        f"{query}\n\n"
        "candidate_count:\n"
        f"{candidate_count}\n\n"
        "candidates:\n"
        f"{candidates_json}\n\n"
        "Required output format:\n\n"
        "{\n"
        f'  "candidate_count": {candidate_count},\n'
        '  "evaluations": [\n'
        '    {\n'
        '      "candidate_id": "C01",\n'
        '      "score": 0.85,\n'
        '      "reason": "Directly covers the requested topic"\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        f'The "evaluations" array MUST contain exactly {candidate_count} objects.\n'
        'Even candidates with score 0.0 MUST be included.'
    )

    active_system_prompt = system_prompt if system_prompt else SYSTEM_PROMPT
    try:
        print(active_system_prompt)
    except Exception:
        pass
    payload = {
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": active_system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = Request(
        _endpoint(),
        data=json.dumps(payload).encode("utf-8", errors="ignore"),
        headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    active_timeout = timeout if timeout is not None else API_TIMEOUT_SECONDS
    try:
        with urlopen(request, timeout=active_timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM request failed: HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc

    content = data["choices"][0]["message"]["content"]
    try:
        print("--- LLM INPUT CANDIDATES ---")
        print(candidates_json)
        print("--- LLM RAW RESPONSE ---")
        print(content)
    except Exception:
        # Prevent Windows console encoding (cp950) errors from crashing the request
        pass

    parsed = json.loads(content)
    try:
        print("--- LLM PARSED RESPONSE ---")
        print(parsed)
    except Exception:
        pass

    debug_info = LlmDebugInfo(
        system_prompt=active_system_prompt,
        input_candidates=[candidate.for_llm() for candidate in candidates],
        raw_response=content,
        parsed_response=parsed
    )

    return LlmRerankResponse.model_validate(parsed), debug_info
