#!/usr/bin/env python3
"""
WeChat Official Account Article Fetcher
Fetches and extracts structured content from mp.weixin.qq.com articles.
Usage:
  python3 fetch_wechat_article.py <url>
  python3 fetch_wechat_article.py <url> --format json
  python3 fetch_wechat_article.py <url> --format markdown
  python3 fetch_wechat_article.py <url> --save-dir /path/to/output
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional


BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

OUTPUT_TEMPLATE_STYLE = """
:root {
  color-scheme: light;
  --fg: #1f2328;
  --muted: #57606a;
  --border: #d0d7de;
  --bg: #ffffff;
  --chip: #f6f8fa;
  --link: #0969da;
}
body {
  margin: 0;
  background: #f6f8fa;
  color: var(--fg);
  font: 16px/1.75 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
main {
  max-width: 920px;
  margin: 32px auto;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(31, 35, 40, 0.08);
  overflow: hidden;
}
header {
  padding: 32px 36px 20px;
  border-bottom: 1px solid var(--border);
}
h1 {
  margin: 0 0 12px;
  font-size: 32px;
  line-height: 1.3;
}
.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--muted);
  font-size: 14px;
}
.meta span {
  background: var(--chip);
  border-radius: 999px;
  padding: 4px 10px;
}
.summary {
  margin-top: 16px;
  color: var(--fg);
}
.cover {
  width: 100%;
  display: block;
  max-height: 420px;
  object-fit: cover;
  border-bottom: 1px solid var(--border);
}
article {
  padding: 32px 36px 40px;
}
article img {
  max-width: 100%;
  height: auto !important;
  display: block;
  margin: 18px auto;
  border-radius: 8px;
}
article section, article p, article blockquote, article ul, article ol {
  max-width: 100%;
}
article a {
  color: var(--link);
  word-break: break-all;
}
footer {
  border-top: 1px solid var(--border);
  padding: 18px 36px 28px;
  color: var(--muted);
  font-size: 14px;
}
code, pre {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
pre {
  white-space: pre-wrap;
  background: #f6f8fa;
  padding: 14px 16px;
  border-radius: 10px;
  overflow-wrap: anywhere;
}
""".strip()


@dataclass
class ArticleData:
    source_url: str
    final_url: str
    title: str
    author: str
    account_id: str
    digest: str
    publish_time: str
    cover_url: str
    raw_page_has_captcha: bool
    body_html: str
    body_markdown: str
    body_text: str
    images: list[str]


class ContentFormatter(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.md_parts: list[str] = []
        self.text_parts: list[str] = []
        self.images: list[str] = []
        self.link_stack: list[Optional[str]] = []
        self.list_stack: list[str] = []
        self.in_pre = False
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class", "") or ""
        if tag in {"script", "style"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "br":
            self._newline()
        elif tag in {"p", "section", "article", "div"}:
            self._paragraph_break()
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._paragraph_break()
            self.md_parts.append("#" * int(tag[1]) + " ")
        elif tag in {"ul", "ol"}:
            self.list_stack.append(tag)
            self._paragraph_break()
        elif tag == "li":
            prefix = "1. " if self.list_stack and self.list_stack[-1] == "ol" else "- "
            indent = "  " * max(len(self.list_stack) - 1, 0)
            self._paragraph_break()
            self.md_parts.append(indent + prefix)
            self.text_parts.append("\n" + indent + prefix)
        elif tag == "blockquote":
            self._paragraph_break()
            self.md_parts.append("> ")
        elif tag in {"strong", "b"}:
            self.md_parts.append("**")
        elif tag in {"em", "i"}:
            self.md_parts.append("*")
        elif tag == "code":
            self.md_parts.append("`")
        elif tag == "pre":
            self.in_pre = True
            self._paragraph_break()
            self.md_parts.append("```\n")
            self.text_parts.append("\n")
        elif tag == "a":
            href = attrs_dict.get("href")
            self.link_stack.append(href)
            self.md_parts.append("[")
        elif tag == "img":
            src = (attrs_dict.get("data-src") or attrs_dict.get("src") or "").strip()
            alt = attrs_dict.get("alt") or attrs_dict.get("data-alt") or ""
            if src:
                self.images.append(src)
                alt_text = alt.strip() or "图片"
                self._paragraph_break()
                self.md_parts.append(f"![{alt_text}]({src})\n")
                self.text_parts.append(f"\n[图片] {src}\n")
        elif tag == "hr":
            self._paragraph_break()
            self.md_parts.append("---\n")
            self.text_parts.append("\n----------------------------------------\n")
        elif tag == "mp-common-profile" or "mp_profile_iframe" in classes:
            nickname = attrs_dict.get("data-nickname") or ""
            signature = attrs_dict.get("data-signature") or ""
            profile_bits = [bit for bit in [nickname, signature] if bit]
            if profile_bits:
                self._paragraph_break()
                line = " | ".join(profile_bits)
                self.md_parts.append(f"> 公众号卡片：{line}\n")
                self.text_parts.append(f"\n公众号卡片：{line}\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in {"p", "section", "article", "div", "blockquote", "li"}:
            self._paragraph_break()
        elif tag in {"strong", "b"}:
            self.md_parts.append("**")
        elif tag in {"em", "i"}:
            self.md_parts.append("*")
        elif tag == "code":
            self.md_parts.append("`")
        elif tag == "pre":
            self.in_pre = False
            self.md_parts.append("\n```\n")
            self.text_parts.append("\n")
        elif tag == "a":
            href = self.link_stack.pop() if self.link_stack else None
            self.md_parts.append(f"]({href})" if href else "]")
        elif tag in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
            self._paragraph_break()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = data.replace("\xa0", " ")
        if not text.strip() and not self.in_pre:
            return
        self.md_parts.append(text)
        self.text_parts.append(text)

    def handle_entityref(self, name: str) -> None:
        self.handle_data(html.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.handle_data(html.unescape(f"&#{name};"))

    def _newline(self) -> None:
        self.md_parts.append("\n")
        self.text_parts.append("\n")

    def _paragraph_break(self) -> None:
        self.md_parts.append("\n")
        self.text_parts.append("\n")

    def render_markdown(self) -> str:
        return normalize_whitespace("".join(self.md_parts), markdown=True)

    def render_text(self) -> str:
        return normalize_whitespace("".join(self.text_parts), markdown=False)


def normalize_whitespace(text: str, *, markdown: bool) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    if not markdown:
        text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def decode_js_escapes(value: str) -> str:
    def replace_unicode(match: re.Match[str]) -> str:
        return chr(int(match.group(1), 16))

    def replace_hex(match: re.Match[str]) -> str:
        return chr(int(match.group(1), 16))

    replacements = {
        r"\\n": "\n",
        r"\\r": "\r",
        r"\\t": "\t",
        r"\\/": "/",
        r"\\\"": '"',
        r"\\'": "'",
        r"\\\\": "\\",
    }
    value = re.sub(r"\\u([0-9a-fA-F]{4})", replace_unicode, value)
    value = re.sub(r"\\x([0-9a-fA-F]{2})", replace_hex, value)
    for src, target in replacements.items():
        value = value.replace(src, target)
    return value


def strip_cdata(value: str) -> str:
    return value.replace("<![CDATA[", "").replace("]]>", "")


def fetch_article(url: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers=BROWSER_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        html_text = resp.read().decode("utf-8", errors="replace")
        final_url = resp.geturl()
    return html_text, final_url


def extract_field(html_text: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, html_text, re.S)
        if not match:
            continue
        value = match.group(1).strip()
        if value:
            return decode_js_escapes(strip_cdata(value)).strip()
    return ""


def extract_publish_time(html_text: str) -> str:
    candidates = [
        extract_field(html_text, [r"var\s+ct\s*=\s*['\"]?(\d{10})['\"]?"]),
        extract_field(html_text, [r'"publish_time"\s*:\s*"?(\d{10})"?']),
    ]
    for candidate in candidates:
        if candidate.isdigit() and len(candidate) == 10:
            try:
                return datetime.fromtimestamp(int(candidate)).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
    return ""


def extract_body_html(html_text: str) -> str:
    payload = extract_field(html_text, [r"content_noencode\s*:\s*JsDecode\('(.+?)'\)"])
    if payload:
        return sanitize_body_html(payload)
    fallback = extract_html_block_by_id(html_text, "js_content")
    if fallback:
        return sanitize_body_html(fallback)
    return ""


def extract_html_block_by_id(html_text: str, element_id: str) -> str:
    pattern = re.compile(
        rf"<(?P<tag>[a-zA-Z0-9]+)(?P<attrs>[^>]*\bid=[\"']){re.escape(element_id)}([\"'][^>]*)>",
        re.S,
    )
    match = pattern.search(html_text)
    if not match:
        return ""
    tag = match.group("tag")
    start = match.end()
    scan = start
    depth = 1
    open_pattern = re.compile(r"<(?:/)?([a-zA-Z0-9]+)(?:\s[^<>]*?)?>", re.S)
    for tag_match in open_pattern.finditer(html_text, start):
        current_tag = tag_match.group(1).lower()
        full_tag = tag_match.group(0)
        if current_tag != tag.lower():
            continue
        if full_tag.startswith("</"):
            depth -= 1
            if depth == 0:
                return html_text[start:tag_match.start()]
        elif not full_tag.endswith("/>"):
            depth += 1
        scan = tag_match.end()
    return html_text[start:scan]


def sanitize_body_html(body_html: str) -> str:
    body_html = body_html.strip()
    body_html = body_html.replace("<\/", "</")
    body_html = body_html.replace("﻿", "")
    body_html = html.unescape(body_html)
    body_html = re.sub(r"<script[^>]*>.*?</script>", "", body_html, flags=re.S | re.I)
    body_html = re.sub(r"<style[^>]*>.*?</style>", "", body_html, flags=re.S | re.I)
    return body_html.strip()


def extract_images(body_html: str) -> list[str]:
    urls: list[str] = []
    for match in re.finditer(r"<(?:img|image)\b[^>]*(?:data-src|src)=['\"]([^'\"]+)['\"]", body_html, re.I):
        src = html.unescape(match.group(1).strip())
        if src and src not in urls:
            urls.append(src)
    return urls


def to_markdown_and_text(body_html: str) -> tuple[str, str, list[str]]:
    parser = ContentFormatter()
    parser.feed(body_html)
    parser.close()
    images: list[str] = []
    for src in parser.images:
        if src not in images:
            images.append(src)
    return parser.render_markdown(), parser.render_text(), images


def build_article_data(source_url: str, final_url: str, html_text: str) -> ArticleData:
    title = extract_field(html_text, [r"var\s+msg_title\s*=\s*['\"]([^'\"]+)['\"]"])
    author = extract_field(
        html_text,
        [r"var\s+nickname\s*=\s*['\"]([^'\"]+)['\"]", r'data-nickname=["\']([^"\']+)["\']'],
    )
    account_id = extract_field(html_text, [r"var\s+biz\s*=\s*['\"]([^'\"]+)['\"]"])
    digest = extract_field(html_text, [r"var\s+msg_desc\s*=\s*['\"]([^'\"]+)['\"]"])
    cover_url = extract_field(
        html_text,
        [r"var\s+msg_cdn_url\s*=\s*['\"]([^'\"]+)['\"]", r'"cdn_url"\s*:\s*"([^"]+)"'],
    )
    publish_time = extract_publish_time(html_text)
    body_html = extract_body_html(html_text)
    body_markdown, body_text, parser_images = to_markdown_and_text(body_html) if body_html else ("", "", [])
    image_urls = extract_images(body_html)
    for src in parser_images:
        if src not in image_urls:
            image_urls.append(src)
    return ArticleData(
        source_url=source_url,
        final_url=final_url,
        title=title,
        author=author,
        account_id=account_id,
        digest=digest,
        publish_time=publish_time,
        cover_url=cover_url,
        raw_page_has_captcha=("环境异常" in html_text and "wappoc_appmsgcaptcha" in html_text),
        body_html=body_html,
        body_markdown=body_markdown,
        body_text=body_text,
        images=image_urls,
    )


def article_to_json(article: ArticleData) -> dict:
    return {
        "title": article.title,
        "author": article.author,
        "account_id": article.account_id,
        "digest": article.digest,
        "publish_time": article.publish_time,
        "cover_url": article.cover_url,
        "source_url": article.source_url,
        "final_url": article.final_url,
        "raw_page_has_captcha": article.raw_page_has_captcha,
        "body_html": article.body_html,
        "body_markdown": article.body_markdown,
        "body_text": article.body_text,
        "images": article.images,
    }


def render_text_output(article: ArticleData) -> str:
    lines: list[str] = []
    if article.title:
        lines.append(f"标题: {article.title}")
    if article.author:
        lines.append(f"作者/公众号: {article.author}")
    if article.publish_time:
        lines.append(f"发布时间: {article.publish_time}")
    if article.digest:
        lines.append(f"摘要: {article.digest}")
    if article.cover_url:
        lines.append(f"封面图: {article.cover_url}")
    lines.append(f"源链接: {article.source_url}")
    if article.final_url and article.final_url != article.source_url:
        lines.append(f"最终链接: {article.final_url}")
    lines.append(f"检测到验证页外壳: {'是' if article.raw_page_has_captcha else '否'}")
    lines.append(f"图片数量: {len(article.images)}")
    lines.append("")
    lines.append("正文（Markdown 近似保留版）:")
    lines.append(article.body_markdown or "[空]")
    if article.images:
        lines.append("")
        lines.append("图片链接:")
        lines.extend(f"- {src}" for src in article.images)
    return "\n".join(lines).strip()


def slugify(value: str) -> str:
    value = re.sub(r"\s+", "-", value.strip())
    value = re.sub(r"[^0-9A-Za-z\-一-鿿]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "wechat-article"


def build_archive_html(article: ArticleData) -> str:
    meta_items = []
    if article.author:
        meta_items.append(f"<span>公众号：{html.escape(article.author)}</span>")
    if article.publish_time:
        meta_items.append(f"<span>发布时间：{html.escape(article.publish_time)}</span>")
    meta_items.append(f"<span>图片数量：{len(article.images)}</span>")
    meta_items.append(
        f'<span><a href="{html.escape(article.source_url)}" target="_blank" rel="noreferrer">原文链接</a></span>'
    )
    summary = f'<p class="summary">{html.escape(article.digest)}</p>' if article.digest else ""
    cover = f'<img class="cover" src="{html.escape(article.cover_url)}" alt="封面图">' if article.cover_url else ""
    return f"""<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(article.title or '微信公众号文章归档')}</title>
  <style>{OUTPUT_TEMPLATE_STYLE}</style>
