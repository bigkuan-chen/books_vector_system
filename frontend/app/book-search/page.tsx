"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { FileJson, Search, Settings2, X } from "lucide-react";
import { AppHeader } from "../../components/AppHeader";

const API_URL = process.env.NEXT_PUBLIC_BOOK_SEARCH_API_URL ?? "http://localhost:8001/api/books/search";
const API_KEY = process.env.NEXT_PUBLIC_BOOK_QUERY_API_KEY ?? "";
const DEFAULT_API_TIMEOUT = process.env.NEXT_PUBLIC_API_TIMEOUT_SECONDS ?? "90";
const DEFAULT_TOP_K = process.env.NEXT_PUBLIC_DEFAULT_TOP_K ?? "10";
const DEFAULT_CANDIDATE_LIMIT = process.env.NEXT_PUBLIC_DEFAULT_CANDIDATE_LIMIT ?? "30";
const DEFAULT_SCORE_THRESHOLD = process.env.NEXT_PUBLIC_DEFAULT_SCORE_THRESHOLD ?? "";
const DEFAULT_LLM_MIN_SCORE = process.env.NEXT_PUBLIC_DEFAULT_LLM_MIN_SCORE ?? "0.6";

const DEFAULT_SYSTEM_PROMPT = `You are a book relevance evaluator, not a recommendation system.

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
- no candidate_id is missing or duplicated`;


type SearchResponse = {
  request_id?: string | null;
  query?: string | null;
  count?: number;
  isbns?: string[];
  results?: Array<Record<string, unknown>>;
  metadata?: {
    qdrant_candidates?: number;
    llm_filtered_candidates?: number;
    returned_results?: number;
    llm_rerank_used?: boolean;
    elapsed_ms?: number;
    fallback_reason?: string | null;
    vector_elapsed_ms?: number | null;
    llm_elapsed_ms?: number | null;
    llm_debug?: {
      system_prompt?: string | null;
      input_candidates?: Array<Record<string, unknown>> | null;
      raw_response?: string | null;
      parsed_response?: Record<string, unknown> | null;
    } | null;
  };
  [key: string]: unknown;
};

type Filters = {
  language?: string;
  publisher?: string;
  subjects?: string[];
  publish_year_from?: number;
  publish_year_to?: number;
};

