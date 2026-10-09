---
name: design-frontend-sangrak
description: Use when starting frontend work in a project with no existing design system, when building or theming UI with shadcn/ui or Tailwind CSS, or when asked to review/audit web UI. Default design baseline for new screens, plus container-first responsive rules, URL-first routing, scoped async loading, theme/i18n defaults, and applied UX laws.
metadata:
  author: kargnas
  version: "0.9.1"
  argument-hint: <file-or-pattern>
---

# Design Frontend (Sangrak)

## Review Preflight

When the current request asks for a review or audit:

1. MUST fetch `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md` with WebFetch before writing findings.
2. MUST verify that WebFetch returned the current rule set and output format. If it failed, report the failure instead of writing findings.
3. Read or search the review target and apply both rule sets.

A review without a successful WebFetch call is invalid.

Two modes, both grounded in the same design system below:

- **Build mode** — writing/editing UI code: apply the design system directly.
- **Review mode** — asked to review/audit UI: check code against the design system AND the fetched Vercel guidelines, output findings as terse `file:line` entries.

For transitions, animation, or motion-token work, MUST read and follow the bundled [Transitions.dev guide](sub-skills/transitions-dev/GUIDE.md). This design system wins when its visual, accessibility, review-output, or mutation rules conflict with the bundled guide.

Transition references: [01](sub-skills/transitions-dev/01-card-resize.md), [02](sub-skills/transitions-dev/02-number-pop-in.md), [03](sub-skills/transitions-dev/03-notification-badge.md), [04](sub-skills/transitions-dev/04-text-states-swap.md), [05](sub-skills/transitions-dev/05-menu-dropdown.md), [06](sub-skills/transitions-dev/06-modal.md), [07](sub-skills/transitions-dev/07-panel-reveal.md), [08](sub-skills/transitions-dev/08-page-side-by-side.md).
[09](sub-skills/transitions-dev/09-icon-swap.md), [10](sub-skills/transitions-dev/10-success-check.md), [11](sub-skills/transitions-dev/11-avatar-group-hover.md), [12](sub-skills/transitions-dev/12-error-state-shake.md), [13](sub-skills/transitions-dev/13-input-clear-dissolve.md), [14](sub-skills/transitions-dev/14-skeleton-reveal.md), [15](sub-skills/transitions-dev/15-shimmer-text.md), [16](sub-skills/transitions-dev/16-tabs-sliding.md).
[17](sub-skills/transitions-dev/17-tooltip.md), [18](sub-skills/transitions-dev/18-texts-reveal.md), [19](sub-skills/transitions-dev/19-card-tilt.md), [20](sub-skills/transitions-dev/20-plus-menu-morph.md), [21](sub-skills/transitions-dev/21-accordion.md), [22](sub-skills/transitions-dev/22-toast.md), [23](sub-skills/transitions-dev/23-like-button.md), [24](sub-skills/transitions-dev/24-learn-more-hover.md).
[25](sub-skills/transitions-dev/25-checkbox-check.md), [26](sub-skills/transitions-dev/26-spinning-counter.md), [27](sub-skills/transitions-dev/27-toggle.md), [28](sub-skills/transitions-dev/28-thinking-states.md), [29](sub-skills/transitions-dev/29-reasoning-stream.md), [30](sub-skills/transitions-dev/30-streaming-text.md), [31](sub-skills/transitions-dev/31-matrix-loader.md), [32](sub-skills/transitions-dev/32-banner-stacking.md), [shared motion tokens](sub-skills/transitions-dev/_root.css).

## Stack

Everything below uses shadcn/ui (CLI v4) and Tailwind CSS v4 names.

- **New project:** `npx shadcn@latest init -b base -p mira --pointer` (add `-t next|vite|start|react-router|laravel|astro` when no app exists yet), then `npx shadcn@latest add font-jetbrains-mono`. That font item also rewrites the `html` rule in `@layer base` to `@apply font-mono`; set it back to `@apply font-sans` so mono stays limited to numbers and identifiers. Mira already sets Inter as `--font-sans`, and `--pointer` writes the button cursor rule. Then apply the theme below.
- **Existing project with `components.json`:** run `npx shadcn@latest info --json` first and follow its base (`base`/`radix`/`aria`), style, icon library, and Tailwind version. Never re-run `init` or switch presets unasked.
- **Legacy markers:** if the theme lives in `tailwind.config.*`, the CSS starts with `@tailwind base`, `lib/utils.ts` builds `cn` from `clsx` + `tailwind-merge`, `components.json#style` is `default`/`new-york`, or the CSS defines `--bg`/`--panel`/`--ink`, read [references/legacy.md](references/legacy.md) before writing code.
- Component APIs, composition, and CLI flags come from `npx shadcn@latest docs <component>` (or the official shadcn skill when installed). This file only adds the design system on top.

