<img src="assets/icon.svg" width="96" align="right" alt="B站文案提取">

# B站视频文案提取

把 B站视频的**官方字幕**（人工 CC 优先，否则 B站 AI 自动生成）批量导出成 Markdown 文案包。
单视频、某个 UP 主的最近 N 条 / 全部、按播放量或点赞排名、某段日期区间、某个合集或系列，都能一次拿走。

纯 Python 标准库实现，**零第三方依赖**，不需要 ffmpeg / yt-dlp / 浏览器自动化。

## 它能做什么

| 场景 | 命令示例 |
|---|---|
| 单个视频 | `python scripts/bili_copy.py "https://www.bilibili.com/video/BV1xx411c7mD"` |
| UP 主最近 10 条 | `python scripts/bili_copy.py --up 某UP主 --limit 10` |
| UP 主全部视频 | `python scripts/bili_copy.py --up 某UP主 --all --yes` |
| 点赞最多 | `python scripts/bili_copy.py --up 某UP主 --sort like --limit 10` |
| 播放最多 | `python scripts/bili_copy.py --up 某UP主 --sort play --limit 10` |
| 某段日期区间 | `python scripts/bili_copy.py --up 某UP主 --since 2026-10-01 --until 2026-10-31` |
| 某个合集 / 系列 | `python scripts/bili_copy.py --up 某UP主 --collection 示例课程` |
| 往已有文件夹里追加 | `python scripts/bili_copy.py --up 某UP主 --limit 15 --into 某UP主_最近10条视频文案_20261031` |
| 只看清单不下字幕 | `python scripts/bili_copy.py --up 某UP主 --limit 10 --dry-run` |

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
| ffmpeg / yt-dlp | **不需要**，只取官方字幕 JSON，不下载视频或音频 |
| 网络 | 能访问 `api.bilibili.com`、`www.bilibili.com` 及字幕 CDN |

## 安装

**方式一：SkillHub 社区源**

```bash
skillhub install bilibili-copy-extractor
```

**方式二：手动放进技能目录**

```bash
git clone https://github.com/cincoutstream/bilibili-copy-extractor.git
```

把整个目录复制到你这边的 skills 目录即可，例如：

- OpenBitFun：`%APPDATA%\openbitfun\skills\bilibili-copy-extractor\`
- macOS / Linux：`~/.config/openbitfun/skills/bilibili-copy-extractor/`

**方式三：只想跑一下**

不装也能用，直接 `python scripts/bili_copy.py --help`。

## 前提：必须有 SESSDATA

**不需要登录其他平台、不需要 API Key、不需要注册任何账号。** 只用你自己的 B站账号取一次 `SESSDATA` 即可。

B站把字幕地址锁在登录态后面——未登录时 `subtitle_url` 是空字符串、`is_lock=true`。
**没有 SESSDATA，任何工具都只能拿到空字幕列表**，这是接口层面的限制，不是脚本 bug。

获取方式（务必自己操作，不要把 cookie 值发到聊天里）：

1. 浏览器登录 `bilibili.com` → `F12` → **Application** → **Cookies** → `https://www.bilibili.com`
2. 复制 `SESSDATA` 这一行的 Value
3. 存成以下任一种：
   - 命令行参数 `--sessdata xxxxxxxx`
   - 环境变量 `BILI_SESSDATA`
   - 当前目录建 `sessdata.txt`，粘贴值保存（最省事）

优先级：`--sessdata` > 环境变量 > `sessdata.txt`。

## 输出结构

```
某UP主_最近10条视频文案_20261031/
    01_这期聊聊AI工具怎么选_2026-10-31.md
    02_另一个视频标题_2026-10-30.md
    _index.md        总目录（表格，可点击跳转）
    _manifest.json   机器可读的同款数据
    _progress.json   断点续跑记录，勿手改
```

每个 md 含 YAML front matter（bvid、标题、UP主、发布时间、时长、播放/点赞/收藏/投币/弹幕/评论、字幕来源、字数、覆盖率）+ 自动分段正文。

