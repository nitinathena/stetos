// Server-side fetch() calls need an absolute URL - there's no "current page"
// to resolve a relative path against inside a Route Handler.
//
// Deliberately NOT using VERCEL_URL here: it points at the ephemeral
// per-deployment hostname, which sits behind Vercel's "Vercel Authentication"
// deployment protection - an internal fetch to it gets redirected to an HTML
// auth page instead of reaching /api/predict (Vercel's own docs note VERCEL_URL
// "cannot be used in conjunction with Standard Deployment Protection").
// VERCEL_PROJECT_PRODUCTION_URL is the stable production domain and isn't
// behind that wall.
export function getBaseUrl(): string {
  if (process.env.VERCEL_PROJECT_PRODUCTION_URL) {
    return `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`;
  }
  if (process.env.VERCEL_URL) {
    return `https://${process.env.VERCEL_URL}`;
  }
  return `http://localhost:${process.env.PORT ?? 3000}`;
}
