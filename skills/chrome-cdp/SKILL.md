---
name: chrome-cdp
description: >-
  Drives an already-open local Chrome, Chromium, Brave, Edge or Vivaldi tab
  over the Chrome DevTools Protocol: lists tabs, takes viewport screenshots,
  dumps the accessibility tree, evaluates JavaScript, clicks by selector or
  coordinates, and types text, including into cross-origin iframes where
  evaluation does not reach. Talks raw WebSocket instead of Puppeteer, so it
  connects instantly and survives a browser with a hundred tabs. Acts only on
  the page the user points at, and only on explicit approval, since it drives
  a session that is already logged in. Triggers on: Chrome, Chromium, Brave,
  Edge, browser tab, open page, DevTools, CDP, screenshot of a page, inspect a
  live page, debug the page, click in the browser, fill a form, accessibility
  tree, Browser fernsteuern, Tab ansehen, Screenshot der Seite, Seite
  inspizieren, im Browser klicken.
---

# Chrome CDP

Lightweight Chrome DevTools Protocol CLI. Connects directly via WebSocket, so it needs no Puppeteer, works with 100+ tabs and connects instantly.

## Prerequisites

- Chrome, Chromium, Brave, Edge or Vivaldi, with remote debugging enabled for whichever you use. On macOS the port file is located automatically for Chrome, Chromium, Brave and Edge; a Vivaldi user sets `CDP_PORT_FILE` instead: open `chrome://inspect/#remote-debugging` and toggle the switch
- Node.js 22+ (uses built-in WebSocket)
- If your browser's `DevToolsActivePort` is in a non-standard location, set `CDP_PORT_FILE` to its full path

## Commands

All commands use `scripts/cdp.mjs`. The `<target>` is a **unique** targetId prefix from `list`; copy the full prefix shown in the `list` output (for example `6BE827FA`). The CLI rejects ambiguous prefixes.

### List open pages

```bash
scripts/cdp.mjs list
```

### Take a screenshot

```bash
scripts/cdp.mjs shot <target> [file]    # default: screenshot-<target>.png in runtime dir
```

Captures the **viewport only**. Scroll first with `eval` if you need content below the fold. Output includes the page's DPR and coordinate conversion hint (see **Coordinates** below).

### Accessibility tree snapshot

```bash
scripts/cdp.mjs snap <target>
```

### Evaluate JavaScript

```bash
scripts/cdp.mjs eval <target> <expr>
```

> **Watch out:** avoid index-based selection (`querySelectorAll(...)[i]`) across multiple `eval` calls when the DOM can change between them (dismissing an item shifts the indices of the rest). Collect all data in one `eval` or use stable selectors.

### Other commands

```bash
scripts/cdp.mjs html    <target> [selector]   # full page or element HTML
scripts/cdp.mjs nav     <target> <url>         # navigate and wait for load
scripts/cdp.mjs net     <target>               # resource timing entries
scripts/cdp.mjs click   <target> <selector>    # click element by CSS selector
scripts/cdp.mjs clickxy <target> <x> <y>       # click at CSS pixel coords
scripts/cdp.mjs type    <target> <text>         # Input.insertText at current focus; works in cross-origin iframes unlike eval
scripts/cdp.mjs loadall <target> <selector> [ms]  # click "load more" until gone (default 1500ms between clicks)
scripts/cdp.mjs evalraw <target> <method> [json]  # raw CDP command passthrough
scripts/cdp.mjs open    [url]                  # open new tab (each triggers Allow prompt)
scripts/cdp.mjs stop    [target]               # stop daemon(s)
```

## Coordinates

`shot` saves an image at native resolution: image pixels = CSS pixels × DPR. CDP Input events (`clickxy` etc.) take **CSS pixels**.

```
CSS px = screenshot image px / DPR
```

`shot` prints the DPR for the current page. Typical Retina (DPR=2): divide screenshot coords by 2.

## Tips

- Prefer `snap` over `html` for page structure. The snapshot is always the compact form; there is no flag for the full tree.
- Use `type` (not eval) to enter text in cross-origin iframes. Use `click` or `clickxy` to focus first, then `type`.
- Chrome shows an "Allow debugging" modal once per tab on first access. A background daemon keeps the session alive so subsequent commands need no further approval. Daemons auto-exit after 20 minutes of inactivity.
