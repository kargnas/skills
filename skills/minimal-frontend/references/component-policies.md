# Component Policies

Counts, behavior, and copy limits per component. Tokens and spacing come from SKILL.md, chrome and loading from app.md; both win on conflict. Read the sections for the components you build or review.

## Badges

- A notification badge marks something the user has not seen yet (unread message, new alert) and disappears as soon as they see it. Never show `0`.
- A count badge shows at most 4 characters including `+`: `1` to `99` as is, `99+` above.
- Use a count when the number matters (unread chats) and a dot when only presence matters or space is tight.
- Keep notification badges few per screen, and never put them on 3 or more bottom tabs at once.
- A status badge: 1-2 per object, with a 2-3 word label.
- A badge is information, never a control. For an action, use a button, a chip, or a toggle.
- Badge strength follows the background: a weak style in repeated lists, a solid high-contrast style over images or busy backgrounds. A weak badge never sits on a colored surface.
- Badge colors use the status vocabulary in SKILL.md (Status colors).

## Dialogs, sheets, and side panels

- `AlertDialog` (confirm) has at most 2 actions including the dismiss action, always describes what the action does, and ignores outside clicks; Esc acts as its dismiss action. It is the top layer: it may open over an open sheet or side panel.
- The destructive color goes only on the button that destroys something: deleting data, discarding a draft, resetting settings. Never on Cancel.
- `Dialog` grows to at most 80% of the viewport height. Title and footer stay fixed and the body scrolls; a divider under the title appears only while the body is scrolled.
- A dialog has a header X or a footer Cancel, never both. Info and view dialogs keep the X. Input and edit dialogs use a footer Cancel and drop the X (`<DialogContent showCloseButton={false}>`), so attention stays on the footer actions.
- Outside click and Esc are the quick exit for light layers (notices, view dialogs). In a layer that holds input, they act like Cancel, so changed input gets the leave warning from Forms.
- A bottom sheet is at most 480px wide and 90% of the viewport high. Content taller than that becomes a page, not a scrolling sheet.
- A sheet that must not close by accident (payment, complex form, screens inside the sheet) has a close button at the top and no drag handle. A sheet with snap points has at least 2 (90%, 50%, optional 10%) and always shows its handle.
- Input method picks the form (SKILL.md, Layout & Responsive). Under `pointer-coarse:`, a responsive dialog or side panel opens as a bottom sheet. With a fine pointer, a narrow window keeps the dialog at up to 90% of the window width and the side panel at up to 80%, so 20% of the page stays visible.
- A side panel (`Sheet`) opens on the right for details and settings and on the left for the full menu. Its width follows the use: 480px for simple details, 720px for a two-column form or a list-detail comparison, 960px for dashboards and editors.
- A docked panel that stays open while the page stays usable exists only from `md:` (768px) up. Below that, it opens as an overlay.

## Buttons

- At most one filled button per view, whatever its color (app.md, Von Restorff).
- At most 2 buttons side by side. Further actions move to an icon button or the `…` menu, because 3 or more side by side look equally important and truncate when text is enlarged.
- A dismiss action (Close, Reset) next to the filled button uses `variant="secondary"`. In a full-width row, the two split 3:7 (dismiss : primary). Two secondary actions of equal weight split evenly.
- `outline` pairs only with `outline`, never with a filled button. Use it when the same action repeats across a screen, such as row and card actions.
- The label is a verb that predicts the result (`Create project`, not `Next`). One action keeps one word everywhere.
- Add an icon to a button only when it adds meaning, and never on both sides of the label. Use an icon-only button only when space demands it, and give it an `aria-label`.
- A button row that overflows (translation, enlarged text) stacks vertically instead of truncating: `flex flex-wrap` with growing buttons.
- A floating action button: one per screen, bottom right, clear of fixed bottom bars, in a color that never changes. Its label is short (`Write`, not `Post multiple items`) and may hide while the user scrolls down.

## Navigation

- Back returns to the previous step and keeps what was entered. Close ends the layer or flow and returns to where it started. In a multi-step search, Back goes one step back and Close leaves the search. Back never acts as Close.
- The flow decides where Back goes. Browsing flows (search, recommendations) go back through history (`history.back()`). Fixed hierarchies (settings) go to the parent route: Back from notification settings opens the settings index.
- Bottom tab bar (phone chrome, `pointer-coarse:`): at most 5 tabs; more destinations move to top tabs. Labels fit one line, up to 10 Latin characters. The active tab is shown by color, not by a different icon shape.
  - 한국어의 경우: tab labels take up to 5 Hangul syllables.
