<h1 align="center">Bilibili Copy Extractor</h1>

<p align="center">
  <strong>English</strong>
  &nbsp;·&nbsp;
  <a href="./README.md">简体中文</a>
</p>

<p align="center">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-blue?style=flat-square&amp;labelColor=1b1f23">
  <img alt="python" src="https://img.shields.io/badge/python-3.7%2B-3776AB?style=flat-square&amp;labelColor=1b1f23">
  <img alt="dependencies" src="https://img.shields.io/badge/dependencies-0-brightgreen?style=flat-square&amp;labelColor=1b1f23">
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-6e7781?style=flat-square&amp;labelColor=1b1f23">
  <img alt="subtitles" src="https://img.shields.io/badge/B%E7%AB%99-official%20subtitles-FB7299?style=flat-square&amp;labelColor=1b1f23">
  <img alt="credential" src="https://img.shields.io/badge/login-own%20SESSDATA%20only-00A1D6?style=flat-square&amp;labelColor=1b1f23">
</p>

<p align="center"><sub>Pure Python standard library · zero third-party dependencies · no third-party login, no API key, no sign-up</sub></p>

<br/>

Batch-export a Bilibili video's official subtitles into a Markdown copy package — one Markdown file per video plus an index you can scan.

It prefers human-contributed CC subtitles and falls back to Bilibili's own AI-generated subtitles. Works for a single video, the latest N uploads of a creator, everything they ever published, top videos by views or likes, a date range, or a whole collection / series.

Language support is limited to whatever Bilibili itself produced — Chinese for essentially every video, occasionally other languages when the uploader supplied them.

## What it does

| Use case | Command |
|---|---|
| Single video | `python scripts/bili_copy.py "https://www.bilibili.com/video/BV1xx411c7mD"` |
| Latest N uploads | `python scripts/bili_copy.py --up <creator> --limit 10` |
| Every upload | `python scripts/bili_copy.py --up <creator> --all --yes` |
| Most liked | `python scripts/bili_copy.py --up <creator> --sort like --limit 10` |
| Most viewed | `python scripts/bili_copy.py --up <creator> --sort play --limit 10` |
| Date range | `python scripts/bili_copy.py --up <creator> --since 2026-10-01 --until 2026-10-31` |
| One collection / series | `python scripts/bili_copy.py --up <creator> --collection <name>` |
| Append into an existing folder | `python scripts/bili_copy.py --up <creator> --limit 15 --into <folder>` |
| Preview only, download nothing | `python scripts/bili_copy.py --up <creator> --limit 10 --dry-run` |

`--up` accepts a creator name, a uid, or a space URL. Add `--zip` to pack the output folder, `--srt` to also emit timestamped files, `--resume` to continue an interrupted run, `--workers` to tune concurrency.

Full help — output layout, naming rules, how to get SESSDATA, FAQ:

```bash
python scripts/bili_copy.py help
```

## Requirements

| Item | Requirement |
|---|---|
| Python | **3.7+** (3.9 / 3.11 / 3.12 all fine) |
| Third-party packages | **None.** Do not `pip install` anything |
| ffmpeg / yt-dlp | **Not needed.** Only the official subtitle JSON is read — no video, no audio |
| Browser automation | **Not needed.** No Selenium, no Playwright |
| Network | Access to `api.bilibili.com`, `www.bilibili.com` and the subtitle CDN |
| Disk | Roughly 20–30 KB of Markdown per 20–30 minute video |

## Install

**Option 1 — SkillHub community registry**

```bash
skillhub install bilibili-copy-extractor
```

**Option 2 — manual, into a skills directory**

```bash
git clone https://github.com/cincoutstream/bilibili-copy-extractor.git
```

Then copy the whole folder into the skills directory of your agent runtime:

- OpenBitFun: `%APPDATA%\openbitfun\skills\bilibili-copy-extractor\`
- macOS / Linux: `~/.config/openbitfun/skills/bilibili-copy-extractor/`

**Option 3 — just run it**

Installation is optional. `python scripts/bili_copy.py --help` works from a bare checkout.

## Prerequisite: SESSDATA

No third-party login, no API key, no account to create. The only credential needed is a `SESSDATA` cookie from your own Bilibili account.

Bilibili gates subtitle URLs behind the login state: when logged out, `subtitle_url` comes back as an empty string and `is_lock` is `true`. That is an API-level restriction, not a bug in this script — every tool hits it.

How to get it (do this yourself; never paste the cookie value into a chat):

1. Log in at `bilibili.com` → `F12` → **Application** → **Cookies** → `https://www.bilibili.com`
2. Copy the value of the `SESSDATA` row
3. Store it in any one of these places:
   - the `--sessdata` flag
   - the `BILI_SESSDATA` environment variable
   - a `sessdata.txt` file in the working directory

