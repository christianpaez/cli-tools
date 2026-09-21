import os
import re
import sys
from dotenv import load_dotenv
from substack import Api

load_dotenv()

sid = os.getenv("SUBSTACK_SID")
if sid:
    api = Api(cookies_string=f"substack.sid={sid}", publication_url=os.getenv("PUBLICATION_URL"))
else:
    api = Api(
        email=os.getenv("EMAIL"),
        password=os.getenv("PASSWORD"),
        publication_url=os.getenv("PUBLICATION_URL"),
    )

def parse_frontmatter(s):
    s = s.strip()
    if not s.startswith("---"):
        return s, None, None
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", s, re.DOTALL)
    if not m:
        return s, None, None
    fm = m.group(1)
    title_match = re.search(r"^title:\s*(.+)$", fm, re.MULTILINE)
    title = title_match.group(1).strip().strip('"') if title_match else None
    image_match = re.search(r"^image:\s*(.+)$", fm, re.MULTILINE)
    image = image_match.group(1).strip().strip('"') if image_match else None
    return s[m.end():], title, image

file = sys.argv[1] if len(sys.argv) > 1 else "post.md"

with open(file) as f:
    raw = f.read()

md, fm_title, fm_image = parse_frontmatter(raw)
title_arg = sys.argv[2] if len(sys.argv) > 2 else None
title = title_arg or fm_title or os.path.splitext(os.path.basename(file))[0]

if fm_image:
    if not fm_image.startswith(("http://", "https://")):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rel_path = os.path.relpath(os.path.join(project_root, fm_image))
        if os.path.exists(os.path.join(project_root, fm_image)):
            fm_image = rel_path
    alt = os.path.splitext(os.path.basename(fm_image))[0].replace("-", " ").replace("_", " ").title()
    md = f"![{alt}]({fm_image})\n\n" + md

result = api.create_draft_from_markdown(
    title=title,
    markdown=md,
    publish=True,
    send=True,
)

url = result.get("url")
if not url and result.get("slug"):
    url = f"{os.getenv('PUBLICATION_URL')}/p/{result['slug']}"
print(f"Published: {url}")
