# all of this crap was vibecoded but it works...

import os
import re
import sys
import hashlib
import mimetypes
from datetime import date
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests

NOTION_VERSION = "2022-06-28"
API = "https://api.notion.com/v1"


def die(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def env(name, default=None, required=False):
    v = os.getenv(name)
    if v is None or v == "":
        v = default
    if required and (v is None or v == ""):
        die(f"{name} is required")
    return v


def parse_bool(v, default=False):
    if v is None or v == "":
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def extract_page_id(s):
    if not s:
        return None
    s = s.strip()
    m = re.search(r"([0-9a-fA-F]{32})", s.replace("-", ""))
    if not m:
        return None
    raw = m.group(1).lower()
    return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"


def notion_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
    }


def notion_get(session, path, params=None):
    r = session.get(f"{API}{path}", params=params, timeout=30)
    if not r.ok:
        die(f"Notion API {path} failed ({r.status_code}): {r.text}")
    return r.json()


def rich_text_to_md(rich):
    out = []
    for rt in rich or []:
        if rt.get("type") == "text":
            text = rt["text"].get("content", "")
            link = rt["text"].get("link")
            href = link.get("url") if link else None
        elif rt.get("type") == "equation":
            expr = rt.get("equation", {}).get("expression", "")
            text = f"${expr}$"
            href = None
        else:
            text = rt.get("plain_text", "")
            href = rt.get("href")
        ann = rt.get("annotations", {})
        if ann.get("code"):
            text = f"`{text}`"
        if ann.get("bold"):
            text = f"**{text}**"
        if ann.get("italic"):
            text = f"*{text}*"
        if ann.get("strikethrough"):
            text = f"~~{text}~~"
        if ann.get("underline"):
            text = f"<u>{text}</u>"
        if href and not ann.get("code"):
            text = f"[{text}]({href})"
        out.append(text)
    return "".join(out)


