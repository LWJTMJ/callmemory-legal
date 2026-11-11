#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build static legal pages for 打给回忆 from project docs (read-only)."""
import html
import os
import re

SRC = "/Users/jayli/AI/打给回忆/docs"
OUT = "/tmp/callmemory-legal"

EFFECTIVE_ZH = "2026-11-12"
EFFECTIVE_EN = "2026-11-12"


def strip_internal(text):
    """Cut everything from the internal-note marker onwards."""
    for marker in ("<!-- ===== 内部备注", "<!-- ===== INTERNAL NOTE"):
        i = text.find(marker)
        if i != -1:
            text = text[:i]
    # drop trailing horizontal rules / whitespace
    return text.rstrip().rstrip("-").rstrip()


def inline(s):
    """Inline markdown -> HTML: code, bold, links, autolinks, escape first."""
    parts = []
    # protect inline code
    def code_sub(m):
        parts.append("<code>%s</code>" % html.escape(m.group(1)))
        return "\x00%d\x00" % (len(parts) - 1)

    s = re.sub(r"`([^`]+)`", code_sub, s)

    def link_sub(m):
        label, url = m.group(1), m.group(2)
        parts.append('<a href="%s">%s</a>' % (html.escape(url, quote=True), html.escape(label)))
        return "\x00%d\x00" % (len(parts) - 1)

    def auto_sub(m):
        url = m.group(1)
        parts.append('<a href="%s">%s</a>' % (html.escape(url, quote=True), html.escape(url)))
        return "\x00%d\x00" % (len(parts) - 1)

    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", link_sub, s)
    s = re.sub(r"<(https?://[^>]+)>", auto_sub, s)

    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)

    def restore(m):
        return parts[int(m.group(1))]

    return re.sub(r"\x00(\d+)\x00", restore, s)


def md_to_html(text):
    lines = text.split("\n")
    out = []
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            out.append("<h%d>%s</h%d>" % (level, inline(m.group(2)), level))
            i += 1
            continue

        # unordered list
        if re.match(r"^[-*]\s+", stripped):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i].rstrip()):
                item = re.sub(r"^\s*[-*]\s+", "", lines[i].rstrip()).strip()
                # continuation lines (indented, non-list)
                i += 1
                while i < n and lines[i].strip() and not re.match(
                    r"^\s*[-*]\s+", lines[i]
                ) and not lines[i].startswith(("#", ">", "|")):
                    item += " " + lines[i].strip()
                    i += 1
                items.append("<li>%s</li>" % inline(item))
            out.append("<ul>\n%s\n</ul>" % "\n".join(items))
            continue

        # ordered list
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i].rstrip()):
                item = re.sub(r"^\s*\d+\.\s+", "", lines[i].rstrip()).strip()
                i += 1
                while i < n and lines[i].strip() and not re.match(
                    r"^\s*\d+\.\s+", lines[i]
                ) and not lines[i].startswith(("#", ">", "|")):
                    item += " " + lines[i].strip()
                    i += 1
                items.append("<li>%s</li>" % inline(item))
            out.append("<ol>\n%s\n</ol>" % "\n".join(items))
            continue

        # blockquote
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote>%s</blockquote>" % inline(" ".join(buf)))
            continue

        # paragraph: gather until blank / structural line
        buf = []
        while i < n:
            cur = lines[i].rstrip()
            if not cur.strip():
                break
            if re.match(r"^(#{1,6}\s|[-*]\s|\d+\.\s|>|-\-\-|\|)", cur.strip()):
                break
            buf.append(cur.strip())
            i += 1
        # bold "label:" lines are authored as separate visual lines -> hard break
        joined = ""
        for k, chunk in enumerate(buf):
            if k == 0:
                joined = inline(chunk)
            elif re.match(r"^\*\*(?:[^*]+\*\*[：:]|[^*]+[：:]\*\*)", chunk):
                joined += "<br>\n" + inline(chunk)
            else:
                joined += " " + inline(chunk)
        out.append("<p>%s</p>" % joined)

    return "\n".join(out)


