---
name: design-frontend-sangrak
description: Use when starting frontend work in a project with no existing design system, or when asked to review/audit web UI. Default design baseline for new screens, plus container-first responsive rules, URL-first routing, theme/i18n defaults, and applied UX laws.
metadata:
  author: kargnas
  version: "0.7.0"
  argument-hint: <file-or-pattern>
---

# Design Frontend (Sangrak)

Two modes, both grounded in the same design system below:

- **Build mode** — writing/editing UI code: apply the design system directly.
- **Review mode** — asked to review/audit UI: check code against the design system AND the fetched Vercel guidelines, output findings as terse `file:line` entries.

## Design System

### Tokens (light / `html.dark`)

| Token | Light | Dark |
|---|---|---|
| `--bg` | `#fafafa` | `#0a0a0b` |
| `--panel` | `#ffffff` | `#141416` |
| `--ink` | `#0f0f10` | `#ededef` |
| `--ink-secondary` | `#6b7280` | `#8a8f98` |
| `--accent` | `#5e6ad2` | `#5e6ad2` |
| `--accent-tint` | `rgba(94,106,210,.10)` | `rgba(94,106,210,.14)` |
| `--hairline` | `#00000014` | `#ffffff14` |
| `--hairline-bright` | `#0000001f` | `#ffffff1f` |
| `--hover-bg` | `rgba(0,0,0,.035)` | `rgba(255,255,255,.05)` |
| `--card-shadow` | `0 1px 2px rgba(0,0,0,.04)` | `none` |

New projects adopt these values as-is; existing projects with their own tokens keep theirs — the density and anti-slop rules still apply.

### Fonts

- Inter (sans, UI text), JetBrains Mono (mono — numbers/ids/paths/status badges), Noto Sans KR/SC/JP (CJK fallback).
- Numbers, identifiers, file paths, and status badges are ALWAYS mono — proportional digits jitter when values update.

### Status colors

- live/streaming = emerald, neutral/ok = ink-secondary, error/failure = red.
- Quota/progress bars add amber for the 20–50% remaining band.

### Density scale

- Padding: boxes/cards/bands use the SAME value on all four sides — large cards `p-4`, dense boards/list items `p-3`. Asymmetric padding only on small buttons/chips (and table cells `px-4 py-2`).
- **Padding/gap tokens never exceed 16px (=4)** — `p-5`/`p-6`/`gap-5`+ are forbidden. Gaps: `gap-2/3/4`.
- Vertical rhythm: `mt-8` between sections, `mb-3` between a section title and its content — same scale on every section. Inside a card's internal list: `space-y-3`/`space-y-3.5`.
- Header bars: `h-12` (page header, sidebar logo), `h-11` (card/table header).
- Font sizes — the entire scale: `text-[24px]` KPI numbers, `text-[14px]` page titles, `text-[13px]` body/nav, `text-[11px]`/`text-[12px]` captions and table headers. Do not introduce new sizes.
- Headings are semantic `h1`/`h2` with `text-balance`. Dates and comparable numbers get `tabular-nums`.
- Labels/questions recede visually (small, secondary ink); the answer/content is the visual protagonist.
- A screen may declare an explicit, documented exception to this scale (e.g. an ultra-dense matrix), but the exception must be written down where the screen lives and ideally pinned by a test — never silently drift.

### Keyboard hints

