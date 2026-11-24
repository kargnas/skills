# Report pages

A report page presents findings, an analysis, or a status to readers who were not part of the work. It is one HTML file with no app shell, router, or build step. Every rule in SKILL.md applies. This file adds how to style the page without shadcn or Tailwind, and how to write it.

## Options

Some rules are optional. Each option is one file in `report-options/`, and each file there has one row in this table.

| Option | Checklist line | Offer when | File |
|---|---|---|---|
| Inline translation | Show quotes in the page's language, with the original in a tooltip | The page quotes words in a language other than the page's language | [`report-options/inline-translation.md`](report-options/inline-translation.md) |
| Speaker photos | Put each speaker's photo before their quotes; the photos go inside the file | The page quotes people, and photos are available for more than half of them | [`report-options/speaker-photos.md`](report-options/speaker-photos.md) |

1. Before writing the page, check each row's "Offer when" against the content.
2. When one or more options apply, MUST ask the user once, as a single multi-select question with one checkbox per applicable option, labeled with its checklist line. Wait for the answer. Skip the question only when the request already says which options to use, or says to use none.
3. Read the file of every checked option in full before writing the page. An unchecked option is not applied, and its file is not read.
4. A checked option's rules win where they differ from this file.

## Plain CSS

- All CSS sits in one `<style>` block. The markup carries no inline style except the width of a bar in a Bars block; a checked option's script may set positions while the page runs. The page loads no CSS framework, utility-class runtime, or component library.
- The theme tokens keep their names and values from SKILL.md, declared as custom properties: light values on `:root`, dark values on `:root:not([data-theme="light"])` inside `@media (prefers-color-scheme: dark)`, and the same dark values on `:root[data-theme="dark"]`. Only the tokens the page uses are declared.
- The type scale and `--shadow-card` from the `@theme` block in SKILL.md are plain custom properties on `:root` here. The two dark rules set `--shadow-card: none`.
- `--font-sans` is Inter, then the Noto Sans family for the page's language, then system fonts. `--font-mono` is JetBrains Mono, then system monospace fonts. One Google Fonts stylesheet link loads weights 400, 500, and 600 of those families; the system fonts keep the page readable offline.
- The theme selector is a native `<select>` with an `aria-label`, in the top bar. A script in `<head>` copies a stored `light` or `dark` choice to `data-theme` on `<html>` before first paint; System removes the attribute. Every storage call sits in `try`/`catch`.

SKILL.md writes sizes and colors as Tailwind names. In the page's CSS they read as follows.

| In SKILL.md | In the page |
|---|---|
| `p-4`, `gap-3`, `mt-8`, `h-12` | One unit is 4px: `16px`, `12px`, `32px`, `48px` |
| `text-body`, `text-caption` | `font-size: var(--text-body)`, `var(--text-caption)` |
| `bg-card`, `text-muted-foreground`, `border` | `var(--card)`, `var(--muted-foreground)`, `1px solid var(--border)` |
| `bg-primary/10 dark:bg-primary/14` | `color-mix(in oklch, var(--primary) 10%, transparent)`, and 14% in the two dark rules |
| `shadow-card dark:shadow-none` | `box-shadow: var(--shadow-card)` |
| `font-mono`, `tabular-nums` | `font-family: var(--font-mono)`, `font-variant-numeric: tabular-nums` |
| `text-balance`, `wrap-anywhere`, `min-w-0` | `text-wrap: balance`, `overflow-wrap: anywhere`, `min-width: 0` |
| `@container`, `@md:` | `container-type: inline-size` on the wrapper, `@container (max-width: …)` on its children |
| `pointer-coarse:` | `@media (pointer: coarse)` |
| The focus ring pair | `:focus-visible { outline: 2px solid var(--ring); outline-offset: 2px; }` |

SKILL.md names two status colors that the theme table gives no value for. A report page has no preset or palette to take them from, so it uses these:

| Token | Light | Dark |
|---|---|---|
| `--destructive` (critical) | `oklch(0.577 0.245 27.325)` | `oklch(0.808 0.114 19.571)` |
| `--warning` (amber) | `oklch(0.6 0.14 70)` | `oklch(0.78 0.14 80)` |

Radius is `8px` on cards, tables, and blocks, `6px` on controls, quotes, and code blocks, and `4px` on badges and inline code.

## Page frame

