import urllib.request
import urllib.parse
import html.parser
import os
import time

BASE_URL = "https://help.tdx.com.cn"
MAIN_PAGE = "/quant/"
OUTPUT_DIR = "tdx_quant_site"


class LinkExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.in_sidebar = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if (
            tag == "aside"
            and "class" in attrs_dict
            and "sidebar" in attrs_dict.get("class", "")
        ):
            self.in_sidebar = True
        if tag == "a" and self.in_sidebar and "href" in attrs_dict:
            href = attrs_dict["href"]
            if href.startswith("/quant/"):
                self.links.append(href)

    def handle_endtag(self, tag):
        if tag == "aside":
            self.in_sidebar = False


def get_all_links():
    url = urllib.parse.urljoin(BASE_URL, MAIN_PAGE)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        html_content = resp.read().decode("utf-8")
    parser = LinkExtractor()
    parser.feed(html_content)
    return list(set(parser.links))


def fetch_page(url):
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def save_page(html_content, url):
    path = url.replace("/quant/", "").rstrip("/")
    if not path:
        path = "index.html"
    elif not path.endswith(".html"):
        path = path + ".html"

    filepath = os.path.join(OUTPUT_DIR, path)
    os.makedirs(
        os.path.dirname(filepath) if os.path.dirname(filepath) else OUTPUT_DIR,
        exist_ok=True,
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    return filepath


# Main
print("Fetching main page to discover all links...")
links = get_all_links()
print(f"Found {len(links)} pages to fetch\n")

os.makedirs(OUTPUT_DIR, exist_ok=True)

for i, link in enumerate(sorted(links), 1):
    url = urllib.parse.urljoin(BASE_URL, link)
    print(f"[{i}/{len(links)}] Fetching {link}")
    html_content = fetch_page(url)
    if html_content:
        filepath = save_page(html_content, link)
        print(f"  Saved to {filepath}")
    time.sleep(0.5)

print(f"\nDone! All pages saved to {OUTPUT_DIR}/")
