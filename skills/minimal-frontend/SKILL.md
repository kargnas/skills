---
name: minimal-frontend
description: Design system shared by app UI and standalone HTML report pages, covering theme tokens, type and density scale, status colors, container-first responsive rules, anti-slop, and accessibility. Use when starting frontend work in a project with no existing design system, when building or theming UI with shadcn/ui or Tailwind CSS, when asked to review or audit web UI, or when findings, an analysis, or a status must become an HTML page people read (report page, readable page, 리포트, 보고서, html로 만들어, 보기 쉽게 정리). App rules add URL-first routing, scoped async loading, theme and i18n defaults, applied UX laws, component policies, and UI copy. Report rules add the page skeleton, blocks, wording, and checkbox options for inline translation with original-text tooltips and for speaker photos (인용 번역, 원문 툴팁, 발언자 프사).
metadata:
  author: kargnas
  version: "0.11.0"
  argument-hint: <file-or-pattern>
---

# Minimal Frontend

One design system for two kinds of output: app UI and report pages. This file holds the rules both share, written in shadcn/ui and Tailwind CSS v4 names. The file for the output says how to apply them.

## Pick the output

| Request | MUST read before writing code or findings |
|---|---|
| App UI: building or editing screens, components, or flows inside a product, a report screen included | [app.md](app.md) |
| A review or audit of web UI | [app.md](app.md), Review Preflight first; also [report.md](report.md) when the target is a report page |
| Report page: one standalone HTML file that presents findings, an analysis, or a status to readers | [report.md](report.md) |

`app.md` says when to read these, and a report page never needs them: [references/component-policies.md](references/component-policies.md) for per-component counts, behavior, and copy limits; [references/legacy.md](references/legacy.md) for Tailwind CSS v3 and older token names; the [Transitions.dev guide](sub-skills/transitions-dev/GUIDE.md) for transitions and motion tokens. `report.md` offers the report options as checkboxes, and a page reads only the checked ones: [`report-options/inline-translation.md`](report-options/inline-translation.md) and [`report-options/speaker-photos.md`](report-options/speaker-photos.md).

## Design System

### Theme tokens

These values are the theme. `app.md` and `report.md` say where each output declares them.

| Tokens | Light | Dark |
|---|---|---|
| `--background`, `--sidebar` | `oklch(0.985 0 0)` | `oklch(0.145 0.002 286.131)` |
| `--card`, `--popover` | `oklch(1 0 0)` | `oklch(0.192 0.004 286.018)` |
| `--foreground`, `--card-foreground`, `--popover-foreground`, `--secondary-foreground`, `--accent-foreground`, `--sidebar-foreground`, `--sidebar-accent-foreground` | `oklch(0.169 0.002 286.177)` | `oklch(0.947 0.003 286.349)` |
| `--muted-foreground` | `oklch(0.551 0.023 264.364)` | `oklch(0.649 0.015 262.359)` |
| `--primary`, `--sidebar-primary`, `--ring`, `--sidebar-ring` | `oklch(0.567 0.159 275.206)` | `oklch(0.567 0.159 275.206)` |
| `--primary-foreground`, `--sidebar-primary-foreground` | `oklch(1 0 0)` | `oklch(1 0 0)` |
| `--accent`, `--muted`, `--secondary`, `--sidebar-accent` | `oklch(0 0 0 / 3.5%)` | `oklch(1 0 0 / 5%)` |
| `--border`, `--sidebar-border` | `oklch(0 0 0 / 8%)` | `oklch(1 0 0 / 8%)` |
| `--input` | `oklch(0 0 0 / 12%)` | `oklch(1 0 0 / 12%)` |

- `primary` is the single accent color, and focus rings use it too. shadcn's `accent` is the hover/selected surface, not the brand color.
- Selected or active backgrounds use `bg-primary/10 dark:bg-primary/14`.
- A new semantic color follows shadcn's pair convention: `--name` and `--name-foreground`, defined for light and dark.
- Every output ships both themes behind a three-way `System / Light / Dark` selector: default System (`prefers-color-scheme`), persisted. Nothing ships light-only.

