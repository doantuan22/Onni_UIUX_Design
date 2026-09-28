/**
 * @recipe grain-texture
 *
 * A subtle film-grain or dot-grid layer behind a hero or a full-bleed band: adds material without blurred gradient
 * blobs. Inline SVG noise (no image request), pointer-events disabled, hidden from assistive tech, and kept below
 * 5% opacity so text contrast is unaffected. Skip it on data-dense screens.
 *
 * Usage (inside a `relative isolate` section):
 *   <GrainTexture />                 // film grain
 *   <GrainTexture pattern="dots" />  // 24px dot grid that fades out toward the bottom
 */
const NOISE =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")";

export function GrainTexture({ pattern = "grain" }: { pattern?: "grain" | "dots" }) {
  if (pattern === "dots") {
    return (
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(color-mix(in_oklch,var(--color-ink-900)_14%,transparent)_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:linear-gradient(to_bottom,black,transparent_85%)]"
      />
    );
  }
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 -z-10 opacity-[0.045] mix-blend-multiply"
      style={{ backgroundImage: NOISE }}
    />
  );
}
