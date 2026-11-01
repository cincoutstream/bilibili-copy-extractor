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

<p align="center"><sub>纯 Python 标准库 · 零第三方依赖 · 无需登录其他平台 · 无需 API Key · 无需注册</sub></p>

<br/>

把 B站视频的**官方字幕**批量导出成 Markdown 文案包：一条视频一个 md 文件，外加一份可跳转的索引。

优先取人工 CC 字幕，没有时取 B站 AI 自动生成的字幕。适用于单个视频、某个 UP 主的最近 N 条、全部投稿、按播放量或点赞排名、某段日期区间，以及某个合集或系列。

字幕语言取决于 B站本身提供了什么——绝大多数视频是中文，个别视频由 UP 主上传了其他语言。

## 它能做什么

| 场景 | 命令示例 |
|---|---|
| 单个视频 | `python scripts/bili_copy.py "https://www.bilibili.com/video/BV1xx411c7mD"` |
| UP 主最近 N 条 | `python scripts/bili_copy.py --up <UP主> --limit 10` |
| UP 主全部投稿 | `python scripts/bili_copy.py --up <UP主> --all --yes` |
| 点赞最多 | `python scripts/bili_copy.py --up <UP主> --sort like --limit 10` |
| 播放最多 | `python scripts/bili_copy.py --up <UP主> --sort play --limit 10` |
| 某段日期区间 | `python scripts/bili_copy.py --up <UP主> --since 2026-10-01 --until 2026-10-31` |
| 某个合集或系列 | `python scripts/bili_copy.py --up <UP主> --collection <合集名>` |
| 往已有文件夹里追加 | `python scripts/bili_copy.py --up <UP主> --limit 15 --into <文件夹>` |
| 只看清单，不下字幕 | `python scripts/bili_copy.py --up <UP主> --limit 10 --dry-run` |

`--up` 接受 UP 主名、uid 或空间主页链接。加 `--zip` 打包成压缩包，`--srt` 附带时间轴文件，`--resume` 断点续跑，`--workers` 调整并发。

完整帮助（含输出结构、命名规则、SESSDATA 获取、常见问题）：

```bash
python scripts/bili_copy.py help
```

## 环境要求

| 项 | 要求 |
|---|---|
| Python | **3.7+**（3.9 / 3.11 / 3.12 均可） |
| 第三方包 | **不需要**，不要 `pip install` 任何东西 |
| ffmpeg / yt-dlp | **不需要**，只读官方字幕 JSON，不下载视频或音频 |
| 浏览器自动化 | **不需要**，不用 Selenium / Playwright |
| 网络 | 能访问 `api.bilibili.com`、`www.bilibili.com` 及字幕 CDN |
| 磁盘 | 每个 20-30 分钟视频约 20-30 KB 的 md |

## 安装

**方式一：SkillHub 社区源**

```bash
skillhub install bilibili-copy-extractor
```

**方式二：手动放进技能目录**

```bash
git clone https://github.com/cincoutstream/bilibili-copy-extractor.git
```

把整个目录复制到你所用的 agent 运行时的技能目录即可：

- OpenBitFun：`%APPDATA%\openbitfun\skills\bilibili-copy-extractor\`
- macOS / Linux：`~/.config/openbitfun/skills/bilibili-copy-extractor/`

**方式三：只想跑一下**

不安装也能用，直接在仓库目录执行 `python scripts/bili_copy.py --help`。

## 前提：必须有 SESSDATA

**不需要登录其他平台、不需要 API Key、不需要注册任何账号。** 唯一需要的是你自己 B站账号的 `SESSDATA` cookie。

B站把字幕地址锁在登录态后面：未登录时 `subtitle_url` 是空字符串、`is_lock` 为 `true`。这是接口层面的限制，不是脚本的 bug——任何工具都会撞上。

获取方式（务必自己操作，不要把 cookie 值发到聊天里）：

1. 浏览器登录 `bilibili.com` → `F12` → **Application** → **Cookies** → `https://www.bilibili.com`
2. 复制 `SESSDATA` 这一行的 Value
3. 存成以下任一种：
   - 命令行参数 `--sessdata`
   - 环境变量 `BILI_SESSDATA`
   - 当前目录建 `sessdata.txt` 文件

优先级：命令行参数 > 环境变量 > 文件。

## 输出结构

每次提取生成一个文件夹，一条视频一个 md 文件，外加索引：

