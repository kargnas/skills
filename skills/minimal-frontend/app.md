# App UI

Rules for screens, components, and flows inside a product, and for UI reviews. They add to the design system in SKILL.md and use its names.

## Review Preflight

When the current request asks for a review or audit:

1. MUST fetch `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md` with WebFetch before writing findings.
2. MUST verify that WebFetch returned the current rule set and output format. If it failed, report the failure instead of writing findings.
3. Read or search the review target and apply both rule sets.

A review without a successful WebFetch call is invalid.

Two modes, both grounded in the design system in SKILL.md and the rules below:

- **Build mode** — writing/editing UI code: apply the design system directly.
- **Review mode** — asked to review/audit UI: check code against the design system AND the fetched Vercel guidelines, output findings as terse `file:line` entries.

Before building or reviewing any of these, MUST read [references/component-policies.md](references/component-policies.md) for their counts, behavior, and copy limits: badges, dialogs, sheets, side panels, button rows, tabs, back and close navigation, pagination, selection controls (select, radio, checkbox, switch, chips, segmented control, slider, stepper), date and time pickers, forms, lists, cards, images, accordions, dividers, empty and result screens, and icons.

For transitions, animation, or motion-token work, MUST read and follow the bundled [Transitions.dev guide](sub-skills/transitions-dev/GUIDE.md). This design system wins when its visual, accessibility, review-output, or mutation rules conflict with the bundled guide.

Transition references: [01](sub-skills/transitions-dev/01-card-resize.md), [02](sub-skills/transitions-dev/02-number-pop-in.md), [03](sub-skills/transitions-dev/03-notification-badge.md), [04](sub-skills/transitions-dev/04-text-states-swap.md), [05](sub-skills/transitions-dev/05-menu-dropdown.md), [06](sub-skills/transitions-dev/06-modal.md), [07](sub-skills/transitions-dev/07-panel-reveal.md), [08](sub-skills/transitions-dev/08-page-side-by-side.md).
[09](sub-skills/transitions-dev/09-icon-swap.md), [10](sub-skills/transitions-dev/10-success-check.md), [11](sub-skills/transitions-dev/11-avatar-group-hover.md), [12](sub-skills/transitions-dev/12-error-state-shake.md), [13](sub-skills/transitions-dev/13-input-clear-dissolve.md), [14](sub-skills/transitions-dev/14-skeleton-reveal.md), [15](sub-skills/transitions-dev/15-shimmer-text.md), [16](sub-skills/transitions-dev/16-tabs-sliding.md).
[17](sub-skills/transitions-dev/17-tooltip.md), [18](sub-skills/transitions-dev/18-texts-reveal.md), [19](sub-skills/transitions-dev/19-card-tilt.md), [20](sub-skills/transitions-dev/20-plus-menu-morph.md), [21](sub-skills/transitions-dev/21-accordion.md), [22](sub-skills/transitions-dev/22-toast.md), [23](sub-skills/transitions-dev/23-like-button.md), [24](sub-skills/transitions-dev/24-learn-more-hover.md).
[25](sub-skills/transitions-dev/25-checkbox-check.md), [26](sub-skills/transitions-dev/26-spinning-counter.md), [27](sub-skills/transitions-dev/27-toggle.md), [28](sub-skills/transitions-dev/28-thinking-states.md), [29](sub-skills/transitions-dev/29-reasoning-stream.md), [30](sub-skills/transitions-dev/30-streaming-text.md), [31](sub-skills/transitions-dev/31-matrix-loader.md), [32](sub-skills/transitions-dev/32-banner-stacking.md), [shared motion tokens](sub-skills/transitions-dev/_root.css).

## Stack

Everything below uses shadcn/ui (CLI v4) and Tailwind CSS v4 names.