### 命名规则

文件夹：`{UP主}_{批次说明}视频文案_{生成日期}`

| 场景 | 文件夹名 |
|---|---|
| 单视频 | `某UP主_2026-10-31_这期聊聊AI工具怎么选` |
| 最近 N 条 | `某UP主_最近10条视频文案_20261031` |
| 全部 | `某UP主_全部N条视频文案_20261031` |
| 点赞最多 | `某UP主_点赞最多10条视频文案_20261031` |
| 播放最多 | `某UP主_播放最多10条视频文案_20261031` |
| 日期区间 | `某UP主_2026-10-20至2026-10-25视频文案_20261031` |
| 合集 / 系列 | `某UP主_合集-示例课程视频文案_20261031` |

文件：`{两位序号}_{标题}_{发布日期}.md`

- **序号**在该批次内排名，与 `_index.md` 表格一致，保证文件夹顺序 = 排名顺序
- **标题**紧跟序号，一眼能认出是哪条，截断到 50 字，替换 Windows 非法字符
- **日期**放最后，看发布时间不必打开文件

### 追加到同一文件夹（`--into`）

不想每跑一次就多一个新文件夹时，用 `--into` 往里补：

- 已在文件夹里的视频按 **bvid** 去重，自动跳过，不会重复下载
- 新条目接在已有序号之后继续排（已有 10 条就从 `11` 开始），老文件不重命名
- `_index.md` / `_manifest.json` 会合并老条目一起重写
- 文件夹名是项目名，不会因条数变化而改名

## 排序与成本

| 排序 | 代价 | 说明 |
|---|---|---|
| `newest` / `oldest` | 1 次请求 | 只取需要的条数 |
| `play` | 需全量翻页，投稿越多越久 | 列表自带播放数（准确），但要知道全站最高必须翻完 |
| `like` | 逐条查，条数越多越久 | 列表接口不含点赞数，只能一条条查；用 `--scan N` 圈定候选池 |

投稿列表全量结果缓存 30 分钟，重复查询秒开。

## 已知限制

- **AI 字幕不是上传时就有**：B站要等有人在播放器里点过「字幕 → 中文」才生成（首次约 10-30 秒），之后缓存给所有人。取不到时脚本会生成说明文件并记进索引，去播放器触发一次再重跑即可。
- **同音错字是 B站转写本身的**，不是提取错误。要精修需再过一道语言模型。
- 部分视频的 AI 字幕**完全没有标点**，脚本按「句末标点 → 话语标记词 → 虚词边界」三级断句来分段。
- 空间接口有频率限制，`--workers` 设得太大会触发 412 风控。

## 常见错误

| 现象 | 原因与处理 |
|---|---|
| 字幕列表为空 | 没给 SESSDATA，或 SESSDATA 过期（重新复制） |
| `code=-352` / `HTTP 412` | 触发风控，等几分钟，或降低 `--workers` |
| 合集里全是 1 集 | 名字没匹配上，先跑 `--list-collections` 看准确名称 |
| 提取条数比预期少 | 检查 `--limit`；日期区间会自动扩量，其它模式按需取数 |

## 安全

`sessdata.txt` 等同账号登录凭据：只写本地、不写日志、不回显。用完可删，或在 B站「退出登录」使其立即失效。
`.gitignore` 已排除 `sessdata.txt`，但**提交前仍请自行确认**没有把凭据带进仓库。

## 免责声明

- 本项目为**非官方**工具，与哔哩哔哩（bilibili）无任何隶属或背书关系。
- 仓库图标为自制的 B站配色图形，**不使用**B站官方商标标识。
- 仅用于提取你本就有权访问的公开字幕内容，请遵守 B站的用户协议与 robots 规则，不要用于批量抓取或二次分发他人作品。
- 字幕内容版权归原视频作者所有。

## License

[MIT](LICENSE)
