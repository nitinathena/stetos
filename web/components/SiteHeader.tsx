import Link from "next/link";

export default function SiteHeader() {
  return (
    <header
      className="w-full border-b px-4 py-4 sm:px-6"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold text-white"
            style={{ background: "var(--brand)" }}
          >
            C
          </span>
          <span className="text-lg font-semibold tracking-tight">CorAscult</span>
        </Link>
        <nav className="flex items-center gap-6 text-sm font-medium">
          <Link href="/" className="hover:opacity-70">
            Dashboard
          </Link>
          <Link href="/upload" className="hover:opacity-70">
            Upload a recording
          </Link>
        </nav>
      </div>
    </header>
  );
}