- `<html lang>` names the language the report is written in. The theme options use the same language.
- Top bar: sticky, full width, `h-12`, `px-4`, `bg-background`, `border-b`. It holds the report title in `text-title` weight 600 on one truncated line at the left, and the theme selector at the right.
- Column: centered, `max-width: 760px`, `p-4`.
- Head: `h1` in `text-title` weight 600, then the three facts from Skeleton as a list without markers in `text-caption text-muted-foreground`.
- Contents: a page with five or more sections lists its `h2` titles as anchor links in one wrapping row under the head, in `text-caption`, with no title above the row. Each anchored heading gets a `scroll-margin-top` of the bar height plus `16px`.
- Section: every `h2` opens one card with `bg-card`, `border`, radius `8px`, `shadow-card`, `p-4`, and `mt-8` above it. `h2` is `text-title` weight 600 with `mb-3`. `h3` is `text-caption` weight 600 in `text-muted-foreground` with `mt-4` and `mb-2`.
- Body: `text-body` with `line-height: 1.65`. Paragraphs and lists end with `mb-3`. Inline code is `font-mono text-caption` on `bg-muted`.
- A page of long prose that is read once from start to finish may set its body text to `text-title` with `line-height: 1.75`. A CSS comment at the top of the `<style>` block records that exception, as the Density scale requires.
- Links are underlined and take `text-foreground`; hover thickens the underline to `2px`. `text-primary` is not used for running text, because it is too dim on the dark background.
- Print: `@media print` hides the top bar and the contents list, removes card borders, shadows, and padding, sets `break-inside: avoid` on cards, and lets tables grow to full width.

## Skeleton

Sections come in this order. A section with nothing to say is left out.

1. `h1`: `<subject>: as of <YYYY-MM-DD>`, then three facts in a list: the as-of date with its time zone and units, what was examined, and which kinds of sources were read.
2. Summary: two short paragraphs. The first states what the records or data show, conclusion first. The second states what people said or what is estimated, and the limits of that. Key figures follow.
3. Background: the terms, definitions, or setup the reader needs for the rest.
4. Timeline: when the subject is a sequence of events.
5. Findings: one `h2` section per finding or record set. Tables hold the records. A bar block shows figures that add up to a total.
6. Open questions: a numbered list of what no source answers.
7. Sources: one sentence on how the sources were found, then a table of source, date, and what the page used from it.

The file contains no HTML comments, because they travel with it.

## Blocks

A block sits inside a section card, so it has a border but no shadow.

