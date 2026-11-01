#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
B 站视频文案批量提取器 —— 单视频 / UP 主合集 / UP 主全部视频

纯 Python 标准库实现，无需 pip 安装任何依赖。

需要 SESSDATA
    B 站把字幕地址锁在登录态后面（未登录时 subtitle_url 是空字符串），
    没有 SESSDATA 只能拿到空列表。三种给法（优先级从高到低）：
      1) --sessdata 参数
      2) 环境变量 BILI_SESSDATA
      3) sessdata.txt（脚本同目录 / 当前目录 / ~/.openbitfun）
    获取：浏览器登录 bilibili.com -> F12 -> Application -> Cookies
          -> https://www.bilibili.com -> SESSDATA -> 复制 Value

常用命令
    # 单个视频
    python bili_copy.py "https://www.bilibili.com/video/BV1xx411c7mD"

    # UP 主最近 10 条
    python bili_copy.py --up 某UP主 --limit 10

    # UP 主全部视频（超过 100 条需要加 --yes 确认）
    python bili_copy.py --up 某UP主 --all --yes

    # 点赞最多的 10 条
    python bili_copy.py --up 某UP主 --sort like --limit 10

    # 播放最多的 10 条
    python bili_copy.py --up 某UP主 --sort play --limit 10

    # 某个月份的
    python bili_copy.py --up 某UP主 --since 2026-10-01 --until 2026-10-31

    # 先看这个 UP 有哪些合集 / 系列
    python bili_copy.py --up 某UP主 --list-collections

    # 提取某个合集
    python bili_copy.py --up 某UP主 --collection 示例课程

    # 只看清单，不真下字幕
    python bili_copy.py --up 某UP主 --limit 10 --dry-run
"""

import argparse
import hashlib
import http.cookiejar
import json
import os
import re
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "https://api.bilibili.com"
HOME = "https://www.bilibili.com/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
WORKERS = 4          # 并发线程数，太高容易触发风控
UP_PAGE_SIZE = 50    # arc/search 单页上限实测 50（100 会被拒）
COLL_PAGE_SIZE = 30
CACHE_TTL = 1800     # 投稿列表缓存有效期（秒）

MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]

SENT_END = "。！？!?…；;"
SOFT_MARKERS = (
    "然后", "但是", "所以", "因为", "其实", "于是", "接着", "随后", "这时候",
    "这个时候", "接下来", "那么", "不过", "而且", "另外", "总之", "首先",
    "其次", "最后", "结果", "突然", "如果", "虽然", "尽管", "因此", "此时",
    "之后", "于是乎", "话说", "也就是说", "换句话说", "简单说", "反过来",
    "问题是", "关键是", "事实上", "实际上", "另一方面", "与此同时",
)

HELP_EPILOG = r"""
常用示例
--------
  # 单个视频
  python bili_copy.py "https://www.bilibili.com/video/BV1xx411c7mD"

  # UP 主最近 10 条
  python bili_copy.py --up 某UP主 --limit 10

  # UP 主全部视频（超过 100 条需要 --yes 确认）
  python bili_copy.py --up 某UP主 --all --yes

  # 点赞最多 / 播放最多
  python bili_copy.py --up 某UP主 --sort like --limit 10
  python bili_copy.py --up 某UP主 --sort play --limit 10

  # 某段日期区间
  python bili_copy.py --up 某UP主 --since 2026-10-01 --until 2026-10-31

  # 先看这个 UP 有哪些合集/系列，再提取其中一个
  python bili_copy.py --up 某UP主 --list-collections
  python bili_copy.py --up 某UP主 --collection 示例课程

  # 只看清单，不下载字幕
  python bili_copy.py --up 某UP主 --limit 10 --dry-run

  # 往已有的项目文件夹里继续补（已提取过的自动跳过，序号接着往下排）
  python bili_copy.py --up 某UP主 --limit 5 --into 某UP主_最近10条视频文案_20261031
  python bili_copy.py --sort play --limit 3 --into "C:\Users\me\bili文案\我的专辑"

追加模式（--into）
------------------
  --into 后面给「文件夹路径」或「--outdir 下的文件夹名」都行，不存在会自动建。
  规则：
    * 已在这个文件夹里的视频（按 bvid 判断）自动跳过，不会重复下载
    * 新条目接在已有序号后面继续排（已有 5 条就从 06 开始），不会重命名老文件
    * _index.md / _manifest.json 会合并老条目一起重写，批次名沿用原来的
  想彻底重来就别加 --into，会按批次规则新建一个文件夹。

输出结构
--------
  某UP主_最近10条视频文案_20261031/
      01_这期聊聊AI工具怎么选？_2026-10-31.md
      02_拉开差距的潜在品质，“敢于学习”_2026-10-30.md
      _index.md        总目录（表格，可点击跳转）
      _manifest.json   机器可读的同款数据
      _progress.json   断点续跑记录，勿手改

命名规则
--------
  文件夹：{UP主}_{批次说明}视频文案_{生成日期}
      某UP主_最近10条视频文案_20261031
      某UP主_最早10条视频文案_20261031
      某UP主_全部N条视频文案_20261031
      某UP主_点赞最多10条视频文案_20261031
      某UP主_播放最多10条视频文案_20261031
      某UP主_2026-10-01至2026-10-31视频文案_20261031
      某UP主_合集-示例课程视频文案_20261031
      某UP主_2026-10-31_这期聊聊AI工具怎么选...   （单视频）

  单个文件：{序号}_{标题}_{发布日期}.md
      序号 = 该批次内的排名，与 _index.md 表格一致，
             保证文件夹里的顺序就是你要的排名顺序
      标题 = 截断到 50 字，替换 Windows 非法字符 \ / : * ? " < > |

关于 SESSDATA（必需）
---------------------
  B 站把字幕地址锁在登录态后面：未登录时 subtitle_url 是空字符串、is_lock=true。
  这不是脚本的问题，任何工具都一样。

  获取：浏览器登录 bilibili.com → F12 → Application（应用） → Cookies
        → 点开 https://www.bilibili.com → 复制 SESSDATA 这一行的 Value
  保存（三种任选其一）：
        1) 命令行    --sessdata xxxxxxxx
        2) 环境变量  set BILI_SESSDATA=xxxxxxxx
        3) 文本文件  当前目录建 sessdata.txt，粘贴值保存（最省事）

常见问题
--------
  字幕列表为空     → 没给 SESSDATA，或已过期，重新复制一个
  code=-352 / 412  → 触发风控，等几分钟，或把 --workers 降到 2
  提取条数偏少     → 检查 --limit；日期区间会自动扩量，其它模式按需取数
  某条无字幕       → B 站 AI 字幕要有人在播放器点过「字幕→中文」才生成，
                     生成后会缓存，届时重跑即可
