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
  <img alt="subtitles" src="https://img.shields.io/badge/B%E7%AB%99-%E5%AE%98%E6%96%B9%E5%AD%97%E5%B9%95-FB7299?style=flat-square&amp;labelColor=1b1f23">
  <img alt="credential" src="https://img.shields.io/badge/%E7%99%BB%E5%BD%95-%E5%8F%AA%E9%9C%80%E8%87%AA%E5%B7%B1%E7%9A%84%20SESSDATA-fb7299?style=flat-square&amp;labelColor=1b1f23">
</p>

<p align="center"><sub>Python 3.7+ · standard library only · no third-party dependencies</sub></p>

<br/>

## Overview

Exports Bilibili subtitles to Markdown: one md file per video, plus an index. Subtitles come from the human-contributed CC track or from Bilibili's AI-generated track. The CC track is preferred and the AI track is used when no CC track exists. The tool performs no speech recognition and produces no subtitle text of its own.

Subtitle language follows whatever tracks Bilibili provides. Nearly every video is Chinese; a small number carry another language uploaded by the creator.

## What it does

| Use case | Command |
|---|---|
| Single video | `python scripts/bili_copy.py "https://www.bilibili.com/video/BV1xx411c7mD"` |
| Latest N uploads | `python scripts/bili_copy.py --up <creator> --limit 10` |
| All uploads | `python scripts/bili_copy.py --up <creator> --all --yes` |
| Ranked by likes | `python scripts/bili_copy.py --up <creator> --sort like --limit 10` |
| Ranked by views | `python scripts/bili_copy.py --up <creator> --sort play --limit 10` |
| Date range | `python scripts/bili_copy.py --up <creator> --since 2026-10-01 --until 2026-10-31` |
| Named collection or series | `python scripts/bili_copy.py --up <creator> --collection <name>` |
| Append to an existing folder | `python scripts/bili_copy.py --up <creator> --limit 15 --into <folder>` |
| List only, no download | `python scripts/bili_copy.py --up <creator> --limit 10 --dry-run` |

`--up` accepts a creator name, a uid, or a space URL. `--zip` packages the output as a zip archive, `--srt` writes a timeline file, `--resume` skips videos already extracted, `--workers` sets the concurrency, and `--outdir` sets the output root (default `./bili文案`). Full usage:

```bash
python scripts/bili_copy.py help
```

## Requirements

| Item | Requirement |
|---|---|
| Python | 3.7 or later |
| Third-party packages | None; `pip install` is not needed |
| ffmpeg / yt-dlp | Not required; only subtitle JSON is read, no audio or video is downloaded |
| Browser automation | Not required; no dependency on Selenium or Playwright |
| Network | Access to `api.bilibili.com`, `www.bilibili.com`, and the subtitle CDN |
| Disk | Roughly 20 to 30 KB for a 20 to 30 minute video |

## Install

### Option 1: SkillHub

```bash
skillhub install bilibili-copy-extractor
```

### Option 2: Manual copy

```bash
git clone https://github.com/cincoutstream/bilibili-copy-extractor.git
```

Place the directory in the skills folder of the runtime in use:

| Runtime | Path |
|---|---|
| OpenBitFun | `%APPDATA%\openbitfun\skills\bilibili-copy-extractor\` |
| macOS / Linux | `~/.config/openbitfun/skills/bilibili-copy-extractor/` |

### Option 3: Run without installing

From the repository root, run `python scripts/bili_copy.py --help`.

## Credentials

The only credential required is the `SESSDATA` cookie of a Bilibili account. No API key and no third-party account are involved.

Bilibili returns subtitle URLs only to signed-in clients. Without a session, `subtitle_url` is an empty string and `is_lock` is `true`. This is a restriction on the server side, not a defect in the script.

Steps:

1. Sign in to `bilibili.com` in a browser and open the developer tools with F12
2. Go to Application, then Cookies, and select the `https://www.bilibili.com` domain
3. Copy the Value of the `SESSDATA` row
4. Supply the value in any one of the following ways

| Method | Usage |
|---|---|
| Command-line argument | `--sessdata <value>` |
| Environment variable | `BILI_SESSDATA` |
| File | `sessdata.txt` in the current directory |