### After every `shadcn add`

Generated components are project code. Bring them onto this system before using them:

| Generated | Change to |
|---|---|
| `import { cn } from "cn"` | `import { cn } from "@/lib/utils"` (the `utils` alias), the instance that knows the type scale |
| `text-xs/relaxed`, `text-xs`, `text-sm`, `text-base`, `text-[0.625rem]` | The role's token from the type scale below; keep line-height modifiers such as `/relaxed` |
| `transition-all` (Button, Badge, Tabs, Sidebar) | `transition-colors`, or Tailwind's default `transition` when a transform animates |
| `shadow-md`/`shadow-lg` (menus, Select, Sheet, Toast) | `shadow-card dark:shadow-none` |
| `p-6` (Sheet, Empty), card `--spacing(5)` or more (Vega, Rhea) | `p-4`, `--spacing(4)` |
| `Kbd` with `font-sans` and no border | The badge style in Keyboard hints |
| `data-active:bg-sidebar-accent` on `SidebarMenuButton` | `data-active:bg-primary/10 dark:data-active:bg-primary/14` |

## Design System

### Theme tokens (`:root` / `.dark`)

Set these values in the `:root` and `.dark` blocks that `init` generated. Tokens not listed (`--destructive`, `--chart-*`, `--radius`) keep the preset values.

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
- A new semantic color follows shadcn's pair convention: `--name` and `--name-foreground` in `:root` and `.dark`, exposed with `@theme inline { --color-name: var(--name); }`.

Add the type scale and the only allowed elevation to the same CSS file:

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

Tailwind inlines theme shadows into the utility, so dark mode drops the card shadow with `dark:shadow-none`, not by redefining `--shadow-card`.

Register the scale with `cn` too. The default `cn` reads unknown `text-*` names as colors, so `cn("text-primary-foreground text-body")` silently drops one of the two classes:

```ts
// lib/utils.ts
import { createCn } from "cn/config"

export const cn = createCn({
  extend: { classGroups: { "font-size": [{ text: ["kpi", "title", "body", "caption", "micro"] }] } },
})
```

New projects adopt these values as-is; existing projects with their own tokens keep theirs — the density and anti-slop rules still apply.

### Fonts

- Inter (`font-sans`, UI text), JetBrains Mono (`font-mono` — numbers/ids/paths/status badges), Noto Sans KR/SC/JP appended to the `--font-sans` stack as CJK fallback.
- Numbers, identifiers, file paths, and status badges are ALWAYS `font-mono` — proportional digits jitter when values update.

### Status colors

- live/streaming = emerald, neutral/ok = `text-muted-foreground`, error/failure = `destructive`.
- Quota/progress bars add amber for the 20–50% remaining band.

### Density scale

- Padding: boxes/cards/bands use the SAME value on all four sides — large cards `p-4`, dense boards/list items `p-3` (shadcn `Card` default and `size="sm"`). Asymmetric padding only on small buttons/chips (and table cells `px-4 py-2`).
- **Padding/gap tokens never exceed 16px (=4)** — `p-5`/`p-6`/`gap-5`+ and `--spacing(5)`+ are forbidden. Gaps: `gap-2/3/4`.
- Vertical rhythm: `mt-8` between sections, `mb-3` between a section title and its content — same scale on every section. Inside a card's internal list: `space-y-3`/`space-y-3.5`.
- Header bars: `h-12` (page header, sidebar logo), `h-11` (card/table header).
- Font sizes — the entire scale is the five `@theme` tokens: `text-kpi`, `text-title`, `text-body`, `text-caption`, `text-micro`. Do not introduce new sizes or arbitrary `text-[Npx]` values.
- Headings are semantic `h1`/`h2` with `text-balance`. Dates and comparable numbers get `tabular-nums`.
- Labels/questions recede visually (small, secondary ink); the answer/content is the visual protagonist.
- A screen may declare an explicit, documented exception to this scale (e.g. an ultra-dense matrix), but the exception must be written down where the screen lives and ideally pinned by a test — never silently drift.

### Keyboard hints

