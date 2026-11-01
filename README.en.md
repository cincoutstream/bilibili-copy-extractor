<h1 align="center">Bilibili Copy Extractor</h1>

<p align="center">
  <strong>English</strong>
  &nbsp;·&nbsp;
  <a href="./README.md">简体中文</a>
</p>

<p align="center">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-blue?style=flat-square&amp;labelColor=1b1f23">
  <img alt="python" src="https://img.shields.io/badge/python-3.7%2B-3776AB?style=flat-square&amp;labelColor=1b1f23">
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-6e7781?style=flat-square&amp;labelColor=1b1f23">
  <img alt="subtitles" src="https://img.shields.io/badge/B%E7%AB%99-%E5%AE%98%E6%96%B9%E5%AD%97%E5%B9%95-FB7299?style=flat-square&amp;labelColor=1b1f23">
  <img alt="credential" src="https://img.shields.io/badge/%E7%99%BB%E5%BD%95-%E5%8F%AA%E9%9C%80%E8%87%AA%E5%B7%B1%E7%9A%84%20SESSDATA-fb7299?style=flat-square&amp;labelColor=1b1f23">
</p>

<p align="center"><sub>Python 3.7+</sub></p>

<br/>

## Overview

Exports Bilibili subtitles to Markdown: one md file per video, plus an index table and a machine-readable manifest. Subtitles come from the human-contributed CC track or from Bilibili's AI-generated track. The CC track is preferred and the AI track is used when no CC track exists. The tool reads only the subtitle data Bilibili already provides and performs no speech recognition.

Subtitle language follows the tracks Bilibili provides. Nearly every video is Chinese; a small number carry another language uploaded by the creator.

## What the skill can do

The left column names the task, the right column gives a request that can be sent to an agent as it stands.

| Task | Example request |
|---|---|
| Single video | Export the subtitles of this video as text: <video URL> |
| Latest uploads | Export the subtitles of the 10 most recent videos from <creator> |
| All uploads | Export the subtitles of every upload from <creator> |
| Top videos by likes | Export the 10 most-liked videos of <creator> as text |
| Top videos by views | Export the 10 most-viewed videos of <creator> as text |
| Date range | Export the videos <creator> published in October 2026 |
| Collection or series | Export the subtitles of the "<series>" series from <creator> |
| List collections | List the collections and series of <creator> |
| List only | List the titles of the 10 most recent videos from <creator> before extracting |
| Append to an existing folder | Add the 15 most recent videos of <creator> to the folder from the last run |
| Packaging and timeline | Package the result as a zip and include the subtitle timeline files |
| Resume after interruption | The previous run stopped midway; continue from the completed position |
| Output location | Save the result under D:\data |

A creator can be identified by name, uid, or space URL. Output goes to a `bili文案` folder under the working directory unless another location is given.

## Requirements

Python 3.7 or later.

## Install

### Option 1: Let an agent install it

Send the following message in the conversation; the agent performs the installation:

```
Install https://github.com/cincoutstream/bilibili-copy-extractor as a skill.
It contains SKILL.md and scripts/bili_copy.py. When the installation is done, tell me which requests I can make to extract text from Bilibili videos.
```

This option assumes no particular agent tool; any agent that can install skills can act on it.

### Option 2: SkillHub

```
skillhub install bilibili-copy-extractor
```

### Option 3: Manual placement

Download the repository and place the whole directory in the skills directory of the agent tool in use. The location is documented by that tool.

## Credential and safety

The only credential required is the `SESSDATA` cookie of the user's own Bilibili account.

Bilibili returns subtitle URLs only to signed-in requests. An anonymous request succeeds but yields an empty subtitle list. This is a server-side restriction, not a defect of the tool.

Steps:

1. Sign in to `bilibili.com` in a browser and press F12 to open the developer tools
2. Open Application, then Cookies, and select the `https://www.bilibili.com` domain
3. Copy the Value of the `SESSDATA` row
4. Send the copied value to the agent, which stores it on the local machine