"""


# ---------------------------------------------------------------------------
# 基础工具
# ---------------------------------------------------------------------------
HELP_HINT = "提示：加 --help 可查看全部参数、输出结构与命名规则"


def die(msg, code=1):
    print("\n[失败] " + msg)
    print("（加 --help 查看完整用法）")
    sys.exit(code)


def human_err(res):
    c = (res or {}).get("code")
    table = {
        -101: "未登录或 SESSDATA 已过期",
        -352: "触发风控，等几分钟再试，或降低 --workers",
        -400: "请求参数不对",
        -403: "没有访问权限（充电专属 / 地区限制 / 已私密）",
        -404: "视频不存在或已删除",
        62002: "稿件不可见",
        62004: "稿件审核中",
        53013: "该 UP 主设置了隐私，空间不可见",
    }
    if c in table:
        return table[c]
    return "接口返回 code=%s, message=%s" % (c, (res or {}).get("message"))


def sanitize(name, limit=60):
    """Windows 文件名安全化"""
    name = re.sub(r'[\\/:*?"<>|\r\n\t]', "_", name or "untitled")
    name = re.sub(r"\s+", " ", name).strip(" .")
    name = name.replace("_", "_")
    return name[:limit].strip(" .") or "untitled"


def clock(sec):
    sec = int(sec or 0)
    h, sec = divmod(sec, 3600)
    m, sec = divmod(sec, 60)
    return ("%d:%02d:%02d" % (h, m, sec)) if h else ("%02d:%02d" % (m, sec))


def srt_time(sec):
    ms = int(round(max(0.0, float(sec)) * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def hms_to_sec(text):
    """'17:23' / '113:11' / '1:02:03' -> 秒"""
    try:
        parts = [int(x) for x in str(text).split(":")]
    except (ValueError, AttributeError):
        return 0
    sec = 0
    for p in parts:
        sec = sec * 60 + p
    return sec


def fmt_date(ts, with_time=False):
    if not ts:
        return ""
    return time.strftime("%Y-%m-%d %H:%M" if with_time else "%Y-%m-%d",
                         time.localtime(ts))


def fmt_num(n):
    if n is None:
        return "-"
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "-"
    if n >= 10000:
        return "%.1f万" % (n / 10000.0)
    return str(n)


def yaml_str(s):
    """YAML 安全字符串（JSON 字符串同时也是合法 YAML）"""
    return json.dumps("" if s is None else str(s), ensure_ascii=False)


# ---------------------------------------------------------------------------
# HTTP 会话
# ---------------------------------------------------------------------------
class Session(object):
    def __init__(self, sessdata=None):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar))
        self._wbi = None
        if sessdata:
            self._set_sessdata(sessdata)
        try:
            self.raw(HOME, referer=HOME, retries=2)
        except Exception:
            pass

    def _set_sessdata(self, value):
        value = (value or "").strip().strip('"').strip("'")
        m = re.search(r"SESSDATA=([^;\s]+)", value)
        if m:
            value = m.group(1)
        if not value:
            return
        self.jar.set_cookie(http.cookiejar.Cookie(
            version=0, name="SESSDATA", value=value, port=None,
            port_specified=False, domain=".bilibili.com", domain_specified=True,
            domain_initial_dot=True, path="/", path_specified=True, secure=True,
            expires=None, discard=False, comment=None, comment_url=None,
            rest={}, rfc2109=False))

    def has_sessdata(self):
        return any(c.name == "SESSDATA" and c.value for c in self.jar)

    def raw(self, url, referer="https://www.bilibili.com/", timeout=25, retries=3):
        headers = {
            "User-Agent": UA, "Referer": referer,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Origin": "https://www.bilibili.com",
        }
        last = None
        for i in range(retries):
            try:
                req = urllib.request.Request(url, headers=headers)
                with self.opener.open(req, timeout=timeout) as r:
                    return r.read()
            except urllib.error.HTTPError as e:
                last = e
                if e.code == 412:          # 风控，退避要狠一点
                    time.sleep(3.0 * (i + 1))
                    continue
                if e.code in (403, 429):
                    time.sleep(1.5 * (i + 1))
                    continue
                raise
            except Exception as e:
                last = e
                if i + 1 < retries:
                    time.sleep(0.8 * (i + 1))
        raise last

    def get_json(self, url, **kw):
        body = self.raw(url, **kw)
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            raise RuntimeError("返回的不是 JSON（可能被风控）：%r" % body[:160])

    def api(self, path, params=None, signed=False):
        params = dict(params or {})
        if signed:
            params = self._enc_wbi(params)
        url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
        return self.get_json(url)

    def _wbi_keys(self):
        if self._wbi and time.time() - self._wbi[2] < 6 * 3600:
            return self._wbi[0], self._wbi[1]
        res = self.api("/x/web-interface/nav")
        wbi = ((res.get("data") or {}).get("wbi_img")) or {}
        if not wbi.get("img_url") or not wbi.get("sub_url"):
            raise RuntimeError("拿不到 wbi 密钥，接口可能变了")
        img = wbi["img_url"].rsplit("/", 1)[-1].split(".")[0]
        sub = wbi["sub_url"].rsplit("/", 1)[-1].split(".")[0]
        self._wbi = (img, sub, time.time())
        return img, sub

    def _enc_wbi(self, params):
        img, sub = self._wbi_keys()
        mixin = "".join((img + sub)[i] for i in MIXIN_KEY_ENC_TAB)[:32]
        params = dict(params)
        params["wts"] = int(time.time())
        clean = {}
        for k in sorted(params):
            clean[k] = "".join(ch for ch in str(params[k]) if ch not in "!'()*")
        query = urllib.parse.urlencode(clean)
        clean["w_rid"] = hashlib.md5((query + mixin).encode("utf-8")).hexdigest()
        return clean


class SessionPool(object):
    """每线程一个 Session，避免 CookieJar 竞争"""

    def __init__(self, sessdata, workers=WORKERS):
        self.sessdata = sessdata
        self.workers = workers
        self._local = threading.local()

    def get(self):
        s = getattr(self._local, "s", None)
        if s is None:
            s = Session(self.sessdata)
            self._local.s = s
        return s


# ---------------------------------------------------------------------------
# 输入解析
# ---------------------------------------------------------------------------
def bvid_from_text(text):
    m = re.search(r"(BV[0-9A-Za-z]{10})", text)
    return m.group(1) if m else None


def resolve_video(text, s):
    """把链接 / BV / av 号解析成 bvid"""
    text = (text or "").strip()
    if "b23.tv" in text:
        try:
            req = urllib.request.Request(text, headers={"User-Agent": UA})
            with s.opener.open(req, timeout=25) as r:
                text = r.geturl()
        except Exception:
            pass
    bv = bvid_from_text(text)
    if bv:
        return bv
    m = re.search(r"av(\d+)", text, re.I)
    if m or re.fullmatch(r"\d+", text):
        aid = m.group(1) if m else text
        res = s.api("/x/web-interface/view", {"aid": aid})
        if res.get("code") != 0:
            die(human_err(res))
        return res["data"]["bvid"]
    die("认不出这是哪个视频：%s" % text)


def resolve_up(s, text):
    """UP 主名 / uid / 空间链接 -> (mid, name)"""
    text = (text or "").strip()
    m = re.search(r"space\.bilibili\.com/(\d+)", text)
    if m:
        mid = int(m.group(1))
    elif re.fullmatch(r"\d{3,12}", text):
        mid = int(text)
    else:
        res = s.api("/x/web-interface/wbi/search/type",
                    {"search_type": "bili_user", "keyword": text, "page": 1},
                    signed=True)
        if res.get("code") != 0:
            die(human_err(res))
        users = ((res.get("data") or {}).get("result")) or []
        if not users:
            die("没搜到 UP 主：%s" % text)
        exact = [u for u in users if u.get("uname") == text]
        u = (exact or users)[0]
        name = u.get("uname")
        mid = u.get("mid")
        print("  搜索命中: %s (uid=%s, %s 粉, %s 个投稿)"
              % (name, mid, fmt_num(u.get("fans")), u.get("videos")))
        return mid, name
    res = s.api("/x/space/wbi/acc/info",
                {"mid": mid, "platform": "web", "web_location": "1550101"},
                signed=True)
    name = ((res.get("data") or {}).get("name")) or str(mid)
    return mid, name


# ---------------------------------------------------------------------------
# 投稿列表
# ---------------------------------------------------------------------------
def _arc_cache_path(mid):
    d = os.path.join(tempfile.gettempdir(), "bili_copy_cache")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "arc_%s.json" % mid)


def list_up_videos(s, mid, want=None, stop_before=None):
    """
    按发布日期倒序拉 UP 主投稿。
    vlist 自带 play / length / created（已核对与 view 接口一致），
    所以按播放排序不用再逐条查。
    want=None 表示要全部；stop_before 表示翻到这个时间点之前就停
    （配合 --since 用，避免为了一个日期区间把整个空间翻一遍）。
    B 站空间接口有频率限制，所以全量结果会缓存 30 分钟。
    """
    full_scan = (want is None and stop_before is None)
    cache_path = _arc_cache_path(mid)
    if full_scan and os.path.exists(cache_path):
        try:
            d = json.load(open(cache_path, "r", encoding="utf-8"))
            age = time.time() - d.get("ts", 0)
            if age < CACHE_TTL:
                print("  使用缓存（%.0f 分钟前抓的投稿列表，共 %d 条）"
                      % (age / 60.0, len(d.get("videos") or [])))
                return d.get("videos") or []
        except Exception:
            pass

    out, pn, total = [], 1, None
    hit_stop = False
    while pn <= 200:
        res = None
        for attempt in range(3):
            try:
                res = s.api("/x/space/wbi/arc/search",
                            {"mid": mid, "ps": UP_PAGE_SIZE, "pn": pn,
                             "order": "pubdate", "platform": "web",
                             "web_location": "1550101"}, signed=True)
            except Exception as e:
                if attempt == 2:
                    if out:
                        print("\n  翻页被限流中断（%s），已拿到 %d 条，继续用已取到的部分"
                              % (type(e).__name__, len(out)))
                        return out
                    die("读取投稿列表失败（%s）。可能触发了风控，等几分钟再试" % e)
                time.sleep(5.0 * (attempt + 1))
                continue
            if res.get("code") == 0:
                break
            if res.get("code") in (-352, -412, -509) and attempt < 2:
                time.sleep(5.0 * (attempt + 1))
                continue
            if pn == 1:
                die(human_err(res))
            return out

        data = res.get("data") or {}
        page = data.get("page") or {}
        if total is None:
            total = page.get("count")
            print("  该 UP 主共 %s 个投稿%s"
                  % (total, "" if want is None else "，本次需要 %d 个" % want))
        vlist = (data.get("list") or {}).get("vlist") or []
        if not vlist:
            break
        for v in vlist:
            c = v.get("created") or 0
            if stop_before and c and c < stop_before:
                hit_stop = True
                break
            out.append({
                "bvid": v.get("bvid"),
                "title": v.get("title") or "",
                "created": c,
                "play": v.get("play"),
                "duration": hms_to_sec(v.get("length")),
                "stat": None,
                "source": "arc",
            })
        if hit_stop:
            break
        if want and len(out) >= want:
            break
        if total and len(out) >= total:
            break
        pn += 1
        if pn % 5 == 0:
            print("    ...第 %d 页，已取 %d / %s" % (pn - 1, len(out), total or "?"))
        time.sleep(0.9)
    if full_scan and out and (not total or len(out) >= total):
        try:
            json.dump({"ts": time.time(), "videos": out},
                      open(cache_path, "w", encoding="utf-8"), ensure_ascii=False)
        except Exception:
            pass
    return out[:want] if want else out


def list_collections(s, mid):
    """列出合集(season)与系列(series)。注意 page_size 上限是 20，超过会 -400"""
    out, page_num = [], 1
    has_more = True
    while has_more and page_num <= 20:
        res = s.api("/x/polymer/web-space/seasons_series_list",
                    {"mid": mid, "page_num": page_num, "page_size": 20},
                    signed=True)
        if res.get("code") != 0:
            if page_num == 1:
                die(human_err(res))
            break
        items = ((res.get("data") or {}).get("items_lists")) or {}
        seasons = items.get("seasons_list") or []
        series = items.get("series_list") or []
        for sn in seasons:
            meta = sn.get("meta") or {}
            out.append({"kind": "合集", "id": meta.get("season_id"),
                        "name": re.sub(r"^合集[·:：]\s*", "", meta.get("name") or ""),
                        "total": meta.get("total")})
        for se in series:
            meta = se.get("meta") or {}
            out.append({"kind": "系列", "id": meta.get("series_id"),
                        "name": meta.get("name") or "", "total": meta.get("total")})
        has_more = bool(items.get("has_more"))
        page_num += 1
        if not has_more:
            break
        time.sleep(0.15)
    return out


def list_collection_videos(s, mid, coll):
    """拉取某个合集/系列里的全部视频"""
    out, pn, total = [], 1, None
    while pn <= 100:
        if coll["kind"] == "合集":
            res = s.api("/x/polymer/web-space/seasons_archives_list",
                        {"mid": mid, "season_id": coll["id"],
                         "sort_reverse": "false", "page_num": pn,
                         "page_size": COLL_PAGE_SIZE}, signed=True)
            data = res.get("data") or {}
            page = data.get("page") or {}
            arcs = data.get("archives") or []
        else:
            res = s.api("/x/series/archives",
                        {"mid": mid, "series_id": coll["id"],
                         "only_normal": "true", "sort": "desc",
                         "pn": pn, "ps": COLL_PAGE_SIZE}, signed=True)
            data = res.get("data") or {}
            page = data.get("page") or {}
            arcs = data.get("archives") or []
        if res.get("code") != 0:
            if pn == 1:
                die(human_err(res))
            break
        if total is None:
            total = page.get("total")
        if not arcs:
            break
        for a in arcs:
            out.append({
                "bvid": a.get("bvid"),
                "title": a.get("title") or "",
                "created": a.get("pubdate") or a.get("ctime") or 0,
                "play": (a.get("stat") or {}).get("view"),
                "duration": a.get("duration") or 0,
                "stat": None,
                "source": "collection",
            })
        if total and len(out) >= total:
            break
        pn += 1
        time.sleep(0.15)
    return out


# ---------------------------------------------------------------------------
# 视频详情与统计
# ---------------------------------------------------------------------------
def fetch_view(s, bvid, retries=3):
    for i in range(retries):
        try:
            res = s.api("/x/web-interface/view", {"bvid": bvid})
        except Exception:
            time.sleep(1.0 + i)
            continue
        if res.get("code") == 0:
            return res.get("data") or {}
        if res.get("code") in (-352, -412, -509):
            time.sleep(2.0 * (i + 1))
            continue
        return None
    return None


def enrich(pool, bvids, label="获取视频统计"):
    """并发补齐 view 详情（含点赞、收藏等列表接口拿不到的字段）"""
    if not bvids:
        return {}
    got = {}
    todo = [b for b in bvids]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fetch_view, pool.get(), b): b for b in todo}
        done = 0
        for fu in as_completed(futs):
            b = futs[fu]
            done += 1
            try:
                d = fu.result()
            except Exception:
                d = None
            if d:
                got[b] = d
            if done % 20 == 0 or done == len(todo):
                sys.stdout.write("\r  %s %d/%d  (%.0fs)      "
                                 % (label, done, len(todo), time.time() - t0))
                sys.stdout.flush()
    if todo:
        print()
    return got


# ---------------------------------------------------------------------------
# 字幕
# ---------------------------------------------------------------------------
def get_subtitles(s, bvid, cid):
    res = s.api("/x/player/wbi/v2", {"bvid": bvid, "cid": cid}, signed=True)
    if res.get("code") != 0:
        return None, res
    return ((res.get("data") or {}).get("subtitle") or {}), res


def is_ai_sub(sub):
    return (sub.get("ai_type") == 1) or (sub.get("lan") or "").lower().startswith("ai-")


def pick_subtitle(subs, prefer="cc"):
    usable = [x for x in subs if (x.get("subtitle_url") or "").strip()]
    if not usable:
        return None

    def score(x):
        lan = (x.get("lan") or "").lower()
        ai = is_ai_sub(x)
        if lan in ("zh-cn", "zh-hans", "zh", "zh-tw", "zh-hant", "ai-zh") or "zh" in lan:
            lang = 0
        elif lan.startswith("en"):
            lang = 2
        else:
            lang = 4
        kind = (0 if ai else 1) if prefer == "ai" else (0 if not ai else 1)
        return (lang, kind)

    return sorted(usable, key=score)[0]


def parse_body(payload):
    if isinstance(payload, list):
        rows = payload
    else:
        rows = (payload.get("body") or payload.get("payload")
                or payload.get("subtitles") or [])
    out = []
    for r in rows:
        if isinstance(r, dict):
            f = r.get("from", r.get("start", 0))
            t = r.get("to", r.get("end", 0))
            txt = r.get("content", r.get("text", ""))
        elif isinstance(r, (list, tuple)) and len(r) >= 3:
            f, t, txt = r[0], r[1], r[2]
        else:
            continue
        txt = (txt or "").strip()
        if not txt:
            continue
        try:
            out.append({"from": float(f), "to": float(t), "text": txt})
        except (TypeError, ValueError):
            continue
    out.sort(key=lambda x: x["from"])
    return out


def download_subtitle(s, sub):
    url = sub.get("subtitle_url") or ""
    if url.startswith("//"):
        url = "https:" + url
    elif not url.startswith("http"):
        url = "https://" + url.lstrip("/")
    return parse_body(s.get_json(url, referer="https://www.bilibili.com/"))


def dedupe(items):
    out = []
    for it in items:
        key = re.sub(r"\s+", "", it["text"])
        if not key:
            continue
        if out:
            prev = re.sub(r"\s+", "", out[-1]["text"])
            if key == prev:
                continue
            if len(key) >= 2 and prev.endswith(key):
                continue
        out.append(it)
    return out


def to_paragraphs(items, with_time=False, target=130, hard=220):
    paras = []
    buf, buf_start = "", 0.0

    def flush(head):
        head = head.strip()
        if head:
            paras.append((buf_start, head))

    for it in items:
        if not buf:
            buf_start = it["from"]
        buf += it["text"]
        if len(buf) < target:
            continue
        cut = -1
        for i, ch in enumerate(buf):
            if ch in SENT_END:
                cut = i
        if cut >= 40:
            head, buf = buf[:cut + 1], buf[cut + 1:]
            flush(head)
            buf_start = it["from"]
            continue
        lo = max(60, int(len(buf) * 0.55))
        bi = -1
        for m in SOFT_MARKERS:
            i = buf.rfind(m, lo)
            if i > bi:
                bi = i
        if bi > 0:
            head, buf = buf[:bi], buf[bi:]
            flush(head)
            buf_start = it["from"]
            continue
        if len(buf) >= hard:
            cut_at = hard
            for back in range(0, 25):
                p = hard - back
                if p > 0 and buf[p - 1] in "的了是在和就都也还而或者":
                    cut_at = p
                    break
            head, buf = buf[:cut_at], buf[cut_at:]
            flush(head)
            buf_start = it["from"]

    flush(buf)
    return [(("%s  " % clock(t)) if with_time else "") + txt for t, txt in paras if txt]


def to_srt(items):
    lines = []
    for i, it in enumerate(items, 1):
        lines.append(str(i))
        lines.append("%s --> %s" % (srt_time(it["from"]), srt_time(it["to"])))
        lines.append(it["text"])
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Markdown 生成
# ---------------------------------------------------------------------------
def video_markdown(info, meta, items, sub, cid, coverage):
    title = (meta or {}).get("title") or info.get("title") or info["bvid"]
    up = ((meta or {}).get("owner") or {}).get("name") or "-"
    st = (meta or {}).get("stat") or {}
    pub = (meta or {}).get("pubdate") or info.get("created") or 0
    dur = (meta or {}).get("duration") or info.get("duration") or 0
    words = sum(len(x["text"]) for x in items) if items else 0
    kind = "AI字幕" if (sub and is_ai_sub(sub)) else ("人工CC" if sub else "无")
    lan = (sub or {}).get("lan_doc") or (sub or {}).get("lan") or "-"

    fm = [
        "---",
        "bvid: %s" % info["bvid"],
        "title: %s" % yaml_str(title),
        "up: %s" % yaml_str(up),
        "up_uid: %s" % ((meta or {}).get("owner") or {}).get("mid", ""),
        "url: https://www.bilibili.com/video/%s/" % info["bvid"],
        "published: %s" % fmt_date(pub, True),
        "duration: %s" % clock(dur),
        "stats:",
        "  view: %s" % (st.get("view", info.get("play")) or 0),
        "  like: %s" % (st.get("like") or 0),
        "  favorite: %s" % (st.get("favorite") or 0),
        "  coin: %s" % (st.get("coin") or 0),
        "  danmaku: %s" % (st.get("danmaku") or 0),
        "  reply: %s" % (st.get("reply") or 0),
        "subtitle_source: %s" % yaml_str(kind),
        "subtitle_language: %s" % yaml_str(lan),
        "segments: %d" % (len(items) if items else 0),
        "words: %d" % words,
        "coverage: %s" % yaml_str(coverage),
        "extracted_at: %s" % time.strftime("%Y-%m-%d %H:%M:%S"),
        "---",
        "",
        "# %s" % title,
        "",
    ]
    if items:
        fm.append("> UP主 %s ｜ 发布 %s ｜ 时长 %s ｜ 播放 %s ｜ 点赞 %s ｜ 收藏 %s"
                  % (up, fmt_date(pub), clock(dur), fmt_num(st.get("view", info.get("play"))),
                     fmt_num(st.get("like")), fmt_num(st.get("favorite"))))
        fm.append("")
        fm.append("字幕来源：%s（%s），%d 条，约 %d 字，覆盖 %s"
                  % (kind, lan, len(items), words, coverage))
        fm.append("")
        fm.append("## 文案")
        fm.append("")
        fm.extend(to_paragraphs(items))
    else:
        fm.append("> UP主 %s ｜ 发布 %s ｜ 时长 %s"
                  % (up, fmt_date(pub), clock(dur)))
        fm.append("")
        fm.append("## 无字幕")
        fm.append("")
        fm.append("该视频没有可用字幕（既无人工 CC，B 站也尚未生成 AI 字幕）。")
        fm.append("")
        fm.append("如需获取，请在浏览器里打开该视频，点播放器右下角【字幕】按钮")
        fm.append("并选择【中文】触发 B 站生成 AI 字幕（首次约 10-30 秒），")
        fm.append("生成后 B 站会缓存，届时重跑本命令即可。")
        fm.append("")
        fm.append("视频地址：https://www.bilibili.com/video/%s/" % info["bvid"])
    fm.append("")
    return "\n".join(fm)


def index_markdown(folder_meta, rows):
    kinds = {}
    for r in rows:
        kinds[r["sub_kind"]] = kinds.get(r["sub_kind"], 0) + 1
    kind_label = "、".join("%s %d 条" % (k, v) for k, v in sorted(kinds.items())) or "-"
    lines = [
        "# %s" % folder_meta["title"],
        "",
        "| 项 | 内容 |",
        "|---|---|",
        "| UP主 | %s (uid=%s) |" % (folder_meta["up"], folder_meta["uid"]),
        "| 批次 | %s |" % folder_meta["label"],
        "| 条数 | %d |" % len(rows),
        "| 排序 | %s |" % folder_meta["sort_label"],
        "| 生成时间 | %s |" % folder_meta["created_at"],
        "| 字幕来源 | %s（B站官方字幕） |" % kind_label,
        "",
        "## 目录",
        "",
        "| # | 发布 | 标题 | 时长 | 播放 | 点赞 | 字数 | 字幕 | 文件 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append("| %d | %s | %s | %s | %s | %s | %d | %s | [%s](%s) |" % (
            r["rank"], r["date"], r["title"].replace("|", "\\|"), r["duration"],
            fmt_num(r["view"]), fmt_num(r["like"]), r["words"], r["sub_kind"],
            r["filename"], urllib.parse.quote(r["filename"])))
    lines.append("")
    if folder_meta.get("no_sub"):
        lines.append("## 无字幕视频")
        lines.append("")
        for bv, t in folder_meta["no_sub"]:
            lines.append("- %s（%s）" % (t, bv))
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def load_sessdata(cli_value, cwd):
    if cli_value:
        return cli_value, "--sessdata"
    env = os.environ.get("BILI_SESSDATA", "").strip()
    if env:
        return env, "环境变量 BILI_SESSDATA"
    cands = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessdata.txt"),
        os.path.join(cwd, "sessdata.txt"),
        os.path.join(os.path.expanduser("~"), ".openbitfun", "sessdata.txt"),
    ]
    for p in cands:
        if os.path.exists(p):
            v = open(p, "r", encoding="utf-8-sig").read().strip()
            if v:
                return v, p
    return None, None


def build_pool(args, s, up_name, up_uid):
    """组装候选列表 [{bvid,title,created,play,duration,stat,source}]"""
    if args.collection:
        colls = list_collections(s, up_uid)
        hits = [c for c in colls if args.collection in c["name"]]
        if not hits:
            print("  该 UP 主的合集/系列：")
            for c in colls:
                print("    [%s] %s（%s 集）" % (c["kind"], c["name"], c["total"]))
            die("没找到名字包含「%s」的合集或系列" % args.collection)
        coll = hits[0]
        print("  命中%s：%s（%s 集）" % (coll["kind"], coll["name"], coll["total"]))
        args._coll_name = coll["name"]
        args._coll_kind = coll["kind"]
        return list_collection_videos(s, up_uid, coll)
    stop_before = None
    if args.since:
        stop_before = time.mktime(time.strptime(args.since, "%Y-%m-%d"))
    if args.sort == "like":
        # 点赞只能逐条查，所以用 --scan 圈定候选池
        want = args.scan if args.scan and args.scan > 0 else None
    elif args.sort in ("newest", "oldest"):
        # 有日期筛选时必须多取，否则窗口内靠后的视频会被 --limit 截掉
        want = None if (args.all or args.since or args.until) else max(args.limit, 10)
    else:
        # 播放排序要看全量才知道最高的是哪几条（vlist 自带 play，不额外花请求）
        want = None
    return list_up_videos(s, up_uid, want=want, stop_before=stop_before)


def apply_window(pool, args):
    if args.since:
        t = time.mktime(time.strptime(args.since, "%Y-%m-%d"))
        pool = [p for p in pool if p["created"] >= t]
    if args.until:
        t = time.mktime(time.strptime(args.until, "%Y-%m-%d")) + 86399
        pool = [p for p in pool if p["created"] <= t]
    return pool


def sort_label(args):
    if getattr(args, "_keep_order", False):
        return "合集/系列原始顺序"
    return {"newest": "按发布日期（新→旧）", "oldest": "按发布日期（旧→新）",
            "play": "按播放量（高→低）", "like": "按点赞数（高→低）"}[args.sort]


def make_folder_label(args, count):
    if args.collection:
        return "%s-%s" % (getattr(args, "_coll_kind", "合集"),
                          getattr(args, "_coll_name", args.collection))
    if args.since or args.until:
        a = args.since or "最早"
        b = args.until or "至今"
        return "%s至%s" % (a, b)
    if args.all:
        return "全部%d条" % count
    if args.sort == "like":
        return "点赞最多%d条" % count
    if args.sort == "play":
        return "播放最多%d条" % count
    if args.sort == "oldest":
        return "最早%d条" % count
    return "最近%d条" % count


def main():
    global WORKERS
    ap = argparse.ArgumentParser(
        description="B 站视频文案批量提取（单视频 / UP 主合集 / UP 主全部视频）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=HELP_EPILOG)
    ap.add_argument("target", nargs="?", help="视频链接 / BV 号 / av 号")
    ap.add_argument("--up", help="UP 主名、uid 或空间链接")
    ap.add_argument("--collection", help="合集或系列名（可模糊匹配），配合 --up")
    ap.add_argument("--list-collections", action="store_true", help="只列出该 UP 的合集/系列")
    ap.add_argument("--limit", type=int, default=10, help="取前 N 条，默认 10")
    ap.add_argument("--all", action="store_true", help="取全部")
    ap.add_argument("--sort", choices=["newest", "oldest", "play", "like"],
                    default=None,
                    help="排序方式：newest/oldest/play/like。不填时单个 UP 用 newest，"
                         "合集则保留原始顺序")
    ap.add_argument("--scan", type=int, default=200,
                    help="点赞排序时的候选池大小（只扫最近 N 条），默认 200，0 表示全部")
    ap.add_argument("--since", help="起始日期 YYYY-MM-DD")
    ap.add_argument("--until", help="结束日期 YYYY-MM-DD")
    ap.add_argument("--outdir", default="bili文案", help="输出根目录，默认 ./bili文案")
    ap.add_argument("--into", metavar="FOLDER",
                    help="追加到已有的项目文件夹（给路径或文件夹名），"
                         "新视频接在已有序号后面，已提取过的自动跳过")
    ap.add_argument("--sessdata", help="SESSDATA cookie 值")
    ap.add_argument("--prefer", choices=["cc", "ai"], default="cc",
                    help="字幕优先人工CC(cc)还是AI(ai)，默认 cc")
    ap.add_argument("--srt", action="store_true", help="额外输出 srt 时间轴")
    ap.add_argument("--zip", action="store_true", help="打包成 zip")
    ap.add_argument("--dry-run", action="store_true", help="只列清单，不下字幕")
    ap.add_argument("--resume", action="store_true", help="跳过已提取过的视频")
    ap.add_argument("--yes", action="store_true", help="超过 100 条时确认")
    ap.add_argument("--workers", type=int, default=WORKERS, help="并发数，默认 4")
    args = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # 让 `python bili_copy.py help` 也能打开帮助
    if args.target and str(args.target).strip().lower() in ("help", "h", "?", "？", "帮助"):
        ap.print_help()
        return
    WORKERS = max(1, min(8, args.workers))

    cwd = os.getcwd()
    explicit_sort = args.sort is not None
    if args.sort is None:
        args.sort = "newest"
    # 合集/系列默认保留自身顺序（课程是按 1、2、3 排的，按日期重排会把顺序打乱）
    args._keep_order = bool(args.collection and not explicit_sort)
    sessdata, src = load_sessdata(args.sessdata, cwd)
    print("=" * 66)
    print("B 站文案提取" + ("" if args.up else "（单视频）"))
    print("=" * 66)
    if sessdata:
        print("登录态: 已提供 SESSDATA（来源: %s）" % src)
    else:
        print("登录态: [缺少 SESSDATA] —— 没有它只能拿到空字幕列表")
        print("")
        print("  怎么拿（一分钟）：")
        print("    1. 浏览器登录 bilibili.com")
        print("    2. 按 F12 -> 顶部选 Application(应用) -> 左侧 Cookies")
        print("       -> 点开 https://www.bilibili.com")
        print("    3. 找到 SESSDATA 那一行，复制它的 Value")
        print("")
        print("  怎么用（三种任选）：")
        print("    a) 命令行   --sessdata 你复制的值")
        print("    b) 环境变量 set BILI_SESSDATA=你复制的值")
        print("    c) 文件     在当前目录建 sessdata.txt，把值粘进去（最省事）")
        print("")
        print("  说明：SESSDATA 等同你的登录态，只在本机使用、不会外发。")
        print("       介意的话用完删掉 sessdata.txt，或在B站退出登录使其失效。")
        print("")

    if not args.target and not args.up:
        die("请给一个视频链接，或用 --up 指定 UP 主")

    pool_sess = SessionPool(sessdata, WORKERS)
    s = Session(sessdata)

    # ---------------- 单视频 ----------------
    if not args.up:
        bvid = resolve_video(args.target, s)
        meta = fetch_view(s, bvid)
        if not meta:
            die("拿不到视频信息，视频可能不可见")
        title = meta.get("title") or bvid
        up = ((meta.get("owner") or {}).get("name")) or "-"
        folder = sanitize("%s_%s_%s" % (up, fmt_date(meta.get("pubdate")),
                                        title), 90)
        root = resolve_into_root(args.into, args.outdir) or os.path.join(args.outdir, folder)

        existing_rows, existing_meta, start_rank = [], {}, 1
        if args.into:
            existing_rows = load_existing_rows(root)
            existing_meta = load_existing_meta(root)
            if existing_meta.get("title"):
                title = existing_meta["title"]
            if existing_rows:
                start_rank = max([r.get("rank") or 0 for r in existing_rows]) + 1
        skip = set(r.get("bvid") for r in existing_rows if r.get("bvid"))

        print("\n视频: %s" % title)
        print("UP主: %s   时长: %s" % (up, clock(meta.get("duration"))))
        print("输出: %s" % root)
        if args.into and existing_rows:
            print("追加模式：已有 %d 条，新条目从第 %02d 条开始"
                  % (len(existing_rows), start_rank))
        if args.dry_run:
            print("\n[dry-run] 不写文件")
            return
        os.makedirs(root, exist_ok=True)
        rows = extract_batch([{"bvid": bvid, "title": title,
                               "created": meta.get("pubdate") or 0,
                               "play": (meta.get("stat") or {}).get("view"),
                               "duration": meta.get("duration") or 0,
                               "stat": meta}],
                             pool_sess, args, root, up, "", title,
                             rows=existing_rows, start_rank=start_rank,
                             skip_bvids=skip)
        rows.sort(key=lambda r: r.get("rank") or 0)
        write_index(root, {"title": title, "up": up, "uid": "single",
                           "label": existing_meta.get("label") or "单视频",
                           "sort_label": existing_meta.get("sort_label") or "-",
                           "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}, rows)
        if args.zip:
            do_zip(root)
        print_summary(rows, root)
        print(HELP_HINT)
        return

    # ---------------- UP 主 ----------------
    mid, up_name = resolve_up(s, args.up)
    print("\nUP主: %s  (uid=%s)" % (up_name, mid))

    if args.list_collections:
        colls = list_collections(s, mid)
        if not colls:
            print("  这个 UP 主没有合集或系列")
        for c in colls:
            print("  [%s] %-40s %s 集  (id=%s)" % (c["kind"], c["name"], c["total"], c["id"]))
        return

    pool = build_pool(args, s, up_name, mid)
    if not pool:
        die("这个 UP 主没有公开投稿")
    pool = apply_window(pool, args)
    if not pool:
        die("按日期筛选后没有视频，检查 --since / --until")

    # 排序：like 一定要逐条查；play 在合集/系列来源下也不可靠，同样要查
    if args.sort == "like" and len(pool) > 400 and not args.yes:
        print("\n点赞排序需要在 %d 条候选里逐条读取统计，会比较久。" % len(pool))
        print("加 --yes 继续，或用 --scan N 只扫最近 N 条。")
        die("已中止（未加 --yes）")
    need_stats = (args.sort == "like"
                  or (args.sort == "play" and any(p["source"] != "arc" for p in pool)))
    if need_stats:
        print("\n按 %s 排序需要逐条读取统计（列表接口不含点赞数）"
              % ("点赞" if args.sort == "like" else "播放"))
        stats = enrich(pool_sess, [p["bvid"] for p in pool], "读取统计")
        for p in pool:
            d = stats.get(p["bvid"]) or {}
            p["stat"] = d or None
            if d:
                p["play"] = (d.get("stat") or {}).get("view", p.get("play"))
                p["created"] = d.get("pubdate") or p["created"]
                p["title"] = d.get("title") or p["title"]

    key = {"newest": lambda p: -p["created"], "oldest": lambda p: p["created"],
           "play": lambda p: -(p.get("play") or 0),
           "like": lambda p: -(((p.get("stat") or {}).get("stat") or {}).get("like") or 0)}
    if not getattr(args, "_keep_order", False):
        pool.sort(key=key[args.sort])

    total_sel = len(pool) if args.all else min(args.limit, len(pool))
    if total_sel > 100 and not args.yes:
        print("\n将提取 %d 条，耗时可能很长（每条约 0.5-2 秒）。" % total_sel)
        print("确认请加 --yes，或先用 --limit 缩小范围。")
        die("已中止（未加 --yes）")

    selected = pool[:total_sel]

    label = make_folder_label(args, len(selected))
    folder = sanitize("%s_%s视频文案_%s" % (up_name, label,
                                           time.strftime("%Y%m%d")), 90)
    root = resolve_into_root(args.into, args.outdir) or os.path.join(args.outdir, folder)
    title = "%s %s视频文案" % (up_name, label)

    existing_rows, existing_meta, start_rank = [], {}, 1
    if args.into:
        # 注意：这里不建目录，--dry-run 不该留下空文件夹
        existing_rows = load_existing_rows(root)
        existing_meta = load_existing_meta(root)
        if existing_meta.get("title"):
            title = existing_meta["title"]
        if existing_meta.get("label"):
            label = existing_meta["label"]
        if existing_rows:
            start_rank = max([r.get("rank") or 0 for r in existing_rows]) + 1
            print("\n追加模式：该文件夹已有 %d 条，新条目从第 %02d 条开始"
                  % (len(existing_rows), start_rank))
        else:
            print("\n追加模式：该文件夹当前为空，按新批次写入")

    print("\n排序: %s" % sort_label(args))
    print("选中: %d 条" % len(selected))
    print("输出: %s" % root)
    for i, p in enumerate(selected[:5], 1):
        print("   %2d. %s  %s" % (i, fmt_date(p["created"]), p["title"][:40]))
    if len(selected) > 5:
        print("   ... 另有 %d 条" % (len(selected) - 5))

    if args.dry_run:
        print("\n[dry-run] 不写文件")
        return

    os.makedirs(root, exist_ok=True)
    skip = set(r.get("bvid") for r in existing_rows if r.get("bvid"))
    rows = extract_batch(selected, pool_sess, args, root, up_name, label, title,
                         rows=existing_rows, start_rank=start_rank,
                         skip_bvids=skip)
    rows.sort(key=lambda r: r.get("rank") or 0)
    write_index(root, {"title": title, "up": up_name, "uid": mid, "label": label,
                       "sort_label": existing_meta.get("sort_label") or sort_label(args),
                       "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}, rows)
    if args.zip:
        do_zip(root)
    print_summary(rows, root)
    print(HELP_HINT)


def resolve_into_root(value, outdir):
    """
    解析 --into 的目标文件夹。可以是：
      1) 已存在的路径（原样用）
      2) --outdir 下的文件夹名（已存在就用，不存在就建）
      3) 带分隔符的新路径
    """
    v = (value or "").strip().strip('"').strip("'")
    if not v:
        return None
    if os.path.isdir(v):
        return os.path.abspath(v)
    cand = os.path.join(outdir, v)
    if os.path.isdir(cand):
        return cand
    if os.sep in v or "/" in v or ":" in v:
        return os.path.abspath(v)
    return cand


def parse_md_front_matter(path):
    """从本脚本生成的 md 里读回 front matter（老文件夹没有 manifest 时兜底用）"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            head = f.read(6000)
    except Exception:
        return None
    if not head.startswith("---"):
        return None
    parts = head.split("---", 2)
    if len(parts) < 3:
        return None
    info, stats, in_stats = {}, {}, False
    for line in parts[1].split("\n"):
        if not line.strip():
            continue
        if line.startswith(("  ", "\t")) and in_stats:
            k, _, v = line.strip().partition(":")
            stats[k.strip()] = v.strip()
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        in_stats = False
        if k == "stats":
            in_stats = True
            continue
        if v.startswith('"'):
            try:
                v = json.loads(v)
            except Exception:
                v = v.strip('"')
        info[k] = v
    info["_stats"] = stats
    return info


