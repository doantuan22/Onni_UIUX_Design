# Design system workflow

Create or update `DESIGN-SYSTEM.md` as the source of truth after direction is approved. Its Typography system section is produced by [Typography Intelligence](../typography/README.md); motion duration/easing tokens follow the ranges in [motion-principles](../../knowledge/motion/motion-principles.md). Define semantic color, typography hierarchy, spacing, radius, borders, elevation, grid, breakpoints, containers, iconography, imagery, motion, states, and base component contracts. Then create `DESIGN-TOKENS.md` mapped to the existing stack.

Tokens are available values, not a substitute for rendered visual behavior. Hand the approved token system to [Visual Language](../visual-language/workflow.md), which records color/type/surface/motion character and component grammar without creating a competing token source.

For an existing frontend, first create `CURRENT-DESIGN-SYSTEM.md`: inventory colors, typography, spacing, components, layout conventions, CSS strategy, and exceptions; compare it to target direction and choose keep/refine/replace/migrate. Audit hardcoded values as keep, normalize, tokenize, or remove—do not refactor blindly.
