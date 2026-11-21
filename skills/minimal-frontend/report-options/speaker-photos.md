# Option: Speaker photos

Each quote of a person starts with a small round photo of that person, so a reader sees who is speaking before reading the words. The avatar rules in SKILL.md (Anti-slop) still apply.

## Which quotes

- A quote of a person's own spoken or written words gets a photo: inline quotes, Quote blocks, and timeline items that quote someone.
- The speaker is the person whose words are quoted, not the person who forwarded, reported, or cited them.
- A quote from a document, an organization, or a system gets no photo and no icon.
- The photo never replaces the name. The speaker's name stays in the same sentence or in the Quote block's attribution line, so the photo is decorative.

## Photos

- Use only photos that the user supplied or that the quoted records attach to each person, such as a profile picture. Never search the web for a face, and never use one person's photo for another.
- Match a photo to a speaker by an identifier, or by the name exactly as the record writes it. When one person appears under two names, both names use the same photo.
- A speaker with no photo gets the person icon (`sp-none`), never initials.
- Crop each photo square around the face, scale it to 64×64 px, and save it as JPEG or WebP. Embed it once as a data URI in a `.sp-<id>` rule, so a person quoted ten times adds one photo to the file. Never link to a remote image, because the file must work offline and after it is forwarded.

## Markup

The opening quotation mark of each quote sits in a `.sp` span. The photo is drawn before that mark, and the two never split across lines.

```html
한지우는 <span class="sp sp-jiwoo">“</span>인덱스가 빠진 것 같습니다”라고 썼습니다.
```

- `<id>` is an ASCII id, unique per person, such as `sp-dana-reyes` or `sp-p2`.
- With inline translation, the span holds the opening mark in front of `.tq`: `<span class="sp sp-dana-reyes">“</span><span class="tq" …>…</span>”`.

## Style

Add this to the `<style>` block, then one rule per person that sets `--photo`.

```css
.sp { white-space: nowrap; }
.sp::before { content: ""; display: inline-block; width: 1.25em; height: 1.25em; margin-right: 0.25em; vertical-align: -0.3em; border: 1px solid var(--border); border-radius: 50%; background: var(--muted) var(--photo, none) center / cover no-repeat; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.sp-none::before { --icon: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 20 20'%3E%3Ccircle cx='10' cy='10' r='10' opacity='.28'/%3E%3Ccircle cx='10' cy='8' r='3.4'/%3E%3Cpath d='M3.6 16.4a7.4 7.4 0 0 1 12.8 0A10 10 0 0 1 3.6 16.4z'/%3E%3C/svg%3E"); border: 0; background: var(--muted-foreground); -webkit-mask: var(--icon) center / 100% no-repeat; mask: var(--icon) center / 100% no-repeat; }
.sp-jiwoo { --photo: url("data:image/jpeg;base64,/9j/4AAQ…"); }
```

## Before handing over

1. Each person's photo is in the file once, and the file links to no remote image.
2. Every photo belongs to the person whose words follow it.
3. At 375px wide, in light and in dark, no photo sits on a different line from its quotation mark, and the person icon is visible.
4. Print preview shows the photos.