def load_existing_rows(root):
    """读回文件夹里已有的结果，用于追加时合并索引"""
    if not os.path.isdir(root):
        return []
    mp = os.path.join(root, "_manifest.json")
    if os.path.exists(mp):
        try:
            rows = json.load(open(mp, "r", encoding="utf-8")).get("items") or []
            if rows:
                return rows
        except Exception:
            pass
    rows = []
    for fn in sorted(os.listdir(root)):
        if not fn.lower().endswith(".md") or fn.startswith("_"):
            continue
        fm = parse_md_front_matter(os.path.join(root, fn))
        if not fm:
            continue
        m = re.match(r"^(\d+)_", fn)
        try:
            words = int(fm.get("words") or 0)
        except (TypeError, ValueError):
            words = 0
        st = fm.get("_stats") or {}
        rows.append({
            "rank": int(m.group(1)) if m else len(rows) + 1,
            "date": (fm.get("published") or "")[:10],
            "title": fm.get("title") or fn[:-3],
            "duration": fm.get("duration") or "",
            "view": st.get("view"), "like": st.get("like"),
            "words": words,
            "sub_kind": fm.get("subtitle_source") or "-",
            "filename": fn,
            "bvid": fm.get("bvid") or "",
        })
    rows.sort(key=lambda r: r.get("rank") or 0)
    return rows