</head>
<body>
  <main>
    <header>
      <h1>{html.escape(article.title or '未命名文章')}</h1>
      <div class=\"meta\">{''.join(meta_items)}</div>
      {summary}
    </header>
    {cover}
    <article>
      {article.body_html}
    </article>
    <footer>
      <div>抓取时间：{html.escape(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</div>
      <div>检测到验证页外壳：{'是' if article.raw_page_has_captcha else '否'}</div>
      <div>最终链接：{html.escape(article.final_url)}</div>
    </footer>
  </main>
</body>
</html>
""".strip()


def save_outputs(article: ArticleData, save_dir: Path) -> dict[str, str]:
    save_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_name = f"{timestamp}-{slugify(article.title or 'wechat-article')}"
    files = {
        "json": save_dir / f"{base_name}.json",
        "markdown": save_dir / f"{base_name}.md",
        "text": save_dir / f"{base_name}.txt",
        "body_html": save_dir / f"{base_name}.body.html",
        "archive_html": save_dir / f"{base_name}.html",
    }
    files["json"].write_text(json.dumps(article_to_json(article), ensure_ascii=False, indent=2), encoding="utf-8")
    files["markdown"].write_text(article.body_markdown, encoding="utf-8")
    files["text"].write_text(render_text_output(article), encoding="utf-8")
    files["body_html"].write_text(article.body_html, encoding="utf-8")
    files["archive_html"].write_text(build_archive_html(article), encoding="utf-8")
    return {name: str(path) for name, path in files.items()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="读取微信公众号文章并提取结构化内容")
    parser.add_argument("url", help="微信公众号文章 URL")
    parser.add_argument("--format", choices=["text", "json", "markdown", "html"], default="text", help="输出格式，默认 text")
    parser.add_argument("--save-dir", help="将抓取结果保存到指定目录")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    url = args.url.strip()
    if "mp.weixin.qq.com" not in url:
        print("错误: URL 不是微信公众号文章链接", file=sys.stderr)
        sys.exit(1)
    try:
        html_text, final_url = fetch_article(url)
    except Exception as exc:
        print(f"错误: 无法获取文章内容 - {exc}", file=sys.stderr)
        sys.exit(1)
    article = build_article_data(url, final_url, html_text)
    if not article.body_html and not article.body_text:
        print("错误: 正文提取失败，文章可能已被删除、受访问限制，或页面结构发生变化。", file=sys.stderr)
        sys.exit(1)
    saved_files: dict[str, str] = {}
    if args.save_dir:
        saved_files = save_outputs(article, Path(args.save_dir).expanduser())
    if args.format == "json":
        print(json.dumps(article_to_json(article), ensure_ascii=False, indent=2))
    elif args.format == "markdown":
        print(article.body_markdown)
    elif args.format == "html":
        print(article.body_html)
    else:
        print(render_text_output(article))
    if saved_files:
        print("\n已保存文件:", file=sys.stderr)
        for name, path in saved_files.items():
            print(f"- {name}: {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