def slugify(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "page"


class Exporter:
    def __init__(self, session, site_dir, out_rel, img_dir_rel, img_url_prefix, slug="image"):
        self.session = session
        self.site_dir = Path(site_dir)
        self.out_path = self.site_dir / out_rel
        self.img_dir = self.site_dir / img_dir_rel
        self.img_url_prefix = (img_url_prefix or "").rstrip("/")
        self.slug = slugify(slug)
        self.downloaded = []

    def fetch_children(self, block_id):
        results = []
        cursor = None
        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            data = notion_get(self.session, f"/blocks/{block_id}/children", params=params)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return results

    def download_image(self, url, block_id):
        self.img_dir.mkdir(parents=True, exist_ok=True)
        parsed = urlparse(url)
        name = unquote(Path(parsed.path).name) or "image"
        ext = Path(name).suffix
        if not ext or len(ext) > 6:
            ext = ""
        # friendly name based on page slug; avoid collisions
        index = len(self.downloaded) + 1
        base_name = self.slug if index == 1 else f"{self.slug}-{index}"
        filename = f"{base_name}{ext}" if ext else base_name
        dest = self.img_dir / filename
        try:
            r = self.session.get(url, timeout=60)
            r.raise_for_status()
        except Exception:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
        content = r.content
        if not dest.suffix:
            ctype = r.headers.get("Content-Type", "").split(";")[0].strip()
            guess = mimetypes.guess_extension(ctype) or ".bin"
            if guess == ".jpe":
                guess = ".jpg"
            dest = dest.with_suffix(guess)
            filename = dest.name
        # if name collides with a different file, add numeric suffix
        if dest.exists():
            try:
                if dest.read_bytes() != content:
                    n = 2
                    while True:
                        candidate = self.img_dir / f"{dest.stem}-{n}{dest.suffix}"
                        if not candidate.exists() or candidate.read_bytes() == content:
                            dest = candidate
                            filename = dest.name
                            break
                        n += 1
            except Exception:
                pass
        dest.write_bytes(content)
        local = f"{self.img_url_prefix}/{filename}" if self.img_url_prefix else filename
        self.downloaded.append(local)
        return local

    def block_to_md(self, block, depth=0):
        btype = block.get("type")
        data = block.get(btype, {}) if btype else {}
        indent = "  " * depth
        lines = []

        def children_md(extra_depth=0):
            if not block.get("has_children"):
                return []
            kids = self.fetch_children(block["id"])
            out = []
            for k in kids:
                out.extend(self.block_to_md(k, depth + extra_depth))
            return out

        if btype == "paragraph":
            text = rich_text_to_md(data.get("rich_text"))
            lines.append(f"{indent}{text}" if text.strip() else "")
            lines.extend(children_md())
        elif btype == "heading_1":
            lines.append(f"# {rich_text_to_md(data.get('rich_text'))}")
            lines.extend(children_md())
        elif btype == "heading_2":
            lines.append(f"## {rich_text_to_md(data.get('rich_text'))}")
            lines.extend(children_md())
        elif btype == "heading_3":
            lines.append(f"### {rich_text_to_md(data.get('rich_text'))}")
            lines.extend(children_md())
        elif btype == "bulleted_list_item":
            lines.append(f"{indent}- {rich_text_to_md(data.get('rich_text'))}")
            lines.extend(children_md(1))
        elif btype == "numbered_list_item":
            lines.append(f"{indent}1. {rich_text_to_md(data.get('rich_text'))}")
            lines.extend(children_md(1))
        elif btype == "to_do":
            checked = "x" if data.get("checked") else " "
            lines.append(f"{indent}- [{checked}] {rich_text_to_md(data.get('rich_text'))}")
            lines.extend(children_md(1))
        elif btype == "quote":
            text = rich_text_to_md(data.get("rich_text"))
            for l in (text.splitlines() or [""]):
                lines.append(f"> {l}")
            lines.extend(children_md())
        elif btype == "code":
            lang = data.get("language") or ""
            if lang == "plain text":
                lang = ""
            code = rich_text_to_md(data.get("rich_text"))
            lines.append(f"```{lang}")
            lines.append(code)
            lines.append("```")
        elif btype == "divider":
            lines.append("---")
        elif btype == "image":
            url = None
            if data.get("type") == "file":
                url = data.get("file", {}).get("url")
            elif data.get("type") == "external":
                url = data.get("external", {}).get("url")
            caption = rich_text_to_md(data.get("caption"))
            alt = caption or "image"
            if url:
                local = self.download_image(url, block["id"])
                lines.append(f"![{alt}]({local})")
            else:
                lines.append(f"![{alt}]()")
        elif btype == "callout":
            text = rich_text_to_md(data.get("rich_text"))
            icon = data.get("icon", {}) or {}
            emoji = icon.get("emoji", "") if icon.get("type") == "emoji" else ""
            prefix = f"{emoji} " if emoji else ""
            lines.append(f"> {prefix}{text}".rstrip())
            lines.extend(children_md())
        else:
            text = rich_text_to_md(data.get("rich_text")) if isinstance(data, dict) and data.get("rich_text") else ""
            if text:
                lines.append(text)
            lines.extend(children_md())

        return lines


def yaml_quote(s):
    s = str(s).replace('\\', '\\\\').replace('"', '\\"')
    return f'"{s}"'


def main():
    token = env("NOTION_TOKEN", required=True)
    page_ref = env("PAGE_URL") or env("PAGE_ID")
    page_id = extract_page_id(page_ref or "")
    if not page_id:
        die("Provide PAGE_URL or PAGE_ID")

    site_dir = env("SITE_DIR", "/site")
    out_rel = env("OUT", "")
    img_dir_rel = env("IMG_DIR", "assets/images/notion")
    img_url_prefix = env("IMG_URL_PREFIX", "assets/images/notion")
    layout = env("LAYOUT", "post")
    title_override = env("TITLE")
    permalink = env("PERMALINK")
    author = env("AUTHOR")
    categories = env("CATEGORIES")
    featured = env("FEATURED")
    hidden = env("HIDDEN")
    image_field = env("IMAGE")
    post_date = env("DATE", date.today().isoformat())
    slug_env = env("SLUG")

    session = requests.Session()
    session.headers.update(notion_headers(token))

    page = notion_get(session, f"/pages/{page_id}")
    props = page.get("properties", {})
    title = title_override
    if not title:
        for p in props.values():
            if p.get("type") == "title":
                title = "".join(t.get("plain_text", "") for t in p.get("title", []))
                break
    title = title or "Untitled"

    slug = slug_env or slugify(title)
    if not out_rel or out_rel.strip() == "":
        out_rel = f"_posts/{post_date}-{slug}.md"
    else:
        out_rel = out_rel.replace("{date}", post_date).replace("{slug}", slug)

    exporter = Exporter(session, site_dir, out_rel, img_dir_rel, img_url_prefix, slug=slug)
    blocks = exporter.fetch_children(page_id)
    body_lines = []
    for b in blocks:
        md_lines = exporter.block_to_md(b)
        if not md_lines:
            continue
        if body_lines and body_lines[-1] != "":
            body_lines.append("")
        body_lines.extend(md_lines)
    body = "\n".join(body_lines).strip() + "\n"

    if not image_field and exporter.downloaded:
        image_field = exporter.downloaded[0]

    fm = ["---"]
    fm.append(f"layout: {layout}")
    fm.append(f"title: {yaml_quote(title)}")
    if author:
        fm.append(f"author: {author}")
    if categories:
        cats = [c.strip() for c in categories.split(",") if c.strip()]
        if cats:
            fm.append("categories: [" + ", ".join(cats) + "]")
    if image_field:
        fm.append(f"image: {image_field}")
    if featured is not None and featured != "":
        fm.append(f"featured: {'true' if parse_bool(featured) else 'false'}")
    if hidden is not None and hidden != "":
        fm.append(f"hidden: {'true' if parse_bool(hidden) else 'false'}")
    if permalink:
        fm.append(f"permalink: {permalink}")
    fm.append("---")
    fm.append("")

    exporter.out_path.parent.mkdir(parents=True, exist_ok=True)
    exporter.out_path.write_text("\n".join(fm) + body, encoding="utf-8")

    print(f"Exported page: {title}")
    print(f"Markdown: {exporter.out_path}")
    print(f"Images dir: {exporter.img_dir}")
    if exporter.downloaded:
        print(f"Images: {len(exporter.downloaded)}")


if __name__ == "__main__":
    main()