| Block | Use | Shape |
|---|---|---|
| Key figures | The two to four figures the summary rests on | Grid `repeat(auto-fit, minmax(240px, 1fr))` with `gap-3`. Each cell has `p-3`, `border`, and radius `8px`. Label: `text-caption` weight 600 `text-muted-foreground`. Value: `font-mono text-title` weight 600 `tabular-nums`. Then one line that names the source and date of the figure. The value takes `text-kpi` only under the stat-tile rule in SKILL.md |
| Bars | Amounts compared with each other, or the parts of one total | One row per amount with columns `112px minmax(0, 1fr) 96px` and `gap-3`: the label in `text-muted-foreground`, an `8px` track in `bg-muted` holding a block-level `bg-primary` bar, both with radius `4px`, and the value in `font-mono tabular-nums` aligned right. The bar's width is its share of the largest value, set as an inline `style` percentage. The total row has `border-t`, weight 600, and an empty track cell |
| Timeline | Events in order | A list without markers. Each item is a grid with columns `8px minmax(0, 1fr)` and `gap-x-3`, and every item but the last has `pb-3`. The second column holds the date in `font-mono text-caption text-muted-foreground tabular-nums`, then one sentence for the event on the next line. The item's pseudo-elements draw the rest: in the first column, an `8px` round dot in `bg-muted-foreground` centered on the date's line, and a `2px` line in `border` color that runs behind the dots from each dot's center to the next one's, through the `pb-3` space. The line stops at the last dot |
| Node graph | Parts that branch, join, or carry details that the reader opens | One inline SVG in a box, as [Node graph](#node-graph) below describes |
| Table | Records | A wrapper with `overflow-x: auto`, `border`, and radius `8px`. A table with three or more columns keeps `min-width: 520px`, so a narrow screen scrolls it inside the wrapper instead of squeezing its columns. Header cells: `text-caption` weight 500 `text-muted-foreground` on `bg-muted`, on one line. Body cells: `px-4 py-2`, top-aligned, `border-t` between rows. Numbers, dates, and identifiers are `font-mono tabular-nums` on one line. A column of amounts is right-aligned together with its header; every other column is left-aligned. A status in a cell is a Badge; other cell text keeps `text-foreground` |
| Badge | A status word beside an item | `font-mono text-micro`, `line-height: 18px`, `px-1.5`, radius `4px`, `border`, `bg-muted`, `text-muted-foreground`. A critical or warning badge keeps the `bg-muted` fill and takes its status color for the text and, mixed at 35% with transparent, for the border. A badge always holds a word |
| Quote | Words taken from a source | Block: `p-3`, `bg-muted`, radius `6px`, no outer margin, then the speaker or source and the time in `text-caption text-muted-foreground`. Inline: quotation marks only. Neither form has a left bar |

### Node graph

Legibility decides every choice in a node graph. Use one when parts branch, join, or carry details that the reader opens; events that need one sentence each are a Timeline. The content picks the direction and the parts: a part appears only when its "When" holds.

Three things always hold:

- The graph is one inline `<svg>` at its real size: `width` and `height` equal its `viewBox`, so its text stays on the type scale. The `viewBox` ends where the drawing ends, with no empty space around it. The markup holds geometry only, and colors come from classes in the `<style>` block.
- Nodes line up in rows and columns, and nothing overlaps: text stays inside its node, an arrow never runs through a node, a label, or a group name, and a label sits beside its arrow, clear of both nodes.
- The graph shows whole at the full column width: it is at most `668px` wide, the inner width of its box at that width. The box has `border`, radius `8px`, `p-3`, and `overflow-x: auto`. The SVG is a block with `margin: 0 auto`, which centers a narrow graph and lets a wide one scroll from its left edge. On a narrower screen the graph scrolls inside the box.

| Part | When | Shape |
|---|---|---|
| Direction | Always | Left to right or top to bottom, whichever reads better. Left to right holds about four nodes in a row; a longer flow, or one with long names, runs top to bottom |
| Node | Always | A rectangle with `bg-card` fill, a `1px` line in `input` color, and radius `6px`. It holds a name in `text-body` weight 500 and at most one note line in `text-caption text-muted-foreground`. A node with a status (SKILL.md, Status colors) writes the status word as its note, in the status color |
| Arrow | Always | A `1.5px` line in `muted-foreground` color with an arrowhead, straight or with right-angle turns. Its label names what moves along it, in `text-caption text-muted-foreground` |
| Group | Nodes run in the same place | A `bg-muted` rectangle with radius `8px` and no border behind those nodes, with the group's name at a free corner in `text-caption` weight 600 `text-muted-foreground` |
| Change marks | The graph shows what a change did | New: `bg-primary` fill and `primary-foreground` text. Changed: a `1.5px` line in `primary` color. Removed: no fill, a dashed line in `muted-foreground` color, and the name in `text-muted-foreground`. A new arrow takes `primary` color, and a removed arrow is dashed. A key above the box names each mark in use, in `text-caption text-muted-foreground` |
| Details | A node has more to say than its note line holds | Only such a node is a button (`role="button"`, `tabindex="0"`, `aria-pressed`) that a click, Enter, or Space selects, and hover covers it with a rectangle in `accent` color. The selected node gets a `1.5px` ring in `foreground` color, `3px` outside it, so selection never reads as a change mark. Keyboard focus shows on the same ring, in `ring` color at `2px`. A panel under the box (`mt-3`, `p-3`, `border`, radius `8px`) shows the selected node's name in `text-title` weight 600, its mark or status as a Badge, and its details as rows of label and value, with labels in `text-caption` weight 600 `text-muted-foreground`. When the page opens, the first button with a change mark is selected, or the first button when none has a mark. Every node's panel is in the HTML: a script hides all but the selected one, and print shows them all |

These sizes read well: nodes `44px` tall with one shared width, arrows `40px` or longer, and a group edge `12px` from its nodes, with `26px` above them for the group's name.

## Wording

- Each sentence is one of three kinds, and its verb shows which: what a record or the data shows, what a person wrote or said, or what the author infers. An inference is marked as one.
- A number appears as its source writes it, with its unit and period, next to the total it belongs to.
- A sentence that says something was not found names what was searched.
- A quote stays in its original language, with its speaker and time. A translation follows it when the readers do not read that language.
- Dates are `YYYY-MM-DD`. The head names the time zone once.
- The whole page keeps one register.

## Before handing over

1. Open the file in a browser and run the width check from SKILL.md (Layout & Responsive), in light and in dark. Set the viewport width, not the window width, and look at a screenshot of each.
2. Confirm that the page does not scroll sideways and that every table and node graph scrolls inside its wrapper. At 800 and 1280, no node graph scrolls. No arrow runs through a node or a label.
3. Add up every total again and compare every number on the page with its source.
4. Search the file for HTML comments and unfilled placeholders.
5. Run the checks in the file of every checked option.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Token values typed from memory, or renamed (`--bg`, `--ink`) | The names and values in the theme table in SKILL.md |
| A row of large numbers at the top of the page | Key figures at `text-title`; `text-kpi` only under the stat-tile rule |
| A quote or callout marked with a left bar | A `bg-muted` block |
| Emoji or icons as section markers | Headings only |
| A colored fill behind a status badge | The `bg-muted` fill; the status color goes on the text and border |
| Loading a CSS framework to save time | Plain CSS in the one `<style>` block |