- The rule is about labeling, not about adding shortcuts: **any action that IS keyboard-accessible displays its shortcut inline** as a `<kbd>` badge (`⌘K` inside a search field, `⌘↵` next to a submit label). No hidden shortcuts — if it works from the keyboard, the UI says so.
- Inventing new shortcuts is fine too, but the key map MUST mirror a well-known global product in the same category (Linear/Slack/Gmail/GitHub conventions — `⌘K` command palette, `⌘↵` submit, `/` focus search, `j`/`k` navigate). Never invent a novel binding for an action those products already have a convention for.
- Badge: shadcn `Kbd`/`KbdGroup` restyled to `font-mono text-micro text-muted-foreground bg-muted border border-border` with a small radius. It reads as a quiet affordance, not a button. Inside a search field it sits in an `InputGroupAddon`.
- Platform-aware modifier: `⌘` on macOS, `Ctrl` elsewhere (detect via `navigator.platform`/userAgentData).
- A displayed shortcut MUST actually work — wire the handler in the same PR as the badge. A dead `<kbd>` hint is worse than none.
- Badges are decorative for screen readers: `aria-hidden` on the `<kbd>`, put the shortcut in the control's `aria-keyshortcuts` instead.

### Layout & Responsive

- Layout responds to **container width**; chrome (nav pattern, target size, popover vs sheet) responds to **input method**. Never bind both to one viewport breakpoint.
- Inside a region (card, form, table, panel) use `@container` on the wrapper and `@md:`-style variants on descendants. Viewport `md:`/`lg:` only for the page skeleton: whether the sidebar exists, header arrangement, sticky bars.
- Grids: `repeat(auto-fit, minmax(Npx, 1fr))`. Column count is derived from available space, never declared per breakpoint. The `grid-cols-1 md:grid-cols-2 lg:grid-cols-4` ladder is forbidden.
- Narrow ≠ mobile. An 800px desktop window keeps the density scale, hover states, and mouse chrome. Phone-only treatment (hamburger, bottom nav, sheets, 44px targets) is gated by `pointer-coarse:` (`@media (pointer: coarse)`); Tailwind v4 already scopes `hover:` to `@media (hover: hover)`.
- Regions degrade independently: sidebar → icon rail → hidden; table → hide low-priority columns → horizontal scroll (never row-to-card); grid → fewer columns. One region collapsing must not collapse another.
- No horizontal overflow at any width. `h-dvh`/`min-h-dvh`, not `h-screen` (`100vh`).
- Type and spacing stay on the fixed scale — no `clamp()`. Width changes column count and region visibility, nothing else.
- Verify in one window at 375 / 800 / 1280. 800 must read as a narrow desktop, not a phone.

### Routing & URL

- **URL first.** User intent (tab, filter, sort, page, selected item, open panel) writes the URL; the UI is a function of the URL and re-renders from it. Never mutate state and then "sync" the URL afterwards — no parallel `useState` copy of anything the URL already says.
- A screen without a route is unfinished: every new page, tab, panel, and modal gets its route in the same PR. Verify by pasting the URL into a fresh tab.
- Navigation is `<a>`/`<Link>` (Cmd-click works); opening a modal/panel pushes history so Back closes it, filter/sort changes replace.
- A button-styled link stays a link: `<Link className={buttonVariants({ variant: "outline" })}>`. On Base UI never pass `render={<a />}` to `Button`, because it forces `role="button"`; on Radix, wrap the `<Link>` in `<Button asChild>`.

### Loading Scope

- Scope pending UI to the smallest region invalidated by the request: a tab replaces its panel, a filter or page change replaces its results, and a chart selection replaces only the dependent chart. Keep the app shell, navigation, headers, and independent sibling regions mounted.
- A router or network request does not by itself justify a page loader. Whole-page initialization is reserved for the first load when no stable shell or useful content can render. Never subscribe a page to every router/network start event and swap the entire page for a spinner.
- Show pending feedback (`Spinner`) at the initiating control or inside the affected region, mark that region with `aria-busy`, and disable only controls that would conflict with the in-flight request.
- Request only the data the interaction invalidates (`only` for Inertia, a scoped query key, or the framework equivalent). When stale data must disappear, replace only that region and preserve its approximate size to avoid layout shifts.

### Theme & Language

- Theme selector is three-way `System / Light / Dark`, default System (`prefers-color-scheme`), persisted; the `.dark` class on `<html>` drives the tokens above through shadcn's `@custom-variant dark (&:is(.dark *))`. Nothing ships light-only.
- Language selector lists `Auto` first (from `navigator.languages`, never IP), then each supported language; default Auto, persisted.
- No hardcoded UI strings, ever — internal tools and prototypes included. Every user-visible string goes through the i18n layer (`t()`), one translation file per locale, keys added in the same PR as the UI.

## UX Laws (applied)

One decision rule per law plus the code smell that violates it. No theory — only the ruling.