The value is equivalent to an account credential. Do not paste it into group chats or public channels. It stays on the local machine, is never written to logs, and is never echoed in the terminal or the conversation. It can be removed after the run, or invalidated immediately by signing out of Bilibili.

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

Folder and file names are generated in Chinese, following the interface language of the source site. Each Markdown file opens with a field block carrying the bvid, title, creator, publish date, duration, view, like, favourite, coin, danmaku and comment counts, subtitle source, word count and coverage, followed by the segmented transcript. When packaging is requested, the zip archive is written next to the folder.

## Naming rules

Batch folders are named from the creator, a batch label and the generation date. A single video uses its own form:

| Task | Folder name example |
|---|---|
| Single video | `<creator>_2026-10-31_<video title>` |
| Latest N | `<creator>_最近10条视频文案_20261031` |
| Earliest N | `<creator>_最早10条视频文案_20261031` |
| All uploads | `<creator>_全部N条视频文案_20261031` |
| Most liked | `<creator>_点赞最多10条视频文案_20261031` |
| Most viewed | `<creator>_播放最多10条视频文案_20261031` |
| Date range | `<creator>_2026-10-20至2026-10-25视频文案_20261031` |
| Collection or series | `<creator>_合集-<name>视频文案_20261031` |

File names follow `{index}_{title}_{publish date}.md`:

| Part | Rule |
|---|---|
| Index | Rank within the batch, matching the row order of the index table, so that name order in a file manager equals rank order. Padded to two digits; beyond 99 entries the width grows to fit |
| Title | Follows the index, truncated to 50 characters. The Windows-reserved characters `\ / : * ? " < > \|` are replaced with underscores |
| Date | Placed last, so the publish date is visible from the directory listing |

## Appending to an existing folder

By default every run creates a new folder. To merge newly extracted videos into an existing folder, name that folder in the request; the output goes into it and no new batch folder is created.

The following rules apply:

| Case | Behaviour |
|---|---|
| Video already in the folder | Skipped after a bvid check, not extracted again |
| Numbering of new entries | Continues after the highest existing number; existing files are not renamed |
| Index and manifest files | Rewritten with the old and new entries merged |
| Folder name | Unchanged regardless of entry count. A folder named `最近10条` may end up holding 15 files |
| Folder does not exist | Created automatically, so the folder can serve as a long-running project directory |

Without a target folder, a new batch folder is created.

## Sort order and run time

| Sort order | Run time | Notes |
|---|---|---|
| Latest or earliest N | Shortest; only the requested entries are read | The upload list is not traversed in full |
| By views | Longer for creators with many uploads | The whole list must be traversed to find the highest view count |
| By likes | Longer for larger batches | Like counts are absent from the list data and must be read per video. Candidates are drawn from the 200 most recent uploads by default, and a wider range can be requested |

A run is confirmed first when it would extract more than 100 videos, and when sorting by likes over a candidate range of more than 400 videos.

The result of a full upload-list read is cached for 30 minutes, so repeat extractions for the same creator within that window reuse it.

## Known limitations

- The AI track must exist before it can be read. Bilibili creates it only after a user selects 字幕 then 中文 in the player, which takes about 10 to 30 seconds the first time and is then available to everyone. When no track is available, a note file is written into the folder and recorded in the index; trigger the track in the player and extract again.
- Homophone errors come from Bilibili's own transcription, not from extraction. Cleaning them up requires an additional language model pass.
- Some AI tracks carry no punctuation. Segmentation is restored from sentence-ending punctuation, discourse markers and function-word boundaries.
- The API is rate limited. Processing too many videos at once triggers risk control, which appears as a rejected request. Wait a few minutes and retry, or process fewer videos at a time in several batches.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Empty subtitle list | Missing or expired SESSDATA; obtain the value again and retry |
| Request rejected with 412 or -352 | Bilibili risk control; wait a few minutes and retry, or process fewer videos at a time in several batches |
| A collection returns 1 video | The name did not match. Ask the agent to list the collections and series of the creator, then use the exact name |
| Fewer videos than expected | Check the requested count. The date-range mode expands automatically; other modes take exactly the requested count |

## License

[MIT](LICENSE)