Priority: flag > environment variable > file.

## Output layout

One folder per run, one Markdown file per video, plus an index:

```
<creator>_最近10条视频文案_20261031/
    01_<video title>_2026-10-31.md
    02_<video title>_2026-10-30.md
    _index.md        sortable table, clickable links to every file
    _manifest.json   the same data, machine-readable
    _progress.json   resume bookkeeping — do not edit by hand
```

Every Markdown file opens with YAML front matter (bvid, title, creator, publish time, duration, views / likes / favorites / coins / danmaku / comments, subtitle source, word count, coverage) followed by the transcript split into paragraphs.

### Naming rules

Folder: `{creator}_{batch}视频文案_{YYYYMMDD}` — the literal word `视频文案` ("video copy") is kept in the filename regardless of interface language.

| Batch | Example folder |
|---|---|
| Single video | `<creator>_2026-10-31_<video title>` |
| Latest N | `<creator>_最近10条视频文案_20261031` |
| Oldest N | `<creator>_最早10条视频文案_20261031` |
| Every upload | `<creator>_全部N条视频文案_20261031` |
| Most liked | `<creator>_点赞最多10条视频文案_20261031` |
| Most viewed | `<creator>_播放最多10条视频文案_20261031` |
| Date range | `<creator>_2026-10-20至2026-10-25视频文案_20261031` |
| Collection | `<creator>_合集-<collection>视频文案_20261031` |

File: `{NN}_{title}_{YYYY-MM-DD}.md`

- **NN** ranks the video inside the batch and matches the `_index.md` table, so the folder's alphabetical order is your ranking
- **Title** comes right after the number so you can recognise a file at a glance; truncated to 50 characters, Windows-illegal characters (`\ / : * ? " < > |`) replaced
- **Date** goes last, so you can see when it was published without opening the file

### Appending into the same folder (`--into`)

When you would rather grow one project folder than create a new one every run:

```bash
python scripts/bili_copy.py --up <creator> --limit 10                                  # first run: normal folder
python scripts/bili_copy.py --up <creator> --limit 15 --into <folder name or path>      # later runs: append
```

- Videos already in the folder are deduplicated by **bvid** and skipped — nothing is downloaded twice
- New entries continue after the highest existing number (10 items → the next is `11`); existing files are never renamed
- `_index.md` and `_manifest.json` are rewritten with old and new entries merged
- The folder name is the project name, so it does not change when the item count does

Drop `--into` to start a fresh batch folder instead.

## Sorting and cost

| Sort | Cost | Notes |
|---|---|---|
| `newest` / `oldest` | one request | fetches only what you asked for |
| `play` | full pagination — slower as the upload count grows | the list endpoint already carries view counts (accurate), but finding the global maximum means walking every page |
| `like` | one lookup per video | the list endpoint has no like count at all; use `--scan N` to cap the candidate pool |

Creator upload lists are cached for 30 minutes, so a repeated query returns instantly.

## Known limitations

- **AI subtitles do not exist at upload time.** Bilibili generates them only after someone opens the player and picks 字幕 → 中文 (about 10–30 seconds). After that they are cached for everyone. When a video has none, the script writes a note file and records it in the index — trigger it in the player once, then re-run.
- **Homophone errors come from Bilibili's transcription,** not from extraction. Cleaning them up requires a language-model pass afterwards.
- **Some AI subtitles carry no punctuation at all.** Paragraph breaks are restored with a three-tier rule: sentence-final punctuation → discourse markers → function-word boundaries.
- **The creator-space API is rate limited.** Push `--workers` too high and you will get HTTP 412.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Empty subtitle list | No SESSDATA, or it expired — copy a fresh one |
| `code=-352` / `HTTP 412` | Rate limited; wait a few minutes or lower `--workers` |
| A collection appears to contain 1 episode | The name did not match; run `--list-collections` to see exact names |
| Fewer videos than expected | Check `--limit`; date ranges auto-expand, other modes fetch exactly what you ask for |

## Security

`sessdata.txt` is a login credential: it is written locally only, never logged, never echoed. Delete it when you are done, or log out on Bilibili to invalidate it immediately.

`.gitignore` already excludes `sessdata.txt`, but **double-check before every commit** that no credential slipped into the repository.

## License

[MIT](LICENSE)