| Law | Rule | Smell |
|---|---|---|
| Fitts | Actions sit where the cursor already is: row actions on the row, the whole row is the target, destructive kept apart from primary | 16px icon button with no padding; Delete beside Save |
| Hick + progressive disclosure | One primary action per view, the rest behind `…`/expander; defaults cover the 80% case, advanced options hidden until asked | three equal-weight buttons; every option visible on first load |
| Miller + chunking | Past ~7 items, group: auto-group by `group` key, 5+ chips become a parent chip + expandable sub-chips, long forms become steps | 12 flat chips; 20 rows with no sections |
| Gestalt (proximity, common region) | Spacing is grouping: related pairs sit closer than unrelated ones; a panel bg or hairline groups better than a border | equal gap between label→input and between unrelated fields |
| Jakob | Copy Linear/Slack/GitHub/Gmail for nav placement, wording, empty and error states (shortcuts: see Keyboard hints) | invented term or gesture for something those products already name |
| Von Restorff | Exactly one thing stands out: one `primary`-filled button per view; red only for errors/destructive | two primary buttons visible; decorative red |
| Feedback (Doherty, Nielsen 1, Zeigarnik) | Pressed state <100ms, progress after 400ms, optimistic UI for reversible ops, `Skeleton` only on first load; every async action shows pending/success/error where it was triggered; multi-step shows position; unsaved drafts are marked | `await` with no pending state; success visible only after reload; wizard without step indicator |
| User control (Nielsen 3) | Undo beats confirm: reversible ops get an undo toast (`sonner` or Base UI `toast` with an Undo action, 5–10s), confirm only for the irreversible, never both; the server rejects duplicate submits | `window.confirm` on archive; double-click creates two rows |
| Errors (Nielsen 5, 9, Postel) | Validate on blur, message at the field (`Field` + `FieldError`, `aria-invalid` on the control), says what to do; accept messy input and normalize (trim, pasted whitespace, both date formats) instead of rejecting | errors only on submit at the top; "Invalid input"; disabled submit with no reason |
| Recognition over recall (Nielsen 6) | Current state always visible: active filters as chips, selected value in the trigger, format example in the placeholder, recents first; raw values shown, derived values alongside | filter applied but not displayed; rounded number hiding the raw |
| Tesler | Complexity moves, it doesn't vanish: move it into the system (smart defaults, derive platform/timezone/group, remember the last choice) | asking for a value the app already knows |

## Anti-slop (never do this)

- **No left accent border** on cards, rows, or nav items — ever, on any page.
- No drop shadows beyond `shadow-card` (dark mode has none at all).
- No gradients, no decorative icons beyond the project's icon set (`components.json#iconLibrary`).
- shadcn `Chart` (Recharts) for multi-series dashboards; inline SVG only for sparklines.
- No new font sizes, weights, or spacing values outside the scale above.
- Margin/padding must be consistent with sibling components of the same purpose; misaligned spacing is a bug, not a nit.
- Loading states: distinguish initializing (no data yet) from loading (refresh); show an animated spinner in the scope defined above; don't leave stale data visible during a new load unless explicitly requested.
- **Stat tiles / big numbers.** A row of label + huge number is the signature AI-slop dashboard move. Rules:
  - Big-number treatment (`text-kpi`) is EARNED by context: the tile must carry a delta vs previous period, a target, or a sparkline. A bare number with no context cannot be a tile — demote it to a table/list row.
  - Cumulative counters (total tokens, total requests, all-time sums) are logs, not KPIs — they belong in a table row, never a stat tile.
  - Never repeat as a big number what a table on the same screen already shows. The tile row is not a table header.
- **Avatar initials / name placeholders.** A circle holding one Hangul syllable, surname or given name (`김`, `민`), identifies no one: too many people share each syllable. Rules:
  - If the people data has no photo field, or most records leave it empty (meeting participants, recordings, imported contacts), draw no avatars. List the names as text, the first one or two and then `+N`, with the full list one click or tap away.
  - If photos are the norm and one is missing, a Korean name's `AvatarFallback` holds a neutral person icon from the project's icon set. It may hold the two-syllable given name instead only when all three hold: the circle fits two syllables at `text-micro` or larger; the data already stores the given name in its own field (never split a full name, since 남궁·제갈·선우 are two-syllable surnames); and the service supports a small fixed set of languages, such as Korean only or Korean and English.

## Interaction & Accessibility (required, not optional)