- **New project:** `npx shadcn@latest init -b base -p mira --pointer` (add `-t next|vite|start|react-router|laravel|astro` when no app exists yet), then `npx shadcn@latest add font-jetbrains-mono`. That font item also rewrites the `html` rule in `@layer base` to `@apply font-mono`; set it back to `@apply font-sans` so mono stays limited to numbers and identifiers. Mira already sets Inter as `--font-sans`, and `--pointer` writes the button cursor rule. Then MUST wire the theme (Theme wiring below) before adding components.
- **Existing project with `components.json`:** run `npx shadcn@latest info --json` first and follow its base (`base`/`radix`/`aria`), style, icon library, and Tailwind version. Never re-run `init` or switch presets unasked.
- **Legacy markers:** if the theme lives in `tailwind.config.*`, the CSS starts with `@tailwind base`, `lib/utils.ts` builds `cn` from `clsx` + `tailwind-merge`, `components.json#style` is `default`/`new-york`, or the CSS defines `--bg`/`--panel`/`--ink`, read [references/legacy.md](references/legacy.md) before writing code.
- Component APIs, composition, and CLI flags come from `npx shadcn@latest docs <component>` (or the official shadcn skill when installed). This skill only adds the design system on top.
- shadcn `Chart` (Recharts) for multi-series dashboards; inline SVG only for sparklines.

### Theme wiring

Set the theme token values from SKILL.md in the `:root` and `.dark` blocks that `init` generated. Tokens not listed (`--destructive`, `--chart-*`, `--radius`) keep the preset values.

- A new semantic color is exposed with `@theme inline { --color-name: var(--name); }`.
- Add the `@theme` block from SKILL.md (type scale and `--shadow-card`) to the same CSS file.

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

### After every `shadcn add`

Generated components are project code. Bring them onto this system before using them:

| Generated | Change to |
|---|---|
| `import { cn } from "cn"` | `import { cn } from "@/lib/utils"` (the `utils` alias), the instance that knows the type scale |
| `text-xs/relaxed`, `text-xs`, `text-sm`, `text-base`, `text-[0.625rem]` | The role's token from the type scale in SKILL.md; keep line-height modifiers such as `/relaxed` |
| `transition-all` (Button, Badge, Tabs, Sidebar) | `transition-colors`, or Tailwind's default `transition` when a transform animates |
| `shadow-md`/`shadow-lg` (menus, Select, Sheet, Toast) | `shadow-card dark:shadow-none` |
| `p-6` (Sheet, Empty), card `--spacing(5)` or more (Vega, Rhea) | `p-4`, `--spacing(4)` |
| `Kbd` with `font-sans` and no border | The badge style in Keyboard hints |
| `data-active:bg-sidebar-accent` on `SidebarMenuButton` | `data-active:bg-primary/10 dark:data-active:bg-primary/14` |
| `active:not-aria-[haspopup]:translate-y-px` on `Button` | The press feedback in Interaction |
| `AlertDialogCancel` defaulting to `variant = "outline"` | `variant = "secondary"`, because outline pairs only with outline |
| `showOutsideDays = true` in `Calendar` | `showOutsideDays = false`, so days of other months stay blank |

## Keyboard hints

- The rule is about labeling, not about adding shortcuts: **any action that IS keyboard-accessible displays its shortcut inline** as a `<kbd>` badge (`⌘K` inside a search field, `⌘↵` next to a submit label). No hidden shortcuts — if it works from the keyboard, the UI says so.
- Inventing new shortcuts is fine too, but the key map MUST mirror a well-known global product in the same category (Linear/Slack/Gmail/GitHub conventions — `⌘K` command palette, `⌘↵` submit, `/` focus search, `j`/`k` navigate). Never invent a novel binding for an action those products already have a convention for.
- Badge: shadcn `Kbd`/`KbdGroup` restyled to `font-mono text-micro text-muted-foreground bg-muted border border-border` with a small radius. It reads as a quiet affordance, not a button. Inside a search field it sits in an `InputGroupAddon`.
- Platform-aware modifier: `⌘` on macOS, `Ctrl` elsewhere (detect via `navigator.platform`/userAgentData).
- A displayed shortcut MUST actually work — wire the handler in the same PR as the badge. A dead `<kbd>` hint is worse than none.
- Badges are decorative for screen readers: `aria-hidden` on the `<kbd>`, put the shortcut in the control's `aria-keyshortcuts` instead.

