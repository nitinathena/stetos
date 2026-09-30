// Server-side fetch() calls need an absolute URL - there's no "current page"
// to resolve a relative path against inside a Route Handler. Vercel injects
// VERCEL_URL (the deployment's own hostname, no protocol) automatically;
// fall back to localhost for `next dev`.
export function getBaseUrl(): string {
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`;
  }
  return `http://localhost:${process.env.PORT ?? 3000}`;
}
