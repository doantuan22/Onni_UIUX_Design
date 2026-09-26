# Motion review

Run during [craft review](../../skills/visual-language/craft-review.md) on rendered output (or source when rendering is unavailable, stated as a limitation). Record in `VISUAL-REVIEW.md`.

| Code | Detect | Severity guide | Fix |
|---|---|---|---|
| `MOTION_FOR_DECORATION` | Motion with no feedback/orientation/hierarchy/state/story purpose (floating blobs, glowing pulses, perpetual gradients) | MINOR–MAJOR by area | Remove, or reduce to a single justified brand moment |
| `EXCESSIVE_ENTRANCE_ANIMATION` | Entrance on most elements; per-card/per-paragraph reveals; re-trigger on scroll-up; stagger > ~600ms | MAJOR | One reveal per section at most; cap stagger; above-fold content visible immediately |
| `EVERYTHING_ANIMATED` | No region is calm; multiple `HIGH` regions; budget missing | MAJOR | Apply [intensity budget](motion-principles.md#intensity-budget) |
| `SLOW_INTERACTION` | Controls > ~200ms feedback; overlays > ~400ms; content blocked while animating | MAJOR | Use timing ranges by interaction type |
| `SCROLL_JANK_RISK` | See [performance-safety.md](performance-safety.md) | MAJOR (BLOCKER if scroll is unusable) | Native/IO strategies; transform-only; disable on mobile |
| `MOTION_WITHOUT_REDUCED_MODE` | No `prefers-reduced-motion` handling for non-essential motion | MAJOR/BLOCKER | [reduced-motion.md](reduced-motion.md) |
| `MOTION_STYLE_DRIFT` | Durations/easings/directions inconsistent across equivalent components; character contradicts archetype; two animation libraries mixed | MINOR–MAJOR | Normalize to motion tokens and one implementation approach |
| `SCROLL_HIJACKING` | Wheel/touch speed or direction overridden; forced snapping through content | MAJOR/BLOCKER | Native scroll; pinning only with scrub and escape |
| `MOTION_LAYOUT_INSTABILITY` | Animated layout properties or late motion causing layout shift | MAJOR | Transform/opacity; reserve space |
| `COMPETING_MOTION_DIRECTIONS` | Simultaneous movements in different directions | MINOR–MAJOR | One spatial model; stagger or remove |
| `UNJUSTIFIED_PARALLAX` | Parallax without depth narrative, on text, multiple sections, or on mobile | MAJOR | Remove or restrict to one atmospheric layer with reduced fallback |

Checks also include: `transition: all` usage, focus visibility during transitions, auto-moving content > 5s without pause, content hidden when JS fails, dependency added without authorization.

Already-good motion: if purposeful, budgeted, consistent and reduced-motion-safe, classify `KEEP` and leave it.