PAGE_ZH = """<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>打给回忆 · 隐私政策</title>
<meta name="description" content="打给回忆（Call Your Memory）隐私政策：无服务器、无账号，录音只留在你的设备与你的 iCloud。">
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
<nav class="lang"><a href="en/" hreflang="en">English</a> · <a href="support.html">支持 / Support</a></nav>
{body}
<hr>
<footer>
<p>打给回忆 / Call Your Memory · 开发者：李杰（Weijie Li）<br>
联系：<a href="mailto:lwjtmj@outlook.com">lwjtmj@outlook.com</a></p>
<p><a href="en/">English Privacy Policy</a> · <a href="support.html">技术支持 / Support</a></p>
</footer>
</main>
</body>
</html>
"""

PAGE_EN = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Call Your Memory — Privacy Policy</title>
<meta name="description" content="Privacy policy for Call Your Memory: no server, no account. Recordings stay on your device and in your own iCloud.">
<link rel="stylesheet" href="../style.css">
</head>
<body>
<main>
<nav class="lang"><a href="../" hreflang="zh-Hans">中文</a> · <a href="../support.html">Support</a></nav>
{body}
<hr>
<footer>
<p>Call Your Memory / 打给回忆 · Developer: Weijie Li (李杰)<br>
Contact: <a href="mailto:lwjtmj@outlook.com">lwjtmj@outlook.com</a></p>
<p><a href="../">中文隐私政策</a> · <a href="../support.html">Support</a></p>
</footer>
</main>
</body>
</html>
"""

SUPPORT = """<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>打给回忆 · 技术支持</title>
<meta name="description" content="打给回忆（Call Your Memory）技术支持与常见问题：取消订阅、录音位置、删除录音、iCloud 同步。">
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
<nav class="lang"><a href="./">隐私政策</a> · <a href="en/">English Privacy Policy</a></nav>

<h1>打给回忆 · 技术支持</h1>
<p class="meta">生效日期：2026-11-12</p>

<p><strong>打给回忆（Call Your Memory）</strong>是一款 iOS 应用：你可以对着空气录下一段话，留给未来的某一天，或者留给某一个人——到点它会给你的手机打回来。</p>

<h2>联系开发者</h2>
<p>遇到问题、想反馈建议，或对隐私政策有疑问，请写信到：<br>
<strong><a href="mailto:lwjtmj@outlook.com">lwjtmj@outlook.com</a></strong></p>
<p>我们通常在 7 个工作日内回复。写信时如果能附上 iPhone 型号、iOS 版本和 App 版本，会帮我们更快定位问题。</p>

<h2>常见问题</h2>

<h3>1. 如何取消订阅（会员）？</h3>
<p>订阅由 Apple 管理，App 里不能直接替你取消。请前往：<br>
<strong>iOS 设置 → 你的名字（Apple ID）→ 订阅 → 打给回忆 → 取消订阅</strong></p>
<p>也可以在 App Store 里点右上角头像 → 订阅，找到本 App 后取消。取消后当前订阅周期到期不再续费，已付费的周期内仍可使用会员功能。退款由 Apple 处理，需要在 Apple 的「报告问题」页面申请。</p>

<h3>2. 我的录音存在哪里？</h3>
<p>只存在两个地方，都由你自己掌握：</p>
<ul>
<li><strong>本机</strong>：App 的私有存储目录，其他 App 读不到。</li>
<li><strong>你自己的 iCloud</strong>：如果设备登录了 iCloud，录音会同时写入 <code>iCloud.com.jayli.callmemory</code> 这个 CloudKit <strong>私有数据库</strong>。只有你的 Apple ID 能读写，开发者看不到里面的内容。</li>
</ul>
<p>本 App 没有服务器、没有账号，录音不会上传到开发者这一侧。</p>