- The right side of a top bar holds up to 2 icon buttons (3 at most) and 1 text button. More actions go to a `…` menu. The title never runs under the actions.
- Tabs navigate; a segmented control operates. Tabs sit at the top and switch to a different view with its own route. A segmented control sits right above the content it controls and changes only that content (view mode, filter, sort). Map view vs street view is a segmented control; switching between product sections is tabs.
- Full-width tabs: at most 5. With 6 or more tabs, or long labels, use content-width tabs that scroll sideways. Two-level tabs use underline tabs on the first level and chip tabs on the second, and chip tabs never share a screen with filter chips.
- In side navigation, a parent item only expands and never navigates. The parent of the active item starts expanded. Labels wrap instead of truncating.
- Pagination keeps a fixed width with a fixed slot count: 9 slots when the pagination container is 480px or wider, 7 below (`@container`). Content pagination hides an unusable end arrow and keeps its 40px slot empty, so no button shifts between pages. Table pagination disables the arrow instead.
- Content of 3-4 screens or less is not paginated.
- Table pagination sits below the table, never above. It offers 3-4 rows-per-page options (10, 25, 50). When the total is unknown, the current range is plain text instead of a range select.
- Onboarding and step forms show a step indicator, not page numbers.

## Selection controls

Pick the control by the shape of the options:

- Each option needs an image or a multi-line description: selectable cards.
- 2-4 options with short labels: chips (`ToggleGroup`).
- One choice from 2-6 options that never change: `RadioGroup`. Preselect the most common or recommended option, and stack the options vertically.
- One choice from more than 6 options, or from a list that can grow (birth year, country): `Select`.
- Several choices from 2-10 options: a `Checkbox` group.

Then:

- If a choice applies immediately, use `Switch`. If it applies on save or submit, use `Checkbox`. Consent ("I have read the above") is a checkbox. Select-all is a parent checkbox over child checkboxes, never a master switch above child switches.
- A segmented control (`ToggleGroup`, single selection) has 2-4 short segments (`Popular`, `Recommended`), and a screen has only one. A label too long for a segment (`Most popular reviews`) calls for another control.
- `Select` picks a value that applies on save or submit. A menu (`DropdownMenu`) runs a command on click.
- A subjective continuous value (volume, brightness) gets a continuous slider. A value in fixed units (rating 1-5, discount in 5% steps) gets a stepped slider, and a click on its track snaps to the nearest step.
- A quantity stepper disables − at the minimum and + at the maximum. When going below the minimum means removing the item (cart), − at the minimum becomes delete. The number itself is not clickable.

## Selection behavior

- Single select: picking the selected item again keeps it selected, and the list closes on pick. Multi-select: picking a selected item again clears it, and the list stays open. A click outside closes the list and keeps the previous value.
- A list opens scrolled to the selected item.
- When "none" is a valid answer, add it as an option named after the question (`No meal preference`, not `Not applicable`). Put it first or last in its own group, and let it satisfy the required check, so skipping and answering "none" stay distinguishable.
- When an answer is mandatory, there is no "none" option and an empty submit is blocked (the country code of a phone number). When an empty state cannot exist (sort order), preselect a default.
- A multi-select has no option that changes other options (`Select all`, a `None` that clears the rest). When select-all is common, use a parent checkbox.
- State the maximum of a multi-select in its helper text (`Up to 3`). At the maximum, block new picks and say why in the helper text.
- When a multi-select must tell "skipped" from "none", ask a yes/no question first: checking `Has defects` reveals `Defect types`.
- Summarize selected values that don't fit. For values with clearly different meanings, show the first value and the count of the rest (`Gangnam and 2 more` for three picks). For equal values or tight space, show the total (`3 selected`).
  - 한국어의 경우: '외' counts the values after the first ('강남구 외 2곳' for three picks), and '등' counts all of them ('강남구 등 3곳'). '강남구 등 2곳' for three picks is wrong.
- Join values with the locale's list rules (`Intl.ListFormat`), never with hand-written separators. When "and" vs "or" changes the result (filters), the helper text says which one applies.
- Order options by one property the list really has (frequency, size, time). An option of a different kind goes to its own group. Option labels are short nouns without filler such as "Select".

## Date and time

- A calendar opens on the month of the selected value, or on the current month when nothing is selected. A range uses its start date; multiple dates use the earliest one.
- Range picking: a click before the start date becomes the new start, a click after a complete range starts over, and confirm stays disabled while only the start is set. Multiple-date picking: clicking a picked date removes it.
- State the limits before the user picks. A note above the calendar gives the minimum and maximum length or count, and multiple-date picking shows how many remain.
- When the user extends a running range (an ad period), only the start date is read-only; the end date stays free.
- Read-only keeps the filled background, so the value reads as present. Disabled is dimmed with no background. Days of the previous and next month stay blank, not dimmed (`showOutsideDays={false}`).
- A fine pointer gets a range picker with two months side by side (`numberOfMonths={2}`). Under `pointer-coarse:`, it is a bottom sheet with continuously scrolling months, a sticky weekday row, and Select and Reset buttons at the bottom.
- The week starts on the locale's first day.
  - 한국어의 경우: weeks start on Sunday.
