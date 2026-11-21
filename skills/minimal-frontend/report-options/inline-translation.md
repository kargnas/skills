# Option: Inline translation

A quote in another language shows its translation in place, in the page's language. The original is one hover, focus, or tap away in a tooltip, and it appears in print.

## Which quotes

- Every quote in a language other than the page's language is translated. Names, product names, labels, identifiers, and code inside it stay as written.
- A quote whose exact wording the page examines, such as a contract clause or a disputed sentence, keeps the original in place. Its translation goes in the tooltip instead, under the label for "translation".
- A quote in the page's language gets no tooltip.

## Translating

- Translate each quote for its meaning in context, with its surrounding sentence and its source in view. Keep the page's register.
- Where the translation departs from the wording, such as an idiom, an unclear referent, or a term with no equivalent, a translator's note follows the quote. It sits in parentheses in `text-caption text-muted-foreground` and starts with the page language's word for "translator's note".
- The sentence around the quote still names who wrote or said it, as Wording in report.md requires.
- The head list gets one more line, in the page's language: pointing at or tapping a quote with a dotted underline shows its original, or its translation where the page keeps the original.

## Markup

```html
“<span class="tq" tabindex="0" aria-describedby="tq-1">이 프로젝트를 더 유지할 시간이 없습니다</span>”<span class="tq-src" id="tq-1" hidden><span class="tq-label">원문 · Dana Reyes</span> <span lang="en">“I no longer have time to maintain this project”</span></span>
```

- The quotation marks stay outside `.tq`, and `.tq-src` follows the closing mark. Each `tq-<n>` id is unique on the page.
- The label is the page language's word for "original", or for "translation" when the original stays in place. When the quote has a speaker, ` · ` and the speaker's name follow it.
- `aria-describedby` gives the original to screen readers. The visible tooltip is a copy, so it is hidden from them.

## Style

Add this to the `<style>` block. A dotted underline marks a translation, and `cursor: help` is the convention for text that has a tooltip.

```css
.tq { border-radius: 2px; text-decoration: underline dotted var(--muted-foreground); text-decoration-thickness: 1px; text-underline-offset: 4px; cursor: help; }
.tq:hover { text-decoration-color: var(--foreground); }
.tq:focus-visible { outline: 2px solid var(--ring); outline-offset: 2px; }
.tq-note { font-size: var(--text-caption); color: var(--muted-foreground); }
#tq-tip { position: fixed; z-index: 50; max-width: min(480px, calc(100vw - 32px)); max-height: calc(100dvh - 32px); overflow: auto; padding: 12px; font-size: var(--text-caption); line-height: 1.5; overflow-wrap: anywhere; color: var(--foreground); background: var(--card); border: 1px solid var(--input); border-radius: 8px; box-shadow: var(--shadow-card); }
#tq-tip .tq-label { display: block; margin-bottom: 4px; font-weight: 600; color: var(--muted-foreground); }
@media print {
  #tq-tip { display: none; }
  .tq { text-decoration: none; }
  .tq-src[hidden] { display: inline; font-size: var(--text-caption); color: var(--muted-foreground); }
  .tq-src::before { content: " ("; }
  .tq-src::after { content: ")"; }
  .tq-label::after { content: ":"; }
}
```

## Script

Add this as one `<script>` at the end of `<body>`, as written. Besides the theme script, it is the only script on the page. The tooltip position it sets is the only inline style besides bar widths.

```html
<script>
(() => {
  const tip = document.createElement("div");
  tip.id = "tq-tip";
  tip.hidden = true;
  tip.setAttribute("aria-hidden", "true");
  document.body.append(tip);
  let current = null;
  let timer = 0;
  const close = () => { clearTimeout(timer); tip.hidden = true; current = null; };
  const place = (y) => {
    const rects = [...current.getClientRects()];
    const r = rects.find((b) => y >= b.top && y <= b.bottom) || rects[0];
    const vw = document.documentElement.clientWidth, vh = window.innerHeight, m = 16, gap = 6;
    if (!r || r.bottom < 0 || r.top > vh) return close();
    tip.style.left = "0px";
    tip.style.top = "0px";
    const { width: w, height: h } = tip.getBoundingClientRect();
    let top = r.bottom + gap;
    if (top + h > vh - m && r.top - gap - h >= m) top = r.top - gap - h;
    tip.style.left = `${Math.max(m, Math.min(r.left, vw - w - m))}px`;
    tip.style.top = `${Math.max(m, Math.min(top, vh - h - m))}px`;
  };
  const open = (q, y) => {
    clearTimeout(timer);
    const src = document.getElementById(q.getAttribute("aria-describedby"));
    if (!src) return;
    if (current !== q) { current = q; tip.replaceChildren(...src.cloneNode(true).childNodes); }
    tip.hidden = false;
    place(y);
  };
  const closeSoon = () => {
    clearTimeout(timer);
    timer = setTimeout(() => { if (current && current !== document.activeElement) close(); }, 200);
  };
  document.addEventListener("mouseover", (e) => {
    const q = e.target.closest(".tq");
    if (q) open(q, e.clientY);
    else if (tip.contains(e.target)) clearTimeout(timer);
  });
  document.addEventListener("mouseout", (e) => { if (e.target.closest(".tq") || tip.contains(e.target)) closeSoon(); });
  document.addEventListener("focusin", (e) => { const q = e.target.closest(".tq"); if (q) open(q); else if (current) close(); });
  document.addEventListener("focusout", (e) => { if (e.target === current && !tip.contains(e.relatedTarget)) close(); });
  document.addEventListener("click", (e) => { const q = e.target.closest(".tq"); if (q) open(q, e.clientY); });
  document.addEventListener("pointerdown", (e) => { if (current && !e.target.closest(".tq") && !tip.contains(e.target)) close(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && current) close(); });
  window.addEventListener("scroll", () => { if (current) place(); }, { capture: true, passive: true });
  window.addEventListener("resize", () => { if (current) place(); }, { passive: true });
})();
</script>
```

## Before handing over

1. Every translated quote has an original, and each original matches its source character for character.
2. In a browser, hover a quote, move to it with Tab, and tap one at 375px wide. Each time the tooltip opens next to the quote and stays inside the screen, and Esc closes it.
3. Print preview shows each original in parentheses after its quote.
