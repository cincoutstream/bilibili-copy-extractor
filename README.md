<h1 align="center">B站视频文案提取</h1>

<p align="center">
  <a href="./README.en.md">English</a>
  &nbsp;·&nbsp;
  <strong>简体中文</strong>
</p>

<p align="center">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-blue?style=flat-square&amp;labelColor=1b1f23">
  <img alt="python" src="https://img.shields.io/badge/python-3.7%2B-3776AB?style=flat-square&amp;labelColor=1b1f23">
  <img alt="dependencies" src="https://img.shields.io/badge/dependencies-0-brightgreen?style=flat-square&amp;labelColor=1b1f23">
  <img alt="platform" src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-6e7781?style=flat-square&amp;labelColor=1b1f23">
  <img alt="subtitles" src="https://img.shields.io/badge/B%E7%AB%99-%E5%AE%98%E6%96%B9%E5%AD%97%E5%B9%95-FB7299?style=flat-square&amp;labelColor=1b1f23">
  <img alt="credential" src="https://img.shields.io/badge/%E7%99%BB%E5%BD%95-%E5%8F%AA%E9%9C%80%E8%87%AA%E5%B7%B1%E7%9A%84%20SESSDATA-fb7299?style=flat-square&amp;labelColor=1b1f23">
</p>

<p align="center"><sub>Python 3.7+ · 仅用标准库 · 无第三方依赖</sub></p>

<br/>

## 概述

把 B站视频的官方字幕导出为 Markdown 文档：每个视频生成一个 md 文件，同时生成一份索引。字幕取自 B站提供的人工 CC 字幕或 AI 自动生成字幕，有人工 CC 字幕时优先使用，没有时回退到 AI 字幕。本工具不做语音识别，也不生成字幕内容。

字幕语言以 B站提供的字幕轨为准。绝大多数视频为中文，个别视频由 UP 主上传了其他语言。

## 功能

| 场景 | 命令 |
|---|---|
| 单个视频 | `python scripts/bili_copy.py "https://www.bilibili.com/video/BV1xx411c7mD"` |
| UP 主最近 N 条 | `python scripts/bili_copy.py --up <UP主> --limit 10` |
| UP 主全部投稿 | `python scripts/bili_copy.py --up <UP主> --all --yes` |
| 按点赞数排序 | `python scripts/bili_copy.py --up <UP主> --sort like --limit 10` |
| 按播放量排序 | `python scripts/bili_copy.py --up <UP主> --sort play --limit 10` |
| 指定日期区间 | `python scripts/bili_copy.py --up <UP主> --since 2026-10-01 --until 2026-10-31` |
| 指定合集或系列 | `python scripts/bili_copy.py --up <UP主> --collection <合集名>` |
| 追加到已有文件夹 | `python scripts/bili_copy.py --up <UP主> --limit 15 --into <文件夹>` |
| 只列出清单 | `python scripts/bili_copy.py --up <UP主> --limit 10 --dry-run` |

`--up` 接受 UP 主名称、uid 或空间主页链接。`--zip` 将输出打包为 zip，`--srt` 附带时间轴文件，`--resume` 跳过已提取的视频，`--workers` 设置并发数，`--outdir` 指定输出根目录（默认 `./bili文案`）。完整说明：

```bash
python scripts/bili_copy.py help
```

## 环境要求

| 项 | 要求 |
|---|---|
| Python | 3.7 及以上 |
| 第三方包 | 无，不需要执行 `pip install` |
| ffmpeg / yt-dlp | 不需要，只读取字幕 JSON，不下载音视频 |
| 浏览器自动化 | 不需要，不依赖 Selenium 或 Playwright |
| 网络 | 可访问 `api.bilibili.com`、`www.bilibili.com` 及字幕 CDN |
| 磁盘 | 20 至 30 分钟的视频约占用 20 至 30 KB |

## 安装

### 方式一：SkillHub

```bash
skillhub install bilibili-copy-extractor
```

### 方式二：手动复制

```bash
git clone https://github.com/cincoutstream/bilibili-copy-extractor.git
```

将整个目录放入所用运行时的技能目录：

| 运行时 | 路径 |
|---|---|
| OpenBitFun | `%APPDATA%\openbitfun\skills\bilibili-copy-extractor\` |
| macOS / Linux | `~/.config/openbitfun/skills/bilibili-copy-extractor/` |

### 方式三：免安装运行

在仓库目录直接执行 `python scripts/bili_copy.py --help`。

## 凭据

运行所需凭据只有一项：使用者自己 B站账号的 `SESSDATA` cookie。其余凭据一概不用。

B站仅在登录态下返回字幕地址：未登录时接口返回的 `subtitle_url` 为空字符串，`is_lock` 为 `true`。这是接口侧的限制，与脚本实现无关。

获取步骤：

1. 在浏览器登录 `bilibili.com`，按 F12 打开开发者工具
2. 进入 Application，选择 Cookies，域名选 `https://www.bilibili.com`
3. 复制 `SESSDATA` 一行的 Value
4. 按下列任一方式提供该值