<h3>3. 如何删除录音？</h3>
<ul>
<li><strong>单条删除</strong>：在 App 内找到这条录音，左滑或长按选择删除。删除后若开启了 iCloud 同步，iCloud 中的副本也会一并删除。</li>
<li><strong>全部删除</strong>：在系统里删除本 App，本机的录音与设置会一起被删掉。</li>
<li><strong>只清 iCloud 副本</strong>：iOS 设置 → 你的名字 → iCloud → 管理账户存储 → 打给回忆 → 删除数据。</li>
</ul>
<p>注意：删除 App 本身不会自动清掉 iCloud 里的副本，需要按上面第三条单独处理。</p>

<h3>4. iCloud 同步是怎么工作的？</h3>
<ul>
<li>同步走 Apple 的 CloudKit <strong>私有数据库</strong>，同一 Apple ID 的设备之间自动保持一致。</li>
<li>没有登录 iCloud 时不同步，录音只保存在本机，功能照常可用。</li>
<li>如果同步看起来卡住了，先确认「设置 → 你的名字 → iCloud」已登录、iCloud Drive 可用，并检查网络；仍不生效可以重启 App 或设备后再看。</li>
<li>开发者无法访问、导出或恢复你的 iCloud 数据——这部分只有 Apple 和你本人能操作。</li>
</ul>

<h3>5. 需要麦克风、通讯录、定位、通知权限吗？</h3>
<ul>
<li><strong>麦克风</strong>：录音必需，只在你按下录音键时使用。</li>
<li><strong>通讯录</strong>：<strong>只读</strong>，仅用于把电话号码对上姓名/昵称，方便「拨给某个人」。拒绝授权只影响这一个功能，其他功能照常可用。App 不会修改你的通讯录。</li>
<li><strong>定位</strong>：<strong>默认不请求</strong>，只有你在设置里主动开启「城市称呼」后才会读取大致城市名，坐标不写入磁盘、不上传。</li>
<li><strong>通知</strong>：只用于「未来来电」到点提醒，由系统在本地生成，不经过任何服务器。</li>
</ul>

<h3>6. 数据会在我换手机后丢失吗？</h3>
<p>如果两台设备登录同一个 Apple ID 且开启了 iCloud 同步，录音会同步过去。也可以随时在 App 内把全部录音打包导出到系统「文件」，导出的文件由你自己保管。</p>

<hr>
<footer>
<p>打给回忆 / Call Your Memory · 开发者：李杰（Weijie Li）<br>
联系：<a href="mailto:lwjtmj@outlook.com">lwjtmj@outlook.com</a></p>
<p><a href="./">隐私政策</a> · <a href="en/">English Privacy Policy</a></p>
</footer>
</main>
</body>
</html>
"""

STYLE = """/* 打给回忆 · 静态法律页面样式（无任何外链资源） */
:root {
  --fg: #1c1c1e;
  --muted: #6b6b70;
  --bg: #fdfcfa;
  --rule: #e3e0da;
  --accent: #8a5a3b;
}

* { box-sizing: border-box; }

html { -webkit-text-size-adjust: 100%; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--fg);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  font-size: 16.5px;
  line-height: 1.75;
}

main {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 20px 64px;
}

nav.lang {
  font-size: 0.9em;
  color: var(--muted);
  margin-bottom: 20px;
}

nav.lang a { color: var(--muted); }

h1 {
  font-size: 1.7em;
  line-height: 1.35;
  margin: 0 0 8px;
  letter-spacing: 0.01em;
}

h2 {
  font-size: 1.22em;
  margin: 2em 0 0.6em;
  padding-top: 0.2em;
}

h3 {
  font-size: 1.04em;
  margin: 1.6em 0 0.4em;
}

p, li { margin: 0.7em 0; }

ul, ol { padding-left: 1.3em; }

li > ul, li > ol { margin: 0.3em 0; }

hr {
  border: 0;
  border-top: 1px solid var(--rule);
  margin: 2.4em 0 1.6em;
}