- The rule is about labeling, not about adding shortcuts: **any action that IS keyboard-accessible displays its shortcut inline** as a `<kbd>` badge (`⌘K` inside a search field, `⌘↵` next to a submit label). No hidden shortcuts — if it works from the keyboard, the UI says so.
- Inventing new shortcuts is fine too, but the key map MUST mirror a well-known global product in the same category (Linear/Slack/Gmail/GitHub conventions — `⌘K` command palette, `⌘↵` submit, `/` focus search, `j`/`k` navigate). Never invent a novel binding for an action those products already have a convention for.
- Badge style: mono font, `text-[11px]`, `--ink-secondary`, subtle bg (`--hover-bg`) with hairline border, small radius. It reads as a quiet affordance, not a button.
- Platform-aware modifier: `⌘` on macOS, `Ctrl` elsewhere (detect via `navigator.platform`/userAgentData).
- A displayed shortcut MUST actually work — wire the handler in the same PR as the badge. A dead `<kbd>` hint is worse than none.
- Badges are decorative for screen readers: `aria-hidden` on the `<kbd>`, put the shortcut in the control's `aria-keyshortcuts` instead.

### Layout & Responsive

- Layout responds to **container width**; chrome (nav pattern, target size, popover vs sheet) responds to **input method**. Never bind both to one viewport breakpoint.
- Inside a region (card, form, table, panel) use `@container` on the wrapper and `@md:`-style variants on descendants. Viewport `md:`/`lg:` only for the page skeleton: whether the sidebar exists, header arrangement, sticky bars.
- Grids: `repeat(auto-fit, minmax(Npx, 1fr))`. Column count is derived from available space, never declared per breakpoint. The `grid-cols-1 md:grid-cols-2 lg:grid-cols-4` ladder is forbidden.
- Narrow ≠ mobile. An 800px desktop window keeps the density scale, hover states, and mouse chrome. Phone-only treatment (hamburger, bottom nav, sheets, 44px targets) is gated by `@media (pointer: coarse)`; hover-only affordances by `@media (hover: hover)`.
- Regions degrade independently: sidebar → icon rail → hidden; table → hide low-priority columns → horizontal scroll (never row-to-card); grid → fewer columns. One region collapsing must not collapse another.
- No horizontal overflow at any width. `100dvh`, not `100vh`.
- Type and spacing stay on the fixed scale — no `clamp()`. Width changes column count and region visibility, nothing else.
- Verify in one window at 375 / 800 / 1280. 800 must read as a narrow desktop, not a phone.
- If `frontend-taste` is also loaded, its "single column below 768px" rule loses to this section.

### Routing & URL

- **URL first.** User intent (tab, filter, sort, page, selected item, open panel) writes the URL; the UI is a function of the URL and re-renders from it. Never mutate state and then "sync" the URL afterwards — no parallel `useState` copy of anything the URL already says.
- A screen without a route is unfinished: every new page, tab, panel, and modal gets its route in the same PR. Verify by pasting the URL into a fresh tab.
- Navigation is `<a>`/`<Link>` (Cmd-click works); opening a modal/panel pushes history so Back closes it, filter/sort changes replace.

### Theme & Language

- Theme selector is three-way `System / Light / Dark`, default System (`prefers-color-scheme`), persisted; `html.dark` drives the token table above. Nothing ships light-only.
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
| Von Restorff | Exactly one thing stands out: one accent-filled button per view; red only for errors/destructive | two accent buttons visible; decorative red |
| Feedback (Doherty, Nielsen 1, Zeigarnik) | Pressed state <100ms, progress after 400ms, optimistic UI for reversible ops, skeleton only on first load; every async action shows pending/success/error where it was triggered; multi-step shows position; unsaved drafts are marked | `await` with no pending state; success visible only after reload; wizard without step indicator |
| User control (Nielsen 3) | Undo beats confirm: reversible ops get an undo toast (5–10s), confirm only for the irreversible, never both; the server rejects duplicate submits | `window.confirm` on archive; double-click creates two rows |
| Errors (Nielsen 5, 9, Postel) | Validate on blur, message at the field, says what to do; accept messy input and normalize (trim, pasted whitespace, both date formats) instead of rejecting | errors only on submit at the top; "Invalid input"; disabled submit with no reason |
| Recognition over recall (Nielsen 6) | Current state always visible: active filters as chips, selected value in the trigger, format example in the placeholder, recents first; raw values shown, derived values alongside | filter applied but not displayed; rounded number hiding the raw |
| Tesler | Complexity moves, it doesn't vanish: move it into the system (smart defaults, derive platform/timezone/group, remember the last choice) | asking for a value the app already knows |

