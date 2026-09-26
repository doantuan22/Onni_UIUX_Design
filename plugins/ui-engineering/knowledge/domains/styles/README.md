# Style Intelligence

A style is a **visual language**: a coherent set of decisions about layout, type, color, surfaces, imagery, motion, interaction and effects. It is not a keyword. Product-level [design archetypes](../../../skills/design-inspiration/archetypes.md) say *what kind of product experience* is needed; styles say *which visual language realizes it*. The archetype constrains the style, never the reverse.

| File | Family | Styles |
|---|---|---|
| [restrained.md](restrained.md) | restrained / editorial | minimal, swiss, editorial, monochrome, luxury, organic |
| [expressive.md](expressive.md) | expressive | neo-brutalism, brutalist, y2k, playful, experimental, creative-agency, retro-futurism, cyberpunk |
| [material.md](material.md) | material / depth | glassmorphism, liquid-glass, bento, tactile, spatial, gradient-heavy, cinematic |
| [futuristic.md](futuristic.md) | futuristic / AI | futuristic, calm-futurism, ai-native |
| [product.md](product.md) | product / commerce | developer-tool, enterprise-saas, modern-saas, data-dense, fintech, productivity, ecommerce-premium |

## Using a style entry

1. Do not browse this folder. The [Capability Resolver](../../../skills/capability-resolver/README.md) ranks candidates from intent; load only the chosen primary (and at most one secondary) entry.
2. Treat every field as a **direction**, then encode it in tokens (Design System), behavior (Visual Grammar), motion (Motion System) and components.
3. `compatible_styles` lists safe secondaries. Mixing is limited to a primary plus one secondary, with the secondary scoped (e.g., "hero only").
4. `default_tell: true` marks styles that are overused in AI-generated interfaces. They are allowed with a recorded product reason; they are never a default. See [anti-homogenization](../composition/anti-homogenization.md).
5. Machine fields (`domains`, `conveys`, `perceived_risks`, `intensity`, `contexts`, `motion_ceiling`) feed the resolver. `intensity` is the visual-intensity range 1–5 the style supports; `motion_ceiling` is the highest motion tier it tolerates.

Schema: [schema.md](../schema.md#style).
