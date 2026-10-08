# Legacy Stacks

Read only the section that matches the project. Keep writing in the project's current stack; upgrade it only when the user asks.

## Token names from this skill (0.8 and earlier)

Projects built with earlier versions of this skill define their own custom properties instead of shadcn tokens. Read each one as its current equivalent. Rename them only when the task is theming or the user asks, and then rename the definitions and every usage in one change.

| 0.8 and earlier | Current |
|---|---|
| `--bg` | `--background` |
| `--panel` | `--card`, `--popover` |
| `--ink` | `--foreground` and the other `*-foreground` tokens in the theme table |
| `--ink-secondary` | `--muted-foreground` |
| `--accent` | `--primary` (shadcn's `--accent` is the hover surface) |
| `--accent-tint` | `bg-primary/10 dark:bg-primary/14` |
| `--hairline` | `--border` |
| `--hairline-bright` | `--input` |
| `--hover-bg` | `--accent`, `--muted` |
| `--card-shadow` | `shadow-card dark:shadow-none` |
| `text-[24px]`, `text-[14px]`, `text-[13px]`, `text-[12px]`, `text-[11px]` | `text-kpi`, `text-title`, `text-body`, `text-caption`, `text-micro` |

## shadcn/ui on Tailwind CSS v3

Markers: `tailwind.config.*` maps colors to `hsl(var(--…))`, `components.json#tailwind.config` is set, or the CSS starts with `@tailwind base`.

- Token names match the theme table, except `--sidebar-background` (v4: `--sidebar`) and `--destructive-foreground` (removed in v4).
- Values are bare HSL channels that the config wraps in `hsl()`. The palette in that form:

| Tokens | Light | Dark |
|---|---|---|
| `--background`, `--sidebar-background` | `0 0% 98%` | `240 4.8% 4.1%` |
| `--card`, `--popover` | `0 0% 100%` | `240 4.8% 8.2%` |
| `--foreground` and the other `*-foreground` tokens in the theme table | `240 3.2% 6.1%` | `240 5.9% 93.3%` |
| `--muted-foreground` | `220 8.9% 46.1%` | `218.6 6.4% 56.9%` |
| `--primary`, `--sidebar-primary`, `--ring`, `--sidebar-ring` | `233.8 56.3% 59.6%` | `233.8 56.3% 59.6%` |
| `--primary-foreground`, `--sidebar-primary-foreground` | `0 0% 100%` | `0 0% 100%` |
| `--accent`, `--muted`, `--secondary`, `--sidebar-accent` | `0 0% 0% / 0.035` | `0 0% 100% / 0.05` |
| `--border`, `--sidebar-border` | `0 0% 0% / 0.08` | `0 0% 100% / 0.08` |
| `--input` | `0 0% 0% / 0.12` | `0 0% 100% / 0.12` |

- A token that carries alpha cannot take an opacity modifier in v3, because `hover:bg-muted/50` would produce an invalid `hsl()`. Drop the modifier where a component uses one.
- v3's opacity scale has no 14, so the dark active background is `dark:bg-primary/[0.14]`.
- The scale tokens live in `tailwind.config.*` under `theme.extend`: `fontSize: { kpi: "24px", title: "14px", body: "13px", caption: "12px", micro: "11px" }` and `boxShadow: { card: "0 1px 2px rgb(0 0 0 / 0.04)" }`.
- `cn` stays `twMerge(clsx(...))` on tailwind-merge v2, and it needs the same registration as the current `cn`: build it from `extendTailwindMerge({ extend: { classGroups: { "font-size": [{ text: ["kpi", "title", "body", "caption", "micro"] }] } } })`.
- Dark mode is `darkMode: ["class"]`, animations come from the `tailwindcss-animate` plugin, and components use `React.forwardRef` without `data-slot`. Undo toasts use `sonner`.

Rules from this skill that need different syntax on v3:

| Rule | v4 | v3 |
|---|---|---|
| Phone-only chrome | `pointer-coarse:` | `[@media(pointer:coarse)]:` |
| Hover only on hover-capable devices | built into `hover:` | `future: { hoverOnlyWhenSupported: true }` in the config |
| Container queries | built in | `@tailwindcss/container-queries` plugin |
| Long text wrapping | `wrap-break-word`, `wrap-anywhere` | `break-words`, `[overflow-wrap:anywhere]` |
| Pointer cursor on buttons | the base rule from `init --pointer` | already set by v3 Preflight |

Reading v3 class names:

| v3 | v4 |
|---|---|
| `shadow-sm`, `shadow` | `shadow-xs`, `shadow-sm` |
| `rounded-sm`, `rounded` | `rounded-xs`, `rounded-sm` |
| `blur-sm`, `blur` | `blur-xs`, `blur-sm` |
| `outline-none` (transparent outline) | `outline-hidden` |
| `ring` (3px) | `ring-3` |
| `bg-[--brand]` | `bg-(--brand)` |
| `!font-bold` | `font-bold!` |
| `flex-shrink-0`, `flex-grow` | `shrink-0`, `grow` |
| `bg-opacity-50` | `bg-black/50` |
| `first:*:pt-0` (variants apply right to left) | `*:first:pt-0` (left to right) |

## Tailwind CSS v4.0–4.2

| Current name | Added in | Before that |
|---|---|---|
| `pointer-coarse:` | 4.1 | `[@media(pointer:coarse)]:` |
| `wrap-break-word` | 4.1 | `break-words` |
| `inset-s-*`, `inset-e-*` | 4.2, which deprecated `start-*`/`end-*` | `start-*`, `end-*` |

## Older shadcn/ui on Tailwind CSS v4

| Marker | Current |
|---|---|
| `components.json#style` is `new-york` (Radix, before the `{base}-{style}` presets) | Same rules; run the "After every `shadcn add`" table on its components |
| `:root` values written as `hsl(…)` (upgraded from v3) | The OKLCH values from the theme table work as-is |
| `lib/utils.ts` builds `cn` from `clsx` + `tailwind-merge` | The `createCn` setup in the theme section, after `npx shadcn@latest migrate cn`; until then register the scale with `extendTailwindMerge` and the same `extend` object |
| Components import `@radix-ui/react-*` | The unified `radix-ui` package, via `npx shadcn@latest migrate radix` |
| `@plugin "tailwindcss-animate"` | `@import "tw-animate-css"` |
| No `Kbd`, `Spinner`, `Empty`, `Field`, `Item`, `InputGroup`, `ButtonGroup` | `npx shadcn@latest add <name>` instead of hand-rolling them |
| No pointer-cursor base rule | Add the rule from Interaction & Accessibility |
| Radix `asChild` | Base UI uses `render`; button-styled links still use `buttonVariants()` |