def load_existing_meta(root):
    mp = os.path.join(root, "_manifest.json")
    if os.path.exists(mp):
        try:
            return json.load(open(mp, "r", encoding="utf-8")).get("meta") or {}
        except Exception:
            pass
    return {}


def extract_batch(items, pool, args, root, up_name, label, title,
                  rows=None, start_rank=1, skip_bvids=None):
    """逐条提取字幕并写 md，返回索引行（追加模式时 rows 里带已有条目）"""
    rows = list(rows or [])
    skip_bvids = set(skip_bvids or [])
    prog_path = os.path.join(root, "_progress.json")
    done = {}
    if os.path.exists(prog_path):
        try:
            done = json.load(open(prog_path, "r", encoding="utf-8"))
        except Exception:
            done = {}
    if args.resume and done:
        print("  断点续跑：已有 %d 条记录" % len(done))

    width = max(2, len(str(start_rank + len(items) - 1)))
    added = 0
    for i, info in enumerate(items, 1):
        bvid = info["bvid"]
        meta = info.get("stat")
        if not meta:
            meta = fetch_view(pool.get(), bvid)
        title_now = (meta or {}).get("title") or info.get("title") or bvid
        date = fmt_date((meta or {}).get("pubdate") or info.get("created"))
        dur = clock((meta or {}).get("duration") or info.get("duration"))
        st = (meta or {}).get("stat") or {}

        if bvid in skip_bvids:
            print("[%d/%d] 已存在，跳过  %s" % (i, len(items), title_now[:38]))
            continue

        # 断点续跑：这条之前已经写成文件了，直接复用，不重新下载
        prev = done.get(bvid) if args.resume else None
        prev_name = prev.get("filename") if isinstance(prev, dict) else prev
        resumed = bool(prev_name) and os.path.exists(
            os.path.join(root, prev_name or ""))

        # 序号只为「真正占位的条目」递增，跳过的重复项不占号
        if resumed and isinstance(prev, dict) and prev.get("rank"):
            rank = prev["rank"]
        else:
            rank = start_rank + added
        added = max(added + 1, rank - start_rank + 1)

        # 文件名：{序号}_{标题}_{日期}.md —— 标题靠前，一眼能认出是哪条
        fname = "%0*d_%s_%s.md" % (width, rank,
                                   sanitize(title_now or bvid, 50), date)
        path = os.path.join(root, fname)

        if resumed:
            print("[%d/%d] 跳过（已完成）%s" % (i, len(items), title_now[:34]))
            if isinstance(prev, dict):
                r = dict(prev)
                r["rank"] = rank
            else:
                r = {"rank": rank, "date": date, "title": title_now,
                     "duration": dur, "view": st.get("view", info.get("play")),
                     "like": st.get("like"), "words": 0,
                     "sub_kind": "已跳过", "filename": prev_name, "bvid": bvid}
            rows.append(r)
            continue

        print("[%d/%d] %s" % (i, len(items), title_now[:44]))

        pages_s = pool.get()
        pgs = pages_s.api("/x/player/pagelist", {"bvid": bvid, "jsonp": "jsonp"})
        if pgs.get("code") != 0:
            print("    无法读取分P: %s" % human_err(pgs))
            rows.append(blank_row(rank, date, title_now, dur, st, info, fname, "失败"))
            continue
        page_list = pgs.get("data") or []
        cid = page_list[0]["cid"] if page_list else None
        if not cid:
            rows.append(blank_row(rank, date, title_now, dur, st, info, fname, "无分P"))
            continue

        sub, res = get_subtitles(pages_s, bvid, cid)
        subs = (sub or {}).get("subtitles") or []
        chosen = pick_subtitle(subs, args.prefer)
        items_s = []
        coverage = "-"
        if chosen:
            try:
                items_s = dedupe(download_subtitle(pages_s, chosen))
                tot = max([x["to"] for x in items_s] or [0])
                coverage = "%s / %s" % (clock(tot), clock(
                    (meta or {}).get("duration") or info.get("duration")))
            except Exception as e:
                print("    字幕下载失败: %s" % e)
                items_s = []
        if not items_s:
            print("    无可用字幕（已写入说明文件）")
        else:
            print("    %d 条 / %d 字 / 覆盖 %s"
                  % (len(items_s), sum(len(x["text"]) for x in items_s), coverage))

        md = video_markdown(info, meta or {}, items_s, chosen, cid, coverage)
        with open(path, "w", encoding="utf-8") as f:
            f.write(md)

        if args.srt and items_s:
            with open(path[:-3] + ".srt", "w", encoding="utf-8") as f:
                f.write(to_srt(items_s))

        row = {
            "rank": rank, "date": date, "title": title_now, "duration": dur,
            "view": st.get("view", info.get("play")),
            "like": st.get("like"), "words": sum(len(x["text"]) for x in items_s),
            "sub_kind": ("AI字幕" if (chosen and is_ai_sub(chosen))
                         else ("人工CC" if chosen else "无")),
            "filename": fname, "bvid": bvid,
        }
        rows.append(row)
        done[bvid] = row
        try:
            json.dump(done, open(prog_path, "w", encoding="utf-8"),
                      ensure_ascii=False)
        except Exception:
            pass
    return rows