| 方式 | 用法 |
|---|---|
| 命令行参数 | `--sessdata <值>` |
| 环境变量 | `BILI_SESSDATA` |
| 文件 | 当前目录下的 `sessdata.txt` |

读取优先级为命令行参数、环境变量、文件。该值等同于账号凭据，请勿粘贴到聊天工具或公开渠道。

## 输出结构

每次提取生成一个文件夹：

```
<UP主>_最近10条视频文案_20261031/
    01_<视频标题>_2026-10-31.md
    02_<视频标题>_2026-10-30.md
    _index.md        可排序的表格，可跳转到每个文件
    _manifest.json   同一份数据的机器可读版本
    _progress.json   断点续跑记录，请勿手工编辑
```

每个 md 文件以 YAML front matter 开头，包含 bvid、标题、UP 主、发布时间、时长、播放、点赞、收藏、投币、弹幕、评论数、字幕来源、字数与覆盖率，其后为分段后的正文。

## 命名规则

文件夹名为 `{UP主}_{批次说明}视频文案_{生成日期}`：

| 场景 | 文件夹名示例 |
|---|---|
| 单个视频 | `<UP主>_2026-10-31_<视频标题>` |
| 最近 N 条 | `<UP主>_最近10条视频文案_20261031` |
| 最早 N 条 | `<UP主>_最早10条视频文案_20261031` |
| 全部投稿 | `<UP主>_全部N条视频文案_20261031` |
| 点赞最多 | `<UP主>_点赞最多10条视频文案_20261031` |
| 播放最多 | `<UP主>_播放最多10条视频文案_20261031` |
| 日期区间 | `<UP主>_2026-10-20至2026-10-25视频文案_20261031` |
| 合集或系列 | `<UP主>_合集-<合集名>视频文案_20261031` |

文件名为 `{两位序号}_{标题}_{发布日期}.md`：

| 组成 | 规则 |
|---|---|
| 序号 | 该批次内的排名，与 `_index.md` 表格一致，使目录按字母序排列即为排名顺序 |
| 标题 | 紧接序号，最长 50 字，Windows 非法字符 `\ / : * ? " < > \|` 会被替换 |
| 日期 | 置于末尾，按发布时间浏览时无需打开文件 |

## 追加到已有文件夹

指定 `--into` 后，输出会写入同一个文件夹，不再按批次新建：

```bash
# 首次提取，新建文件夹
python scripts/bili_copy.py --up <UP主> --limit 10

# 之后追加到该文件夹
python scripts/bili_copy.py --up <UP主> --limit 15 --into <文件夹名或路径>
```

追加时的处理规则：

| 情形 | 行为 |
|---|---|
| 视频已存在于文件夹 | 按 bvid 去重后跳过，不重复下载 |
| 新条目编号 | 接在现有最大序号之后，既有文件不改名 |
| `_index.md` 与 `_manifest.json` | 合并新旧条目后整体重写 |
| 文件夹名 | 保持不变，不随条数变化 |

未指定 `--into` 时按批次规则新建文件夹。

## 排序与开销

| 排序 | 开销 | 说明 |
|---|---|---|
| `newest` / `oldest` | 一次请求 | 只读取所需条数 |
| `play` | 需翻完所有列表页，投稿越多耗时越长 | 列表接口自带播放数，数据准确 |
| `like` | 每条视频查询一次 | 列表接口不含点赞数，可用 `--scan N` 限制候选池 |

UP 主投稿列表缓存 30 分钟，重复查询不再发起请求。

## 已知限制

- AI 字幕需要先在播放器内生成。B站要等到有用户在播放器中选择「字幕 → 中文」后才生成该字幕，首次约 10 至 30 秒，之后对所有人可用。取不到时脚本写入一份说明文件并记入索引，在播放器触发后重跑即可。
- 同音错字来自 B站自身的转写结果，不属于提取错误。精修需要另加一道语言模型后处理。
- 部分 AI 字幕不带标点。脚本按句末标点、话语标记词、虚词边界三级规则恢复分段。
- 空间接口有频率限制。`--workers` 取值过大会触发 HTTP 412。

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| 字幕列表为空 | 未提供 SESSDATA，或该值已过期，重新获取后重试 |
| `code=-352` 或 `HTTP 412` | 触发风控，等待数分钟后重试，或降低 `--workers` |
| 合集只取到 1 集 | 名称未匹配，先执行 `--list-collections` 确认准确名称 |
| 提取条数少于预期 | 检查 `--limit`。日期区间模式会自动扩量，其余模式严格按指定条数取 |

## 安全

`sessdata.txt` 等同于账号登录凭据。脚本只将其写入本地，不写入日志，不在终端回显。使用完毕后可删除该文件，或在 B站执行退出登录使其立即失效。

`.gitignore` 已排除 `sessdata.txt`。提交前仍建议确认凭据未被纳入版本库。

## 许可证

[MIT](LICENSE)
