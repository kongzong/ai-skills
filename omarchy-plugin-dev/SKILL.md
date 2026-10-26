---
name: omarchy-plugin-dev
description: This skill should be used when developing, debugging, installing, or publishing Omarchy 4 (Quattro) shell plugins — bar widgets, overlay panels, or services using manifest.json + QML under ~/.config/omarchy/plugins/. Covers the plugin contract, official component reuse (Panel/BarIconButton/KeyboardPanel), common QML traps, log-based debugging, glyph codepoint verification, and the install/uninstall flow. Also applies when a bar icon fails to appear or a plugin silently fails to load.
agent_created: true
---

# Omarchy 4 Shell Plugin Development

Purpose: build and debug third-party omarchy-shell plugins (Quickshell/QML) on Omarchy 4.x, where bar, launcher, and panels are all omarchy-shell modules — there is no Waybar/Walker/rofi.

## Plugin contract (verified on Omarchy 4.0.6)

1. Plugin directory: `~/.config/omarchy/plugins/<dir>/` containing `manifest.json` + entry-point QML (+ assets).
2. `manifest.json` required shape:
   - `schemaVersion: 1`, `id`, `name`, `version`, `author`, `license`, `description`
   - `kinds`: `["bar-widget"]` (bar icon + panel), `["overlay"]` (floating PanelWindow, like clipboard plugin), `"service"`, `"panel"`, `"menu"`
   - `entryPoints`: `{"barWidget": "MyWidget.qml"}` (key must match kind family: barWidget/overlay)
   - `barWidget: { displayName, description, category, aliases, allowMultiple }`
3. **`omarchy.*` id prefix is reserved.** Use reverse-domain: `com.github.<user>.<name>`. Validate fails otherwise.
4. Lifecycle: copy dir in → `omarchy-shell shell rescanPlugins` → `omarchy plugin enable <id>` → verify with `omarchy plugin list` and that `shell.json` gained the id in `bar.layout.<left|center|right>`.

## Structure of a bar-widget plugin (copy official `agents` plugin)

Clone the shape of `/usr/share/omarchy/shell/plugins/agents/Panel.qml`:

- Root: `Panel { }` (from `qs.Ui`, base Item owning IPC open/close lifecycle, exposes `opened`, `toggle()`, `bar`, `settings`).
- Bind root size — **mandatory**: `implicitWidth: button.implicitWidth` / `implicitHeight: button.implicitHeight`. The bar sizes each slot from the root's implicit size; missing this renders an invisible zero-width widget.
- Bar button: `BarIconButton { id: button; anchors.fill: parent; bar: root.bar; text: <nerd-font glyph>; active: <bool>; onPressed: ... }`.
- Popup panel: `KeyboardPanel { anchorItem: button; owner: root; open: root.opened; contentWidth/Height: panel.fittedContentWidth/Height(...) }` — put only visual Items inside it.
- State persistence: `FileView` from Quickshell.Io (see clipboard plugin): `path`, `onLoaded`, `setText(JSON.stringify(...))`, `atomicWrites: true`.
- Timers: schedule at next hour with a repeating Timer whose `interval` is recomputed in `onTriggered`; align on `Component.onCompleted`.
- First-party components available via `qs.Commons` (Style, Color) and `qs.Ui` (Panel, BarIconButton, KeyboardPanel, ToggleSwitch, PanelController). Read their QML under `/usr/share/omarchy/shell/Ui/` before using — APIs are non-obvious (see Traps).

## Traps (each one cost real debugging time)

1. **KeyboardPanel/panel containers accept only QQuickItem children.** Their default property is a `contentItem` list; a `Timer` (QtObject) placed directly inside fails the whole component load with `Cannot assign object of type "QQmlTimer" to list property "contentItem"`. Keep non-visual objects (Timer, FileView, IpcHandler, Process) at the root Panel level.
2. **Editing the plugin file does not fully take effect on hot reload.** `rescanPlugins`/file-watch reloads exist, but the qs:// module compile cache can serve stale content (error line numbers from the old file). Run `omarchy restart shell` after every substantive QML change to verify against a fresh process.
3. **`ToggleSwitch` (qs.Ui) does not flip `checked` on click** — it only emits `toggled()`. In `onToggled` assign the new value explicitly (caller-owns-value).
4. **`Style.font` property names** are `body`/`bodySmall` etc., not `bodySize`.
5. **ffmpeg `aevalsrc` has no `sign()`** — build square waves with `gte(sin(...),0)*2-1`.
6. **Never take screenshots from an agent sandbox** (`grim`/screencopy): on this machine a screencopy request crashed Hyprland itself (SIGBUS in Mesa `Screenshare::copyShm` → `readPixels`). Verify UI via logs (`hyprctl layers`, `omarchy-shell shell listPlugins`) and ask the user to look.
7. Bar slots collapse when the item is `visible: false` or zero implicit width — an "invisible icon" is almost always one of these two.

## Debugging: find the actual load error

omarchy-shell's stdout/stderr (including QML compile errors with file:line) goes to the **system journal**, tagged by process:

```bash
journalctl --no-pager | grep "omarchy-shell\[<PID>]"          # current shell full log
journalctl --since "-60s" --no-pager | grep omarchy-shell      # recent, after a change
NEWPID=$(journalctl --since "-15s" --no-pager | grep -oE "omarchy-shell\[[0-9]+\]" | tail -1)
```

Load failures appear as `Plugin widget <id> failed: <file>:<line>: <error>`. `omarchy plugin validate` uses bash process substitution (`/dev/fd`) and fails inside sandboxes without /dev/fd — not a plugin problem.

## Glyphs (bar icons)

Use nerd-font glyphs from JetBrainsMono Nerd Font (bar font). **Verify codepoints against the installed font file — do not trust memorized MDI codes** (e.g. U+F1954 is `md-sphere`, a ball; the real alarm clock is U+F0020). Use `scripts/find_glyph.py` (pure Python, no deps):

```bash
python3 scripts/find_glyph.py /usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf alarm
# → U+F0020 md-alarm, U+F0023 md-alarm_off, U+F078E md-alarm_bell ...
```

Codepoints ≥ U+10000 need surrogate escapes in QML: U+F0020 → `"\uDB80\uDC20"`. BMP nerd glyphs (U+F0xxx) work as literal characters (official plugins embed literals).

Surrogate recipe: `hi = 0xD800 + ((cp - 0x10000) >> 10)`, `lo = 0xDC00 + ((cp - 0x10000) & 0x3FF)`.

## Install / uninstall (ask user consent first — it modifies their shell config)

Install: backup `~/.config/omarchy/shell.json` → `cp -r <plugin-dir> ~/.config/omarchy/plugins/` → `omarchy-shell shell rescanPlugins` → `omarchy plugin enable <id>` → `omarchy restart shell` → user verifies icon.

Uninstall: `omarchy plugin disable <id>` → `gio trash ~/.config/omarchy/plugins/<dir>` → restore `shell.json` from backup if needed.

## Publishing to GitHub

Repo layout: `README.md` (install = clone → cp → rescan → enable; uninstall) + `<plugin-dir>/` (manifest + QML + assets) + `tools/` (asset generation scripts, e.g. ffmpeg chime synthesis). Keep the chime/sound parameters as env vars so users can retune without editing QML.