The type scale and the only allowed elevation:

```css
@theme {
  --text-kpi: 24px;     /* KPI numbers */
  --text-title: 14px;   /* page, card, dialog titles */
  --text-body: 13px;    /* body, nav, menus, buttons, inputs, table cells */
  --text-caption: 12px; /* captions, field labels, table headers */
  --text-micro: 11px;   /* kbd, badges, xs buttons, menu shortcuts */
  --shadow-card: 0 1px 2px rgb(0 0 0 / 0.04);
}
```

The text tokens set font size only. Line height comes from the parent or from a modifier such as `text-body/relaxed`.

### Fonts

- Inter (`font-sans`, UI text), JetBrains Mono (`font-mono` — numbers/ids/paths/status badges), Noto Sans KR/SC/JP appended to the `--font-sans` stack as CJK fallback.
- Numbers, identifiers, file paths, and status badges are ALWAYS `font-mono` — proportional digits jitter when values update.

### Status colors

One status vocabulary for every component (badge, field, toast, chart):

- critical (error, failure, rejected, failed check) = `destructive`.
- warning (expiring soon, missing submission) = amber. Quota/progress bars use amber for the 20-50% remaining band.
- live/streaming = emerald.
- neutral, ok, and informative (beta, limited permission) = `text-muted-foreground`. Positive results (saved, approved, published) count as ok.
- AI features and AI-generated content carry one marker everywhere, including their loading and notice states: the same icon from the project's icon set plus an `AI` label, with no extra color.

### Density scale

- Padding: boxes/cards/bands use the SAME value on all four sides — large cards `p-4`, dense boards/list items `p-3` (shadcn `Card` default and `size="sm"`). Asymmetric padding only on small buttons/chips (and table cells `px-4 py-2`).
- **Padding/gap tokens never exceed 16px (=4)** — `p-5`/`p-6`/`gap-5`+ and `--spacing(5)`+ are forbidden. Gaps: `gap-2/3/4`.
- Vertical rhythm: `mt-8` between sections, `mb-3` between a section title and its content — same scale on every section. Inside a card's internal list: `space-y-3`/`space-y-3.5`.
- Header bars: `h-12` (page header, sidebar logo), `h-11` (card/table header).
- Font sizes — the entire scale is the five `@theme` tokens: `text-kpi`, `text-title`, `text-body`, `text-caption`, `text-micro`. Do not introduce new sizes or arbitrary `text-[Npx]` values.
- Headings are semantic `h1`/`h2` with `text-balance`. Dates and comparable numbers get `tabular-nums`.
- Labels/questions recede visually (small, secondary ink); the answer/content is the visual protagonist.
- A screen may declare an explicit, documented exception to this scale (e.g. an ultra-dense matrix), but the exception must be written down where the screen lives and ideally pinned by a test — never silently drift.

### Layout & Responsive

- Layout responds to **container width**; chrome (nav pattern, target size, popover vs sheet) responds to **input method**. Never bind both to one viewport breakpoint.
- Inside a region (card, form, table, panel) use `@container` on the wrapper and `@md:`-style variants on descendants. Viewport `md:`/`lg:` only for the page skeleton: whether the sidebar exists, header arrangement, sticky bars.
- Grids: `repeat(auto-fit, minmax(Npx, 1fr))`. Column count is derived from available space, never declared per breakpoint. The `grid-cols-1 md:grid-cols-2 lg:grid-cols-4` ladder is forbidden.
- Narrow ≠ mobile. An 800px desktop window keeps the density scale, hover states, and mouse chrome. Phone-only treatment (hamburger, bottom nav, sheets, 44px targets) is gated by `pointer-coarse:` (`@media (pointer: coarse)`); Tailwind v4 already scopes `hover:` to `@media (hover: hover)`.
- Regions degrade independently: sidebar → icon rail → hidden; table → hide low-priority columns → horizontal scroll (never row-to-card); grid → fewer columns. One region collapsing must not collapse another.
- No horizontal overflow at any width. `h-dvh`/`min-h-dvh`, not `h-screen` (`100vh`).
- Type and spacing stay on the fixed scale — no `clamp()`. Width changes column count and region visibility, nothing else.
- Verify in one window at 375 / 800 / 1280. 800 must read as a narrow desktop, not a phone.

