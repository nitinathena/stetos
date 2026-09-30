import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient, PREDICTIONS_TABLE } from "@/lib/supabase-server";
import { getBaseUrl } from "@/lib/api-base-url";

// Receives a WAV upload from the browser (drag-and-drop / file picker on
// /upload), forwards it to the Python inference function, then logs the
// result into the predictions table with source="user_upload". The
// browser never talks to Supabase directly - this route is the only thing
// that does, using the service_role key server-side.
export async function POST(request: NextRequest) {
  const formData = await request.formData();
  const file = formData.get("file");

  if (!file || !(file instanceof Blob)) {
    return NextResponse.json({ error: "No 'file' provided" }, { status: 400 });
  }

  const forwardForm = new FormData();
  forwardForm.append("file", file, (file as File).name ?? "upload.wav");

  let predictResult: { filename: string; prediction: string; confidence: number };
  try {
    const predictRes = await fetch(`${getBaseUrl()}/api/predict`, {
      method: "POST",
      body: forwardForm,
    });
    const predictJson = await predictRes.json();

    if (!predictRes.ok) {
      return NextResponse.json(
        { error: predictJson.error ?? "Inference failed" },
        { status: predictRes.status }
      );
    }
    predictResult = predictJson;
  } catch (e) {
    return NextResponse.json(
      { error: `Could not reach inference endpoint: ${e}` },
      { status: 502 }
    );
  }

  try {
    const supabase = getSupabaseServerClient();
    const { error } = await supabase.from(PREDICTIONS_TABLE).insert({
      filename: predictResult.filename,
      source: "user_upload",
      prediction: predictResult.prediction,
      confidence: predictResult.confidence,
    });

    if (error) {
      // Inference succeeded but logging failed - still return the
      // prediction to the user, but surface the logging problem.
      return NextResponse.json({
        ...predictResult,
        warning: `Prediction succeeded but was not logged: ${error.message}`,
      });
    }
  } catch (e) {
    return NextResponse.json({
      ...predictResult,
      warning: `Prediction succeeded but was not logged: ${e}`,
    });
  }

  return NextResponse.json(predictResult);
}
