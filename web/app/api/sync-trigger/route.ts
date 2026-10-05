import { NextResponse } from "next/server";
import { getBaseUrl } from "@/lib/api-base-url";

// Backs the dashboard's "Sync now" button. Runs server-side only, so
// CRON_SECRET never reaches the browser - the button's client component
// just POSTs here with no arguments, and this route attaches the secret
// itself before calling the same /api/sync the Vercel Cron job hits.
export async function POST() {
  const secret = process.env.CRON_SECRET;
  if (!secret) {
    return NextResponse.json(
      { error: "CRON_SECRET is not configured on the server" },
      { status: 500 }
    );
  }

  let res: Response;
  try {
    res = await fetch(`${getBaseUrl()}/api/sync`, {
      method: "POST",
      headers: { Authorization: `Bearer ${secret}` },
    });
  } catch (e) {
    return NextResponse.json(
      { error: `Could not reach sync endpoint: ${e}` },
      { status: 502 }
    );
  }

  // Read as text first - a crash or misroute can return an HTML error page
  // instead of JSON, and res.json() throwing a SyntaxError on that would
  // otherwise surface as an opaque "Unexpected token '<'" message.
  const bodyText = await res.text();
  try {
    const json = JSON.parse(bodyText);
    return NextResponse.json(json, { status: res.status });
  } catch {
    return NextResponse.json(
      {
        error: `Sync endpoint returned a non-JSON response (HTTP ${res.status})`,
        bodyPreview: bodyText.slice(0, 200),
      },
      { status: 502 }
    );
  }
}
