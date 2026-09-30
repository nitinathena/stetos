import "server-only";
import { createClient } from "@supabase/supabase-js";

// Server-only Supabase client using the service_role key. Import this ONLY
// from Server Components, Route Handlers, or other server-side code - the
// "server-only" import above makes Next.js throw a build error if any
// Client Component ever tries to import this file, so a mistake here fails
// loudly instead of silently leaking the key to the browser.

export function getSupabaseServerClient() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!url || !key) {
    throw new Error(
      "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set (see .env.example)"
    );
  }

  return createClient(url, key, {
    auth: { persistSession: false },
  });
}

export const PREDICTIONS_TABLE = "predictions";
