import urllib.request
import urllib.parse
import urllib.error
import html.parser
import os
import time
import random

BASE_URL = "https://help.tdx.com.cn"
MAIN_PAGE = "/quant/"
OUTPUT_DIR = "tdx_quant_site"

# 限流控制参数
INITIAL_DELAY = 2.0  # 初始请求间隔（秒）
MIN_DELAY = 0.5  # 最小请求间隔
MAX_DELAY = 30.0  # 最大退避间隔
MAX_RETRIES = 5  # 最大重试次数
BACKOFF_FACTOR = 2.0  # 指数退避因子
JITTER = True  # 是否添加随机抖动


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


def smart_delay(attempt, base_delay=INITIAL_DELAY):
    """智能延迟：指数退避 + 随机抖动"""
    delay = min(base_delay * (BACKOFF_FACTOR**attempt), MAX_DELAY)
    if JITTER:
        delay = delay * (0.5 + random.random() * 0.5)  # 50%-100% 随机化
    return max(delay, MIN_DELAY)


def fetch_with_retry(url, max_retries=MAX_RETRIES):
    """带重试和指数退避的请求"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "identity",
        "Connection": "keep-alive",
    }

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Too Many Requests
                delay = smart_delay(attempt)
                print(
                    f"    ⚠ 限流 (429)，等待 {delay:.1f}s 后重试 ({attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                continue
            elif e.code >= 500:  # 服务器错误
                delay = smart_delay(attempt)
                print(
                    f"    ⚠ 服务器错误 ({e.code})，等待 {delay:.1f}s 后重试 ({attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                continue
            else:
                print(f"    ✖ HTTP 错误 {e.code}: {e.reason}")
                return None
        except urllib.error.URLError as e:
            delay = smart_delay(attempt)
            print(
                f"    ⚠ 网络错误: {e.reason}，等待 {delay:.1f}s 后重试 ({attempt + 1}/{max_retries})"
            )
            time.sleep(delay)
            continue
        except Exception as e:
            delay = smart_delay(attempt)
            print(
                f"    ⚠ 未知错误: {e}，等待 {delay:.1f}s 后重试 ({attempt + 1}/{max_retries})"
            )
            time.sleep(delay)
            continue

    print(f"    ✖ 达到最大重试次数 ({max_retries})，跳过")
    return None


def get_all_links():
    url = urllib.parse.urljoin(BASE_URL, MAIN_PAGE)
    print(f"获取主页链接: {url}")
    html_content = fetch_with_retry(url)
    if not html_content:
        print("✖ 无法获取主页")
        return []
    parser = LinkExtractor()
    parser.feed(html_content)
    return list(set(parser.links))


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
print("=" * 60)
print("通达信量化文档爬虫 - 智能限流版")
print("=" * 60)
print(f"\n配置:")
print(f"  初始延迟: {INITIAL_DELAY}s")
print(f"  最小延迟: {MIN_DELAY}s")
print(f"  最大延迟: {MAX_DELAY}s")
print(f"  最大重试: {MAX_RETRIES}")
print(f"  退避因子: {BACKOFF_FACTOR}")
print(f"  随机抖动: {'是' if JITTER else '否'}")
print()

print("步骤 1/2: 获取主页链接...")
links = get_all_links()
if not links:
    print("✖ 未找到任何链接，退出")
    exit(1)
print(f"✓ 找到 {len(links)} 个页面\n")

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("步骤 2/2: 抓取页面内容...")
print("-" * 60)

success_count = 0
fail_count = 0
current_delay = INITIAL_DELAY

for i, link in enumerate(sorted(links), 1):
    url = urllib.parse.urljoin(BASE_URL, link)
    print(f"\n[{i}/{len(links)}] {link}")

    html_content = fetch_with_retry(url)
    if html_content:
        filepath = save_page(html_content, link)
        print(f"  ✓ 已保存: {filepath}")
        success_count += 1
    else:
        print(f"  ✖ 抓取失败")
        fail_count += 1

    # 平滑递增请求速率：随着成功次数增加，逐渐减少间隔
    if success_count > 0:
        current_delay = max(MIN_DELAY, INITIAL_DELAY / (1 + success_count * 0.1))
    else:
        current_delay = INITIAL_DELAY

    if i < len(links):
        print(f"  ⏱ 等待 {current_delay:.1f}s...")
        time.sleep(current_delay)

print("\n" + "=" * 60)
print(f"抓取完成!")
print(f"  成功: {success_count}/{len(links)}")
print(f"  失败: {fail_count}/{len(links)}")
print(f"  保存目录: {OUTPUT_DIR}/")
print("=" * 60)
