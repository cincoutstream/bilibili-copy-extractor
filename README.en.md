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

## Highlights

| Highlight | Detail |
|---|---|
| Official subtitles | Reads the human CC track or the AI-generated track from Bilibili instead of re-transcribing audio, so wording matches the site |
| Batch extraction from one sentence | Name the creator and the count; links do not have to be pasted one by one |
| Readable output | One Markdown file per video, opening with title, publish date, view and like counts, followed by the segmented transcript |
| The folder is the index | Sequence number first and publish date last, so alphabetical order equals rank order; a clickable index table is included |
| Ranking and collections | Take the top N by likes or views, or extract a single collection or series |
| Resumable | A batch that stops midway skips completed videos when it is started again |
| Packageable | The result can be zipped, with subtitle timeline files attached on request |

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
| Collection or series | Export the subtitles of the <series> series from <creator> |
| List collections | List the collections and series of <creator> |
| List only | List the titles of the 10 most recent videos from <creator> before extracting |
| Append to an existing folder | Add the 15 most recent videos of <creator> to the folder from the last run |
| Packaging and timeline | Package the result as a zip and include the subtitle timeline files |
| Resume after interruption | The previous run stopped midway; continue from the completed position |
| Output location | Save the result under D:\data |

Replace `<creator>` with a name, uid, or space URL. Output goes to a `bili文案` folder under the working directory unless another location is given.

## Requirements

Python 3.7 or later.

## Install

### Option 1: Let an agent install it

Send the following message in the conversation; the agent performs the installation:

```
Install bilibili-copy-extractor as a skill.
Prefer GitHub: https://github.com/cincoutstream/bilibili-copy-extractor
If GitHub is unreachable, install the same skill from SkillHub: skillhub install @user_c14bff27/bilibili-copy-extractor
It contains SKILL.md and scripts/bili_copy.py. When the installation is done, tell me which requests I can make to extract text from Bilibili videos.
```

This option assumes no particular agent tool; any agent that can install skills can act on it. GitHub is unreachable on some networks, in which case the SkillHub package holds the same content.

### Option 2: Install it yourself

From SkillHub:

```
skillhub install @user_c14bff27/bilibili-copy-extractor
```

Alternatively download the repository and place the whole directory in the skills directory of the agent tool in use. The location is documented by that tool.

## Credential and safety

The only credential required is the `SESSDATA` cookie of the user's own Bilibili account.

Bilibili returns subtitle URLs only to signed-in requests. An anonymous request succeeds but yields an empty subtitle list. This is a server-side restriction, not a defect of the tool.

Steps:

1. Sign in to `bilibili.com` in a browser and press F12 to open the developer tools
2. Open Application, then Cookies, and select the `https://www.bilibili.com` domain
3. Copy the Value of the `SESSDATA` row
4. Send the copied value to the agent, which stores it on the local machine

The value is equivalent to an account credential. Do not paste it into group chats or public channels. It stays on the local machine, is never written to logs, and is never echoed in the terminal or the conversation. It can be removed after the run, or invalidated immediately by signing out of Bilibili.

## Walkthrough

A complete extraction, start to finish.

1. State the request. For a single video, the link is enough:

```
Export the subtitles of this video as text: https://www.bilibili.com/video/BV1xx411c7mD
```

For a batch from one creator, name the creator and the count:

```
Export the 10 most-liked videos of <creator> as text
```

2. Provide the credential on first use. Copy `SESSDATA` as described in the previous section and send it to the agent; later runs reuse it.

3. Wait for the run to finish. A batch is processed video by video, so a large batch takes a while. A run of more than 100 videos, or a like-sorted run over more than 400 candidates, reports the expected scale and asks for confirmation first.

4. Collect the output. The result lands in a `bili文案` folder under the working directory:

```
<creator>_点赞最多10条视频文案_20261031/
    01_<video title>_2026-10-31.md
    02_<video title>_2026-10-29.md
    _index.md
```

Open `_index.md` for a table in rank order with links to each file. The folder itself can be archived as is.

If a video yields no subtitles, Bilibili has probably not generated its AI track yet: open the video in the player, select 字幕 then 中文 once, and ask the agent to retry.

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

When appending to an existing folder, the folder name stays the same, new entries continue after the highest existing number, and videos already present are not extracted again.

## License

[MIT](LICENSE)
