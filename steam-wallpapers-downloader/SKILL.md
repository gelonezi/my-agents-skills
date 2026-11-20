---
name: steam-wallpapers-downloader
description: Download a Steam game's trading card wallpapers, profile backgrounds, badges and emoticons from steamcardexchange.net into the user's wallpapers folder, each file named after its card. Use whenever the user asks to download or save the wallpapers, card art, backgrounds, badges or emoticons of a game (e.g. "download the wallpapers from the game Monster Train", "get the Hades card art"), or sends a steamcardexchange.net link or Steam appid for that purpose, even if they don't mention the site. Works from a game name (searches and asks which game) or a direct link, for one or several games.
---

# Steam Card Exchange image downloader

Saves a game's full-size card art, profile backgrounds, and small badge/emoticon images into
`<root>/<Game Title>/`, each file named after its item. The source is always
https://www.steamcardexchange.net/.

All the scraping and downloading is done by `scripts/sce.py`, which sits next to this file. It needs only
Python 3 (standard library) and works on Linux, macOS and Windows. Use it rather than writing new scraping
code: it already handles the site's quirks. Call it by its full path, e.g.
`python3 "<this skill's folder>/scripts/sce.py" ...` (on Windows the interpreter is usually `python` or `py`).

## Workflow

### 1. Make sure a download folder is set

Run `sce.py config`. If it prints `root=NOT SET`, ask the user where images should be saved, offering the
printed `suggested_root` (the Pictures/wallpapers folder of their home) as the default, then store the answer
with `sce.py config --root "<folder>"`. This is asked once per machine; afterwards just use it. If the user
names a different folder for one request, pass `--root "<folder>"` to `download` instead of changing the
config.

### 2. Identify the game(s)

- **Link or appid given:** run `sce.py info <link|appid> [more...]` to get each title and file counts.
- **Only a name given:** run `sce.py search "<name>"`. It prints the 5 best matches (best first), one per
  line as `appid<TAB>title<TAB>link`. If the right game clearly isn't there, retry with a shorter or
  alternate spelling, or `--limit 15`.

### 3. Confirm before downloading

The user wants to approve the game before anything is saved, because names are ambiguous (sequels,
editions, similarly named games).

- **After a search:** let the user tick which results to download using a multiple-choice question with
  checkboxes (the AskUserQuestion tool with `multiSelect: true`, one option per result, labelled with the
  title and described with the appid). Best match first. That tool takes at most 4 options, so offer the
  top 4 and mention the 5th in the question text — the user can type it via "Other". If no such tool is
  available, show a numbered list and ask for the numbers. The user may pick several.
- **After a direct link:** one short line naming the game title(s) is enough ("That's Magicka 2 — go?").
  When several links are sent, confirm them all together in one list, not one by one.

### 4. Download

Run a single command for everything confirmed: `sce.py download <appid|link> [<appid|link> ...]`.
Extras: `--dry-run` previews without saving; `--title "Name"` overrides the folder name (single game only).

### 5. Report

The script ends with one combined report. Relay it as a short summary per game: folder, how many files
were downloaded, and — these matter to the user, don't drop them — every file skipped because it already
existed (existing files are never overwritten), every failure, any `NOTE:` lines, and which groups the game
doesn't have on the site.

## What gets saved

| Folder | Group on the site | Notes |
|---|---|---|
| `Trading Cards/` | Trading Cards | Full-size image behind the "Wallpaper" arrow link (the image popup shows the same file). |
| `Backgrounds/` | Backgrounds | Full-size image behind the "Wallpaper" arrow link. |
| `Emoticons/` | Badges, Foil Badges, Emoticons | Small images. Foil badges get ` (Foil)` appended so they don't collide with regular badges. Emoticon names lose the `:colons:` and gain a capital first letter (`:naru:` → `Naru`). |

Details worth knowing when the user asks "why":

- Files keep the site's original extension (cards/backgrounds are usually `.jpg`, badges/emoticons `.png`);
  when a link has no extension the real type is detected from the downloaded data.
- Characters that are illegal in filenames on any OS (`/ \ : * ? " < > |`) become `-`.
- Foil Trading Cards are skipped on purpose: they link to the very same images as Trading Cards.
- Only the trading-card series is used. Points-shop groups (animated stickers, animated backgrounds, avatar
  frames, animated avatars) and game-specific extras (e.g. Counter-Strike chat/flair emoticons) are not
  downloaded; the user never asked for them. Offer nothing more unless they ask.
- If a card or background has no wallpaper version on the site, the small item image is saved instead and a
  `NOTE:` says so — pass that on, since it won't be wallpaper quality.
- Games with several card series are handled; a repeated name gets ` (2)` rather than overwriting.

## If something looks wrong

Zero files for a game that clearly has cards, or a title of `None`, most likely means the site changed its
page layout. Say so instead of guessing; look at the page HTML and fix `scripts/sce.py` (sections are found
by their `#series-N-<kind>` anchors, items by their name `<div>`).