- The minute step follows the use, and the current time rounds to that step: 1 min for alarms and timers, 5 min for meetings and appointments (the default), 10 min for loose time windows, 15 or 30 min for booking slots, and 30 min for business hours. With 5-minute steps, 9:13 opens as 9:15.
- When date and time are picked together, the two pickers sit side by side, each in the form that suits it: the date calendar inline, and the time in a popover (a sheet under `pointer-coarse:`).

## Forms

- Required marks follow the majority. When 2/3 or more of the fields are required, mark only the optional ones (`Optional`); otherwise mark the required ones with `*`. One form uses one convention.
- While a field shows an error, its helper text is hidden. A character counter appears only when there is a length limit.
- A label is a noun phrase without a period, on one line (two at most). Helper text is an instruction (`Enter a 10-11 digit phone number`).
- Field checks (required, length, format) run on blur, as in UX Laws. Business and server rules run on submit.
- Leaving a create or edit screen with changed input warns that the input will be lost. There is no warning when nothing changed or when drafts autosave.
- Create and edit forms share one layout. When earlier answers add fields, or the form crowds a phone screen, split it into steps.
- A fixed format is no reason to split an input: a phone number is one field with auto-formatting. Split an input only to mask part of the value (a card number), because split fields break select-all, copy, editing, and OS autofill.
  - 한국어의 경우: the back half of a 주민등록번호 is masked in its own field.
- A placeholder never replaces the label: it disappears on typing, and screen readers lose the purpose of the field. It says what value goes in (`Select a region`), not the label again and not an instruction (`Tap here to expand`).
- An auto-height textarea keeps at least 3 lines. A fixed-height textarea shows at least 2 lines, has a maximum height, and scrolls inside.
- A search field is one line with no line breaks. Submitting shows the results and dismisses the on-screen keyboard, and tapping or scrolling the results dismisses it too. Clearing the query keeps focus in the field.

## Lists, cards, and images

- A list row holds at most 3 clickable elements.
- A row with a checkbox, radio, or switch is one hit area: the whole row toggles, and it holds no other buttons. A link inside it (`View terms`) stops propagation, so it doesn't toggle the row.
- Nested corners: the inner radius is the outer radius minus the padding between them (16px - 6px = 10px).
- A single-select list has at least 2 items, and one group never mixes single and multiple selection.
- An `Accordion` has at least 2 items; a single item becomes a `Collapsible`. All items start closed, a panel never scrolls inside, and the whole header row is the trigger, not only the chevron.
- Use dividers (`Separator`) only where spacing can't separate, and never under the last section. Strength rises from an inset line within a group, to a full-width line between groups, to an 8px band for a topic change. Repeated rows usually need none.
- An image takes at most 1 overlay per corner and 2 in total (a badge and a save button). The badge shows status or category only; counts and durations go in a separate indicator. An overlay icon shows the content type and does nothing on click.
- Image corners follow the image size: 4px up to 24px wide, 6px up to 48px, and 8px above that. Full-bleed images are not rounded.
- Tags are keywords that fit one line, all the same size. When space runs out, the lowest-priority tags truncate first.
  - 한국어의 경우: a tag takes 6-10 characters, without 조사 or 접속어.
- A container that clips content at a scroll edge fades that edge with `mask-image`. The fade stays visible whether or not the user is scrolling, because toggling it on scroll start and stop flickers. Its depth equals the container's end padding (`p-4`), so the last item can scroll clear of the fade.

## Empty and result screens

- An empty screen tells the user what to do next. A failure screen says what went wrong and what to do next.
- The way out of a failure screen follows its context: an input error goes `Back` to the previous step, a modal closes with X, and a screen with nowhere to return to offers `Go home`. `Try again` can sit beside any of them.
- When the next action is the point of the screen, it gets the view's one filled button (full width at the bottom under `pointer-coarse:`). A secondary action is a small button inside the region.
- Use illustrations only for moments unique to the product, never on generic messages such as a sign-up on hold.

## Icons and motion

- Icons are at least 12px.
- These rules apply when the project's icon library ships filled variants (Lucide does not):
  - Filled icons at 16px and below, and inside containers (buttons, chips).
  - Line icons next to regular text, filled icons next to bold text.
  - Line icons in top bars, filled icons in bottom tabs, and one style per bar.
  - A toggle's icon is line by default, filled when on, and line with a slash when off.
- An auto-hiding header never stops halfway. When scrolling ends, it snaps fully hidden or fully shown at 50% of its travel, in 200ms. Keyboard focus inside it reveals it at once, and reduced motion turns auto-hide off.
