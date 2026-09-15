"""Report the live status of every external link in dist/. Report only: always exits 0.

Usage: uv run python scripts/check_links.py [dist]
"""

import sys
import urllib.error
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

# Sites that answer bots with a login wall or a non-standard code even when the page exists.
LOGIN_WALLED = ("x.com", "linkedin.com", "t.me", "instagram.com")


def status(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return str(response.status)
    except urllib.error.HTTPError as err:
        return str(err.code)
    except Exception as err:  # DNS, TLS, timeout
        return type(err).__name__


def main():
    dist = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    urls = {}
    for page in sorted(dist.rglob("*.html")):
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        for a in soup.find_all("a", href=True):
            if a["href"].startswith(("http://", "https://")):
                urls.setdefault(a["href"], page.relative_to(dist).as_posix())

    problems = 0
    for url, page in sorted(urls.items()):
        code = status(url)
        walled = any(host in url for host in LOGIN_WALLED)
        ok = code.startswith(("2", "3")) or walled
        problems += not ok
        print(f"{'ok ' if ok else 'BAD'} {code:>18}  {url}  ({page}){'  [login-walled, not checked]' if walled and not code.startswith('2') else ''}")
    print(f"\n{len(urls)} external links, {problems} need a look")


if __name__ == "__main__":
    main()
