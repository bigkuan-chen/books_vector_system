"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, Upload } from "lucide-react";

const navItems = [
  { href: "/", label: "圖書資料匯入", icon: Upload },
  { href: "/book-search", label: "圖書向量資料查詢", icon: Search },
];

export function AppHeader() {
  const pathname = usePathname();

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-4 md:flex-row md:items-center md:justify-between">
        <Link className="flex items-center gap-3" href="/">
          <div className="h-11 w-11 overflow-hidden border border-slate-200 bg-white">
            <img src="/book-vector-logo.png" alt="Book Vector System" className="h-full w-full object-cover" />
          </div>
          <div>
            <p className="text-xs font-medium uppercase text-slate-500">Book Vector System</p>
            <h1 className="text-xl font-semibold tracking-normal text-slate-950">圖書向量資料庫系統</h1>
          </div>
        </Link>

        <nav className="flex gap-2 overflow-x-auto text-sm" aria-label="主要功能">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                className={`inline-flex h-10 items-center gap-2 whitespace-nowrap border px-3 font-medium ${
                  active
                    ? "border-slate-950 bg-slate-950 text-white"
                    : "border-slate-300 bg-white text-slate-700 hover:bg-slate-100"
                }`}
                href={item.href}
                key={item.href}
              >
                <Icon size={16} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
