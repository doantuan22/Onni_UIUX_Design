# target-c-next-tailwind — elevated overlay

The Elevate result for [`target-c-next-tailwind`](../target-c-next-tailwind/): these files replace or add to the
base fixture, and the recipes from `plugins/ui-engineering/knowledge/code-recipes/react-tailwind/` are mounted at
`src/components/recipes/`. Content (headings, copy, actions, routes) is unchanged; the app shell (Navbar, Footer,
layout) is untouched. Tests assemble base + overlay + recipes in memory and check it with `diff_ui_maps`.