def blank_row(rank, date, title, dur, st, info, fname, kind):
    return {"rank": i, "date": date, "title": title, "duration": dur,
            "view": st.get("view", info.get("play")), "like": st.get("like"),
            "words": 0, "sub_kind": kind, "filename": fname, "bvid": info["bvid"]}


def write_index(root, meta, rows):
    with open(os.path.join(root, "_index.md"), "w", encoding="utf-8") as f:
        f.write(index_markdown(meta, rows))
    with open(os.path.join(root, "_manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "items": rows}, f, ensure_ascii=False, indent=2)
    print("\n索引: %s" % os.path.join(root, "_index.md"))


def do_zip(root):
    zpath = root.rstrip("\\/") + ".zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(root):
            for fn in files:
                p = os.path.join(base, fn)
                z.write(p, os.path.relpath(p, os.path.dirname(root)))
    print("打包: %s (%.1f KB)" % (zpath, os.path.getsize(zpath) / 1024.0))


def print_summary(rows, root):
    withsub = [r for r in rows if r["sub_kind"] in ("AI字幕", "人工CC")]
    skipped = [r for r in rows if r["sub_kind"] == "已跳过"]
    nosub = [r for r in rows if r["sub_kind"] not in ("AI字幕", "人工CC", "已跳过")]
    print("\n" + "=" * 66)
    tail = "，%d 条是之前已完成跳过的" % len(skipped) if skipped else ""
    print("完成：共 %d 条，其中 %d 条取到文案，%d 条无字幕%s"
          % (len(rows), len(withsub), len(nosub), tail))
    if withsub:
        print("总字数: %d" % sum(r["words"] for r in withsub))
    if nosub:
        print("无字幕: " + ", ".join(r["bvid"] for r in nosub[:8])
              + (" ..." if len(nosub) > 8 else ""))
    print("目录: %s" % os.path.abspath(root))
    print("=" * 66)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已中断")
        sys.exit(130)
