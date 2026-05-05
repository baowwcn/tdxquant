import html.parser
import os
import re


class HTMLToMarkdown(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.tag_stack = []
        self.in_content = False
        self.in_code = False
        self.in_pre = False
        self.list_counter = []
        self.skip = False
        self.current_tag = None
        self._pending_link = None
        self.in_thead = False
        self.in_tbody = False
        self.row_cells = []
        self.table_rows = []
        self.in_table = False

    def reset_state(self):
        self.result = []
        self.tag_stack = []
        self.in_content = False
        self.in_code = False
        self.in_pre = False
        self.list_counter = []
        self.skip = False
        self.current_tag = None
        self._pending_link = None
        self.in_thead = False
        self.in_tbody = False
        self.row_cells = []
        self.table_rows = []
        self.in_table = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag_lower = tag.lower()

        if tag_lower == "div" and "content__default" in attrs_dict.get("class", ""):
            self.in_content = True
            return

        if not self.in_content:
            return

        self.tag_stack.append(tag_lower)
        self.current_tag = tag_lower

        if tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.result.append("\n\n")
        elif tag_lower == "p":
            self.result.append("\n\n")
        elif tag_lower == "br":
            self.result.append("  \n")
        elif tag_lower in ("strong", "b"):
            self.result.append("**")
        elif tag_lower in ("em", "i"):
            self.result.append("*")
        elif tag_lower == "code":
            if not self.in_pre:
                self.result.append("`")
            self.in_code = True
        elif tag_lower == "pre":
            self.in_pre = True
            lang = ""
            cls = attrs_dict.get("class", "")
            lang_match = re.search(r"language-(\w+)", cls)
            if lang_match:
                lang = lang_match.group(1)
            self.result.append(f"\n```{lang}\n")
        elif tag_lower == "ul":
            self.list_counter.append(0)
            self.result.append("\n\n")
        elif tag_lower == "ol":
            self.list_counter.append(0)
            self.result.append("\n\n")
        elif tag_lower == "li":
            indent = "  " * (len(self.list_counter) - 1)
            if self.list_counter and self.list_counter[-1] > 0:
                self.list_counter[-1] += 1
                self.result.append(f"\n{indent}{self.list_counter[-1]}. ")
            else:
                if self.list_counter:
                    self.list_counter[-1] += 1
                self.result.append(f"\n{indent}- ")
        elif tag_lower == "a":
            href = attrs_dict.get("href", "")
            if href and not href.startswith("#"):
                href = href.replace(".html", ".md")
                self.result.append("[")
                self._pending_link = href
            else:
                self._pending_link = None
        elif tag_lower == "blockquote":
            self.result.append("\n\n")
        elif tag_lower == "table":
            self.in_table = True
            self.table_rows = []
            self.result.append("\n\n")
        elif tag_lower == "tr":
            self.row_cells = []
        elif tag_lower == "th":
            pass
        elif tag_lower == "td":
            pass
        elif tag_lower == "img":
            alt = attrs_dict.get("alt", "")
            src = attrs_dict.get("src", "")
            self.result.append(f"![{alt}]({src})")
            self.skip = True
        elif tag_lower == "hr":
            self.result.append("\n\n---\n\n")

    def handle_endtag(self, tag):
        tag_lower = tag.lower()

        if tag_lower == "div" and self.in_content:
            if self.tag_stack and self.tag_stack[-1] == "div":
                self.tag_stack.pop()
            self.in_content = False
            return

        if not self.in_content:
            return

        if self.tag_stack and self.tag_stack[-1] == tag_lower:
            self.tag_stack.pop()

        if tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            pass
        elif tag_lower == "p":
            pass
        elif tag_lower in ("strong", "b"):
            self.result.append("**")
        elif tag_lower in ("em", "i"):
            self.result.append("*")
        elif tag_lower == "code":
            if not self.in_pre:
                self.result.append("`")
            self.in_code = False
        elif tag_lower == "pre":
            self.in_pre = False
            self.result.append("\n```\n")
        elif tag_lower in ("ul", "ol"):
            if self.list_counter:
                self.list_counter.pop()
            self.result.append("\n")
        elif tag_lower == "li":
            pass
        elif tag_lower == "a":
            link = getattr(self, "_pending_link", None)
            if link:
                self.result.append(f"]({link})")
            self._pending_link = None
        elif tag_lower == "blockquote":
            self.result.append("\n")
        elif tag_lower == "table":
            self.in_table = False
            md_table = self._build_table()
            self.result.append(md_table)
            self.result.append("\n\n")
        elif tag_lower == "tr":
            self.table_rows.append(self.row_cells[:])
        elif tag_lower == "th":
            pass
        elif tag_lower == "td":
            pass
        elif tag_lower == "img":
            self.skip = False

        self.current_tag = self.tag_stack[-1] if self.tag_stack else None

    def _build_table(self):
        if not self.table_rows:
            return ""
        lines = []
        header = self.table_rows[0]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        for row in self.table_rows[1:]:
            padded = row + [""] * (len(header) - len(row))
            lines.append("| " + " | ".join(padded[: len(header)]) + " |")
        return "\n".join(lines)

    def handle_data(self, data):
        if not self.in_content or self.skip:
            return

        if self.in_table:
            if self.current_tag in ("th", "td"):
                self.row_cells.append(data.strip())
            return

        if self.current_tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(self.current_tag[1])
            prefix = "#" * level + " "
            stripped = data.strip()
            if stripped:
                self.result.append(f"\n\n{prefix}{stripped}")
        elif self.current_tag == "blockquote":
            for line in data.split("\n"):
                stripped = line.strip()
                if stripped:
                    self.result.append(f"> {stripped}\n")
        elif self.in_pre:
            self.result.append(data)
        else:
            self.result.append(data)

    def get_markdown(self):
        text = "".join(self.result)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        return text


def extract_title_from_html(html_content):
    match = re.search(r"<title>(.*?)</title>", html_content, re.DOTALL)
    if match:
        title = match.group(1).strip()
        title = re.sub(r"\s*\|.*$", "", title).strip()
        return title
    return ""


def convert_html_to_md(html_content):
    parser = HTMLToMarkdown()
    parser.feed(html_content)
    return parser.get_markdown()


def process_file(html_path, output_dir):
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    title = extract_title_from_html(html_content)
    md_content = convert_html_to_md(html_content)

    rel_path = os.path.relpath(html_path, os.path.dirname(output_dir))

    base = os.path.basename(rel_path)
    parent = os.path.dirname(rel_path)

    if base.endswith(".md.html"):
        base = base[:-5]
    elif base.endswith(".html"):
        base = base[:-5]

    md_filename = base + ".md"
    md_path = (
        os.path.join(output_dir, parent, md_filename)
        if parent
        else os.path.join(output_dir, md_filename)
    )
    os.makedirs(os.path.dirname(md_path), exist_ok=True)

    full_md = ""
    if title:
        full_md += f"# {title}\n\n"
    full_md += md_content

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(full_md)

    print(f"  {html_path} -> {md_path}")
    return md_path


# Main
BASE_DIR = "tdx_quant_site"
MD_DIR = "tdx_quant_md"

html_files = []
for root, dirs, files in os.walk(BASE_DIR):
    for fname in files:
        if fname.endswith(".html"):
            html_files.append(os.path.join(root, fname))

print(f"Found {len(html_files)} HTML files to convert\n")

for i, html_file in enumerate(sorted(html_files), 1):
    print(f"[{i}/{len(html_files)}] Converting {html_file}")
    process_file(html_file, MD_DIR)

print(f"\nDone! All markdown files saved to {MD_DIR}/")
