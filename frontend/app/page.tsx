"use client";

import { useEffect, useMemo, useState } from "react";
import type { ChangeEvent, ReactNode } from "react";
import { CheckCircle2, Database, FileJson, Play, RefreshCw, Upload, XCircle } from "lucide-react";
import { AppHeader } from "../components/AppHeader";

type Severity = "error" | "warning" | "info";
type RecordStatus = "valid" | "warning" | "error";

type Message = {
  severity: Severity;
  code: string;
  message: string;
};

type Preview = {
  row_number: number;
  isbn: string | null;
  title: string | null;
  status: RecordStatus;
  messages: Message[];
};

type ValidationSummary = {
  validation_id: string;
  filename: string;
  total_records: number;
  valid_records: number;
  warning_records: number;
  invalid_records: number;
  duplicate_records: number;
  importable: boolean;
  messages: Message[];
  preview: Preview[];
};

type Health = {
  qdrant_status: "ok" | "error";
  qdrant_url: string;
  collection_name: string;
  collection_status: string;
  dashboard_url?: string | null;
  available_collections?: string[];
  detail?: string | null;
  error_type?: string | null;
  error_traceback?: string | null;
};

type ImportStatus = {
  batch_id: string;
  filename: string;
  status: "pending" | "running" | "completed" | "failed";
  total_records: number;
  processed_records: number;
  success_records: number;
  failed_records: number;
  errors: { code: string; message: string }[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8001/api";

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [summary, setSummary] = useState<ValidationSummary | null>(null);
  const [status, setStatus] = useState<ImportStatus | null>(null);
  const [filter, setFilter] = useState<"all" | RecordStatus>("all");
  const [importMode, setImportMode] = useState("valid_only");
  const [duplicatePolicy, setDuplicatePolicy] = useState("upsert");
  const [batchSize, setBatchSize] = useState(100);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshHealth() {
    try {
      const response = await fetch(`${API_BASE}/health/qdrant`);
      setHealth(await response.json());
    } catch (err) {
      setHealth({
        qdrant_status: "error",
        qdrant_url: "http://localhost:6333",
        collection_name: "books",
        collection_status: "error",
        available_collections: [],
        detail: err instanceof Error ? err.message : "連線失敗",
        error_type: err instanceof Error ? err.name : "FetchError",
        error_traceback: err instanceof Error ? err.stack ?? null : null,
      });
    }
  }

  useEffect(() => {
    refreshHealth();
  }, []);

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
    setSummary(null);
    setStatus(null);
    setError(null);
  }

  async function validateFile() {
    if (!file) return;
    setBusy(true);
    setError(null);
    setStatus(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const response = await fetch(`${API_BASE}/import/validate`, {
        method: "POST",
        body: form,
      });
      if (!response.ok) throw new Error(await response.text());
      setSummary(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "檢查失敗");
    } finally {
      setBusy(false);
    }
  }

  async function executeImport() {
    if (!summary?.validation_id) return;
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/import/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          validation_id: summary.validation_id,
          import_mode: importMode,
          duplicate_policy: duplicatePolicy,
          batch_size: batchSize,
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      setStatus(await response.json());
      refreshHealth();
    } catch (err) {
      setError(err instanceof Error ? err.message : "匯入失敗");
    } finally {
      setBusy(false);
    }
  }

  const filteredPreview = useMemo(() => {
    if (!summary) return [];
    return summary.preview.filter((row) => filter === "all" || row.status === filter);
  }, [summary, filter]);

  const canImport = Boolean(summary?.validation_id && summary.importable && (summary.valid_records + summary.warning_records) > 0);
  const progress = status && status.total_records > 0 ? Math.round((status.processed_records / status.total_records) * 100) : 0;

  return (
    <main className="min-h-screen">
      <AppHeader />
      <header className="hidden">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-6 pt-5 md:flex-row md:items-end md:justify-between">
          <div className="flex items-center gap-3 pb-4">
            <div className="h-12 w-12 overflow-hidden border border-stone-200 bg-stone-950 shadow-sm">
              <img
                src="/book-vector-logo.png"
                alt="圖書向量資料系統 logo"
                className="h-full w-full object-cover"
              />
            </div>
            <div>
              <p className="text-xs font-medium uppercase text-stone-500">Book Vector System</p>
              <h1 className="text-xl font-semibold tracking-normal text-stone-950">圖書向量資料系統</h1>
            </div>
          </div>
          <nav className="flex gap-1 overflow-x-auto" aria-label="主要功能">
            <a
              className="relative flex h-12 items-center whitespace-nowrap border-x border-t border-stone-200 bg-stone-50 px-5 text-sm font-semibold text-stone-950"
              href="/"
            >
              圖書向量資料庫匯入
              <span className="absolute inset-x-0 bottom-0 h-0.5 bg-teal-700" />
            </a>
            <a
              className="flex h-12 items-center whitespace-nowrap border-x border-t border-transparent px-5 text-sm font-medium text-stone-500 hover:border-stone-200 hover:bg-stone-50 hover:text-stone-800"
              href="/book-search"
            >
              圖書向量資料查詢
              <span className="ml-2 align-middle text-xs font-normal text-stone-400">待開發</span>
            </a>
          </nav>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[360px_1fr]">
        <aside className="space-y-6">
          <Panel
            title="連線狀態"
            icon={<Database size={18} />}
            action={
              <button
                className="inline-flex h-7 items-center gap-1 border border-stone-300 bg-white px-2 text-xs font-medium text-stone-700 hover:bg-stone-50"
                onClick={refreshHealth}
                type="button"
              >
                <RefreshCw size={13} />
                重新檢查
              </button>
            }
          >
            <div className="space-y-3 text-sm">
              <StatusLine label="Qdrant" ok={health?.qdrant_status === "ok"} value={health?.qdrant_status ?? "checking"} />
              <InfoLine label="URL" value={health?.qdrant_url ?? "-"} />
              <InfoLine label="Collection" value={health?.collection_name ?? "books"} />
              <InfoLine label="狀態" value={health?.collection_status ?? "-"} />
              {health?.dashboard_url ? (
                <a className="block break-all text-xs text-teal-700 underline" href={health.dashboard_url} rel="noreferrer" target="_blank">
                  開啟 Qdrant collection
                </a>
              ) : null}
              {health?.detail || health?.error_type || health?.error_traceback ? (
                <pre className="max-h-64 overflow-auto whitespace-pre-wrap border border-red-200 bg-red-50 p-3 text-xs leading-5 text-red-800">
                  {[
                    health.error_type ? `error_type: ${health.error_type}` : null,
                    health.detail ? `detail: ${health.detail}` : null,
                    health.error_traceback ? `traceback:\n${health.error_traceback}` : null,
                  ]
                    .filter(Boolean)
                    .join("\n\n")}
                </pre>
              ) : null}
            </div>
          </Panel>

          <Panel title="JSON 檔案" icon={<FileJson size={18} />}>
            <label className="flex cursor-pointer items-center gap-3 border border-stone-300 bg-stone-50 px-3 py-3 hover:bg-stone-100">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center bg-white text-teal-700">
                <Upload size={18} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-medium text-stone-900">
                  {file ? file.name : "選擇 JSON 檔"}
                </span>
                <span className="mt-0.5 block truncate text-xs text-stone-500">
                  {file ? `${(file.size / 1024).toFixed(1)} KB` : `支援陣列或 { books: [...] }`}
                </span>
              </span>
              <span className="shrink-0 border border-stone-300 bg-white px-2 py-1 text-xs font-medium text-stone-700">
                瀏覽
              </span>
              <input className="hidden" type="file" accept=".json,application/json" onChange={onFileChange} />
            </label>
            <button
              className="mt-3 inline-flex h-9 w-full items-center justify-center gap-2 bg-teal-700 px-4 text-sm font-medium text-white hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-stone-300"
              disabled={!file || busy}
              onClick={validateFile}
              type="button"
            >
              <CheckCircle2 size={16} />
              檢查資料
            </button>
          </Panel>

          <Panel title="匯入選項">
            <div className="space-y-4 text-sm">
              <SelectLine label="模式" value={importMode} onChange={setImportMode} options={["valid_only", "all_or_nothing"]} />
              <SelectLine label="重複 ISBN" value={duplicatePolicy} onChange={setDuplicatePolicy} options={["upsert", "skip", "reject"]} />
              <label className="block">
                <span className="mb-1 block text-xs font-medium text-stone-500">批次大小</span>
                <input
                  className="h-10 w-full border border-stone-300 px-3"
                  min={10}
                  max={1000}
                  type="number"
                  value={batchSize}
                  onChange={(event) => setBatchSize(Number(event.target.value))}
                />
              </label>
              <button
                className="inline-flex h-10 w-full items-center justify-center gap-2 bg-stone-950 px-4 text-sm font-medium text-white hover:bg-stone-800 disabled:cursor-not-allowed disabled:bg-stone-300"
                disabled={!canImport || busy}
                onClick={executeImport}
                type="button"
              >
                <Play size={16} />
                匯入向量資料庫
              </button>
            </div>
          </Panel>
        </aside>

        <section className="space-y-6">
          {error ? <div className="border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">{error}</div> : null}

          <Panel title="檢查摘要">
            {summary ? (
              <>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
                  <Metric label="總筆數" value={summary.total_records} />
                  <Metric label="有效" value={summary.valid_records} />
                  <Metric label="警告" value={summary.warning_records} />
                  <Metric label="錯誤" value={summary.invalid_records} />
                  <Metric label="重複 ISBN" value={summary.duplicate_records} />
                </div>
                {summary.messages.length ? (
                  <MessageList messages={summary.messages} />
                ) : null}
              </>
            ) : (
              <EmptyState text="尚未檢查檔案" />
            )}
          </Panel>

          <Panel title="匯入進度">
            {status ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-stone-900">{status.status}</span>
                  <span className="text-stone-500">{progress}%</span>
                </div>
                <div className="h-3 bg-stone-200">
                  <div className="h-3 bg-teal-700" style={{ width: `${progress}%` }} />
                </div>
                <div className="grid gap-3 sm:grid-cols-3">
                  <Metric label="已處理" value={status.processed_records} />
                  <Metric label="成功" value={status.success_records} />
                  <Metric label="失敗" value={status.failed_records} />
                </div>
                {status.errors.length ? <MessageList messages={status.errors.map((item) => ({ severity: "error" as const, ...item }))} /> : null}
              </div>
            ) : (
              <EmptyState text="完成檢查後即可匯入" />
            )}
          </Panel>

          <Panel title="資料預覽">
            {summary ? (
              <>
                <div className="mb-4 flex flex-wrap gap-2">
                  {(["all", "valid", "warning", "error"] as const).map((item) => (
                    <button
                      className={`h-9 border px-3 text-sm ${filter === item ? "border-teal-700 bg-teal-700 text-white" : "border-stone-300 bg-white text-stone-700"}`}
                      key={item}
                      onClick={() => setFilter(item)}
                      type="button"
                    >
                      {item}
                    </button>
                  ))}
                </div>
                <div className="overflow-x-auto max-h-[500px] overflow-y-auto border border-stone-200">
                  <table className="w-full min-w-[760px] border-collapse text-sm">
                    <thead className="sticky top-0 z-10 bg-white shadow-[0_1px_0_0_rgba(0,0,0,0.05)]">
                      <tr className="border-b border-stone-200 text-left text-xs font-medium uppercase text-stone-500 bg-white">
                        <th className="py-2.5 px-3">#</th>
                        <th className="py-2.5 pr-3">ISBN</th>
                        <th className="py-2.5 pr-3">書名</th>
                        <th className="py-2.5 pr-3">狀態</th>
                        <th className="py-2.5 pr-3">訊息</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredPreview.map((row) => (
                        <tr className="border-b border-stone-100 align-top" key={row.row_number}>
                          <td className="py-3 px-3 text-stone-500">{row.row_number}</td>
                          <td className="py-3 pr-3">{row.isbn ?? "-"}</td>
                          <td className="max-w-xs py-3 pr-3">{row.title ?? "-"}</td>
                          <td className="py-3 pr-3">
                            <StatusBadge status={row.status} />
                          </td>
                          <td className="py-3 pr-3 text-xs text-stone-600">
                            {row.messages.map((message) => message.message).join("；") || "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <EmptyState text="檢查結果會顯示在這裡" />
            )}
          </Panel>
        </section>
      </div>
    </main>
  );
}

function Panel({ title, icon, action, children }: { title: string; icon?: ReactNode; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="border border-stone-200 bg-white p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          {icon}
          <h2 className="text-base font-semibold text-stone-950">{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function InfoLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3">
      <span className="text-stone-500">{label}</span>
      <span className="break-all text-right font-medium text-stone-900">{value}</span>
    </div>
  );
}

function StatusLine({ label, ok, value }: { label: string; ok: boolean; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-stone-500">{label}</span>
      <span className={`inline-flex items-center gap-1 font-medium ${ok ? "text-teal-700" : "text-red-700"}`}>
        {ok ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
        {value}
      </span>
    </div>
  );
}

function SelectLine({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium text-stone-500">{label}</span>
      <select className="h-10 w-full border border-stone-300 bg-white px-3" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-stone-200 bg-stone-50 p-4">
      <p className="text-xs font-medium text-stone-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-stone-950">{value}</p>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="border border-dashed border-stone-300 bg-stone-50 px-4 py-8 text-center text-sm text-stone-500">{text}</div>;
}

function StatusBadge({ status }: { status: RecordStatus }) {
  const color = status === "valid" ? "bg-teal-50 text-teal-800" : status === "warning" ? "bg-amber-50 text-amber-800" : "bg-red-50 text-red-800";
  return <span className={`inline-flex px-2 py-1 text-xs font-medium ${color}`}>{status}</span>;
}

function MessageList({ messages }: { messages: Message[] }) {
  return (
    <div className="mt-4 space-y-2">
      {messages.map((message, index) => (
        <div className="border border-stone-200 bg-stone-50 px-3 py-2 text-sm" key={`${message.code}-${index}`}>
          <span className="font-medium">{message.code}</span>
          <span className="ml-2 text-stone-600">{message.message}</span>
        </div>
      ))}
    </div>
  );
}
