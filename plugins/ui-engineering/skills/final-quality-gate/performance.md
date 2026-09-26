# Performance quality

At final QA, inspect layout shift, image sizing/fallback/lazy loading, unused or duplicated CSS patterns, unnecessary animation, heavy DOM, excessive nesting, and expensive visual effects. Run Lighthouse or Core Web Vitals checks only when the environment supports them and the task warrants it; they are final evidence, not a per-edit loop.

For motion, apply [motion performance safety](../../knowledge/motion/performance-safety.md) and flag `SCROLL_JANK_RISK`; for effects, interactions and graphics, check the [performance budget](../frontend-implementation/performance-budget.md).