## Routing & URL

- **URL first.** User intent (tab, filter, sort, page, selected item, open panel) writes the URL; the UI is a function of the URL and re-renders from it. Never mutate state and then "sync" the URL afterwards — no parallel `useState` copy of anything the URL already says.
- A screen without a route is unfinished: every new page, tab, panel, and modal gets its route in the same PR. Verify by pasting the URL into a fresh tab.
- Navigation is `<a>`/`<Link>` (Cmd-click works); opening a modal/panel pushes history so Back closes it, filter/sort changes replace.
- A button-styled link stays a link: `<Link className={buttonVariants({ variant: "outline" })}>`. On Base UI never pass `render={<a />}` to `Button`, because it forces `role="button"`; on Radix, wrap the `<Link>` in `<Button asChild>`.

## Loading Scope

- Scope pending UI to the smallest region invalidated by the request: a tab replaces its panel, a filter or page change replaces its results, and a chart selection replaces only the dependent chart. Keep the app shell, navigation, headers, and independent sibling regions mounted.
- A router or network request does not by itself justify a page loader. Whole-page initialization is reserved for the first load when no stable shell or useful content can render. Never subscribe a page to every router/network start event and swap the entire page for a spinner.
- Show pending feedback (`Spinner`) at the initiating control or inside the affected region, mark that region with `aria-busy`, and disable only controls that would conflict with the in-flight request.
- Request only the data the interaction invalidates (`only` for Inertia, a scoped query key, or the framework equivalent). When stale data must disappear, replace only that region and preserve its approximate size to avoid layout shifts.
- Long waits escalate after the 400ms delay in UX Laws. After 4s, add a status line that says what is happening. After 10s, show determinate progress and an estimate when the task reports progress. After 1 minute, offer to continue in the background and to cancel.
- A wait that can hang (fetching location, external verification) gets a timeout that ends in an error with a retry.
- `Skeleton` (first load only, as in UX Laws) fits a known layout, such as repeated lists and fixed layouts, and matches the real content's size, line height, and radius. `Spinner` fits an unknown layout, saves, and partial refreshes. One region never shows both.
- A plain data load needs no success message; the data is the result.
- Loading states: distinguish initializing (no data yet) from loading (refresh); show an animated spinner in the scope defined here; don't leave stale data visible during a new load unless explicitly requested.

## Theme & Language

- The theme selector (SKILL.md, Theme tokens) sets the `.dark` class on `<html>`, which drives the tokens through shadcn's `@custom-variant dark (&:is(.dark *))`.
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

## Interaction (required, not optional)