## Anti-slop (never do this)

- **No left accent border** on cards, rows, or nav items — ever, on any page.
- No drop shadows beyond `shadow-card` (dark mode has none at all). A sticky header over scrolling content separates with a hairline (`border-b`), not a shadow.
- No gradient fills (backgrounds, text, borders), no decorative icons beyond the project's icon set (`components.json#iconLibrary`).
- No new font sizes, weights, or spacing values outside the scale above.
- Margin/padding must be consistent with sibling components of the same purpose; misaligned spacing is a bug, not a nit.
- **Stat tiles / big numbers.** A row of label + huge number is the signature AI-slop dashboard move. Rules:
  - Big-number treatment (`text-kpi`) is EARNED by context: the tile must carry a delta vs previous period, a target, or a sparkline. A bare number with no context cannot be a tile — demote it to a table/list row.
  - Cumulative counters (total tokens, total requests, all-time sums) are logs, not KPIs — they belong in a table row, never a stat tile.
  - Never repeat as a big number what a table on the same screen already shows. The tile row is not a table header.
- **Avatar initials / name placeholders.** A circle holding one Hangul syllable, surname or given name (`김`, `민`), identifies no one: too many people share each syllable. Rules:
  - If the people data has no photo field, or most records leave it empty (meeting participants, recordings, imported contacts), draw no avatars. List the names as text, the first one or two and then `+N`, with the full list one click or tap away.
  - If photos are the norm and one is missing, a Korean name's `AvatarFallback` holds a neutral person icon from the project's icon set. It may hold the two-syllable given name instead only when all three hold: the circle fits two syllables at `text-micro` or larger; the data already stores the given name in its own field (never split a full name, since 남궁·제갈·선우 are two-syllable surnames); and the service supports a small fixed set of languages, such as Korean only or Korean and English.

## Accessibility (required, not optional)

- Every interactive element has BOTH a visible focus ring (shadcn's `focus-visible:ring-*` + `focus-visible:ring-ring/*` pair) and a `hover:` state. `outline-none`/`outline-hidden` without a visible focus replacement is forbidden.
- Long-text containers get `wrap-break-word` (`wrap-anywhere` in table cells, where `break-word` cannot shrink the column); flex/grid children that hold text get `min-w-0` (the classic invisible-overflow bug).
- Every clickable element shows `cursor-pointer` — buttons, links styled as buttons, clickable rows/cards/list items, tabs, chips, icon buttons. `<button>` is NOT exempt, because its default cursor is `default`: one base rule covers it (`button:not(:disabled), [role="button"]:not(:disabled) { cursor: pointer }`). Disabled controls get `cursor-not-allowed`; text inputs keep the I-beam.
- Every screen is usable on mobile web (375px wide, touch, no hover): nothing is hover-only — an action revealed on `hover:` is also always visible on touch (`pointer-coarse:opacity-100`) or reachable from a tap menu, and horizontal scroll lives only inside tables/code (`overflow-x-auto` on that container), never on the page. Check 375px before calling a screen done.
- Recommended target size: 44×44px under touch (`pointer-coarse:min-h-11`), 24×24px with a fine pointer. A dense table row or toolbar may go smaller. When a small icon needs a bigger target, grow its hit area, not its glyph.
- Color never carries information alone: pair it with text or an icon (status, errors, chart series).
- Color pairs outside the theme table (status, chart, and new semantic colors) meet APCA contrast: Lc 75 (90 preferred) for body text, titles, input values, and tooltips; Lc 60 for other text; Lc 30 for placeholder and disabled text.
- Enlarged text (browser zoom, OS text size) wraps instead of clipping, and button rows stack.
- Decorative elements get `aria-hidden`.