a { color: var(--accent); text-decoration: underline; text-underline-offset: 2px; }

a:hover { text-decoration-thickness: 2px; }

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.9em;
  background: #f2efe9;
  border-radius: 4px;
  padding: 0.1em 0.35em;
  word-break: break-word;
}

blockquote {
  margin: 1.2em 0;
  padding: 0.2em 0 0.2em 1em;
  border-left: 3px solid var(--rule);
  color: var(--muted);
}

p.meta {
  color: var(--muted);
  font-size: 0.9em;
  margin: 0 0 1.6em;
}

strong { font-weight: 600; }

footer {
  color: var(--muted);
  font-size: 0.9em;
}

footer a { color: var(--muted); }

@media (max-width: 480px) {
  body { font-size: 16px; }
  main { padding: 24px 16px 48px; }
  h1 { font-size: 1.45em; }
}
"""


SOURCE_PATH_REFS = [
    "（`Core/LCDNavigation.swift:91`）",
]


def strip_internal_refs(text):
    """Public pages must not carry source-file paths / line numbers."""
    for ref in SOURCE_PATH_REFS:
        text = text.replace(ref, "")
    text = re.sub(r"`[A-Za-z][A-Za-z0-9_]+(?:/[A-Za-z0-9_.]+)+\.(?:swift|m|h)(?::\d+(?:-\d+)?)?`", "", text)
    text = re.sub(r"[（(]\s*[)）]", "", text)
    text = re.sub(r"([\"”」])\s+\.", r"\1.", text)
    return re.sub(r"[ \t]{2,}", " ", text)


APPLE_URL_RE = re.compile(
    r'<a href="(https://www\.apple\.com/legal/privacy/)">[^<]*</a>'
)


def deanchor_third_party(html_text):
    """要求：页面 0 条第三方外链。第三方 URL 保留为纯文本引用，不做可点击外链。"""
    return APPLE_URL_RE.sub(r"\1", html_text)


def main():
    zh = strip_internal(open(os.path.join(SRC, "privacy-policy-zh.md"), encoding="utf-8").read())
    en = strip_internal(open(os.path.join(SRC, "privacy-policy-en.md"), encoding="utf-8").read())

    os.makedirs(os.path.join(OUT, "en"), exist_ok=True)

    zh = strip_internal_refs(zh)
    en = strip_internal_refs(en)

    zh_html = PAGE_ZH.format(eff_zh=EFFECTIVE_ZH, body=md_to_html(zh))
    en_html = PAGE_EN.format(eff_en=EFFECTIVE_EN, body=md_to_html(en))
    zh_html = deanchor_third_party(zh_html)
    en_html = deanchor_third_party(en_html)

    # 生效日期紧跟标题，作为页面顶部标识
    zh_html = zh_html.replace(
        "</h1>",
        '</h1>\n<p class="meta">生效日期：%s　|　适用版本 1.0 及以后</p>' % EFFECTIVE_ZH,
        1,
    )
    en_html = en_html.replace(
        "</h1>",
        '</h1>\n<p class="meta">Effective date: %s　|　Applies to version 1.0 and later</p>'
        % EFFECTIVE_EN,
        1,
    )

    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(zh_html)
    with open(os.path.join(OUT, "en", "index.html"), "w", encoding="utf-8") as f:
        f.write(en_html)
    with open(os.path.join(OUT, "support.html"), "w", encoding="utf-8") as f:
        f.write(SUPPORT)
    with open(os.path.join(OUT, "style.css"), "w", encoding="utf-8") as f:
        f.write(STYLE)

    # leftover-markdown sanity check
    for name in ("index.html", os.path.join("en", "index.html"), "support.html"):
        text = open(os.path.join(OUT, name), encoding="utf-8").read()
        leaks = [m for m in ("## ", "**", "\x00") if m in text]
        print("%-18s %6d bytes  leftover=%s" % (name, len(text), leaks or "none"))


if __name__ == "__main__":
    main()