- Press feedback changes only the surface color, never the text or icon color. `active:` reuses the variant's hover surface instead of a new color, and ghost elements get that surface too, so a mouse user sees one style on hover and on press.
- An element whose color already means its state (`Switch`, a selected tab or chip) shows a press by scale only.
- Press scale moves a fixed 2px, not a fixed ratio: `scale = (basis - 2) / basis`, where `basis = max(height, width / 4, 24)` in px. A 32×32 icon button presses to `scale-[0.938]` and a 120×48 button to `scale-[0.958]`. Color and scale share one transition (Tailwind's default `transition`, 150ms) and start together.
- Only the pressed element shrinks. A checkbox inside a shrinking row doesn't shrink on its own, and a card with several equal actions (open, like, save) lets only the pressed button react. Loading and disabled elements don't shrink, and `motion-reduce:` drops the scale but keeps the color change.
- A loading button ignores repeat activation. It stays enabled only when a click must still do something during loading (cancel, stop); otherwise it is disabled.
- `transition-all` is forbidden — name the transitioned properties (`transition-colors`, `transition-opacity`). Respect `motion-reduce:`.
- Tap targets get `touch-manipulation`.
- Tailwind v4 Preflight sets `cursor: default` on `<button>`. `init --pointer` writes the pointer-cursor base rule from SKILL.md (Accessibility); a project created without it adds the rule once, or the class per element.
- Every pinch or drag action also works with a tap or a click.
- A one-shot animation (not a loading indicator) stays under 2s or offers a skip. Nothing flashes more than 3 times per second. Media doesn't autoplay by default; media that must autoplay starts muted, and sound that plays longer than 3s gets a pause, stop, or volume control.
- Errors and status changes that appear in place are announced: `FieldError` has `role="alert"`, and other async results go in an `aria-live` region.

## UI Copy

These rules hold in every language. A `한국어의 경우:` line adds the Korean form.

- Use plain, familiar words: a verb over a nominalized phrase (`Can't message this person`, not `Messaging is unavailable`).
  - 한국어의 경우: prefer native words to Sino-Korean nouns ('대화할 수 없어요', not '대화가 불가능합니다').
- Name the user's action and lead with the result, not the data processing (`Review sent`, not `Review submission completed`).
- Name the purpose, not the feature (`Trade via chat`, not `Chat`; `You liked this comment`, not `You pressed Like on this comment`).
- Use the official feature name, never the users' shorthand.
  - 한국어의 경우: '끌어올리기', not '끌올'.
- Phrase positively and avoid double negatives (`You can change this once a month`, not `You can't change this more than once a month`; `Upload complete`, not `Upload didn't fail`).
- Use active voice by default, and passive only when it carries the meaning better, such as when the actor is unknown or irrelevant.
  - 한국어의 경우: no double passive ('보이는', not '보여지는').
- One idea per sentence. Use an exclamation mark only when needed, and never repeat it.
- An error says how to fix it (`The service is temporarily unavailable. Try again in a moment.`, not `Server error`).
- Write counts as numerals (`1 item`).
  - 한국어의 경우: '1개', not '한 개'.
- 한국어의 경우: default to '-요' endings and use the honorific '-시-' only when needed ('등록할 수 있어요', not '등록하실 수 있어요'). Automated messages that call for care use '-니다'.
- Statements and instructions end with a period. Titles, headings, KPI numbers, buttons, menu items, and labels take none. A one-sentence toast has no period; when a toast has two or more sentences, every sentence gets one.
- A button that answers yes or no puts a comma after the answer (`Yes, delete`).
  - 한국어의 경우: '네, 삭제할게요'.
- 한국어의 경우: a feature name or status value is written as one word ('예약중'), and the same words in a sentence are spaced ('예약 중일 때는 채팅할 수 없어요').
- Every label fits on one line without truncation: menu items, tags, badges (2-3 words), toast actions (1-2 words), and bottom tabs (10 Latin characters). A selectable card's description takes at most 2 lines.
  - 한국어의 경우: menu items take 2-6 characters, tags 6-10, and bottom tabs 5.

## Review Mode

1. Complete the Review Preflight above.

   ```
   https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md
   ```

2. Read the specified files (or ask which files to review if none given).
3. Check against BOTH rule sets: the fetched Vercel guidelines, and every section of SKILL.md and this file, plus [references/component-policies.md](references/component-policies.md) for the components in the target.
4. Output findings in terse `file:line` format. When the two rule sets conflict, this design system wins.

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
| Dialog with both a header X and a footer Cancel | Input and edit dialogs: footer Cancel with `showCloseButton={false}`; view dialogs: X only |
| Outline Cancel next to a filled Save | `variant="secondary"` for the dismiss action |
| Phone number split into three inputs | One field with auto-formatting |
| A spinner alone through a long wait | Status line after 4s; determinate progress after 10s when the task reports it |