```
<UP主>_最近10条视频文案_20261031/
    01_<视频标题>_2026-10-31.md
    02_<视频标题>_2026-10-30.md
    _index.md        可排序的表格，点击可跳转到每个文件
    _manifest.json   同款数据的机器可读版本
    _progress.json   断点续跑记录，勿手工编辑
```

每个 md 文件开头是 YAML front matter（bvid、标题、UP主、发布时间、时长、播放/点赞/收藏/投币/弹幕/评论、字幕来源、字数、覆盖率），后面是分段后的正文。

### 命名规则

文件夹：`{UP主}_{批次说明}视频文案_{生成日期}`

| 场景 | 文件夹名示例 |
|---|---|
| 单视频 | `<UP主>_2026-10-31_<视频标题>` |
| 最近 N 条 | `<UP主>_最近10条视频文案_20261031` |
| 最早 N 条 | `<UP主>_最早10条视频文案_20261031` |
| 全部投稿 | `<UP主>_全部N条视频文案_20261031` |
| 点赞最多 | `<UP主>_点赞最多10条视频文案_20261031` |
| 播放最多 | `<UP主>_播放最多10条视频文案_20261031` |
| 日期区间 | `<UP主>_2026-10-20至2026-10-25视频文案_20261031` |
| 合集或系列 | `<UP主>_合集-<合集名>视频文案_20261031` |

文件：`{两位序号}_{标题}_{发布日期}.md`

- **序号**：在该批次内的排名，与 `_index.md` 表格一致，保证文件夹的字母序就是你的排名顺序
- **标题**：紧跟序号，一眼能认出是哪条；截断到 50 字，替换 Windows 非法字符 `\ / : * ? " < > |`
- **日期**：放最后，看发布时间不必打开文件

### 追加到同一文件夹（`--into`）

不想每跑一次就多一个新文件夹，而是往同一个项目文件夹里攒：

```bash
python scripts/bili_copy.py --up <UP主> --limit 10                              # 第一次：正常新建文件夹
python scripts/bili_copy.py --up <UP主> --limit 15 --into <文件夹名或路径>        # 之后：追加进去
```

- 已在文件夹里的视频按 **bvid** 去重，自动跳过，不会重复下载
- 新条目接在已有最大序号之后继续排（已有 10 条就从 `11` 开始），老文件不重命名
- `_index.md` 与 `_manifest.json` 会合并新旧条目一起重写
- 文件夹名是项目名，不会因为条数变化而改名

不加 `--into` 就是按批次规则新建一个文件夹。

## 排序与成本

| 排序 | 代价 | 说明 |
|---|---|---|
| `newest` / `oldest` | 一次请求 | 只取你要的条数 |
| `play` | 需全量翻页，投稿越多越久 | 列表接口自带播放数（准确），但要知道全局最高必须翻完所有页 |
| `like` | 每条视频一次查询 | 列表接口完全不含点赞数；用 `--scan N` 限制候选池大小 |

UP 主投稿列表会缓存 30 分钟，重复查询秒开。

## 已知限制

- **AI 字幕不是上传时就有**：B站要等有人在播放器里点过「字幕 → 中文」才生成（首次约 10-30 秒），之后缓存给所有人。取不到时脚本会写一份说明文件并记进索引——去播放器触发一次，再重跑即可。
- **同音错字来自 B站自身的转写**，不是提取错误。要精修需要再过一道语言模型。
- **部分 AI 字幕完全没有标点**。脚本按三级规则恢复分段：句末标点 → 话语标记词 → 虚词边界。
- **空间接口有频率限制**。`--workers` 设得太大会触发 HTTP 412。

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| 字幕列表为空 | 没给 SESSDATA，或已过期——重新复制一个 |
| `code=-352` / `HTTP 412` | 触发风控，等几分钟，或降低 `--workers` |
| 合集里只有 1 集 | 名字没匹配上，先跑 `--list-collections` 看准确名称 |
| 提取条数比预期少 | 检查 `--limit`；日期区间会自动扩量，其他模式严格按你要求的条数取 |

## 安全

`sessdata.txt` 等同账号登录凭据：只写本地、不写日志、不回显。用完可删，或在 B站「退出登录」使其立即失效。

`.gitignore` 已排除 `sessdata.txt`，但**每次提交前仍请自行确认**没有把凭据带进仓库。

## 许可证

[MIT](LICENSE)
