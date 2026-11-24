---
name: report-long-work
description: Reports work that an agent finished (a migration, a cutover, a cleanup, a long autonomous task) to a reader who was not there, as an HTML page with node graphs of what changed and in which order, a to-do list for the reader, verification results, and an image of every destructive action. Covers saving the records while the work runs, checking the page, sharing it in a chat channel as paste-ready text with images, and a single-file HTML export. Use when a report is due at the end of agent-run work, or on 이 작업 끝나고 정리해줘.
---

# Report Long Work

The reader was not there. The report tells them what changed, how that was checked, what was destroyed, and what they must do now. It is built from records saved while the work ran, so start step 1 as soon as a request says to report at the end.

Two tools come with this skill. Execute [scripts/report.py](scripts/report.py); its `--help` lists the commands. Source [scripts/evidence.sh](scripts/evidence.sh) from a script.

In the commands, `T` is the task folder (default `<project>/.agents/ai-tasks/<YYYYMMDD-HHmm-slug>/`) and `S` is the absolute path of the `scripts/` folder next to this `SKILL.md`. Write `uv run --no-project --no-config python $S/report.py <command>` out in full each time: a variable that holds the whole command does not split in zsh.

## 1. While the work runs: save records

A screen that was not saved cannot be shown later.

- `$T/timeline.txt`: one line per milestone when it happens: time with zone, what happened, effect on users.
- `$T/evidence/NN-<what>.txt`: the output of every plan and check, saved when it runs. Every number in the report comes from one of these files.
- A destructive action in a terminal (it deletes data or a resource, cannot be undone, stops a service, or spends money): run it from a script that sources `$S/evidence.sh`. The transcript then holds the state before, a check that the target is the planned one (`expect` stops the script when it is not), the command, and the state after. Save it as `$T/destructive/NN-<what>.txt`. The header of `scripts/evidence.sh` shows the calls.
- A destructive or paid action in a web page (sign-up, purchase, delete button): save a screenshot before and after as `$T/evidence/browser/NN-<what>.png`.
- A record never shows a secret. Mask it in a copy before the copy goes into the report.

## 2. Build the page

One HTML file, `$T/report/public/index.html`, with its CSS and scripts inside and its images in `shots/` next to it. The page must be readable in light and dark and on a phone. Only the blocks below and their order are fixed.

Leave out a block that has nothing to say.

| Block | Holds |
|---|---|
| Do now | At most 5 numbered actions that only the reader can take, each with one line of reason and a time estimate. Include what the reader must not do until a condition holds. |
| Outcome | One table of the few numbers that the result rests on, such as before → after, downtime, test counts, cost: one row per number, with its unit and its basis. Never KPI cards (tiles that each hold a label and a large number). |
| Before and after | A node graph of the system before, and one after: components as nodes, arrows labeled with what flows, groups for where a node runs. Mark the nodes that are still a single point. |
| Order of work | A node graph of the steps in time order, each with its time and its result. Mark outages and destructive steps. |
| Verification | A table of what was checked and the measured result. Then one line that names what was not tested. |
| Destructive actions | One image per transcript, then the browser screenshots. Name every destructive action that has no record, and say where its trace is. |
| Cost | Amount and basis per item, and a total. Say that it is an estimate. |
| Changes from the plan | What was done differently and why, and earlier statements that turned out wrong. |
| What is left | Two lists: needs a decision, good to know. |
| Where things are | URLs and access commands. |

- The node graphs are the core of the page. A reader selects a node, by click or keyboard, and a panel shows what changed there, how it was checked, and a link to its record. A graph shows whole at 800px; on a phone it may scroll inside its own box.
- Transcript image: `uv run --no-project --no-config python $S/report.py shot <transcript> $T/report/public/shots/<name>.png --title "<what, when>"`. It prints the image's size: keep those proportions on the page.
- An image opens larger in place, not through a link to its file, because the single-file export carries no other files.
- Take every fact from a record, not from memory. Measure again, or leave out, what has no record.
- A number carries its unit and its basis. Say "estimate" when it is one.
- Write full sentences in the reader's language, without labels invented during the work. Show times in one time zone and name it once.

## 3. Check

`uv run --no-project --no-config python $S/report.py check $T/report/public/index.html` renders the page at 375, 800 and 1280px in light and dark. It fails on sideways scroll, script errors, missing or stretched images, links to anchors that do not exist, a graph that is cut off at 800px, and a page where nothing can be selected. It clicks every selectable element and lists the ones that change nothing. It writes page images to `$T/report/check/` and prints their paths.

1. Fix every reported problem and run it again.
2. Open every image that it printed. Arrows that run through nodes, cut-off text, and labels that overlap show only there.
3. Compare every number on the page with its record, and add up every total again.

## 4. Deliver

- Reader on another machine: serve `$T/report/public/` over HTTPS and confirm that the URL answers 200. On a tailnet: `uv run --no-project --no-config python -m http.server <port> --bind 127.0.0.1 --directory $T/report/public` in the background, then `tailscale serve --bg --https=<public-port> http://127.0.0.1:<port>`.
- Host that shows HTML in the thread: show a short page there with Do now, Outcome and the graphs, and a link to the full page. The thread frame applies its own theme, so the full page stays the report.
- Final reply: the Do now list, the URL, what is still running with the command that stops it, and what could not be verified. Do not repeat the page.

## 5. Share and keep current

- Chat channel: post only with an identity that belongs to the agent. Never post as the user. Hand over a kit instead:
  - Plain text that survives a paste: lines that start with `•`, section labels in `[brackets]`, the outcome first, then downtime and data effects, what the readers must do or must not do, and what to know.
  - Images of the page: `uv run --no-project --no-config python $S/report.py capture $T/report/public/index.html $T/report/public/share/<name>.png --select "<CSS selectors of the blocks>"`. Keep each one below about 2,200px tall.
  - Links that open for those readers. A tailnet or localhost URL does not: link a repository or a pull request, or attach the single file.
- One file for people who cannot reach the server: `uv run --no-project --no-config python $S/report.py single $T/report/public/index.html $T/report/public/<subject>-<date>.html`.
- When the state changes after delivery (a merge, a pending check, a decision): confirm the new state with a command and save its output as a record. Then update the page, check it again, and export again what was shared. Tell the user which earlier statement no longer holds.
