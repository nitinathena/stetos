export default function DisclaimerBanner() {
  return (
    <div
      role="note"
      aria-label="Research prototype disclaimer"
      className="w-full border-b px-4 py-3 text-sm sm:px-6"
      style={{
        background: "var(--warning-bg)",
        borderColor: "var(--warning-border)",
        color: "var(--warning-text)",
      }}
    >
      <div className="mx-auto flex max-w-6xl items-start gap-2">
        <span aria-hidden="true" className="mt-0.5">
          ⚠️
        </span>
        <p className="leading-snug">
          <strong className="font-semibold">Research prototype, not a medical device.</strong>{" "}
          CorAscult is a student-competition project. Predictions are experimental,
          have not been validated against real hardware recordings with confirmed
          ground truth, and must never be used to diagnose, rule out, or make any
          decision about a real heart condition. If you have health concerns, see a
          clinician.
        </p>
      </div>
    </div>
  );
}