- Every interactive element has BOTH a visible focus ring (shadcn's `focus-visible:ring-*` + `focus-visible:ring-ring/*` pair) and a `hover:` state. `outline-none`/`outline-hidden` without a visible focus replacement is forbidden.
- Long-text containers get `wrap-break-word` (`wrap-anywhere` in table cells, where `break-word` cannot shrink the column); flex/grid children that hold text get `min-w-0` (the classic invisible-overflow bug).
- `transition-all` is forbidden — name the transitioned properties (`transition-colors`, `transition-opacity`). Respect `motion-reduce:`.
- Tap targets get `touch-manipulation`.
- Every clickable element shows `cursor-pointer` — buttons, links styled as buttons, clickable rows/cards/list items, tabs, chips, icon buttons. Tailwind v4 Preflight sets `cursor: default` on `<button>`, so `<button>` is NOT exempt: `init --pointer` writes the base rule (`button:not(:disabled), [role="button"]:not(:disabled) { cursor: pointer }`); a project created without it adds the rule once, or the class per element. Disabled controls get `cursor-not-allowed`; text inputs keep the I-beam.
- Every screen is usable on mobile web (375px wide, touch, no hover): tap targets are at least 44×44px under touch (`pointer-coarse:min-h-11`, dense table rows included — Mira ships 28px controls), nothing is hover-only — an action revealed on `hover:` is also always visible on touch (`pointer-coarse:opacity-100`) or reachable from a tap menu, and horizontal scroll lives only inside tables/code (`overflow-x-auto` on that container), never on the page. Check 375px before calling a screen done.
- Decorative elements get `aria-hidden`.

## Review Mode

1. Complete the Review Preflight above.

   ```
   https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
   ```

2. Read the specified files (or ask which files to review if none given).
3. Check against BOTH rule sets: the fetched Vercel guidelines and the Design System + UX Laws + Anti-slop sections above.
4. Output findings in terse `file:line` format. When the two rule sets conflict, this file wins.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Inventing a new font size "just for this label" | Use the nearest token on the scale; if truly needed, document the exception |
| `text-[13px]`-style arbitrary sizes | `text-body` and the other `@theme` scale tokens |
| Proportional font for a KPI number | `font-mono` (JetBrains Mono) |
| Card shadow in dark mode | `shadow-card dark:shadow-none` |
| Left accent border to mark "active" nav item | `bg-primary/10 dark:bg-primary/14` background instead |
| Avatar letters cut from a Korean name string (`name[0]`, `name.slice(1)`) | Names as text when most people have no photo; otherwise a person icon (given-name exception under Anti-slop) |
| Brand color written into `--accent` | Brand goes in `--primary`; shadcn's `--accent` is the hover surface |
| `--bg`/`--panel`/`--ink` defined next to shadcn tokens | Use the shadcn names; map old ones with [references/legacy.md](references/legacy.md) |
| Using a shadcn component exactly as generated | Apply the "After every `shadcn add`" table first |
| Reviewing only against Vercel guidelines | The local design system is half the review |
| `p-5`/`p-6` on a card or page | Padding cap is 16px — `p-4` or below; `Card size="sm"` for `p-3` |
| `outline-none` to "clean up" focus ring | Keep shadcn's `focus-visible:ring-*` pair |
| `transition-all` for a quick hover effect | Name the properties (`transition-colors`, `transition-opacity`) |
| `<button>` without `cursor-pointer` | `init --pointer`, or add the base rule once |
| `<Button render={<a />}>` for navigation (Base UI) | `buttonVariants()` on a `<Link>` |
| `grid-cols-1 lg:grid-cols-3` on a table + sidebar body | Collapse per region at content-min width: `minmax`/`auto-fit` or `@container` |
| Row action icons that appear on `group-hover` only | Always visible on touch (`pointer-coarse:opacity-100`) or moved into a tap-reachable menu |
| `grid-cols-1 md:grid-cols-2 lg:grid-cols-4` | `grid-cols-[repeat(auto-fit,minmax(Npx,1fr))]` — let the count derive |
| Hamburger menu on an 800px desktop window | Gate phone chrome behind `pointer-coarse:`, not a width |
| `md:flex-row` inside a card that lives in a sidebar | `@container` on the wrapper, `@md:flex-row` on the child |
| `window.confirm` on a reversible action | Undo toast; confirm only when nothing can bring it back |
| Small thumbnail with no enlarge | Click opens the original |
| Result panel with no export | Copy as Markdown |
| `setFilter(x)` then `router.push(?filter=x)` | Push the URL; derive the filter from `searchParams` |
| New tab/panel component with no route | Register the route in the same PR; open the URL in a fresh tab to verify |
| Every router request replaces the page with one spinner | Track pending state at the interaction and replace only the data-dependent region |
| Two-way `Light / Dark` toggle, or a language list without Auto | `System / Light / Dark` and `Auto` + languages, System/Auto as defaults |
