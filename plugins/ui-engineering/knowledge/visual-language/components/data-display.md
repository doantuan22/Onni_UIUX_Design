# Data display grammar

| Component | Design rules | States | Implementation guidance |
|---|---|---|---|
| **Cards** | A card needs a grouping or interaction reason ([surfaces](surfaces.md)); one primary action; consistent anatomy within a collection; whole-card links use one stretched anchor | default, hover (if interactive), focus, selected, loading, disabled | Consistent aspect ratios for media; no nested cards without a hierarchy boundary |
| **Data visualization container** | Title stating the insight, time range, legend near data, source/updated time, actions (expand, export) in a quiet toolbar | loading (skeleton shaped like the chart), empty (explain why), error (retry), partial data (flag), stale (timestamp) | Chart colors from the data palette, not decoration; text summary or table alternative; container queries for small widths |
| **Upload** | Drop zone plus a visible browse button; accepted types and size limits stated before upload; per-file progress and result | idle, drag-over, invalid, uploading, success, error per file, cancelled | `interaction.drop-zone`; keyboard browse path; progress via `transform: scaleX`; retry per file |
| **Skeletons** | Shapes mirror the final layout; low contrast; shimmer slow or static | loading → content crossfade without shift | Appear after ~300ms to avoid flash; `aria-busy` on the region; static under reduced motion |
| **Empty states** | Explain what will appear and offer the next action; different copy for first use, no results and all done | first-use, no-results, cleared | See [screen.empty-state](../../domains/screens/states.md); illustrations optional and decorative |

Anti-patterns: decorative charts without insight; skeletons that do not match the layout; spinner-only uploads; empty states that are only an illustration.