## Anti-slop (never do this)

- **No left accent border** on cards, rows, or nav items — ever, on any page.
- No drop shadows beyond `--card-shadow` (dark mode has none at all).
- No gradients, no decorative icons beyond the established icon set of the project.
- Chart libraries (recharts) for multi-series dashboards; inline SVG only for sparklines.
- No new font sizes, weights, or spacing values outside the scale above.
- Margin/padding must be consistent with sibling components of the same purpose; misaligned spacing is a bug, not a nit.
- Loading states: distinguish initializing (no data yet) from loading (refresh); show an animated spinner; don't leave stale data visible during a new load unless explicitly requested.
- **Stat tiles / big numbers.** A row of label + huge number is the signature AI-slop dashboard move. Rules:
  - Big-number treatment (`text-[24px]`) is EARNED by context: the tile must carry a delta vs previous period, a target, or a sparkline. A bare number with no context cannot be a tile — demote it to a table/list row.
  - Cumulative counters (total tokens, total requests, all-time sums) are logs, not KPIs — they belong in a table row, never a stat tile.
  - Never repeat as a big number what a table on the same screen already shows. The tile row is not a table header.

## Interaction & Accessibility (required, not optional)

- Every interactive element has BOTH `focus-visible:ring` and a `hover:` state. `outline-none` without a visible focus replacement is forbidden.
- Long-text containers get `break-words`; flex/grid children that hold text get `min-w-0` (the classic invisible-overflow bug).
- `transition: all` is forbidden — name the transitioned properties. Respect `motion-reduce`.
- Tap targets get `touch-action: manipulation`.
- Decorative elements get `aria-hidden`.

## Review Mode

1. Fetch fresh guidelines before each review:

   ```
   https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
   ```

   Use WebFetch. The fetched content contains the full rule set and output format.

2. Read the specified files (or ask which files to review if none given).
3. Check against BOTH rule sets: the fetched Vercel guidelines and the Design System + UX Laws + Anti-slop sections above.
4. Output findings in terse `file:line` format. When the two rule sets conflict, this file wins.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Inventing a new font size "just for this label" | Use the nearest size on the scale; if truly needed, document the exception |
| Proportional font for a KPI number | JetBrains Mono |
| Card shadow in dark mode | Dark mode has no shadows |
| Left accent border to mark "active" nav item | Use `--accent-tint` background instead |
| Reviewing only against Vercel guidelines | The local design system is half the review |
| `p-5`/`p-6` on a card or page | Padding cap is 16px — use `p-4` or below |
| `outline-none` to "clean up" focus ring | Replace with `focus-visible:ring` |
| `transition-all` for a quick hover effect | Name the properties (`transition-colors`, `transition-opacity`) |
| `grid-cols-1 md:grid-cols-2 lg:grid-cols-4` | `grid-cols-[repeat(auto-fit,minmax(Npx,1fr))]` — let the count derive |
| Hamburger menu on an 800px desktop window | Gate phone chrome behind `@media (pointer: coarse)`, not a width |
| `md:flex-row` inside a card that lives in a sidebar | `@container` on the wrapper, `@md:flex-row` on the child |
| `window.confirm` on a reversible action | Undo toast; confirm only when nothing can bring it back |
| Small thumbnail with no enlarge | Click opens the original |
| Result panel with no export | Copy as Markdown |
| `setFilter(x)` then `router.push(?filter=x)` | Push the URL; derive the filter from `searchParams` |
| New tab/panel component with no route | Register the route in the same PR; open the URL in a fresh tab to verify |
| Two-way `Light / Dark` toggle, or a language list without Auto | `System / Light / Dark` and `Auto` + languages, System/Auto as defaults |
