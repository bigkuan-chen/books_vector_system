import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.candidate_builder import Candidate
from app.config import LLM_API_BASE, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_TIMEOUT_SECONDS
from app.schemas import LlmRerankResponse


SYSTEM_PROMPT = """You are a book search reranker.
Select only candidates that are semantically relevant to the user's query.
Return JSON only. Do not invent candidate IDs or ISBNs.
The ISBN in the final API response will always be taken from Qdrant payload, not from you.
Score each selected item from 0 to 1 and keep each reason under 100 characters."""


def is_configured() -> bool:
    return bool(LLM_API_BASE and LLM_API_KEY and LLM_MODEL)


def _endpoint() -> str:
    return f"{LLM_API_BASE.rstrip('/')}/chat/completions"


def rerank_candidates(query: str, candidates: list[Candidate], llm_min_score: float) -> LlmRerankResponse:
    if not is_configured():
        raise RuntimeError("LLM is not configured")

    candidates_json = json.dumps([candidate.for_llm() for candidate in candidates], ensure_ascii=False)
    user_prompt = (
        "User query:\n"
        f"{query}\n\n"
        f"Minimum score: {llm_min_score}\n\n"
        "Candidates:\n"
        f"{candidates_json}\n\n"
        'Return exactly this JSON shape: {"selected":[{"candidate_id":"C01","score":0.92,"reason":"short reason"}]}'
    )
    payload = {
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = Request(
        _endpoint(),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=LLM_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM request failed: HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc

    content = data["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return LlmRerankResponse.model_validate(parsed)
