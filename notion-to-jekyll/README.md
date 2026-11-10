# notion-to-jekyll

Dockerized Notion -> Jekyll exporter (Markdown + downloaded images).

## Setup
1. cd ~/cli-tools/notion-to-jekyll
2. Edit .env and set NOTION_TOKEN, PAGE_URL, and OUT (e.g. _posts/YYYY-MM-DD-your-post.md).
3. Adjust front matter fields as needed (LAYOUT, AUTHOR, CATEGORIES, IMAGE, FEATURED, HIDDEN, PERMALINK, TITLE).
4. Run make export.

Defaults: SITE=~/personal-website, IMG_DIR=assets/images/notion, IMG_URL_PREFIX=assets/images/notion.
The exporter writes .md and images directly into SITE. If IMAGE is empty, it uses the first downloaded image.
