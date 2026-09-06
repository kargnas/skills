# Browser Preview Guide

A local server that shows the eight UI concepts in the user's browser and records which one they click.

## How It Works

The server watches a directory for HTML files and serves the newest one to the browser. You write HTML to `screen_dir`; the user sees it and clicks to select. Selections are appended to `state_dir/events`, which you read on your next turn.

**Content fragments vs full documents:** If your HTML file starts with `<!DOCTYPE` or `<html`, the server serves it as-is (plus the helper script). Otherwise it wraps your content in `scripts/frame-template.html`, which adds the theme CSS, connection status, and click handling. **Write content fragments by default.**

## Starting a Session

```bash
# --open auto-opens the browser on the first screen. Invoking this skill is the
# approval, so always pass it. --project-dir persists mockups and lets a restart
# reuse the same port.
scripts/start-server.sh --project-dir /path/to/project --open

# Returns: {"type":"server-started","port":52341,
#           "url":"http://localhost:52341/?key=ab12…",
#           "screen_dir":"/path/to/project/.agents/ai-tasks/dont-trust-my-ui-idea/12345-1706000000/content",
#           "state_dir":"/path/to/project/.agents/ai-tasks/dont-trust-my-ui-idea/12345-1706000000/state"}
```

Save `screen_dir` and `state_dir` from the response. Share the URL as a fallback too (headless or remote setups will not auto-open).

**The URL contains a session key (`?key=…`).** The server rejects any request without it, so always give the user the complete URL from the `url` field. After the first load the browser keeps the key in a cookie.

**Finding connection info:** The server writes its startup JSON to `$STATE_DIR/server-info`. If you launched it in the background and lost stdout, read that file.

Pass the project root as `--project-dir` so files land in `.agents/ai-tasks/dont-trust-my-ui-idea/`. Remind the user to add `.agents/ai-tasks/` to `.gitignore` if it is not already there.

**Launching by runtime:**

- **Claude Code:** run the command as-is; the script backgrounds the server itself.
- **Codex:** run the command as-is; the script detects `CODEX_CI` and switches to foreground mode.
- **Any environment that reaps detached processes:** add `--foreground` and launch it with your platform's background execution mechanism, then read `$STATE_DIR/server-info` on the next turn.

If the URL is unreachable from the user's browser (remote or containerized setups), bind a non-loopback host:

```bash
scripts/start-server.sh --project-dir /path/to/project --host 0.0.0.0 --url-host localhost
```

## The Loop

1. **Check the server is alive, then write HTML** to a new file in `screen_dir`:
   - Confirm `$STATE_DIR/server-info` exists and `$STATE_DIR/server-stopped` does not. If it has shut down, restart with `start-server.sh` and the **same `--project-dir`**: it reuses the port, so the open tab reconnects on its own. The server exits after 4 hours idle (`--idle-timeout-minutes`).
   - Use semantic filenames: `concepts.html`, `concepts-v2.html`. **Never reuse a filename.**
   - Write the file with your file-creation tool. A heredoc dumps the whole HTML into the terminal.
   - The server serves the newest file automatically.

2. **Tell the user what to expect and end your turn:**
   - Repeat the URL every time, not only the first.
   - Summarize what is on screen in one line.
   - Ask them to click a concept and reply in the terminal.

3. **On your next turn**, read `$STATE_DIR/events` if it exists and merge it with the user's terminal text. The terminal message is primary; events give the click trail.

4. **Iterate or advance.** If feedback changes the current screen, write a new versioned file. Move on only once a concept is chosen.

5. **Unload when returning to the terminal.** Once a concept is chosen and you start implementing, push a waiting screen so the user is not staring at a resolved choice:

   ```html
   <!-- filename: waiting.html -->
   <div style="display:flex;align-items:center;justify-content:center;min-height:60vh">
     <p class="subtitle">Continuing in terminal...</p>
   </div>
   ```

## The Concept Screen

All eight concepts go on one screen as a single-select `.cards` grid. Each card carries `data-choice` with a short slug and shows a wireframe inside `.card-image`, with the concept name and a one-line rationale in `.card-body`.

```html
<h2>Which direction should we build?</h2>
<p class="subtitle">Click one. Each concept is a full alternative, not a variation.</p>

<div class="cards">
  <div class="card" data-choice="recommended" onclick="toggleSelect(this)">
    <div class="card-image"><!-- wireframe --></div>
    <div class="card-body">
      <h3>1. My recommendation</h3>
      <p>Why this fits OP.GG users</p>
    </div>
  </div>
  <!-- cards 2..8 -->
</div>
```

Build the wireframes from the frame's mock elements and inline styles. Real content beats placeholder text when it exposes a layout problem.

## CSS Classes Available

### Cards (selectable concepts)

```html
<div class="cards">
  <div class="card" data-choice="slug" onclick="toggleSelect(this)">
    <div class="card-image"><!-- mockup --></div>
    <div class="card-body"><h3>Name</h3><p>Description</p></div>
  </div>
</div>
```

Add `data-multiselect` to the container to allow several selections.

### Options (text A/B/C choices)

```html
<div class="options">
  <div class="option" data-choice="a" onclick="toggleSelect(this)">
    <div class="letter">A</div>
    <div class="content"><h3>Title</h3><p>Description</p></div>
  </div>
</div>
```

### Mockup container and split view

```html
<div class="mockup">
  <div class="mockup-header">Preview: Champion detail</div>
  <div class="mockup-body"><!-- mockup HTML --></div>
</div>

<div class="split">
  <div class="mockup"><!-- left --></div>
  <div class="mockup"><!-- right --></div>
</div>
```

### Pros/Cons

```html
<div class="pros-cons">
  <div class="pros"><h4>Pros</h4><ul><li>Benefit</li></ul></div>
  <div class="cons"><h4>Cons</h4><ul><li>Drawback</li></ul></div>
</div>
```

### Mock elements (wireframe building blocks)

```html
<div class="mock-nav">Logo | Home | About | Contact</div>
<div style="display: flex;">
  <div class="mock-sidebar">Navigation</div>
  <div class="mock-content">Main content area</div>
</div>
<button class="mock-button">Action Button</button>
<input class="mock-input" placeholder="Input field">
<div class="placeholder">Placeholder area</div>
```

### Typography and sections

- `h2` page title, `h3` section heading
- `.subtitle` secondary text below the title
- `.section` content block with bottom margin
- `.label` small uppercase label

## Browser Events Format

Clicks are appended to `$STATE_DIR/events`, one JSON object per line. The file is cleared when you push a new screen.

```jsonl
{"type":"click","choice":"recommended","text":"1. My recommendation …","timestamp":1706000101}
{"type":"click","choice":"unusual","text":"4. Unusual …","timestamp":1706000108}
```

The last `choice` is usually the final pick, but the trail can reveal hesitation worth asking about. If the file does not exist, the user did not click; use their terminal text only.

## Cleaning Up

```bash
scripts/stop-server.sh $SESSION_DIR
```

Sessions started with `--project-dir` keep their mockups on disk. Only `/tmp` sessions are deleted on stop.

## Reference

- Frame template (CSS reference): `scripts/frame-template.html`
- Client helper: `scripts/helper.js`