The lookup order is command-line argument, then environment variable, then file. The value is equivalent to an account credential; do not paste it into chat tools or public channels.

## Output layout

Each run writes one folder:

```
<creator>_最近10条视频文案_20261031/
    01_<video title>_2026-10-31.md
    02_<video title>_2026-10-30.md
    _index.md        sortable table linking to each file
    _manifest.json   the same data, machine readable
    _progress.json   resume state, do not edit by hand
```

Folder and file names are generated in Chinese, matching the interface language of the source site. Each md file opens with YAML front matter carrying the bvid, title, creator, publish date, duration, view, like, favourite, coin, danmaku and comment counts, subtitle source, word count and coverage, followed by the segmented transcript.

## Naming rules

The folder name is `{creator}_{batch}视频文案_{date}`:

| Use case | Folder name example |
|---|---|
| Single video | `<creator>_2026-10-31_<video title>` |
| Latest N | `<creator>_最近10条视频文案_20261031` |
| Earliest N | `<creator>_最早10条视频文案_20261031` |
| All uploads | `<creator>_全部N条视频文案_20261031` |
| Most liked | `<creator>_点赞最多10条视频文案_20261031` |
| Most viewed | `<creator>_播放最多10条视频文案_20261031` |
| Date range | `<creator>_2026-10-20至2026-10-25视频文案_20261031` |
| Collection or series | `<creator>_合集-<name>视频文案_20261031` |

The file name is `{nn}_{title}_{publish date}.md`:

| Part | Rule |
|---|---|
| Sequence number | Rank within the batch, matching the `_index.md` table so that alphabetical folder order equals rank order |
| Title | Follows the sequence number, truncated to 50 characters, with the Windows-reserved characters `\ / : * ? " < > \|` replaced |
| Date | Placed last, so the publish date is readable without opening the file |

## Appending to an existing folder

With `--into`, output goes into one folder instead of a new batch folder:

```bash
# First run: creates the folder
python scripts/bili_copy.py --up <creator> --limit 10

# Later runs: append into that folder
python scripts/bili_copy.py --up <creator> --limit 15 --into <folder name or path>
```

Rules applied when appending:

| Case | Behaviour |
|---|---|
| Video already in the folder | Skipped after a bvid check, not downloaded again |
| Numbering of new entries | Continues after the highest existing number; existing files are not renamed |
| `_index.md` and `_manifest.json` | Rewritten with the old and new entries merged |
| Folder name | Unchanged, regardless of entry count |

Without `--into`, a new batch folder is created.

## Sorting and cost

| Sort key | Cost | Notes |
|---|---|---|
| `newest` / `oldest` | One request | Reads only the requested number of entries |
| `play` | Requires paging through the whole list; longer for prolific creators | The list endpoint carries view counts, so the data is exact |
| `like` | One request per video | The list endpoint carries no like counts; use `--scan N` to bound the candidate pool |

The creator upload list is cached for 30 minutes, so repeated queries issue no new requests.

## Known limitations

- The AI track has to be generated first. Bilibili creates it only after a user selects 字幕 then 中文 in the player, which takes about 10 to 30 seconds on first use and is then cached for everyone. When no track is available the script writes a note file and records it in the index; trigger the track in the player and run the command again.
- Homophone errors come from Bilibili's own transcription, not from extraction. Cleaning them up requires a separate language model pass.
- Some AI tracks carry no punctuation. The script restores segmentation using sentence-ending punctuation, discourse markers, and function-word boundaries, in that order.
- The space API is rate limited. A high `--workers` value can trigger HTTP 412.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Empty subtitle list | Missing or expired SESSDATA; fetch the value again |
| `code=-352` or `HTTP 412` | Rate limiting; wait a few minutes and retry, or lower `--workers` |
| A collection returns 1 video | The name did not match; run `--list-collections` to get the exact name |
| Fewer videos than expected | Check `--limit`. The date-range mode expands automatically; other modes take exactly the requested count |

## Security

`sessdata.txt` is equivalent to an account credential. The script writes it only to local disk, never to logs, and never echoes it to the terminal. Delete the file when finished, or sign out of Bilibili to invalidate it immediately.

`.gitignore` excludes `sessdata.txt`. Verify before committing that no credential has reached the repository.

## License

[MIT](LICENSE)