export default function BookSearchPage() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(DEFAULT_TOP_K);
  const [candidateLimit, setCandidateLimit] = useState(DEFAULT_CANDIDATE_LIMIT);
  const [scoreThreshold, setScoreThreshold] = useState(DEFAULT_SCORE_THRESHOLD);
  const [llmMinScore, setLlmMinScore] = useState(DEFAULT_LLM_MIN_SCORE);
  const [useLlm, setUseLlm] = useState(true);
  const [includeDetails, setIncludeDetails] = useState(true);
  const [language, setLanguage] = useState("");
  const [publisher, setPublisher] = useState("");
  const [subjects, setSubjects] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");
  const [status, setStatus] = useState("狀態：尚未操作");
  const [error, setError] = useState("");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [apiTimeout, setApiTimeout] = useState(DEFAULT_API_TIMEOUT);
  const [selectedIsbn, setSelectedIsbn] = useState<string | null>(null);
  const [systemPrompt, setSystemPrompt] = useState(DEFAULT_SYSTEM_PROMPT);
  const [debugTab, setDebugTab] = useState<"system" | "candidates" | "raw" | "parsed">("system");

  function nextStatus(message: string) {
    setStatus(`狀態：${message}`);
  }

  function numberOrNull(value: string) {
    const trimmed = value.trim();
    return trimmed === "" ? null : Number(trimmed);
  }

  function buildPayload() {
    const parsedSubjects = subjects
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

    const filters: Filters = {};
    const from = numberOrNull(yearFrom);
    const to = numberOrNull(yearTo);
    if (language) filters.language = language;
    if (publisher.trim()) filters.publisher = publisher.trim();
    if (parsedSubjects.length) filters.subjects = parsedSubjects;
    if (from !== null) filters.publish_year_from = from;
    if (to !== null) filters.publish_year_to = to;

    return {
      query: query.trim(),
      top_k: Number(topK || 10),
      candidate_limit: Number(candidateLimit || 30),
      score_threshold: numberOrNull(scoreThreshold),
      llm_min_score: Number(llmMinScore || 0.6),
      use_llm_rerank: useLlm,
      system_prompt: useLlm ? systemPrompt : null,
      include_details: includeDetails,
      api_timeout_seconds: numberOrNull(apiTimeout),
      ...(Object.keys(filters).length ? { filters } : {}),
    };
  }

  function validatePayload(payload: ReturnType<typeof buildPayload>) {
    if (!payload.query) return "請輸入查詢文字";
    if (payload.query.length > 2000) return "查詢文字不可超過 2000 個字元";
    if (payload.candidate_limit < payload.top_k) return "候選數量不可小於 Top K";
    const filters = payload.filters;
    if (filters?.publish_year_from !== undefined && filters?.publish_year_to !== undefined) {
      if (filters.publish_year_to < filters.publish_year_from) return "年份迄不可小於年份起";
    }
    return "";
  }

  async function runSearch() {
    nextStatus("查詢中");
    const payload = buildPayload();
    const validationError = validatePayload(payload);
    setError(validationError);
    if (validationError) return;

    const headers: Record<string, string> = {
      Accept: "application/json",
      "Content-Type": "application/json",
    };
    if (API_KEY) headers["X-API-Key"] = API_KEY;

    setLoading(true);
    try {
      const result = await fetch(API_URL, {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      });
      const text = await result.text();
      const data = text ? JSON.parse(text) : {};
      setResponse(data);
      if (result.ok && data.isbns && data.isbns.length > 0) {
        setSelectedIsbn(data.isbns[0]);
      } else {
        setSelectedIsbn(null);
      }
      if (!result.ok) {
        setError(data.detail ? (typeof data.detail === "object" ? JSON.stringify(data.detail) : String(data.detail)) : JSON.stringify(data));
        nextStatus(`查詢失敗 HTTP ${result.status}`);
        return;
      }
      setError("");
      nextStatus("查詢完成");
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      nextStatus("查詢錯誤");
    } finally {
      setLoading(false);
    }
  }

  function clearAll() {
    setQuery("");
    setTopK(DEFAULT_TOP_K);
    setCandidateLimit(DEFAULT_CANDIDATE_LIMIT);
    setScoreThreshold(DEFAULT_SCORE_THRESHOLD);
    setLlmMinScore(DEFAULT_LLM_MIN_SCORE);
    setUseLlm(true);
    setIncludeDetails(true);
    setLanguage("");
    setPublisher("");
    setSubjects("");
    setYearFrom("");
    setYearTo("");
    setError("");
    setResponse(null);
    setSelectedIsbn(null);
    setSystemPrompt(DEFAULT_SYSTEM_PROMPT);
    setApiTimeout(DEFAULT_API_TIMEOUT);
    nextStatus("已清除");
  }

  const metadata = response?.metadata ?? {};
  const isbns = Array.isArray(response?.isbns) ? response.isbns : [];
  const results = Array.isArray(response?.results) ? (response.results as any[]) : [];
  const selectedResult = results.find((r) => r.isbn === selectedIsbn);

  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <AppHeader />

      <div className="mx-auto grid max-w-7xl gap-5 px-5 py-5 lg:grid-cols-[minmax(340px,40%)_1fr]">
        <aside className="space-y-5">
          <section className="border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <Search size={18} />
              <h2 className="text-base font-semibold">搜尋</h2>
            </div>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-slate-700">查詢文字</span>
              <textarea
                className="min-h-24 w-full resize-y border border-slate-300 bg-white px-3 py-2 text-sm leading-6 outline-none focus:border-teal-700"
                maxLength={2000}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="例如：想找追尋星光的少女漫畫，或輸入 ISBN：9786264039666"
                value={query}
              />
              <span className="mt-1 flex justify-between text-xs text-slate-500">
                <span>輸入自然語言需求、書名、作者或 ISBN。</span>
                <span>{query.length}/2000</span>
              </span>
            </label>

            <div className="mt-4 grid grid-cols-2 gap-2">
              <button
                className="inline-flex h-10 items-center justify-center gap-2 bg-teal-700 px-4 text-sm font-medium text-white hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-300"
                disabled={loading}
                onClick={runSearch}
                type="button"
              >
                <Search size={16} />
                {loading ? "查詢中..." : "查詢"}
              </button>
              <button
                className="inline-flex h-10 items-center justify-center gap-2 border border-rose-300 bg-rose-50 px-4 text-sm font-semibold text-rose-800 hover:border-rose-400 hover:bg-rose-100 active:bg-rose-200"
                onClick={clearAll}
                type="button"
              >
                <X size={16} />
                清除
              </button>
            </div>
            <div className="mt-3 border border-sky-200 bg-sky-50 px-3 py-2 text-xs font-medium text-sky-800" aria-live="polite">
              {status}
            </div>
            {response && useLlm && !metadata.llm_rerank_used && (
              <div className="mt-3 border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800 rounded-sm">
                ⚠️ LLM 重排未生效 (原因: {String(metadata.fallback_reason || "未知")})，已自動降級為純向量搜尋。
              </div>
            )}
            {response && !useLlm && (
              <div className="mt-3 border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800 rounded-sm">
                ⚠️ 未啟用 LLM 重排，目前為純向量搜尋。
              </div>
            )}
            {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
          </section>

          <section className="border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <Settings2 size={18} />
              <h2 className="text-base font-semibold">參數</h2>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="分數門檻"><input className="h-10 w-full border border-slate-300 px-3 text-sm" max={1} min={0} onChange={(event) => setScoreThreshold(event.target.value)} placeholder={DEFAULT_SCORE_THRESHOLD ? `預設 ${DEFAULT_SCORE_THRESHOLD}` : "不限制"} step={0.01} type="number" value={scoreThreshold} /></Field>
              <Field label="候選數量"><input className="h-10 w-full border border-slate-300 px-3 text-sm" max={100} min={5} onChange={(event) => setCandidateLimit(event.target.value)} placeholder={`預設 ${DEFAULT_CANDIDATE_LIMIT}`} step={1} type="number" value={candidateLimit} /></Field>
              <Field label="LLM 最低分"><input className="h-10 w-full border border-slate-300 px-3 text-sm" max={1} min={0} onChange={(event) => setLlmMinScore(event.target.value)} placeholder={`預設 ${DEFAULT_LLM_MIN_SCORE}`} step={0.05} type="number" value={llmMinScore} /></Field>
              <Field label="Top K"><input className="h-10 w-full border border-slate-300 px-3 text-sm" max={50} min={1} onChange={(event) => setTopK(event.target.value)} placeholder={`預設 ${DEFAULT_TOP_K}`} step={1} type="number" value={topK} /></Field>
              <Field label="API 逾時 (秒)"><input className="h-10 w-full border border-slate-300 px-3 text-sm" max={600} min={1} onChange={(event) => setApiTimeout(event.target.value)} placeholder={`預設 ${DEFAULT_API_TIMEOUT}`} step={1} type="number" value={apiTimeout} /></Field>
            </div>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <label className="flex items-center justify-between gap-3 border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                <span className="font-medium text-slate-700">使用 LLM rerank</span>
                <input checked={useLlm} onChange={(event) => setUseLlm(event.target.checked)} type="checkbox" />
              </label>
              <label className="flex items-center justify-between gap-3 border border-slate-200 bg-slate-50 px-3 py-2 text-sm">
                <span className="font-medium text-slate-700">包含詳細資料</span>
                <input checked={includeDetails} onChange={(event) => setIncludeDetails(event.target.checked)} type="checkbox" />
              </label>
            </div>
            {useLlm && (
              <div className="mt-4 border-t border-slate-200 pt-4">
                <Field label="LLM 系統提示詞 (System Prompt)">
                  <textarea
                    className="min-h-[140px] w-full border border-slate-300 px-3 py-2 text-xs outline-none focus:border-teal-700 font-mono leading-relaxed bg-slate-50"
                    onChange={(event) => setSystemPrompt(event.target.value)}
                    value={systemPrompt}
                  />
                </Field>
              </div>
            )}
            <div className="mt-4 border-t border-slate-200 pt-4">
              <h3 className="mb-3 text-sm font-semibold text-slate-800">Payload 篩選</h3>
              <div className="grid gap-3">
                <Field label="語言">
                  <select className="h-10 w-full border border-slate-300 bg-white px-3 text-sm" onChange={(event) => setLanguage(event.target.value)} value={language}>
                    <option value="">不限語言</option>
                    <option value="zh-TW">zh-TW</option>
                    <option value="zh-CN">zh-CN</option>
                    <option value="en">en</option>
                    <option value="ja">ja</option>
                  </select>
                </Field>
                <Field label="出版社"><input className="h-10 w-full border border-slate-300 px-3 text-sm" maxLength={200} onChange={(event) => setPublisher(event.target.value)} value={publisher} /></Field>
                <Field label="主題"><input className="h-10 w-full border border-slate-300 px-3 text-sm" onChange={(event) => setSubjects(event.target.value)} placeholder="用逗號分隔，例如：漫畫, 藝術" value={subjects} /></Field>
                <div className="grid grid-cols-2 gap-3">
                  <Field label="年份起"><input className="h-10 w-full border border-slate-300 px-3 text-sm" max={2100} min={1000} onChange={(event) => setYearFrom(event.target.value)} placeholder="2020" step={1} type="number" value={yearFrom} /></Field>
                  <Field label="年份迄"><input className="h-10 w-full border border-slate-300 px-3 text-sm" max={2100} min={1000} onChange={(event) => setYearTo(event.target.value)} placeholder="2026" step={1} type="number" value={yearTo} /></Field>
                </div>
              </div>
            </div>
          </section>
        </aside>

        <section className="space-y-5">
          <Panel title="摘要">
            {response ? (
              <div className="space-y-4">
                {/* 核心數據網格 */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div className="border border-slate-100 bg-slate-50 p-2.5 rounded-sm">
                    <span className="block text-slate-500 font-medium mb-0.5">查詢字元</span>
                    <span className="font-semibold text-slate-900 truncate block" title={response.query || ""}>
                      {response.query || "-"}
                    </span>
                  </div>
                  <div className="border border-slate-100 bg-slate-50 p-2.5 rounded-sm">
                    <span className="block text-slate-500 font-medium mb-0.5">要求識別碼</span>
                    <span className="font-mono text-slate-600 truncate block">
                      {response.request_id || "-"}
                    </span>
                  </div>
                  <div className="border border-slate-100 bg-slate-50 p-2.5 rounded-sm">
                    <span className="block text-slate-500 font-medium mb-0.5">Qdrant 候選筆數</span>
                    <span className="text-sm font-semibold text-slate-900">
                      {Number(metadata.qdrant_candidates ?? 0)} 筆
                    </span>
                  </div>
                  <div className="border border-slate-100 bg-slate-50 p-2.5 rounded-sm">
                    <span className="block text-slate-500 font-medium mb-0.5">最終回傳筆數</span>
                    <span className="text-sm font-semibold text-teal-700">
                      {response.count ?? 0} 筆
                    </span>
                  </div>
                </div>

                {/* 耗時統計 */}
                <div className="pt-3 border-t border-slate-100">
                  <div className="flex items-baseline justify-between mb-2">
                    <h3 className="text-xs font-semibold text-slate-800">查詢耗時分析</h3>
                    <span className="text-sm font-bold text-teal-700 font-mono">
                      {metadata.elapsed_ms ?? 0} ms
                    </span>
                  </div>

                  {/* 耗時分割比例條 */}
                  {(() => {
                    const total = Number(metadata.elapsed_ms ?? 0);
                    const vec = Number(metadata.vector_elapsed_ms ?? 0);
                    const llm = metadata.llm_rerank_used ? Number(metadata.llm_elapsed_ms ?? 0) : 0;
                    const system = Math.max(0, total - vec - llm);

                    const vecPct = total > 0 ? (vec / total) * 100 : 0;
                    const llmPct = total > 0 ? (llm / total) * 100 : 0;
                    const sysPct = total > 0 ? (system / total) * 100 : 0;

                    return (
                      <div>
                        {/* 比例條 */}
                        <div className="w-full bg-slate-100 h-2.5 rounded-full overflow-hidden flex mb-3.5 shadow-inner">
                          {vecPct > 0 && (
                            <div
                              className="bg-indigo-600 h-full transition-all duration-500"
                              style={{ width: `${vecPct}%` }}
                              title={`向量檢索與處理: ${vec} ms (${vecPct.toFixed(1)}%)`}
                            />
                          )}
                          {llmPct > 0 && (
                            <div
                              className="bg-teal-500 h-full transition-all duration-500"
                              style={{ width: `${llmPct}%` }}
                              title={`LLM 重排與過濾: ${llm} ms (${llmPct.toFixed(1)}%)`}
                            />
                          )}
                          {sysPct > 0 && (
                            <div
                              className="bg-slate-400 h-full transition-all duration-500"
                              style={{ width: `${sysPct}%` }}
                              title={`系統開銷: ${system} ms (${sysPct.toFixed(1)}%)`}
                            />
                          )}
                        </div>

                        {/* 詳細指標清單 */}
                        <div className="space-y-2 text-xs">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1.5 text-slate-700">
                              <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 inline-block" />
                              <span>向量檢索與處理</span>
                            </div>
                            <span className="font-mono text-slate-600">
                              {vec} ms <span className="text-slate-400 font-normal">({vecPct.toFixed(1)}%)</span>
                            </span>
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1.5 text-slate-700">
                              <span className="w-2.5 h-2.5 rounded-full bg-teal-500 inline-block" />
                              <span>LLM 重排與過濾</span>
                            </div>
                            <span className="font-mono text-slate-600">
                              {metadata.llm_rerank_used ? (
                                <>
                                  {llm} ms <span className="text-slate-400 font-normal">({llmPct.toFixed(1)}%)</span>
                                </>
                              ) : (
                                <span className="text-slate-400 italic">未啟用/降級</span>
                              )}
                            </span>
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1.5 text-slate-700">
                              <span className="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block" />
                              <span>系統其他開銷</span>
                            </div>
                            <span className="font-mono text-slate-600">
                              {system} ms <span className="text-slate-400 font-normal">({sysPct.toFixed(1)}%)</span>
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500 py-2">尚未查詢。</p>
            )}
          </Panel>
          <Panel title="查詢結果 (請點選書籍)">
            <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-1">
              {isbns.length ? (
                isbns.map((isbn, index) => {
                  const matchedResult = results.find((r: any) => r.isbn === isbn) as any;
                  const title = matchedResult?.title || "未知書名";
                  const isSelected = selectedIsbn === isbn;
                  return (
                    <button
                      key={isbn}
                      onClick={() => setSelectedIsbn(isbn)}
                      className={`w-full flex items-center justify-between gap-3 border p-3 text-left transition-all rounded-sm ${
                        isSelected
                          ? "border-teal-600 bg-teal-50 text-teal-950 shadow-sm font-medium"
                          : "border-slate-200 bg-white hover:bg-slate-50 text-slate-800"
                      }`}
                      type="button"
                    >
                      <span className="text-sm font-semibold truncate pr-2">
                        {index + 1}. {title}
                      </span>
                      <span className="text-xs font-mono text-slate-500 whitespace-nowrap">
                        {isbn}
                      </span>
                    </button>
                  );
                })
              ) : (
                <p className="text-sm text-slate-500 py-2">尚無查詢結果。</p>
              )}
            </div>

          </Panel>
          <Panel title="詳細結果">
            {selectedResult ? (
              <div className="space-y-4 text-sm text-slate-800 bg-white border border-slate-100 p-4 rounded-sm">
                <div className="grid grid-cols-[100px_1fr] gap-x-2 gap-y-2.5">
                  <span className="font-semibold text-slate-500">書名：</span>
                  <span className="font-semibold text-slate-955">{selectedResult.title || "-"}</span>

                  <span className="font-semibold text-slate-500">ISBN：</span>
                  <span className="font-mono text-slate-950">{selectedResult.isbn || "-"}</span>

                  <span className="font-semibold text-slate-500">作者：</span>
                  <span>
                    {Array.isArray(selectedResult.authors)
                      ? selectedResult.authors.join("、")
                      : selectedResult.authors || "-"}
                  </span>

                  <span className="font-semibold text-slate-500">出版社：</span>
                  <span>{selectedResult.publisher || "-"}</span>

                  <span className="font-semibold text-slate-500">出版日期：</span>
                  <span>{selectedResult.publish_date || "-"}</span>

                  <span className="font-semibold text-slate-500">主題分類：</span>
                  <span>
                    {Array.isArray(selectedResult.subjects)
                      ? selectedResult.subjects.join("、")
                      : selectedResult.subjects || "-"}
                  </span>

                  <span className="font-semibold text-slate-500">向量分數：</span>
                  <span className="font-mono text-slate-700">{selectedResult.vector_score ?? "-"}</span>

                  <span className="font-semibold text-slate-500">LLM 分數：</span>
                  <span className="font-mono text-slate-700">
                    {selectedResult.llm_score !== undefined && selectedResult.llm_score !== null
                      ? selectedResult.llm_score
                      : "未啟用/降級"}
                  </span>

                  <span className="font-semibold text-slate-500">最終分數：</span>
                  <span className="font-mono font-semibold text-teal-700">{selectedResult.final_score ?? "-"}</span>

                  {selectedResult.reason && (
                    <>
                      <span className="font-semibold text-slate-500">篩選原因：</span>
                      <span className="text-teal-900 bg-teal-50 px-2 py-0.5 rounded text-xs inline-block w-fit">
                        {selectedResult.reason}
                      </span>
                    </>
                  )}
                </div>

                {selectedResult.description && (
                  <div className="mt-4 pt-3 border-t border-slate-100">
                    <span className="font-semibold text-slate-500 block mb-1.5">內容簡介：</span>
                    <p className="text-xs leading-5 text-slate-600 bg-slate-50 p-2.5 rounded border border-slate-100 max-h-[160px] overflow-y-auto">
                      {selectedResult.description}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-slate-500 py-2">請先在上方「查詢結果」中點選書籍以查看詳細資料。</p>
            )}
          </Panel>
          <Panel title="書籍資訊" icon={<FileJson size={18} />}>
            {selectedResult && selectedResult.payload ? (
              <pre className="max-h-[350px] overflow-auto border border-slate-200 bg-slate-950 p-4 text-xs leading-5 text-slate-100 font-mono">
                {JSON.stringify(selectedResult.payload, null, 2)}
              </pre>
            ) : (
              <pre className="max-h-[350px] overflow-auto border border-slate-200 bg-slate-950 p-4 text-xs leading-5 text-slate-100 font-mono">
                {"尚未選擇書籍或該書籍無原始資料。"}
              </pre>
            )}
          </Panel>

          {response?.metadata?.llm_debug ? (
            <Panel title="LLM 評估日誌" icon={<Settings2 size={18} />}>
              <div className="flex border-b border-slate-200 mb-3 overflow-x-auto whitespace-nowrap">
                {(["system", "candidates", "raw", "parsed"] as const).map((tab) => {
                  const labels: Record<string, string> = {
                    system: "System Prompt",
                    candidates: "Input Candidates",
                    raw: "LLM Raw Response",
                    parsed: "LLM Parsed Response",
                  };
                  const isActive = debugTab === tab;
                  return (
                    <button
                      key={tab}
                      onClick={() => setDebugTab(tab)}
                      className={`px-3 py-2 text-xs font-medium border-b-2 -mb-[2px] transition-all outline-none ${
                        isActive
                          ? "border-teal-600 text-teal-700 font-semibold"
                          : "border-transparent text-slate-500 hover:text-slate-800"
                      }`}
                      type="button"
                    >
                      {labels[tab]}
                    </button>
                  );
                })}
              </div>
              <div className="bg-slate-950 text-slate-100 p-4 font-mono text-xs max-h-[400px] overflow-auto border border-slate-200 rounded-sm">
                {debugTab === "system" && (
                  <pre className="whitespace-pre-wrap leading-5">
                    {response.metadata.llm_debug.system_prompt || "無 System Prompt"}
                  </pre>
                )}
                {debugTab === "candidates" && (
                  <pre className="leading-5">
                    {response.metadata.llm_debug.input_candidates
                      ? JSON.stringify(response.metadata.llm_debug.input_candidates, null, 2)
                      : "無輸入候選資料"}
                  </pre>
                )}
                {debugTab === "raw" && (
                  <pre className="whitespace-pre-wrap leading-5">
                    {response.metadata.llm_debug.raw_response || "無原始回覆"}
                  </pre>
                )}
                {debugTab === "parsed" && (
                  <pre className="leading-5">
                    {response.metadata.llm_debug.parsed_response
                      ? JSON.stringify(response.metadata.llm_debug.parsed_response, null, 2)
                      : "無解析後資料"}
                  </pre>
                )}
              </div>
            </Panel>
          ) : null}
        </section>
      </div>
    </main>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-slate-500">{label}</span>
      {children}
    </label>
  );
}

function Panel({ title, icon, children }: { title: string; icon?: ReactNode; children: ReactNode }) {
  return (
    <section className="border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-center gap-2">
        {icon}
        <h2 className="text-base font-semibold">{title}</h2>
      </div>
      {children}
    </section>
  );
}
